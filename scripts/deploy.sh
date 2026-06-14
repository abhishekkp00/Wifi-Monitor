#!/bin/bash
# deploy.sh
# Deployment script to set up Wi-Fi Monitor as a systemd background service.

set -euo pipefail

# Ensure script is run with sudo
if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run this script with sudo:"
  echo "sudo ./scripts/deploy.sh"
  exit 1
fi

# Detect actual user (not root) and their home directory
REAL_USER="${SUDO_USER:-$(whoami)}"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "----------------------------------------"
echo "Deploying Wi-Fi Monitor"
echo "Project Directory: $PROJECT_DIR"
echo "Running as user  : $REAL_USER"
echo "----------------------------------------"

# 1. Check system dependencies
echo "Checking system dependencies..."
for cmd in ping nmcli ip; do
  if ! command -v "$cmd" &> /dev/null; then
    echo "Warning: Required system tool '$cmd' is not installed."
  fi
done

# 2. Update virtual environment and install requirements (including gunicorn)
echo "Installing python dependencies..."
sudo -u "$REAL_USER" "$PROJECT_DIR/venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt"

# 3. Create systemd service file
SERVICE_FILE="/etc/systemd/system/wifi-monitor.service"
echo "Creating systemd service file at $SERVICE_FILE..."

cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=Wi-Fi Monitor Dashboard
After=network.target

[Service]
Type=simple
User=$REAL_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$PROJECT_DIR/venv/bin/gunicorn -w 1 --threads 4 -b 0.0.0.0:5000 "dashboard.app:create_app(auto_run=True)"
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 4. Reload and start service
echo "Reloading systemd daemon..."
systemctl daemon-reload

echo "Enabling wifi-monitor service to start on boot..."
systemctl enable wifi-monitor

echo "Starting wifi-monitor service..."
systemctl restart wifi-monitor

echo "----------------------------------------"
echo "Deployment Successful!"
echo "Dashboard is running and accessible at:"
echo "http://localhost:5000 or http://<your-server-ip>:5000"
echo ""
echo "To check service status:  sudo systemctl status wifi-monitor"
echo "To view service logs:     sudo journalctl -u wifi-monitor -f"
echo "----------------------------------------"
