# Advanced JavaScript injection for tracking prevention and blocking
dtmg_script = """
// Block Google Analytics and gtag functionality
// Replaces tracking functions with console logging for debugging
window.ga = window.ga || function() { console.log('GA blocked:', arguments); };
window.gtag = function() { console.log('GTag blocked:', arguments); };
window.dataLayer = window.dataLayer || [];
window.dataLayer.push = function() { console.log('DataLayer blocked:', arguments); };

// Remove tracking-related attributes from all elements
// Targets common event listener attributes used for tracking
const removeTrackingAttributes = (element) => {
    const attributes = ['onclick', 'onmousedown', 'onmouseup', 'onfocus', 'ontouchstart'];
    attributes.forEach(attr => element.removeAttribute(attr));
};

// Clean URLs by removing tracking parameters
// Handles various tracking parameter formats and malformed URLs
const cleanUrl = (url) => {
    try {
        const parsed = new URL(url);
        // Remove known tracking parameters (UTM, Facebook, Google Ads, Microsoft Ads)
        ['utm_', 'fbclid', 'gclid', 'msclkid'].forEach(param => {
            parsed.searchParams.forEach((_, key) => {
                if (key.startsWith(param)) parsed.searchParams.delete(key);
            });
        });
        return parsed.toString();
    } catch {
        return url; // Return original URL if parsing fails
    }
};

// Process links, images, and iframes to remove tracking
// Handles both static and dynamically added elements
const processElements = () => {
    // Process all elements with href/src attributes
    document.querySelectorAll('a, img, iframe').forEach(el => {
        if (el.tagName === 'A') {
            // Handle Google redirect URLs
            if (el.href.includes('google.com/url?')) {
                const url = new URL(el.href);
                el.href = url.searchParams.get('q') || el.href;
            }
            el.href = cleanUrl(el.href);
        } else if (el.src) {
            el.src = cleanUrl(el.src);
        }
        removeTrackingAttributes(el);
    });

    // Process forms to clean action URLs and remove tracking
    document.querySelectorAll('form').forEach(form => {
        form.setAttribute('data-original-action', form.action);
        form.action = cleanUrl(form.action);
        removeTrackingAttributes(form);
    });
};

// Initialize MutationObserver to handle dynamic content
// Monitors DOM changes and processes new elements
const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        mutation.addedNodes.forEach(node => {
            if (node.nodeType === Node.ELEMENT_NODE) {
                processElements();
                removeTrackingAttributes(node);
            }
        });
    });
});

// Set up initial processing and start observer
document.addEventListener('DOMContentLoaded', () => {
    processElements();
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: false
    });
});

// Intercept and block tracking requests
// Override XMLHttpRequest and fetch to prevent analytics calls
const originalXHROpen = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function(method, url) {
    if (url.includes('google-analytics.com')) {
        console.log('Blocked analytics request:', url);
        return;
    }
    originalXHROpen.apply(this, arguments);
};

const originalFetch = window.fetch;
window.fetch = function(url, options) {
    if (typeof url === 'string' && url.includes('google-analytics.com')) {
        console.log('Blocked analytics fetch:', url);
        return Promise.reject(new Error('Tracking blocked'));
    }
    return originalFetch.call(this, url, options);
};
"""
