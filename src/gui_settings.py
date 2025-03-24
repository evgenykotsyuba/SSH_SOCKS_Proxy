import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict
from config import ConfigManager, SSHConfig
from languages_dictionary import TRANSLATIONS
from password_encryption_decryption import encrypt_password, salt


class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, gui_instance):
        super().__init__(parent)  # Pass the correct parent (self.root)
        self.gui_instance = gui_instance  # Store reference to SSHProxyGUI
        self.config = gui_instance.config  # Access configuration
        self.selected_language = gui_instance.selected_language  # Access selected language
        self.title("Settings")
        self.geometry("600x470")
        self.transient(parent)  # Bind window to parent
        self.grab_set()  # Capture focus
        self._create_widgets()  # Call method to create widgets

    def _create_widgets(self):
        settings_frame = ttk.Frame(self, padding="10")
        settings_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        translations = TRANSLATIONS.get(self.selected_language.get(), TRANSLATIONS["en"])

        # Authentication method
        ttk.Label(settings_frame, text=translations["Authentication Method:"]).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.auth_method_var = tk.StringVar(value=self.config.auth_method)
        auth_frame = ttk.Frame(settings_frame)
        auth_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)

        self.password_radio = ttk.Radiobutton(auth_frame, text=translations["Password"], variable=self.auth_method_var,
                                              value="password", command=self.toggle_auth_method)
        self.password_radio.pack(side=tk.LEFT)
        self.key_radio = ttk.Radiobutton(auth_frame, text=translations["SSH Key"], variable=self.auth_method_var,
                                         value="key", command=self.toggle_auth_method)
        self.key_radio.pack(side=tk.LEFT)

        # Basic fields
        basic_fields = [
            ("CONNECTION_NAME", translations["Connection Name:"]),
            ("HOST", translations["SSH Server:"]),
            ("PORT", translations["SSH Port:"]),
            ("USER", translations["Username:"]),
            ("DYNAMIC_PORT", translations["SOCKS Port:"]),
            ("KEEPALIVE_INTERVAL", translations["Keepalive interval:"]),
            ("KEEPALIVE_COUNT_MAX", translations["Keepalive count MAX:"]),
            ("TEST_URL", translations["Test SOCKS URL:"]),
            ("HTTP_PROXY_PORT", translations["HTTP Proxy Port:"]),
            ("USER_AGENT", translations["Browser User-Agent:"]),
            ("HOME_PAGE", translations["Browser Home Page:"]),
        ]

        self.settings_vars: Dict[str, tk.StringVar] = {}
        for i, (key, label) in enumerate(basic_fields, start=1):
            ttk.Label(settings_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=2)
            var = tk.StringVar(value=getattr(self.config, key.lower(), ""))
            self.settings_vars[key] = var
            entry = ttk.Entry(settings_frame, textvariable=var)
            entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=2)
            entry.bind("<KeyRelease>", lambda _: self._reset_password())

        # Password field
        self.password_label = ttk.Label(settings_frame, text=translations["Password"] + ":")
        self.password_label.grid(row=len(basic_fields) + 1, column=0, sticky=tk.W, pady=2)
        self.password_var = tk.StringVar(value=self.config.password or "")
        self.password_entry = ttk.Entry(settings_frame, textvariable=self.password_var, show="*")
        self.password_entry.grid(row=len(basic_fields) + 1, column=1, sticky=(tk.W, tk.E), pady=2)

        # SSH Key field
        self.key_label = ttk.Label(settings_frame, text=translations["SSH Key"] + ":")
        self.key_label.grid(row=len(basic_fields) + 2, column=0, sticky=tk.W, pady=2)
        key_frame = ttk.Frame(settings_frame)
        key_frame.grid(row=len(basic_fields) + 2, column=1, sticky=(tk.W, tk.E), pady=2)
        self.key_var = tk.StringVar(value=self.config.key_path or "")
        self.key_entry = ttk.Entry(key_frame, textvariable=self.key_var)
        self.key_entry.grid(column=0, row=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.key_entry.bind("<KeyRelease>", lambda _: self._reset_password())
        self.browse_btn = ttk.Button(key_frame, text="Browse", command=self.browse_key)
        self.browse_btn.grid(column=1, row=0, sticky=tk.E)

        key_frame.columnconfigure(0, weight=1)
        key_frame.columnconfigure(1, weight=0)

        # Language selection
        ttk.Label(settings_frame, text=translations["Language:"]).grid(row=len(basic_fields) + 3, column=0, sticky=tk.W,
                                                                       pady=2)
        language_dropdown = ttk.Combobox(settings_frame, textvariable=self.selected_language, state="readonly")
        language_dropdown["values"] = ["en", "ru", "ua", "fr", "es", "cn", "de"]
        language_dropdown.grid(row=len(basic_fields) + 3, column=1, sticky=(tk.W, tk.E), pady=2)
        language_dropdown.bind("<<ComboboxSelected>>",
                               lambda _: (self.gui_instance._update_texts(), self._reset_password()))

        # Save button
        ttk.Button(settings_frame, text=translations["Save"], command=self.save_settings).grid(
            row=len(basic_fields) + 4, column=0, columnspan=2, pady=10)

        self.toggle_auth_method()

    def toggle_auth_method(self):
        """Toggle authentication method fields based on user selection."""
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
        """Open file dialog to select SSH key file."""
        key_path = filedialog.askopenfilename(title="Select SSH Key File",
                                              filetypes=[("SSH Key Files", "*.pem *.key"), ("All Files", "*.*")])
        if key_path and os.path.exists(key_path):
            self.key_var.set(key_path)
        else:
            messagebox.showerror("Error", "Selected file does not exist or cannot be accessed.")

    def _reset_password(self):
        """Reset the password field."""
        self.password_var.set("")

    def save_settings(self):
        """Save settings and update configuration."""
        # The implementation remains unchanged
        try:
            config_dict = {
                'connection_name': self.settings_vars['CONNECTION_NAME'].get() or 'Default',
                'host': self.settings_vars['HOST'].get(),
                'port': int(self.settings_vars['PORT'].get() or 22),
                'user': self.settings_vars['USER'].get(),
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

            if self.auth_method_var.get() == "password":
                password = self.password_var.get()
                if not password:
                    raise ValueError("Password cannot be empty for password authentication.")
                encrypted_password = encrypt_password(password, salt)
                config_dict['password'] = encrypted_password.decode('utf-8')
                config_dict['key_path'] = None
            else:
                key_path = self.key_var.get()
                if not key_path or not os.path.exists(key_path):
                    raise FileNotFoundError("SSH Key file does not exist.")
                config_dict['key_path'] = key_path
                config_dict['password'] = None

            # Update configuration in gui_instance
            self.gui_instance.config = SSHConfig(**config_dict)
            ConfigManager.save_config(self.gui_instance.config)
            self.gui_instance._update_window_title()
            messagebox.showinfo("Settings", "Configuration saved successfully!")
            self.destroy()
        except ValueError as ve:
            messagebox.showerror("Validation Error", str(ve))
        except FileNotFoundError as fe:
            messagebox.showerror("File Error", str(fe))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
