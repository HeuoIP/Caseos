# Starts the FastAPI skeleton on 127.0.0.1:8000 for local Swagger access.
# Usage: powershell -ExecutionPolicy Bypass -File backend/scripts/run_dev.ps1
$projectRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$python = Join-Path $projectRoot '.tools\Python312\python.exe'
if (-not (Test-Path $python)) {
    Write-Host "Missing $python. Install Python 3.12 first." -ForegroundColor Red
    exit 1
}
Set-Location (Join-Path $projectRoot 'backend')
& $python -m pip install --quiet -r requirements.txt
& $python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
