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
echo Using Yarn to install and run Titan...
echo.

REM Use yarn to run the install-and-run script
call yarn install-and-run:yarn

if %errorlevel% neq 0 (
    echo.
    echo [X] Failed to install and run Titan
    pause
    exit /b 1
)

echo.
echo [+] Titan is running!
pause
