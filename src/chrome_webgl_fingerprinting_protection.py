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
            [WebGL2RenderingContext.MAX_COLOR_ATTACHMENTS]: 8,
            [WebGLRenderingContext.MAX_VERTEX_ATTRIBS]: 16,
            [WebGLRenderingContext.MAX_VERTEX_UNIFORM_VECTORS]: 1024,
            [WebGLRenderingContext.MAX_FRAGMENT_UNIFORM_VECTORS]: 1024,
            [WebGLRenderingContext.MAX_VARYING_VECTORS]: 30,
            [WebGLRenderingContext.MAX_VERTEX_TEXTURE_IMAGE_UNITS]: 16,
            [WebGLRenderingContext.MAX_TEXTURE_IMAGE_UNITS]: 16,
            [WebGLRenderingContext.MAX_COMBINED_TEXTURE_IMAGE_UNITS]: 32,
            [WebGLRenderingContext.MAX_CUBE_MAP_TEXTURE_SIZE]: 16384,
            [WebGL2RenderingContext.MAX_ARRAY_TEXTURE_LAYERS]: 2048,
            [WebGL2RenderingContext.MAX_SAMPLES]: 8,
            [WebGLRenderingContext.ALIASED_LINE_WIDTH_RANGE]: [1, 1],
            [WebGLRenderingContext.ALIASED_POINT_SIZE_RANGE]: [1, 1024]
        },
        extensions: [
            'ANGLE_instanced_arrays',
            'EXT_blend_minmax',
            'WEBGL_compressed_texture_s3tc',
            'WEBGL_compressed_texture_etc',
            'WEBGL_compressed_texture_bptc',
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
    
    // Intercepting existing Canvas elements
    const canvases = document.querySelectorAll('canvas');
    canvases.forEach(canvas => {
        const originalGetContext = canvas.getContext.bind(canvas);
        canvas.getContext = function(type, attrs) {
            if (type === 'webgl' || type === 'webgl2') {
                const ctx = originalGetContext(type, attrs);
                return ctx ? wrapContext(ctx, type === 'webgl2') : null;
            }
            return originalGetContext(type, attrs);
        };
    });

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


def modify_webgl_textures(driver):
    """
    Modifies WebGL textures to emulate an NVIDIA GTX 1080 Ti,
    including texture parameters, compression formats, and shader characteristics.
    """
    texture_spoofing_script = """
    // Texture parameter configuration for GTX 1080 Ti
    const textureConfig = {
        MAX_TEXTURE_SIZE: 16384,
        MAX_CUBE_MAP_TEXTURE_SIZE: 16384,
        MAX_3D_TEXTURE_SIZE: 2048,
        MAX_TEXTURE_IMAGE_UNITS: 32,
        MAX_COMBINED_TEXTURE_IMAGE_UNITS: 192,
        MAX_ARRAY_TEXTURE_LAYERS: 2048,
        COMPRESSED_TEXTURE_FORMATS: [
            33776, 33777, 33778, 33779,  // S3TC
            37492, 37493, 37494, 37495,  // BPTC
            35898, 35899, 35900          // ETC
        ],
        MAX_SAMPLES: 8
    };

    // Intercept basic texture parameters
    const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(param) {
        switch(param) {
            case WebGLRenderingContext.MAX_TEXTURE_SIZE:
                return textureConfig.MAX_TEXTURE_SIZE;
            case WebGLRenderingContext.MAX_CUBE_MAP_TEXTURE_SIZE:
                return textureConfig.MAX_CUBE_MAP_TEXTURE_SIZE;
            case WebGL2RenderingContext.MAX_3D_TEXTURE_SIZE:
                return textureConfig.MAX_3D_TEXTURE_SIZE;
            case WebGLRenderingContext.MAX_TEXTURE_IMAGE_UNITS:
                return textureConfig.MAX_TEXTURE_IMAGE_UNITS;
            case WebGLRenderingContext.MAX_COMBINED_TEXTURE_IMAGE_UNITS:
                return textureConfig.MAX_COMBINED_TEXTURE_IMAGE_UNITS;
            case WebGL2RenderingContext.MAX_ARRAY_TEXTURE_LAYERS:
                return textureConfig.MAX_ARRAY_TEXTURE_LAYERS;
            case WebGL2RenderingContext.MAX_SAMPLES:
                return textureConfig.MAX_SAMPLES;
            default:
                return originalGetParameter.call(this, param);
        }
    };

    // Override supported compression formats
    const originalGetSupportedExtensions = WebGLRenderingContext.prototype.getSupportedExtensions;
    WebGLRenderingContext.prototype.getSupportedExtensions = function() {
        const original = originalGetSupportedExtensions.call(this);
        return [...original, 
            'WEBGL_compressed_texture_s3tc',
            'WEBGL_compressed_texture_etc',
            'WEBGL_compressed_texture_bptc'
        ];
    };

    // Intercept texture creation
    const originalCreateTexture = WebGLRenderingContext.prototype.createTexture;
    WebGLRenderingContext.prototype.createTexture = function() {
        const texture = originalCreateTexture.call(this);

        // Override parameters when binding textures
        const originalBindTexture = this.bindTexture;
        this.bindTexture = function(target, texture) {
            originalBindTexture.call(this, target, texture);

            // Automatically set filtering parameters
            this.texParameteri(target, this.TEXTURE_MIN_FILTER, this.LINEAR_MIPMAP_LINEAR);
            this.texParameteri(target, this.TEXTURE_MAG_FILTER, this.LINEAR);
            this.texParameteri(target, this.TEXTURE_WRAP_S, this.REPEAT);
            this.texParameteri(target, this.TEXTURE_WRAP_T, this.REPEAT);
        };

        return texture;
    };

    // Override texture data
    const originalTexImage2D = WebGLRenderingContext.prototype.texImage2D;
    WebGLRenderingContext.prototype.texImage2D = function(target, level, internalformat, width, height, border, format, type, pixels) {

        // Filter specific formats
        if (internalformat === WebGLRenderingContext.COMPRESSED_RGB_S3TC_DXT1_EXT) {
            internalformat = WebGLRenderingContext.RGB;
        }

        return originalTexImage2D.call(
            this, target, level, internalformat, 
            width, height, border, format, type, pixels
        );
    };

    // Emulate rendering capabilities
    const originalRender = WebGLRenderingContext.prototype.drawElements;
    WebGLRenderingContext.prototype.drawElements = function(mode, count, type, offset) {
        // Add NVIDIA-specific rendering artifacts
        this.enable(this.POLYGON_SMOOTH);
        this.hint(this.POLYGON_SMOOTH_HINT, this.NICEST);
        return originalRender.call(this, mode, count, type, offset);
    };

    // Override shader information
    const originalShaderSource = WebGLRenderingContext.prototype.shaderSource;
    WebGLRenderingContext.prototype.shaderSource = function(shader, source) {
        const modifiedSource = source
            .replace(/Adreno/gi, 'NVIDIA')
            .replace(/Mali/gi, 'NVIDIA')
            .replace(/PowerVR/gi, 'NVIDIA')
            .replace(/Intel/gi, 'NVIDIA');
        return originalShaderSource.call(this, shader, modifiedSource);
    };
    """

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": texture_spoofing_script
    })
    driver.execute_script(texture_spoofing_script)

    return driver
