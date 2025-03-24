import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import asyncio
import queue
import logging
import datetime
from typing import Optional, Dict, Any

from config import ConfigManager, SSHConfig
from ssh_client import SSHClient, SSHConnectionError
from chrome import chrome_browser
from socks_to_http_proxy import SOCKStoHTTPProxy
from languages_dictionary import TRANSLATIONS
from logging_handler import ColoredLogQueue, ColoredLogHandler, ColorMapping
from protocol_baner import run_check_banner
from gui_traffic_monitor import PortTrafficMonitor
from gui_settings import SettingsWindow


# Class to manage connections and proxy
class ConnectionManager:
    def __init__(self, config: SSHConfig):
        self.config = config
        self.ssh_client: Optional[SSHClient] = None
        self.proxy: Optional[SOCKStoHTTPProxy] = None
        self.browser_driver = None
        self.proxy_thread: Optional[threading.Thread] = None
        self.chrome_thread: Optional[threading.Thread] = None

    def start_ssh_connection(self) -> None:
        """Starts SSH connection in a separate thread."""
        run_check_banner(self.config.host, self.config.port)
        try:
            self.ssh_client = SSHClient(self.config)
            asyncio.run(self.ssh_client.manage_connection())
        except SSHConnectionError as e:
            logging.error(f"SSH Connection failed: {e}")
            raise

    def stop_ssh_connection(self) -> None:
        """Stops SSH connection."""
        if self.ssh_client:
            self.ssh_client.stop()
            self.ssh_client = None

    def start_http_proxy(self, socks_port: int, http_port: int) -> None:
        """Starts HTTP proxy."""
        self.proxy = SOCKStoHTTPProxy(http_port=http_port, socks_port=socks_port)
        self.proxy_thread = threading.Thread(target=self.proxy.start, daemon=True)
        self.proxy_thread.start()
        logging.info(f"HTTP Proxy started on port {http_port} with SOCKS on {socks_port}")

    def stop_http_proxy(self) -> None:
        """Stops HTTP proxy."""
        if self.proxy:
            self.proxy.stop()
            if self.proxy_thread and self.proxy_thread.is_alive():
                self.proxy_thread.join(timeout=2)
            self.proxy = None
            self.proxy_thread = None
            logging.info("HTTP Proxy stopped")

    def start_chrome(self, socks_port: int, user_agent: str, home_page: str, title: str, language: str) -> None:
        """Starts Chrome with proxy."""
        def run_browser():
            try:
                self.browser_driver = chrome_browser(socks_port, user_agent, home_page, title, language)
            except Exception as e:
                logging.error(f"Failed to launch Chrome: {e}")
                raise
        self.chrome_thread = threading.Thread(target=run_browser, daemon=True)
        self.chrome_thread.start()

    def stop_chrome(self) -> None:
        """Closes Chrome."""
        if self.browser_driver:
            self.browser_driver.quit()
            self.browser_driver = None
            if self.chrome_thread and self.chrome_thread.is_alive():
                self.chrome_thread.join(timeout=1)
            logging.info("Chrome closed")


# Main GUI class
class SSHProxyGUI:
    def __init__(self, root: tk.Tk, log_queue: queue.Queue):
        self.root = root
        self.log_queue = log_queue
        self.config = ConfigManager.load_config()
        self.connection_manager = ConnectionManager(self.config)
        self.connection_thread: Optional[threading.Thread] = None
        self.log_enabled = False
        self.traffic_monitor: Optional[PortTrafficMonitor] = None
        self.traffic_window: Optional[tk.Toplevel] = None

        self.root.geometry("880x90")
        self._update_window_title()
        self._setup_logging()
        self.selected_language = tk.StringVar(value=self.config.selected_language)
        self._create_gui()
        self._check_log_queue()

    def _update_window_title(self) -> None:
        """Updates window title."""
        connection_name = self.config.connection_name or "Default"
        self.root.title(f"SSH SOCKS Proxy - {connection_name}")

    def _setup_logging(self) -> None:
        """Sets up logging."""
        log_dir = os.path.join(os.getcwd(), "log")
        os.makedirs(log_dir, exist_ok=True)
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        log_filename = os.path.join(log_dir, f"socks_proxy_{datetime.date.today()}.log")
        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        handler = ColoredLogHandler(self.log_queue)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)

    def _create_gui(self) -> None:
        """Creates GUI."""
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        self.connect_btn = ttk.Button(btn_frame, text="Connect", command=self._start_connection)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        self.disconnect_btn = ttk.Button(btn_frame, text="Disconnect", command=self._stop_connection, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)
        self.settings_btn = ttk.Button(btn_frame, text="Settings", command=self._show_settings)
        self.settings_btn.pack(side=tk.LEFT, padx=5)
        self.chrome_btn = ttk.Button(btn_frame, text="Chrome", command=self._run_chrome, state=tk.DISABLED)
        self.chrome_btn.pack(side=tk.LEFT, padx=5)
        self.http_proxy_btn = ttk.Button(btn_frame, text="HTTP Proxy", command=self._run_http_proxy, state=tk.DISABLED)
        self.http_proxy_btn.pack(side=tk.LEFT, padx=5)
        self.traffic_btn = ttk.Button(btn_frame, text="Traffic Monitor", command=self._toggle_traffic_monitor,
                                      state=tk.DISABLED)
        self.traffic_btn.pack(side=tk.LEFT, padx=5)
        self.toggle_logs_btn = ttk.Button(btn_frame, text="Show Logs", command=self._toggle_logs)
        self.toggle_logs_btn.pack(side=tk.LEFT, padx=5)
        self.help_btn = ttk.Button(btn_frame, text="Help", command=self._show_help)
        self.help_btn.pack(side=tk.RIGHT, padx=5)

        self.log_frame = ttk.LabelFrame(main_frame, text="Logs")
        self.log_frame.pack_forget()
        self.log_display = ColoredLogQueue(self.log_frame, height=10, width=80, wrap=tk.WORD, font=('Courier', 9))
        self.log_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_display.config(state=tk.DISABLED)

        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.pack(fill=tk.X, pady=5)
        self.status_var = tk.StringVar(value="Not Connected")
        ttk.Label(self.status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.LEFT,
                                                                                                       expand=True,
                                                                                                       fill=tk.X,
                                                                                                       padx=(0, 5))
        self.status_canvas = tk.Canvas(self.status_frame, width=20, height=20, highlightthickness=0)
        self.status_canvas.pack(side=tk.RIGHT, padx=5)
        self._draw_connection_indicator(False)

        self._update_texts()

    def _draw_connection_indicator(self, connected: bool) -> None:
        """Draws connection status indicator."""
        self.status_canvas.delete("all")
        color = "green" if connected else "red"
        self.status_canvas.create_oval(3, 3, 17, 17, fill=color, outline=color)

    def _toggle_logs(self) -> None:
        """Toggles log display."""
        translations = TRANSLATIONS.get(self.selected_language.get(), TRANSLATIONS["en"])
        if self.log_enabled:
            self.log_frame.pack_forget()
            self.root.geometry("880x90")
            self.toggle_logs_btn.config(text=translations["Show Logs"])
            self.log_enabled = False
        else:
            self.log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            self.root.geometry("880x600")
            self.toggle_logs_btn.config(text=translations["Hide Logs"])
            self.log_enabled = True

    def _show_settings(self) -> None:
        """Opens settings window."""
        SettingsWindow(self.root, self)

    def _show_help(self) -> None:
        """Opens help window."""
        if not os.path.exists("info.md"):
            logging.warning("Help file 'info.md' not found")
            messagebox.showinfo("Help", "Help documentation is not available.")
            return
        try:
            with open("info.md", "r", encoding="utf-8") as help_file:
                help_content = help_file.read()
            help_window = tk.Toplevel(self.root)
            help_window.title("Help")
            help_window.geometry("600x500")
            help_window.transient(self.root)
            help_window.grab_set()
            text_frame = ttk.Frame(help_window, padding="10")
            text_frame.pack(fill=tk.BOTH, expand=True)
            help_text = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, font=("Arial", 10), state=tk.NORMAL)
            help_text.insert(tk.END, help_content)
            help_text.config(state=tk.DISABLED)
            help_text.pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            logging.error(f"Failed to load help content: {e}")
            messagebox.showerror("Error", f"Could not load help content:\n{e}")

    def _start_connection(self) -> None:
        """Starts SSH connection."""
        if not all([self.config.host, self.config.user]):
            messagebox.showerror("Error", "Missing SSH configuration")
            return
        try:
            self.connection_thread = threading.Thread(target=self.connection_manager.start_ssh_connection, daemon=True)
            self.connection_thread.start()
            self._update_gui_state(True)
        except Exception as e:
            self._handle_error(f"Failed to start connection: {e}")
            self._update_gui_state(False)

    def _stop_connection(self) -> None:
        """Stops connection and related services."""
        self.connection_manager.stop_chrome()
        self.connection_manager.stop_http_proxy()
        self.connection_manager.stop_ssh_connection()
        self._close_traffic_monitor()
        self._update_gui_state(False)

    def _run_http_proxy(self) -> None:
        """Starts or stops HTTP proxy."""
        translations = TRANSLATIONS.get(self.selected_language.get(), TRANSLATIONS["en"])
        if self.connection_manager.proxy:
            self.connection_manager.stop_http_proxy()
            self._update_button(self.http_proxy_btn, translations["HTTP Proxy"], self._run_http_proxy)
        else:
            try:
                self.connection_manager.start_http_proxy(self.config.dynamic_port, self.config.http_proxy_port)
                self._update_button(self.http_proxy_btn, translations["Disconnect Proxy"], self._run_http_proxy)
            except Exception as e:
                self._handle_error(f"Failed to start HTTP Proxy: {e}")

    def _run_chrome(self) -> None:
        """Starts or closes Chrome."""
        translations = TRANSLATIONS.get(self.selected_language.get(), TRANSLATIONS["en"])
        if self.connection_manager.browser_driver:
            self.connection_manager.stop_chrome()
            self._update_button(self.chrome_btn, translations["Chrome"], self._run_chrome)
        else:
            try:
                title = f"{self.config.connection_name}: {self.config.home_page.replace('https://', '')}"
                self.connection_manager.start_chrome(
                    self.config.dynamic_port, self.config.user_agent, self.config.home_page, title, self.config.selected_language
                )
                self._update_button(self.chrome_btn, translations["Close Chrome"], self._run_chrome)
            except Exception as e:
                self._handle_error(f"Failed to start Chrome: {e}")

    def _toggle_traffic_monitor(self) -> None:
        """Toggles traffic monitoring."""
        if self.traffic_window:
            self._close_traffic_monitor()
        else:
            self._create_traffic_window()
            self.traffic_monitor = PortTrafficMonitor(self.config.dynamic_port, self._update_traffic_display)

            def run_monitoring():
                asyncio.run(self.traffic_monitor.start_monitoring())

            self.monitor_thread = threading.Thread(target=run_monitoring, daemon=True)
            self.monitor_thread.start()

    def _create_traffic_window(self) -> None:
        """Creates traffic monitoring window."""
        translations = TRANSLATIONS.get(self.selected_language.get(), TRANSLATIONS["en"])
        self.traffic_window = tk.Toplevel(self.root)
        self.traffic_window.title(f"Port {self.config.dynamic_port} Traffic Monitor")
        self.traffic_window.geometry("400x300")
        self.traffic_window.protocol("WM_DELETE_WINDOW", self._close_traffic_monitor)
        main_frame = ttk.Frame(self.traffic_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        stats_frame = ttk.LabelFrame(main_frame, text=translations["Traffic Statistics"])
        stats_frame.pack(fill=tk.BOTH, expand=True)
        self.traffic_labels = {}
        stats = [
            ("upload_speed", translations["Upload Speed:"], "0 B/s"),
            ("download_speed", translations["Download Speed:"], "0 B/s"),
            ("total_upload", translations["Total Uploaded:"], "0 B"),
            ("total_download", translations["Total Downloaded:"], "0 B"),
            ("connections", translations["Active Connections:"], "0")
        ]
        for i, (key, text, default) in enumerate(stats):
            ttk.Label(stats_frame, text=text).grid(row=i, column=0, sticky=tk.W, padx=5, pady=5)
            label = ttk.Label(stats_frame, text=default)
            label.grid(row=i, column=1, sticky=tk.E, padx=5, pady=5)
            self.traffic_labels[key] = label

    def _update_traffic_display(self, stats: Dict[str, Any]) -> None:
        """Updates traffic statistics display."""
        if self.traffic_window and self.traffic_labels:
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
                label.config(text=value)

    def _close_traffic_monitor(self) -> None:
        """Closes traffic monitoring."""
        if self.traffic_monitor:
            self.traffic_monitor.stop_monitoring()
        if self.traffic_window:
            self.traffic_window.destroy()
            self.traffic_window = None
            self.traffic_labels = {}

    def _update_texts(self) -> None:
        """Updates GUI texts."""
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
        self.status_var.set(translations["Not Connected"])

    def _update_button(self, button: ttk.Button, text: str, command: callable) -> None:
        """Updates button text and command."""
        button.config(text=text, command=command)

    def _handle_error(self, message: str) -> None:
        """Handles errors with user notification."""
        logging.error(message)
        messagebox.showerror("Error", message)

    def _update_gui_state(self, connected: bool) -> None:
        """Updates GUI state."""
        self.connect_btn.config(state=tk.NORMAL if not connected else tk.DISABLED)
        self.disconnect_btn.config(state=tk.DISABLED if not connected else tk.NORMAL)
        self.settings_btn.config(state=tk.NORMAL if not connected else tk.DISABLED)
        self.chrome_btn.config(state=tk.DISABLED if not connected else tk.NORMAL)
        self.http_proxy_btn.config(state=tk.DISABLED if not connected else tk.NORMAL)
        self.traffic_btn.config(state=tk.DISABLED if not connected else tk.NORMAL)
        self.status_var.set("Connected" if connected else "Not Connected")
        self._draw_connection_indicator(connected)

    def _check_log_queue(self) -> None:
        """Checks log queue."""
        try:
            while True:
                message, level = self.log_queue.get_nowait()
                color = ColorMapping.GUI_COLORS.get(level, '#000000')
                self.log_display.append_colored_text(message, color)
        except queue.Empty:
            pass
        self.root.after(100, self._check_log_queue)


if __name__ == "__main__":
    root = tk.Tk()
    app = SSHProxyGUI(root)
    root.mainloop()
