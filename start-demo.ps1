Set-Location $PSScriptRoot

Write-Host "Starting TRUSTLOCK backend and frontend..."

Start-Process powershell -ArgumentList "-NoExit", "-File", ".\backend\run.ps1"
Start-Process powershell -ArgumentList "-NoExit", "-File", ".\frontend\run.ps1"

Write-Host "Waiting for backend to be ready..."
$ready = $false
$lastError = ""

for ($i = 0; $i -lt 60; $i++) {
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8001/health" -Method Get -ErrorAction Stop
        if ($response.service -eq "trustlock") {
            $ready = $true
            break
        }
    } catch {
        $lastError = $_.Exception.Message
    }
    Start-Sleep -Seconds 1
}

if ($ready) {
    Write-Host "TRUSTLOCK backend ready." -ForegroundColor Green
    Start-Process "http://localhost:5173"
} else {
    Write-Host "Failed to start backend after 60 seconds." -ForegroundColor Red
    Write-Host "Last error: $lastError" -ForegroundColor Red
}
