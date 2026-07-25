# Stops any running CaseOS python processes and removes the scheduled task.
$ErrorActionPreference = 'Stop'
$taskName = 'CaseOS-Backend-Dev'

$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host ("Removed scheduled task: $taskName")
} else {
    Write-Host ("Scheduled task does not exist: $taskName")
}

Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalPort -eq 8000 } |
    ForEach-Object {
        try { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } catch {}
    }

Write-Host 'Done.'
