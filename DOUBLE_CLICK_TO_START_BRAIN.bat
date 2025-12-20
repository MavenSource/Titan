@echo off
title TITAN BRAIN - LIVE MAINNET SCANNING
color 0A

echo.
echo ========================================================================
echo   APEX-OMEGA TITAN: BRAIN STARTING
echo ========================================================================
echo.
echo   You will see live scanning activity below...
echo   Press Ctrl+C to stop
echo.
echo ========================================================================
echo.

set EXECUTION_MODE=PAPER
python mainnet_orchestrator.py

pause
