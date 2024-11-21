import tkinter as tk
from gui import SSHProxyGUI
from config import ConfigManager


def main():
    # Создание дефолтного .env при первом запуске
    if not ConfigManager.load_config().host:
        ConfigManager.create_default_env()

    root = tk.Tk()
    SSHProxyGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

