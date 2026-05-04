' Invisible launcher for start_server.ps1.
' wscript.exe runs without a console; Run(..., 0, False) starts PowerShell
' fully hidden (no flash) and returns immediately so the task ends cleanly
' while uvicorn keeps running.
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
ps1 = fso.BuildPath(scriptDir, "start_server.ps1")
cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File """ & ps1 & """"
CreateObject("WScript.Shell").Run cmd, 0, False
