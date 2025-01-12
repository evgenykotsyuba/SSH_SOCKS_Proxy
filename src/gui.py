import os
import tkinter as tk
import traceback
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import queue
import logging
import asyncio
import datetime

from config import ConfigManager, SSHConfig
from ssh_client import SSHClient, SSHConnectionError
from chrome import chrome_browser
from socks_to_http_proxy import SOCKStoHTTPProxy
from languages_dictionary import TRANSLATIONS
from logging_handler import ColoredLogQueue, ColoredLogHandler, ColorMapping
from password_encryption_decryption import encrypt_password, salt
from protocol_baner import run_check_banner

from traffic_monitor import PortTrafficMonitor


class SSHProxyGUI:
    def __init__(self, root, log_queue):
        self.root = root
        self.log_queue = log_queue
        self.config = ConfigManager.load_config()

        # Initialize the title dynamically
        self._update_window_title()

        self.root.geometry("880x90")

        self.ssh_client = None
        self.connection_thread = None

        self.log_enabled = False

        self.traffic_window = None
        self.traffic_monitor = None

        self._setup_logging()

        # Initialize selected_language before calling _create_gui()
        self.selected_language = tk.StringVar(value=self.config.selected_language)

        # Initialize asyncio loop for traffic monitoring
        self.loop = asyncio.new_event_loop()
        self.traffic_running = False

        self._create_gui()
        self._check_log_queue()
        #----------
        # self.root = root
        # self.config = ConfigManager.load_config()
        #
        # # Initialize the title dynamically
        # self._update_window_title()
        #
        # self.root.geometry("880x90")
        #
        # self.log_queue = queue.Queue()
        # self.ssh_client = None
        # self.connection_thread = None
        #
        # self.log_enabled = False
        #
        # self.traffic_window = None
        # self.traffic_monitor = None
        #
        # self._setup_logging()
        #
        # # Initialize selected_language before calling _create_gui()
        # self.selected_language = tk.StringVar(value=self.config.selected_language)
        #
        # # Initialize asyncio loop for traffic monitoring
        # self.loop = asyncio.new_event_loop()
        # self.traffic_running = False
        #
        # self.loop = None
        # self.traffic_task = None
        #
        # self._create_gui()
        # self._check_log_queue()

    def _update_window_title(self):
        """Update the window title based on connection status and configuration."""
        connection_name = getattr(self.config, 'connection_name', None) or "Default"
        self.root.title(f"SSH SOCKS Proxy - {connection_name}")

    def _setup_logging(self):

        # Determine the log directory (cross-platform)
        log_dir = os.path.join(os.getcwd(), "log")
        os.makedirs(log_dir, exist_ok=True)

        # Create logger
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)  # Switch to INFO for release

        # Create file handler with a robust file path
        log_filename = os.path.join(log_dir, f"socks_proxy_{datetime.date.today()}.log")
        file_handler = logging.FileHandler(log_filename)

        # Set formatter
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        # Add handler to logger
        logger.addHandler(file_handler)

        # Add a handler for the interface
        handler = ColoredLogHandler(self.log_queue)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)

    def _create_gui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        # self.selected_language = tk.StringVar(value="en")  # Default language

        self.connect_btn = ttk.Button(btn_frame, text="Connect", command=self._start_connection)
        self.connect_btn.pack(side=tk.LEFT, padx=5)

        self.disconnect_btn = ttk.Button(btn_frame, text="Disconnect", command=self._stop_connection, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)

        self.settings_btn = ttk.Button(btn_frame, text="Settings", command=self._show_settings)
        self.settings_btn.pack(side=tk.LEFT, padx=5)

        self.chrome_btn = ttk.Button(btn_frame, text="Chrome", command=self._run_chrome_browser, state=tk.DISABLED)
        self.chrome_btn.pack(side=tk.LEFT, padx=5)

        self.chrome_btn.bind("<Enter>", lambda event: self.status_var.set("Chrome browser - Incognito Tab"))
        self.chrome_btn.bind("<Leave>", lambda event: self.status_var.set(""))

        self.http_proxy_btn = ttk.Button(btn_frame, text="HTTP Proxy", command=self._run_http_proxy, state=tk.DISABLED)
        self.http_proxy_btn.pack(side=tk.LEFT, padx=5)

        self.http_proxy_btn.bind("<Enter>", lambda event: self.status_var.set("HTTP proxy over SOCKS5"))
        self.http_proxy_btn.bind("<Leave>", lambda event: self.status_var.set(""))

        # Add traffic monitor button
        self.traffic_btn = ttk.Button(btn_frame, text="Traffic Monitor", command=self._toggle_traffic_monitor,
                                      state=tk.DISABLED)
        self.traffic_btn.pack(side=tk.LEFT, padx=5)

        self.toggle_logs_btn = ttk.Button(btn_frame, text="Show Logs", command=self._toggle_logs)
        self.toggle_logs_btn.pack(side=tk.LEFT, padx=5)

        self.help_btn = ttk.Button(btn_frame, text="Help", command=self._show_help)
        self.help_btn.pack(side=tk.RIGHT, padx=5)

        # Log display
        self.log_frame = ttk.LabelFrame(main_frame, text="Logs")
        self.log_frame.pack_forget()  # Initially hidden

        # Create log display with scrollbar
        self.log_display = ColoredLogQueue(
            self.log_frame,
            height=10,
            width=80,  # Увеличиваем ширину для лучшей читаемости
            wrap=tk.WORD,
            font=('Courier', 9)  # Используем моноширинный шрифт
        )
        self.log_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_display.config(state=tk.DISABLED)

        # Status bar
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.pack(fill=tk.X, pady=5)

        # Status text
        self.status_var = tk.StringVar(value="Not Connected")
        status_label = ttk.Label(self.status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_label.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        # Connection status indicator
        self.status_canvas = tk.Canvas(self.status_frame, width=20, height=20, highlightthickness=0,
                                       background=self.root.winfo_toplevel().cget('background'))
        self.status_canvas.pack(side=tk.RIGHT, padx=5)

        self._draw_connection_indicator(False)

        self._update_texts()

    def _draw_connection_indicator(self, connected: bool):
        """Draw a round indicator showing connection status."""
        self.status_canvas.delete("all")
        color = "green" if connected else "red"
        self.status_canvas.create_oval(3, 3, 17, 17, fill=color, outline=color)

    def _toggle_logs(self):
        """Toggle the visibility of logs."""
        translations = TRANSLATIONS.get(self.selected_language.get(), TRANSLATIONS["en"])
        if self.log_enabled:
            # Hide logs
            self.log_frame.pack_forget()
            self.root.geometry("880x90")  # Smaller window
            self.toggle_logs_btn.config(text=translations["Show Logs"])
            self.log_enabled = False
        else:
            # Show logs
            self.log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            self.root.geometry("880x600")  # Larger window
            self.toggle_logs_btn.config(text=translations["Hide Logs"])
            self.log_enabled = True

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

        # Show SSH server banner
        run_check_banner(self.config.host, self.config.port)

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
        translations = TRANSLATIONS.get(self.selected_language.get(), TRANSLATIONS["en"])
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("600x470")
        settings_window.transient(self.root)
        settings_window.grab_set()

        settings_frame = ttk.Frame(settings_window, padding="10")
        settings_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Basic fields
        basic_fields = [
            ("CONNECTION_NAME", translations["Connection Name:"]),
            ("SSH_HOST", translations["SSH Server:"]),
            ("SSH_PORT", translations["SSH Port:"]),
            ("SSH_USER", translations["Username:"]),
            ("DYNAMIC_PORT", translations["SOCKS Port:"]),
            ("KEEPALIVE_INTERVAL", translations["Keepalive interval:"]),
            ("KEEPALIVE_COUNT_MAX", translations["Keepalive count MAX:"]),
            ("TEST_URL", translations["Test SOCKS URL:"]),
            ("HTTP_PROXY_PORT", translations["HTTP Proxy Port:"]),
            ("USER_AGENT", translations["Browser User-Agent:"]),
            ("HOME_PAGE", translations["Browser Home Page:"]),
        ]

        self.settings_vars = {}

        # Authentication method selection
        ttk.Label(settings_frame, text=translations["Authentication Method:"]).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.auth_method_var = tk.StringVar(value=os.getenv("AUTH_METHOD", "password"))
        auth_frame = ttk.Frame(settings_frame)
        auth_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)

        self.password_radio = ttk.Radiobutton(auth_frame, text=translations["Password"], variable=self.auth_method_var,
                                              value="password",
                                              command=lambda: (self.toggle_auth_method(), self._reset_password()))
        self.password_radio.pack(side=tk.LEFT)

        self.key_radio = ttk.Radiobutton(auth_frame, text=translations["SSH Key"], variable=self.auth_method_var,
                                         value="key", command=self.toggle_auth_method)
        self.key_radio.pack(side=tk.LEFT)

        # Add basic fields
        for i, (key, label) in enumerate(basic_fields, start=1):
            ttk.Label(settings_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=2)
            var = tk.StringVar(value=os.getenv(key, ""))
            self.settings_vars[key] = var
            entry = ttk.Entry(settings_frame, textvariable=var)
            entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=2)

            # Bind changes to reset password
            entry.bind("<KeyRelease>", lambda _: self._reset_password())

        # Password field
        self.password_label = ttk.Label(settings_frame, text=translations["Password"] + ":")
        self.password_label.grid(row=len(basic_fields) + 1, column=0, sticky=tk.W, pady=2)
        self.password_var = tk.StringVar(value=os.getenv("SSH_PASSWORD", ""))
        self.password_entry = ttk.Entry(settings_frame, textvariable=self.password_var, show="*")
        self.password_entry.grid(row=len(basic_fields) + 1, column=1, sticky=(tk.W, tk.E), pady=2)

        # SSH Key field
        self.key_label = ttk.Label(settings_frame, text=translations["SSH Key"] + ":")
        self.key_label.grid(row=len(basic_fields) + 2, column=0, sticky=tk.W, pady=2)

        key_frame = ttk.Frame(settings_frame)
        key_frame.grid(row=len(basic_fields) + 2, column=1, sticky=(tk.W, tk.E), pady=2)

        self.key_var = tk.StringVar(value=os.getenv("SSH_KEY_PATH", ""))
        self.key_entry = ttk.Entry(key_frame, textvariable=self.key_var)
        self.key_entry.grid(column=0, row=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.key_entry.bind("<KeyRelease>", lambda _: self._reset_password())

        self.browse_btn = ttk.Button(key_frame, text="Browse", command=self.browse_key)
        self.browse_btn.grid(column=1, row=0, sticky=tk.E)

        # Flexibility settings
        key_frame.columnconfigure(0, weight=1)
        key_frame.columnconfigure(1, weight=0)

        # Language selection dropdown
        ttk.Label(settings_frame, text=translations["Language:"]).grid(row=len(basic_fields) + 3, column=0, sticky=tk.W, pady=2)
        self.selected_language = tk.StringVar(value=self.selected_language.get())  # Default language
        language_dropdown = ttk.Combobox(settings_frame, textvariable=self.selected_language, state="readonly")
        language_dropdown["values"] = ["en", "ru", "ua", "fr", "es", "cn"]
        language_dropdown.grid(row=len(basic_fields) + 3, column=1, sticky=(tk.W, tk.E), pady=2)

        # Bind the event for language selection
        language_dropdown.bind("<<ComboboxSelected>>", lambda _: (self._update_texts(), self._reset_password()))

        # Save button
        ttk.Button(settings_frame, text=translations["Save"], command=lambda: self.save_settings(settings_window)).grid(
            row=len(basic_fields) + 4, column=0, columnspan=2, pady=10)

        # Initialize auth method visibility
        self.toggle_auth_method()

    def _reset_password(self):
        """
        Clear the password field and reset the password variable when any settings are changed.
        """
        self.password_var.set("")

    def _update_texts(self):
        """Update button and label texts based on the selected language."""
        translations = TRANSLATIONS.get(self.selected_language.get(), TRANSLATIONS["en"])
        self.connect_btn.config(text=translations["Connect"])
        self.disconnect_btn.config(text=translations["Disconnect"])
        self.settings_btn.config(text=translations["Settings"])
        self.chrome_btn.config(text=translations["Chrome"])
        self.http_proxy_btn.config(text=translations["HTTP Proxy"])
        self.traffic_btn.config(text=translations["Traffic Monitor"])
        self.toggle_logs_btn.config(
            text=translations["Show Logs"] if not self.log_enabled else translations["Hide Logs"])
        self.help_btn.config(text=translations["Help"])
        self.status_var.set(translations["Not Connected"] if not self.ssh_client else translations["Connected"])

    def _run_http_proxy(self):
        try:
            translations = TRANSLATIONS.get(self.selected_language.get(), TRANSLATIONS["en"])
            socks_port = self.config.dynamic_port
            http_port = self.config.http_proxy_port

            # Create and start the HTTP proxy
            self.proxy = SOCKStoHTTPProxy(http_port=http_port, socks_port=socks_port)

            # Start the proxy server in a separate thread
            self.proxy_thread = threading.Thread(target=self.proxy.start, daemon=True)
            self.proxy_thread.start()

            logging.info(f"HTTP Proxy started on port {http_port} with SOCKS Proxy connection on port {socks_port}")

            # Update button state and command
            self.http_proxy_btn.config(
                text=translations["Disconnect Proxy"],
                command=self._close_http_proxy
            )

        except ValueError as e:
            logging.error(f"Error starting the HTTP Proxy: {e}")
        except Exception as e:
            logging.error(f"Unknown error: {e}")
            logging.error(traceback.format_exc())

    def _close_http_proxy(self):
        """Disconnect HTTP Proxy."""
        try:
            translations = TRANSLATIONS.get(self.selected_language.get(), TRANSLATIONS["en"])

            # Temporarily disable the button to prevent multiple clicks
            self.http_proxy_btn.config(state=tk.DISABLED)

            if hasattr(self, 'proxy') and self.proxy:
                # Stop the proxy server
                self.proxy.stop()

                # Wait for the thread to finish if it exists
                if hasattr(self, 'proxy_thread') and self.proxy_thread.is_alive():
                    self.proxy_thread.join(timeout=2)

                # Remove references
                self.proxy = None
                self.proxy_thread = None

                logging.info("HTTP Proxy disconnected successfully")

        except Exception as e:
            logging.error(f"Error during HTTP Proxy disconnection: {e}")
            logging.error(traceback.format_exc())

        finally:
            # Always restore button state
            self.http_proxy_btn.config(
                text=translations["HTTP Proxy"],
                command=self._run_http_proxy,
                state=tk.NORMAL
            )

    def _run_chrome_browser(self):
        """Starting Chrome browser with proxy settings."""
        try:
            translations = TRANSLATIONS.get(self.selected_language.get(), TRANSLATIONS["en"])
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
            self.chrome_btn.config(text=translations["Close Chrome"], command=self._close_chrome_browser)
        except Exception as e:
            logging.error(f"Error in Chrome browser launch: {e}")
            messagebox.showerror("Error", f"Failed to start Chrome: {str(e)}")

    def _close_chrome_browser(self):
        """Closing Chrome Browser."""
        translations = TRANSLATIONS.get(self.selected_language.get(), TRANSLATIONS["en"])
        try:
            if hasattr(self, 'browser_driver') and self.browser_driver:
                self.browser_driver.quit()
                self.browser_driver = None
                logging.info("Chrome browser closed.")

            if hasattr(self, 'chrome_thread') and self.chrome_thread.is_alive():
                self.chrome_thread.join(timeout=1)

            # Return the button to its original state
            self.chrome_btn.config(text=translations["Chrome"], command=self._run_chrome_browser)
        except Exception as e:
            logging.error(f"Error closing Chrome browser: {e}")
            messagebox.showerror("Error", f"Failed to close Chrome: {str(e)}")

    def _show_help(self):
        """Displays the content of info.md in a new help window."""
        # Check if info.md file exists
        if not os.path.exists("info.md"):
            logging.warning("Help file 'info.md' not found")
            messagebox.showinfo("Help", "Help documentation is not available.")
            return

        try:
            # Load the content of info.md
            with open("info.md", "r", encoding="utf-8") as help_file:
                help_content = help_file.read()

            # Create a new window
            help_window = tk.Toplevel(self.root)
            help_window.title("Help")
            help_window.geometry("600x500")  # Adjusted size for better readability
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
        """
        Save user-defined settings to the configuration.
        """
        try:
            # Prepare configuration dictionary
            config_dict = {
                'connection_name': self.settings_vars['CONNECTION_NAME'].get() or 'Default',
                'host': self.settings_vars['SSH_HOST'].get(),
                'port': int(self.settings_vars['SSH_PORT'].get() or 22),
                'user': self.settings_vars['SSH_USER'].get(),
                'dynamic_port': int(self.settings_vars['DYNAMIC_PORT'].get() or 1080),
                'keepalive_interval': int(self.settings_vars['KEEPALIVE_INTERVAL'].get() or 60),
                'keepalive_count_max': int(self.settings_vars['KEEPALIVE_COUNT_MAX'].get() or 120),
                'test_url': self.settings_vars['TEST_URL'].get() or 'https://example.com',
                'http_proxy_port': int(self.settings_vars['HTTP_PROXY_PORT'].get() or 8080),
                'auth_method': self.auth_method_var.get(),
                'user_agent': self.settings_vars[
                                  'USER_AGENT'].get() or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'home_page': self.settings_vars['HOME_PAGE'].get() or 'https://www.whatismybrowser.com/',
                'selected_language': self.selected_language.get()
            }

            # Add authentication details based on the method
            if self.auth_method_var.get() == "password":
                password = self.password_var.get()

                if not password:
                    raise ValueError("Password cannot be empty for password authentication.")

                # Encrypt the password and save it
                encrypted_password = encrypt_password(password, salt)
                config_dict['password'] = encrypted_password.decode('utf-8')  # Store encrypted as string
                config_dict['key_path'] = None

                # Save encrypted password in environment variable
                os.environ["SSH_PASSWORD"] = encrypted_password.decode('utf-8')
            else:
                key_path = self.key_var.get()
                if not key_path or not os.path.exists(key_path):
                    raise FileNotFoundError("SSH Key file does not exist.")

                config_dict['key_path'] = key_path
                config_dict['password'] = None  # No password required for key-based auth

                # Save key path in environment variable
                os.environ["SSH_KEY_PATH"] = key_path

            # Update environment variables for other settings
            os.environ["CONNECTION_NAME"] = config_dict['connection_name']
            os.environ["SSH_HOST"] = config_dict['host']
            os.environ["SSH_PORT"] = str(config_dict['port'])
            os.environ["SSH_USER"] = config_dict['user']
            os.environ["DYNAMIC_PORT"] = str(config_dict['dynamic_port'])
            os.environ['KEEPALIVE_INTERVAL'] = str(config_dict['keepalive_interval'])
            os.environ['KEEPALIVE_COUNT_MAX'] = str(config_dict['keepalive_count_max'])
            os.environ["TEST_URL"] = config_dict['test_url']
            os.environ["HTTP_PROXY_PORT"] = str(config_dict['http_proxy_port'])
            os.environ["AUTH_METHOD"] = config_dict['auth_method']
            os.environ["USER_AGENT"] = config_dict['user_agent']
            os.environ["HOME_PAGE"] = config_dict['home_page']
            os.environ["LANGUAGE"] = config_dict['selected_language']

            # Update configuration object and save to file
            self.config = SSHConfig(**config_dict)
            ConfigManager.save_config(self.config)

            # Update the title with the new connection name
            self._update_window_title()

            # Show success message and close settings window
            messagebox.showinfo("Settings", "Configuration saved successfully!")
            settings_window.destroy()

        except ValueError as ve:
            messagebox.showerror("Validation Error", str(ve))
        except FileNotFoundError as fe:
            messagebox.showerror("File Error", str(fe))
        except Exception as e:
            # Log unexpected errors
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")

    def _check_log_queue(self):
        """Update the log display with new colored log messages."""
        if not hasattr(self, 'log_display'):
            self.root.after(100, self._check_log_queue)
            return

        try:
            while True:
                # Get message and level from queue
                message, level = self.log_queue.get_nowait()
                color = ColorMapping.GUI_COLORS.get(level, '#000000')  # Default to black if level not found
                self.log_display.append_colored_text(message, color)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._check_log_queue)

    # def _append_log(self, message):
    #     self.log_display.config(state=tk.NORMAL)
    #     self.log_display.insert(tk.END, message + '\n')
    #     self.log_display.see(tk.END)
    #     self.log_display.config(state=tk.DISABLED)

    def _update_gui_state(self, connected: bool):
        self.connect_btn.config(state=tk.NORMAL if not connected else tk.DISABLED)
        self.disconnect_btn.config(state=tk.DISABLED if not connected else tk.NORMAL)
        self.settings_btn.config(state=tk.NORMAL if not connected else tk.DISABLED)
        self.chrome_btn.config(state=tk.DISABLED if not connected else tk.NORMAL)
        self.http_proxy_btn.config(state=tk.DISABLED if not connected else tk.NORMAL)
        self.traffic_btn.config(state=tk.DISABLED if not connected else tk.NORMAL)
        self.status_var.set("Connected" if connected else "Not Connected")
        self._draw_connection_indicator(connected)
        self._update_window_title()

    def _create_traffic_window(self):
        """Create traffic monitoring window"""
        translations = TRANSLATIONS.get(self.selected_language.get(), TRANSLATIONS["en"])
        if self.traffic_window is None:
            self.traffic_window = tk.Toplevel(self.root)
            self.traffic_window.title(f"Port {self.config.dynamic_port} Traffic Monitor")
            self.traffic_window.geometry("400x300")
            self.traffic_window.protocol("WM_DELETE_WINDOW", self._close_traffic_monitor)

            # Ensure window closes if main window is closed
            self.traffic_window.transient(self.root)

            # Create traffic monitoring frame with proper layout management
            main_frame = ttk.Frame(self.traffic_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Stats frame
            stats_frame = ttk.LabelFrame(main_frame, text=translations["Traffic Statistics"])
            stats_frame.pack(fill=tk.BOTH, expand=True, pady=5)

            # Grid configuration for proper spacing
            stats_frame.grid_columnconfigure(1, weight=1)

            # Create labels for statistics with better layout
            self.traffic_labels = {}
            stats = [
                ("upload_speed", translations["Upload Speed:"], "0 B/s"),
                ("download_speed", translations["Download Speed:"], "0 B/s"),
                ("total_upload", translations["Total Uploaded:"], "0 B"),
                ("total_download", translations["Total Downloaded:"], "0 B"),
                ("connections", translations["Active Connections:"], "0")
            ]

            for i, (key, text, default) in enumerate(stats):
                ttk.Label(stats_frame, text=text).grid(row=i, column=0, sticky=tk.W, padx=(5, 10), pady=5)
                label = ttk.Label(stats_frame, text=default)
                label.grid(row=i, column=1, sticky=tk.E, padx=5, pady=5)
                self.traffic_labels[key] = label

            # Create button frame
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(fill=tk.X, pady=5)

            # Store the button frame for later use
            self.traffic_btn_frame = btn_frame

    def _start_traffic_monitoring(self):
        """Start traffic monitoring with proper asyncio handling"""
        if not self.traffic_running:
            self.traffic_running = True

            # Create new event loop
            if self.loop is None or self.loop.is_closed():
                self.loop = asyncio.new_event_loop()

            def run_async_loop():
                try:
                    asyncio.set_event_loop(self.loop)
                    self.traffic_monitor = PortTrafficMonitor(self.config.dynamic_port, self._update_traffic_display)

                    # Add reset counters button after monitor is created
                    if hasattr(self, 'traffic_btn_frame'):
                        self.traffic_window.after(0, self._add_reset_button)

                    self.traffic_task = self.loop.create_task(self.traffic_monitor.start_monitoring())
                    self.loop.run_forever()
                except Exception as e:
                    logging.error(f"Error in traffic monitoring loop: {e}")
                finally:
                    if not self.loop.is_closed():
                        self.loop.close()

            self.monitor_thread = threading.Thread(target=run_async_loop, daemon=True)
            self.monitor_thread.start()

    def _add_reset_button(self):
        """Add reset button to traffic window"""
        translations = TRANSLATIONS.get(self.selected_language.get(), TRANSLATIONS["en"])
        if hasattr(self, 'reset_counters_btn'):
            self.reset_counters_btn.destroy()

        self.reset_counters_btn = ttk.Button(
            self.traffic_btn_frame,
            text=translations["Reset Counters"],
            command=self.traffic_monitor.reset_counters
        )
        self.reset_counters_btn.pack(side=tk.LEFT, padx=5)

    def _toggle_traffic_monitor(self):
        """Toggle traffic monitoring window"""
        if self.traffic_window is None:
            self._create_traffic_window()
            self._start_traffic_monitoring()
        else:
            self._close_traffic_monitor()

    def _update_traffic_display(self, stats: dict):
        """Update traffic statistics display with error handling"""
        if self.traffic_window and not self.traffic_window.winfo_exists():
            self._close_traffic_monitor()
            return

        try:
            if self.traffic_window:
                self.traffic_window.after(0, self._update_traffic_labels, stats)
        except tk.TclError:
            # Handle case where window was closed
            self._close_traffic_monitor()

    def _update_traffic_labels(self, stats: dict):
        """Update traffic monitor labels with error handling"""
        if not self.traffic_labels:
            return

        try:
            for key, label in self.traffic_labels.items():
                if key == "upload_speed":
                    value = f"{PortTrafficMonitor.format_bytes(stats['upload_speed'])}/s"
                elif key == "download_speed":
                    value = f"{PortTrafficMonitor.format_bytes(stats['download_speed'])}/s"
                elif key == "total_upload":
                    value = f"{PortTrafficMonitor.format_bytes(stats['total_bytes_sent'])}"
                elif key == "total_download":
                    value = f"{PortTrafficMonitor.format_bytes(stats['total_bytes_recv'])}"
                elif key == "connections":
                    value = str(stats['active_connections'])
                else:
                    continue

                label.config(text=value)
        except tk.TclError:
            # Handle case where labels were destroyed
            self._close_traffic_monitor()

    def _close_traffic_monitor(self):
        """Close traffic monitoring window and cleanup resources"""
        try:
            # First stop the monitoring
            if self.traffic_monitor:
                self.traffic_monitor.stop_monitoring()
                self.traffic_running = False

            # Cancel any running tasks
            if self.traffic_task and not self.traffic_task.done():
                self.traffic_task.cancel()

            # Properly stop and close the event loop
            if self.loop and not self.loop.is_closed():
                try:
                    # Schedule the loop to stop
                    self.loop.call_soon_threadsafe(self.loop.stop)

                    # Wait briefly for the loop to stop
                    if self.monitor_thread and self.monitor_thread.is_alive():
                        self.monitor_thread.join(timeout=2)

                    # Now it's safe to close the loop
                    if not self.loop.is_closed():
                        self.loop.close()
                except Exception as e:
                    logging.error(f"Error closing event loop: {e}")
                finally:
                    self.loop = None

            # Clean up the window and labels
            if self.traffic_window:
                self.traffic_window.destroy()
                self.traffic_window = None
                self.traffic_labels = {}

        except Exception as e:
            logging.error(f"Error during traffic monitor cleanup: {e}")
            # Ensure window is destroyed even if other cleanup fails
            if self.traffic_window:
                self.traffic_window.destroy()
                self.traffic_window = None
