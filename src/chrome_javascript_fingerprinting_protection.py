def get_javascript_fingerprinting_protection_script() -> str:
    return """
    (function() {
        // Apply CSP as early as possible
        const applyCsp = () => {
            const cspMeta = document.createElement('meta');
            cspMeta.httpEquiv = 'Content-Security-Policy';
            cspMeta.content = "default-src 'self'; " +
                "script-src 'self' 'unsafe-inline'; " +  // Allow inline scripts for compatibility
                "connect-src 'self'; " +
                "img-src 'self' data:; " +
                "style-src 'self' 'unsafe-inline'; " +  // Allow inline styles for compatibility
                "object-src 'none'; " +
                "base-uri 'self';";

            // Insert at the beginning of head for maximum effect
            if (document.head.firstChild) {
                document.head.insertBefore(cspMeta, document.head.firstChild);
            } else {
                document.head.appendChild(cspMeta);
            }
        };

        // Apply CSP immediately
        applyCsp();

        // Re-apply after DOMContentLoaded to ensure it's not overridden
        document.addEventListener('DOMContentLoaded', applyCsp);

        // Block external resources more effectively
        const isExternalResource = (url) => {
            if (!url) return false;
            try {
                // Handle relative URLs
                const absoluteUrl = new URL(url, window.location.href);
                return absoluteUrl.origin !== window.location.origin && 
                    !url.startsWith('data:') && 
                    !url.startsWith('blob:') &&
                    !url.startsWith('about:');
            } catch (e) {
                // Invalid URL format
                return false;
            }
        };

        // More effective mutation observer to block external scripts
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (!node.tagName) return;

                    const tagName = node.tagName.toLowerCase();

                    // Block external scripts
                    if (tagName === 'script') {
                        if (node.src && isExternalResource(node.src)) {
                            console.log('[Blocked] Third-party script:', node.src);
                            node.remove();
                            return;
                        }
                    }

                    // Block iframes, images, and other elements with external sources
                    if (['iframe', 'img', 'link', 'object', 'embed'].includes(tagName)) {
                        if (node.src && isExternalResource(node.src)) {
                            console.log('[Blocked] Third-party resource:', node.src);
                            if (tagName === 'img') {
                                // Replace with placeholder for images
                                node.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="1" height="1"%3E%3C/svg%3E';
                            } else {
                                node.remove();
                            }
                        }
                    }

                    // Handle noscript elements - make them truly invisible
                    if (tagName === 'noscript') {
                        node.style.display = 'none';
                        // Replace content with empty div
                        const emptyDiv = document.createElement('div');
                        emptyDiv.style.display = 'none';
                        node.parentNode.replaceChild(emptyDiv, node);
                    }
                });
            });
        });

        // Start observing as early as possible with comprehensive coverage
        observer.observe(document.documentElement, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['src', 'href', 'data']
        });

        // Override dangerous JavaScript functions
        const originalEval = window.eval;
        window.eval = function(code) {
            console.log('[Blocked] eval() attempt');
            return null;
        };

        const originalFunction = window.Function;
        window.Function = function(...args) {
            console.log('[Blocked] new Function() attempt');
            return () => {};
        };

        // Better noscript handling
        const handleNoscriptElements = () => {
            const noscriptElements = document.getElementsByTagName('noscript');
            Array.from(noscriptElements).forEach(element => {
                // Create a placeholder
                const placeholder = document.createElement('div');
                placeholder.style.display = 'none';
                element.parentNode.replaceChild(placeholder, element);
            });
        };

        // Handle noscript elements on load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', handleNoscriptElements);
        } else {
            handleNoscriptElements();
        }

        // Override document.write
        const originalWrite = document.write;
        document.write = function(...args) {
            const content = args.join('');
            if (content.includes('<script') || content.includes('<iframe')) {
                console.log('[Blocked] document.write() with potentially dangerous content');
                return;
            }
            // Sanitize noscript tags
            const sanitizedContent = content.replace(/<noscript[^>]*>(.*?)<\\/noscript>/gi, '');
            originalWrite.apply(document, [sanitizedContent]);
        };

        // Block WebAssembly
        window.WebAssembly = undefined;

        // Override createElement to block scripts and handle noscript
        const originalCreateElement = document.createElement;
        document.createElement = function(tagName, options) {
            const tag = typeof tagName === 'string' ? tagName.toLowerCase() : tagName;

            if (tag === 'script') {
                console.log('[Monitored] createElement("script") - returning neutered script');
                const safeScript = originalCreateElement.call(document, 'script', options);
                // Monitor src attribute changes
                const originalSetAttribute = safeScript.setAttribute;
                safeScript.setAttribute = function(name, value) {
                    if (name.toLowerCase() === 'src' && isExternalResource(value)) {
                        console.log('[Blocked] Setting external script source:', value);
                        return;
                    }
                    return originalSetAttribute.call(this, name, value);
                };
                return safeScript;
            }

            if (tag === 'noscript') {
                console.log('[Modified] createElement("noscript") - creating hidden div instead');
                const div = originalCreateElement.call(document, 'div', options);
                div.style.display = 'none';
                return div;
            }

            return originalCreateElement.call(document, tagName, options);
        };

        // Ensure JavaScript is detected as enabled
        const ensureJsDetection = () => {
            // Find and remove all noscript elements
            const noscripts = document.querySelectorAll('noscript');
            noscripts.forEach(ns => {
                if (ns && ns.parentNode) {
                    ns.parentNode.removeChild(ns);
                }
            });

            // Make sure JS-dependent elements are visible
            document.querySelectorAll('.js-enabled, [data-js-enabled]').forEach(el => {
                el.style.display = '';
            });

            document.querySelectorAll('.no-js, .js-disabled').forEach(el => {
                el.style.display = 'none';
            });

            // Add js class to html element (common pattern)
            document.documentElement.classList.remove('no-js');
            document.documentElement.classList.add('js');
        };

        // Run JS detection fix immediately and after DOM load
        ensureJsDetection();
        document.addEventListener('DOMContentLoaded', ensureJsDetection);
    })();
    """


def get_navigator_protection_script() -> str:
    return """
    (function() {
        // Comprehensive navigator protection
        const navigatorProps = {
            // Set javaEnabled to false
            javaEnabled: { value: () => false },

            // Hide webdriver
            webdriver: { value: false },

            // Set standard language values
            languages: { value: ['en-US', 'en'] },

            // Empty plugins and mimeTypes
            plugins: { 
                get: function() {
                    const fakePlugins = Object.create(PluginArray.prototype);
                    fakePlugins.length = 0;
                    return fakePlugins;
                }
            },
            mimeTypes: {
                get: function() {
                    const fakeMimeTypes = Object.create(MimeTypeArray.prototype);
                    fakeMimeTypes.length = 0;
                    return fakeMimeTypes;
                }
            }
        };

        // Apply all navigator protection properties
        for (const prop in navigatorProps) {
            try {
                Object.defineProperty(navigator, prop, navigatorProps[prop]);
            } catch (e) {
                console.log(`Could not modify navigator.${prop}`);
            }
        }

        // Hide automation-related objects
        const hideObjects = {
            'chrome': undefined,
            'Notification': undefined,
            '__nightmare': undefined,
            'domAutomation': undefined,
            'domAutomationController': undefined,
            '_selenium': undefined,
            'callSelenium': undefined,
            '_Selenium_IDE_Recorder': undefined,
            '_phantom': undefined,
            'phantom': undefined,
            'ClientUtils': undefined,
            'XPCNativeWrapper': undefined,
            'XPCSafeJSObjectWrapper': undefined
        };

        // Apply all hiding
        for (const prop in hideObjects) {
            try {
                Object.defineProperty(window, prop, { value: hideObjects[prop] });
            } catch (e) {
                console.log(`Could not hide ${prop}`);
            }
        }
    })();
    """
