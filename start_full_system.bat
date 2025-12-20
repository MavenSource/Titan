@echo off
REM ==============================================================================
REM APEX-OMEGA TITAN: FULL SYSTEM LAUNCHER
REM ==============================================================================
REM Starts both Brain and Bot in separate windows that stay open

echo.
echo ===================================================
echo    APEX-OMEGA TITAN: STARTING FULL SYSTEM
echo ===================================================
echo.

REM Set execution mode
set EXECUTION_MODE=PAPER
echo Mode: %EXECUTION_MODE%
echo.

REM Start Brain in new window
echo [32mStarting Brain (Python)...[0m
start "Titan Brain - PAPER MODE" cmd /k "set EXECUTION_MODE=PAPER && python mainnet_orchestrator.py"

REM Wait for Brain to initialize
timeout /t 5 /nobreak >nul

REM Start Bot in new window
echo [32mStarting Bot (JavaScript)...[0m
start "Titan Bot - PAPER MODE" cmd /k "set EXECUTION_MODE=PAPER && node execution\bot.js"

echo.
echo [32m====================================================[0m
echo [32m   TITAN SYSTEM LAUNCHED[0m
echo [32m====================================================[0m
echo.
echo Two windows opened:
echo   1. Titan Brain - Real-time data and calculations
echo   2. Titan Bot - Signal execution
echo.
echo [33mClose each window or press Ctrl+C to stop[0m
echo.
pause
