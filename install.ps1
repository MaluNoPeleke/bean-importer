# BeanImporter — one-shot installer for Windows.
#
# What it does:
#   1. Checks for Python >= 3.12
#   2. Installs Python dependencies via pip
#   3. Registers the BeanImporter Windows scheduled task (runs at logon)
#   4. Starts the task immediately
#   5. Opens the browser on http://127.0.0.1:8000/ for first-run onboarding
#
# Run from the repo root:
#   powershell -ExecutionPolicy Bypass -File install.ps1

$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
Set-Location $projectRoot

Write-Host ""
Write-Host "=== BeanImporter installer ===" -ForegroundColor Cyan
Write-Host ""

# --- 1. Python version check -------------------------------------------------

$python = $null
foreach ($candidate in @("python", "py")) {
    $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($cmd) {
        $versionOutput = & $cmd.Source --version 2>&1
        if ($versionOutput -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 12)) {
                $python = $cmd.Source
                Write-Host "[OK] Python gefunden: $versionOutput  ($python)" -ForegroundColor Green
                break
            }
        }
    }
}

if (-not $python) {
    Write-Host "[FEHLER] Python >= 3.12 wurde nicht gefunden." -ForegroundColor Red
    Write-Host "         Bitte von https://www.python.org/downloads/ installieren"
    Write-Host "         und 'Add Python to PATH' aktivieren, dann install.ps1 erneut starten."
    exit 1
}

# --- 2. pip install ----------------------------------------------------------

Write-Host ""
Write-Host "Installiere Python-Pakete (pip install -r requirements.txt) ..." -ForegroundColor Cyan
& $python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { Write-Host "[FEHLER] pip-Upgrade fehlgeschlagen." -ForegroundColor Red; exit 1 }

& $python -m pip install -r (Join-Path $projectRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) { Write-Host "[FEHLER] pip install fehlgeschlagen." -ForegroundColor Red; exit 1 }

& $python -m playwright install chromium
if ($LASTEXITCODE -ne 0) { Write-Host "[FEHLER] Chromium-Download fehlgeschlagen." -ForegroundColor Red; exit 1 }

Write-Host "[OK] Pakete installiert." -ForegroundColor Green

# --- 3. Scheduled Task registrieren -----------------------------------------

Write-Host ""
Write-Host "Registriere Windows-Scheduled-Task 'BeanImporter' ..." -ForegroundColor Cyan
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $projectRoot "scripts\install_task.ps1")
if ($LASTEXITCODE -ne 0) { Write-Host "[FEHLER] Task-Registrierung fehlgeschlagen." -ForegroundColor Red; exit 1 }

# --- 4. Task starten ---------------------------------------------------------

Write-Host ""
Write-Host "Starte Server ..." -ForegroundColor Cyan

# Falls schon ein alter uvicorn auf Port 8000 hängt: vorher killen.
$existing = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($existing) {
    $existing | Select-Object -First 1 -ExpandProperty OwningProcess | ForEach-Object {
        try { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue } catch {}
    }
    Start-Sleep -Seconds 1
}

Start-ScheduledTask -TaskName "BeanImporter"

# Warte bis Port 8000 antwortet (max. 30s).
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
}

if ($ready) {
    Write-Host "[OK] Server läuft auf http://127.0.0.1:8000/" -ForegroundColor Green
} else {
    Write-Host "[WARN] Server hat innerhalb von 30s nicht geantwortet." -ForegroundColor Yellow
    Write-Host "       Logs: $(Join-Path $projectRoot 'logs\server.log')"
}

# --- 5. Browser öffnen -------------------------------------------------------

Write-Host ""
Write-Host "Öffne Browser für First-Run-Onboarding ..." -ForegroundColor Cyan
Start-Process "http://127.0.0.1:8000/"

Write-Host ""
Write-Host "=== Fertig ===" -ForegroundColor Green
Write-Host "Im Browser jetzt Provider wählen und API-Key einsetzen."
Write-Host "Der Server startet ab jetzt automatisch bei jeder Anmeldung."
Write-Host ""
Write-Host "Befehle für später:"
Write-Host "  Server neustarten:    Start-ScheduledTask  -TaskName BeanImporter"
Write-Host "  Server stoppen:       Stop-ScheduledTask   -TaskName BeanImporter"
Write-Host "  Deinstallieren:       powershell -ExecutionPolicy Bypass -File scripts\uninstall_task.ps1"
Write-Host ""
