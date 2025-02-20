OVERRIDE = {
    "MacOS_Safari": """
        // Override navigator properties
        Object.defineProperty(navigator, 'platform', { get: () => 'MacIntel' });
        Object.defineProperty(navigator, 'userAgent', {
            get: () => 'Mozilla/5.0 (Macintosh; Intel Mac OS X 15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
        });
        Object.defineProperty(navigator, 'vendor', { get: () => 'Apple Computer, Inc.' });
        Object.defineProperty(navigator, 'deviceMemory', { get: () => 16 }); // Device memory protection
        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 }); // Typical number of CPU cores
        Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 0 }); // No touch points for Mac

        // Override screen properties
        Object.defineProperty(window, 'screen', {
            get: () => ({
                width: 1440,
                height: 900,
                availWidth: 1440,
                availHeight: 900,
                colorDepth: 24,
                pixelDepth: 24,
            }),
        });

        // Override devicePixelRatio
        Object.defineProperty(window, 'devicePixelRatio', { get: () => 2 }); // Typical for Retina displays

        console.log('macOS fingerprint protection applied.');
    """,
    "Windows10_Chrome": """
        // Override navigator properties
        Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
        Object.defineProperty(navigator, 'userAgent', {
            get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        });
        Object.defineProperty(navigator, 'vendor', { get: () => 'Google Inc.' });
        Object.defineProperty(navigator, 'deviceMemory', { get: () => 32 }); // Device memory protection
        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 12 }); // Typical number of CPU cores
        Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 0 }); // No touch points for Windows 10

        // Override screen properties
        Object.defineProperty(window, 'screen', {
            get: () => ({
                width: 1920,
                height: 1080,
                availWidth: 1920,
                availHeight: 1040,
                colorDepth: 24,
                pixelDepth: 24,
            }),
        });

        // Override devicePixelRatio
        Object.defineProperty(window, 'devicePixelRatio', { get: () => 1 }); // Standard for most displays

        console.log('Windows 10 fingerprint protection applied.');
    """,
    "Linux_Ubuntu_Firefox": """
        // Override navigator properties
        Object.defineProperty(navigator, 'platform', { get: () => 'Linux x86_64' });
        Object.defineProperty(navigator, 'userAgent', {
            get: () => 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0',
        });
        Object.defineProperty(navigator, 'vendor', { get: () => '' }); // Firefox typically has no vendor
        Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 }); // Device memory protection
        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 4 }); // Typical number of CPU cores
        Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 0 }); // No touch points for Linux

        // Override screen properties
        Object.defineProperty(window, 'screen', {
            get: () => ({
                width: 1920,
                height: 1080,
                availWidth: 1920,
                availHeight: 1080,
                colorDepth: 24,
                pixelDepth: 24,
            }),
        });

        // Override devicePixelRatio
        Object.defineProperty(window, 'devicePixelRatio', { get: () => 1 }); // Standard for most displays

        console.log('Linux Ubuntu fingerprint protection applied.');
    """,
    "Android_Pixel_Chrome": """
        // Override navigator properties
        Object.defineProperty(navigator, 'platform', { get: () => 'Linux armv8l' });
        Object.defineProperty(navigator, 'userAgent', {
            get: () => 'Mozilla/5.0 (Linux; Android 15; Pixel) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36',
        });
        Object.defineProperty(navigator, 'appVersion', {
            get: () => '5.0 (Linux; Android 15; Pixel) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36',
        });
        Object.defineProperty(navigator, 'vendor', { get: () => 'Google Inc.' });
        Object.defineProperty(navigator, 'deviceMemory', { get: () => 4 }); // Device memory protection
        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 }); // Typical number of CPU cores
        Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 10 }); // Typical for touch devices

        // Override screen properties
        Object.defineProperty(window, 'screen', {
            get: () => ({
                width: 1080,
                height: 2400,
                availWidth: 1080,
                availHeight: 2400,
                colorDepth: 24,
                pixelDepth: 24,
            }),
        });

        // Override devicePixelRatio
        Object.defineProperty(window, 'devicePixelRatio', { get: () => 3 }); // Typical for high-resolution screens

        console.log('Android Pixel fingerprint protection applied.');
    """,
    "iPadOS_Safari": """
        // Override navigator properties
        Object.defineProperty(navigator, 'platform', { get: () => 'iPad' });
        Object.defineProperty(navigator, 'userAgent', {
            get: () => 'Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/605.1.15',
        });
        Object.defineProperty(navigator, 'appVersion', {
            get: () => '5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/605.1.15',
        });
        Object.defineProperty(navigator, 'vendor', { get: () => 'Apple Computer, Inc.' });
        Object.defineProperty(navigator, 'deviceMemory', { get: () => 4 }); // Device memory protection
        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 4 }); // Typical number of CPU cores
        Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 10 }); // Typical for touch devices

        // Override screen properties
        Object.defineProperty(window, 'screen', {
            get: () => ({
                width: 810,
                height: 1080,
                availWidth: 810,
                availHeight: 1080,
                colorDepth: 24,
                pixelDepth: 24,
            }),
        });

        // Override devicePixelRatio
        Object.defineProperty(window, 'devicePixelRatio', { get: () => 2 }); // Typical for Retina displays

        console.log('iPadOS fingerprint protection applied.');
    """,
    "Windows_Server_IE11": """
        // Override navigator properties
        Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
        Object.defineProperty(navigator, 'userAgent', {
            get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
        });
        Object.defineProperty(navigator, 'appVersion', {
            get: () => '5.0 (Windows NT 10.0; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
        });
        Object.defineProperty(navigator, 'vendor', { get: () => 'Microsoft, Inc.' });
        Object.defineProperty(navigator, 'deviceMemory', { get: () => 128 }); // Device memory protection
        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 24 }); // Typical number of CPU cores
        Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 0 }); // No touch points for Windows Server

        // Override screen properties
        Object.defineProperty(window, 'screen', {
            get: () => ({
                width: 1920,
                height: 1080,
                availWidth: 1920,
                availHeight: 1040,
                colorDepth: 24,
                pixelDepth: 24,
            }),
        });

        // Override devicePixelRatio
        Object.defineProperty(window, 'devicePixelRatio', { get: () => 1 }); // Standard for most displays

        console.log('Windows Server fingerprint protection applied.');
    """,
    "Unknown": """
        // Override navigator vendor
        Object.defineProperty(navigator, 'vendor', { get: () => 'Google Inc.' });

        console.log('Unknown fingerprint protection applied.');
    """,
    "iOS_Safari": """
        // Override navigator properties
        Object.defineProperty(navigator, 'platform', { get: () => 'iPhone' });
        Object.defineProperty(navigator, 'userAgent', {
            get: () => 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        });
        Object.defineProperty(navigator, 'appVersion', {
            get: () => '5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        });
        Object.defineProperty(navigator, 'vendor', { get: () => 'Apple Computer, Inc.' });
        Object.defineProperty(navigator, 'deviceMemory', { get: () => 4 }); // Device memory protection
        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 4 }); // Typical number of CPU cores
        Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 10 }); // Typical for touch devices

        // Override screen properties
        Object.defineProperty(window, 'screen', {
            get: () => ({
                width: 375,
                height: 812,
                availWidth: 375,
                availHeight: 812,
                colorDepth: 24,
                pixelDepth: 24,
            }),
        });

        // Override devicePixelRatio
        Object.defineProperty(window, 'devicePixelRatio', { get: () => 3 }); // Typical for Retina displays

        console.log('iOS fingerprint protection applied.');
    """
}
