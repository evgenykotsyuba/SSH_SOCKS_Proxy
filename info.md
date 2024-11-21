# SSH SOCKS Proxy Manager

## Overview

SSH SOCKS Proxy Manager is a desktop application that simplifies establishing and managing SSH SOCKS proxy connections through a user-friendly graphical interface.

## Key Features

### Connection Management
- Establish secure SSH SOCKS proxy connections
- Support for multiple authentication methods
  - Password-based authentication
  - SSH key-based authentication
- Dynamic port configuration
- Intuitive connection and disconnection controls

### Configuration Options
- Configurable SSH host, port, and username
- Flexible authentication method selection
- SSH key file browser
- Environment variable integration
- Persistent configuration saving

### Logging and Monitoring
- Real-time logging display
- Scrollable log text area
- Detailed connection status tracking
- Error handling and notifications

### Technical Highlights
- Asynchronous connection management
- Multithreaded design
- Event-driven GUI using Tkinter
- Integrated configuration management
- Robust error handling

## Authentication Methods

### Password Authentication
- Enter SSH credentials directly
- Simple and quick setup

### SSH Key Authentication
- Support for PEM and key file formats
- Secure key-based login
- File browser for easy key selection

## Technologies Used
- Python
- Tkinter (GUI)
- Asyncio (Asynchronous programming)
- Threading
- Logging

## System Requirements
- Python 3.7+
- SSH server access
- Internet connection