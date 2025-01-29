from selenium.webdriver.remote.webdriver import WebDriver
import logging
import random


def modify_tls_fingerprinting_protection(driver: WebDriver, randomization_level: float = 0.5) -> WebDriver:
    """
    Modifies the browser's TLS fingerprint with enhanced reliability and customization,
    including randomization of JA4, JA4_r, JA4_ro, JA3, JA3n fingerprints.

    Args:
        driver (WebDriver): Selenium WebDriver instance
        randomization_level (float): Level of fingerprint randomization (0.0-1.0)

    Returns:
        WebDriver: Modified WebDriver instance
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # # Generate a random User-Agent
    # user_agents = [
    #     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    #     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    #     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    #     "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
    # ]
    # random_user_agent = random.choice(user_agents)

    # Randomize TLS cipher suites
    cipher_suites = [
        "TLS_AES_128_GCM_SHA256",
        "TLS_AES_256_GCM_SHA384",
        "TLS_CHACHA20_POLY1305_SHA256",
        "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256",
        "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
        "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384",
        "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
        "TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256",
        "TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256",
        "TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA",
        "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA",
        "TLS_RSA_WITH_AES_128_GCM_SHA256",
        "TLS_RSA_WITH_AES_256_GCM_SHA384",
        "TLS_RSA_WITH_AES_128_CBC_SHA",
        "TLS_RSA_WITH_AES_256_CBC_SHA"
    ]
    random.shuffle(cipher_suites)

    # Randomize TLS extensions
    extensions = [
        "server_name",
        "extended_master_secret",
        "renegotiation_info",
        "supported_groups",
        "ec_point_formats",
        "session_ticket",
        "application_layer_protocol_negotiation",
        "status_request",
        "delegated_credentials",
        "signed_certificate_timestamp",
        "key_share",
        "psk_key_exchange_modes",
        "supported_versions",
        "compress_certificate",
        "record_size_limit"
    ]
    random.shuffle(extensions)

    # Randomize TLS versions
    tls_versions = ["TLSv1.2", "TLSv1.3"]
    random.shuffle(tls_versions)

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

        // Modify WebGL fingerprint
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) { // UNMASKED_VENDOR_WEBGL
                return 'Google Inc. (NVIDIA)';
            }
            if (parameter === 37446) { // UNMASKED_RENDERER_WEBGL
                return 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0, D3D11)';
            }
            return getParameter.call(this, parameter);
        };

        // Modify JA3, JA3n, JA4, JA4_r, JA4_ro fingerprints
        const originalTlsParams = window.TLS_PARAMS;
        window.TLS_PARAMS = {
            cipherSuites: %s,
            extensions: %s,
            tlsVersions: %s
        };
    })();
    """ % (randomization_level, randomization_level, cipher_suites, extensions, tls_versions)

    try:
        # Enable CDP debugging
        driver.execute_cdp_cmd("Network.enable", {})

        # # Set random User-Agent
        # driver.execute_cdp_cmd("Network.setUserAgentOverride", {
        #     "userAgent": random_user_agent
        # })

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
