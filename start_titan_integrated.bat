@echo off
REM ===================================================================
REM TITAN INTEGRATED STARTUP (NO REDIS REQUIRED)
REM ===================================================================
REM Launches both Python brain and Node.js executor in parallel
REM Signals flow via JSON files: signals/outgoing -> signals/processed
REM ===================================================================

echo.
echo ========================================================================
echo   TITAN ARBITRAGE SYSTEM - INTEGRATED STARTUP
echo ========================================================================
echo   Mode: File-based signaling (No Redis required)
echo   Python Brain: Finds opportunities ^& writes signals
echo   Node.js Bot: Reads signals ^& executes (PAPER mode)
echo ========================================================================
echo.

cd /d "%~dp0"

REM Check if Node.js is installed
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if Python is installed
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH
    echo Please install Python 3.8+ from https://python.org/
    pause
    exit /b 1
)

REM Install Node.js dependencies if needed
if not exist "node_modules\" (
    echo [SETUP] Installing Node.js dependencies...
    call npm install
    if %errorlevel% neq 0 (
        echo [ERROR] npm install failed
        pause
        exit /b 1
    )
)

REM Create signal directories
if not exist "signals\outgoing\" mkdir "signals\outgoing"
if not exist "signals\processed\" mkdir "signals\processed"

echo [OK] Environment ready
echo.
echo Starting both processes...
echo   - Python Brain: mainnet_orchestrator.py
echo   - Node.js Bot: execution/bot.js
echo.
echo Press Ctrl+C to stop both processes
echo.

REM Start both processes in parallel using PowerShell
powershell -NoProfile -Command ^
    "$pythonJob = Start-Job -ScriptBlock { cd '%cd%'; python mainnet_orchestrator.py 2>&1 }; ^
     $nodeJob = Start-Job -ScriptBlock { cd '%cd%'; node execution/bot.js 2>&1 }; ^
     try { ^
         while ($true) { ^
             Receive-Job -Job $pythonJob,nodeJob -ErrorAction SilentlyContinue; ^
             Start-Sleep -Milliseconds 100; ^
             if ($pythonJob.State -eq 'Failed' -or $nodeJob.State -eq 'Failed') { break } ^
         } ^
     } finally { ^
         Stop-Job -Job $pythonJob,$nodeJob -ErrorAction SilentlyContinue; ^
         Remove-Job -Job $pythonJob,$nodeJob -ErrorAction SilentlyContinue; ^
     }"

echo.
echo ========================================================================
echo   System stopped
echo ========================================================================
pause
