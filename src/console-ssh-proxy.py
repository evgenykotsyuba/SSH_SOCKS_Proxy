import os
import asyncio
import logging
from datetime import date
import threading
import socket
import signal
import sys
import argparse
import time

from concurrent.futures import ThreadPoolExecutor
from config import ConfigManager, SSHConfig
from ssh_client import SSHClient, SSHConnectionError
from socks_to_http_proxy import SOCKStoHTTPProxy
from password_encryption_decryption import encrypt_password, salt
from logging_handler import ColoredFormatter


class ConsoleSSHProxy:
    def __init__(self):
        self.config = ConfigManager.load_config()
        self.ssh_client = None
        self.http_proxy = None
        self.traffic_monitor = None
        self.monitor_thread = None
        self.monitor_running = False
        self.traffic_running = False
        self.loop = None
        self._setup_logging()
        self._setup_signal_handlers()
        self.log_file = os.path.join(os.getcwd(), "log", f"socks_proxy_{date.today()}.log")

    def _setup_logging(self):
        """
        Configure logging with:
        - Colored console output (WARNING level and above)
        - File logging (INFO level and above)
        """
        # Create log directory if it doesn't exist
        log_dir = os.path.join(os.getcwd(), "log")
        os.makedirs(log_dir, exist_ok=True)

        # Get the root logger
        logger = logging.getLogger()
        # Clear any existing handlers to avoid duplication
        logger.handlers.clear()
        # Set root logger to lowest level used (INFO)
        logger.setLevel(logging.INFO)

        # Console Handler (WARNING and above)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_formatter = ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File Handler (INFO and above)
        log_filename = os.path.join(log_dir, f"socks_proxy_{date.today()}.log")
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    def _setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        print("\nShutting down gracefully...")
        self.stop()
        sys.exit(0)

    def show_logs(self):
        """Display logs and provide options to return to main menu"""
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("\nLog Viewer")
            print("==========")
            print("1. View latest logs")
            print("2. View all logs")
            print("3. Return to main menu")

            choice = input("\nEnter your choice (1-3): ")

            if choice == "1":
                try:
                    # Read last 20 lines of the log file
                    with open(self.log_file, 'r') as f:
                        lines = f.readlines()
                        print("\nLatest logs:")
                        print("============")
                        for line in lines[-20:]:
                            print(line.strip())
                except FileNotFoundError:
                    print("No log file found.")

                input("\nPress Enter to continue...")

            elif choice == "2":
                try:
                    # Read all logs
                    with open(self.log_file, 'r') as f:
                        print("\nFull logs:")
                        print("==========")
                        print(f.read())
                except FileNotFoundError:
                    print("No log file found.")

                input("\nPress Enter to continue...")

            elif choice == "3":
                return

            else:
                print("Invalid choice. Please try again.")

    def configure(self):
        print("\nSSH Proxy Configuration")
        print("=====================")

        config_dict = {
            'connection_name': input("Connection Name [Default]: ") or 'Default',
            'host': input("SSH Server: "),
            'port': int(input("SSH Port [22]: ") or "22"),
            'user': input("Username: "),
            'dynamic_port': int(input("SOCKS Port [1080]: ") or "1080"),
            'keepalive_interval': int(input("Keepalive interval [60]: ") or "60"),
            'keepalive_count_max': int(input("Keepalive count MAX [120]: ") or "120"),
            'test_url': input("Test SOCKS URL [https://example.com]: ") or 'https://example.com',
            'http_proxy_port': int(input("HTTP Proxy Port [8080]: ") or "8080"),
        }

        auth_method = input("Authentication Method (password/key) [password]: ") or "password"
        config_dict['auth_method'] = auth_method

        if auth_method == "password":
            import getpass
            password = getpass.getpass("Password: ")
            encrypted_password = encrypt_password(password, salt)
            config_dict['password'] = encrypted_password.decode('utf-8')
            config_dict['key_path'] = None
        else:
            key_path = input("SSH Key Path: ")
            if not os.path.exists(key_path):
                raise FileNotFoundError("SSH Key file does not exist.")
            config_dict['key_path'] = key_path
            config_dict['password'] = None

        self.config = SSHConfig(**config_dict)
        ConfigManager.save_config(self.config)
        logging.info("Configuration saved successfully!")
        print("Configuration saved successfully!")

    async def connect(self):
        try:
            self.ssh_client = SSHClient(self.config)
            await self.ssh_client.manage_connection()
            print("Connected successfully!")
        except SSHConnectionError as e:
            logging.error(f"SSH connection error: {e}")
            print(f"Connection error: {e}")
        except Exception as e:
            logging.error(f"Unexpected error during connection: {e}")
            print(f"Unexpected error: {e}")

    def _is_port_available(self, port):
        """Check if a port is available for binding."""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return True
        except OSError:
            return False

    async def start_http_proxy(self):
        """Asynchronous HTTP proxy start with improved error handling"""
        try:
            socks_port = self.config.dynamic_port
            http_port = self.config.http_proxy_port

            # Check SOCKS proxy availability
            logging.info(f"[HTTP Proxy] Checking SOCKS proxy (port {socks_port})...")
            if not await self._async_verify_socks_proxy(socks_port, retries=10, delay=2):
                raise RuntimeError(f"SOCKS proxy is not available on port {socks_port}")

            # Check if HTTP port is busy
            logging.info(f"[HTTP Proxy] Checking port {http_port}...")
            if not await self._async_is_port_available(http_port):
                raise RuntimeError(f"Port {http_port} is busy")

            # Initialize HTTP proxy
            try:
                self.http_proxy = SOCKStoHTTPProxy(
                    http_port=http_port,
                    socks_port=socks_port
                )
                logging.info("[HTTP Proxy] Starting server...")
                await asyncio.to_thread(self.http_proxy.start)
            except Exception as e:
                logging.error(f"[HTTP Proxy] Start error: {str(e)}", exc_info=True)
                raise

            # Wait for initialization
            logging.info("[HTTP Proxy] Waiting for initialization (5 sec)...")
            await asyncio.sleep(5)

            # Check functionality
            logging.info("[HTTP Proxy] Checking functionality...")
            if not await self._async_verify_http_proxy(http_port, retries=10, delay=2):
                raise RuntimeError("HTTP proxy is not responding")

            logging.info(f"[HTTP Proxy] Successfully started on port {http_port}")
            print(f"HTTP proxy: port {http_port}")
            return True

        except Exception as e:
            logging.error(f"[HTTP Proxy] Critical error: {str(e)}", exc_info=True)
            if self.http_proxy:
                await asyncio.to_thread(self.http_proxy.stop)
                self.http_proxy = None
            return False

    async def _async_verify_http_proxy(self, port, retries=10, delay=2):
        """Verification with increased number of attempts"""
        for i in range(retries):
            logging.info(f"HTTP proxy check attempt #{i + 1}")
            if await self._async_check_port(port):
                return True
            await asyncio.sleep(delay)
        return False

    async def _async_verify_socks_proxy(self, port, retries=10, delay=2):
        """Verification with increased number of attempts"""
        for i in range(retries):
            logging.info(f"SOCKS check #{i + 1}")
            if await self._async_check_port(port):
                return True
            await asyncio.sleep(delay)
        return False

    async def _async_is_port_available(self, port):
        """Asynchronous port availability check"""
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, self._check_port_availability, port)
            return True
        except OSError:
            return False

    def _check_port_availability(self, port):
        """Synchronous port check"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(('127.0.0.1', port))
                return True
            except OSError:
                return False

    async def _async_verify_http_proxy(self, port, retries=3, delay=1):
        """Asynchronous HTTP proxy verification"""
        for _ in range(retries):
            if await self._async_check_port(port):
                return True
            await asyncio.sleep(delay)
        return False

    async def _async_check_port(self, port):
        """Asynchronous port connection check"""
        loop = asyncio.get_event_loop()
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection('127.0.0.1', port),
                timeout=2
            )
            writer.close()
            await writer.wait_closed()
            return True
        except (ConnectionRefusedError, asyncio.TimeoutError):
            return False

    async def show_connection_status(self):
        """Display current connection status for SSH SOCKS and HTTP proxy"""
        print("\nConnection Status")
        print("================")

        # Check SSH SOCKS connection
        ssh_status = "Connected" if self.ssh_client and await self.ssh_client.is_connected() else "Not Connected"
        print(f"SSH SOCKS: {ssh_status}")

        # Check HTTP proxy connection
        http_status = "Connected" if self.http_proxy else "Not Connected"
        print(f"HTTP proxy: {http_status}")

    def stop(self):
        if self.ssh_client:
            self.ssh_client.stop()
            self.ssh_client = None
            logging.info("SOCKS Proxy stopped.")
            print("SOCKS Proxy stopped.")

        if self.http_proxy:
            self.http_proxy.stop()
            self.http_proxy = None
            logging.info("HTTP Proxy stopped.")
            print("HTTP Proxy stopped.")

        if self.loop and not self.loop.is_closed():
            self.loop.stop()
            self.loop.close()

        logging.info("All services stopped")
        print("All services stopped")

    def _run_async_task(self, task, *args):
        """Run async task without blocking the main thread"""

        def run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(task(*args))

        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()
        # Removed thread.join() to avoid blocking

    def show_menu(self):
        while True:
            if not self.monitor_running:
                os.system('cls' if os.name == 'nt' else 'clear')
                print("\nSSH Proxy Menu")
                print("=============")
                print("1. Configure")
                print("2. Connect")
                print("3. Disconnect")
                print("4. Start HTTP Proxy")
                print("5. Stop HTTP Proxy")
                print("6. Connection Status")
                print("7. Show Traffic Monitor")
                print("8. Show Logs")
                print("9. Exit")

            choice = input("\nEnter your choice (1-9): ")

            try:
                if choice == "1":
                    self.configure()
                elif choice == "2":
                    threading.Thread(target=self._run_async_task, args=(self.connect,), daemon=True).start()
                elif choice == "3":
                    self.stop()
                elif choice == "4":
                    self._run_async_task(self.start_http_proxy)
                elif choice == "5":
                    if self.http_proxy:
                        self.http_proxy.stop()
                        self.http_proxy = None
                elif choice == "6":
                    self._run_async_task(self.show_connection_status)
                elif choice == "7":
                    pass
                elif choice == "8":
                    self.show_logs()
                elif choice == "9":
                    self.stop()
                    break
                else:
                    print("Invalid choice. Please try again.")
            except Exception as e:
                logging.error(f"An error occurred: {e}")
                print(f"An error occurred: {e}")

            if not self.monitor_running:
                input("\nPress Enter to continue...")

    async def start_services(self, connect_http=False):
        if connect_http:
            await self.connect()
            if self.ssh_client and await self.ssh_client.is_connected():
                # Increase wait time to 5 seconds
                await asyncio.sleep(5)

                # Start HTTP proxy
                if not await self.start_http_proxy():
                    logging.error("HTTP proxy failed to start")
                    return

                # Infinite loop to keep services running
                while True:
                    await asyncio.sleep(1)
            else:
                logging.error("Cannot start HTTP proxy: SSH connection not established")
                print("Cannot start HTTP proxy: SSH connection not established")

    def _verify_socks_proxy(self, port):
        """Verify SOCKS proxy is running and accepting connections"""
        import socket
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=2):
                return True
        except (socket.timeout, ConnectionRefusedError):
            return False

    def _verify_http_proxy(self, port):
        """Verify HTTP proxy is running and accepting connections"""
        import socket
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=2):
                return True
        except (socket.timeout, ConnectionRefusedError):
            return False


def parse_arguments():
    parser = argparse.ArgumentParser(description='SSH SOCKS and HTTP Proxy Manager')
    parser.add_argument('--connect-http', action='store_true',
                       help='Start SSH connection and HTTP proxy together')
    parser.add_argument('--interactive', action='store_true',
                       help='Start in interactive menu mode')
    return parser.parse_args()


async def run_services(proxy, args):
    """Asynchronous function for running services"""
    try:
        await proxy.start_services(connect_http=args.connect_http)

        # Keep the program running while services are active
        while True:
            if proxy.ssh_client or proxy.http_proxy:
                await asyncio.sleep(1)
            else:
                break
    except asyncio.CancelledError:
        # Proper handling of task cancellation
        if proxy.ssh_client:
            await proxy.ssh_client.stop()
        if proxy.http_proxy:
            proxy.http_proxy.stop()
        raise


def main():
    args = parse_arguments()
    proxy = ConsoleSSHProxy()

    if len(sys.argv) == 1 or args.interactive:
        proxy.show_menu()
    else:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            print("\nStarting services. Press Ctrl+C to exit.")

            # Create and run the main task
            main_task = loop.create_task(run_services(proxy, args))

            try:
                loop.run_until_complete(main_task)
            except KeyboardInterrupt:
                print("\nShutting down...")
                # Cancel the main task
                main_task.cancel()
                # Wait for all tasks to complete
                loop.run_until_complete(asyncio.gather(main_task, return_exceptions=True))

            # Exit if no services are running
            if not (proxy.ssh_client or proxy.http_proxy):
                print("No services are running. Exiting...")
                proxy.stop()

        finally:
            try:
                # Cancel remaining tasks
                remaining_tasks = asyncio.all_tasks(loop)
                for task in remaining_tasks:
                    task.cancel()
                # Wait for all remaining tasks to complete
                loop.run_until_complete(asyncio.gather(*remaining_tasks, return_exceptions=True))
            finally:
                if loop and not loop.is_closed():
                    loop.close()


if __name__ == "__main__":
    main()
