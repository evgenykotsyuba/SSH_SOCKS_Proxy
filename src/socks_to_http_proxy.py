#!/usr/bin/env python3
import socket
import threading
import sys
import logging
import traceback

# Logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('proxy_debug.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SOCKStoHTTPProxy:
    def __init__(self, socks_host='localhost', socks_port=1080,
                 http_host='localhost', http_port=8080, max_bind_attempts=10):
        """
        Initializes the proxy server with improved port binding.

        :param max_bind_attempts: Number of attempts to bind to alternative ports
        """
        self.socks_host = socks_host
        self.socks_port = socks_port
        self.http_host = http_host
        self.http_port = http_port
        self.server_socket = None
        self._stop_event = threading.Event()

        # Create the server socket for the HTTP proxy
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            # Attempt to bind to the port, with fallback to alternative ports
            self.http_host, self.http_port = bind_to_port(
                self.server_socket,
                self.http_host,
                self.http_port,
                max_attempts=max_bind_attempts
            )

            self.server_socket.listen(5)
            logger.info(f"HTTP proxy started at {self.http_host}:{self.http_port}")
            logger.info(f"Forwarding requests to SOCKS proxy {self.socks_host}:{self.socks_port}")

        except Exception as e:
            logger.error(f"Failed to start proxy server: {e}")
            self.stop()
            sys.exit(1)

    def create_socks_connection(self, target_host, target_port):
        """
        Creates a SOCKS connection.

        :param target_host: Target host
        :param target_port: Target port
        :return: SOCKS connection socket
        """
        try:
            # Establish SOCKS connection
            socks_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socks_socket.connect((self.socks_host, self.socks_port))

            # Send SOCKS5 greeting
            socks_socket.send(b'\x05\x01\x00')  # Version 5, 1 method, no authentication
            greeting_response = socks_socket.recv(2)
            logger.debug(f"SOCKS greeting response: {greeting_response.hex()}")

            # Send connection request
            connect_request = (
                b'\x05'  # SOCKS version
                b'\x01'  # CONNECT command
                b'\x00'  # Reserved
                b'\x03'  # Address type - domain name
                + bytes([len(target_host)])  # Domain name length
                + target_host.encode()  # Domain name
                + target_port.to_bytes(2, 'big')  # Port
            )
            socks_socket.send(connect_request)
            socks_response = socks_socket.recv(10)
            logger.debug(f"SOCKS connection response: {socks_response.hex()}")

            if socks_response[1] != 0x00:
                logger.error(f"SOCKS connection error: {socks_response[1]}")
                socks_socket.close()
                return None

            return socks_socket

        except Exception as e:
            logger.error(f"Error creating SOCKS connection: {e}")
            logger.error(traceback.format_exc())
            return None

    def handle_client(self, client_socket):
        """
        Handles a client connection and forwards it through SOCKS.

        :param client_socket: Client socket
        """
        if self._stop_event.is_set():
            client_socket.close()
            return

        try:
            # Read the HTTP request
            request = client_socket.recv(4096)
            if not request:
                client_socket.close()
                return

            # Parse the HTTP request to extract the target host and port
            request_str = request.decode('utf-8', errors='ignore')
            logger.debug(f"Received request:\n{request_str}")

            request_lines = request_str.split('\n')
            host_lines = [line for line in request_lines if line.lower().startswith('host:')]

            if not host_lines:
                logger.error("Failed to find the host in the request")
                client_socket.close()
                return

            host_line = host_lines[0]
            target_host = host_line.split(':', 1)[1].strip()
            target_port = 443 if 'CONNECT' in request_str else 80  # HTTPS or HTTP

            if ':' in target_host:
                target_host, target_port = target_host.rsplit(':', 1)
                target_port = int(target_port)

            logger.info(f"Connecting to: {target_host}:{target_port}")

            # Create a SOCKS connection
            socks_socket = self.create_socks_connection(target_host, target_port)
            if not socks_socket:
                client_socket.close()
                return

            # Handle HTTPS CONNECT
            if 'CONNECT' in request_str:
                client_socket.sendall(b'HTTP/1.1 200 Connection Established\r\n\r\n')
                self.forward_data(client_socket, socks_socket)
            else:
                # Proxy HTTP request
                socks_socket.sendall(request)
                self.forward_data(client_socket, socks_socket)

        except Exception as e:
            logger.error(f"Error handling client: {e}")
            logger.error(traceback.format_exc())
        finally:
            try:
                client_socket.close()
            except:
                pass

    def forward_data(self, client_socket, socks_socket):
        """
        Bidirectional data forwarding between client and SOCKS.
        """

        def forward(source, destination):
            try:
                while not self._stop_event.is_set():
                    data = source.recv(4096)
                    if not data:
                        break
                    destination.sendall(data)
            except socket.error as e:
                logger.debug(f"Forwarding error: {e}")
            finally:
                source.close()
                destination.close()

        # Create threads for data forwarding
        client_to_socks = threading.Thread(target=forward, args=(client_socket, socks_socket), daemon=True)
        socks_to_client = threading.Thread(target=forward, args=(socks_socket, client_socket), daemon=True)

        client_to_socks.start()
        socks_to_client.start()

        # Wait for threads to finish
        client_to_socks.join()
        socks_to_client.join()

    def start(self):
        try:
            while not self._stop_event.is_set():
                client_socket, address = self.server_socket.accept()
                if self._stop_event.is_set():
                    break
                logger.info(f"New connection from {address}")

                # Handle the client in a separate thread
                threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()
        except Exception as e:
            logging.error(f"Server error: {e}")
        finally:
            self.stop()

    def stop(self):
        """Gracefully stops the proxy server."""
        logging.info("Attempting to stop HTTP Proxy server...")

        # Установка флага остановки
        self._stop_event.set()

        try:
            # Закрытие серверного сокета
            if self.server_socket:
                self.server_socket.close()
                logging.info("Server socket closed.")
        except Exception as e:
            logging.error(f"Error closing server socket: {e}")

        # Принудительное закрытие всех активных потоков
        for thread in threading.enumerate():
            if thread is not threading.main_thread() and thread.is_alive():
                try:
                    # Попытка закрыть сокеты, связанные с потоком
                    if hasattr(thread, '_target') and thread._target == self.handle_client:
                        # Если это поток обработки клиента, попробуем закрыть его сокеты
                        if hasattr(thread, 'client_socket'):
                            try:
                                thread.client_socket.shutdown(socket.SHUT_RDWR)
                                thread.client_socket.close()
                            except:
                                pass

                    # Попытка принудительно завершить поток
                    if thread.is_alive():
                        thread._stop()
                except Exception as e:
                    logging.error(f"Error stopping thread {thread.name}: {e}")


def bind_to_port(server_socket, host, port, max_attempts=10):
    """
    Attempt to bind to a port with multiple attempts and optional port increment.

    :param server_socket: Socket to bind
    :param host: Host to bind to
    :param port: Initial port to try
    :param max_attempts: Maximum number of port binding attempts
    :return: Tuple of (final_host, final_port)
    """
    original_port = port
    for attempt in range(max_attempts):
        try:
            server_socket.bind((host, port))
            if attempt > 0:
                logger.info(f"Successfully bound to alternative port {port}")
            return host, port
        except OSError as e:
            if e.errno == 98:  # Address already in use
                port = original_port + attempt + 1
                logger.warning(f"Port {original_port} in use. Trying port {port}")
                server_socket.close()
                # Recreate socket
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            else:
                raise

    raise RuntimeError(f"Could not bind to a port after {max_attempts} attempts")
