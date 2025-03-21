import logging
import time
import os
import platform
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Constants
INCOGNITO = False
USER_DATA_DIR = "./user/data"
PROFILE_DIR = "Profile"
DEFAULT_LANGUAGE = "en"
SOCKS_HOST = "localhost"
IMPLICIT_WAIT_SECONDS = 10
CHROMEDRIVER_PATH = "./chromedriver"  # Default path for local ChromeDriver

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_locale_configuration(language_setting: str) -> Dict:
    """Gets locale configuration for the specified language."""
    language_map = {
        "en": {"accept_language": "en-US,en;q=0.9",
               "timezone": {"name": "America/Los_Angeles", "offset": 480, "display": "Pacific Standard Time"}},
        "ru": {"accept_language": "ru-RU,ru;q=0.9",
               "timezone": {"name": "Europe/Moscow", "offset": -180, "display": "Moscow Standard Time"}},
        "ua": {"accept_language": "uk-UA,uk;q=0.9",
               "timezone": {"name": "Europe/Kiev", "offset": -120, "display": "Eastern European Standard Time"}},
        "fr": {"accept_language": "fr-FR,fr;q=0.9",
               "timezone": {"name": "Europe/Paris", "offset": -60, "display": "Central European Standard Time"}},
        "es": {"accept_language": "es-ES,es;q=0.9",
               "timezone": {"name": "Europe/Madrid", "offset": -60, "display": "Central European Standard Time"}},
        "cn": {"accept_language": "zh-CN,zh;q=0.9",
               "timezone": {"name": "Asia/Shanghai", "offset": -480, "display": "China Standard Time"}},
        "de": {"accept_language": "de-DE,de;q=0.9",
               "timezone": {"name": "Europe/Berlin", "offset": -60, "display": "Central European Standard Time"}},
    }
    return language_map.get(language_setting.lower(), language_map[DEFAULT_LANGUAGE])


def configure_chrome_options(socks_host: str, socks_port: int, user_agent: str, language_setting: str) -> Options:
    """Configures Chrome options for an anti-detect browser."""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument(f"--proxy-server=socks5://{socks_host}:{socks_port}")
    if INCOGNITO:
        options.add_argument("--incognito")
    options.add_argument(f"--user-agent={user_agent}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-features=UserAgentClientHint")

    locale_config = get_locale_configuration(language_setting)
    options.add_argument(f"--lang={language_setting.lower()}")
    options.add_argument(f"--accept-language={locale_config['accept_language']}")

    # WebGL and Canvas
    options.add_argument("--use-gl=desktop")
    options.add_argument("--ignore-gpu-blocklist")
    options.add_argument("--enable-webgl")
    options.add_argument("--enable-webgl2")
    options.add_argument("--enable-2d-canvas")

    # WebRTC protection
    options.add_argument("--force-webrtc-ip-handling-policy=default_public_interface_only")
    options.add_argument("--disable-features=WebRtcHideLocalIpsWithMdns,WebRtcAllowInputVolumeAdjustment")
    options.add_argument("--webrtc-ip-handling-policy=disable_non_proxied_udp")
    options.add_argument("--enable-features=WebRtcRemoteEventLog")
    # options.add_argument("--disable-rtc")
    # options.add_argument("--disable-peer-connection")
    # options.add_argument("--disable-webrtc")
    # options.add_argument("--force-webrtc-ip-handling-policy=disable_non_proxied_udp")
    # options.add_argument("--disable-features=WebRtcHideLocalIpsWithMdns")
    # options.add_argument("--enforce-webrtc-ip-permission-check")

    # Remove automation traces
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # User profile
    options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
    options.add_argument(f"--profile-directory={PROFILE_DIR}")

    return options


def get_chromedriver_path() -> Optional[str]:
    """Find local ChromeDriver or return None if not found."""
    # Check current directory first
    if os.path.exists(CHROMEDRIVER_PATH):
        if platform.system() == "Windows":
            return f"{CHROMEDRIVER_PATH}.exe"
        return CHROMEDRIVER_PATH

    # Check if chromedriver is in PATH
    for path in os.environ["PATH"].split(os.pathsep):
        exe_file = os.path.join(path, "chromedriver")
        if platform.system() == "Windows":
            exe_file += ".exe"
        if os.path.exists(exe_file):
            return exe_file

    # Additional common paths
    common_paths = [
        "/usr/local/bin/chromedriver",
        "/usr/bin/chromedriver",
        "C:\\Program Files\\ChromeDriver\\chromedriver.exe",
        "C:\\ChromeDriver\\chromedriver.exe"
    ]

    for path in common_paths:
        if os.path.exists(path):
            return path

    return None


def inject_scripts(driver: webdriver.Chrome, scripts: List[Dict]) -> webdriver.Chrome:
    """Injects scripts into the browser."""
    for script_info in scripts:
        try:
            if "script" in script_info:
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": script_info["script"]})
                logging.info(f"Successfully injected script: {script_info['name']}")
            elif "function" in script_info:
                driver = script_info["function"](driver)
                logging.info(f"Applied function: {script_info['name']}")
        except Exception as e:
            logging.error(f"Error injecting {script_info['name']}: {e}")
    return driver


def launch_browser(socks_port: int, user_agent: str, home_page: str, custom_title: str,
                   language_setting: str) -> webdriver.Chrome:
    """Launches Chrome with specified settings."""
    if not isinstance(socks_port, int):
        raise TypeError("SOCKS port must be an integer")
    if not (0 <= socks_port <= 65535):
        raise ValueError("SOCKS port must be between 0 and 65535")

    # Configure options
    chrome_options = configure_chrome_options(SOCKS_HOST, socks_port, user_agent, language_setting)
    locale_config = get_locale_configuration(language_setting)

    # Launch browser
    try:
        # Try to use WebDriver Manager first
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            logging.info("Using ChromeDriverManager to get driver")
        except Exception as e:
            logging.warning(f"Failed to use ChromeDriverManager: {e}")

            # Fall back to local ChromeDriver
            chromedriver_path = get_chromedriver_path()
            if chromedriver_path:
                logging.info(f"Using local ChromeDriver at: {chromedriver_path}")
                service = Service(executable_path=chromedriver_path)
            else:
                # Last resort - try without specifying path, hoping it's in PATH
                logging.warning("No ChromeDriver found, trying to use system default")
                service = Service()

        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(IMPLICIT_WAIT_SECONDS)
        logging.info("Browser successfully launched")
    except Exception as e:
        logging.error(f"Browser launch error: {e}")
        raise

    # Import dependencies only if browser launch was successful
    try:
        from chrome_os_info import OVERRIDE
        from user_agent_parser import parse_os_from_user_agent
        from chrome_tls_fingerprinting_protection import modify_tls_fingerprinting_protection
        from chrome_javascript_fingerprinting_protection import get_javascript_fingerprinting_protection_script, \
            get_navigator_protection_script
        from chrome_font_fingerprinting_protection import get_font_fingerprinting_protection_script
        from chrome_canvas_fingerprinting_protection import get_canvas_fingerprinting_protection_script
        from chrome_timezone_configuration import get_timezone_spoofing_script
        from chrome_webgl_fingerprinting_protection import modify_webgl_vendor_renderer, modify_webgl_textures
        from chrome_privacy_fingerprint_protection import modify_privacy_fingerprint
        from chrome_webrtc_protection import get_webrtc_protection_script
        from chrome_plugin_fingerprinting_protection import modify_plugins
        from chrome_audiocontext_fingerprinting_protection import modify_audiocontext
        from chrome_dtmg import dtmg_script

        # Prepare scripts for injection
        ua_os = parse_os_from_user_agent(user_agent)
        os_override_map = {
            "Windows": "Windows10_Chrome", "iOS": "iOS_Safari", "MacOS": "MacOS_Safari",
            "Android": "Android_Pixel_Chrome", "Linux": "Linux_Ubuntu_Firefox"
        }
        script_to_override = OVERRIDE.get(os_override_map.get(ua_os, "Unknown"))

        scripts = [
            {"name": "OS Override", "script": script_to_override},
            {"name": "Navigator Protection", "script": get_navigator_protection_script()},
            {"name": "WebGL Vendor", "function": modify_webgl_vendor_renderer},
            {"name": "WebGL Textures", "function": modify_webgl_textures},
            {"name": "Canvas Protection", "script": get_canvas_fingerprinting_protection_script()},
            {"name": "Font Protection", "script": get_font_fingerprinting_protection_script()},
            {"name": "WebRTC Protection", "script": get_webrtc_protection_script()},
            {"name": "Timezone Spoofing",
             "script": get_timezone_spoofing_script(locale_config["timezone"], locale_config["accept_language"])},
            {"name": "JavaScript Protection", "script": get_javascript_fingerprinting_protection_script()},
            {"name": "DTMG", "script": dtmg_script},
        ]

        # Inject scripts
        driver = inject_scripts(driver, scripts)
    except ImportError as e:
        logging.warning(f"Could not import some anti-fingerprinting modules: {e}")
        logging.warning("Browser will launch, but without full anti-detection capabilities")
    except Exception as e:
        logging.error(f"Error setting up anti-fingerprinting: {e}")
        logging.warning("Browser will launch, but without anti-detection capabilities")

    # Navigation and page setup
    try:
        driver.get(home_page)
        time.sleep(2)
        driver.execute_script(f"document.title = '{custom_title}';")
        logging.info(f"Page title set: {custom_title}")
    except Exception as e:
        logging.error(f"Error during navigation to {home_page}: {e}")
        logging.warning("Browser launched but page loading failed")

    return driver


def chrome_browser(socks_port: int, user_agent: str, home_page: str, custom_title: str,
                   language_setting: str) -> webdriver.Chrome:
    """Main function for launching an anti-detect browser."""
    try:
        driver = launch_browser(socks_port, user_agent, home_page, custom_title, language_setting)
        logging.info("Anti-detect browser successfully launched")
        return driver
    except Exception as e:
        logging.error(f"Error launching anti-detect browser: {e}")
        raise
