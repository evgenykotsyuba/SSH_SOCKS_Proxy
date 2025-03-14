# chrome.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import logging
import time

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
    chrome_options.add_argument("--disable-features=UserAgentClientHint")
    chrome_options.add_argument(f"--user-agent={user_agent}")  # Set a custom User-Agent
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Remove WebDriver flag
    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--v=1")  # Enable detailed logging

    # Disable JavaScript fingerprinting
    chrome_options.add_argument("--disable-features=SiteIsolationForCrossOriginIframes")

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

    # Canvas - changed from disable to enable for better detection
    chrome_options.add_argument("--enable-2d-canvas")

    # Font fingerprinting protection
    chrome_options.add_argument("--disable-remote-fonts")  # Disable remote font loading
    chrome_options.add_argument("--font-render-hinting=none")  # Disable font hinting

    # Enhanced WebRTC disabling options
    chrome_options.add_argument("--disable-webrtc")
    chrome_options.add_argument("--enforce-webrtc-ip-permission-check")
    chrome_options.add_argument("--force-webrtc-ip-handling-policy=disable_non_proxied_udp")
    chrome_options.add_argument("--disable-features=WebRtcHideLocalIpsWithMdns")

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
        "webkit.webprefs.fonts_enabled": True,  # Changed to True to avoid detection
        "webkit.webprefs.default_font_size": 16,
        "webkit.webprefs.default_fixed_font_size": 16,

        # Changed to 1 for compatibility - prevents detection
        "browser.display.use_document_fonts": 1,

        # Language preferences
        "intl.accept_languages": accept_language,

        # DTMG
        "websocket.enabled": False,

        # JavaScript settings - ensure JS is enabled
        "javascript.enabled": True,

        # Ensure all content is visible
        "dom.disable_noscript": True,

        # Privacy settings
        "dom.disable_open_during_load": True,
        "plugins.click_to_play": True,
        "dom.disable_beforeunload": True,
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
        logging.info("Starting Chrome with proxy...")
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Important: Set page load strategy
        driver.implicitly_wait(10)  # Wait up to 10 seconds for elements to appear

        # Add TLS Fingerprint modification
        driver = modify_tls_fingerprinting_protection(driver)

        # Order of script injections matters for compatibility
        scripts_to_inject = [
            # First add essential fingerprinting protection
            {"name": "OS Override", "script": script_to_override},
            {"name": "Navigator Protection", "script": get_navigator_protection_script()},

            # Next add feature protections
            {"name": "WebGL Vendor and Renderer", "function": modify_webgl_vendor_renderer},
            {"name": "WebGL Textures", "function": modify_webgl_textures},
            {"name": "Privacy Fingerprint", "script": modify_privacy_fingerprint()},
            {"name": "Plugins", "script": modify_plugins()},
            {"name": "AudioContext", "script": modify_audiocontext()},

            # Then add specialized protection scripts
            {"name": "Canvas Protection", "script": get_canvas_fingerprinting_protection_script()},
            {"name": "Font Protection", "script": get_font_fingerprinting_protection_script()},
            {"name": "WebRTC Protection", "script": get_webrtc_protection_script()},

            # Language and timezone settings
            {"name": "Language Config", "script": f"""
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
            """},
            {"name": "Timezone Spoofing", "script": get_timezone_spoofing_script(tz_config, accept_language)},

            # JavaScript protection should be last to not interfere with other scripts
            {"name": "JavaScript Protection", "script": get_javascript_fingerprinting_protection_script()},

            # DTMG script last
            {"name": "DTMG Script", "script": dtmg_script}
        ]

        # Execute all scripts in order
        for script_info in scripts_to_inject:
            try:
                if "script" in script_info:
                    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                        "source": script_info["script"]
                    })
                    logging.info(f"Injected {script_info['name']} script")
                elif "function" in script_info:
                    driver = script_info["function"](driver)
                    logging.info(f"Applied {script_info['name']} function")
            except Exception as e:
                logging.error(f"Failed to inject {script_info['name']}: {e}")

        # Navigate to the specified home page
        driver.get(home_page)

        # Ensure page is fully loaded
        time.sleep(2)

        # Execute needed scripts directly on the page after load
        critical_post_load_scripts = [
            # Re-inject DTMG after loading
            dtmg_script,

            # Handle noscript elements specifically
            """
            (function() {
                // Remove all noscript elements
                const noscripts = document.querySelectorAll('noscript');
                noscripts.forEach(ns => {
                    if (ns && ns.parentNode) {
                        ns.parentNode.removeChild(ns);
                    }
                });

                // Add JS enabled classes and remove no-JS classes
                document.documentElement.classList.remove('no-js');
                document.documentElement.classList.add('js');

                document.querySelectorAll('.no-js, .js-disabled').forEach(el => {
                    el.style.display = 'none';
                });

                document.querySelectorAll('.js-enabled, [data-js-enabled]').forEach(el => {
                    el.style.display = '';
                });
            })();
            """
        ]

        for script in critical_post_load_scripts:
            try:
                driver.execute_script(script)
            except Exception as e:
                logging.error(f"Error executing post-load script: {e}")

        # Set the custom title using JavaScript
        driver.execute_script(f"document.title = `{custom_title}`;")
        logging.info(f"Page title set to: {custom_title}")

        return driver

    except Exception as e:
        logging.error(f"Failed to launch Chrome: {e}")
        raise


def chrome_browser(socks_port: int, user_agent: str, home_page: str, custom_title: str, language_setting: str):
    """Launches the Chrome browser with SOCKS proxy and sets a custom title."""
    if not isinstance(socks_port, int):
        raise TypeError("socks_port must be an integer")
    if socks_port < 0 or socks_port > 65535:
        raise ValueError("socks_port must be between 0 and 65535")

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
