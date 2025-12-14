@echo off
REM ==============================================================================
REM APEX-OMEGA TITAN: ONE-CLICK INSTALL AND RUN (Windows)
REM ==============================================================================
REM This script installs all dependencies and starts the Titan system
REM Prerequisites: Node.js, Python, Git must be installed
REM Configuration: Edit .env file before running
REM ==============================================================================

setlocal enabledelayedexpansion

REM Set title and colors
TITLE Apex-Omega Titan - One Click Setup
color 0B

echo.
echo ================================================================
echo    APEX-OMEGA TITAN: ONE-CLICK INSTALL ^& RUN
echo ================================================================
echo.
echo This script will:
echo   1. Install Node.js dependencies
echo   2. Install Python dependencies  
echo   3. Compile smart contracts
echo   4. Start the Titan system
echo.
echo Make sure you have configured .env file first!
echo.

REM ==============================================================================
REM STEP 1: CHECK PREREQUISITES
REM ==============================================================================

echo [STEP 1/5] Checking prerequisites...
echo.

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Node.js not found. Please install from https://nodejs.org/
    pause
    exit /b 1
)
echo [+] Node.js found

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Python not found. Please install from https://python.org/
    pause
    exit /b 1
)
echo [+] Python found

where pip >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] pip not found. Please install with Python
    pause
    exit /b 1
)
echo [+] pip found

echo.

REM ==============================================================================
REM STEP 2: CHECK .env FILE
REM ==============================================================================

echo [STEP 2/5] Checking configuration...
echo.

if not exist .env (
    echo [!] .env file not found. Creating from template...
    if exist .env.example (
        copy .env.example .env >nul
        echo [+] .env file created from .env.example
        echo.
        echo [!] IMPORTANT: Edit .env file with your configuration before continuing!
        echo     - Add your PRIVATE_KEY
        echo     - Add RPC endpoints (Infura/Alchemy API keys)
        echo     - Add LIFI_API_KEY
        echo     - Configure EXECUTION_MODE (PAPER or LIVE)
        echo.
        pause
    ) else (
        echo [X] .env.example not found
        pause
        exit /b 1
    )
)
echo [+] .env file exists

echo.

REM ==============================================================================
REM STEP 3: INSTALL NODE.JS DEPENDENCIES
REM ==============================================================================

echo [STEP 3/5] Installing Node.js dependencies...
echo.

REM Try yarn first, fall back to npm
where yarn >nul 2>&1
if %errorlevel% equ 0 (
    echo [i] Using Yarn...
    call yarn install
) else (
    echo [i] Using npm...
    call npm install --legacy-peer-deps
)

if %errorlevel% neq 0 (
    echo [X] Failed to install Node.js dependencies
    pause
    exit /b 1
)
echo [+] Node.js dependencies installed

echo.

REM ==============================================================================
REM STEP 4: INSTALL PYTHON DEPENDENCIES
REM ==============================================================================

echo [STEP 4/5] Installing Python dependencies...
echo.

pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [X] Failed to install Python dependencies
    pause
    exit /b 1
)
echo [+] Python dependencies installed

echo.

REM ==============================================================================
REM STEP 5: COMPILE SMART CONTRACTS
REM ==============================================================================

echo [STEP 5/5] Compiling smart contracts...
echo.

call npx hardhat compile
if %errorlevel% neq 0 (
    echo [X] Failed to compile smart contracts
    pause
    exit /b 1
)
echo [+] Smart contracts compiled

echo.
echo ================================================================
echo    INSTALLATION COMPLETE!
echo ================================================================
echo.
echo Starting Titan system...
echo.

REM ==============================================================================
REM START THE SYSTEM
REM ==============================================================================

REM Start components in separate windows
start "Titan [BRAIN]" cmd /k "python ml/brain.py"
timeout /t 2 /nobreak >nul
start "Titan [EXECUTOR]" cmd /k "node execution/bot.js"

echo.
echo ================================================================
echo    TITAN SYSTEM IS NOW RUNNING!
echo ================================================================
echo.
echo Components started:
echo   - Brain (AI Engine): Python ml/brain.py
echo   - Executor (Trading Bot): Node execution/bot.js
echo.
echo Monitor the separate windows to see system activity.
echo.
echo To stop the system: Close the component windows or press Ctrl+C
echo.
pause
