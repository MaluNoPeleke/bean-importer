#!/bin/bash
# Uninstalls the BeanImporter launchd agent (macOS) or systemd service (Linux).
# Run from the repo root: ./uninstall.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo "=== BeanImporter deinstallieren ==="
echo ""

# Stop the server
echo "Stoppe Server ..."
pkill -f "uvicorn main:app" 2>/dev/null || true

if [[ "$(uname)" == "Darwin" ]]; then
    LAUNCHD_DIR="$HOME/Library/LaunchAgents"
    PLIST_FILE="$LAUNCHD_DIR/com.beanimporter.plist"
    
    if [[ -f "$PLIST_FILE" ]]; then
        launchctl unload "$PLIST_FILE" 2>/dev/null || true
        rm -f "$PLIST_FILE"
        echo "[OK] LaunchAgent entfernt."
    else
        echo "[INFO] Kein LaunchAgent gefunden."
    fi
    
elif [[ -f /etc/os-release ]] && grep -q "Linux" /etc/os-release; then
    SERVICE_FILE="/etc/systemd/system/beanimporter.service"
    
    if [[ -f "$SERVICE_FILE" ]]; then
        sudo systemctl stop beanimporter
        sudo systemctl disable beanimporter
        rm -f "$SERVICE_FILE"
        sudo systemctl daemon-reload
        echo "[OK] systemd service entfernt."
    else
        echo "[INFO] Kein systemd service gefunden."
    fi
fi

echo ""
echo "=== Deinstallation abgeschlossen ==="
echo ""