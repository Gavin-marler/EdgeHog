#!/bin/bash
set -e

echo "Deploying EdgeHog..."

# Create Python virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Install dependencies
./venv/bin/pip install -r requirements.txt

# Copy systemd service file
sudo cp edgehog.service /etc/systemd/system/

# Reload systemd and enable/start the service
sudo systemctl daemon-reload
sudo systemctl enable edgehog.service
sudo systemctl restart edgehog.service

echo "Deployment complete. EdgeHog is running."
echo "View logs with: sudo journalctl -u edgehog -f"
