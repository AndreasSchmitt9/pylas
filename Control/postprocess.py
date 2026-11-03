
"""
This class postprocesses control signal. It takes the desired concentration signal and creates a useful udp signal
"""
import socket

class Postprocessor:
    def __init__(self, host='127.0.0.1', port=12345):
        self._addr = (host, port)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def publish(self, control_signal: float):
        # Plain text so MATLAB can parse it with str2double
        self._sock.sendto(f"{control_signal:.6f}".encode(), self._addr)

    def close(self):
        self._sock.close()
