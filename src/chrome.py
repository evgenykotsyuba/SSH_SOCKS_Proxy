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
        "browser.display.use_document_fonts": 0
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

        # Execute the script to override OS detection properties
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": script_to_override
        })

        # Canvas fingerprinting protection script
        canvas_protection_script = """
        (function() {
            // Store original functions
            const originalGetContext = HTMLCanvasElement.prototype.getContext;
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            const originalToBlob = HTMLCanvasElement.prototype.toBlob;
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;

            // Helper to add subtle noise to canvas data
            function addNoise(data) {
                const noise = 5;  // Small noise value
                for (let i = 0; i < data.length; i += 4) {
                    data[i] = Math.max(0, Math.min(255, data[i] + (Math.random() * 2 - 1) * noise));     // Red
                    data[i+1] = Math.max(0, Math.min(255, data[i+1] + (Math.random() * 2 - 1) * noise)); // Green
                    data[i+2] = Math.max(0, Math.min(255, data[i+2] + (Math.random() * 2 - 1) * noise)); // Blue
                    // Alpha channel remains unchanged
                }
                return data;
            }

            // Override getContext
            HTMLCanvasElement.prototype.getContext = function(type, attributes) {
                const context = originalGetContext.call(this, type, attributes);
                if (context && (type === '2d' || type === 'webgl' || type === 'experimental-webgl')) {
                    // Add noise to text rendering
                    const originalFillText = context.fillText;
                    context.fillText = function(...args) {
                        const result = originalFillText.apply(this, args);
                        // Add subtle randomization to text position
                        this.translate((Math.random() * 2 - 1) * 0.5, (Math.random() * 2 - 1) * 0.5);
                        return result;
                    };
                }
                return context;
            };

            // Override toDataURL
            HTMLCanvasElement.prototype.toDataURL = function(...args) {
                const context = this.getContext('2d');
                if (context) {
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    const pixels = imageData.data;
                    addNoise(pixels);
                    context.putImageData(imageData, 0, 0);
                }
                return originalToDataURL.apply(this, args);
            };

            // Override toBlob
            HTMLCanvasElement.prototype.toBlob = function(callback, ...args) {
                const context = this.getContext('2d');
                if (context) {
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    const pixels = imageData.data;
                    addNoise(pixels);
                    context.putImageData(imageData, 0, 0);
                }
                return originalToBlob.call(this, callback, ...args);
            };

            // Override getImageData
            CanvasRenderingContext2D.prototype.getImageData = function(...args) {
                const imageData = originalGetImageData.apply(this, args);
                imageData.data = addNoise(imageData.data);
                return imageData;
            };

            // Notify attempts to access canvas
            console.warn("Canvas fingerprinting protection active");
        })();
        """

        # Font fingerprinting protection via JavaScript
        font_protection_script = """
        // Override font-related APIs
        function protectFonts() {
            // Override font enumeration
            Object.defineProperty(document, 'fonts', {
                get: () => ({
                    ready: Promise.resolve(),
                    check: () => false,
                    load: () => Promise.reject(),
                    addEventListener: () => {},
                    removeEventListener: () => {}
                })
            });

            // Standardize font measurement
            if (HTMLCanvasElement.prototype.measureText) {
                const originalMeasureText = HTMLCanvasElement.prototype.measureText;
                HTMLCanvasElement.prototype.measureText = function(text) {
                    return {
                        width: text.length * 8,
                        actualBoundingBoxAscent: 8,
                        actualBoundingBoxDescent: 2,
                        fontBoundingBoxAscent: 8,
                        fontBoundingBoxDescent: 2
                    };
                };
            }

            // Override font loading
            if (window.FontFace) {
                window.FontFace = function() {
                    return {
                        load: () => Promise.reject(),
                        loaded: Promise.reject(),
                        status: 'error',
                        family: 'sans-serif'
                    };
                };
            }
        }
        protectFonts();

        // Monitor and reapply protection
        setInterval(protectFonts, 1000);
        """

        # Execute both protection scripts
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": canvas_protection_script
        })
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": font_protection_script
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
