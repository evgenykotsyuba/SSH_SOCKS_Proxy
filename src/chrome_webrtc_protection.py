def get_webrtc_protection_script():
    return """
        // Full override of RTCPeerConnection
        (function() {
            const originalRTCPeerConnection = window.RTCPeerConnection || window.webkitRTCPeerConnection;
            if (!originalRTCPeerConnection) return;

            function filterCandidate(candidate) {
                const patterns = [
                    /srflx/,  // Server Reflexive
                    /host/,   // Host (local IP)
                    /prflx/   // Peer Reflexive
                ];
                return patterns.some(re => re.test(candidate)) ? null : candidate;
            }

            window.RTCPeerConnection = function(...args) {
                const pc = new originalRTCPeerConnection(...args);

                // Intercept adding ICE candidates
                pc.addIceCandidate = function(candidate, ...rest) {
                    if (candidate.candidate) {
                        const filtered = filterCandidate(candidate.candidate);
                        if (!filtered) return Promise.resolve();
                        candidate = new RTCIceCandidate({...candidate, candidate: filtered});
                    }
                    return pc.addIceCandidate(candidate, ...rest);
                };

                // Filter SDP description
                const origSetLocalDesc = pc.setLocalDescription.bind(pc);
                pc.setLocalDescription = async (description) => {
                    if (description && description.sdp) {
                        description.sdp = description.sdp.split('\r\n')
                            .filter(line => !line.startsWith('a=candidate') || line.includes('relay'))
                            .join('\r\n');
                    }
                    return origSetLocalDesc(description);
                };

                return pc;
            };
        })();

        // Block WebRTC API
        Object.defineProperty(navigator, 'mediaDevices', {
            value: {
                getUserMedia: () => Promise.reject(new Error('WebRTC blocked')),
                enumerateDevices: () => Promise.resolve([])
            },
            configurable: false
        });

        Object.defineProperty(window, 'RTCPeerConnection', {configurable: false, writable: false});
        Object.defineProperty(window, 'webkitRTCPeerConnection', {configurable: false, writable: false});
    """