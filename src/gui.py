import os
import tkinter as tk
import traceback
from tkinter import ttk, messagebox, scrolledtext
import threading
import queue
import logging
import asyncio
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
from gui_settings import SettingsWindow  # Добавлен импорт


class SSHProxyGUI:
    def __init__(self, root: tk.Tk, log_queue: queue.Queue):
        # self.root = tk.Tk()
        # self.config = SSHConfig(...)  # Ваша конфигурация
        # self.selected_language = tk.StringVar()
        #
        self.root: tk.Tk = root
        self.log_queue: queue.Queue = log_queue
        self.config: SSHConfig = ConfigManager.load_config()

        self.ssh_client: Optional[SSHClient] = None
        self.connection_thread: Optional[threading.Thread] = None
        self.log_enabled: bool = False
        self.traffic_window: Optional[tk.Toplevel] = None
        self.traffic_monitor: Optional[PortTrafficMonitor] = None
        self.traffic_task: Optional[asyncio.Task] = None
        self.loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        self.traffic_running: bool = False

        self.root.geometry("880x90")
        self._update_window_title()

        self._setup_logging()
        self.selected_language: tk.StringVar = tk.StringVar(value=self.config.selected_language)
        self._create_gui()
        self._check_log_queue()

    def _update_window_title(self) -> None:
        connection_name = getattr(self.config, 'connection_name', None) or "Default"
        self.root.title(f"SSH SOCKS Proxy - {connection_name}")

    def _setup_logging(self) -> None:
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
        self.chrome_btn = ttk.Button(btn_frame, text="Chrome", command=self._run_chrome_browser, state=tk.DISABLED)
        self.chrome_btn.pack(side=tk.LEFT, padx=5)
        self.chrome_btn.bind("<Enter>", lambda event: self.status_var.set("Chrome browser - Incognito Tab"))
        self.chrome_btn.bind("<Leave>", lambda event: self.status_var.set(""))
        self.http_proxy_btn = ttk.Button(btn_frame, text="HTTP Proxy", command=self._run_http_proxy, state=tk.DISABLED)
        self.http_proxy_btn.pack(side=tk.LEFT, padx=5)
        self.http_proxy_btn.bind("<Enter>", lambda event: self.status_var.set("HTTP proxy over SOCKS5"))
        self.http_proxy_btn.bind("<Leave>", lambda event: self.status_var.set(""))
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
        status_label = ttk.Label(self.status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_label.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        self.status_canvas = tk.Canvas(self.status_frame, width=20, height=20, highlightthickness=0,
                                       background=self.root.winfo_toplevel().cget('background'))
        self.status_canvas.pack(side=tk.RIGHT, padx=5)
        self._draw_connection_indicator(False)

        self._update_texts()

    def _draw_connection_indicator(self, connected: bool) -> None:
        self.status_canvas.delete("all")
        color = "green" if connected else "red"
        self.status_canvas.create_oval(3, 3, 17, 17, fill=color, outline=color)

    def _toggle_logs(self) -> None:
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

    def _start_connection(self) -> None:
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

    def _run_connection(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        run_check_banner(self.config.host, self.config.port)
        try:
            self.ssh_client = SSHClient(self.config, status_callback=self._update_connection_status)
            loop.run_until_complete(self.ssh_client.manage_connection())
        except SSHConnectionError as e:
            logging.error(str(e))
        finally:
            loop.close()
            self._update_gui_state(connected=False)

    def _update_connection_status(self, connected: bool) -> None:
        self._update_gui_state(connected)

    def _stop_connection(self) -> None:
        if self.ssh_client:
            self._close_chrome_browser()
            self.chrome_btn.config(state=tk.DISABLED)
            self._close_http_proxy()
            self.http_proxy_btn.config(state=tk.DISABLED)
            self.ssh_client.stop()

    def _show_settings(self) -> None:
        SettingsWindow(self.root, self)

    def _update_texts(self) -> None:
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

    def _run_http_proxy(self) -> None:
        try:
            translations = TRANSLATIONS.get(self.selected_language.get(), TRANSLATIONS["en"])
            socks_port = self.config.dynamic_port
            http_port = self.config.http_proxy_port
            self.proxy = SOCKStoHTTPProxy(http_port=http_port, socks_port=socks_port)
            self.proxy_thread = threading.Thread(target=self.proxy.start, daemon=True)
            self.proxy_thread.start()
            logging.info(f"HTTP Proxy started on port {http_port} with SOCKS Proxy connection on port {socks_port}")
            self.http_proxy_btn.config(text=translations["Disconnect Proxy"], command=self._close_http_proxy)
        except ValueError as e:
            logging.error(f"Error starting the HTTP Proxy: {e}")
        except Exception as e:
            logging.error(f"Unknown error: {e}")
            logging.error(traceback.format_exc())

    def _close_http_proxy(self) -> None:
        try:
            translations = TRANSLATIONS.get(self.selected_language.get(), TRANSLATIONS["en"])
            self.http_proxy_btn.config(state=tk.DISABLED)
            if hasattr(self, 'proxy') and self.proxy:
                self.proxy.stop()
                if hasattr(self, 'proxy_thread') and self.proxy_thread.is_alive():
                    self.proxy_thread.join(timeout=2)
                self.proxy = None
                self.proxy_thread = None
                logging.info("HTTP Proxy disconnected successfully")
        except Exception as e:
            logging.error(f"Error during HTTP Proxy disconnection: {e}")
            logging.error(traceback.format_exc())
        finally:
            self.http_proxy_btn.config(text=translations["HTTP Proxy"], command=self._run_http_proxy, state=tk.NORMAL)

    def _run_chrome_browser(self) -> None:
        try:
            translations = TRANSLATIONS.get(self.selected_language.get(), TRANSLATIONS["en"])
            socks_port = self.config.dynamic_port
            user_agent = self.config.user_agent
            home_page = self.config.home_page
            language_setting = self.config.selected_language

            def start_browser():
                try:
                    custom_title = self.config.connection_name + ': ' + self.config.home_page.replace("https://", "")
                    self.browser_driver = chrome_browser(socks_port, user_agent, home_page, custom_title,
                                                         language_setting)
                except Exception as e:
                    logging.error(f"Error launching Chrome browser: {e}")
                    messagebox.showerror("Error", f"Failed to launch Chrome: {str(e)}")

            self.chrome_thread = threading.Thread(target=start_browser, daemon=True)
            self.chrome_thread.start()
            self.chrome_btn.config(text=translations["Close Chrome"], command=self._close_chrome_browser)
        except Exception as e:
            logging.error(f"Error in Chrome browser launch: {e}")
            messagebox.showerror("Error", f"Failed to start Chrome: {str(e)}")

    def _close_chrome_browser(self) -> None:
        translations = TRANSLATIONS.get(self.selected_language.get(), TRANSLATIONS["en"])
        try:
            if hasattr(self, 'browser_driver') and self.browser_driver:
                self.browser_driver.quit()
                self.browser_driver = None
                logging.info("Chrome browser closed.")
            if hasattr(self, 'chrome_thread') and self.chrome_thread.is_alive():
                self.chrome_thread.join(timeout=1)
            self.chrome_btn.config(text=translations["Chrome"], command=self._run_chrome_browser)
        except Exception as e:
            logging.error(f"Error closing Chrome browser: {e}")
            messagebox.showerror("Error", f"Failed to close Chrome: {str(e)}")

    def _show_help(self) -> None:
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

    def _check_log_queue(self) -> None:
        if not hasattr(self, 'log_display'):
            self.root.after(100, self._check_log_queue)
            return
        try:
            while True:
                message, level = self.log_queue.get_nowait()
                color = ColorMapping.GUI_COLORS.get(level, '#000000')
                self.log_display.append_colored_text(message, color)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._check_log_queue)

    def _update_gui_state(self, connected: bool) -> None:
        self.connect_btn.config(state=tk.NORMAL if not connected else tk.DISABLED)
        self.disconnect_btn.config(state=tk.DISABLED if not connected else tk.NORMAL)
        self.settings_btn.config(state=tk.NORMAL if not connected else tk.DISABLED)
        self.chrome_btn.config(state=tk.DISABLED if not connected else tk.NORMAL)
        self.http_proxy_btn.config(state=tk.DISABLED if not connected else tk.NORMAL)
        self.traffic_btn.config(state=tk.DISABLED if not connected else tk.NORMAL)
        self.status_var.set("Connected" if connected else "Not Connected")
        self._draw_connection_indicator(connected)
        self._update_window_title()

    def _create_traffic_window(self) -> None:
        translations = TRANSLATIONS.get(self.selected_language.get(), TRANSLATIONS["en"])
        if self.traffic_window is None:
            self.traffic_window = tk.Toplevel(self.root)
            self.traffic_window.title(f"Port {self.config.dynamic_port} Traffic Monitor")
            self.traffic_window.geometry("400x300")
            self.traffic_window.protocol("WM_DELETE_WINDOW", self._close_traffic_monitor)
            self.traffic_window.transient(self.root)
            main_frame = ttk.Frame(self.traffic_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            stats_frame = ttk.LabelFrame(main_frame, text=translations["Traffic Statistics"])
            stats_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            stats_frame.grid_columnconfigure(1, weight=1)
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
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(fill=tk.X, pady=5)
            self.traffic_btn_frame = btn_frame

    def _start_traffic_monitoring(self) -> None:
        if not self.traffic_running:
            self.traffic_running = True
            if self.loop is None or self.loop.is_closed():
                self.loop = asyncio.new_event_loop()
            def run_async_loop():
                try:
                    asyncio.set_event_loop(self.loop)
                    self.traffic_monitor = PortTrafficMonitor(self.config.dynamic_port, self._update_traffic_display)
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

    def _add_reset_button(self) -> None:
        translations = TRANSLATIONS.get(self.selected_language.get(), TRANSLATIONS["en"])
        if hasattr(self, 'reset_counters_btn'):
            self.reset_counters_btn.destroy()
        self.reset_counters_btn = ttk.Button(self.traffic_btn_frame, text=translations["Reset Counters"],
                                             command=self.traffic_monitor.reset_counters)
        self.reset_counters_btn.pack(side=tk.LEFT, padx=5)

    def _toggle_traffic_monitor(self) -> None:
        if self.traffic_window is None:
            self._create_traffic_window()
            self._start_traffic_monitoring()
        else:
            self._close_traffic_monitor()

    def _update_traffic_display(self, stats: Dict[str, Any]) -> None:
        if self.traffic_window and not self.traffic_window.winfo_exists():
            self._close_traffic_monitor()
            return
        try:
            if self.traffic_window:
                self.traffic_window.after(0, self._update_traffic_labels, stats)
        except tk.TclError:
            self._close_traffic_monitor()

    def _update_traffic_labels(self, stats: Dict[str, Any]) -> None:
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
            self._close_traffic_monitor()

    def _close_traffic_monitor(self) -> None:
        try:
            if self.traffic_monitor:
                self.traffic_monitor.stop_monitoring()
                self.traffic_running = False
            if self.traffic_task and not self.traffic_task.done():
                self.traffic_task.cancel()
            if self.loop and not self.loop.is_closed():
                self.loop.call_soon_threadsafe(self.loop.stop)
                if self.monitor_thread and self.monitor_thread.is_alive():
                    self.monitor_thread.join(timeout=2)
                if not self.loop.is_closed():
                    self.loop.close()
            if self.traffic_window:
                self.traffic_window.destroy()
                self.traffic_window = None
                self.traffic_labels = {}
        except Exception as e:
            logging.error(f"Error during traffic monitor cleanup: {e}")
            if self.traffic_window:
                self.traffic_window.destroy()
                self.traffic_window = None
