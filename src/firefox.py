from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from webdriver_manager.firefox import GeckoDriverManager
import logging

from chrome_os_info import OVERRIDE  # Assuming we'll adapt this for Firefox
from user_agent_parser import parse_os_from_user_agent
# Assuming we'll need to create a firefox_tls_fingerprint module
from firefox_tls_fingerprint import modify_tls_fingerprint


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


def launch_firefox_with_socks_proxy(socks_host: str, socks_port: int, user_agent: str, home_page: str,
                                   custom_title: str, language_setting: str):
    """Launches Firefox with SOCKS5 proxy settings and sets a custom title."""
    # Firefox options
    firefox_options = Options()
    
    # Get comprehensive locale configuration
    locale_config = get_locale_configuration(language_setting)
    accept_language = locale_config['accept_language']
    lang_code = language_setting.lower()
    tz_config = locale_config['timezone']

    # Configure Firefox preferences
    firefox_options.set_preference("network.proxy.type", 1)
    firefox_options.set_preference("network.proxy.socks", socks_host)
    firefox_options.set_preference("network.proxy.socks_port", socks_port)
    firefox_options.set_preference("network.proxy.socks_version", 5)
    
    # Privacy and security settings
    firefox_options.set_preference("privacy.resistFingerprinting", True)
    firefox_options.set_preference("webgl.disabled", True)
    firefox_options.set_preference("media.peerconnection.enabled", False)  # Disable WebRTC
    firefox_options.set_preference("dom.webrtc.enabled", False)
    
    # Language and locale settings
    firefox_options.set_preference("intl.accept_languages", accept_language)
    firefox_options.set_preference("general.useragent.override", user_agent)
    
    # Font fingerprinting protection
    firefox_options.set_preference("browser.display.use_document_fonts", 0)
    firefox_options.set_preference("gfx.downloadable_fonts.enabled", False)
    
    # Additional privacy settings
    firefox_options.set_preference("privacy.trackingprotection.enabled", True)
    firefox_options.set_preference("network.cookie.cookieBehavior", 1)
    firefox_options.set_preference("browser.privatebrowsing.autostart", True)
    
    # Timezone preferences
    firefox_options.set_preference("intl.timezone.automatic", False)
    firefox_options.set_preference("intl.timezone.override", tz_config['name'])

    # Define OS override configuration
    OS_OVERRIDE_MAP = {
        'Windows': 'Windows10_Firefox',
        'iOS': 'iOS_Firefox',
        'MacOS': 'MacOS_Firefox',
        'Android': 'Android_Firefox',
        'Linux': 'Linux_Ubuntu_Firefox'
    }

    ua = parse_os_from_user_agent(user_agent)
    script_to_override = OVERRIDE.get(OS_OVERRIDE_MAP.get(ua, 'Unknown'))

    try:
        # Launch the browser
        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=firefox_options)
        
        # Modify TLS fingerprint
        driver = modify_tls_fingerprint(driver)

        # Execute the script to override OS detection properties
        driver.execute_script(script_to_override)

        # Canvas fingerprinting protection script
        canvas_protection_script = """
            (function() {
                const originalGetContext = HTMLCanvasElement.prototype.getContext;
                const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                const originalToBlob = HTMLCanvasElement.prototype.toBlob;
                
                function addNoise(data) {
                    const noise = 5;
                    for (let i = 0; i < data.length; i += 4) {
                        data[i] = Math.max(0, Math.min(255, data[i] + (Math.random() * 2 - 1) * noise));
                        data[i+1] = Math.max(0, Math.min(255, data[i+1] + (Math.random() * 2 - 1) * noise));
                        data[i+2] = Math.max(0, Math.min(255, data[i+2] + (Math.random() * 2 - 1) * noise));
                    }
                    return data;
                }

                HTMLCanvasElement.prototype.getContext = function(type, attributes) {
                    const context = originalGetContext.call(this, type, attributes);
                    if (context) {
                        const originalGetImageData = context.getImageData;
                        context.getImageData = function(...args) {
                            const imageData = originalGetImageData.apply(this, args);
                            imageData.data = addNoise(imageData.data);
                            return imageData;
                        };
                    }
                    return context;
                };
            })();
        """

        # Language and timezone configuration script
        locale_script = f"""
            Object.defineProperty(navigator, 'language', {{
                get: () => '{lang_code}'
            }});

            Object.defineProperty(navigator, 'languages', {{
                get: () => ['{accept_language.split(',')[0]}', '{lang_code}']
            }});

            const originalDate = Date;
            Date.prototype.getTimezoneOffset = function() {{
                return {tz_config['offset']};
            }};
        """

        # Execute protection scripts
        driver.execute_script(canvas_protection_script)
        driver.execute_script(locale_script)

        # Navigate to the specified home page
        driver.get(home_page)

        # Set the custom title
        driver.execute_script(f"document.title = '{custom_title}';")
        logging.info(f"Page title set to: {custom_title}")

        return driver

    except Exception as e:
        logging.error(f"Failed to launch Firefox: {e}")
        raise


def firefox_browser(socks_port: int, user_agent: str, home_page: str, custom_title: str, language_setting: str):
    """Launches the Firefox browser with SOCKS proxy and sets a custom title."""
    socks_host = 'localhost'
    try:
        driver = launch_firefox_with_socks_proxy(socks_host,
                                               socks_port,
                                               user_agent,
                                               home_page,
                                               custom_title,
                                               language_setting)
        logging.info("Firefox browser launched successfully.")
        return driver
    except Exception as e:
        logging.error(f"Error launching Firefox browser: {e}")
        raise
