# Installation and Usage

## Features

- Intuitive graphical interface for SSH proxy configuration
- Support for password and SSH key authentication
- Dynamic SOCKS proxy port configuration
- Integrated Chrome browser launch with proxy settings
- Comprehensive logging and connection status monitoring
- Cross-platform compatibility (Linux, macOS, Windows)
- Real-time traffic monitoring
- Multilingual interface (en, ru, ua, fr, es, cn)
- Support for HTTP proxy over SOCKS
- Password encryption
- Keepalive configuration for connections
- Customizable User-Agent and browser homepage
- Logging system

## Prerequisites

### System Requirements

- Python 3.7 or higher
- pip (Python package manager)
- SSH server access
- Chrome browser installed
- tkinter for GUI
- Integration with Chrome browser
- Multilingual support
- Traffic monitoring
- HTTP proxy over SOCKS

### Required System Packages

- Python development tools
- SSH client libraries
- Chrome WebDriver

### Required Python Packages

**Windows** - Installing with Python package.

**Linux** - Before running the application, install the following dependencies:
```bash
pip install tkinter
```

## Installation Steps

### 1. Clone the Repository
```bash
git clone https://github.com/evgenykotsyuba/SSH_SOCKS_Proxy ssh_socks_proxy
cd ssh_socks_proxy
```

### 2. Create Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Unix-like systems
venv\Scripts\activate     # On Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## Configuration Methods

### Authentication Options

#### 1. Password Authentication
- Simple and quick setup
- Enter SSH server credentials directly
- Less secure compared to key-based authentication

#### 2. SSH Key Authentication
- More secure authentication method
- Supports .pem and .key file formats
- Recommended for production environments

### Configuration Parameters

#### Required Settings
- SSH Host
- SSH Port (default: 22)
- Username
- Authentication Method
- Local Dynamic SOCKS Port (default: 1080)

#### Optional Settings
- Custom User Agent
- Browser Home Page
- Test SOCKS URL
- Keepalive settings
- HTTP proxy settings
- Traffic monitoring settings

## Running the Application

### Launch Methods
```bash
# Launch via Python
python src/main.py

# Linux Binary Execution
./dist/ssh_socks_proxy_binary

# Windows Binary Execution
dist\ssh_socks_proxy_binary.exe
```

### Application Workflow

1. Open application
2. Click "Settings"
3. Configure SSH connection details
4. Choose authentication method
5. Click "Connect"
6. Monitor connection status in log window
7. Launch Chrome browser with proxy settings (optional)
8. Monitor traffic in real-time
9. Customize User-Agent and homepage
10. Enable keepalive settings

## Advanced Configuration

### Environment Variable Overrides

Set these environment variables to pre-configure settings:

- `SSH_HOST`: SSH server hostname/IP
- `SSH_PORT`: SSH server port
- `SSH_USER`: SSH username
- `SSH_PASSWORD`: SSH password (not recommended)
- `SSH_KEY_PATH`: Path to SSH private key
- `AUTH_METHOD`: Authentication method (password/key)
- `DYNAMIC_PORT`: Local SOCKS proxy port
- `TEST_URL`: URL for proxy testing
- `USER_AGENT`: Browser user agent
- `HOME_PAGE`: Browser default homepage
- `KEEPALIVE`: Keepalive settings
- `HTTP_PROXY`: HTTP proxy settings

## Security Recommendations

### Best Practices
- Use SSH key authentication
- Set restrictive key file permissions
- Use strong, unique passwords
- Regularly rotate SSH credentials
- Keep application and dependencies updated
- Use firewall rules to restrict SSH access
- Encrypt passwords

### Potential Risks
- Avoid storing credentials in plain text
- Do not share SSH keys
- Be cautious when using public networks
- Monitor SSH connection logs
- Monitor traffic for suspicious activity

## Troubleshooting

### Common Connection Issues
- Verify SSH server accessibility
- Check firewall and network settings
- Confirm SSH credentials
- Validate SSH key file permissions
- Review application logs
- Check keepalive settings
- Verify HTTP proxy settings

### Debugging
- Enable verbose logging
- Check system network configuration
- Verify Chrome WebDriver compatibility
- Monitor traffic logs

## Supported Platforms
- Linux (Ubuntu, CentOS, Debian)
- macOS
- Windows 10/11