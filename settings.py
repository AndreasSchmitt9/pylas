"""
Loads settings.toml once at import and offers optional live reload.

Usage:
    from settings import cfg, reload_if_changed

    kp = cfg["pid"]["KP"]            # read a value

    if reload_if_changed():          # call once per loop tick (live reload)
        ...                          # re-apply values to your objects
"""
import os
from pathlib import Path

try:
    import tomllib                   # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib          # pip install tomli (needed on Python 3.8)

SETTINGS_PATH = Path(__file__).resolve().parent / "settings.toml"

# Loaded once at import. A missing or broken file raises here, so you notice at startup.
with open(SETTINGS_PATH, "rb") as f:
    cfg = tomllib.load(f)

_mtime = os.stat(SETTINGS_PATH).st_mtime_ns


def reload_if_changed():
    """Re-read settings.toml if it changed on disk.

    Returns True if cfg was updated, False otherwise. On a typo or half-saved
    file it keeps the old values. The dict is updated in place, so
    `from settings import cfg` stays valid in every module of this process.
    """
    global _mtime
    try:
        mtime = os.stat(SETTINGS_PATH).st_mtime_ns
        if mtime == _mtime:
            return False
        with open(SETTINGS_PATH, "rb") as f:
            new = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError) as e:
        print(f"Params: keeping old values ({e})", flush=True)
        return False
    _mtime = mtime
    cfg.clear()
    cfg.update(new)
    print("Params: reloaded", flush=True)
    return True