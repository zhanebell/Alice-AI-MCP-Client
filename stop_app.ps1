# Alice AI Assignment Tracker Shutdown Script (PowerShell)

Write-Host "============================================" -ForegroundColor Red
Write-Host "   Alice AI Assignment Tracker Shutdown" -ForegroundColor Red
Write-Host "============================================" -ForegroundColor Red
Write-Host ""

Write-Host "Stopping all Alice AI services..." -ForegroundColor Yellow

# Function to kill processes on specific ports
function Kill-ProcessOnPort {
    param($Port)
    
    try {
        $processes = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
        foreach ($pid in $processes) {
            if ($pid) {
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                Write-Host "Stopped process $pid on port $Port" -ForegroundColor Green
            }
        }
    } catch {
        Write-Host "No processes found on port $Port" -ForegroundColor Gray
    }
}

# Kill processes on specific ports
Write-Host "Stopping Backend (port 8001)..." -ForegroundColor Yellow
Kill-ProcessOnPort -Port 8001

Write-Host "Stopping Frontend (port 3000)..." -ForegroundColor Yellow
Kill-ProcessOnPort -Port 3000

# Kill Python processes
Write-Host "Stopping Python processes..." -ForegroundColor Yellow
Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Kill Node.js processes
Write-Host "Stopping Node.js processes..." -ForegroundColor Yellow  
Get-Process -Name "node" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Kill any remaining PowerShell processes that might be running the services
Write-Host "Cleaning up background processes..." -ForegroundColor Yellow
Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like "*backend*python main.py*" -or $_.CommandLine -like "*frontend*npm run dev*" } | ForEach-Object { 
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped background process: $($_.ProcessId)" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "     All Alice AI services stopped!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your database and all data have been preserved." -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"
