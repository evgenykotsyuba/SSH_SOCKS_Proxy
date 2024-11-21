# SSH SOCKS Proxy Manager: Installation and Usage Guide

## Prerequisites

### System Requirements
- Python 3.7 or higher
- pip (Python package manager)
- SSH server access

### Required Python Packages
Before running the application, install the following dependencies:

```bash
pip install tkinter asyncio
```

## Installation Steps

### 1. Clone the Repository
```bash
git clone https://github.com/evgenykotsyuba/SSH_SOCKS_Proxy
cd ssh-socks-proxy-manager
```

### 2. Create Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## Configuring SSH Connection

### Authentication Methods
The application supports two authentication methods:

#### 1. Password Authentication
- Enter SSH host
- Enter username
- Enter password

#### 2. SSH Key Authentication
- Enter SSH host
- Enter username
- Select SSH key file (*.pem or *.key)

## Running the Application

### Launch the Application
```bash
python src/main.py
```

## Linux binary assembly
```bash
./dist/ssh_socks_proxy_binary
```

## Configuration Guide

### Settings Window
1. Click "Settings" button
2. Choose authentication method
   - Password
   - SSH Key
3. Fill in required fields:
   - Host
   - Port (default: 22)
   - Username
   - Local Dynamic Port (default: 1080)

### Connection Process
1. Configure settings
2. Click "Connect"
3. Monitor connection status in log window
4. Click "Disconnect" to terminate connection

## Troubleshooting

### Common Issues
- Ensure SSH server is reachable
- Verify credentials
- Check firewall settings
- Confirm SSH key permissions (key authentication)

### Logging
- Detailed logs displayed in application window
- Helps diagnose connection problems

## Security Notes
- Store SSH keys securely
- Use strong, unique passwords
- Prefer key-based authentication

## Additional Configuration

### Environment Variables
You can pre-configure connection settings using environment variables:
- `SSH_HOST`
- `SSH_PORT`
- `SSH_USER`
- `SSH_PASSWORD`
- `SSH_KEY_PATH`
- `AUTH_METHOD`

## Recommended Practices
- Use SSH keys instead of passwords
- Limit SSH key access
- Regularly rotate credentials
- Keep application and dependencies updated

## Support
For issues or feature requests, please file a GitHub issue in the project repository.