# SSH SOCKS Proxy Manager

## Overview

SSH SOCKS Proxy Manager is a desktop application that simplifies establishing and managing SSH SOCKS proxy connections through a user-friendly graphical interface. It provides a robust solution for creating secure, encrypted tunnels through SSH, enabling users to route network traffic securely and bypass network restrictions.

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

### Logging and Monitoring
- **Advanced Logging Features**
  - Real-time logging display
  - Scrollable log text area with detailed entries
  - Comprehensive connection status tracking
- **Error Handling**
  - Detailed error notifications
  - Graceful error management and recovery

### Technical Highlights
- **Advanced Architecture**
  - Asynchronous connection management
  - Multithreaded design for responsive UI
  - Event-driven GUI using Tkinter
- **Robust Design**
  - Integrated configuration management
  - Comprehensive error handling
  - Secure connection protocols

## Authentication Methods

### Password Authentication
- Simple and quick setup
- Directly enter SSH credentials
- Suitable for quick, temporary connections

### SSH Key Authentication
- Enhanced Security
  - Support for PEM and key file formats
  - Secure key-based login mechanism
  - Easy key file selection through file browser
- Recommended for persistent and secure connections

## Use Cases

### Network Security
- Bypass network restrictions
- Create secure communication channels
- Protect sensitive data transmission

### Remote Access
- Establish secure connections to remote servers
- Access geo-restricted content
- Implement network tunneling

### Development and Testing
- Test applications through different network configurations
- Simulate various network environments
- Develop and debug network-dependent applications

## Technologies Used
- **Programming Language**: Python 3.7+
- **GUI Framework**: Tkinter
- **Asynchronous Programming**: Asyncio
- **Concurrency**: Threading
- **Logging**: Python's logging module

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

## Security Considerations
- Always use strong, unique passwords or SSH keys
- Regularly update SSH key pairs
- Be cautious when using public networks
- Verify SSH server authenticity before connecting

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

## License
GNU GENERAL PUBLIC LICENSE, Version 3.

## Disclaimer
This tool is intended for legitimate and authorized network access. Users are responsible for compliance with local laws and network policies.