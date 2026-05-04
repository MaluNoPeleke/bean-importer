# Registers a Windows Scheduled Task that starts the BeanImporter server
# silently at user logon. Re-running this script overwrites the existing task.
# Run from any directory: powershell -ExecutionPolicy Bypass -File scripts\install_task.ps1

$ErrorActionPreference = "Stop"

$taskName = "BeanImporter"
$startScript = Join-Path $PSScriptRoot "start_server.ps1"

if (-not (Test-Path $startScript)) {
    throw "start_server.ps1 not found at $startScript"
}

# Hidden launcher: powershell.exe with -WindowStyle Hidden runs the script
# without flashing a console window. Output of the script itself is redirected
# inside start_server.ps1 to logs\server.log.
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$startScript`""

$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0)

# Run as the current interactive user, lowest privilege (no UAC prompt).
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Limited

if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "Removed existing task '$taskName'."
}

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Starts the local BeanImporter FastAPI server at user logon." | Out-Null

Write-Host "Installed task '$taskName'. It will run at next logon."
Write-Host "To start it now without rebooting:"
Write-Host "    Start-ScheduledTask -TaskName $taskName"
Write-Host "Logs: $((Join-Path (Split-Path -Parent $PSScriptRoot) 'logs\server.log'))"
