# Registers a startup task that boots the CaseOS FastAPI skeleton hidden.
# Usage: powershell -ExecutionPolicy Bypass -File backend/scripts/register_startup.ps1
$ErrorActionPreference = 'Stop'

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$vbs = Join-Path $projectRoot 'backend\scripts\run_dev_hidden.vbs'
if (-not (Test-Path $vbs)) {
    throw "Missing launcher: $vbs"
}

$taskName = 'CaseOS-Backend-Dev'
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

$action = New-ScheduledTaskAction -Execute 'wscript.exe' `
    -Argument ('"' + $vbs + '"') `
    -WorkingDirectory $projectRoot

$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
    -MultipleInstances IgnoreNew -Compatibility Win8 -AllowHardTerminate:$false `
    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description 'Launch the CaseOS FastAPI development server (hidden) at user logon.' `
    -Force | Out-Null

Write-Host ('Scheduled task "{0}" registered. Swagger will be served at http://localhost:8000/docs once it starts.' -f $taskName)
