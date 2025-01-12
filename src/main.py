import tkinter as tk
import signal
import datetime
import os
import logging
import queue

from gui import SSHProxyGUI
from config import ConfigManager
from logging_handler import ColoredFormatter, ColoredLogHandler


def setup_logging(log_queue=None):
    """
    Configure logging for console, file, and optional GUI log queue.
    """
    # Set up log directory
    log_dir = os.path.join(os.getcwd(), "log")
    os.makedirs(log_dir, exist_ok=True)

    log_filename = os.path.join(log_dir, f"socks_proxy_{datetime.date.today()}.log")

    # Configure formatters
    console_formatter = ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s')
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Set up handlers
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(console_formatter)
    stream_handler.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.INFO)

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    # Add GUI log queue handler
    if log_queue:
        queue_handler = ColoredLogHandler(log_queue)
        queue_handler.setFormatter(file_formatter)  # Use non-colored format for the queue
        logger.addHandler(queue_handler)

    return logger


def handle_signal(signum):
    """
    Handle OS signals to ensure a graceful shutdown.
    """
    logging.info(f"Signal {signum} received. Shutting down gracefully...")
    if app and app.root:
        app.on_closing()


class Application:
    """
    Main Application class for managing the SSH Proxy GUI and logging.
    """

    def __init__(self):
        self.log_queue = queue.Queue()
        self.logger = setup_logging(self.log_queue)
        self.root = None

    def initialize_config(self):
        """
        Load or create default configuration.
        """
        try:
            config = ConfigManager.load_config()
            if not config.host:
                self.logger.info("No configuration found. Creating a default .env file.")
                ConfigManager.create_default_env()
        except Exception as e:
            self.logger.error(f"Error initializing configuration: {e}")
            raise

    def create_gui(self):
        """
        Initialize the GUI and pass the logging queue for real-time log updates.
        """
        try:
            self.root = tk.Tk()
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            SSHProxyGUI(self.root, self.log_queue)
        except Exception as e:
            self.logger.error(f"Failed to create GUI: {e}")
            raise

    def on_closing(self):
        """
        Perform cleanup when the application is closed.
        """
        self.logger.info("Shutting down application...")
        if self.root:
            self.root.destroy()

    def run(self):
        """
        Entry point to start the application.
        """
        try:
            # Register signal handlers
            signal.signal(signal.SIGINT, handle_signal)
            signal.signal(signal.SIGTERM, handle_signal)

            self.logger.info("Starting the application...")
            self.initialize_config()
            self.create_gui()

            if self.root:
                self.logger.info("Entering the main event loop.")
                self.root.mainloop()

        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received.")
            self.on_closing()
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise
        finally:
            self.logger.info("Application has terminated.")


def main():
    """
    Main function to initialize and run the application.
    """
    global app  # Make the app globally accessible for signal handlers
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
