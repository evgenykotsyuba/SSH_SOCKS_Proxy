from dataclasses import dataclass
import os
from dotenv import load_dotenv, set_key
import logging


@dataclass
class SSHConfig:
    def __init__(self, connection_name='Default', host=None, port=22, user=None, dynamic_port=1080,
                 auth_method='password', password=None, key_path=None,
                 http_proxy_port=8080, test_url=None, user_agent=None, home_page=None):
        self.connection_name = connection_name
        self.host = host
        self.port = port
        self.user = user
        self.dynamic_port = dynamic_port
        self.auth_method = auth_method
        self.password = password
        self.key_path = key_path
        self.test_url = test_url
        self.http_proxy_port = http_proxy_port
        self.user_agent = user_agent
        self.home_page = home_page


class ConfigManager:
    @staticmethod
    def create_default_env():
        if not os.path.exists('.env'):
            default_content = """
        CONNECTION_NAME=Default

        # SSH Connection Settings
        SSH_HOST=example.com
        SSH_USER=username
        SSH_PORT=22
        DYNAMIC_PORT=1080
        AUTH_METHOD=password
        TEST_URL=https://example.com
        HTTP_PROXY_PORT=8080
        SSH_PASSWORD=
        SSH_KEY_PATH=

        # Browser Settings
        USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36
        HOME_PAGE=https://www.whatismybrowser.com
        """
            with open('.env', 'w') as f:
                f.write(default_content.strip())
            logging.info("Default .env file created.")
        else:
            logging.info(".env file already exists.")

    @staticmethod
    def load_config() -> SSHConfig:
        load_dotenv()

        return SSHConfig(
            connection_name=os.getenv('CONNECTION_NAME', 'Default'),
            host=os.getenv('SSH_HOST', ''),
            port=int(os.getenv('SSH_PORT', '22')),
            user=os.getenv('SSH_USER', ''),
            auth_method=os.getenv('AUTH_METHOD', 'password'),
            password=os.getenv('SSH_PASSWORD', None),
            key_path=os.getenv('SSH_KEY_PATH', None),
            dynamic_port=int(os.getenv('DYNAMIC_PORT', '1080')),
            test_url=os.getenv('TEST_URL', ''),
            http_proxy_port=int(os.getenv('HTTP_PROXY_PORT', '8080')),
            user_agent = os.getenv('USER_AGENT', ''),
            home_page = os.getenv('HOME_PAGE', '')
        )

    @staticmethod
    def save_config(config: SSHConfig):
        env_vars = {
            'CONNECTION_NAME': str(config.connection_name),
            'SSH_HOST': config.host,
            'SSH_PORT': str(config.port),
            'SSH_USER': config.user,
            'AUTH_METHOD': config.auth_method,
            'SSH_PASSWORD': config.password or '',
            'SSH_KEY_PATH': config.key_path or '',
            'DYNAMIC_PORT': str(config.dynamic_port),
            'TEST_URL': str(config.test_url),
            'HTTP_PROXY_PORT': str(config.http_proxy_port),
            'USER_AGENT': str(config.user_agent),
            'HOME_PAGE': str(config.home_page)
        }
        for key, value in env_vars.items():
            set_key('.env', key, value)
