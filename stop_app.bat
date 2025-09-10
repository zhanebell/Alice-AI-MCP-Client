@echo off
echo ============================================
echo   Alice AI Assignment Tracker Shutdown
echo ============================================
echo.

REM Set the absolute path to the project directory
set "PROJECT_DIR=c:\Users\zhane\OneDrive\Desktop\Alice-AI-MCP-Client"

echo Stopping all Alice AI services...

REM Kill processes running on ports 8001 and 3000
echo Stopping Backend (port 8001)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do (
    taskkill /F /PID %%a >nul 2>&1
    if !errorlevel! equ 0 echo Backend process stopped.
)

echo Stopping Frontend (port 3000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do (
    taskkill /F /PID %%a >nul 2>&1
    if !errorlevel! equ 0 echo Frontend process stopped.
)

REM Also kill any Python processes running main.py
echo Stopping any remaining Python processes...
taskkill /F /IM python.exe >nul 2>&1

REM Kill any Node.js processes (Vite dev server)
echo Stopping any remaining Node.js processes...
taskkill /F /IM node.exe >nul 2>&1

REM Kill any hidden CMD windows that might be running the services
taskkill /F /FI "WINDOWTITLE eq Alice AI Backend" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Alice AI Frontend" >nul 2>&1

echo.
echo ============================================
echo     All Alice AI services stopped!
echo ============================================
echo.
echo Your database and all data have been preserved.
echo.
pause
