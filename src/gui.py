import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import queue
import logging
import asyncio

from config import ConfigManager, SSHConfig
from ssh_client import SSHClient, SSHConnectionError


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
        self.root.title("SSH SOCKS Proxy")
        self.root.geometry("700x500")
        
        self.log_queue = queue.Queue()
        self.ssh_client = None
        self.connection_thread = None
        self.config = ConfigManager.load_config()

        self._setup_logging()
        self._create_gui()
        self._check_log_queue()

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

        # Log display
        log_frame = ttk.LabelFrame(main_frame, text="Logs")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_display = scrolledtext.ScrolledText(log_frame, height=20, wrap=tk.WORD)
        self.log_display.pack(fill=tk.BOTH, expand=True)
        self.log_display.config(state=tk.DISABLED)

        # Status bar
        self.status_var = tk.StringVar(value="Not Connected")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=5)

    def _start_connection(self):
        # Validation logic
        if not all([self.config.host, self.config.user]):
            messagebox.showerror("Error", "Missing SSH configuration")
            return

        self.connect_btn.config(state=tk.DISABLED)
        self.disconnect_btn.config(state=tk.NORMAL)
        self.settings_btn.config(state=tk.DISABLED)
        
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

    def _update_connection_status(self, connected: bool):
        """Updates the connection status in the GUI."""
        self.root.after(0, lambda: self._update_gui_state(connected))

    def _stop_connection(self):
        if self.ssh_client:
            self.ssh_client.stop()

    def _show_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("430x250")
        settings_window.transient(self.root)
        settings_window.grab_set()

        settings_frame = ttk.Frame(settings_window, padding="10")
        settings_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Basic fields
        basic_fields = [
            ("SSH_HOST", "SSH Server:"),
            ("SSH_PORT", "SSH Port:"),
            ("SSH_USER", "Username:"),
            ("DYNAMIC_PORT", "SOCKS Port:")
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

    def toggle_auth_method(self):
        auth_method = self.auth_method_var.get()

        if auth_method == "password":
            # Show password entry and hide SSH key entry
            self.password_label.grid()
            self.password_entry.grid()
            self.key_label.grid_remove()
            self.key_entry.grid_remove()
            self.browse_btn.grid_remove()
        else:
            # Show SSH key entry and hide password entry
            self.password_label.grid_remove()
            self.password_entry.grid_remove()
            self.key_label.grid()
            self.key_entry.grid()
            self.browse_btn.grid()

    def browse_key(self):
        key_path = filedialog.askopenfilename(
            title="Select SSH Key File",
            filetypes=[("SSH Key Files", "*.pem *.key"), ("All Files", "*.*")]
        )
        if key_path and os.path.exists(key_path):
            self.key_var.set(key_path)
        else:
            messagebox.showerror("Error", "Selected file does not exist or cannot be accessed.")

    def save_settings(self, settings_window):
        try:
            # Prepare configuration dictionary
            config_dict = {
                'host': self.settings_vars['SSH_HOST'].get(),
                'port': int(self.settings_vars['SSH_PORT'].get() or 22),
                'user': self.settings_vars['SSH_USER'].get(),
                'dynamic_port': int(self.settings_vars['DYNAMIC_PORT'].get() or 1080),
                'auth_method': self.auth_method_var.get()
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

            # Update environment variables (optional, depending on your needs)
            os.environ["SSH_HOST"] = config_dict['host']
            os.environ["SSH_PORT"] = str(config_dict['port'])
            os.environ["SSH_USER"] = config_dict['user']
            os.environ["DYNAMIC_PORT"] = str(config_dict['dynamic_port'])
            os.environ["AUTH_METHOD"] = config_dict['auth_method']

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
