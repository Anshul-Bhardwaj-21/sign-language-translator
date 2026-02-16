@echo off
echo ========================================
echo   Starting Video Call App
echo ========================================
echo.

echo [1/2] Starting Backend Server...
start "Backend Server" cmd /k "cd backend && python server.py"
timeout /t 3 /nobreak > nul

echo [2/2] Starting Frontend...
start "Frontend Dev Server" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo   Both servers are starting!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Press any key to stop all servers...
pause > nul

taskkill /FI "WINDOWTITLE eq Backend Server*" /T /F
taskkill /FI "WINDOWTITLE eq Frontend Dev Server*" /T /F
