# tests/test_selenium_fonts.py

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
    from chrome_font_fingerprinting_protection import get_font_fingerprinting_protection_script
except ImportError as e:
    logger.error(f"Failed to import chrome_font_fingerprinting_protection: {e}")
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


def modify_font_context(driver: webdriver.Chrome) -> webdriver.Chrome:
    """Injects font fingerprinting protection script into the browser."""
    protection_script = get_font_fingerprinting_protection_script()
    try:
        driver.execute_script(protection_script)
        logger.info("Font fingerprinting protection script injected successfully")
    except Exception as e:
        logger.error(f"Failed to inject font protection script: {e}")
    return driver


def get_font_info(driver: webdriver.Chrome) -> Dict:
    """Retrieves font-related information using JavaScript."""
    test_script = """
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.font = '14px Arial';

    // Measure text
    const textMetrics = ctx.measureText('Hello World!');

    // Check font availability
    const fontCheck = document.fonts ? document.fonts.check('12px Arial') : 'N/A';

    // Get computed style
    document.body.style.fontFamily = 'Arial, Helvetica, sans-serif';
    const computedStyle = window.getComputedStyle(document.body).fontFamily;

    // Attempt to load a font
    let fontLoadStatus = 'N/A';
    if (document.fonts && document.fonts.load) {
        document.fonts.load('12px Comic Sans MS').then(
            () => fontLoadStatus = 'loaded',
            () => fontLoadStatus = 'failed'
        );
    }

    return {
        textWidth: textMetrics.width,
        fontBoundingBoxAscent: textMetrics.fontBoundingBoxAscent || 'N/A',
        fontCheckResult: fontCheck,
        computedFontFamily: computedStyle,
        fontLoadStatus: fontLoadStatus
    };
    """
    return driver.execute_script(test_script)


def test_font_spoofing(headless: bool = False, output_file: Optional[str] = None) -> bool:
    """Test to verify font fingerprinting protection."""
    driver = setup_driver(headless)
    if not driver:
        return False

    try:
        # Retrieve data before spoofing
        driver.get("about:blank")
        original_font = get_font_info(driver)
        logger.info("Font information before spoofing:")
        logger.info(json.dumps(original_font, indent=4))

        # Apply spoofing
        driver = modify_font_context(driver)

        # Retrieve data after spoofing
        driver.get("about:blank")
        spoofed_font = get_font_info(driver)
        logger.info("Font information after spoofing:")
        logger.info(json.dumps(spoofed_font, indent=4))

        # Verify changes
        changes_detected = False
        expected_changes = {
            "computedFontFamily": "sans-serif",
            "fontCheckResult": False,
            "fontLoadStatus": "failed"
        }

        for key, expected in expected_changes.items():
            if spoofed_font[key] == expected and original_font[key] != spoofed_font[key]:
                logger.info(f"Detected expected change in {key}: {original_font[key]} -> {spoofed_font[key]}")
                changes_detected = True

        # Check textWidth for randomization (should differ slightly due to noise)
        if abs(original_font["textWidth"] - spoofed_font["textWidth"]) > 0:
            logger.info(f"Detected change in textWidth: {original_font['textWidth']} -> {spoofed_font['textWidth']}")
            changes_detected = True

        if not changes_detected:
            logger.warning("Font spoofing not detected!")
            return False

        # Save results to file (if specified)
        if output_file:
            result = {"original": original_font, "spoofed": spoofed_font}
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
    parser = argparse.ArgumentParser(description="Font fingerprinting protection test in Chrome")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Logging level")
    parser.add_argument("--output", type=str, help="Path to file for saving results in JSON format")
    args = parser.parse_args()

    # Set logging level
    logger.setLevel(getattr(logging, args.log_level.upper()))

    # Run test
    success = test_font_spoofing(headless=args.headless, output_file=args.output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

# Example usage:
# 1. Basic run: python tests/test_selenium_fonts.py
# 2. Run in headless mode with DEBUG logging: python tests/test_selenium_fonts.py --headless --log-level DEBUG
# 3. Run with results saved: python tests/test_selenium_fonts.py --headless --output font_results.json
# 4. Full run with details: python tests/test_selenium_fonts.py --headless --log-level DEBUG --output font_test_results.json
