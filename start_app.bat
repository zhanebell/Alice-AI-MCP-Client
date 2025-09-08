@echo off
echo ============================================
echo    Alice AI Assignment Tracker Startup
echo ============================================
echo.

REM Check if we're in the correct directory
if not exist "backend\main.py" (
    echo Error: backend\main.py not found!
    echo Please run this script from the Alice-AI-MCP-Client directory
    pause
    exit /b 1
)

if not exist "frontend\package.json" (
    echo Error: frontend\package.json not found!
    echo Please run this script from the Alice-AI-MCP-Client directory
    pause
    exit /b 1
)

echo [1/4] Starting Backend Server (FastAPI on port 8001)...
start /min "Alice AI Backend" cmd /c "cd backend && python main.py"

echo [2/4] Waiting for backend to start...
timeout /t 3 /nobreak > nul

echo [3/4] Starting Frontend Development Server (Vite on port 3000)...
start /min "Alice AI Frontend" cmd /c "cd frontend && npm run dev"

echo [4/4] Opening application in browser...
timeout /t 5 /nobreak > nul
start "" "http://localhost:3000"

echo.
echo ============================================
echo    Alice AI Assignment Tracker Started!
echo ============================================
echo.
echo Services running in background:
echo   - Backend API: http://localhost:8001
echo   - Frontend:    http://localhost:3000
echo.
echo The app should open automatically in your browser.
echo.
echo To stop all services:
echo   1. Use the 'Shutdown App' button in the web interface
echo   2. Or run stop_app.bat
echo   3. Or close the browser and the services will continue running
echo.
echo This window will close in 3 seconds...
timeout /t 3 /nobreak > nul
exit
echo Your database (assignments.db) will persist between sessions.
echo.
pause
