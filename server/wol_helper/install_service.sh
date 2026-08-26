#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/lan-control-plane-wol-helper"
SERVICE_NAME="lan-control-plane-wol-helper"
SERVICE_DEST="/etc/systemd/system/${SERVICE_NAME}.service"
ENV_SOURCE="${WOL_HELPER_ENV_FILE:-$SCRIPT_DIR/.env}"
ENV_DEST="/etc/${SERVICE_NAME}.env"

echo "==> Checking Python virtual environment support"
if ! python3 -c 'import venv' >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install python3-venv -y
fi

echo "==> Creating install directory"
sudo mkdir -p "$INSTALL_DIR"

echo "==> Copying helper files"
sudo cp "$SCRIPT_DIR/app.py" "$INSTALL_DIR/app.py"
sudo cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/requirements.txt"

if [ ! -f "$ENV_SOURCE" ]; then
  echo "Missing WOL helper environment file: $ENV_SOURCE" >&2
  echo "Create it from $SCRIPT_DIR/.env.example and use the same token in server/.env." >&2
  exit 1
fi
sudo install -m 600 "$ENV_SOURCE" "$ENV_DEST"

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
