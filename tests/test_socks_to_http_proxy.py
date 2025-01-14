# Example run: python -Wd -X tracemalloc=5 -m unittest tests/test_socks_to_http_proxy.py -v

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

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from socks_to_http_proxy import SOCKStoHTTPProxy


class TestSOCKStoHTTPProxy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.disable(logging.CRITICAL)

    def setUp(self):
        self.socks_host = 'localhost'
        self.http_host = 'localhost'
        self.socks_port = get_free_port()
        self.http_port = get_free_port()

        # Создание mock SOCKS сервера
        self.mock_socks_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mock_socks_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.mock_socks_server.bind((self.socks_host, self.socks_port))
        self.mock_socks_server.listen(1)

        # Запуск прокси в отдельном потоке
        self.proxy = SOCKStoHTTPProxy(
            socks_host=self.socks_host,
            socks_port=self.socks_port,
            http_host=self.http_host,
            http_port=self.http_port
        )
        self.proxy_thread = threading.Thread(target=self.proxy.start)
        self.proxy_thread.daemon = True
        self.proxy_thread.start()

        # Ожидание запуска прокси
        time.sleep(0.1)

    def tearDown(self):
        try:
            if hasattr(self, 'proxy') and self.proxy:
                self.proxy.stop()
            if hasattr(self, 'mock_socks_server') and self.mock_socks_server:
                self.mock_socks_server.close()
            if hasattr(self, 'proxy_thread') and self.proxy_thread.is_alive():
                self.proxy_thread.join(timeout=1.0)
        except Exception as e:
            logging.error(f"Error during tearDown: {e}")
        finally:
            # Убедитесь, что все потоки завершены
            for thread in threading.enumerate():
                if thread != threading.current_thread() and thread.is_alive():
                    logging.warning(f"Thread {thread.name} is still alive")

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
        """Test 2: Check proxy availability and request handling"""

        def mock_socks_response():
            conn, _ = self.mock_socks_server.accept()
            # Send SOCKS handshake response
            conn.send(b'\x05\x00')
            # Receive connection request
            conn.recv(1024)
            # Send connection success response
            conn.send(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
            # Send mock HTTP response
            conn.send(b'HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK')
            conn.close()

        # Start mock SOCKS server response handler
        socks_thread = threading.Thread(target=mock_socks_response)
        socks_thread.daemon = True
        socks_thread.start()

        try:
            # Test HTTP request through proxy
            with self.create_test_socket() as sock:
                sock.connect((self.http_host, self.http_port))
                # Send HTTP request
                sock.send(b'GET http://example.com/ HTTP/1.1\r\nHost: example.com\r\n\r\n')
                # Receive response
                response = sock.recv(1024)
                self.assertIn(b'200 OK', response, "Proxy should return 200 OK response")
        except Exception as e:
            self.fail(f"Proxy availability test failed: {str(e)}")

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
