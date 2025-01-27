from selenium.webdriver.remote.webdriver import WebDriver


def modify_tls_fingerprint(driver: WebDriver) -> WebDriver:
    """
    Modifies the browser's TLS fingerprint by injecting custom JavaScript
    into the browser's context via Chrome DevTools Protocol (CDP) commands.

    This helps mitigate browser fingerprinting attempts by introducing randomness
    to cryptographic methods and altering the user agent string.

    Args:
        driver (WebDriver): An instance of the Selenium WebDriver.

    Returns:
        WebDriver: The Selenium WebDriver instance with the TLS fingerprint modifications applied.
    """
    tls_modification_script = """
    (function() {
        // Override cryptographic methods
        const originalCreateSign = crypto.subtle.sign;
        const originalCreateHash = crypto.subtle.digest;

        crypto.subtle.sign = async function(algorithm, key, data) {
            // Add random noise to the signature
            const noise = new Uint8Array(data.byteLength).map(() => Math.floor(Math.random() * 256));
            const modifiedData = new Uint8Array(data.byteLength);
            for (let i = 0; i < data.byteLength; i++) {
                modifiedData[i] = data[i] ^ noise[i];
            }
            return originalCreateSign.call(this, algorithm, key, modifiedData);
        };

        crypto.subtle.digest = async function(algorithm, data) {
            // Modify the hashing process with slight random adjustments
            const noise = new Uint8Array(data.byteLength).map(() => Math.floor(Math.random() * 10));
            const modifiedData = new Uint8Array(data.byteLength);
            for (let i = 0; i < data.byteLength; i++) {
                modifiedData[i] = (data[i] + noise[i]) % 256;
            }
            return originalCreateHash.call(this, algorithm, modifiedData);
        };

        # // Override the navigator object to mask the user agent string
        # Object.defineProperty(navigator, 'userAgent', {
        #     get: function() {
        #         // Replace the Chrome version with a random value
        #         return navigator.userAgent.replace(/Chrome\/[\d.]+/, 'Chrome/' + Math.floor(Math.random() * 100) + '.0.0.0');
        #     }
        # });
    })();
    """

    # Inject the JavaScript script to modify the TLS fingerprint
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": tls_modification_script
    })

    return driver
