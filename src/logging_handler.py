import logging
import tkinter as tk
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)


class ColorMapping:
    """Defines color mappings for both console and GUI."""
    CONSOLE_COLORS = {
        logging.DEBUG: Fore.BLUE,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    GUI_COLORS = {
        logging.DEBUG: '#0000FF',  # Blue
        logging.INFO: '#008000',  # Green
        logging.WARNING: '#FFA500',  # Orange
        logging.ERROR: '#FF0000',  # Red
        logging.CRITICAL: '#8B0000',  # Dark Red
    }


class ColoredFormatter(logging.Formatter):
    """Custom logging formatter for colored console output."""

    def format(self, record):
        color = ColorMapping.CONSOLE_COLORS.get(record.levelno, "")
        reset = Style.RESET_ALL
        record.msg = f"{color}{record.msg}{reset}"
        return super().format(record)


class ColoredLogHandler(logging.Handler):
    """A logging handler that adds colored logs to a queue for GUI display."""

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        try:
            msg = self.format(record)
            # Put both message and level as a tuple
            self.log_queue.put((msg, record.levelno))
        except Exception:
            self.handleError(record)


class ColoredLogQueue(tk.scrolledtext.ScrolledText):
    """A custom ScrolledText widget that supports colored text output."""

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.tag_config('DEBUG', foreground=ColorMapping.GUI_COLORS[logging.DEBUG])
        self.tag_config('INFO', foreground=ColorMapping.GUI_COLORS[logging.INFO])
        self.tag_config('WARNING', foreground=ColorMapping.GUI_COLORS[logging.WARNING])
        self.tag_config('ERROR', foreground=ColorMapping.GUI_COLORS[logging.ERROR])
        self.tag_config('CRITICAL', foreground=ColorMapping.GUI_COLORS[logging.CRITICAL])

    def append_colored_text(self, message, color):
        """Append text with color to the widget."""
        self.config(state=tk.NORMAL)
        end_index = self.index(tk.END)
        self.insert(tk.END, message + '\n')

        # Create a unique tag for this color
        tag_name = f"color_{color.replace('#', '')}"
        self.tag_config(tag_name, foreground=color)

        # Apply the color tag to the last line
        line_start = f"{float(end_index) - 1.0}"
        self.tag_add(tag_name, line_start, end_index)

        self.see(tk.END)
        self.config(state=tk.DISABLED)
