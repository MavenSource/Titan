@echo off
REM Quick system status checker

echo.
echo ===================================================
echo    TITAN SYSTEM STATUS CHECK
echo ===================================================
echo.

REM Check if processes are running
echo [34mChecking running processes...[0m
powershell -Command "Get-Process | Where-Object {$_.ProcessName -match 'python|node'} | Select-Object Id,ProcessName,@{Name='Runtime';Expression={(Get-Date) - $_.StartTime}} | Format-Table -AutoSize"

echo.
echo [34mChecking signal files...[0m
if exist signals\outgoing\*.json (
    echo [32mPending signals:[0m
    dir /b signals\outgoing\*.json 2>nul | find /c /v "" 
) else (
    echo [33mNo pending signals[0m
)

if exist signals\processed\*.json (
    echo [32mProcessed signals:[0m
    dir /b signals\processed\*.json 2>nul | find /c /v ""
) else (
    echo [33mNo processed signals yet[0m
)

echo.
echo [34mRecent log entries...[0m
if exist logs\deployment_report_*.txt (
    dir /b /o-d logs\deployment_report_*.txt 2>nul | findstr /r "." >nul && (
        echo [32mLatest deployment report found[0m
    )
)

echo.
pause
