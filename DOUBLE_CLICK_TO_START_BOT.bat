@echo off
title TITAN BOT - SIGNAL EXECUTOR
color 0B

echo.
echo ========================================================================
echo   APEX-OMEGA TITAN: BOT STARTING
echo ========================================================================
echo.
echo   Monitoring for signals from Brain...
echo   Press Ctrl+C to stop
echo.
echo ========================================================================
echo.

set EXECUTION_MODE=PAPER
node execution\bot.js

pause
