# Removes the BeanImporter scheduled task and stops it if running.

$ErrorActionPreference = "Stop"
$taskName = "BeanImporter"

if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "Removed task '$taskName'."
} else {
    Write-Host "No task named '$taskName' found."
}
