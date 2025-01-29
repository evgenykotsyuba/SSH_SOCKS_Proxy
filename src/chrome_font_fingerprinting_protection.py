def get_font_fingerprinting_protection_script() -> str:
    """
    Returns a JavaScript script that protects against font fingerprinting.
    This script overrides font-related APIs to prevent fingerprinting.
    """
    font_protection_script = """
        // Override font-related APIs
        function protectFonts() {
            // Override font enumeration
            Object.defineProperty(document, 'fonts', {
                get: () => ({
                    ready: Promise.resolve(),
                    check: () => false,
                    load: () => Promise.reject(),
                    addEventListener: () => {},
                    removeEventListener: () => {}
                })
            });

            // Standardize font measurement with slight randomization
            if (HTMLCanvasElement.prototype.measureText) {
                const originalMeasureText = HTMLCanvasElement.prototype.measureText;
                HTMLCanvasElement.prototype.measureText = function(text) {
                    const baseWidth = text.length * 8;
                    const randomOffset = (Math.random() * 2 - 1) * 2; // Small random offset
                    return {
                        width: baseWidth + randomOffset,
                        actualBoundingBoxAscent: 8 + (Math.random() * 2 - 1) * 0.5,
                        actualBoundingBoxDescent: 2 + (Math.random() * 2 - 1) * 0.5,
                        fontBoundingBoxAscent: 8 + (Math.random() * 2 - 1) * 0.5,
                        fontBoundingBoxDescent: 2 + (Math.random() * 2 - 1) * 0.5
                    };
                };
            }

            // Override font loading
            if (window.FontFace) {
                window.FontFace = function() {
                    return {
                        load: () => Promise.reject(),
                        loaded: Promise.reject(),
                        status: 'error',
                        family: 'sans-serif'
                    };
                };
            }

            // Override getComputedStyle for font-related properties
            const originalGetComputedStyle = window.getComputedStyle;
            window.getComputedStyle = function(element, pseudoElement) {
                const styles = originalGetComputedStyle(element, pseudoElement);
                const fontFamily = styles.fontFamily;
                if (fontFamily) {
                    Object.defineProperty(styles, 'fontFamily', {
                        get: () => 'sans-serif'
                    });
                }
                return styles;
            };

            // Override CSS font loading
            if (window.CSS && window.CSS.fontFace) {
                window.CSS.fontFace = function() {
                    return {
                        status: 'error',
                        loaded: Promise.reject(),
                        family: 'sans-serif'
                    };
                };
            }

            // Override document.fonts.ready
            Object.defineProperty(document.fonts, 'ready', {
                get: () => Promise.resolve()
            });

            // Override document.fonts.check
            Object.defineProperty(document.fonts, 'check', {
                value: () => false
            });

            // Override document.fonts.load
            Object.defineProperty(document.fonts, 'load', {
                value: () => Promise.reject()
            });
        }

        protectFonts();

        // Monitor and reapply protection
        setInterval(protectFonts, 1000);
    """
    return font_protection_script
