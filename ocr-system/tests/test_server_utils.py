import socket
import unittest

from server_utils import get_available_port


class ServerUtilsTests(unittest.TestCase):
    def test_get_available_port_returns_next_free_port(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as reserved:
            reserved.bind(("127.0.0.1", 0))
            reserved_port = reserved.getsockname()[1]
            reserved.listen(1)

            candidate = get_available_port(reserved_port, max_attempts=3)

            self.assertTrue(candidate >= reserved_port)
            self.assertTrue(candidate > 0)


if __name__ == "__main__":
    unittest.main()
