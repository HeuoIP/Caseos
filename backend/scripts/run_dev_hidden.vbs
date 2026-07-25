Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("Wscript.Shell")

scriptDir = fso.GetParentFileName(WScript.ScriptFullName)
projectRoot = fso.GetParentFolderName(scriptDir)
projectRoot = fso.GetParentFolderName(projectRoot)
projectRoot = fso.GetParentFolderName(projectRoot)
projectRoot = fso.GetParentFolderName(projectRoot)

pythonExe = projectRoot & "\.tools\Python312\python.exe"
psScript = projectRoot & "\backend\scripts\run_dev.ps1"

cmd = "powershell -NoLogo -NonInteractive -ExecutionPolicy Bypass -File """ & psScript & """"
shell.Run cmd, 0, False
