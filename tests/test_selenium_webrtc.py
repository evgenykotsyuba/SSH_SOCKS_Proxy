# tests/test_selenium_webrtc.py

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
    from chrome_webrtc_protection import get_webrtc_protection_script
except ImportError as e:
    logger.error(f"Failed to import chrome_webrtc_protection: {e}")
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


def apply_webrtc_protection(driver: webdriver.Chrome) -> webdriver.Chrome:
    """Applies WebRTC protection script to the WebDriver instance."""
    protection_script = get_webrtc_protection_script()
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": protection_script
        })
        logger.info("WebRTC protection script applied successfully")
    except Exception as e:
        logger.error(f"Failed to apply WebRTC protection: {str(e)}")
        raise
    return driver


def get_webrtc_info(driver: webdriver.Chrome) -> Dict:
    """Retrieves WebRTC configuration and capabilities using JavaScript."""
    test_script = """
    const result = {};
    try {
        const rtc = new RTCPeerConnection({iceServers: [{urls: 'stun:stun.l.google.com:19302'}]});
        result.iceServers = rtc.getConfiguration().iceServers;

        // Check if WebRTC is enabled
        result.webrtcEnabled = !!window.RTCPeerConnection;

        // Attempt to gather ICE candidates
        return new Promise((resolve) => {
            const candidates = [];
            rtc.onicecandidate = (event) => {
                if (event.candidate) {
                    candidates.push(event.candidate.candidate);
                } else {
                    result.iceCandidates = candidates;
                    rtc.close();
                    resolve(result);
                }
            };
            rtc.createDataChannel('test');
            rtc.createOffer().then(offer => rtc.setLocalDescription(offer));
            setTimeout(() => {
                if (!result.iceCandidates) {
                    result.iceCandidates = candidates;
                    rtc.close();
                    resolve(result);
                }
            }, 2000);
        });
    } catch (error) {
        return { error: error.message };
    }
    """
    try:
        driver.get("about:blank")
        result = driver.execute_script(test_script)
        return result
    except Exception as e:
        return {"error": f"Failed to retrieve WebRTC info: {str(e)}"}


def test_webrtc_spoofing(headless: bool = False, output_file: Optional[str] = None) -> bool:
    """Test to verify WebRTC spoofing/protection."""
    driver = setup_driver(headless)
    if not driver:
        return False

    try:
        # Retrieve data before spoofing
        original_webrtc = get_webrtc_info(driver)
        if "error" in original_webrtc:
            logger.error(original_webrtc["error"])
            return False
        logger.info("WebRTC information before spoofing:")
        logger.info(json.dumps(original_webrtc, indent=4))

        # Apply WebRTC protection
        driver = apply_webrtc_protection(driver)

        # Retrieve data after spoofing
        spoofed_webrtc = get_webrtc_info(driver)
        if "error" in spoofed_webrtc:
            logger.error(spoofed_webrtc["error"])
            return False
        logger.info("WebRTC information after spoofing:")
        logger.info(json.dumps(spoofed_webrtc, indent=4))

        # Verify changes
        changes_detected = False

        # Check if ICE candidates are blocked (srflx candidates should be absent)
        original_candidates = original_webrtc.get("iceCandidates", [])
        spoofed_candidates = spoofed_webrtc.get("iceCandidates", [])
        original_has_srflx = any("srflx" in cand for cand in original_candidates) if original_candidates else False
        spoofed_has_srflx = any("srflx" in cand for cand in spoofed_candidates) if spoofed_candidates else False

        if original_has_srflx and not spoofed_has_srflx:
            logger.info("Public IP candidates (srflx) were blocked after spoofing")
            changes_detected = True
        elif original_candidates and not spoofed_candidates:
            logger.info("All ICE candidates were blocked after spoofing")
            changes_detected = True
        elif original_candidates != spoofed_candidates:
            logger.info(f"Detected change in ICE candidates: {original_candidates} -> {spoofed_candidates}")
            changes_detected = True

        if not changes_detected:
            logger.warning("WebRTC spoofing/protection not detected!")
            return False

        # Save results to file (if specified)
        if output_file:
            result = {"original": original_webrtc, "spoofed": spoofed_webrtc}
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
    parser = argparse.ArgumentParser(description="WebRTC spoofing/protection test in Chrome")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Logging level")
    parser.add_argument("--output", type=str, help="Path to file for saving results in JSON format")
    args = parser.parse_args()

    # Set logging level
    logger.setLevel(getattr(logging, args.log_level.upper()))

    # Run test
    success = test_webrtc_spoofing(headless=args.headless, output_file=args.output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

# Example usage:
# 1. Basic run: python tests/test_selenium_webrtc.py
# 2. Run in headless mode with DEBUG logging: python tests/test_selenium_webrtc.py --headless --log-level DEBUG
# 3. Run with results saved: python tests/test_selenium_webrtc.py --headless --output font_results.json
# 4. Full run with details: python tests/test_selenium_webrtc.py --headless --log-level DEBUG --output font_test_results.json
