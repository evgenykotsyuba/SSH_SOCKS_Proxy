import socket
import threading
import logging
import traceback
import select
import time
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SOCKStoHTTPProxy:
    def __init__(self, socks_host='localhost', socks_port=1080, http_host='localhost', http_port=8080):
        self.socks_host = socks_host
        self.socks_port = socks_port
        self.http_host = http_host
        self.http_port = http_port
        self.server_socket = None
        self._stop_event = threading.Event()
        self._active_connections = set()
        self._connections_lock = threading.Lock()

        try:
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

    def _safe_socket_operation(self, socket_obj: socket.socket, operation, *args, timeout: float = 5.0) -> Optional[
        bytes]:
        """Safely perform socket operations with timeout and error handling."""
        try:
            if operation == 'recv':
                ready = select.select([socket_obj], [], [], timeout)
                if ready[0]:
                    return socket_obj.recv(*args)
            elif operation == 'send':
                ready = select.select([], [socket_obj], [], timeout)
                if ready[1]:
                    return socket_obj.send(*args)
            return None
        except (socket.error, select.error) as e:
            logger.debug(f"Socket operation {operation} failed: {e}")
            return None

    def _handle_connection_error(self, client_socket: socket.socket):
        """Handle connection errors and cleanup."""
        with self._connections_lock:
            if client_socket in self._active_connections:
                self._active_connections.remove(client_socket)
        try:
            client_socket.close()
        except:
            pass

    def handle_client(self, client_socket: socket.socket):
        """Handle incoming client connections with improved error handling."""
        with self._connections_lock:
            self._active_connections.add(client_socket)

        try:
            request = self._safe_socket_operation(client_socket, 'recv', 4096)
            if not request:
                self._handle_connection_error(client_socket)
                return

            request_str = request.decode('utf-8', errors='ignore')
            host_line = next((line for line in request_str.split('\n')
                              if line.lower().startswith('host:')), None)

            if not host_line:
                logger.error("Failed to parse target host from the request")
                self._handle_connection_error(client_socket)
                return

            target_host, target_port = self._parse_target_host_and_port(host_line)
            socks_socket = self._create_socks_connection(target_host, target_port)

            if not socks_socket:
                logger.error("Failed to establish SOCKS connection")
                self._handle_connection_error(client_socket)
                return

            try:
                if request_str.startswith("CONNECT"):
                    self._safe_socket_operation(
                        client_socket, 'send',
                        b'HTTP/1.1 200 Connection Established\r\n\r\n'
                    )
                    self._forward_data(client_socket, socks_socket)
                else:
                    self._safe_socket_operation(socks_socket, 'send', request)
                    self._forward_data(client_socket, socks_socket)
            finally:
                socks_socket.close()

        except Exception as e:
            logger.error(f"Error handling client: {e}\n{traceback.format_exc()}")
        finally:
            self._handle_connection_error(client_socket)

    def _forward_data(self, client_socket: socket.socket, socks_socket: socket.socket):
        """Forward data between sockets with improved error handling."""

        def forward(source: socket.socket, destination: socket.socket, name: str):
            try:
                while not self._stop_event.is_set():
                    data = self._safe_socket_operation(source, 'recv', 4096)
                    if not data:
                        break
                    if not self._safe_socket_operation(destination, 'send', data):
                        break
                    time.sleep(0.001)  # Prevent CPU overload on Windows
            except Exception as e:
                logger.debug(f"Error in {name} forwarding: {e}")
            finally:
                self._handle_connection_error(source)
                self._handle_connection_error(destination)

        client_to_socks = threading.Thread(
            target=forward,
            args=(client_socket, socks_socket, "client->socks")
        )
        socks_to_client = threading.Thread(
            target=forward,
            args=(socks_socket, client_socket, "socks->client")
        )

        client_to_socks.daemon = True
        socks_to_client.daemon = True

        client_to_socks.start()
        socks_to_client.start()

        client_to_socks.join()
        socks_to_client.join()

    def _parse_target_host_and_port(self, host_line: str) -> tuple:
        """Parse target host and port with improved error handling."""
        try:
            host_parts = host_line.split(':', 1)
            target_host = host_parts[1].strip()
            target_port = 80

            if ':' in target_host:
                target_host, port_str = target_host.rsplit(':', 1)
                try:
                    target_port = int(port_str)
                except ValueError:
                    logger.warning(f"Invalid port number: {port_str}, using default 80")
                    target_port = 80

            return target_host, target_port
        except Exception as e:
            logger.error(f"Error parsing host and port: {e}")
            return 'localhost', 80

    def _create_socks_connection(self, target_host: str, target_port: int) -> Optional[socket.socket]:
        """Establishes a connection to the SOCKS proxy with improved error handling."""
        socks_socket = None
        try:
            socks_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socks_socket.settimeout(5.0)  # Set timeout for connection attempts

            # Connect to SOCKS server
            try:
                socks_socket.connect((self.socks_host, self.socks_port))
            except ConnectionRefusedError:
                logger.error(f"Connection to SOCKS server refused at {self.socks_host}:{self.socks_port}")
                return None
            except socket.timeout:
                logger.error("Timeout while connecting to SOCKS server")
                return None

            # SOCKS5 handshake
            handshake = self._safe_socket_operation(socks_socket, 'send', b'\x05\x01\x00')
            if not handshake:
                logger.error("Failed to send SOCKS5 handshake")
                return None

            # Receive handshake response
            response = self._safe_socket_operation(socks_socket, 'recv', 2)
            if not response or len(response) < 2 or response[1] != 0x00:
                logger.error(f"SOCKS handshake failed: {response.hex() if response else 'No response'}")
                return None

            # Prepare connection request
            connect_request = (
                    b'\x05'  # SOCKS version
                    b'\x01'  # CONNECT command
                    b'\x00'  # Reserved
                    b'\x03'  # Address type: domain name
                    + bytes([len(target_host)])  # Length of domain name
                    + target_host.encode()  # Domain name
                    + target_port.to_bytes(2, 'big')  # Port
            )

            # Send connection request
            if not self._safe_socket_operation(socks_socket, 'send', connect_request):
                logger.error("Failed to send SOCKS connection request")
                return None

            # Receive connection response
            response = self._safe_socket_operation(socks_socket, 'recv', 10)
            if not response or len(response) < 2 or response[1] != 0x00:
                logger.error(f"SOCKS connection failed: {response.hex() if response else 'No response'}")
                return None

            return socks_socket

        except Exception as e:
            logger.error(f"Error establishing SOCKS connection: {e}")
            if socks_socket:
                try:
                    socks_socket.close()
                except:
                    pass
            return None

    def stop(self):
        """Stop the proxy server and cleanup all connections."""
        self._stop_event.set()

        # Close all active connections
        with self._connections_lock:
            for sock in self._active_connections.copy():
                try:
                    sock.close()
                except:
                    pass
            self._active_connections.clear()

        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
                logger.info("Server socket closed")
            except Exception as e:
                logger.error(f"Error closing server socket: {e}")

        # Wait for all threads to finish
        for thread in threading.enumerate():
            if (thread != threading.current_thread() and
                    thread.is_alive() and
                    thread.daemon):
                thread.join(timeout=1.0)

    def start(self):
        """Start the proxy server with improved error handling."""
        try:
            while not self._stop_event.is_set():
                try:
                    client_socket, _ = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket,),
                        daemon=True
                    )
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if not self._stop_event.is_set():
                        logger.error(f"Error accepting connection: {e}")
                    break
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.stop()


if __name__ == "__main__":
    proxy = SOCKStoHTTPProxy()
    try:
        proxy.start()
    except KeyboardInterrupt:
        proxy.stop()
