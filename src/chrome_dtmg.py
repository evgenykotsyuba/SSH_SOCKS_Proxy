# Расширенная JavaScript-инъекция для блокировки трекинга
dtmg_script = """
// Блокировка Google Analytics и gtag
window.ga = window.ga || function() { console.log('GA blocked:', arguments); };
window.gtag = function() { console.log('GTag blocked:', arguments); };
window.dataLayer = window.dataLayer || [];
window.dataLayer.push = function() { console.log('DataLayer blocked:', arguments); };

// Удаление трекинговых атрибутов у всех элементов
const removeTrackingAttributes = (element) => {
    const attributes = ['onclick', 'onmousedown', 'onmouseup', 'onfocus', 'ontouchstart'];
    attributes.forEach(attr => element.removeAttribute(attr));
};

// Очистка URL от параметров трекинга
const cleanUrl = (url) => {
    try {
        const parsed = new URL(url);
        // Удаляем известные трекинговые параметры
        ['utm_', 'fbclid', 'gclid', 'msclkid'].forEach(param => {
            parsed.searchParams.forEach((_, key) => {
                if (key.startsWith(param)) parsed.searchParams.delete(key);
            });
        });
        return parsed.toString();
    } catch {
        return url;
    }
};

// Обработка ссылок, изображений и iframe
const processElements = () => {
    // Обработка всех элементов с href/src
    document.querySelectorAll('a, img, iframe').forEach(el => {
        if (el.tagName === 'A') {
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

    // Обработка форм
    document.querySelectorAll('form').forEach(form => {
        form.setAttribute('data-original-action', form.action);
        form.action = cleanUrl(form.action);
        removeTrackingAttributes(form);
    });
};

// Инициализация MutationObserver для динамических элементов
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

// Запуск обработки при загрузке и подключение наблюдателя
document.addEventListener('DOMContentLoaded', () => {
    processElements();
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: false
    });
});

// Перехват XMLHttpRequest и fetch для блокировки трекеров
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
