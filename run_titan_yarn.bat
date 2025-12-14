@echo off
REM ==============================================================================
REM APEX-OMEGA TITAN: ONE-CLICK YARN INSTALL AND RUN (Windows)
REM ==============================================================================
REM This script uses Yarn to install dependencies and starts the Titan system
REM Prerequisites: Node.js, Yarn, Python, Git must be installed
REM Configuration: Edit .env file before running
REM ==============================================================================

setlocal enabledelayedexpansion

REM Set title and colors
TITLE Apex-Omega Titan - One Click Setup (Yarn)
color 0B

echo.
echo ================================================================
echo    APEX-OMEGA TITAN: ONE-CLICK YARN INSTALL ^& RUN
echo ================================================================
echo.

REM Check if Yarn is installed
where yarn >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Yarn not found. Please install Yarn first:
    echo     npm install -g yarn
    echo.
    echo     Or use run_titan.bat which works with npm
    pause
    exit /b 1
)

echo [+] Yarn found
echo.
echo Installing and running Titan with Yarn...
echo.

REM Check for .env file
if not exist .env (
    echo [!] .env file not found. Creating from template...
    if exist .env.example (
        copy .env.example .env >nul
        echo [+] .env file created
        echo.
        echo [!] IMPORTANT: Edit .env file with your configuration!
        echo.
        pause
    )
)

REM Install dependencies with Yarn
echo [1/4] Installing Node.js dependencies with Yarn...
call yarn install
if %errorlevel% neq 0 (
    echo [X] Failed to install Node.js dependencies
    pause
    exit /b 1
)

echo [2/4] Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [X] Failed to install Python dependencies
    pause
    exit /b 1
)

echo [3/4] Compiling smart contracts...
call npx hardhat compile
if %errorlevel% neq 0 (
    echo [X] Failed to compile contracts
    pause
    exit /b 1
)

echo [4/4] Starting Titan system...
echo.
start "Titan [BRAIN]" cmd /k "python ml/brain.py"
timeout /t 2 /nobreak >nul
start "Titan [EXECUTOR]" cmd /k "node execution/bot.js"

echo.
echo [+] Titan is running in separate windows!
pause
