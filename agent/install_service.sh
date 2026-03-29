#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd -- "$AGENT_DIR/.." && pwd)"

INSTALL_DIR="/opt/lan-control-plane-agent"
SERVICE_NAME="lan-control-plane-agent"
SERVICE_FILE_SOURCE="$AGENT_DIR/packaging/linux/${SERVICE_NAME}.service"
SERVICE_FILE_DEST="/etc/systemd/system/${SERVICE_NAME}.service"

echo "==> Creating install directory"
sudo mkdir -p "$INSTALL_DIR"

echo "==> Copying agent and shared sources"
sudo rm -rf "$INSTALL_DIR/agent" "$INSTALL_DIR/shared"
sudo mkdir -p "$INSTALL_DIR"
sudo cp -r "$REPO_ROOT/agent" "$INSTALL_DIR/agent"
sudo cp -r "$REPO_ROOT/shared" "$INSTALL_DIR/shared"

echo "==> Preparing agent env file"
if [ ! -f "$INSTALL_DIR/agent.env" ]; then
  if [ -f "$AGENT_DIR/.env" ]; then
    sudo cp "$AGENT_DIR/.env" "$INSTALL_DIR/agent.env"
  else
    echo "Missing agent/.env. Create it from agent/.env.example first."
    exit 1
  fi
fi

echo "==> Creating virtual environment"
sudo python3 -m venv "$INSTALL_DIR/.venv"

echo "==> Installing uv"
sudo "$INSTALL_DIR/.venv/bin/pip" install --no-cache-dir uv

echo "==> Installing agent dependencies"
cd "$INSTALL_DIR/agent"
sudo "$INSTALL_DIR/.venv/bin/uv" sync --frozen --no-dev

echo "==> Installing systemd unit"
sudo cp "$SERVICE_FILE_SOURCE" "$SERVICE_FILE_DEST"

echo "==> Reloading systemd"
sudo systemctl daemon-reload

echo "==> Enabling service"
sudo systemctl enable "$SERVICE_NAME"

echo "==> Restarting service"
sudo systemctl restart "$SERVICE_NAME"

echo "==> Service status"
sudo systemctl status "$SERVICE_NAME" --no-pager
