def modify_audiocontext() -> str:
    audiocontext_protection_script = """
        // AudioContext Fingerprinting Protection
        const originalAudioContext = AudioContext.prototype.getChannelData;
        AudioContext.prototype.getChannelData = function (param) {
            // Generate fake data
            return new Float32Array(param).fill(0);
        };
    """
    return audiocontext_protection_script
