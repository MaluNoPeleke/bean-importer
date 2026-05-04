# Launches the BeanImporter FastAPI server in the background.
# Logs to logs\server.log relative to the project root (auto-created).
# Old log is rotated to server.log.1 on each start (keep 1 history file).

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $projectRoot "logs"
$logFile = Join-Path $logDir "server.log"
$logFilePrev = Join-Path $logDir "server.log.1"

if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

if (Test-Path $logFile) {
    if (Test-Path $logFilePrev) { Remove-Item $logFilePrev -Force }
    Move-Item $logFile $logFilePrev
}

$python = (Get-Command python.exe).Source
$banner = "=== BeanImporter started $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') === python=$python"
$banner | Out-File -FilePath $logFile -Encoding utf8

Set-Location $projectRoot

# Start uvicorn, redirect both stdout and stderr to the log file.
# uvicorn logs to stderr; with ErrorActionPreference=Stop PowerShell would treat
# each stderr line as a NativeCommandError and abort the script, killing uvicorn.
# Switch to Continue and merge stderr into stdout before appending to the log.
$ErrorActionPreference = "Continue"
& $python -m uvicorn main:app --host 127.0.0.1 --port 8000 --log-level info 2>&1 |
    Out-File -FilePath $logFile -Encoding utf8 -Append
