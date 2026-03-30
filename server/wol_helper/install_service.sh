#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/lan-control-plane-wol-helper"
SERVICE_NAME="lan-control-plane-wol-helper"
SERVICE_DEST="/etc/systemd/system/${SERVICE_NAME}.service"

echo "==> Installing wakeonlan if missing"
if ! command -v wakeonlan >/dev/null 2>&1; then
  sudo apt-get install wakeonlan -y
fi
if ! command -v venv >/dev/null 2>&1; then
  sudo apt-get install python3-venv -y
fi

echo "==> Creating install directory"
sudo mkdir -p "$INSTALL_DIR"

echo "==> Copying helper files"
sudo cp "$SCRIPT_DIR/app.py" "$INSTALL_DIR/app.py"
sudo cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/requirements.txt"

echo "==> Creating virtual environment"
sudo python3 -m venv "$INSTALL_DIR/.venv"

echo "==> Installing Python dependencies"
sudo "$INSTALL_DIR/.venv/bin/pip" install --no-cache-dir -r "$INSTALL_DIR/requirements.txt"

echo "==> Installing systemd unit"
sudo cp "$SCRIPT_DIR/${SERVICE_NAME}.service" "$SERVICE_DEST"

echo "==> Reloading systemd"
sudo systemctl daemon-reload

echo "==> Enabling and restarting service"
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

echo "==> Status"
sudo systemctl status "$SERVICE_NAME" --no-pager
