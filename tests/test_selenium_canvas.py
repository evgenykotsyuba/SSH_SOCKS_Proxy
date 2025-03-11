# tests/test_selenium_canvas.py

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
    from chrome_canvas_fingerprinting_protection import get_canvas_fingerprinting_protection_script
except ImportError as e:
    logger.error(f"Failed to import chrome_canvas_fingerprinting_protection: {e}")
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


def modify_canvas_context(driver: webdriver.Chrome) -> webdriver.Chrome:
    """Injects canvas fingerprinting protection script into the browser."""
    protection_script = get_canvas_fingerprinting_protection_script()
    try:
        driver.execute_script(protection_script)
        logger.info("Canvas fingerprinting protection script injected successfully")
    except Exception as e:
        logger.error(f"Failed to inject canvas protection script: {e}")
    return driver


def get_canvas_info(driver: webdriver.Chrome) -> Dict:
    """Retrieves Canvas information using JavaScript."""
    test_script = """
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    if (!ctx) {
        return { error: 'Canvas 2D context not supported' };
    }

    // Draw a simple test pattern
    ctx.fillStyle = 'rgb(255, 0, 0)';
    ctx.fillRect(0, 0, 50, 50);
    ctx.fillStyle = 'rgb(0, 255, 0)';
    ctx.fillRect(50, 50, 50, 50);

    // Get image data
    const imageData = ctx.getImageData(0, 0, 100, 100).data;
    const dataUrl = canvas.toDataURL();

    return {
        dataUrlSnippet: dataUrl.substring(0, 50),  // First 50 chars for logging
        imageDataSample: Array.from(imageData.slice(0, 12)),  // Sample of first 12 bytes
        canvasSupported: !!canvas.getContext('2d'),
        width: canvas.width,
        height: canvas.height
    };
    """
    return driver.execute_script(test_script)


def test_canvas_spoofing(headless: bool = False, output_file: Optional[str] = None) -> bool:
    """Test to verify Canvas spoofing."""
    driver = setup_driver(headless)
    if not driver:
        return False

    try:
        # Retrieve data before spoofing
        driver.get("about:blank")
        original_canvas = get_canvas_info(driver)
        if "error" in original_canvas:
            logger.error(original_canvas["error"])
            return False
        logger.info("Canvas information before spoofing:")
        logger.info(json.dumps(original_canvas, indent=4))

        # Apply spoofing
        driver = modify_canvas_context(driver)

        # Retrieve data after spoofing
        driver.get("about:blank")
        spoofed_canvas = get_canvas_info(driver)
        if "error" in spoofed_canvas:
            logger.error(spoofed_canvas["error"])
            return False
        logger.info("Canvas information after spoofing:")
        logger.info(json.dumps(spoofed_canvas, indent=4))

        # Verify changes
        changes_detected = False
        for key in ["dataUrlSnippet", "imageDataSample"]:
            if original_canvas[key] != spoofed_canvas[key]:
                logger.info(f"Detected change in {key}: {original_canvas[key]} -> {spoofed_canvas[key]}")
                changes_detected = True

        if not changes_detected:
            logger.warning("Canvas spoofing not detected!")
            return False

        # Save results to file (if specified)
        if output_file:
            result = {"original": original_canvas, "spoofed": spoofed_canvas}
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
    parser = argparse.ArgumentParser(description="Canvas spoofing test in Chrome")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Logging level")
    parser.add_argument("--output", type=str, help="Path to file for saving results in JSON format")
    args = parser.parse_args()

    # Set logging level
    logger.setLevel(getattr(logging, args.log_level.upper()))

    # Run test
    success = test_canvas_spoofing(headless=args.headless, output_file=args.output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

# Example usage:
# 1. Basic run: python tests/test_selenium_canvas.py
# 2. Run in headless mode with DEBUG logging: python tests/test_selenium_canvas.py --headless --log-level DEBUG
# 3. Run with results saved: python tests/test_selenium_canvas.py --headless --output canvas_results.json
# 4. Full run with details: python tests/test_selenium_canvas.py --headless --log-level DEBUG --output canvas_test_results.json
