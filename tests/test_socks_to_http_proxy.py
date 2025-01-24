# Example test run: python -Wd -X tracemalloc=5 -m unittest tests/test_socks_to_http_proxy.py -v

import os
import sys
import unittest
import socket
import threading
import time
import requests
import logging
from unittest.mock import patch, MagicMock
from contextlib import contextmanager

# Get the absolute path to the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# Add project root and src directory to Python path
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from socks_to_http_proxy import SOCKStoHTTPProxy


class TestSOCKStoHTTPProxy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.disable(logging.CRITICAL)

    def setUp(self):
        self.socks_host = 'localhost'
        self.http_host = 'localhost'
        self.socks_port = self._get_free_port()
        self.http_port = self._get_free_port()

        # Create mock SOCKS server with improved error handling
        self.mock_socks_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mock_socks_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.mock_socks_server.bind((self.socks_host, self.socks_port))
        self.mock_socks_server.listen(1)
        self.mock_socks_server.settimeout(1.0)

        # Start proxy with proper initialization
        self.proxy = SOCKStoHTTPProxy(
            socks_host=self.socks_host,
            socks_port=self.socks_port,
            http_host=self.http_host,
            http_port=self.http_port
        )
        self.proxy_thread = threading.Thread(target=self.proxy.start)
        self.proxy_thread.daemon = True
        self.proxy_thread.start()

        # Wait for proxy startup
        time.sleep(0.2)

    def tearDown(self):
        try:
            if hasattr(self, 'proxy'):
                self.proxy.stop()
            if hasattr(self, 'mock_socks_server'):
                self.mock_socks_server.close()
            if hasattr(self, 'proxy_thread'):
                self.proxy_thread.join(timeout=1.0)
        except Exception as e:
            logging.error(f"Error during tearDown: {e}")

    def _get_free_port(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(('', 0))
            return sock.getsockname()[1]

    @contextmanager
    def create_test_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            yield sock
        finally:
            sock.close()

    def test_proxy_connection(self):
        """Test 1: Verify proxy server connection establishment"""
        try:
            with self.create_test_socket() as sock:
                result = sock.connect_ex((self.http_host, self.http_port))
                self.assertEqual(result, 0, "Failed to connect to HTTP proxy")
                self.assertTrue(self.proxy_thread.is_alive(), "Proxy server thread is not running")
        except Exception as e:
            self.fail(f"Proxy connection test failed: {str(e)}")

    def test_proxy_availability(self):
        """Test proxy availability with improved Windows compatibility"""

        def mock_socks_handler():
            try:
                conn, _ = self.mock_socks_server.accept()
                conn.settimeout(1.0)

                # SOCKS handshake
                conn.send(b'\x05\x00')
                conn.recv(1024)  # Connection request

                # Send success response
                conn.send(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')

                # Send HTTP response with proper headers
                response = (
                    b'HTTP/1.1 200 OK\r\n'
                    b'Content-Length: 2\r\n'
                    b'Connection: close\r\n'
                    b'\r\n'
                    b'OK'
                )
                conn.send(response)
                time.sleep(0.1)  # Wait for data to be sent
                conn.close()
            except Exception as e:
                logging.error(f"Mock SOCKS handler error: {e}")

        socks_thread = threading.Thread(target=mock_socks_handler)
        socks_thread.daemon = True
        socks_thread.start()

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                client.settimeout(2.0)
                client.connect((self.http_host, self.http_port))

                request = (
                    b'GET / HTTP/1.1\r\n'
                    b'Host: example.com\r\n'
                    b'Connection: close\r\n'
                    b'\r\n'
                )
                client.send(request)

                response = b''
                while True:
                    try:
                        chunk = client.recv(1024)
                        if not chunk:
                            break
                        response += chunk
                    except socket.timeout:
                        break

                self.assertIn(b'200 OK', response, "Expected 200 OK response")
        except Exception as e:
            self.fail(f"Proxy availability test failed: {str(e)}")
        finally:
            socks_thread.join(timeout=1.0)

    def test_proxy_shutdown(self):
        """Test 3: Verify clean proxy shutdown"""
        # Проверьте, что прокси работает
        with self.create_test_socket() as sock:
            result = sock.connect_ex((self.http_host, self.http_port))
            self.assertEqual(result, 0, "Proxy should be running before shutdown test")

        # Остановите прокси
        self.proxy.stop()
        time.sleep(0.1)  # Дайте потокам время завершиться

        # Убедитесь, что все потоки завершены
        client_threads = [thread for thread in threading.enumerate()
                          if thread != threading.current_thread()
                          and thread.is_alive()]
        if client_threads:
            logging.error(f"Still active threads: {[t.name for t in client_threads]}")
        self.assertEqual(len(client_threads), 0, "All client threads should be terminated")


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('', 0))
        return sock.getsockname()[1]


if __name__ == '__main__':
    unittest.main()
