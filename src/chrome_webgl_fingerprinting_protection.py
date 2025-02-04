def modify_webgl_vendor_renderer(driver):
    """
    Full emulation of the WebGL fingerprint of an NVIDIA GTX 1080 Ti
    with deep interception of all possible detection methods.
    """
    webgl_spoofing_script = """
    // ================= GLOBAL INTERCEPTION OF PROTOTYPES =================
    const spoofedData = {
        vendor: 'NVIDIA Corporation',
        renderer: 'NVIDIA GeForce GTX 1080 Ti/PCIe/SSE2',
        version: 'WebGL 2.0',
        parameters: {
            [WebGLRenderingContext.VENDOR]: 'NVIDIA Corporation',
            [WebGLRenderingContext.RENDERER]: 'NVIDIA GeForce GTX 1080 Ti/PCIe/SSE2',
            [WebGLRenderingContext.VERSION]: 'WebGL 2.0',
            [WebGLRenderingContext.MAX_TEXTURE_SIZE]: 16384,
            [WebGLRenderingContext.MAX_RENDERBUFFER_SIZE]: 16384,
            [WebGL2RenderingContext.MAX_3D_TEXTURE_SIZE]: 2048,
            [WebGL2RenderingContext.MAX_COLOR_ATTACHMENTS]: 8
        },
        extensions: [
            'ANGLE_instanced_arrays',
            'EXT_blend_minmax',
            'WEBGL_debug_renderer_info'
        ]
    };

    // ========== OVERRIDING BASE WEBGL CLASSES ==========
    const wrapContext = (originalContext, isWebGL2 = false) => {
        const handler = {
            get(target, prop) {
                // Intercept getParameter
                if (prop === 'getParameter') {
                    return (param) => {
                        return spoofedData.parameters[param] || target.getParameter(param);
                    };
                }

                // Intercept getExtension
                if (prop === 'getExtension') {
                    return (name) => {
                        if (name === 'WEBGL_debug_renderer_info') {
                            return {
                                UNMASKED_VENDOR_WEBGL: spoofedData.vendor,
                                UNMASKED_RENDERER_WEBGL: spoofedData.renderer
                            };
                        }
                        return target.getExtension(name);
                    };
                }

                // Intercept supported extensions
                if (prop === 'getSupportedExtensions') {
                    return () => [...target.getSupportedExtensions(), ...spoofedData.extensions];
                }

                return target[prop];
            }
        };

        return new Proxy(originalContext, handler);
    };

    // ========== DEEP INTERCEPTION OF CANVAS ==========
    const originalCreateElement = Document.prototype.createElement;
    Document.prototype.createElement = function(type) {
        if (type === 'canvas') {
            const canvas = originalCreateElement.call(this, type);

            const originalGetContext = canvas.getContext.bind(canvas);
            canvas.getContext = function(type, attrs) {
                if (type === 'webgl' || type === 'webgl2') {
                    const ctx = originalGetContext(type, attrs);
                    return ctx ? wrapContext(ctx, type === 'webgl2') : null;
                }
                return originalGetContext(type, attrs);
            };

            return canvas;
        }
        return originalCreateElement.apply(this, arguments);
    };

    // ========== GPU EMULATION VIA NAVIGATOR ==========
    Object.defineProperty(navigator, 'gpu', {
        value: {
            requestAdapter: async () => ({
                name: spoofedData.renderer,
                features: [
                    'depth-clip-control',
                    'texture-compression-bc'
                ],
                limits: {
                    maxTextureDimension2D: 16384
                }
            })
        },
        configurable: false,
        writable: false
    });

    // ========== INTERCEPTION OF WEBGL SHADERS ==========
    const originalShaderSource = WebGLRenderingContext.prototype.shaderSource;
    WebGLRenderingContext.prototype.shaderSource = function(shader, source) {
        const modifiedSource = source.replace(/ATI/gi, 'NVIDIA')
                                     .replace(/Radeon/gi, 'GeForce');
        return originalShaderSource.call(this, shader, modifiedSource);
    };

    // ========== COLD START PROTECTION ==========
    if (window.WebGLRenderingContext) {
        const originalWebGL = window.WebGLRenderingContext;
        window.WebGLRenderingContext = class extends originalWebGL {
            constructor() {
                super();
                return wrapContext(this);
            }
        };
    }
    """

    # Double injection of the script for all frames
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": webgl_spoofing_script
    })

    # For already opened pages
    driver.execute_script(webgl_spoofing_script)

    return driver
