OVERRIDE = {
    "MacOS_Safari": """
        // Override navigator.platform
        Object.defineProperty(navigator, 'platform', {
            get: () => 'MacIntel',
        });

        // Override navigator.userAgent
        Object.defineProperty(navigator, 'userAgent', {
            get: () => 'Mozilla/5.0 (Macintosh; Intel Mac OS X 15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        });
        
        // Add Do Not Track setting
        Object.defineProperty(navigator, 'doNotTrack', {
            get: () => '1',  // '1' means enabled, 'null' means not set, '0' means disabled
        });

        // Override navigator.oscpu
        Object.defineProperty(navigator, 'oscpu', {
            get: () => 'Intel Mac OS X 15.0',
        });

        // Override navigator.appVersion
        Object.defineProperty(navigator, 'appVersion', {
            get: () => '5.0 (Macintosh; Intel Mac OS X 15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        });
        
        // Переопределяем функцию fetch для добавления заголовка Content-Language
        const originalFetch = window.fetch;
        window.fetch = function (input, init = {}) {
            init.headers = {
                ...init.headers,
                'Content-Language': 'en-EN',
            };
            return originalFetch(input, init);
        };

        // Override navigator.vendor
        Object.defineProperty(navigator, 'vendor', {
            get: () => 'Apple Computer, Inc.',
        });

        // Set navigator.webdriver to false (to prevent automation detection)
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });

        // Override navigator.maxTouchPoints
        Object.defineProperty(navigator, 'maxTouchPoints', {
            get: () => 0,
        });

        // Override navigator.hardwareConcurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 4, // Set the actual number of threads for your Mac
        });

        // Override navigator.language and navigator.languages
        Object.defineProperty(navigator, 'language', {
            get: () => 'en-US',
        });

        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });

        // Add Content Language
        Object.defineProperty(navigator, 'contentLanguage', {
            get: () => 'en-EN',
        });
        
        // Override navigator.deviceMemory
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 16,
        });

        // Override date and time methods
        const targetTimezone = 'Europe/Germany'; // UTC
        
        // Intercept Date.prototype.getTimezoneOffset
        const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
        Date.prototype.getTimezoneOffset = function() {
           return -60; // UTC in minutes (-60 minutes = +1 hours)
        };
        
        // Override Intl.DateTimeFormat
        const originalDateTimeFormat = Intl.DateTimeFormat;
        window.Intl.DateTimeFormat = function(locales, options) {
           if(options === undefined) {
               options = {};
           }
           options.timeZone = targetTimezone;
           return new originalDateTimeFormat(locales, options);
        };
        
        // Override resolvedOptions
        Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {
           value: function() {
               return {
                   locale: "en-US",
                   calendar: "gregory",
                   numberingSystem: "latn",
                   timeZone: targetTimezone,
                   year: "numeric",
                   month: "numeric",
                   day: "numeric",
                   hour: "numeric",
                   minute: "numeric",
                   second: "numeric"
               };
           }
        });
        
        // Override toString for Date
        const originalToString = Date.prototype.toString;
        Date.prototype.toString = function() {
           return new Date(this.getTime() - (this.getTimezoneOffset() + 60) * 60000).toUTCString().replace('GMT', 'GMT+0100');
        };
        
        // Override toLocaleString
        const originalToLocaleString = Date.prototype.toLocaleString;
        Date.prototype.toLocaleString = function() {
           return new Date(this.getTime() - (this.getTimezoneOffset() + 50) * 60000)
               .toLocaleString('en-US', {timeZone: targetTimezone});
        };

        // Proxy for window.screen
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

        // Proxy for window.outerWidth and window.outerHeight
        Object.defineProperty(window, 'outerWidth', {
            get: () => 1440,
        });

        Object.defineProperty(window, 'outerHeight', {
            get: () => 900,
        });

        // Proxy for window.devicePixelRatio
        Object.defineProperty(window, 'devicePixelRatio', {
            get: () => 2, // Common value for macOS Retina screens
        });

        // Override clipboard API (to prevent data leaks via clipboard)
        Object.defineProperty(navigator, 'clipboard', {
            get: () => ({
                writeText: () => Promise.resolve(),
                readText: () => Promise.resolve(''),
            }),
        });

        // Block WebGL Fingerprinting
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function (param) {
            // Modify key parameters to mimic macOS
            const spoofedParams = {
                37446: 'Intel Inc.', // UNMASKED_VENDOR_WEBGL
                37445: 'Intel Iris OpenGL Engine', // UNMASKED_RENDERER_WEBGL
            };
            return spoofedParams[param] || getParameter.call(this, param);
        };

        // Block AudioContext Fingerprinting
        const originalAudioContext = AudioContext.prototype.getChannelData;
        AudioContext.prototype.getChannelData = function (param) {
            // Generate fake data
            return new Float32Array(param).fill(0);
        };

        // Block Canvas Fingerprinting
        const toDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function (...args) {
            // Return a fake image
            return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA';
        };

        // Override some other methods for consistency
        window.navigator.__defineGetter__('platform', () => 'MacIntel');
        window.navigator.__defineGetter__('userAgent', () =>
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        );

        console.log('Spoofing as macOS successfully applied.');
    """,
    "Windows10_Chrome": """
        // Override navigator.platform
        Object.defineProperty(navigator, 'platform', {
            get: () => 'Win32',
        });
    
        // Override navigator.userAgent
        Object.defineProperty(navigator, 'userAgent', {
            get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        });
    
        // Override navigator.oscpu
        Object.defineProperty(navigator, 'oscpu', {
            get: () => 'Windows NT 10.0; Win64; x64',
        });
    
        // Add Do Not Track setting
        Object.defineProperty(navigator, 'doNotTrack', {
            get: () => '1',  // '1' means enabled, 'null' means not set, '0' means disabled
        });
    
        // Override navigator.appVersion
        Object.defineProperty(navigator, 'appVersion', {
            get: () => '5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        });
    
        // Override navigator.vendor
        Object.defineProperty(navigator, 'vendor', {
            get: () => 'Google Inc.',
        });
    
        // Override navigator.language and navigator.languages
        Object.defineProperty(navigator, 'language', {
            get: () => 'en-EN',
        });
    
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-EN', 'en'],
        });
    
        // Set navigator.webdriver to false (to prevent automation detection)
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
    
        // Override navigator.maxTouchPoints
        Object.defineProperty(navigator, 'maxTouchPoints', {
            get: () => 0,
        });
    
        // Override navigator.hardwareConcurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8, // Set the actual number of threads for your Windows machine
        });
    
        // Override navigator.deviceMemory
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 16, // Set the device memory in GB
        });
    
        // Override date and time methods
        const targetTimezone = 'Europe/Paris'; // UTC+1
    
        // Intercept Date.prototype.getTimezoneOffset
        Date.prototype.getTimezoneOffset = function() {
            return -60; // UTC+1 in minutes
        };
    
        // Override Intl.DateTimeFormat
        const originalDateTimeFormat = Intl.DateTimeFormat;
        window.Intl.DateTimeFormat = function(locales, options) {
            if(options === undefined) {
                options = {};
            }
            options.timeZone = targetTimezone;
            return new originalDateTimeFormat(locales, options);
        };
    
        // Override resolvedOptions
        Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {
            value: function() {
                return {
                    locale: "en-EN",
                    calendar: "gregory",
                    numberingSystem: "latn",
                    timeZone: targetTimezone,
                    year: "numeric",
                    month: "numeric",
                    day: "numeric",
                    hour: "numeric",
                    minute: "numeric",
                    second: "numeric"
                };
            }
        });
    
        // Proxy for window.screen
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
    
        // Proxy for window.outerWidth and window.outerHeight
        Object.defineProperty(window, 'outerWidth', {
            get: () => 1920,
        });
    
        Object.defineProperty(window, 'outerHeight', {
            get: () => 1040,
        });
    
        // Proxy for window.devicePixelRatio
        Object.defineProperty(window, 'devicePixelRatio', {
            get: () => 1, // Typical value for non-Retina screens
        });
    
        console.log('Spoofing as Windows 10 successfully applied with UTC+1 and language en-EN.');
    """,
    "Linux_Ubuntu_Firefox": """
        // Override navigator.platform
        Object.defineProperty(navigator, 'platform', {
            get: () => 'Linux x86_64',
        });
    
        // Override navigator.userAgent
        Object.defineProperty(navigator, 'userAgent', {
            get: () => 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0',
        });
    
        // Override navigator.oscpu
        Object.defineProperty(navigator, 'oscpu', {
            get: () => 'Linux x86_64',
        });
    
        // Override navigator.appVersion
        Object.defineProperty(navigator, 'appVersion', {
            get: () => '5.0 (X11; Ubuntu; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0',
        });
    
        // Override navigator.vendor
        Object.defineProperty(navigator, 'vendor', {
            get: () => '',
        });
    
        // Set navigator.webdriver to false (to prevent automation detection)
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
    
        // Override navigator.maxTouchPoints
        Object.defineProperty(navigator, 'maxTouchPoints', {
            get: () => 0,
        });
    
        // Override navigator.hardwareConcurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 4, // Set the actual number of threads for your Linux machine
        });
    
        // Override navigator.language and navigator.languages
        Object.defineProperty(navigator, 'language', {
            get: () => 'en-US',
        });
    
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
    
        // Proxy for window.screen
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
    
        // Proxy for window.outerWidth and window.outerHeight
        Object.defineProperty(window, 'outerWidth', {
            get: () => 1920,
        });
    
        Object.defineProperty(window, 'outerHeight', {
            get: () => 1040,
        });
    
        // Proxy for window.devicePixelRatio
        Object.defineProperty(window, 'devicePixelRatio', {
            get: () => 1, // Typical value for non-Retina screens
        });
    
        // Override clipboard API (to prevent data leaks via clipboard)
        Object.defineProperty(navigator, 'clipboard', {
            get: () => ({
                writeText: () => Promise.resolve(),
                readText: () => Promise.resolve(''),
            }),
        });
    
        // Block WebGL Fingerprinting
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function (param) {
            // Modify key parameters to mimic Linux
            const spoofedParams = {
                37446: 'Mozilla', // UNMASKED_VENDOR_WEBGL
                37445: 'Mesa Intel(R) UHD Graphics 620 (WHL GT2)', // UNMASKED_RENDERER_WEBGL
            };
            return spoofedParams[param] || getParameter.call(this, param);
        };
    
        // Block AudioContext Fingerprinting
        const originalAudioContext = AudioContext.prototype.getChannelData;
        AudioContext.prototype.getChannelData = function (param) {
            // Generate fake data
            return new Float32Array(param).fill(0);
        };
    
        // Block Canvas Fingerprinting
        const toDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function (...args) {
            // Return a fake image
            return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA';
        };
    
        // Override some other methods for consistency
        window.navigator.__defineGetter__('platform', () => 'Linux x86_64');
        window.navigator.__defineGetter__('userAgent', () =>
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0'
        );
    
        console.log('Spoofing as Linux Ubuntu successfully applied.');
        """,
    "Android_Pixel_Chrome": """
        // Override navigator.platform
        Object.defineProperty(navigator, 'platform', {
            get: () => 'Linux armv8l',
        });
    
        // Override navigator.userAgent
        Object.defineProperty(navigator, 'userAgent', {
            get: () => 'Mozilla/5.0 (Linux; Android 15; Pixel) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.139 Mobile Safari/537.36',
        });
    
        // Override navigator.appVersion
        Object.defineProperty(navigator, 'appVersion', {
            get: () => '5.0 (Linux; Android 15; Pixel) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.139 Mobile Safari/537.36',
        });
    
        // Override navigator.vendor
        Object.defineProperty(navigator, 'vendor', {
            get: () => 'Google Inc.',
        });
    
        // Set navigator.webdriver to false (to prevent automation detection)
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
    
        // Override navigator.maxTouchPoints
        Object.defineProperty(navigator, 'maxTouchPoints', {
            get: () => 10, // Typical for modern smartphones
        });
    
        // Override navigator.hardwareConcurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8, // Typical number of CPU cores for modern Android devices
        });
    
        // Override navigator.language and navigator.languages
        Object.defineProperty(navigator, 'language', {
            get: () => 'en-US',
        });
    
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
    
        // Proxy for window.screen
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
    
        // Proxy for window.outerWidth and window.outerHeight
        Object.defineProperty(window, 'outerWidth', {
            get: () => 1080,
        });
    
        Object.defineProperty(window, 'outerHeight', {
            get: () => 2400,
        });
    
        // Proxy for window.devicePixelRatio
        Object.defineProperty(window, 'devicePixelRatio', {
            get: () => 3, // Typical for Pixel devices with high-resolution screens
        });
    
        // Override clipboard API (to prevent data leaks via clipboard)
        Object.defineProperty(navigator, 'clipboard', {
            get: () => ({
                writeText: () => Promise.resolve(),
                readText: () => Promise.resolve(''),
            }),
        });
    
        // Block WebGL Fingerprinting
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function (param) {
            // Modify key parameters to mimic Android
            const spoofedParams = {
                37446: 'Qualcomm', // UNMASKED_VENDOR_WEBGL
                37445: 'Adreno (TM) 640', // UNMASKED_RENDERER_WEBGL
            };
            return spoofedParams[param] || getParameter.call(this, param);
        };
    
        // Block AudioContext Fingerprinting
        const originalAudioContext = AudioContext.prototype.getChannelData;
        AudioContext.prototype.getChannelData = function (param) {
            // Generate fake data
            return new Float32Array(param).fill(0);
        };
    
        // Block Canvas Fingerprinting
        const toDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function (...args) {
            // Return a fake image
            return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA';
        };
    
        // Override some other methods for consistency
        window.navigator.__defineGetter__('platform', () => 'Linux armv8l');
        window.navigator.__defineGetter__('userAgent', () =>
            'Mozilla/5.0 (Linux; Android 15; Pixel) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.139 Mobile Safari/537.36'
        );
    
        console.log('Spoofing as Android 15 (Pixel) successfully applied.');
        """,
    "iPadOS_Safari": """
        // Override navigator.platform
        Object.defineProperty(navigator, 'platform', {
            get: () => 'iPad',
        });
    
        // Override navigator.userAgent
        Object.defineProperty(navigator, 'userAgent', {
            get: () => 'Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/605.1.15',
        });
    
        // Override navigator.appVersion
        Object.defineProperty(navigator, 'appVersion', {
            get: () => '5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/605.1.15',
        });
    
        // Override navigator.vendor
        Object.defineProperty(navigator, 'vendor', {
            get: () => 'Apple Computer, Inc.',
        });
    
        // Set navigator.webdriver to false (to prevent automation detection)
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
    
        // Override navigator.maxTouchPoints
        Object.defineProperty(navigator, 'maxTouchPoints', {
            get: () => 10, // iPad typically supports multi-touch with 10 points
        });
    
        // Override navigator.hardwareConcurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8, // Typical number of CPU cores for modern iPads
        });
    
        // Override navigator.language and navigator.languages
        Object.defineProperty(navigator, 'language', {
            get: () => 'en-US',
        });
    
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
    
        // Proxy for window.screen
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
    
        // Proxy for window.outerWidth and window.outerHeight
        Object.defineProperty(window, 'outerWidth', {
            get: () => 810,
        });
    
        Object.defineProperty(window, 'outerHeight', {
            get: () => 1080,
        });
    
        // Proxy for window.devicePixelRatio
        Object.defineProperty(window, 'devicePixelRatio', {
            get: () => 2, // Typical for Retina screens on iPads
        });
    
        // Override clipboard API (to prevent data leaks via clipboard)
        Object.defineProperty(navigator, 'clipboard', {
            get: () => ({
                writeText: () => Promise.resolve(),
                readText: () => Promise.resolve(''),
            }),
        });
    
        // Block WebGL Fingerprinting
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function (param) {
            // Modify key parameters to mimic iPadOS
            const spoofedParams = {
                37446: 'Apple', // UNMASKED_VENDOR_WEBGL
                37445: 'Apple GPU', // UNMASKED_RENDERER_WEBGL
            };
            return spoofedParams[param] || getParameter.call(this, param);
        };
    
        // Block AudioContext Fingerprinting
        const originalAudioContext = AudioContext.prototype.getChannelData;
        AudioContext.prototype.getChannelData = function (param) {
            // Generate fake data
            return new Float32Array(param).fill(0);
        };
    
        // Block Canvas Fingerprinting
        const toDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function (...args) {
            // Return a fake image
            return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA';
        };
    
        // Override some other methods for consistency
        window.navigator.__defineGetter__('platform', () => 'iPad');
        window.navigator.__defineGetter__('userAgent', () =>
            'Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/605.1.15'
        );
    
        console.log('Spoofing as iPadOS 16 (Safari 16) successfully applied.');
        """,
    "Windows_Server_IE11": """
        // Override navigator.platform
        Object.defineProperty(navigator, 'platform', {
            get: () => 'Win32',
        });
    
        // Override navigator.userAgent
        Object.defineProperty(navigator, 'userAgent', {
            get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
        });
    
        // Override navigator.appVersion
        Object.defineProperty(navigator, 'appVersion', {
            get: () => '5.0 (Windows NT 10.0; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
        });
    
        // Override navigator.vendor
        Object.defineProperty(navigator, 'vendor', {
            get: () => '',
        });
    
        // Set navigator.webdriver to false (to prevent automation detection)
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
    
        // Override navigator.maxTouchPoints
        Object.defineProperty(navigator, 'maxTouchPoints', {
            get: () => 0, // Typical for non-touch devices running Windows Server
        });
    
        // Override navigator.hardwareConcurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 4, // Common for Windows Server virtual machines
        });
    
        // Override navigator.language and navigator.languages
        Object.defineProperty(navigator, 'language', {
            get: () => 'en-US',
        });
    
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US'],
        });
    
        // Proxy for window.screen
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
    
        // Proxy for window.outerWidth and window.outerHeight
        Object.defineProperty(window, 'outerWidth', {
            get: () => 1920,
        });
    
        Object.defineProperty(window, 'outerHeight', {
            get: () => 1040,
        });
    
        // Proxy for window.devicePixelRatio
        Object.defineProperty(window, 'devicePixelRatio', {
            get: () => 1, // Typical for standard displays without scaling
        });
    
        // Override clipboard API (to prevent data leaks via clipboard)
        Object.defineProperty(navigator, 'clipboard', {
            get: () => ({
                writeText: () => Promise.resolve(),
                readText: () => Promise.resolve(''),
            }),
        });
    
        // Block WebGL Fingerprinting
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function (param) {
            // Modify key parameters to mimic Windows Server
            const spoofedParams = {
                37446: 'Microsoft', // UNMASKED_VENDOR_WEBGL
                37445: 'Microsoft Basic Render Driver', // UNMASKED_RENDERER_WEBGL
            };
            return spoofedParams[param] || getParameter.call(this, param);
        };
    
        // Block AudioContext Fingerprinting
        const originalAudioContext = AudioContext.prototype.getChannelData;
        AudioContext.prototype.getChannelData = function (param) {
            // Generate fake data
            return new Float32Array(param).fill(0);
        };
    
        // Block Canvas Fingerprinting
        const toDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function (...args) {
            // Return a fake image
            return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA';
        };
    
        // Override some other methods for consistency
        window.navigator.__defineGetter__('platform', () => 'Win32');
        window.navigator.__defineGetter__('userAgent', () =>
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; Trident/7.0; rv:11.0) like Gecko'
        );
    
        console.log('Spoofing as Windows Server 2019 (Internet Explorer 11) successfully applied.');
        """,
    "Unknown": """
        // Override navigator.vendor
        Object.defineProperty(navigator, 'vendor', {
            get: () => 'Google Inc.',
        });  
    """,
    "iOS_Safari": """
        // iOS 16 Safari Spoofing
        Object.defineProperty(navigator, 'platform', {
            get: () => 'iPhone',
        });
        
        Object.defineProperty(navigator, 'userAgent', {
            get: () => 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        });
        
        Object.defineProperty(navigator, 'appVersion', {
            get: () => '5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        });
        
        Object.defineProperty(navigator, 'vendor', {
            get: () => 'Apple Computer, Inc.',
        });
        
        Object.defineProperty(navigator, 'doNotTrack', {
            get: () => '1',
        });
        
        Object.defineProperty(navigator, 'language', {
            get: () => 'en-US',
        });
        
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        Object.defineProperty(navigator, 'maxTouchPoints', {
            get: () => 10, // Typical for iOS devices
        });
        
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 4, // Estimated device memory in GB
        });
        
        Object.defineProperty(window, 'devicePixelRatio', {
            get: () => 3, // Typical for iPhone Retina screens
        });
        
        // Proxy for screen properties
        Object.defineProperty(window, 'screen', {
            get: () => ({
                width: 375, // Logical resolution for iPhone
                height: 812,
                availWidth: 375,
                availHeight: 812,
                colorDepth: 24,
                pixelDepth: 24,
            }),
        });
        
        Object.defineProperty(window, 'outerWidth', {
            get: () => 375,
        });
        
        Object.defineProperty(window, 'outerHeight', {
            get: () => 812,
        });
        
        // Override Date and Time methods
        const targetTimezone = 'America/New_York'; // Example timezone
        
        Date.prototype.getTimezoneOffset = function () {
            return -300; // UTC-5 in minutes
        };
        
        const originalDateTimeFormat = Intl.DateTimeFormat;
        window.Intl.DateTimeFormat = function (locales, options) {
            options = options || {};
            options.timeZone = targetTimezone;
            return new originalDateTimeFormat(locales, options);
        };
        
        Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {
            value: function () {
                return {
                    locale: 'en-US',
                    calendar: 'gregory',
                    numberingSystem: 'latn',
                    timeZone: targetTimezone,
                };
            },
        });
        
        // Block WebGL Fingerprinting
        const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function (param) {
            const spoofedParams = {
                37446: 'Apple Inc.', // UNMASKED_VENDOR_WEBGL
                37445: 'Apple GPU', // UNMASKED_RENDERER_WEBGL
            };
            return spoofedParams[param] || originalGetParameter.call(this, param);
        };
        
        // Block AudioContext Fingerprinting
        const originalGetChannelData = AudioContext.prototype.getChannelData;
        AudioContext.prototype.getChannelData = function () {
            return new Float32Array(128).fill(0);
        };
        
        // Block Canvas Fingerprinting
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function () {
            return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA';
        };
        
        console.log('Spoofing as iOS 16 successfully applied.');
    """
}
