# Example test run: python -m unittest discover -v -s tests -p "test_chrome.py"

import unittest
from unittest.mock import patch, MagicMock, call
from selenium.webdriver.chrome.options import Options
import logging
import os
import sys

# Get the absolute path to the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# Add project root and src directory to Python path
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

# Import the functions to test
from chrome import (
    get_locale_configuration,
    launch_chrome_with_socks_proxy,
    chrome_browser
)


class TestChromeBrowser(unittest.TestCase):
    """Comprehensive test suite for Chrome browser configuration and launch."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        self.test_home_page = "https://example.com"
        self.test_title = "Test Browser"
        self.test_language = "en"
        self.test_socks_port = 9150
        self.test_socks_host = "localhost"

    def test_language_accept_params(self):
        """Test get_locale_configuration returns correct Accept-Language headers"""
        test_cases = {
            'en': 'en-US,en;q=0.9',
            'ru': 'ru-RU,ru;q=0.9',
            'UA': 'uk-UA,uk;q=0.9',  # Test case insensitivity
            'fr': 'fr-FR,fr;q=0.9',
            'es': 'es-ES,es;q=0.9',
            'cn': 'zh-CN,zh;q=0.9',
            'de': 'de-DE,de;q=0.9',
            'unknown': 'en-US,en;q=0.9'  # Default fallback
        }

        for language, expected_header in test_cases.items():
            with self.subTest(language=language):
                result = get_locale_configuration(language)['accept_language']
                self.assertEqual(result, expected_header)

    def test_timezone_spoofing_params(self):
        """Test get_locale_configuration returns correct timezone configurations"""
        test_cases = {
            'en': {
                'name': 'America/Los_Angeles',
                'offset': 480,
                'display': 'Pacific Standard Time'
            },
            'ru': {
                'name': 'Europe/Moscow',
                'offset': -180,
                'display': 'Moscow Standard Time'
            },
            'UA': {  # Test case insensitivity
                'name': 'Europe/Kiev',
                'offset': -120,
                'display': 'Eastern European Standard Time'
            },
            'unknown': {
                'name': 'UTC',
                'offset': 0,
                'display': 'Coordinated Universal Time'
            }
        }

        for language, expected_config in test_cases.items():
            with self.subTest(language=language):
                result = get_locale_configuration(language)['timezone']
                self.assertEqual(result, expected_config)

    @patch('selenium.webdriver.Chrome')
    @patch('webdriver_manager.chrome.ChromeDriverManager')
    def test_launch_chrome_with_socks_proxy(self, mock_driver_manager, mock_chrome):
        """Test Chrome launch with SOCKS proxy configuration."""
        # Setup mock driver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver_manager.return_value.install.return_value = '/path/to/chromedriver'

        # Launch Chrome with test configuration
        driver = launch_chrome_with_socks_proxy(
            self.test_socks_host,
            self.test_socks_port,
            self.test_user_agent,
            self.test_home_page,
            self.test_title,
            self.test_language
        )

        # Verify Chrome options
        chrome_options_calls = mock_chrome.call_args[1]['options']
        self.assertIsInstance(chrome_options_calls, Options)

        # Verify proxy configuration
        proxy_arg = f"--proxy-server=socks5://{self.test_socks_host}:{self.test_socks_port}"
        self.assertIn(proxy_arg, chrome_options_calls.arguments)

        # Verify user agent
        user_agent_arg = f"--user-agent={self.test_user_agent}"
        self.assertIn(user_agent_arg, chrome_options_calls.arguments)

        # Verify basic settings
        self.assertIn("--incognito", chrome_options_calls.arguments)
        self.assertIn("--disable-webrtc", chrome_options_calls.arguments)

        # Verify page load and script execution
        mock_driver.get.assert_called_with(self.test_home_page)
        mock_driver.execute_script.assert_called()

    @patch('chrome.launch_chrome_with_socks_proxy')
    def test_chrome_browser(self, mock_launch):
        """Test the main chrome_browser function."""
        # Setup mock
        mock_driver = MagicMock()
        mock_launch.return_value = mock_driver

        # Test successful launch
        driver = chrome_browser(
            self.test_socks_port,
            self.test_user_agent,
            self.test_home_page,
            self.test_title,
            self.test_language
        )

        self.assertEqual(driver, mock_driver)
        mock_launch.assert_called_once_with(
            'localhost',
            self.test_socks_port,
            self.test_user_agent,
            self.test_home_page,
            self.test_title,
            self.test_language
        )

    @patch('chrome.get_canvas_fingerprinting_protection_script')
    @patch('chrome.get_font_fingerprinting_protection_script')
    @patch('chrome.get_timezone_spoofing_script')
    @patch('selenium.webdriver.Chrome')
    @patch('webdriver_manager.chrome.ChromeDriverManager')
    def test_chrome_fingerprinting_protection(
            self,
            mock_driver_manager,
            mock_chrome,
            mock_timezone_script,
            mock_font_script,
            mock_canvas_script
    ):
        """Test anti-fingerprinting features in Chrome."""

        # Setup mocks
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver_manager.return_value.install.return_value = '/path/to/chromedriver'

        # Setup mock return values for scripts
        mock_canvas_script.return_value = "mocked_canvas_script"
        mock_font_script.return_value = "mocked_font_script"
        mock_timezone_script.return_value = "mocked_timezone_script"

        # Launch Chrome with test configuration
        driver = launch_chrome_with_socks_proxy(
            self.test_socks_host,
            self.test_socks_port,
            self.test_user_agent,
            self.test_home_page,
            self.test_title,
            self.test_language
        )

        # Check if mock was called
        print("Canvas script call args:", mock_canvas_script.call_args_list)  # Дебаг

        # Verify that the scripts were requested
        mock_canvas_script.assert_called_once()
        mock_font_script.assert_called_once()
        mock_timezone_script.assert_called()

        # Verify that the scripts were injected
        expected_calls = [
            call("Page.addScriptToEvaluateOnNewDocument", {"source": "mocked_canvas_script"}),
            call("Page.addScriptToEvaluateOnNewDocument", {"source": "mocked_font_script"}),
            call("Page.addScriptToEvaluateOnNewDocument", {"source": "mocked_timezone_script"})
        ]

        # Check that all scripts were injected
        mock_driver.execute_cdp_cmd.assert_has_calls(expected_calls, any_order=True)

    def test_error_handling(self):
        """Test error handling in chrome_browser function."""
        # Test with invalid port type
        with self.assertRaises(TypeError):
            chrome_browser(
                "invalid_port",  # String instead of integer
                self.test_user_agent,
                self.test_home_page,
                self.test_title,
                self.test_language
            )

        # Test with negative port number
        with self.assertRaises(ValueError):
            chrome_browser(
                -1,  # Negative port number
                self.test_user_agent,
                self.test_home_page,
                self.test_title,
                self.test_language
            )


def setup_logging():
    """Configure logging for tests"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


if __name__ == '__main__':
    setup_logging()
    unittest.main()
