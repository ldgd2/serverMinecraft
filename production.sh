#!/bin/bash

# Minecraft Server Manager - Production Service Installer (systemd)

# 1. Check for Root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./production.sh)"
  exit 1
fi

# 2. Determine Project Path and User
# Script is now in the root directory
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
VENV_PYTHON="$PROJECT_ROOT/venv/bin/python"

# Detect real user (who invoked sudo) to own the process
REAL_USER=${SUDO_USER:-$(whoami)}
REAL_GROUP=$(id -gn $REAL_USER)

echo "Configuration:"
echo "  Project Root: $PROJECT_ROOT"
echo "  User:         $REAL_USER"
echo "  Group:        $REAL_GROUP"
echo "  Python:       $VENV_PYTHON"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERROR: Virtual environment not found at $VENV_PYTHON"
    echo "Please run install.sh first."
    exit 1
fi

# 3. Create Service File
SERVICE_FILE="/etc/systemd/system/minecraft-manager.service"

echo "Creating service file at $SERVICE_FILE..."

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Minecraft Server Manager
After=network.target

[Service]
User=$REAL_USER
Group=$REAL_GROUP
WorkingDirectory=$PROJECT_ROOT
Environment="PATH=$PROJECT_ROOT/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
ExecStart=$VENV_PYTHON run.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 4. Enable and Start
echo "Reloading systemd daemon..."
systemctl daemon-reload

echo "Enabling service on boot..."
systemctl enable minecraft-manager

echo "Starting service..."
systemctl restart minecraft-manager

echo "----------------------------------------------------"
echo "Service installed and started successfully!"
echo "Check status with: systemctl status minecraft-manager"
echo "View logs with:    journalctl -u minecraft-manager -f"
echo "----------------------------------------------------"
