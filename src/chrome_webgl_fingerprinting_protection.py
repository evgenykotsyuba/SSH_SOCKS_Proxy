def modify_webgl_vendor_renderer(driver):
    """
    Modifies the WebGL Vendor, Renderer, and other WebGL-related properties to spoof NVIDIA Graphics.
    This includes overriding WebGL1, WebGL2, and related WebGL context properties.

    Args:
        driver: The Selenium WebDriver instance.

    Returns:
        driver: The modified WebDriver instance.
    """
    webgl_spoofing_script = """
    // Define WebGL constants for better readability
    const VENDOR = WebGLRenderingContext.VENDOR;
    const RENDERER = WebGLRenderingContext.RENDERER;
    const VERSION = WebGLRenderingContext.VERSION;
    const MAX_VERTEX_UNIFORM_VECTORS = WebGLRenderingContext.MAX_VERTEX_UNIFORM_VECTORS;
    const MAX_COLOR_ATTACHMENTS = WebGL2RenderingContext.MAX_COLOR_ATTACHMENTS;
    const MAX_DRAW_BUFFERS = WebGL2RenderingContext.MAX_DRAW_BUFFERS;

    // Override WebGL Vendor, Renderer, and Version
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        if (parameter === VENDOR) {
            return 'NVIDIA Corporation';
        }
        if (parameter === RENDERER) {
            return 'NVIDIA GeForce GTX 1080 Ti/PCIe/SSE2';
        }
        if (parameter === VERSION) {
            return 'WebGL 2.0';
        }
        if (parameter === MAX_VERTEX_UNIFORM_VECTORS) {
            return 4096; // Realistic value for GTX 1080 Ti
        }
        return getParameter.call(this, parameter);
    };

    // Override Unmasked Vendor and Renderer
    const getExtension = WebGLRenderingContext.prototype.getExtension;
    WebGLRenderingContext.prototype.getExtension = function(name) {
        if (name === 'WEBGL_debug_renderer_info') {
            return {
                UNMASKED_VENDOR_WEBGL: 'NVIDIA Corporation',
                UNMASKED_RENDERER_WEBGL: 'NVIDIA GeForce GTX 1080 Ti/PCIe/SSE2'
            };
        }
        return getExtension.call(this, name);
    };

    // Override WebGL rendering context creation
    const originalGetContext = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function(type, attributes) {
        if (type === 'webgl' || type === 'webgl2') {
            const context = originalGetContext.call(this, type, attributes);
            if (context) {
                // Override WebGL debug info
                context.getParameter = function(parameter) {
                    if (parameter === VENDOR) {
                        return 'NVIDIA Corporation';
                    }
                    if (parameter === RENDERER) {
                        return 'NVIDIA GeForce GTX 1080 Ti/PCIe/SSE2';
                    }
                    if (parameter === VERSION) {
                        return 'WebGL 2.0';
                    }
                    if (parameter === MAX_VERTEX_UNIFORM_VECTORS) {
                        return 4096; // Realistic value for GTX 1080 Ti
                    }
                    return getParameter.call(this, parameter);
                };

                context.getExtension = function(name) {
                    if (name === 'WEBGL_debug_renderer_info') {
                        return {
                            UNMASKED_VENDOR_WEBGL: 'NVIDIA Corporation',
                            UNMASKED_RENDERER_WEBGL: 'NVIDIA GeForce GTX 1080 Ti/PCIe/SSE2'
                        };
                    }
                    return getExtension.call(this, name);
                };
            }
            return context;
        }
        return originalGetContext.call(this, type, attributes);
    };

    // Override WebGL2 properties
    if (typeof WebGL2RenderingContext !== 'undefined') {
        const getParameterWebGL2 = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === VENDOR) {
                return 'NVIDIA Corporation';
            }
            if (parameter === RENDERER) {
                return 'NVIDIA GeForce GTX 1080 Ti/PCIe/SSE2';
            }
            if (parameter === VERSION) {
                return 'WebGL 2.0';
            }
            if (parameter === MAX_COLOR_ATTACHMENTS) {
                return 8; // Realistic value for GTX 1080 Ti
            }
            if (parameter === MAX_DRAW_BUFFERS) {
                return 8; // Realistic value for GTX 1080 Ti
            }
            return getParameterWebGL2.call(this, parameter);
        };

        const getExtensionWebGL2 = WebGL2RenderingContext.prototype.getExtension;
        WebGL2RenderingContext.prototype.getExtension = function(name) {
            if (name === 'WEBGL_debug_renderer_info') {
                return {
                    UNMASKED_VENDOR_WEBGL: 'NVIDIA Corporation',
                    UNMASKED_RENDERER_WEBGL: 'NVIDIA GeForce GTX 1080 Ti/PCIe/SSE2'
                };
            }
            return getExtensionWebGL2.call(this, name);
        };
    }

    // Override supported extensions
    const getSupportedExtensions = WebGLRenderingContext.prototype.getSupportedExtensions;
    WebGLRenderingContext.prototype.getSupportedExtensions = function() {
        const original = getSupportedExtensions.call(this);
        return [...original, 'WEBGL_debug_renderer_info'];
    };

    // Emulate GPU properties
    if (!navigator.gpu) {
        navigator.gpu = {
            description: 'NVIDIA GeForce GTX 1080 Ti',
            vendor: 'NVIDIA Corporation',
            architecture: 'Pascal'
        };
    }
    """

    # Execute the script to override WebGL Vendor and Renderer
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": webgl_spoofing_script
    })

    return driver
