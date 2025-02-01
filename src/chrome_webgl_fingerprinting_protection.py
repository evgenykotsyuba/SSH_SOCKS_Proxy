def modify_webgl_vendor_renderer(driver):
    """
    Modifies the WebGL Vendor and Renderer to spoof Nvidia Graphics, including all possible paths.

    Args:
        driver: The Selenium WebDriver instance.

    Returns:
        driver: The modified WebDriver instance.
    """
    webgl_spoofing_script = """
    // Override WebGL Vendor and Renderer
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        if (parameter === 37445) { // VENDOR
            return 'NVIDIA Corporation';
        }
        if (parameter === 37446) { // RENDERER
            return 'NVIDIA GeForce GTX 1080 Ti/PCIe/SSE2';
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
                    if (parameter === 37445) { // VENDOR
                        return 'NVIDIA Corporation';
                    }
                    if (parameter === 37446) { // RENDERER
                        return 'NVIDIA GeForce GTX 1080 Ti/PCIe/SSE2';
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
            if (parameter === 37445) { // VENDOR
                return 'NVIDIA Corporation';
            }
            if (parameter === 37446) { // RENDERER
                return 'NVIDIA GeForce GTX 1080 Ti/PCIe/SSE2';
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
    """

    # Execute the script to override WebGL Vendor and Renderer
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": webgl_spoofing_script
    })

    return driver
