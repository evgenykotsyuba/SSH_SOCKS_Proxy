OVERRIDE = {
    "MacOS_Safari": """
        // Override navigator properties
        Object.defineProperty(navigator, 'platform', { get: () => 'MacIntel' });
        Object.defineProperty(navigator, 'userAgent', {
            get: () => 'Mozilla/5.0 (Macintosh; Intel Mac OS X 15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        });
        Object.defineProperty(navigator, 'vendor', { get: () => 'Apple Computer, Inc.' });
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
    
        // Disable plugins and mimeTypes
        Object.defineProperty(navigator, 'plugins', { get: () => new PluginArray() });
        Object.defineProperty(navigator, 'mimeTypes', { get: () => new MimeTypeArray() });
    
        // Override clipboard API
        Object.defineProperty(navigator, 'clipboard', {
            get: () => ({
                writeText: () => Promise.resolve(),
                readText: () => Promise.resolve(''),
            }),
        });
    
        // Randomize Canvas Fingerprinting
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function (...args) {
            return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA';
        };
    
        const originalGetContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type, attributes) {
            const context = originalGetContext.call(this, type, attributes);
            if (context && type === '2d') {
                const originalGetImageData = context.getImageData;
                context.getImageData = function(...args) {
                    const imageData = originalGetImageData.apply(this, args);
                    // Slightly modify pixel data
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] = (imageData.data[i] + 1) % 256;
                    }
                    return imageData;
                };
            }
            return context;
        };
    
        // Randomize WebGL Fingerprinting
        const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(param) {
            const spoofedParams = {
                37446: 'Intel Inc.', // UNMASKED_VENDOR_WEBGL
                37445: 'Intel Iris OpenGL Engine', // UNMASKED_RENDERER_WEBGL
            };
            return spoofedParams[param] || originalGetParameter.call(this, param);
        };
    
        // Block font enumeration
        Object.defineProperty(document, 'fonts', {
            get: () => ({
                forEach: () => {},
                size: 0,
            }),
        });
    
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
    
        // Override timezone to UTC+0
        Date.prototype.getTimezoneOffset = function() { return 0; };
        console.log('macOS fingerprint protection applied.');
    """,
    "Windows10_Chrome": """
        // WebRTC Leak Protection: Override RTC methods
        const originalRTCPeerConnection = window.RTCPeerConnection || window.webkitRTCPeerConnection;
        if (originalRTCPeerConnection) {
            window.RTCPeerConnection = function(...args) {
                const pc = new originalRTCPeerConnection(...args);
    
                // Override addIceCandidate to block public IPs
                const originalAddIceCandidate = pc.addIceCandidate;
                pc.addIceCandidate = function(candidate, ...rest) {
                    if (candidate && candidate.candidate && candidate.candidate.includes('srflx')) {
                        console.warn('Blocking public IP candidate:', candidate.candidate);
                        return Promise.resolve(); // Block public IPs
                    }
                    return originalAddIceCandidate.apply(pc, [candidate, ...rest]);
                };
    
                // Override setLocalDescription to filter ICE candidates
                const originalSetLocalDescription = pc.setLocalDescription;
                pc.setLocalDescription = function(description, ...rest) {
                    if (description && description.sdp) {
                        const filteredSDP = description.sdp.replace(
                            /a=candidate:(.*?)(srflx.*?)\\r\\n/g, ''
                        );
                        description.sdp = filteredSDP;
                    }
                    return originalSetLocalDescription.apply(pc, [description, ...rest]);
                };
    
                return pc;
            };
        }
    
        // Block public IP leaks in RTCDataChannel
        Object.defineProperty(navigator, 'connection', {
            get: () => null
        });
    
        // Additional WebRTC Protection
        Object.defineProperty(navigator, 'mediaDevices', {
            get: () => ({
                enumerateDevices: () => Promise.resolve([]),
                getUserMedia: () => Promise.reject(new Error('Blocked by WebRTC Protection'))
            })
        });
    
        // Override navigator properties
        Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
        Object.defineProperty(navigator, 'userAgent', {
            get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        });
        Object.defineProperty(navigator, 'vendor', { get: () => 'Google Inc.' });
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
        Object.defineProperty(navigator, 'deviceMemory', { get: () => 16 });
        Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 0 });
        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
        Object.defineProperty(navigator, 'language', { get: () => 'en-EN' });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-EN', 'en'] });
    
        // Disable plugins and mimeTypes
        Object.defineProperty(navigator, 'plugins', { get: () => new PluginArray() });
        Object.defineProperty(navigator, 'mimeTypes', { get: () => new MimeTypeArray() });
    
        // Block font enumeration
        Object.defineProperty(document, 'fonts', {
            get: () => ({
                forEach: () => {},
                size: 0,
            }),
        });
    
        // Randomize Canvas Fingerprinting
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function (...args) {
            return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA';
        };
    
        const originalGetContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type, attributes) {
            const context = originalGetContext.call(this, type, attributes);
            if (context && type === '2d') {
                const originalGetImageData = context.getImageData;
                context.getImageData = function(...args) {
                    const imageData = originalGetImageData.apply(this, args);
                    // Slightly modify pixel data
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] = (imageData.data[i] + 1) % 256;
                    }
                    return imageData;
                };
            }
            return context;
        };
    
        // Randomize WebGL Fingerprinting
        const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(param) {
            const spoofedParams = {
                37446: 'Intel Corporation', // UNMASKED_VENDOR_WEBGL
                37445: 'Intel HD Graphics 620', // UNMASKED_RENDERER_WEBGL
            };
            return spoofedParams[param] || originalGetParameter.call(this, param);
        };
    
        // Timezone spoofing
        const targetTimezone = 'Europe/London'; // UTC+0
        Date.prototype.getTimezoneOffset = function() { return 0; };
        const originalDateTimeFormat = Intl.DateTimeFormat;
        window.Intl.DateTimeFormat = function(locales, options) {
            if(options === undefined) {
                options = {};
            }
            options.timeZone = targetTimezone;
            return new originalDateTimeFormat(locales, options);
        };
    
        // Proxy for screen properties
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
    
        Object.defineProperty(window, 'devicePixelRatio', { get: () => 1 });
    
        console.log('Windows 10 fingerprint protection applied.');
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
    
        // Set navigator.webdriver to false to prevent automation detection
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
    
        // Block Canvas Fingerprinting
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function (...args) {
            return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=';
        };
    
        const originalGetContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type, attributes) {
            const context = originalGetContext.call(this, type, attributes);
            if (context && type === '2d') {
                const originalGetImageData = context.getImageData;
                context.getImageData = function(...args) {
                    const imageData = originalGetImageData.apply(this, args);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] = (imageData.data[i] + 1) % 256; // Slightly modify pixel data
                    }
                    return imageData;
                };
            }
            return context;
        };
    
        // Block WebGL Fingerprinting
        const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(param) {
            const spoofedParams = {
                37446: 'Intel Inc.', // UNMASKED_VENDOR_WEBGL
                37445: 'Mesa DRI Intel(R) HD Graphics', // UNMASKED_RENDERER_WEBGL
            };
            return spoofedParams[param] || originalGetParameter.call(this, param);
        };
    
        // Block WebGL debug extensions
        const originalGetExtension = WebGLRenderingContext.prototype.getExtension;
        WebGLRenderingContext.prototype.getExtension = function(name) {
            const blockedExtensions = ['WEBGL_debug_renderer_info', 'WEBGL_debug_shaders'];
            if (blockedExtensions.includes(name)) {
                return null;
            }
            return originalGetExtension.call(this, name);
        };
    
        // Hide fonts
        const originalFonts = document.fonts;
        Object.defineProperty(document, 'fonts', {
            get: () => ({
                forEach: () => {},
                size: 0
            }),
        });
    
        console.log('Fingerprint protection applied.');
        """,
    "Android_Pixel_Chrome": """
        // Override navigator.platform
        Object.defineProperty(navigator, 'platform', {
            get: () => 'Linux armv8l',
        });
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => new PluginArray(),
            configurable: true
        });
        
        Object.defineProperty(navigator, 'mimeTypes', {
            get: () => new MimeTypeArray(),
            configurable: true
        });
        
        // Override plugins length
        Object.defineProperty(navigator.plugins, 'length', {
            get: () => 0,
            configurable: true
        });
        
        // Override plugin refresh method
        navigator.plugins.refresh = () => {};

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
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => new PluginArray(),
            configurable: true
        });
        
        Object.defineProperty(navigator, 'mimeTypes', {
            get: () => new MimeTypeArray(),
            configurable: true
        });
        
        // Override plugins length
        Object.defineProperty(navigator.plugins, 'length', {
            get: () => 0,
            configurable: true
        });
        
        // Override plugin refresh method
        navigator.plugins.refresh = () => {};

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
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => new PluginArray(),
            configurable: true
        });
        
        Object.defineProperty(navigator, 'mimeTypes', {
            get: () => new MimeTypeArray(),
            configurable: true
        });
        
        // Override plugins length
        Object.defineProperty(navigator.plugins, 'length', {
            get: () => 0,
            configurable: true
        });
        
        // Override plugin refresh method
        navigator.plugins.refresh = () => {};

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
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => new PluginArray(),
            configurable: true
        });
        
        Object.defineProperty(navigator, 'mimeTypes', {
            get: () => new MimeTypeArray(),
            configurable: true
        });
        
        // Override plugins length
        Object.defineProperty(navigator.plugins, 'length', {
            get: () => 0,
            configurable: true
        });
        
        // Override plugin refresh method
        navigator.plugins.refresh = () => {};  
    """,
    "iOS_Safari": """
        // iOS 16 Safari Spoofing
        Object.defineProperty(navigator, 'platform', {
            get: () => 'iPhone',
        });
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => new PluginArray(),
            configurable: true
        });
        
        Object.defineProperty(navigator, 'mimeTypes', {
            get: () => new MimeTypeArray(),
            configurable: true
        });
        
        // Override plugins length
        Object.defineProperty(navigator.plugins, 'length', {
            get: () => 0,
            configurable: true
        });
        
        // Override plugin refresh method
        navigator.plugins.refresh = () => {};  

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