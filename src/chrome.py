from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import logging

from chrome_os_info import OVERRIDE
from user_agent_parser import parse_os_from_user_agent


def launch_chrome_with_socks_proxy(socks_host: str, socks_port: int, user_agent: str, home_page: str,
                                   custom_title: str):
    """Launches Chrome with SOCKS5 proxy settings and sets a custom title."""
    # Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument(f"--proxy-server=socks5://{socks_host}:{socks_port}")
    chrome_options.add_argument("--incognito")  # Enable incognito mode
    chrome_options.add_argument(f"--user-agent={user_agent}")  # Set a custom User-Agent
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Remove WebDriver flag
    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--v=1")  # Enable detailed logging
    # Disable WebDriver automation detection
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    ua = parse_os_from_user_agent(user_agent)

    # Script to override the navigator.platform property and other OS detection methods
    if ua == 'Windows':
        script_to_override = OVERRIDE.get("Windows10_Chrome")
    elif ua == 'MacOS':
        script_to_override = OVERRIDE.get("MacOS_Safari")
    elif ua == 'Android':
        script_to_override = OVERRIDE.get("Android_Pixel_Chrome")
    elif ua == 'Linux':
        script_to_override = OVERRIDE.get("Linux_Ubuntu_Firefox")
    else:
        script_to_override = OVERRIDE.get("Unknown")

    try:
        # Launch the browser
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Execute the script to override OS detection properties
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": script_to_override
        })

        # Navigate to the specified home page
        driver.get(home_page)

        # Set the custom title using JavaScript
        driver.execute_script(f"document.title = `{custom_title}`;")
        logging.info(f"Page title set to: {custom_title}")

        return driver

    except Exception as e:
        logging.error(f"Failed to launch Chrome: {e}")
        raise


def chrome_browser(socks_port: int, user_agent: str, home_page: str, custom_title: str):
    """Launches the Chrome browser with SOCKS proxy and sets a custom title."""
    socks_host = 'localhost'
    try:
        # Launch the browser and return the driver for control
        driver = launch_chrome_with_socks_proxy(socks_host, socks_port, user_agent, home_page, custom_title)
        logging.info("Chrome browser launched successfully.")
        return driver
    except Exception as e:
        logging.error(f"Error launching Chrome browser: {e}")
        raise