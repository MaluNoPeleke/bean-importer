# Registers a Windows Scheduled Task that starts the BeanImporter server
# silently at user logon. Re-running this script overwrites the existing task.
# Run from any directory: powershell -ExecutionPolicy Bypass -File scripts\install_task.ps1

$ErrorActionPreference = "Stop"

$taskName = "BeanImporter"
$vbsLauncher = Join-Path $PSScriptRoot "start_server.vbs"

if (-not (Test-Path $vbsLauncher)) {
    throw "start_server.vbs not found at $vbsLauncher"
}

# Truly invisible launcher: wscript.exe has no console window of its own and
# starts powershell.exe with Run(..., 0) hidden, so there is no flash at logon.
# The .vbs delegates to start_server.ps1, which redirects output to logs\server.log.
$action = New-ScheduledTaskAction `
    -Execute "wscript.exe" `
    -Argument "`"$vbsLauncher`""

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
