@echo off
REM Single window version - shows both Brain and Bot output in one console

echo.
echo ===================================================
echo    APEX-OMEGA TITAN: SINGLE WINDOW MODE
echo ===================================================
echo.
echo This will start both Brain and Bot in THIS window
echo You'll see output from both systems together
echo.
echo Press Ctrl+C to stop the system
echo.
pause

REM Set mode
set EXECUTION_MODE=PAPER

REM Start Bot in background
echo [32mStarting Bot in background...[0m
start /b node execution\bot.js > bot_output.log 2>&1

REM Wait a moment
timeout /t 3 /nobreak >nul

REM Start Brain in foreground (you'll see this output)
echo [32mStarting Brain (you'll see live output below)...[0m
echo.
python mainnet_orchestrator.py

REM If Brain stops, stop Bot too
taskkill /f /im node.exe 2>nul

echo.
echo [33mSystem stopped.[0m
pause
