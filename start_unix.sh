#!/bin/bash
# Launches the BeanImporter FastAPI server in the background.
# Logs to logs/server.log relative to the project root (auto-created).

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/server.log"
LOG_FILE_PREV="$LOG_DIR/server.log.1"

mkdir -p "$LOG_DIR"

if [[ -f "$LOG_FILE" ]]; then
    if [[ -f "$LOG_FILE_PREV" ]]; then
        rm -f "$LOG_FILE_PREV"
    fi
    mv "$LOG_FILE" "$LOG_FILE_PREV"
fi

PYTHON_CMD="python3"
if ! command -v "$PYTHON_CMD" &> /dev/null; then
    PYTHON_CMD="python"
fi

BANNER="=== BeanImporter started $(date '+%Y-%m-%d %H:%M:%S') === python=$($PYTHON_CMD --version)"
echo "$BANNER" > "$LOG_FILE"

exec "$PYTHON_CMD" -m uvicorn main:app --host 127.0.0.1 --port 8000 --log-level info >> "$LOG_FILE" 2>&1