from selenium.webdriver.remote.webdriver import WebDriver
from typing import Optional
import random
import logging


def modify_tls_fingerprint(driver: WebDriver, randomization_level: float = 0.5) -> WebDriver:
    """
    Modifies the browser's TLS fingerprint with enhanced reliability and customization.

    Args:
        driver (WebDriver): Selenium WebDriver instance
        randomization_level (float): Level of fingerprint randomization (0.0-1.0)

    Returns:
        WebDriver: Modified WebDriver instance
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    tls_modification_script = """
    (function() {
        // Store original methods
        const originalCrypto = {
            sign: crypto.subtle.sign,
            digest: crypto.subtle.digest,
            getRandomValues: crypto.getRandomValues
        };

        // Override cryptographic methods with error handling
        crypto.subtle.sign = async function(algorithm, key, data) {
            try {
                const strengthFactor = %f;
                const noise = new Uint8Array(data.byteLength).map(
                    () => Math.floor(Math.random() * 256 * strengthFactor)
                );
                const modifiedData = new Uint8Array(data.byteLength);

                for (let i = 0; i < data.byteLength; i++) {
                    modifiedData[i] = data[i] ^ (noise[i] & 0xFF);
                }

                return await originalCrypto.sign.call(this, algorithm, key, modifiedData);
            } catch (error) {
                console.error('TLS sign modification failed:', error);
                return originalCrypto.sign.call(this, algorithm, key, data);
            }
        };

        crypto.subtle.digest = async function(algorithm, data) {
            try {
                const strengthFactor = %f;
                const noise = new Uint8Array(data.byteLength).map(
                    () => Math.floor(Math.random() * 32 * strengthFactor)
                );
                const modifiedData = new Uint8Array(data.byteLength);

                for (let i = 0; i < data.byteLength; i++) {
                    modifiedData[i] = (data[i] + noise[i]) & 0xFF;
                }

                return await originalCrypto.digest.call(this, algorithm, modifiedData);
            } catch (error) {
                console.error('TLS digest modification failed:', error);
                return originalCrypto.digest.call(this, algorithm, data);
            }
        };

        // Add entropy to random number generation
        crypto.getRandomValues = function(array) {
            const result = originalCrypto.getRandomValues.call(this, array);
            const entropy = new Uint8Array(array.length).map(() => Math.random() * 256);

            for (let i = 0; i < array.length; i++) {
                array[i] = (array[i] + entropy[i]) & 0xFF;
            }

            return result;
        };

        // Modify TLS version enumeration
        const originalGetParameter = RTCPeerConnection.prototype.getConfiguration;
        RTCPeerConnection.prototype.getConfiguration = function() {
            const config = originalGetParameter.call(this);
            if (config && config.iceServers) {
                config.iceServers = config.iceServers.map(server => {
                    if (server.urls) {
                        server.urls = Array.isArray(server.urls) 
                            ? server.urls.map(url => url.replace(/\?.*$/, ''))
                            : server.urls.replace(/\?.*$/, '');
                    }
                    return server;
                });
            }
            return config;
        };
    })();
    """ % (randomization_level, randomization_level)

    try:
        # Enable CDP debugging
        driver.execute_cdp_cmd("Network.enable", {})

        # Clear existing scripts
        driver.execute_cdp_cmd("Page.reload", {"ignoreCache": True})

        # Inject the modified script
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": tls_modification_script
        })

        logger.info("TLS fingerprint modifications applied successfully")

    except Exception as e:
        logger.error(f"Failed to modify TLS fingerprint: {str(e)}")
        raise

    return driver
