# tests/test_selenium_javascript.py

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import sys
import os
import logging
import json
import argparse
from typing import Dict, Optional

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Get the absolute path to the project root directory
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# Add project root and src directory to Python path
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

# Test HTML page for comprehensive testing
TEST_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
</head>
<body>
    <script src="https://example.com/external.js"></script>
    <iframe src="https://example.com/iframe"></iframe>
    <img src="https://example.com/image.jpg">
    <noscript>No JS content</noscript>
    <div class="js-enabled" style="display:none">JS Enabled</div>
    <div class="no-js">No JS</div>
    <script>
        document.write('<script src="https://example.com/injected.js"></script>');
    </script>
</body>
</html>
"""


def get_javascript_fingerprinting_protection_script() -> str:
    return """
    (function() {
        const applyCsp = () => {
            const cspMeta = document.createElement('meta');
            cspMeta.httpEquiv = 'Content-Security-Policy';
            cspMeta.content = "default-src 'self'; script-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self';";
            if (document.head) {
                if (document.head.firstChild) {
                    document.head.insertBefore(cspMeta, document.head.firstChild);
                } else {
                    document.head.appendChild(cspMeta);
                }
            }
        };
        applyCsp();
        document.addEventListener('DOMContentLoaded', applyCsp);

        const isExternalResource = (url) => {
            if (!url) return false;
            try {
                const absoluteUrl = new URL(url, window.location.href);
                return absoluteUrl.origin !== window.location.origin && !url.startsWith('data:') && !url.startsWith('blob:') && !url.startsWith('about:');
            } catch (e) {
                return false;
            }
        };

        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (!node.tagName) return;
                    const tagName = node.tagName.toLowerCase();
                    if (tagName === 'script' && node.src && isExternalResource(node.src)) {
                        node.remove();
                        return;
                    }
                    if (['iframe', 'img', 'link', 'object', 'embed'].includes(tagName) && node.src && isExternalResource(node.src)) {
                        if (tagName === 'img') {
                            node.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="1" height="1"%3E%3C/svg%3E';
                        } else {
                            node.remove();
                        }
                    }
                    if (tagName === 'noscript') {
                        const div = document.createElement('div');
                        div.style.display = 'none';
                        node.parentNode.replaceChild(div, node);
                    }
                });
            });
        });
        observer.observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ['src'] });

        window.eval = function(code) { return null; };
        window.Function = function(...args) { return () => {}; };
        window.WebAssembly = undefined;

        const originalWrite = document.write;
        document.write = function(...args) {
            const content = args.join('');
            if (content.includes('<script') || content.includes('<iframe')) {
                return;
            }
            const sanitizedContent = content.replace(/<noscript[^>]*>(.*?)<\\/noscript>/gi, '');
            originalWrite.call(document, sanitizedContent);
        };

        const originalCreateElement = document.createElement;
        document.createElement = function(tagName, options) {
            const tag = typeof tagName === 'string' ? tagName.toLowerCase() : tagName;
            if (tag === 'script') {
                const safeScript = originalCreateElement.call(document, 'script', options);
                const originalSetAttribute = safeScript.setAttribute;
                safeScript.setAttribute = function(name, value) {
                    if (name.toLowerCase() === 'src' && isExternalResource(value)) {
                        return;
                    }
                    originalSetAttribute.call(this, name, value);
                };
                return safeScript;
            }
            if (tag === 'noscript') {
                const div = originalCreateElement.call(document, 'div', options);
                div.style.display = 'none';
                return div;
            }
            return originalCreateElement.call(document, tagName, options);
        };
    })();
    """


def get_navigator_protection_script() -> str:
    return """
    (function() {
        const navigatorProps = {
            javaEnabled: { value: () => false, writable: false },
            webdriver: { value: false, writable: false },
            languages: { value: ['en-US', 'en'], writable: false },
            plugins: { 
                get: function() {
                    const fakePlugins = Object.create(PluginArray.prototype);
                    fakePlugins.length = 0;
                    return fakePlugins;
                },
                writable: false
            },
            mimeTypes: {
                get: function() {
                    const fakeMimeTypes = Object.create(MimeTypeArray.prototype);
                    fakeMimeTypes.length = 0;
                    return fakeMimeTypes;
                },
                writable: false
            }
        };
        for (const prop in navigatorProps) {
            try {
                Object.defineProperty(navigator, prop, navigatorProps[prop]);
            } catch (e) {}
        }
    })();
    """


def setup_driver(headless: bool = False) -> Optional[webdriver.Chrome]:
    """Sets up and launches WebDriver with additional options."""
    chrome_options = Options()
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    if headless:
        chrome_options.add_argument("--headless")
    try:
        driver = webdriver.Chrome(options=chrome_options)
        logger.info("WebDriver successfully launched")
        return driver
    except Exception as e:
        logger.error(f"WebDriver launch error: {e}")
        return None


def apply_javascript_protection(driver: webdriver.Chrome) -> webdriver.Chrome:
    """Applies JavaScript fingerprinting protection scripts."""
    js_protection_script = get_javascript_fingerprinting_protection_script()
    navigator_protection_script = get_navigator_protection_script()
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": js_protection_script + "\n" + navigator_protection_script
        })
        logger.info("JavaScript protection scripts applied successfully")
    except Exception as e:
        logger.error(f"Failed to apply JavaScript protection: {str(e)}")
        raise
    return driver


def get_javascript_info(driver: webdriver.Chrome) -> Dict:
    """Retrieves JavaScript-related information from a test page."""
    test_script = """
    const result = {};
    try {
        // Navigator properties
        result.javaEnabled = navigator.javaEnabled ? navigator.javaEnabled() : false;
        result.webdriver = navigator.webdriver;
        result.languages = navigator.languages ? Array.from(navigator.languages) : [];
        result.pluginsLength = navigator.plugins ? navigator.plugins.length : 0;
        result.mimeTypesLength = navigator.mimeTypes ? navigator.mimeTypes.length : 0;

        // Dangerous functions
        try {
            result.evalWorks = eval('1 + 1') === 2;
        } catch (e) {
            result.evalWorks = false;
        }
        try {
            const fn = new Function('return 42');
            result.functionWorks = fn() === 42;
        } catch (e) {
            result.functionWorks = false;
        }
        result.webAssembly = !!window.WebAssembly;

        // DOM checks
        result.externalScriptPresent = !!document.querySelector('script[src="https://example.com/external.js"]');
        result.iframePresent = !!document.querySelector('iframe[src="https://example.com/iframe"]');
        result.imgSrc = document.querySelector('img') ? document.querySelector('img').src : '';
        result.noscriptPresent = !!document.querySelector('noscript');
        result.jsEnabledVisible = document.querySelector('.js-enabled') ? window.getComputedStyle(document.querySelector('.js-enabled')).display !== 'none' : false;
        result.noJsVisible = document.querySelector('.no-js') ? window.getComputedStyle(document.querySelector('.no-js')).display !== 'none' : false;

        // CSP check
        result.cspPresent = !!document.querySelector('meta[http-equiv="Content-Security-Policy"]');

        return result;
    } catch (error) {
        return { error: error.message };
    }
    """
    try:
        driver.get("data:text/html;charset=utf-8," + TEST_HTML)
        # Give time for MutationObserver and DOM changes
        driver.implicitly_wait(1)
        result = driver.execute_script(test_script)
        return result
    except Exception as e:
        return {"error": f"Failed to retrieve JavaScript info: {str(e)}"}


def test_javascript_protection(headless: bool = False, output_file: Optional[str] = None) -> bool:
    """Test to verify JavaScript fingerprinting protection."""
    # Driver without protection
    driver1 = setup_driver(headless)
    if not driver1:
        return False

    try:
        original_js = get_javascript_info(driver1)
        if "error" in original_js:
            logger.error(original_js["error"])
            return False
        logger.info("JavaScript information before protection:")
        logger.info(json.dumps(original_js, indent=4))
    finally:
        driver1.quit()

    # Driver with protection
    driver2 = setup_driver(headless)
    if not driver2:
        return False

    try:
        driver2 = apply_javascript_protection(driver2)
        protected_js = get_javascript_info(driver2)
        if "error" in protected_js:
            logger.error(protected_js["error"])
            return False
        logger.info("JavaScript information after protection:")
        logger.info(json.dumps(protected_js, indent=4))

        # Verify changes
        changes_detected = False

        if original_js.get("evalWorks") != protected_js.get("evalWorks"):
            logger.info(f"Detected change in eval: {original_js['evalWorks']} -> {protected_js['evalWorks']}")
            changes_detected = True
        if original_js.get("functionWorks") != protected_js.get("functionWorks"):
            logger.info(f"Detected change in Function: {original_js['functionWorks']} -> {protected_js['functionWorks']}")
            changes_detected = True
        if original_js.get("webAssembly") != protected_js.get("webAssembly"):
            logger.info(f"Detected change in WebAssembly: {original_js['webAssembly']} -> {protected_js['webAssembly']}")
            changes_detected = True
        if original_js.get("pluginsLength") != protected_js.get("pluginsLength"):
            logger.info(f"Detected change in plugins length: {original_js['pluginsLength']} -> {protected_js['pluginsLength']}")
            changes_detected = True
        if original_js.get("mimeTypesLength") != protected_js.get("mimeTypesLength"):
            logger.info(f"Detected change in mimeTypes length: {original_js['mimeTypesLength']} -> {protected_js['mimeTypesLength']}")
            changes_detected = True
        if original_js.get("externalScriptPresent") != protected_js.get("externalScriptPresent"):
            logger.info(f"Detected change in external script presence: {original_js['externalScriptPresent']} -> {protected_js['externalScriptPresent']}")
            changes_detected = True
        if original_js.get("iframePresent") != protected_js.get("iframePresent"):
            logger.info(f"Detected change in iframe presence: {original_js['iframePresent']} -> {protected_js['iframePresent']}")
            changes_detected = True
        if original_js.get("imgSrc") != protected_js.get("imgSrc"):
            logger.info(f"Detected change in img src: {original_js['imgSrc']} -> {protected_js['imgSrc']}")
            changes_detected = True
        if original_js.get("noscriptPresent") != protected_js.get("noscriptPresent"):
            logger.info(f"Detected change in noscript presence: {original_js['noscriptPresent']} -> {protected_js['noscriptPresent']}")
            changes_detected = True
        if original_js.get("jsEnabledVisible") != protected_js.get("jsEnabledVisible"):
            logger.info(f"Detected change in js-enabled visibility: {original_js['jsEnabledVisible']} -> {protected_js['jsEnabledVisible']}")
            changes_detected = True
        if original_js.get("noJsVisible") != protected_js.get("noJsVisible"):
            logger.info(f"Detected change in no-js visibility: {original_js['noJsVisible']} -> {protected_js['noJsVisible']}")
            changes_detected = True
        if not original_js.get("cspPresent") and protected_js.get("cspPresent"):
            logger.info("Detected CSP meta tag addition")
            changes_detected = True

        if not changes_detected:
            logger.warning("JavaScript protection not detected!")
            return False

        if output_file:
            result = {"original": original_js, "protected": protected_js}
            with open(output_file, "w") as f:
                json.dump(result, f, indent=4)
            logger.info(f"Results saved to {output_file}")

        logger.info("Test passed successfully!")
        return True

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return False
    finally:
        driver2.quit()


def main():
    """Handles arguments and runs the test."""
    parser = argparse.ArgumentParser(description="JavaScript fingerprinting protection test in Chrome")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Logging level")
    parser.add_argument("--output", type=str, help="Path to file for saving results in JSON format")
    args = parser.parse_args()

    logger.setLevel(getattr(logging, args.log_level.upper()))
    success = test_javascript_protection(headless=args.headless, output_file=args.output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
