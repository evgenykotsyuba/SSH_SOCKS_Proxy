from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def launch_chrome_with_socks_proxy(socks_host: str, socks_port: int, user_agent: str, home_page: str):
    """Launches Chrome with SOCKS proxy settings."""
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

    # Script to override the navigator.platform property
    script_to_override = """
    Object.defineProperty(navigator, 'platform', {
        get: () => 'Win32',
    });
    """

    # Launch the browser
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Execute the script to override the platform property
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": script_to_override
    })

    # Navigate to the specified home page
    driver.get(home_page)

    return driver


def chrome_browser(socks_port: int, user_agent: str, home_page: str):
    """Launches the Chrome browser with SOCKS proxy."""
    socks_host = 'localhost'
    driver = launch_chrome_with_socks_proxy(socks_host, socks_port, user_agent, home_page)

    # Return the driver object for GUI control
    return driver
