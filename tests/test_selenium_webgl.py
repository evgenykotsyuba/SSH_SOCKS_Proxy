# 1. Basic run: python tests/test_selenium_webgl.py
# 2. Run in headless mode with DEBUG logging level: python tests/test_selenium_webgl.py --headless --log-level DEBUG
# 3. Run with results saved to a file: python tests/test_selenium_webgl.py --headless --output results.json
# 4. Full run with maximum details: python tests/test_selenium_webgl.py --headless --log-level DEBUG --output webgl_test_results.json

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

try:
    from chrome_webgl_fingerprinting_protection import modify_webgl_vendor_renderer, modify_webgl_textures
except ImportError as e:
    logger.error(f"Failed to import chrome_webgl_fingerprinting_protection: {e}")
    sys.exit(1)


def setup_driver(headless: bool = False) -> Optional[webdriver.Chrome]:
    """Sets up and launches WebDriver with additional options."""
    chrome_options = Options()
    chrome_options.add_argument("--disable-web-security")  # For cross-domain requests
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Hide automation
    chrome_options.add_argument("--no-sandbox")  # For containers
    chrome_options.add_argument("--disable-dev-shm-usage")  # For limited resources
    if headless:
        chrome_options.add_argument("--headless")  # Run in headless mode

    try:
        driver = webdriver.Chrome(options=chrome_options)
        logger.info("WebDriver successfully launched")
        return driver
    except Exception as e:
        logger.error(f"WebDriver launch error: {e}")
        return None


def get_webgl_info(driver: webdriver.Chrome) -> Dict:
    """Retrieves WebGL information using JavaScript."""
    test_script = """
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');

    if (!gl) {
        return { error: 'WebGL not supported' };
    }

    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
    const parameters = {
        VENDOR: gl.getParameter(37445),
        RENDERER: gl.getParameter(37446),
        VERSION: gl.getParameter(37447),
        MAX_TEXTURE_SIZE: gl.getParameter(3379),
        UNMASKED_VENDOR: debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : 'N/A',
        UNMASKED_RENDERER: debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 'N/A',
        SHADING_LANGUAGE_VERSION: gl.getParameter(35724),
        SUPPORTED_EXTENSIONS: gl.getSupportedExtensions()
    };

    return parameters;
    """
    return driver.execute_script(test_script)


def test_webgl_spoofing(headless: bool = False, output_file: Optional[str] = None) -> bool:
    """Test to verify WebGL spoofing."""
    driver = setup_driver(headless)
    if not driver:
        return False

    try:
        # Retrieve data before spoofing
        driver.get("about:blank")
        original_webgl = get_webgl_info(driver)
        if "error" in original_webgl:
            logger.error(original_webgl["error"])
            return False
        logger.info("WebGL information before spoofing:")
        logger.info(json.dumps(original_webgl, indent=4))

        # Apply spoofing
        driver = modify_webgl_vendor_renderer(driver)
        driver = modify_webgl_textures(driver)

        # Retrieve data after spoofing
        driver.get("about:blank")
        spoofed_webgl = get_webgl_info(driver)
        if "error" in spoofed_webgl:
            logger.error(spoofed_webgl["error"])
            return False
        logger.info("WebGL information after spoofing:")
        logger.info(json.dumps(spoofed_webgl, indent=4))

        # Verify changes
        changes_detected = False
        for key in ["VENDOR", "RENDERER", "UNMASKED_VENDOR", "UNMASKED_RENDERER"]:
            if original_webgl[key] != spoofed_webgl[key]:
                logger.info(f"Detected change in {key}: {original_webgl[key]} -> {spoofed_webgl[key]}")
                changes_detected = True

        if not changes_detected:
            logger.warning("WebGL spoofing not detected!")
            return False

        # Save results to file (if specified)
        if output_file:
            result = {"original": original_webgl, "spoofed": spoofed_webgl}
            with open(output_file, "w") as f:
                json.dump(result, f, indent=4)
            logger.info(f"Results saved to {output_file}")

        logger.info("Test passed successfully!")
        return True

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return False
    finally:
        driver.quit()


def main():
    """Handles arguments and runs the test."""
    parser = argparse.ArgumentParser(description="WebGL spoofing test in Chrome")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Logging level")
    parser.add_argument("--output", type=str, help="Path to file for saving results in JSON format")
    args = parser.parse_args()

    # Set logging level
    logger.setLevel(getattr(logging, args.log_level.upper()))

    # Run test
    success = test_webgl_spoofing(headless=args.headless, output_file=args.output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
