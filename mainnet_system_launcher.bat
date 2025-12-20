@echo off
REM ==============================================================================
REM APEX-OMEGA TITAN: MAINNET SYSTEM LAUNCHER (Windows)
REM ==============================================================================
REM Complete mainnet orchestration for Windows with:
REM - Real-time data ingestion
REM - Real arbitrage calculations  
REM - Paper execution OR live blockchain interaction (configurable)
REM - Real-time ML model training
REM
REM Usage:
REM   mainnet_system_launcher.bat paper  - Start in paper mode (simulated execution)
REM   mainnet_system_launcher.bat live   - Start in live mode (real execution)
REM   mainnet_system_launcher.bat        - Use mode from .env (default: paper)

setlocal enabledelayedexpansion

REM Parse mode argument
set MODE=%1
if "%MODE%"=="" (
    REM Read from .env if no argument provided
    if exist .env (
        for /f "tokens=2 delims==" %%a in ('findstr /r "^EXECUTION_MODE=" .env') do set MODE=%%a
    )
    if "!MODE!"=="" set MODE=PAPER
)

REM Convert to uppercase
for %%i in (A B C D E F G H I J K L M N O P Q R S T U V W X Y Z) do call set MODE=%%MODE:%%i=%%i%%

REM Validate mode
if not "%MODE%"=="PAPER" if not "%MODE%"=="LIVE" (
    echo [31m❌ Invalid mode: %MODE%[0m
    echo Usage: %0 [paper^|live]
    exit /b 1
)

echo ===================================================
echo    APEX-OMEGA TITAN: MAINNET SYSTEM BOOT
echo ===================================================
echo.
echo [32m   Execution Mode: %MODE%[0m

if "%MODE%"=="PAPER" (
    echo [33m   📝 PAPER MODE: Trades will be simulated[0m
    echo       • Real-time mainnet data: ✓
    echo       • Real arbitrage calculations: ✓
    echo       • Blockchain execution: SIMULATED
    echo       • ML model training: ✓
) else (
    echo [31m   🔴 LIVE MODE: Real blockchain execution[0m
    echo       • Real-time mainnet data: ✓
    echo       • Real arbitrage calculations: ✓
    echo       • Blockchain execution: LIVE
    echo       • ML model training: ✓
    echo       ⚠️  WARNING: Real funds will be used!
)
echo.

REM Set environment variable
set EXECUTION_MODE=%MODE%
set TITAN_EXECUTION_MODE=%MODE%

REM Check prerequisites
echo [34m===================================================[0m
echo [34m   STEP 1: CHECKING PREREQUISITES[0m
echo [34m===================================================[0m
echo.

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [31m❌ Node.js not found![0m
    echo Please install Node.js 18+ from https://nodejs.org
    exit /b 1
)
echo [32m✅ Node.js installed[0m

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [31m❌ Python not found![0m
    echo Please install Python 3.11+ from https://python.org
    exit /b 1
)
echo [32m✅ Python installed[0m

REM Check .env file
if not exist .env (
    echo [33m⚠️  .env file not found, creating from template...[0m
    copy .env.example .env
    echo [33m⚠️  Please edit .env with your RPC endpoints and restart[0m
    pause
    exit /b 1
)
echo [32m✅ .env configuration found[0m

echo.
echo [34m===================================================[0m
echo [34m   STEP 2: INSTALLING DEPENDENCIES[0m
echo [34m===================================================[0m
echo.

REM Install Node dependencies
if not exist node_modules (
    echo Installing Node.js dependencies...
    call npm install --legacy-peer-deps
    if errorlevel 1 (
        echo [31m❌ npm install failed[0m
        exit /b 1
    )
)
echo [32m✅ Node.js dependencies ready[0m

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [31m❌ pip install failed[0m
    exit /b 1
)
echo [32m✅ Python dependencies ready[0m

echo.
echo [34m===================================================[0m
echo [34m   STEP 3: INITIALIZING SYSTEM COMPONENTS[0m
echo [34m===================================================[0m
echo.

REM Create necessary directories
if not exist signals\outgoing mkdir signals\outgoing
if not exist signals\processed mkdir signals\processed
if not exist logs mkdir logs
echo [32m✅ Signal directories created[0m

echo.
echo [34m===================================================[0m
echo [34m   STEP 4: STARTING MAINNET SYSTEM[0m
echo [34m===================================================[0m
echo.
echo [32m🚀 Launching Titan Mainnet System...[0m
echo.
echo [33mThis will start two processes:[0m
echo   1. Python Brain: Real-time data + calculations
echo   2. JavaScript Bot: Signal execution (%MODE% mode)
echo.
echo [33mPress Ctrl+C in each window to stop[0m
echo.

REM Start Python Brain in new window
echo [32m📡 Starting Python Brain (Data + Calculations)...[0m
start "Titan Brain - %MODE%" /D "%CD%" cmd /k "python mainnet_orchestrator.py"

REM Wait a moment for brain to initialize
timeout /t 3 /nobreak >nul

REM Start JavaScript Bot in new window
echo [32m⚙️  Starting JavaScript Bot (Execution)...[0m
start "Titan Bot - %MODE%" /D "%CD%" cmd /k "node execution\bot.js"

echo.
echo [32m===================================================[0m
echo [32m   ✅ TITAN MAINNET SYSTEM ONLINE[0m
echo [32m===================================================[0m
echo.
echo [33mMonitor the two windows for system activity:[0m
echo   • Brain window: Shows arbitrage calculations
echo   • Bot window: Shows trade executions
echo.
echo [33mSignal files: signals\outgoing\[0m
echo [33mProcessed signals: signals\processed\[0m
echo.
echo [32mSystem is running. Close this window to keep it running.[0m
echo.

pause
