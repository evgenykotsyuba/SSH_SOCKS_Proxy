# SSH SOCKS Proxy Manager

## Overview

SSH SOCKS Proxy Manager is a desktop application that simplifies establishing and managing SSH SOCKS proxy connections through a user-friendly graphical interface. It provides a robust solution for creating secure, encrypted tunnels through SSH, enabling users to route network traffic securely and bypass network restrictions.

## Purpose

- Anonymize network traffic.
- Bypass censorship or geoblocks.
- Change your visible IP address to protect your privacy.

## Key Features

### Connection Management
- **Secure Connection Establishment**
  - Establish secure SSH SOCKS proxy connections with a single click
  - Support for multiple authentication methods
    - Password-based authentication
    - SSH key-based authentication
- **Dynamic Port Configuration**
  - Flexible SOCKS port assignment
  - Configurable port settings to match network requirements
- **Intuitive Controls**
  - Easy connection and disconnection functionality
  - Real-time connection status indicators

### Configuration Options
- **Comprehensive SSH Configuration**
  - Configurable SSH host, port, and username
  - Flexible authentication method selection
  - SSH key file browser with format support
- **Environment Integration**
  - Environment variable support
  - Persistent configuration saving
- **Browser Integration**
  - Automatic Chrome browser launch with proxy settings
  - Customizable user agent and home page
- **Language Support**
  - Multilingual interface (en, ru, ua, fr, es, cn)
  - Easy language switching
- **Proxy Settings**
  - Support for HTTP proxy over SOCKS
  - Customizable proxy settings
  - Traffic monitoring capabilities

### Logging and Monitoring
- **Advanced Logging Features**
  - Real-time logging display
  - Scrollable log text area with detailed entries
  - Comprehensive connection status tracking
  - Traffic monitoring and statistics
- **Error Handling**
  - Detailed error notifications
  - Graceful error management and recovery
- **Connection Maintenance**
  - Keepalive configuration
  - Auto-reconnect capabilities
  - Connection health monitoring

### Technical Highlights
- **Advanced Architecture**
  - Asynchronous connection management
  - Multithreaded design for responsive UI
  - Event-driven GUI using Tkinter
- **Robust Design**
  - Integrated configuration management
  - Comprehensive error handling
  - Secure connection protocols
- **Security Features**
  - Password encryption
  - Secure key storage
  - Protected configuration files

## Authentication Methods

### Password Authentication
- Simple and quick setup
- Directly enter SSH credentials
- Suitable for quick, temporary connections
- Encrypted password storage

### SSH Key Authentication
- Enhanced Security
  - Support for PEM and key file formats
  - Secure key-based login mechanism
  - Easy key file selection through file browser
- Recommended for persistent and secure connections
- Support for various key formats and encryption standards

## Use Cases

### Network Security
- Bypass network restrictions
- Create secure communication channels
- Protect sensitive data transmission
- Implement VPN-like functionality

### Remote Access
- Establish secure connections to remote servers
- Access geo-restricted content
- Implement network tunneling
- Secure remote development environment access

### Development and Testing
- Test applications through different network configurations
- Simulate various network environments
- Develop and debug network-dependent applications
- Cross-platform testing capabilities

## Technologies Used
- **Programming Language**: Python 3.7+
- **GUI Framework**: Tkinter
- **Asynchronous Programming**: Asyncio
- **Concurrency**: Threading
- **Logging**: Python's logging module
- **Network**: Paramiko SSH library
- **Security**: cryptography library
- **Browser Automation**: Selenium WebDriver

## System Requirements
- **Minimum Python Version**: 3.7+
- **Operating Systems**: 
  - Windows 10/11
  - macOS 10.14+
  - Linux (Ubuntu 18.04+, Fedora 30+)
- **Prerequisites**
  - SSH server access
  - Internet connection
  - Chrome browser (for browser proxy feature)
  - Minimum 2GB RAM
  - 100MB free disk space

## Security Considerations
- Always use strong, unique passwords or SSH keys
- Regularly update SSH key pairs
- Be cautious when using public networks
- Verify SSH server authenticity before connecting
- Keep the application and dependencies updated
- Use firewall rules to restrict SSH access
- Monitor connection logs regularly
- Enable traffic monitoring for suspicious activity

## Installation
1. Ensure Python 3.7+ is installed
2. Clone the repository
3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python src/main.py
   ```

## Contributing
- Fork the repository
- Create a feature branch
- Submit pull requests
- Report issues and suggest improvements
- Follow coding standards and documentation guidelines
- Include tests for new features
- Update documentation as needed

## Support
- GitHub Issues: [[Repository Issue Tracker](https://github.com/evgenykotsyuba/SSH_SOCKS_Proxy/issues)]
- Email Support: -
- Documentation: [[Online Documentation Link](https://github.com/evgenykotsyuba/SSH_SOCKS_Proxy/tree/main/documentation)]
- Community Forum: [Forum Link]

## Version History
- v1.0.0 - Initial release
- v1.1.0 - Added multilingual support
- v1.2.0 - Implemented traffic monitoring
- v1.3.0 - Added HTTP proxy support
- v1.4.0 - Enhanced security features

## License
GNU GENERAL PUBLIC LICENSE, Version 3.

## Disclaimer
This tool is intended for legitimate and authorized network access. Users are responsible for compliance with local laws and network policies. The developers are not responsible for any misuse or damage caused by this software.

## Acknowledgments
Special thanks to:
- Open source community
- Contributors and testers
- Users providing valuable feedback
- Libraries and tools used in development