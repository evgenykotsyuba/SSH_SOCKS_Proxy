import re


def parse_os_from_user_agent(user_agent):
    """
    Extracts information about the operating system from the User-Agent string

    Args:
        user_agent (str): User-Agent string from the HTTP request

    Returns:
        str: Name of the operating system or "Unknown" if it cannot be determined
    """

    # Dictionary with regular expressions for different OS
    os_patterns = {
        # Windows
        'Windows': {
            'pattern': r'Windows NT (\d+\.\d+)',
        },
        # macOS
        'MacOS': {
            'pattern': r'Mac OS X (\d+[._]\d+[._]\d+|\d+[._]\d+)',
        },
        # iOS
        'iOS': {
            'pattern': r'iPhone OS (\d+[._]\d+)',
        },
        # Android
        'Android': {
            'pattern': r'Android (\d+\.?\d*)',
        },
        # Linux
        'Linux': {
            'pattern': r'Linux',
        }
    }

    # Check each pattern
    for os_name, os_info in os_patterns.items():
        match = re.search(os_info['pattern'], user_agent)
        if match:
            return os_name

    return "Unknown"


# Examples of usage:
test_user_agents = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 15; Pixel) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 15; Pixel) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
]


if __name__ == "__main__":
    for ua in test_user_agents:
        os_info = parse_os_from_user_agent(ua)
        print(f"User-Agent: {ua}\nOS: {os_info}\n")
