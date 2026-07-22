import socket
from typing import Optional


def get_available_port(preferred_port: int = 8001, max_attempts: int = 10) -> int:
    """Return a free port, falling back to another port if preferred is busy."""
    for port in [preferred_port] + list(range(preferred_port + 1, preferred_port + max_attempts + 1)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    raise OSError("No available port found")
