from dataclasses import dataclass
import os
from dotenv import load_dotenv, set_key


@dataclass
class SSHConfig:
    def __init__(self, host=None, port=22, user=None, dynamic_port=1080,
                 auth_method='password', password=None, key_path=None, test_url=None):
        self.host = host
        self.port = port
        self.user = user
        self.dynamic_port = dynamic_port
        self.auth_method = auth_method
        self.password = password
        self.key_path = key_path
        self.test_url = test_url


class ConfigManager:
    @staticmethod
    def load_config() -> SSHConfig:
        load_dotenv()

        return SSHConfig(
            host=os.getenv('SSH_HOST', ''),
            port=int(os.getenv('SSH_PORT', '22')),
            user=os.getenv('SSH_USER', ''),
            auth_method=os.getenv('AUTH_METHOD', 'password'),
            password=os.getenv('SSH_PASSWORD', None),
            key_path=os.getenv('SSH_KEY_PATH', None),
            dynamic_port=int(os.getenv('DYNAMIC_PORT', '1080')),
            test_url=os.getenv('TEST_URL', '')
        )

    @staticmethod
    def save_config(config: SSHConfig):
        env_vars = {
            'SSH_HOST': config.host,
            'SSH_PORT': str(config.port),
            'SSH_USER': config.user,
            'AUTH_METHOD': config.auth_method,
            'SSH_PASSWORD': config.password or '',
            'SSH_KEY_PATH': config.key_path or '',
            'DYNAMIC_PORT': str(config.dynamic_port),
            'TEST_URL': str(config.test_url)
        }
        for key, value in env_vars.items():
            set_key('.env', key, value)

    @staticmethod
    def create_default_env():
        default_content = """
# SSH Connection Settings
SSH_HOST=example.com
SSH_USER=username
SSH_PORT=22
DYNAMIC_PORT=1080
AUTH_METHOD=password
TEST_URL=https://example.com
# SSH_PASSWORD=your_password
# SSH_KEY_PATH=/path/to/private/key
"""
        with open('.env', 'w') as f:
            f.write(default_content.strip())