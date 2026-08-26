#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd -- "$AGENT_DIR/.." && pwd)"
INSTALL_DIR="/opt/lan-control-plane-agent"
PLIST_NAME="com.lancontrolplane.agent.plist"
PLIST_SOURCE="$AGENT_DIR/packaging/macos/$PLIST_NAME"
PLIST_DEST="/Library/LaunchDaemons/$PLIST_NAME"

if [ ! -d "$AGENT_DIR/src" ] || [ ! -d "$REPO_ROOT/shared/src" ]; then
  echo "Agent or shared sources are missing." >&2
  exit 1
fi
if [ ! -f "$AGENT_DIR/.env" ] && [ ! -f "$INSTALL_DIR/agent.env" ]; then
  echo "Missing agent/.env. Create it from agent/.env.example first." >&2
  exit 1
fi
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' || {
  echo "Python 3.12 or newer is required." >&2
  exit 1
}

sudo mkdir -p "$INSTALL_DIR" /var/log/lan-control-plane-agent
sudo rm -rf "$INSTALL_DIR/agent" "$INSTALL_DIR/shared"
sudo mkdir -p "$INSTALL_DIR/agent" "$INSTALL_DIR/shared"
sudo cp "$AGENT_DIR/pyproject.toml" "$AGENT_DIR/uv.lock" "$INSTALL_DIR/agent/"
sudo cp -R "$AGENT_DIR/src" "$INSTALL_DIR/agent/src"
sudo cp "$REPO_ROOT/shared/pyproject.toml" "$INSTALL_DIR/shared/"
sudo cp -R "$REPO_ROOT/shared/src" "$INSTALL_DIR/shared/src"
if [ ! -f "$INSTALL_DIR/agent.env" ]; then
  sudo cp "$AGENT_DIR/.env" "$INSTALL_DIR/agent.env"
fi
sudo chmod 600 "$INSTALL_DIR/agent.env"

sudo python3 -m venv "$INSTALL_DIR/bootstrap-venv"
sudo "$INSTALL_DIR/bootstrap-venv/bin/pip" install --no-cache-dir uv
cd "$INSTALL_DIR/agent"
sudo "$INSTALL_DIR/bootstrap-venv/bin/uv" sync --frozen --no-dev

sudo cp "$PLIST_SOURCE" "$PLIST_DEST"
sudo chown root:wheel "$PLIST_DEST"
sudo chmod 644 "$PLIST_DEST"
sudo launchctl bootout system "$PLIST_DEST" 2>/dev/null || true
sudo launchctl bootstrap system "$PLIST_DEST"
sudo launchctl enable "system/com.lancontrolplane.agent"

echo "LanControlPlaneAgent installed and started."
