# chrome_webrtc_protection.py

def get_webrtc_protection_script():
    """
    Returns a JavaScript script that enhances WebRTC protection by overriding
    native WebRTC methods and blocking potential IP leaks.

    Returns:
        str: JavaScript code for WebRTC protection
    """
    return """
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
    """