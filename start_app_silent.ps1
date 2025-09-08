# Alice AI Assignment Tracker Silent Startup Script
# PowerShell version - runs services in hidden background mode

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   Alice AI Assignment Tracker Startup" -ForegroundColor Cyan
Write-Host "         (Silent Background Mode)" -ForegroundColor Cyan  
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the correct directory
if (-not (Test-Path "backend\main.py")) {
    Write-Host "Error: backend\main.py not found!" -ForegroundColor Red
    Write-Host "Please run this script from the Alice-AI-MCP-Client directory" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path "frontend\package.json")) {
    Write-Host "Error: frontend\package.json not found!" -ForegroundColor Red
    Write-Host "Please run this script from the Alice-AI-MCP-Client directory" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[1/4] Starting Backend Server in background (FastAPI on port 8001)..." -ForegroundColor Yellow
$backendProcess = Start-Process powershell -ArgumentList "-WindowStyle", "Hidden", "-Command", "cd backend; python main.py" -WindowStyle Hidden -PassThru

Write-Host "[2/4] Waiting for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "[3/4] Starting Frontend Development Server in background (Vite on port 3000)..." -ForegroundColor Yellow
$frontendProcess = Start-Process powershell -ArgumentList "-WindowStyle", "Hidden", "-Command", "cd frontend; npm run dev" -WindowStyle Hidden -PassThru

Write-Host "[4/4] Opening application in browser..." -ForegroundColor Yellow
Start-Sleep -Seconds 8
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "   Alice AI Assignment Tracker Started!" -ForegroundColor Green
Write-Host "          (Running in Background)" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services running silently in background:" -ForegroundColor White
Write-Host "  - Backend API: http://localhost:8001" -ForegroundColor Gray
Write-Host "  - Frontend:    http://localhost:3000" -ForegroundColor Gray
Write-Host ""
Write-Host "Process IDs for reference:" -ForegroundColor White
Write-Host "  - Backend PID: $($backendProcess.Id)" -ForegroundColor Gray
Write-Host "  - Frontend PID: $($frontendProcess.Id)" -ForegroundColor Gray
Write-Host ""
Write-Host "The app should open automatically in your browser." -ForegroundColor White
Write-Host ""
Write-Host "To stop all services:" -ForegroundColor White
Write-Host "  1. Use the 'Shutdown' button in the web interface (recommended)" -ForegroundColor Gray
Write-Host "  2. Or run stop_app.bat" -ForegroundColor Gray
Write-Host "  3. Or close all browser windows and run stop_app.bat" -ForegroundColor Gray
Write-Host ""
Write-Host "This window will close in 5 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
exit
