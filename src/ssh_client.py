import asyncio
import asyncssh
import logging
from typing import Optional, Callable


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
        self.max_reconnect_attempts = 10  # Maximum number of reconnection attempts.

    def _update_status(self, connected: bool):
        """Updates the connection status and invokes the callback if provided."""
        if self._connected != connected:
            self._connected = connected
            if self.status_callback:
                self.status_callback(connected)

    async def connect(self):
        """Establishes an SSH connection and configures the SOCKS proxy."""
        try:
            logging.info(f"Connecting to {self.config.user}@{self.config.host}")
            conn_params = {
                'host': self.config.host,
                'port': self.config.port,
                'username': self.config.user,
                'known_hosts': None
            }

            if self.config.auth_method == 'password':
                conn_params['password'] = self.config.password
            else:
                conn_params['client_keys'] = [self.config.key_path]

            # Setting a timeout using asyncio.wait_for
            self.connection = await asyncio.wait_for(
                asyncssh.connect(**conn_params),
                timeout=10  # Timeout in seconds
            )
            self.reconnect_attempts = 0  # Reset reconnection attempts on successful connection.
            self._update_status(True)

            async with self.connection.forward_socks(
                    listen_port=self.config.dynamic_port,
                    listen_host="localhost"
            ) as forwarder:
                logging.info(f"SOCKS proxy on localhost:{self.config.dynamic_port}")
                await forwarder.wait_closed()

        except asyncio.TimeoutError:
            logging.error("Connection timed out")
            self._update_status(False)
            raise SSHConnectionError("Connection timed out")
        except (asyncssh.DisconnectError, OSError) as e:
            logging.error(f"Connection error: {e}")
            self._update_status(False)
            raise SSHConnectionError(f"Connection error: {e}")
        finally:
            if self.connection:
                self.connection.close()

    async def manage_connection(self):
        """Manages the connection and handles reconnection attempts."""
        while self._running:
            if not self._connected:
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
                # Periodic state check.
                self._update_status(self.is_connected())
                await asyncio.sleep(2)

    def is_connected(self) -> bool:
        """Checks the current connection status."""
        return self.connection is not None and not self.connection.is_closed()

    def stop(self):
        """Stops the client and closes the connection."""
        self._running = False
        self._update_status(False)
        if self.connection:
            self.connection.close()
