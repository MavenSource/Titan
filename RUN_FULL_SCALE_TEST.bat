@echo off
title TITAN FULL-SCALE TEST SUITE
color 0E

echo.
echo ========================================================================
echo   APEX-OMEGA TITAN: FULL-SCALE SYSTEM TEST
echo ========================================================================
echo.
echo   This will run comprehensive tests on all components
echo   Test results will be saved to logs folder
echo   Expected duration: 2-3 minutes
echo.
echo ========================================================================
echo.

python full_scale_test.py

echo.
echo ========================================================================
echo   TEST COMPLETE
echo ========================================================================
echo.
echo Check the logs folder for detailed reports:
dir /b /o-d logs\full_scale_test_report_*.txt 2>nul | findstr "." >nul
if %errorlevel%==0 (
    echo.
    echo Latest report:
    for /f %%f in ('dir /b /o-d logs\full_scale_test_report_*.txt 2^>nul') do (
        echo   logs\%%f
        goto :done
    )
    :done
)

echo.
pause
