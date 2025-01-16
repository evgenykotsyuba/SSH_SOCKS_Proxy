import os
import asyncio
import logging
import datetime
import threading
import signal
import sys
import argparse
import time

from concurrent.futures import ThreadPoolExecutor
from config import ConfigManager, SSHConfig
from ssh_client import SSHClient, SSHConnectionError
from socks_to_http_proxy import SOCKStoHTTPProxy
from password_encryption_decryption import encrypt_password, salt


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
        self.log_file = os.path.join(os.getcwd(), "log", f"socks_proxy_{datetime.date.today()}.log")

    def _setup_logging(self):
        """
        Set up logging configuration. Logs will only display warnings and errors.
        """
        log_dir = os.path.join(os.getcwd(), "log")
        os.makedirs(log_dir, exist_ok=True)

        logger = logging.getLogger()
        logger.setLevel(logging.WARNING)  # Set to WARNING to reduce output

        log_filename = os.path.join(log_dir, f"socks_proxy_{datetime.date.today()}.log")
        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
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

    def start_http_proxy(self):
        try:
            socks_port = self.config.dynamic_port
            http_port = self.config.http_proxy_port

            if not self._verify_socks_proxy(socks_port):
                raise RuntimeError(f"SOCKS proxy not running on port {socks_port}")

            def run_proxy():
                try:
                    self.http_proxy = SOCKStoHTTPProxy(
                        http_port=http_port,
                        socks_port=socks_port
                        # Remove bind_address and timeout parameters
                    )
                    self.http_proxy.start()
                except Exception as e:
                    logging.error(f"HTTP proxy thread error: {e}")
                    self.http_proxy = None
                    raise

            proxy_thread = threading.Thread(target=run_proxy, daemon=True)
            proxy_thread.start()

            time.sleep(1)
            if not self._verify_http_proxy(http_port):
                raise RuntimeError(f"HTTP proxy failed to start on port {http_port}")

            logging.info(f"HTTP Proxy successfully started on port {http_port}")
            print(f"HTTP Proxy successfully started on port {http_port}")
            return True

        except Exception as e:
            logging.error(f"Failed to start HTTP proxy: {e}")
            print(f"Failed to start HTTP proxy: {e}")
            if self.http_proxy:
                self.http_proxy.stop()
                self.http_proxy = None
            return False

    async def show_connection_status(self):
        """Display current connection status for SSH SOCKS and HTTP proxy"""
        print("\nConnection Status")
        print("================")

        # Check SSH SOCKS connection
        ssh_status = "Connected" if self.ssh_client and await self.ssh_client.is_connected() else "Not Connected"
        print(f"SSH SOCKS: {ssh_status}")

        # Check HTTP proxy connection
        # http_status = "Connected" if self.http_proxy and self.http_proxy.is_running() else "Not Connected"
        http_status = "Connected" if self.http_proxy else "Not Connected"
        print(f"HTTP proxy: {http_status}")

    def stop(self):
        if self.ssh_client:
            self.ssh_client.stop()
            self.ssh_client = None

        if self.http_proxy:
            self.http_proxy.stop()
            self.http_proxy = None

        # if self.traffic_monitor:
        #     self.traffic_monitor.stop_monitoring()
        #     self.traffic_running = False

        if self.loop and not self.loop.is_closed():
            self.loop.stop()
            self.loop.close()

        logging.info("All services stopped")
        print("All services stopped")

    def _run_async_task(self, task, *args):
        """
        Run an async task in a separate thread to prevent blocking.
        """

        def run_in_thread():
            asyncio.run(task(*args))

        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()
        thread.join()  # Wait for the task to finish

    def show_menu(self):
        while True:
            if not self.monitor_running:  # Если мониторинг неактивен, отображаем главное меню
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
                    self.start_http_proxy()
                elif choice == "5":
                    if self.http_proxy:
                        self.http_proxy.stop()
                        self.http_proxy = None
                        logging.warning("HTTP Proxy stopped.")
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

            if not self.monitor_running:  # Только в обычном режиме ждём Enter
                input("\nPress Enter to continue...")

    async def start_services(self, connect_http=False):
        """Start services based on command line arguments"""
        if connect_http:
            # First establish SSH connection
            await self.connect()

            # If SSH connection is successful, start HTTP proxy
            if self.ssh_client and await self.ssh_client.is_connected():
                # Give some time for SSH connection to stabilize
                await asyncio.sleep(2)
                # Run HTTP proxy in a separate thread with proper synchronization
                with ThreadPoolExecutor() as executor:
                    await asyncio.get_event_loop().run_in_executor(
                        executor, self.start_http_proxy
                    )
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
    """Асинхронная функция для запуска сервисов"""
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
