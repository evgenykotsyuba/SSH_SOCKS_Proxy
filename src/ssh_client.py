import asyncio
import asyncssh
import aiohttp
import logging
from dataclasses import dataclass
from typing import Optional, Callable
from aiohttp_socks import ProxyConnector

# Assuming this module exists and provides the necessary functions
from password_encryption_decryption import decrypt_password, salt


class SSHConnectionError(Exception):
    """Custom exception for SSH connection errors."""
    pass


@dataclass
class SSHConfig:
    """Configuration for SSH connection.

    Attributes:
        host: The hostname or IP address of the SSH server.
        port: The port number of the SSH server.
        user: The username for authentication.
        auth_method: The authentication method ('password' or 'key').
        password: The password for authentication (required if auth_method is 'password').
        key_path: The path to the SSH key (required if auth_method is 'key').
        dynamic_port: The local port for the SOCKS proxy (default: 1080).
        keepalive_interval: Interval for keepalive packets (default: 0, disabled).
        keepalive_count_max: Maximum keepalive packets before disconnection (default: 0, disabled).
        test_url: URL to test the SOCKS proxy connection (optional).
        test_timeout: Timeout for the SOCKS proxy test in seconds (default: 5).
    """
    host: str
    port: int
    user: str
    auth_method: str  # 'password' or 'key'
    password: Optional[str] = None
    key_path: Optional[str] = None
    dynamic_port: int = 1080
    keepalive_interval: int = 0
    keepalive_count_max: int = 0
    test_url: Optional[str] = None
    test_timeout: int = 5

    def __post_init__(self):
        """Validates the configuration after initialization."""
        if self.auth_method not in ['password', 'key']:
            raise ValueError("auth_method must be 'password' or 'key'")
        if self.auth_method == 'password' and not self.password:
            raise ValueError("Password is required for auth_method='password'")
        if self.auth_method == 'key' and not self.key_path:
            raise ValueError("Key path is required for auth_method='key'")


class SSHClient:
    """Manages an SSH connection with SOCKS proxy forwarding.

    Attributes:
        config: The SSH configuration object.
        connection: The active SSH connection (or None).
        _running: Flag to control the connection management loop.
        _connected: Current connection status.
        status_callback: Optional callback to notify status changes.
        reconnect_attempts: Number of reconnection attempts made.
        max_reconnect_attempts: Maximum allowed reconnection attempts.
        _forwarder: The SOCKS forwarder object.
    """

    def __init__(self, config: SSHConfig, status_callback: Optional[Callable[[bool], None]] = None):
        """Initializes the SSH client with configuration and optional status callback.

        Args:
            config: The SSH configuration object.
            status_callback: Optional function to call when connection status changes.

        Raises:
            ValueError: If the provided configuration is invalid.
        """
        self.config = config
        self.connection: Optional[asyncssh.SSHClientConnection] = None
        self._running: bool = True
        self._connected: bool = False
        self.status_callback = status_callback
        self.reconnect_attempts: int = 0
        self.max_reconnect_attempts: int = 10
        self._forwarder = None

    def _update_status(self, connected: bool) -> None:
        """Updates the connection status and invokes the callback if provided.

        Args:
            connected: The new connection status.
        """
        if self._connected != connected:
            self._connected = connected
            if self.status_callback:
                try:
                    self.status_callback(connected)
                except Exception as e:
                    logging.error(f"Error in status callback: {e}")

    async def connect(self) -> None:
        """Establishes an SSH connection and sets up the SOCKS proxy.

        Raises:
            SSHConnectionError: If connection or proxy setup fails.
        """
        conn_params = None
        try:
            # Clean up any existing connection resources first
            await self._cleanup_connection()

            logging.info(f"Connecting to {self.config.user}@{self.config.host}:{self.config.port}")

            # Base connection parameters
            conn_params = {
                'host': self.config.host,
                'port': self.config.port,
                'username': self.config.user,
                'known_hosts': None
            }

            # Add keepalive parameters if they are non-zero
            if self.config.keepalive_interval != 0:
                conn_params['keepalive_interval'] = self.config.keepalive_interval

            if self.config.keepalive_count_max != 0:
                conn_params['keepalive_count_max'] = self.config.keepalive_count_max

            # Configure authentication
            if self.config.auth_method == 'password':
                try:
                    conn_params['password'] = decrypt_password(self.config.password, salt)
                except Exception as e:
                    logging.error(f"Failed to decrypt password: {e}")
                    raise SSHConnectionError("Password decryption failed")
            else:
                if not self.config.key_path:
                    raise SSHConnectionError("SSH key path not provided")
                conn_params['client_keys'] = [self.config.key_path]

            # Establish the connection with a timeout
            try:
                self.connection = await asyncio.wait_for(
                    asyncssh.connect(**conn_params),
                    timeout=10
                )
            except asyncio.TimeoutError:
                raise SSHConnectionError("Connection timed out")

            # Configure the SOCKS proxy
            try:
                self._forwarder = await self.connection.forward_socks(
                    listen_port=self.config.dynamic_port,
                    listen_host="localhost"
                )
            except Exception as e:
                raise SSHConnectionError(f"Failed to establish SOCKS proxy: {e}")

            self.reconnect_attempts = 0
            self._update_status(True)
            logging.info(f"SOCKS proxy established on localhost:{self.config.dynamic_port}")

            # Wait for the forwarder to close
            await self._forwarder.wait_closed()

        except (asyncssh.DisconnectError, OSError) as e:
            logging.error(f"Connection error: {e}")
            self._update_status(False)
            raise SSHConnectionError(f"Connection error: {e}")

        finally:
            # Remove sensitive data and clean up resources if not connected
            if conn_params and 'password' in conn_params:
                conn_params['password'] = None

            if not self._connected:
                await self._cleanup_connection()

    async def _cleanup_connection(self) -> None:
        """Cleans up existing connections and resources."""
        try:
            if self._forwarder:
                # Close the forwarder without checking is_closing()
                try:
                    self._forwarder.close()
                except Exception as e:
                    logging.error(f"Error closing forwarder: {e}")
                self._forwarder = None

            if self.connection:
                if not self.connection.is_closed():
                    self.connection.close()
                self.connection = None

            self._update_status(False)
        except Exception as e:
            logging.error(f"Error during connection cleanup: {e}")

    async def manage_connection(self) -> None:
        """Manages the connection and handles reconnection attempts.

        This method runs in a loop until stopped, handling connection
        maintenance and reconnection attempts when necessary.
        """
        while self._running:
            try:
                if not await self.is_connected():
                    self._update_status(False)
                    try:
                        await self.connect()
                        self.reconnect_attempts = 0
                    except SSHConnectionError as e:
                        self.reconnect_attempts += 1
                        logging.error(f"Reconnect attempt {self.reconnect_attempts}/{self.max_reconnect_attempts}: {e}")
                        if self.reconnect_attempts >= self.max_reconnect_attempts:
                            logging.error("Maximum reconnect attempts reached. Stopping client.")
                            self.stop()
                            return  # Exit the function completely

                        # Exponential backoff for reconnection attempts
                        backoff_time = min(5 * self.reconnect_attempts, 60)
                        logging.info(f"Waiting {backoff_time} seconds before next reconnection attempt")

                        # Check for stop signal every second during backoff
                        for _ in range(backoff_time):
                            if not self._running:
                                return  # Immediate exit if stopped
                            await asyncio.sleep(1)
                    except Exception as e:
                        logging.error(f"Unexpected error during connection management: {e}")
                        await asyncio.sleep(5)
                else:
                    # Check every second if we should stop while connected
                    for _ in range(10):  # Check every 10 seconds when connected
                        if not self._running:
                            return  # Immediate exit if stopped
                        await asyncio.sleep(1)
            except Exception as e:
                logging.error(f"Error in connection management loop: {e}")
                await asyncio.sleep(5)

    async def _check_socks_connection(self) -> bool:
        """Checks if the SOCKS proxy connection is working.

        Returns:
            True if the SOCKS proxy is functional, False otherwise.
        """
        if not self.config.test_url:
            logging.error("No test URL configured for SOCKS connection check")
            return False

        try:
            connector = ProxyConnector.from_url(f'socks5://localhost:{self.config.dynamic_port}')
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                        self.config.test_url,
                        timeout=aiohttp.ClientTimeout(total=self.config.test_timeout),
                        ssl=False if not self.config.test_url.startswith("https") else True
                ) as response:
                    is_successful = response.status == 200
                    logging.info(
                        f"SOCKS connection test {'succeeded' if is_successful else 'failed'}: {response.status}")
                    return is_successful
        except (aiohttp.ClientError, aiohttp.ClientConnectorError, asyncio.TimeoutError, OSError) as e:
            logging.error(f"SOCKS connection check failed: {e}")
            return False

    async def is_connected(self) -> bool:
        """Asynchronously checks the current connection status.

        Returns:
            True if the connection is active and the SOCKS proxy is working, False otherwise.
        """
        try:
            # Basic connection parameters check
            base_check = (
                    self.connection is not None and
                    not self.connection.is_closed() and
                    self._forwarder is not None
            )

            if not base_check:
                return False

            # Perform the asynchronous SOCKS connection check
            return await self._check_socks_connection()

        except Exception as e:
            logging.error(f"Connection status check failed: {e}")
            return False

    def stop(self) -> None:
        """Stops the client and closes the connection."""
        self._running = False
        if self._forwarder:
            self._forwarder.close()
            self._forwarder = None
        if self.connection:
            self.connection.close()
            self.connection = None
        self._update_status(False)

    async def shutdown(self) -> None:
        """Gracefully shuts down the client."""
        self.stop()
        if self.connection:
            await self.connection.wait_closed()
