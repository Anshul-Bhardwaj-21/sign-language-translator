@echo off
echo ========================================
echo Sign Language Video Call System
echo Starting Development Servers...
echo ========================================
echo.

echo [1/2] Starting Backend Server...
start "Backend Server" cmd /k "python backend\enhanced_server.py"
timeout /t 3 /nobreak > nul

echo [2/2] Starting Frontend Server...
start "Frontend Server" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo Servers Starting!
echo ========================================
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to stop all servers...
pause > nul

taskkill /FI "WINDOWTITLE eq Backend Server*" /T /F
taskkill /FI "WINDOWTITLE eq Frontend Server*" /T /F
