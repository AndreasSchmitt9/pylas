# ui/plotter.py
import sys
import time
from collections import deque
from pathlib import Path

import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore, QtWidgets

# Must point to the same folder the PID writer logs to
LOG_DIR = "/home/andreas/Documents/PhD/projects/Welas/github/Control/logs"

WINDOW_S = 180        # visible time window (3 minutes)
KEEP_S = 200          # keep a bit more than visible in memory
POLL_MS = 250         # how often the log file is checked


class LogTail:
    """Reads new complete lines from the newest control_*.csv in a folder."""

    def __init__(self, log_dir, pattern="control_*.csv"):
        self.log_dir = Path(log_dir)
        self.pattern = pattern
        self.path = None
        self.pos = 0
        self.header = None

    def _latest(self):
        files = sorted(self.log_dir.glob(self.pattern))  # timestamped names sort chronologically
        return files[-1] if files else None

    def read_new(self):
        latest = self._latest()
        if latest is None:
            return []
        if latest != self.path:                  # new run -> start from the top
            self.path, self.pos, self.header = latest, 0, None

        try:
            with open(self.path, "rb") as f:     # binary: byte offsets stay exact on Windows
                f.seek(self.pos)
                chunk = f.read()
        except FileNotFoundError:
            return []

        end = chunk.rfind(b"\n")
        if end == -1:                            # no complete line yet
            return []
        self.pos += end + 1

        rows = []
        for line in chunk[:end].decode().splitlines():
            if not line.strip():
                continue
            if self.header is None:
                self.header = [h.strip() for h in line.split(",")]   # tolerate stray spaces
                continue
            try:
                rows.append(dict(zip(self.header, map(float, line.split(",")))))
            except ValueError:
                continue                         # skip malformed line
        return rows


def _set_dynamic_y(plot, series_list, t_min):
    """Fit the y-axis to the data inside the visible time window."""
    lo, hi = np.inf, -np.inf
    for t, y in series_list:
        if len(t) == 0:
            continue
        visible = y[t >= t_min]
        visible = visible[np.isfinite(visible)]
        if len(visible):
            lo = min(lo, visible.min())
            hi = max(hi, visible.max())
    if not np.isfinite(lo) or not np.isfinite(hi):
        return
    span = hi - lo
    pad = span * 0.1 if span > 0 else max(abs(hi) * 0.1, 1e-9)
    plot.setYRange(lo - pad, hi + pad, padding=0)


def run_plotter(data_q=None, stop=None):
    """Entry point for the UI process. data_q is unused for now (kept for the existing signature)."""
    app = QtWidgets.QApplication(sys.argv)
    pg.setConfigOptions(antialias=True)

    win = pg.GraphicsLayoutWidget(title="Control monitor")
    win.resize(1000, 900)

    # --- Subplot 1: LWC and target LWC ---
    p1 = win.addPlot(row=0, col=0, axisItems={"bottom": pg.DateAxisItem()})
    p1.setLabel("left", "LWC", units="g/m³")
    p1.showGrid(x=True, y=True, alpha=0.3)
    p1.addLegend()
    lwc_curve = p1.plot(pen=pg.mkPen("y", width=2), name="LWC")
    tgt_curve = p1.plot(pen=pg.mkPen("c", width=2, style=QtCore.Qt.DashLine), name="Target LWC")

    # --- Subplot 2: P, I, D terms ---
    p2 = win.addPlot(row=1, col=0, axisItems={"bottom": pg.DateAxisItem()})
    p2.setLabel("left", "Controller terms")
    p2.showGrid(x=True, y=True, alpha=0.3)
    p2.addLegend()
    p_curve = p2.plot(pen=pg.mkPen("r", width=2), name="P")
    i_curve = p2.plot(pen=pg.mkPen("g", width=2), name="I")
    d_curve = p2.plot(pen=pg.mkPen("b", width=2), name="D")

    # --- Subplot 3: output (concentration setpoint from PID.output()) ---
    p3 = win.addPlot(row=2, col=0, axisItems={"bottom": pg.DateAxisItem()})
    p3.setLabel("left", "Output (concentration)")
    p3.showGrid(x=True, y=True, alpha=0.3)
    p3.addLegend()
    out_curve = p3.plot(pen=pg.mkPen("m", width=2), name="Output")

    for p in (p1, p2, p3):
        p.setMouseEnabled(x=False, y=False)      # view is driven by the data
        p.enableAutoRange(enable=False)

    # --- Data buffers ---
    keys = ("t", "lwc", "lwc_target", "p", "i", "d", "output")
    buf = {k: deque() for k in keys}
    tail = LogTail(LOG_DIR)

    def refresh():
        # 1) read new rows; clear the plot if a new run started
        prev_path = tail.path
        rows = tail.read_new()
        if tail.path != prev_path:
            for k in keys:
                buf[k].clear()
        for row in rows:
            if not all(k in row for k in keys):  # skip rows with missing columns
                print(f"[plotter] missing columns, header is: {tail.header}")
                continue
            for k in keys:
                buf[k].append(row[k])

        # 2) drop data older than the keep window
        now = time.time()
        while buf["t"] and buf["t"][0] < now - KEEP_S:
            for k in keys:
                buf[k].popleft()

        if not buf["t"]:
            return

        # 3) update curves
        a = {k: np.asarray(buf[k], dtype=float) for k in keys}
        lwc_curve.setData(a["t"], a["lwc"])
        tgt_curve.setData(a["t"], a["lwc_target"])
        p_curve.setData(a["t"], a["p"])
        i_curve.setData(a["t"], a["i"])
        d_curve.setData(a["t"], a["d"])
        out_curve.setData(a["t"], a["output"])

        # 4) scrolling 3-minute x-window and dynamic y-limits
        t_min = now - WINDOW_S
        for p in (p1, p2, p3):
            p.setXRange(t_min, now, padding=0)
        _set_dynamic_y(p1, [(a["t"], a["lwc"]), (a["t"], a["lwc_target"])], t_min)
        _set_dynamic_y(p2, [(a["t"], a["p"]), (a["t"], a["i"]), (a["t"], a["d"])], t_min)
        _set_dynamic_y(p3, [(a["t"], a["output"])], t_min)

    timer = QtCore.QTimer()
    timer.timeout.connect(refresh)
    timer.start(POLL_MS)

    # close the window if the main process signals shutdown
    def check_stop():
        if stop is not None and stop.is_set():
            app.quit()

    stop_timer = QtCore.QTimer()
    stop_timer.timeout.connect(check_stop)
    stop_timer.start(500)

    win.show()
    app.exec()


if __name__ == "__main__":
    # Standalone test: run from the project root with `python -m ui.plotter`
    run_plotter()