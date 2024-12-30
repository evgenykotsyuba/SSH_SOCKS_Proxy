import tkinter as tk
import sys
import signal
from gui import SSHProxyGUI
from config import ConfigManager
import datetime
import os
import logging


def setup_logging():
    """Configure basic logging for the application."""

    # Determine the log directory (cross-platform)
    log_dir = os.path.join(os.getcwd(), "log")
    os.makedirs(log_dir, exist_ok=True)

    log_filename = os.path.join(log_dir, f"socks_proxy_{datetime.date.today()}.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_filename)
        ]
    )
    return logging.getLogger(__name__)


def signal_handler(signum, frame):
    """Handle system signals gracefully."""
    logger = logging.getLogger(__name__)
    logger.info(f"Received signal {signum}. Shutting down...")
    sys.exit(0)


class Application:
    def __init__(self):
        self.logger = setup_logging()
        self.root = None

    def initialize_config(self):
        """Initialize configuration with error handling."""
        try:
            if not ConfigManager.load_config().host:
                self.logger.info("No configuration found. Creating default .env file")
                ConfigManager.create_default_env()
        except Exception as e:
            self.logger.error(f"Failed to initialize configuration: {e}")
            raise

    def create_gui(self):
        """Create and configure the main GUI window."""
        try:
            self.root = tk.Tk()
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            SSHProxyGUI(self.root)
        except Exception as e:
            self.logger.error(f"Failed to create GUI: {e}")
            raise

    def on_closing(self):
        """Handle window closing event."""
        self.logger.info("Application shutting down...")
        if self.root:
            self.root.destroy()

    def run(self):
        """Main application entry point with error handling."""
        try:
            # Register signal handlers
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            self.logger.info("Starting application...")
            self.initialize_config()
            self.create_gui()

            if self.root:
                self.logger.info("Entering main event loop")
                self.root.mainloop()

        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
            self.on_closing()
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise
        finally:
            self.logger.info("Application terminated")


def main():
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
