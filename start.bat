@echo off
chcp 65001 >nul
title Diet Management - Launcher
color 0A

echo ============================================
echo     Diet Management System - Quick Launch
echo ============================================
echo.
echo Checking environment...

:: ---------- 1. Check Python ----------
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)
for /f "tokens=1,2 delims= " %%a in ('python --version 2^>^&1') do set PY_VER=%%b
echo [OK] Python %PY_VER%

:: ---------- 2. Check Node.js ----------
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] Node.js not found. Please install Node.js 18+
    pause
    exit /b 1
)
echo [OK] Node.js found

:: ---------- 3. Install backend deps ----------
echo.
echo [1/4] Installing backend dependencies...
cd /d "%~dp0backend"
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [WARN] pip install failed, retrying...
    pip install -r requirements.txt
)

:: ---------- 4. Install frontend deps ----------
echo [2/4] Installing frontend dependencies...
cd /d "%~dp0frontend"
if not exist "node_modules" (
    call npm install --silent
) else (
    echo [OK] node_modules exists, skipping
)

:: ---------- 5. Start backend ----------
echo [3/4] Starting backend server (port 9876)...

:: Kill old process if port is in use
netstat -ano | findstr ":9876 " | findstr LISTENING >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Port 9876 in use, killing old process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":9876 " ^| findstr LISTENING') do (
        taskkill /f /pid %%a >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
)

start "Backend" cmd /k "color 0B && cd /d %~dp0backend && python run.py"

echo Waiting for backend...
timeout /t 3 /nobreak >nul

:: ---------- 6. Start frontend ----------
echo [4/4] Starting frontend dev server...

:: Kill old frontend processes on 5173/5174 to ensure single instance & fixed port
echo [INFO] Cleaning old frontend processes (port 5173/5174)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173 " ^| findstr LISTENING') do (
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5174 " ^| findstr LISTENING') do (
    taskkill /f /pid %%a >nul 2>&1
)
:: Fallback: kill any leftover vite node process
wmic process where "name='node.exe' and commandline like '%%vite%%'" call terminate >nul 2>&1
timeout /t 2 /nobreak >nul

start "Frontend" cmd /k "color 0C && cd /d %~dp0frontend && npm run dev"

:: ---------- Done ----------
echo.
echo ============================================
echo    All services started!
echo.
echo    Backend:  http://localhost:9876
echo    Frontend: http://localhost:5173
echo.
echo    Close each window to stop the service
echo ============================================
echo.

:: Open browser
timeout /t 2 /nobreak >nul
start http://localhost:5173

echo Press any key to close this window (services keep running)...
pause >nul
exit
