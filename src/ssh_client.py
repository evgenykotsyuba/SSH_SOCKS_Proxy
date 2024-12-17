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

    async def connect(self):
        """Establishes an SSH connection and configures the SOCKS proxy."""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None

            logging.info(f"Connecting to {self.config.user}@{self.config.host}")
            conn_params = {
                'host': self.config.host,
                'port': self.config.port,
                'username': self.config.user,
                'known_hosts': None
            }

            if self.config.auth_method == 'password':
                dencrypted_password = decrypt_password(self.config.password, salt)
                conn_params['password'] = dencrypted_password
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
            if self._forwarder:
                self._forwarder.close()
                self._forwarder = None
            if self.connection:
                self.connection.close()
                self.connection = None
            self._update_status(False)

    async def manage_connection(self):
        """Manages the connection and handles reconnection attempts."""
        while self._running:
            try:
                if not self.is_connected():
                    self._update_status(False)
                    try:
                        await self.connect()
                    except SSHConnectionError as e:
                        self.reconnect_attempts += 1
                        logging.error(f"Attempt {self.reconnect_attempts}/{self.max_reconnect_attempts}: {e}")
                        if self.reconnect_attempts >= self.max_reconnect_attempts:
                            logging.error("Maximum reconnect attempts reached. Stopping client.")
                            self.stop()
                            break
                        await asyncio.sleep(5)
                    except Exception as e:
                        logging.error(f"Unexpected error: {e}")
                        await asyncio.sleep(10)
                else:
                    # Периодическая проверка состояния
                    await asyncio.sleep(2)
            except Exception as e:
                logging.error(f"Error in connection management: {e}")
                await asyncio.sleep(5)

    async def _check_socks_connection(self) -> bool:
        try:
            # Create a SOCKS proxy connector
            connector = ProxyConnector.from_url(f'socks5://localhost:{self.config.dynamic_port}')

            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                        f'{self.config.test_url}',
                        timeout=5,
                        ssl=True
                ) as response:
                    # Check the response status
                    return response.status == 200

        except (
                aiohttp.ClientError,
                aiohttp.ClientConnectorError,
                asyncio.TimeoutError
        ) as e:
            logging.error(f"SOCKS connection check failed: {e}")
            return False
        finally:
            # Close the connector if it is open
            if 'connector' in locals():
                await connector.close()

    def is_connected(self) -> bool:
        try:
            # Basic connection parameters check
            base_check = (
                    self.connection is not None and
                    not self.connection.is_closed() and
                    self._forwarder is not None
            )

            # If the basic check fails, return False
            if not base_check:
                return False

            # Synchronous start of asynchronous check
            return asyncio.run(self._check_socks_connection())

        except Exception as e:
            logging.error(f"Connection status check failed: {e}")
            return False

    def stop(self):
        """Stops the client and closes the connection."""
        self._running = False
        if self._forwarder:
            self._forwarder.close()
            self._forwarder = None
        if self.connection:
            self.connection.close()
            self.connection = None
        self._update_status(False)