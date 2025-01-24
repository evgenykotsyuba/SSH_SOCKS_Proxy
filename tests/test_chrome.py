# Example test run: python -m unittest discover -v -s tests -p "test_chrome.py"

import unittest
from unittest.mock import patch, MagicMock
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


class TestChromeBrowserUtilities(unittest.TestCase):
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

    @patch('chrome.webdriver.Chrome')
    @patch('chrome.Service')
    @patch('chrome.ChromeDriverManager')
    def test_launch_chrome_with_socks_proxy(self, mock_driver_manager, mock_service, mock_chrome):
        """Test launch_chrome_with_socks_proxy with mocked dependencies"""
        # Mock the dependencies
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_service.return_value = MagicMock()
        mock_driver_manager().install.return_value = '/path/to/chromedriver'

        # Test parameters
        socks_host = 'localhost'
        socks_port = 9150
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        home_page = 'https://example.com'
        custom_title = 'Test Browser'
        language_setting = 'en'

        try:
            # Call the function
            driver = launch_chrome_with_socks_proxy(
                socks_host, socks_port, user_agent, home_page, 
                custom_title, language_setting
            )

            # Assertions
            mock_chrome.assert_called_once()
            mock_driver.execute_cdp_cmd.assert_called()
            mock_driver.get.assert_called_with(home_page)
            mock_driver.execute_script.assert_called()
        except Exception as e:
            self.fail(f"launch_chrome_with_socks_proxy raised an unexpected exception: {e}")

    @patch('chrome.launch_chrome_with_socks_proxy')
    def test_chrome_browser(self, mock_launch_chrome):
        """Test chrome_browser with mocked launch_chrome_with_socks_proxy"""
        # Mock dependencies
        mock_driver = MagicMock()
        mock_launch_chrome.return_value = mock_driver

        # Test parameters
        socks_port = 9150
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        home_page = 'https://example.com'
        custom_title = 'Test Browser'
        language_setting = 'en'

        try:
            # Call the function
            driver = chrome_browser(
                socks_port, user_agent, home_page, 
                custom_title, language_setting
            )

            # Assertions
            mock_launch_chrome.assert_called_once_with(
                'localhost', socks_port, user_agent, home_page, 
                custom_title, language_setting
            )
            self.assertEqual(driver, mock_driver)
        except Exception as e:
            self.fail(f"chrome_browser raised an unexpected exception: {e}")


def setup_logging():
    """Configure logging for tests"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


if __name__ == '__main__':
    setup_logging()
    unittest.main()
