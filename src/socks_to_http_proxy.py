import socket
import threading
import logging
import traceback
import select
import time
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum, auto
import asyncio
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProxyError(Exception):
    """Base exception for proxy-related errors"""
    pass


class ConnectionError(ProxyError):
    """Exception for connection-related errors"""
    pass


class ProtocolError(ProxyError):
    """Exception for protocol-related errors"""
    pass


class SOCKSVersion(Enum):
    """SOCKS protocol versions"""
    SOCKS5 = 5


class SOCKSCommand(Enum):
    """SOCKS commands"""
    CONNECT = 1


class AddressType(Enum):
    """SOCKS address types"""
    DOMAIN = 3


class SOCKSResponse(Enum):
    """SOCKS response codes"""
    SUCCESS = 0
    FAILURE = 1


@dataclass
class HostInfo:
    """Host information container"""
    host: str
    port: int = 80

    @classmethod
    def parse_from_header(cls, host_line: str) -> 'HostInfo':
        """Parse host information from HTTP header"""
        try:
            # Remove 'Host:' prefix and strip whitespace
            _, host_value = host_line.split(':', 1)
            host_value = host_value.strip()

            # Check if port is specified
            if ':' in host_value:
                host, port_str = host_value.rsplit(':', 1)
                try:
                    port = int(port_str)
                except ValueError:
                    logger.warning(f"Invalid port number: {port_str}, using default 80")
                    port = 80
                return cls(host=host, port=port)
            else:
                return cls(host=host_value)
        except Exception as e:
            logger.error(f"Error parsing host and port: {e}")
            return cls(host='localhost')


class SocketManager:
    """Socket operations manager with timeout and error handling"""

    @staticmethod
    def safe_recv(sock: socket.socket, buffer_size: int, timeout: float = 5.0) -> Optional[bytes]:
        """Safely receive data with timeout"""
        try:
            ready = select.select([sock], [], [], timeout)
            if ready[0]:
                return sock.recv(buffer_size)
            return None
        except (socket.error, select.error) as e:
            logger.debug(f"Socket recv failed: {e}")
            return None

    @staticmethod
    def safe_send(sock: socket.socket, data: bytes, timeout: float = 5.0) -> bool:
        """Safely send data with timeout"""
        try:
            ready = select.select([], [sock], [], timeout)
            if ready[1]:
                sent = sock.send(data)
                return sent == len(data)
            return False
        except (socket.error, select.error) as e:
            logger.debug(f"Socket send failed: {e}")
            return False

    @staticmethod
    def close(sock: socket.socket) -> None:
        """Safely close a socket"""
        try:
            sock.close()
        except Exception as e:
            logger.debug(f"Error closing socket: {e}")


class SOCKS5Client:
    """SOCKS5 client for connecting to target hosts"""

    def __init__(self, socks_host: str, socks_port: int):
        self.socks_host = socks_host
        self.socks_port = socks_port

    def connect(self, target_host: str, target_port: int) -> Optional[socket.socket]:
        """Establish a connection to the target host through SOCKS5 proxy"""
        socks_socket = None
        try:
            # Create and connect socket to SOCKS server
            socks_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socks_socket.settimeout(5.0)

            try:
                socks_socket.connect((self.socks_host, self.socks_port))
            except ConnectionRefusedError:
                raise ConnectionError(f"SOCKS server refused connection at {self.socks_host}:{self.socks_port}")
            except socket.timeout:
                raise ConnectionError("Timeout connecting to SOCKS server")

            # Perform SOCKS5 handshake
            if not self._perform_handshake(socks_socket):
                raise ProtocolError("SOCKS5 handshake failed")

            # Establish connection to target
            if not self._establish_connection(socks_socket, target_host, target_port):
                raise ProtocolError("SOCKS5 connection establishment failed")

            return socks_socket

        except Exception as e:
            logger.error(f"SOCKS connection error: {e}")
            if socks_socket:
                SocketManager.close(socks_socket)
            return None

    def _perform_handshake(self, sock: socket.socket) -> bool:
        """Perform SOCKS5 protocol handshake"""
        # Send handshake packet (version 5, 1 auth method, no auth)
        handshake_packet = bytes([SOCKSVersion.SOCKS5.value, 1, 0])
        if not SocketManager.safe_send(sock, handshake_packet):
            return False

        # Receive handshake response
        response = SocketManager.safe_recv(sock, 2)
        return (response and len(response) == 2 and
                response[0] == SOCKSVersion.SOCKS5.value and
                response[1] == SOCKSResponse.SUCCESS.value)

    def _establish_connection(self, sock: socket.socket, host: str, port: int) -> bool:
        """Establish connection to target through SOCKS5"""
        # Prepare connection request
        # SOCKS5 | CONNECT | RESERVED | DOMAIN | len(host) | host | port
        connect_packet = bytes([
            SOCKSVersion.SOCKS5.value,
            SOCKSCommand.CONNECT.value,
            0,  # Reserved
            AddressType.DOMAIN.value,
            len(host)
        ]) + host.encode() + port.to_bytes(2, 'big')

        if not SocketManager.safe_send(sock, connect_packet):
            return False

        # Receive connection response
        response = SocketManager.safe_recv(sock, 10)
        return (response and len(response) >= 2 and
                response[0] == SOCKSVersion.SOCKS5.value and
                response[1] == SOCKSResponse.SUCCESS.value)


class DataForwarder:
    """Handles bidirectional data forwarding between sockets"""

    def __init__(self, source: socket.socket, destination: socket.socket,
                 name: str, buffer_size: int = 8192, stop_event=None):
        self.source = source
        self.destination = destination
        self.name = name
        self.buffer_size = buffer_size
        self.stop_event = stop_event or threading.Event()
        self.thread = None

    def start(self):
        """Start forwarding in a separate thread"""
        self.thread = threading.Thread(
            target=self._forward_loop,
            daemon=True,
            name=f"Forwarder-{self.name}"
        )
        self.thread.start()
        return self.thread

    def _forward_loop(self):
        """Main forwarding loop"""
        try:
            while not self.stop_event.is_set():
                # Wait for data with select
                readable, _, _ = select.select([self.source], [], [], 0.5)

                if not readable:
                    continue

                data = self.source.recv(self.buffer_size)
                if not data:
                    break  # Connection closed

                # Forward data to destination
                total_sent = 0
                while total_sent < len(data):
                    sent = self.destination.send(data[total_sent:])
                    if sent == 0:
                        raise ConnectionError("Socket connection broken")
                    total_sent += sent

                # Small sleep to prevent CPU overload on some systems
                time.sleep(0.001)

        except Exception as e:
            if not self.stop_event.is_set():
                logger.debug(f"Error in {self.name} forwarding: {e}")
        finally:
            # Signal that we're done
            self.stop_event.set()


class ConnectionHandler:
    """Handles client connections and setups data forwarding"""

    def __init__(self, client_socket: socket.socket, socks_client: SOCKS5Client):
        self.client_socket = client_socket
        self.socks_client = socks_client
        self.stop_event = threading.Event()
        self.socks_socket = None
        self.forwarders = []

    def handle(self):
        """Process the client connection"""
        try:
            # Receive and parse HTTP request
            request = SocketManager.safe_recv(self.client_socket, 8192)
            if not request:
                logger.error("Empty request received")
                return

            # Parse the request
            host_info = self._parse_request(request)
            if not host_info:
                return

            # Connect to target via SOCKS
            self.socks_socket = self.socks_client.connect(host_info.host, host_info.port)
            if not self.socks_socket:
                logger.error(f"Failed to connect to {host_info.host}:{host_info.port} via SOCKS")
                return

            # Handle based on HTTP method
            request_str = request.decode('utf-8', errors='ignore')
            if request_str.startswith("CONNECT"):
                self._handle_connect_method()
            else:
                self._handle_regular_method(request)

            # Wait for forwarding to complete
            for forwarder in self.forwarders:
                forwarder.thread.join()

        except Exception as e:
            logger.error(f"Error handling client connection: {e}")
        finally:
            self._cleanup()

    def _parse_request(self, request: bytes) -> Optional[HostInfo]:
        """Parse HTTP request to extract host information"""
        try:
            request_str = request.decode('utf-8', errors='ignore')
            # Find Host header
            for line in request_str.split('\r\n'):
                if line.lower().startswith('host:'):
                    return HostInfo.parse_from_header(line)

            logger.error("No Host header found in HTTP request")
            return None
        except Exception as e:
            logger.error(f"Error parsing HTTP request: {e}")
            return None

    def _handle_connect_method(self):
        """Handle HTTP CONNECT method"""
        # Send 200 Connection Established
        response = b'HTTP/1.1 200 Connection Established\r\n\r\n'
        if not SocketManager.safe_send(self.client_socket, response):
            logger.error("Failed to send 200 Connection Established")
            return

        # Setup bidirectional forwarding
        self._setup_forwarding()

    def _handle_regular_method(self, request: bytes):
        """Handle regular HTTP methods (GET, POST, etc.)"""
        # Forward the request as-is
        if not SocketManager.safe_send(self.socks_socket, request):
            logger.error("Failed to forward HTTP request to SOCKS")
            return

        # Setup bidirectional forwarding
        self._setup_forwarding()

    def _setup_forwarding(self):
        """Setup bidirectional data forwarding"""
        # Client to SOCKS
        client_to_socks = DataForwarder(
            self.client_socket, self.socks_socket,
            "client->socks", stop_event=self.stop_event
        )

        # SOCKS to client
        socks_to_client = DataForwarder(
            self.socks_socket, self.client_socket,
            "socks->client", stop_event=self.stop_event
        )

        self.forwarders = [client_to_socks, socks_to_client]

        # Start forwarding
        client_to_socks.start()
        socks_to_client.start()

    def _cleanup(self):
        """Clean up resources"""
        self.stop_event.set()

        if self.socks_socket:
            SocketManager.close(self.socks_socket)

        SocketManager.close(self.client_socket)


class SOCKStoHTTPProxy:
    """Main proxy server class"""

    def __init__(self, socks_host='localhost', socks_port=1080,
                 http_host='localhost', http_port=8080):
        self.socks_host = socks_host
        self.socks_port = socks_port
        self.http_host = http_host
        self.http_port = http_port
        self.server_socket = None
        self.stop_event = threading.Event()
        self.active_connections = set()
        self.connections_lock = threading.Lock()
        self.socks_client = SOCKS5Client(socks_host, socks_port)

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, sig, frame):
        """Handle termination signals"""
        logger.info(f"Received signal {sig}, shutting down...")
        self.stop()

    def start(self):
        """Start the proxy server"""
        try:
            # Initialize server socket
            self._init_server_socket()

            # Main accept loop
            while not self.stop_event.is_set():
                try:
                    # Accept with timeout to allow checking stop_event
                    client_socket, client_addr = self.server_socket.accept()
                    logger.debug(f"New connection from {client_addr}")

                    # Register connection
                    with self.connections_lock:
                        self.active_connections.add(client_socket)

                    # Handle in a separate thread
                    handler = ConnectionHandler(client_socket, self.socks_client)
                    thread = threading.Thread(
                        target=handler.handle,
                        daemon=True,
                        name=f"Handler-{client_addr[0]}:{client_addr[1]}"
                    )
                    thread.start()

                except socket.timeout:
                    # This is expected due to the timeout we set
                    continue

                except Exception as e:
                    if not self.stop_event.is_set():
                        logger.error(f"Error accepting connection: {e}")
                        # Small delay to prevent CPU spinning on repeated errors
                        time.sleep(0.1)

        except Exception as e:
            logger.error(f"Server error: {e}")

        finally:
            self.stop()

    def _init_server_socket(self):
        """Initialize the server socket"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Set timeout for accept() to allow checking stop_event periodically
            self.server_socket.settimeout(1.0)

            # Bind and listen
            self.server_socket.bind((self.http_host, self.http_port))
            self.server_socket.listen(10)  # Increased backlog

            logger.info(f"HTTP Proxy started at {self.http_host}:{self.http_port}")
            logger.info(f"Forwarding to SOCKS proxy at {self.socks_host}:{self.socks_port}")

        except Exception as e:
            logger.error(f"Failed to initialize HTTP proxy: {e}")
            if self.server_socket:
                self.server_socket.close()
                self.server_socket = None
            raise

    def stop(self):
        """Stop the proxy server and clean up resources"""
        if self.stop_event.is_set():
            return  # Already stopping

        self.stop_event.set()
        logger.info("Stopping proxy server...")

        # Close all active connections
        with self.connections_lock:
            for sock in self.active_connections:
                SocketManager.close(sock)
            self.active_connections.clear()

        # Close server socket
        if self.server_socket:
            SocketManager.close(self.server_socket)
            self.server_socket = None

        logger.info("Proxy server stopped")


async def async_main():
    """Async entry point for future async implementation"""
    # This function is a placeholder for future async implementation
    # Currently it just runs the synchronous proxy
    proxy = SOCKStoHTTPProxy()

    # Run in a thread pool
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, proxy.start)


def main():
    """Main entry point"""
    try:
        proxy = SOCKStoHTTPProxy()
        proxy.start()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
