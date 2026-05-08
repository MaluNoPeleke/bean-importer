#!/bin/bash
# BeanImporter — one-shot installer for Unix/macOS.
#
# What it does:
#   1. Checks for Python >= 3.9
#   2. Installs Python dependencies via pip
#   3. Creates a launchd agent (macOS) or systemd service (Linux) for autostart
#   4. Starts the server immediately
#   5. Opens the browser on http://127.0.0.1:8000/ for first-run onboarding
#
# Run from the repo root:
#   ./install.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo ""
echo "=== BeanImporter installer ===" 
echo ""

# --- 1. Python version check -------------------------------------------------

PYTHON_CMD=""
for candidate in python3 py; do
    if command -v "$candidate" &> /dev/null; then
        PYTHON_VERSION=$("$candidate" --version 2>&1 | sed 's/.*Python \([0-9]*\.[0-9]*\).*/\1/')
        if [[ -n "$PYTHON_VERSION" ]]; then
            MAJOR="${PYTHON_VERSION%%.*}"
            MINOR="${PYTHON_VERSION##*.}"
            # Accept Python >= 3.9 (3.12 preferred but 3.9+ works)
            if [[ $MAJOR -gt 3 ]] || [[ $MAJOR -eq 3 && $MINOR -ge 9 ]]; then
                PYTHON_CMD="$candidate"
                echo "[OK] Python gefunden: $($candidate --version)"
                break
            fi
        fi
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    echo "[FEHLER] Python >= 3.9 wurde nicht gefunden."
    echo "         Bitte von https://www.python.org/downloads/ installieren"
    echo "         Oder via Homebrew: brew install python3"
    exit 1
fi

# --- 2. pip install ----------------------------------------------------------

echo ""
echo "Installiere Python-Pakete (pip install -r requirements.txt) ..."
"$PYTHON_CMD" -m pip install --upgrade pip
"$PYTHON_CMD" -m pip install -r requirements.txt

echo "[OK] Pakete installiert."

# --- 3. Launchd (macOS) or systemd (Linux) ----------------------------------

IS_MACOS=false
if [[ "$(uname)" == "Darwin" ]]; then
    IS_MACOS=true
    
    LAUNCHD_DIR="$HOME/Library/LaunchAgents/com.beanimporter"
    PLIST_FILE="$LAUNCHD_DIR/com.beanimporter.plist"
    
    echo ""
    echo "Registriere macOS LaunchAgent ..."
    
    mkdir -p "$LAUNCHD_DIR"
    
    cat > "$PLIST_FILE" << 'PLIST_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.beanimporter</string>
    <key>ProgramArguments</key>
    <array>
        <string>__SCRIPT_PATH__</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
</dict>
</plist>
PLIST_EOF
    
    SCRIPT_PATH="$PROJECT_ROOT/start_unix.sh"
    
    sed -i '' "s|__SCRIPT_PATH__|$SCRIPT_PATH|g" "$PLIST_FILE"
    
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
    launchctl load "$PLIST_FILE"
    
    echo "[OK] LaunchAgent installiert."
    
elif [[ -f /etc/os-release ]] && grep -q "Linux" /etc/os-release; then
    echo ""
    echo "Registriere systemd service ..."
    
    mkdir -p "$HOME/.config/systemd/user"
    SERVICE_FILE="$HOME/.config/systemd/user/beanimporter.service"
    
    cat > "$SERVICE_FILE" << 'EOF'
[Unit]
Description=BeanImporter FastAPI Server

[Service]
Type=simple
WorkingDirectory=PROJECT_ROOT
ExecStart=PROJECT_ROOT/start_unix.sh
Restart=on-failure

[Install]
WantedBy=default.target
EOF
    
    sed -i "s|PROJECT_ROOT|$PROJECT_ROOT|g" "$SERVICE_FILE"
    
    systemctl --user daemon-reload
    systemctl --user enable beanimporter
    systemctl --user restart beanimporter
    
    echo "[OK] systemd service installiert."
    
else
    echo "[WARN] Kein Autostart-Mechanismus erkannt (weder macOS noch systemd)."
    echo "      Bitte Server manuell starten: ./start_unix.sh"
fi

# --- 4. Server starten -----------------------------------------------------

echo ""
echo "Starte Server ..."

# Create logs directory
mkdir -p "$PROJECT_ROOT/logs"

# Kill existing process on port 8000
if lsof -ti :8000 &> /dev/null; then
    kill $(lsof -ti :8000) 2>/dev/null || true
    sleep 1
fi

# Start the server in background
nohup "$PYTHON_CMD" -m uvicorn main:app --host 127.0.0.1 --port 8000 --log-level info > "$PROJECT_ROOT/logs/server.log" 2>&1 &
SERVER_PID=$!

# Wait for server to be ready (max 30s)
READY=false
for i in {1..30}; do
    sleep 1
    if curl -s http://127.0.0.1:8000/ &> /dev/null; then
        READY=true
        break
    fi
done

if $READY; then
    echo "[OK] Server läuft auf http://127.0.0.1:8000/"
else
    echo "[WARN] Server hat innerhalb von 30s nicht geantwortet."
    echo "       Logs: $PROJECT_ROOT/logs/server.log"
fi

# --- 5. Browser öffnen -------------------------------------------------------

echo ""
echo "Öffne Browser für First-Run-Onboarding ..."

if [[ "$(uname)" == "Darwin" ]]; then
    open "http://127.0.0.1:8000/"
else
    xdg-open "http://127.0.0.1:8000/" &> /dev/null || sensible-browser "http://127.0.0.1:8000/" &> /dev/null || true
fi

echo ""
echo "=== Fertig ==="
echo "Im Browser jetzt Provider wählen und API-Key einsetzen."
echo "Der Server startet ab jetzt automatisch bei jeder Anmeldung."
echo ""
echo "Befehle für später:"
echo "  Server neustarten:    ./start_unix.sh"
echo "  Server stoppen:      pkill -f 'uvicorn main:app'"
echo "  Deinstallieren:       ./uninstall.sh"
echo ""