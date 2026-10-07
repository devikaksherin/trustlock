Set-Location $PSScriptRoot
if (!(Test-Path .\venv)) {
    Write-Host "Virtual environment not found. Run these commands:"
    Write-Host "python -m venv venv"
    Write-Host ".\venv\Scripts\python.exe -m pip install -r requirements.txt"
    exit 1
}
.\venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8001
