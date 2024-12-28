import asyncio
import asyncssh
import aiohttp
import logging
from typing import Optional, Callable
from aiohttp_socks import ProxyConnector
from password_encryption_decryption import decrypt_password, salt


class SSHConnectionError(Exception):
    """Custom exception for SSH connection errors."""
    pass


class SSHClient:
    def __init__(self, config, status_callback: Optional[Callable[[bool], None]] = None):
        if not hasattr(config, 'host') or not hasattr(config, 'port'):
            raise ValueError("Invalid config: missing required attributes")
        self.config = config
        self.connection: Optional[asyncssh.SSHClientConnection] = None
        self._running = True
        self._connected = False
        self.status_callback = status_callback
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self._forwarder = None

    def _update_status(self, connected: bool):
        """Updates the connection status and invokes the callback if provided."""
        if self._connected != connected:
            self._connected = connected
            if self.status_callback:
                try:
                    self.status_callback(connected)
                except Exception as e:
                    logging.error(f"Error in status callback: {e}")

    async def connect(self) -> None:
        """Establishes an SSH connection and configures the SOCKS proxy."""
        try:
            if self._forwarder:
                self._forwarder.close()
                self._forwarder = None

            if self.connection:
                self.connection.close()
                self.connection = None

            logging.info(f"Connecting to {self.config.user}@{self.config.host}")
            conn_params = {
                'host': self.config.host,
                'port': self.config.port,
                'username': self.config.user,
                'known_hosts': None,
                'keepalive_interval': 60,  # ServerAliveInterval
                'keepalive_count_max': 120  # ServerAliveCountMax
            }

            if self.config.auth_method == 'password':
                decrypted_password = decrypt_password(self.config.password, salt)
                conn_params['password'] = decrypted_password
            else:
                conn_params['client_keys'] = [self.config.key_path]

            self.connection = await asyncio.wait_for(
                asyncssh.connect(**conn_params),
                timeout=10
            )

            self._forwarder = await self.connection.forward_socks(
                listen_port=self.config.dynamic_port,
                listen_host="localhost"
            )

            self.reconnect_attempts = 0
            self._update_status(True)
            logging.info(f"SOCKS proxy established on localhost:{self.config.dynamic_port}")

            # Ждем закрытия форвардера
            await self._forwarder.wait_closed()

        except asyncio.TimeoutError:
            logging.error("Connection timed out")
            self._update_status(False)
            raise SSHConnectionError("Connection timed out")
        except (asyncssh.DisconnectError, OSError) as e:
            logging.error(f"Connection error: {e}")
            self._update_status(False)
            raise SSHConnectionError(f"Connection error: {e}")
        finally:
            if 'password' in conn_params:
                conn_params['password'] = None
            if self._forwarder and not self._forwarder.is_closing():
                self._forwarder.close()
            if self.connection and not self.connection.is_closed():
                self.connection.close()
            logging.info(f"Disconnected from {self.config.host}")
            self._update_status(False)

    async def manage_connection(self) -> None:
        """Manage the connection and handle reconnection attempts."""
        while self._running:
            try:
                if not await self.is_connected():  # Await now valid
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
                            break
                        await asyncio.sleep(min(5 * self.reconnect_attempts, 60))  # Exponential backoff
                    except Exception as e:
                        logging.error(f"Unexpected error during connection management: {e}")
                        await asyncio.sleep(50)
                else:
                    await asyncio.sleep(100)  # Increased interval for periodic checks
            except Exception as e:
                logging.error(f"Error in connection management loop: {e}")
                await asyncio.sleep(5)

    async def _check_socks_connection(self) -> bool:
        """Check if the SOCKS proxy connection is working."""
        if not self.config.test_url:
            logging.error("No test URL configured for SOCKS connection check")
            return False

        try:
            async with ProxyConnector.from_url(f'socks5://localhost:{self.config.dynamic_port}') as connector:
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(
                            self.config.test_url,
                            timeout=self.config.test_timeout if hasattr(self.config, 'test_timeout') else 5,
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
        """Asynchronously checks the current connection status."""
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

    async def shutdown(self):
        """Gracefully shut down the client."""
        self.stop()
        if self.connection:
            await self.connection.wait_closed()

