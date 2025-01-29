# chrome_timezone_configuration.py

def get_timezone_spoofing_script(tz_config: dict, accept_language: str) -> str:
    """
    Generates a JavaScript script to spoof the timezone and related properties.

    Args:
        tz_config (dict): Dictionary containing timezone configuration (name, offset, display).
        accept_language (str): Accept-Language header value.

    Returns:
        str: JavaScript script to spoof the timezone.
    """
    script = f"""
    // Timezone spoofing
    (function() {{
        const tzConfig = {{
            name: '{tz_config["name"]}',
            offset: {tz_config["offset"]},
            display: '{tz_config["display"]}'
        }};

        // Override Date methods
        const originalDate = Date;
        const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
        const originalToString = Date.prototype.toString;
        const originalToLocaleString = Date.prototype.toLocaleString;
        const originalToTimeString = Date.prototype.toTimeString;

        Date.prototype.getTimezoneOffset = function() {{
            return tzConfig.offset;
        }};

        Date.prototype.toString = function() {{
            const date = new originalDate(this.valueOf());
            return date.toLocaleString('{accept_language}', {{
                timeZone: tzConfig.name,
                hour12: false,
                weekday: 'short',
                year: 'numeric',
                month: 'short',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                timeZoneName: 'short'
            }});
        }};

        // Override Intl.DateTimeFormat
        const originalDateTimeFormat = Intl.DateTimeFormat;
        window.Intl.DateTimeFormat = function(locales, options) {{
            if (options === undefined) {{
                options = {{}};
            }}
            options.timeZone = tzConfig.name;
            return new originalDateTimeFormat(locales, options);
        }};

        // Override Intl.NumberFormat for locale-aware number formatting
        const originalNumberFormat = Intl.NumberFormat;
        window.Intl.NumberFormat = function(locales, options) {{
            if (options === undefined) {{
                options = {{}};
            }}
            options.timeZone = tzConfig.name;
            return new originalNumberFormat(locales, options);
        }};

        // Override Intl.RelativeTimeFormat for locale-aware relative time formatting
        const originalRelativeTimeFormat = Intl.RelativeTimeFormat;
        window.Intl.RelativeTimeFormat = function(locales, options) {{
            if (options === undefined) {{
                options = {{}};
            }}
            options.timeZone = tzConfig.name;
            return new originalRelativeTimeFormat(locales, options);
        }};

        // Override timezone-related properties
        Object.defineProperty(Intl, 'DateTimeFormat', {{
            writable: false,
            configurable: false
        }});

        Object.defineProperty(Intl, 'NumberFormat', {{
            writable: false,
            configurable: false
        }});

        Object.defineProperty(Intl, 'RelativeTimeFormat', {{
            writable: false,
            configurable: false
        }});

        // Override performance.timeOrigin and performance.now()
        const originalPerformance = window.performance;
        const performanceOffset = new originalDate().getTimezoneOffset() * 60 * 1000;

        Object.defineProperty(window, 'performance', {{
            get: function() {{
                return {{
                    ...originalPerformance,
                    timeOrigin: originalPerformance.timeOrigin - performanceOffset,
                    now: function() {{
                        return originalPerformance.now() - performanceOffset;
                    }}
                }};
            }}
        }});
    }})();
    """
    return script
