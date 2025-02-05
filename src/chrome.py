# chrome.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import logging

from chrome_os_info import OVERRIDE
from user_agent_parser import parse_os_from_user_agent
from chrome_tls_fingerprinting_protection import modify_tls_fingerprinting_protection
from chrome_font_fingerprinting_protection import get_font_fingerprinting_protection_script
from canvas_fingerprinting_protection import get_canvas_fingerprinting_protection_script
from chrome_timezone_configuration import get_timezone_spoofing_script
from chrome_webgl_fingerprinting_protection import modify_webgl_vendor_renderer, modify_webgl_textures


def get_locale_configuration(language_setting: str) -> dict:
    """
    Returns a comprehensive locale configuration for a given language code.

    Args:
        language_setting (str): Two-letter language code (e.g., 'en', 'ru', 'fr')

    Returns:
        dict: Dictionary containing language, timezone, and locale configurations
    """
    language_map = {
        'en': {
            'accept_language': 'en-US,en;q=0.9',
            'timezone': {
                'name': 'America/Los_Angeles',
                'offset': 480,
                'display': 'Pacific Standard Time'
            }
        },
        'ru': {
            'accept_language': 'ru-RU,ru;q=0.9',
            'timezone': {
                'name': 'Europe/Moscow',
                'offset': -180,
                'display': 'Moscow Standard Time'
            }
        },
        'ua': {
            'accept_language': 'uk-UA,uk;q=0.9',
            'timezone': {
                'name': 'Europe/Kiev',
                'offset': -120,
                'display': 'Eastern European Standard Time'
            }
        },
        'fr': {
            'accept_language': 'fr-FR,fr;q=0.9',
            'timezone': {
                'name': 'Europe/Paris',
                'offset': -60,
                'display': 'Central European Standard Time'
            }
        },
        'es': {
            'accept_language': 'es-ES,es;q=0.9',
            'timezone': {
                'name': 'Europe/Madrid',
                'offset': -60,
                'display': 'Central European Standard Time'
            }
        },
        'cn': {
            'accept_language': 'zh-CN,zh;q=0.9',
            'timezone': {
                'name': 'Asia/Shanghai',
                'offset': -480,
                'display': 'China Standard Time'
            }
        },
        'de': {
            'accept_language': 'de-DE,de;q=0.9',
            'timezone': {
                'name': 'Europe/Berlin',
                'offset': -60,
                'display': 'Central European Standard Time'
            }
        }
    }

    # Default to English if language not found
    return language_map.get(language_setting.lower(), {
        'accept_language': 'en-US,en;q=0.9',
        'timezone': {
            'name': 'UTC',
            'offset': 0,
            'display': 'Coordinated Universal Time'
        }
    })


def launch_chrome_with_socks_proxy(socks_host: str, socks_port: int, user_agent: str, home_page: str,
                                   custom_title: str, language_setting: str):
    """Launches Chrome with SOCKS5 proxy settings and sets a custom title."""
    # Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument(f"--proxy-server=socks5://{socks_host}:{socks_port}")
    chrome_options.add_argument("--incognito")  # Enable incognito mode
    # chrome_options.add_argument("--disable-web-security")  # Disables security mechanisms
    chrome_options.add_argument(f"--user-agent={user_agent}")  # Set a custom User-Agent
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Remove WebDriver flag
    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--v=1")  # Enable detailed logging

    # Get comprehensive locale configuration
    locale_config = get_locale_configuration(language_setting)
    accept_language = locale_config['accept_language']
    lang_code = language_setting.lower()
    tz_config = locale_config['timezone']

    # Add language settings
    chrome_options.add_argument(f"--lang={lang_code}")
    chrome_options.add_argument(f"--accept-language={accept_language}")

    # WebGL fingerprinting protection
    chrome_options.add_argument("--use-gl=desktop")  # Enable hardware acceleration
    chrome_options.add_argument("--ignore-gpu-blocklist")  # Ignore GPU blocklist
    chrome_options.add_argument("--enable-webgl")  # Enable WebGL
    chrome_options.add_argument("--enable-webgl2")  # Enable WebGL2

    # Font fingerprinting protection
    chrome_options.add_argument("--disable-remote-fonts")  # Disable remote font loading
    chrome_options.add_argument("--font-render-hinting=none")  # Disable font hinting

    # Enhanced WebRTC disabling options
    chrome_options.add_argument("--disable-webrtc")
    chrome_options.add_argument("--enforce-webrtc-ip-permission-check")
    chrome_options.add_argument("--force-webrtc-ip-handling-policy=disable_non_proxied_udp")

    # Set WebRTC and font preferences
    prefs = {
        # WebRTC settings
        "webrtc.ip_handling_policy": "disable_non_proxied_udp",
        "webrtc.multiple_routes_enabled": False,
        "webrtc.nonproxied_udp_enabled": False,
        "webrtc.ipv6_default_handling_policy": "disable_non_proxied_udp",
        "webrtc.ice_candidate_policy": "none",
        "webrtc.ice_candidate_pool_size": 0,
        "webrtc.enabled": False,

        # Font fingerprinting protection
        "webkit.webprefs.fonts_enabled": False,
        "webkit.webprefs.default_font_size": 16,
        "webkit.webprefs.default_fixed_font_size": 16,
        "browser.display.use_document_fonts": 0,

        # Language preferences
        "intl.accept_languages": accept_language
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # Additional privacy-focused options
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-plugins-discovery")
    chrome_options.add_argument("--disable-bundled-ppapi-flash")
    chrome_options.add_argument("--disable-plugins-file")

    # Disable WebDriver automation detection
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # Define a dictionary of OS and configuration correspondences
    OS_OVERRIDE_MAP = {
        'Windows': 'Windows10_Chrome',
        'iOS': 'iOS_Safari',
        'MacOS': 'MacOS_Safari',
        'Android': 'Android_Pixel_Chrome',
        'Linux': 'Linux_Ubuntu_Firefox'
    }

    ua = parse_os_from_user_agent(user_agent)
    # Get configuration from dictionary, if not - use 'Unknown'
    script_to_override = OVERRIDE.get(OS_OVERRIDE_MAP.get(ua, 'Unknown'))

    try:
        # Launch the browser
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Add TLS Fingerprint modification
        driver = modify_tls_fingerprinting_protection(driver)

        # Execute the script to override OS detection properties
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": script_to_override
        })

        # Use the function from the new module for Canvas fingerprinting protection
        canvas_protection_script = get_canvas_fingerprinting_protection_script()
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": canvas_protection_script
        })

        # Use the function from the new module for font fingerprinting protection
        font_protection_script = get_font_fingerprinting_protection_script()
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": font_protection_script
        })

        # Modify WebGL Vendor and Renderer
        driver = modify_webgl_vendor_renderer(driver)
        driver = modify_webgl_textures(driver)

        # Updated language configuration script
        language_config_script = f"""
                    // Override navigator.language and navigator.languages
                    Object.defineProperty(navigator, 'language', {{
                        get: () => '{lang_code}'
                    }});

                    Object.defineProperty(navigator, 'languages', {{
                        get: () => ['{accept_language.split(',')[0]}', '{lang_code}']
                    }});

                    // Override Accept-Language header
                    Object.defineProperty(navigator, 'acceptLanguages', {{
                        get: () => '{accept_language}'
                    }});
                    """

        # Use the function from the new module to spoof the timezone
        timezone_spoofing_script = get_timezone_spoofing_script(tz_config, accept_language)

        # Execute protection scripts
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": language_config_script
        })
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": timezone_spoofing_script
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


def chrome_browser(socks_port: int, user_agent: str, home_page: str, custom_title: str, language_setting: str):
    """Launches the Chrome browser with SOCKS proxy and sets a custom title."""
    socks_host = 'localhost'
    try:
        # Launch the browser and return the driver for control
        driver = launch_chrome_with_socks_proxy(socks_host,
                                                socks_port,
                                                user_agent,
                                                home_page,
                                                custom_title,
                                                language_setting)
        logging.info("Chrome browser launched successfully.")
        return driver
    except Exception as e:
        logging.error(f"Error launching Chrome browser: {e}")
        raise
