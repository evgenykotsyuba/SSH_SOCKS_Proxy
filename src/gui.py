import os
import tkinter as tk
import traceback
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import queue
import logging
import asyncio

from config import ConfigManager, SSHConfig
from ssh_client import SSHClient, SSHConnectionError
from chrome import chrome_browser
from socks_to_http_proxy import SOCKStoHTTPProxy


class LogHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        log_entry = self.format(record)
        self.log_queue.put(log_entry)


class SSHProxyGUI:
    def __init__(self, root):
        self.root = root
        self.config = ConfigManager.load_config()

        # Initialize the title dynamically
        self._update_window_title()

        self.root.geometry("700x500")

        self.log_queue = queue.Queue()
        self.ssh_client = None
        self.connection_thread = None

        self._setup_logging()
        self._create_gui()
        self._check_log_queue()

    def _update_window_title(self):
        """Update the window title based on connection status and configuration."""
        connection_name = getattr(self.config, 'connection_name', None) or "Default"
        self.root.title(f"SSH SOCKS Proxy - {connection_name}")

    def _setup_logging(self):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        handler = LogHandler(self.log_queue)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    def _create_gui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        self.connect_btn = ttk.Button(btn_frame, text="Connect", command=self._start_connection)
        self.connect_btn.pack(side=tk.LEFT, padx=5)

        self.disconnect_btn = ttk.Button(btn_frame, text="Disconnect", command=self._stop_connection, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)

        self.settings_btn = ttk.Button(btn_frame, text="Settings", command=self._show_settings)
        self.settings_btn.pack(side=tk.LEFT, padx=5)

        self.chrome_btn = ttk.Button(btn_frame, text="Chrome", command=self._run_chrome_browser, state=tk.DISABLED)
        self.chrome_btn.pack(side=tk.LEFT, padx=5)

        self.http_proxy_btn = ttk.Button(btn_frame, text="HTTP Proxy", command=self._run_http_proxy, state=tk.DISABLED)
        self.http_proxy_btn.pack(side=tk.LEFT, padx=5)

        self.help_btn = ttk.Button(btn_frame, text="Help", command=self._show_help)
        self.help_btn.pack(side=tk.LEFT, padx=5)

        # Log display
        log_frame = ttk.LabelFrame(main_frame, text="Logs")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_display = scrolledtext.ScrolledText(log_frame, height=20, wrap=tk.WORD)
        self.log_display.pack(fill=tk.BOTH, expand=True)
        self.log_display.config(state=tk.DISABLED)

        # Status bar with connection indicator
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=5)

        # Status text
        self.status_var = tk.StringVar(value="Not Connected")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_label.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        # Connection status indicator canvas
        self.status_canvas = tk.Canvas(status_frame, width=20, height=20, highlightthickness=0,
                                       background=self.root.winfo_toplevel().cget('background'))
        self.status_canvas.pack(side=tk.RIGHT, padx=5)

        # Initial status indicator
        self._draw_connection_indicator(False)

        # Start periodic status monitoring
        self._check_connection_status()

    def _draw_connection_indicator(self, connected: bool):
        """Draw a round indicator showing connection status."""
        self.status_canvas.delete("all")
        color = "green" if connected else "red"
        self.status_canvas.create_oval(3, 3, 17, 17, fill=color, outline=color)

    def _start_connection(self):
        # Validation logic
        if not all([self.config.host, self.config.user]):
            messagebox.showerror("Error", "Missing SSH configuration")
            return

        self.connect_btn.config(state=tk.DISABLED)
        self.disconnect_btn.config(state=tk.NORMAL)
        self.settings_btn.config(state=tk.DISABLED)
        self.chrome_btn.config(state=tk.NORMAL)
        self.http_proxy_btn.config(state=tk.NORMAL)

        self.connection_thread = threading.Thread(target=self._run_connection, daemon=True)
        self.connection_thread.start()

    def _run_connection(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            self.ssh_client = SSHClient(self.config, status_callback=self._update_connection_status)
            loop.run_until_complete(self.ssh_client.manage_connection())
        except SSHConnectionError as e:
            logging.error(str(e))
        finally:
            loop.close()
            self._update_gui_state(connected=False)

    def _check_connection_status(self):
        """Periodically checks the connection status."""
        if self.ssh_client:
            self._update_connection_status(self.ssh_client.is_connected())
        self.root.after(2000, self._check_connection_status)  # Check every 2 seconds

    def _update_connection_status(self, connected: bool):
        """Updates the connection status in the GUI."""
        self._update_gui_state(connected)

    def _stop_connection(self):
        if self.ssh_client:
            self._close_chrome_browser()
            self.chrome_btn.config(state=tk.DISABLED)
            self._close_http_proxy()
            self.http_proxy_btn.config(state=tk.DISABLED)
            self.ssh_client.stop()

    def _show_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("430x390")
        settings_window.transient(self.root)
        settings_window.grab_set()

        settings_frame = ttk.Frame(settings_window, padding="10")
        settings_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Basic fields
        basic_fields = [
            ("CONNECTION_NAME", "Connection Name:"),
            ("SSH_HOST", "SSH Server:"),
            ("SSH_PORT", "SSH Port:"),
            ("SSH_USER", "Username:"),
            ("DYNAMIC_PORT", "SOCKS Port:"),
            ("TEST_URL", "Test SOCKS URL:"),
            ("HTTP_PROXY_PORT", "HTTP Proxy Port:"),
            ("USER_AGENT", "Browser User-Agent"),
            ("HOME_PAGE", "Browser Home Page"),
        ]

        self.settings_vars = {}

        # Authentication method selection
        ttk.Label(settings_frame, text="Authentication Method:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.auth_method_var = tk.StringVar(value=os.getenv("AUTH_METHOD", "password"))
        auth_frame = ttk.Frame(settings_frame)
        auth_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)

        self.password_radio = ttk.Radiobutton(auth_frame, text="Password", variable=self.auth_method_var,
                                              value="password", command=self.toggle_auth_method)
        self.password_radio.pack(side=tk.LEFT)

        self.key_radio = ttk.Radiobutton(auth_frame, text="SSH Key", variable=self.auth_method_var,
                                         value="key", command=self.toggle_auth_method)
        self.key_radio.pack(side=tk.LEFT)

        # Add basic fields
        for i, (key, label) in enumerate(basic_fields, start=1):
            ttk.Label(settings_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=2)
            var = tk.StringVar(value=os.getenv(key, ""))
            self.settings_vars[key] = var
            entry = ttk.Entry(settings_frame, textvariable=var)
            entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=2)

        # Password field
        self.password_label = ttk.Label(settings_frame, text="Password:")
        self.password_label.grid(row=len(basic_fields) + 1, column=0, sticky=tk.W, pady=2)
        self.password_var = tk.StringVar(value=os.getenv("SSH_PASSWORD", ""))
        self.password_entry = ttk.Entry(settings_frame, textvariable=self.password_var, show="*")
        self.password_entry.grid(row=len(basic_fields) + 1, column=1, sticky=(tk.W, tk.E), pady=2)

        # SSH Key field
        self.key_label = ttk.Label(settings_frame, text="SSH Key:")
        self.key_label.grid(row=len(basic_fields) + 2, column=0, sticky=tk.W, pady=2)

        key_frame = ttk.Frame(settings_frame)
        key_frame.grid(row=len(basic_fields) + 2, column=1, sticky=(tk.W, tk.E), pady=2)

        self.key_var = tk.StringVar(value=os.getenv("SSH_KEY_PATH", ""))
        self.key_entry = ttk.Entry(key_frame, textvariable=self.key_var)
        self.key_entry.grid(column=0, row=0, sticky=(tk.W, tk.E), padx=(0, 5))

        self.browse_btn = ttk.Button(key_frame, text="Browse", command=self.browse_key)
        self.browse_btn.grid(column=1, row=0, sticky=tk.E)

        # Flexibility settings
        key_frame.columnconfigure(0, weight=1)
        key_frame.columnconfigure(1, weight=0)

        # Save button
        ttk.Button(settings_frame, text="Save", command=lambda: self.save_settings(settings_window)).grid(
            row=len(basic_fields) + 3, column=0, columnspan=2, pady=10)

        # Initialize auth method visibility
        self.toggle_auth_method()

    def _run_http_proxy(self):
        try:
            socks_port = self.config.dynamic_port  # Extract the SOCKS port from the configuration
            http_port = self.config.http_proxy_port  # Extract the HTTP proxy port from the configuration

            def start_http_proxy():
                # Create and start the HTTP proxy
                proxy = SOCKStoHTTPProxy(http_port=http_port, socks_port=socks_port)
                proxy.start()  # Start the proxy server

            # Start the proxy server in a separate thread to allow asynchronous operation
            threading.Thread(target=start_http_proxy, daemon=True).start()

            logging.info(f"HTTP Proxy started on port {http_port} with SOCKS Proxy connection on port {socks_port}")

            # Enable the button to disconnect the proxy
            self.http_proxy_btn.config(text="Disconnect Proxy", command=self._close_http_proxy())

        except ValueError as e:
            logging.error(f"Error starting the HTTP Proxy: {e}")
        except Exception as e:
            logging.error(f"Unknown error: {e}")

    def _close_http_proxy(self):
        """Disconnect HTTP Proxy."""
        try:
            # Отключаем кнопку для предотвращения повторных нажатий
            self.http_proxy_btn.config(state=tk.DISABLED)

            # Останавливаем прокси-сервер, если он существует
            if hasattr(self, 'proxy'):
                try:
                    # Установка флага остановки
                    self.proxy._stop_event.set()

                    # Попытка остановки прокси-сервера
                    self.proxy.stop()

                    logging.info("HTTP Proxy disconnected successfully.")
                except Exception as e:
                    logging.error(f"Error stopping HTTP Proxy: {e}")
                    logging.error(traceback.format_exc())

                # Удаление ссылки на прокси
                del self.proxy

            # Восстановление состояния кнопки
            self.http_proxy_btn.config(
                text="HTTP Proxy",
                command=self._run_http_proxy,
                state=tk.NORMAL
            )

        except Exception as e:
            logging.error(f"Error during HTTP Proxy disconnection: {e}")
            logging.error(traceback.format_exc())

            # Гарантированное восстановление состояния кнопки
            self.http_proxy_btn.config(
                text="HTTP Proxy",
                command=self._run_http_proxy,
                state=tk.NORMAL
            )

    def _run_chrome_browser(self):
        """Starting Chrome browser with proxy settings."""
        try:
            socks_port = self.config.dynamic_port
            user_agent = self.config.user_agent
            home_page = self.config.home_page

            # Launching the browser in a separate thread
            def start_browser():
                try:
                    custom_title = self.config.connection_name + ': ' + self.config.home_page.replace("https://", "")
                    self.browser_driver = chrome_browser(socks_port, user_agent, home_page, custom_title)
                except Exception as e:
                    logging.error(f"Error launching Chrome browser: {e}")
                    messagebox.showerror("Error", f"Failed to launch Chrome: {str(e)}")

            self.chrome_thread = threading.Thread(target=start_browser, daemon=True)
            self.chrome_thread.start()

            # Enable the button to close the browser
            self.chrome_btn.config(text="Close Chrome", command=self._close_chrome_browser)
        except Exception as e:
            logging.error(f"Error in Chrome browser launch: {e}")
            messagebox.showerror("Error", f"Failed to start Chrome: {str(e)}")

    def _close_chrome_browser(self):
        """Closing Chrome Browser."""
        try:
            if hasattr(self, 'browser_driver') and self.browser_driver:
                self.browser_driver.quit()
                self.browser_driver = None
                logging.info("Chrome browser closed.")

            if hasattr(self, 'chrome_thread') and self.chrome_thread.is_alive():
                self.chrome_thread.join(timeout=1)

            # Return the button to its original state
            self.chrome_btn.config(text="Chrome", command=self._run_chrome_browser)
        except Exception as e:
            logging.error(f"Error closing Chrome browser: {e}")
            messagebox.showerror("Error", f"Failed to close Chrome: {str(e)}")

    def _show_help(self):
        """Displays the content of info.md in a new help window."""
        try:
            # Load the content of info.md
            with open("info.md", "r", encoding="utf-8") as help_file:
                help_content = help_file.read()

            # Create a new window
            help_window = tk.Toplevel(self.root)
            help_window.title("Help")
            help_window.geometry("600x400")  # Adjusted size for better readability
            help_window.transient(self.root)
            help_window.grab_set()

            # Create a frame for the help text
            text_frame = ttk.Frame(help_window, padding="10")
            text_frame.pack(fill=tk.BOTH, expand=True)

            # Create a scrollable text widget to display the help content
            help_text = scrolledtext.ScrolledText(
                text_frame,
                wrap=tk.WORD,
                font=("Arial", 10),
                state=tk.NORMAL,
            )
            help_text.insert(tk.END, help_content)
            help_text.config(state=tk.DISABLED)  # Make the text read-only
            help_text.pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            logging.error(f"Failed to load help content: {e}")
            messagebox.showerror("Error", f"Could not load help content:\n{e}")

    def toggle_auth_method(self):
        """Toggle visibility of authentication method fields."""
        if self.auth_method_var.get() == "password":
            self.password_entry.grid()
            self.password_label.grid()
            self.key_entry.grid_remove()
            self.key_label.grid_remove()
            self.browse_btn.grid_remove()
        else:
            self.password_entry.grid_remove()
            self.password_label.grid_remove()
            self.key_entry.grid()
            self.key_label.grid()
            self.browse_btn.grid()

    def browse_key(self):
        """Open a file dialog to browse for the SSH key."""
        key_path = filedialog.askopenfilename(
            title="Select SSH Key File",
            filetypes=[("SSH Key Files", "*.pem *.key"), ("All Files", "*.*")]
        )
        if key_path and os.path.exists(key_path):
            self.key_var.set(key_path)
        else:
            messagebox.showerror("Error", "Selected file does not exist or cannot be accessed.")

    def save_settings(self, settings_window):
        """Save user-defined settings to the configuration."""
        try:
            # Prepare configuration dictionary
            config_dict = {
                'connection_name': self.settings_vars['CONNECTION_NAME'].get() or 'Default',
                'host': self.settings_vars['SSH_HOST'].get(),
                'port': int(self.settings_vars['SSH_PORT'].get() or 22),
                'user': self.settings_vars['SSH_USER'].get(),
                'dynamic_port': int(self.settings_vars['DYNAMIC_PORT'].get() or 1080),
                'test_url': self.settings_vars['TEST_URL'].get() or 'https://example.com',
                'http_proxy_port': int(self.settings_vars['HTTP_PROXY_PORT'].get() or 8080),
                'auth_method': self.auth_method_var.get(),
                'user_agent': self.settings_vars['USER_AGENT'].get() or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'home_page': self.settings_vars['HOME_PAGE'].get() or 'https://www.whatismybrowser.com/'
            }

            # Add authentication details based on method
            if self.auth_method_var.get() == "password":
                config_dict['password'] = self.password_var.get()
                config_dict['key_path'] = None
            else:
                config_dict['key_path'] = self.key_var.get()
                config_dict['password'] = None

                # Additional key check
                if not os.path.exists(config_dict['key_path']):
                    messagebox.showerror("Error", "SSH Key file does not exist.")
                    return

            # Update configuration
            self.config = SSHConfig(**config_dict)
            ConfigManager.save_config(self.config)

            # Update the title with the new connection name
            self._update_window_title()

            # Update environment variables (optional, depending on your needs)
            os.environ["CONNECTION_NAME"] = config_dict['connection_name']
            os.environ["SSH_HOST"] = config_dict['host']
            os.environ["SSH_PORT"] = str(config_dict['port'])
            os.environ["SSH_USER"] = config_dict['user']
            os.environ["DYNAMIC_PORT"] = str(config_dict['dynamic_port'])
            os.environ["TEST_URL"] = config_dict['test_url']
            os.environ["HTTP_PROXY_PORT"] = str(config_dict['http_proxy_port'])
            os.environ["AUTH_METHOD"] = config_dict['auth_method']
            os.environ["USER_AGENT"] = config_dict['user_agent']
            os.environ["HOME_PAGE"] = config_dict['home_page']

            if config_dict['auth_method'] == "password":
                os.environ["SSH_PASSWORD"] = config_dict.get('password', '')
            else:
                os.environ["SSH_KEY_PATH"] = config_dict.get('key_path', '')

            # Show success message
            messagebox.showinfo("Settings", "Configuration saved successfully!")

            # Close settings window
            settings_window.destroy()

        except Exception as e:
            # Show error message if something goes wrong
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")

    def _check_log_queue(self):
        """Update the log display with new log messages."""
        try:
            while True:
                log_msg = self.log_queue.get_nowait()
                self._append_log(log_msg)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._check_log_queue)

    def _append_log(self, message):
        self.log_display.config(state=tk.NORMAL)
        self.log_display.insert(tk.END, message + '\n')
        self.log_display.see(tk.END)
        self.log_display.config(state=tk.DISABLED)

    def _update_gui_state(self, connected: bool):
        self.connect_btn.config(state=tk.NORMAL if not connected else tk.DISABLED)
        self.disconnect_btn.config(state=tk.DISABLED if not connected else tk.NORMAL)
        self.settings_btn.config(state=tk.NORMAL if not connected else tk.DISABLED)
        self.status_var.set("Connected" if connected else "Not Connected")

        # Update the connection status indicator
        self._draw_connection_indicator(connected)

        # Update the title to reflect the connection status
        self._update_window_title()
