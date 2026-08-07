@echo off
chcp 65001 >nul
title Stop All Services
color 0C

echo Stopping all services...
echo.

:: ---------- 1. Kill by port ----------
echo [1/2] Finding and killing processes by port...

:: Kill backend (port 9876)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":9876 " ^| findstr LISTENING') do (
    echo    Stopping backend PID: %%a
    taskkill /f /pid %%a >nul 2>&1
)

:: Kill frontend (port 5173)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173 " ^| findstr LISTENING') do (
    echo    Stopping frontend PID: %%a
    taskkill /f /pid %%a >nul 2>&1
)

:: ---------- 2. Fallback: wmic cleanup ----------
echo [2/2] Cleaning up residual processes...
wmic process where "name='python.exe' and commandline like '%%run%%'" call terminate >nul 2>&1
wmic process where "name='python.exe' and commandline like '%%manage%%'" call terminate >nul 2>&1
wmic process where "name='node.exe' and commandline like '%%vite%%'" call terminate >nul 2>&1

:: ---------- 3. Clean PID file ----------
if exist "%~dp0backend\.server.pid" (
    del "%~dp0backend\.server.pid"
    echo    Cleaned .server.pid
)

echo.
echo All services stopped.
timeout /t 2 /nobreak >nul
