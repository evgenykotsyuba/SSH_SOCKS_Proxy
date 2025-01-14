import socket
import threading
import logging
import traceback
# from contextlib import closing

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SOCKStoHTTPProxy:
    def __init__(self, socks_host='localhost', socks_port=1080, http_host='localhost', http_port=8080):
        """
        Initializes the proxy server.

        :param socks_host: Host for the SOCKS server
        :param socks_port: Port for the SOCKS server
        :param http_host: Host for the HTTP proxy
        :param http_port: Port for the HTTP proxy
        """
        self.socks_host = socks_host
        self.socks_port = socks_port
        self.http_host = http_host
        self.http_port = http_port
        self.server_socket = None
        self._stop_event = threading.Event()

        try:
            # Create the HTTP server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.http_host, self.http_port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)

            logger.info(f"HTTP Proxy started at {self.http_host}:{self.http_port}")
        except Exception as e:
            logger.error(f"Failed to initialize HTTP proxy: {e}")
            if self.server_socket:
                self.server_socket.close()
            raise

    def handle_client(self, client_socket):
        """
        Handles incoming client connections and forwards data through the SOCKS proxy.

        :param client_socket: The client socket.
        """
        try:
            request = client_socket.recv(4096)
            if not request:
                return

            # Parse the HTTP request to extract the target host and port
            request_str = request.decode('utf-8', errors='ignore')
            host_line = next((line for line in request_str.split('\n') if line.lower().startswith('host:')), None)
            if not host_line:
                logger.error("Failed to parse target host from the request")
                return

            target_host, target_port = self._parse_target_host_and_port(host_line)

            # Establish a SOCKS connection
            with self._create_socks_connection(target_host, target_port) as socks_socket:
                if not socks_socket:
                    logger.error("Failed to establish a SOCKS connection")
                    return

                # Forward the HTTP request through SOCKS
                if request_str.startswith("CONNECT"):
                    client_socket.sendall(b'HTTP/1.1 200 Connection Established\r\n\r\n')
                    self._forward_data(client_socket, socks_socket)
                else:
                    socks_socket.sendall(request)
                    self._forward_data(client_socket, socks_socket)
        except Exception as e:
            logger.error(f"Error handling client: {e}\n{traceback.format_exc()}")
        finally:
            client_socket.close()

    def _parse_target_host_and_port(self, host_line):
        """Parses the target host and port from the Host header."""
        host_parts = host_line.split(':', 1)
        target_host = host_parts[1].strip()
        target_port = 80

        if ':' in target_host:
            target_host, target_port = target_host.rsplit(':', 1)
            target_port = int(target_port)

        return target_host, target_port

    def _create_socks_connection(self, target_host, target_port):
        """Establishes a connection to the SOCKS proxy."""
        try:
            socks_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socks_socket.connect((self.socks_host, self.socks_port))

            # SOCKS5 handshake
            socks_socket.send(b'\x05\x01\x00')
            response = socks_socket.recv(2)
            if response[1] != 0x00:
                logger.error("SOCKS handshake failed")
                socks_socket.close()
                return None

            # SOCKS5 connection request
            connect_request = (
                    b'\x05'  # SOCKS version
                    b'\x01'  # CONNECT command
                    b'\x00'  # Reserved
                    b'\x03'  # Address type: domain name
                    + bytes([len(target_host)])  # Length of domain name
                    + target_host.encode()  # Domain name
                    + target_port.to_bytes(2, 'big')  # Port
            )
            socks_socket.send(connect_request)
            response = socks_socket.recv(10)
            if response[1] != 0x00:
                logger.error(f"SOCKS connection failed with error {response[1]}")
                socks_socket.close()
                return None

            return socks_socket
        except Exception as e:
            logger.error(f"Error establishing SOCKS connection: {e}")
            return None

    def _forward_data(self, client_socket, socks_socket):
        """Forwards data between the client and the SOCKS connection."""

        def forward(source, destination):
            try:
                while not self._stop_event.is_set():
                    data = source.recv(4096)
                    if not data:
                        break
                    destination.sendall(data)
            except Exception as e:
                logger.debug(f"Error in data forwarding: {e}")
            finally:
                source.close()
                destination.close()

        client_to_socks = threading.Thread(target=forward, args=(client_socket, socks_socket))
        socks_to_client = threading.Thread(target=forward, args=(socks_socket, client_socket))

        client_to_socks.start()
        socks_to_client.start()

        client_to_socks.join()
        socks_to_client.join()

    def start(self):
        """Starts the proxy server."""
        try:
            while not self._stop_event.is_set():
                try:
                    client_socket, _ = self.server_socket.accept()
                    threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()
                except socket.timeout:  # Обработка тайм-аута accept
                    logger.debug("Timeout waiting for client connections")  # Меняем уровень на DEBUG
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.stop()

    # def stop(self):
    #     """Stops the proxy server."""
    #     self._stop_event.set()
    #     if self.server_socket:
    #         self.server_socket.close()
    #         logger.info("Server socket closed.")

    def stop(self):
        """Stops the proxy server."""
        self._stop_event.set()
        if self.server_socket:
            try:
                self.server_socket.close()  # Закрытие server_socket завершает accept
                logger.info("Server socket closed.")
            except Exception as e:
                logger.error(f"Error closing server socket: {e}")

        # Ожидание завершения всех потоков
        for thread in threading.enumerate():
            if thread != threading.current_thread() and thread.is_alive():
                logger.debug(f"Waiting for thread {thread.name} to finish")
                thread.join(timeout=1.0)  # Ждём завершения потока


if __name__ == "__main__":
    proxy = SOCKStoHTTPProxy()
    try:
        proxy.start()
    except KeyboardInterrupt:
        proxy.stop()
