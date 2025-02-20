# chrome_canvas_fingerprinting_protection.py
import logging


def get_canvas_fingerprinting_protection_script():
    """
    Возвращает JavaScript код для защиты от Canvas fingerprinting.
    """
    canvas_protection_script = """
        (function() {
            // Store original functions
            const originalGetContext = HTMLCanvasElement.prototype.getContext;
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            const originalToBlob = HTMLCanvasElement.prototype.toBlob;
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;

            // Helper to add subtle noise to canvas data
            function addNoise(data) {
                const noise = 5;  // Small noise value
                for (let i = 0; i < data.length; i += 4) {
                    data[i] = Math.max(0, Math.min(255, data[i] + (Math.random() * 2 - 1) * noise));     // Red
                    data[i+1] = Math.max(0, Math.min(255, data[i+1] + (Math.random() * 2 - 1) * noise)); // Green
                    data[i+2] = Math.max(0, Math.min(255, data[i+2] + (Math.random() * 2 - 1) * noise)); // Blue
                    // Alpha channel remains unchanged
                }
                return data;
            }

            // Override getContext
            HTMLCanvasElement.prototype.getContext = function(type, attributes) {
                const context = originalGetContext.call(this, type, attributes);
                if (context && (type === '2d' || type === 'webgl' || type === 'experimental-webgl')) {
                    // Add noise to text rendering
                    const originalFillText = context.fillText;
                    context.fillText = function(...args) {
                        const result = originalFillText.apply(this, args);
                        // Add subtle randomization to text position
                        this.translate((Math.random() * 2 - 1) * 0.5, (Math.random() * 2 - 1) * 0.5);
                        return result;
                    };

                    // Add WebGL protection
                    if (type === 'webgl' || type === 'experimental-webgl') {
                        const originalGetParameter = context.getParameter;
                        context.getParameter = function(parameter) {
                            if (parameter === context.VERSION || parameter === context.SHADING_LANGUAGE_VERSION) {
                                return "WebGL 1.0 (OpenGL ES 2.0)";
                            }
                            return originalGetParameter.call(this, parameter);
                        };
                    }
                }
                return context;
            };

            // Override toDataURL
            HTMLCanvasElement.prototype.toDataURL = function(...args) {
                const context = this.getContext('2d');
                if (context) {
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    const pixels = imageData.data;
                    addNoise(pixels);
                    context.putImageData(imageData, 0, 0);
                }
                return originalToDataURL.apply(this, args);
            };

            // Override toBlob
            HTMLCanvasElement.prototype.toBlob = function(callback, ...args) {
                const context = this.getContext('2d');
                if (context) {
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    const pixels = imageData.data;
                    addNoise(pixels);
                    context.putImageData(imageData, 0, 0);
                }
                return originalToBlob.call(this, callback, ...args);
            };

            // Override getImageData
            CanvasRenderingContext2D.prototype.getImageData = function(...args) {
                const imageData = originalGetImageData.apply(this, args);
                imageData.data = addNoise(imageData.data);
                return imageData;
            };

            // Notify attempts to access canvas
            console.warn("Canvas fingerprinting protection active");
        })();
        """

    logging.info("Canvas fingerprinting protection script generated.")
    return canvas_protection_script
