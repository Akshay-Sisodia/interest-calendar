@echo off
echo ===== Interest Calendar Ledger =====
echo Starting the application...
echo.

cd /d "%~dp0"

if not exist "data\storage" (
    echo Creating data directories...
    mkdir "data\storage"
)

if not exist "interest_calendars" (
    echo Creating interest calendars directory...
    mkdir "interest_calendars"
)

echo Opening application in your default browser...
echo (The command window must remain open while using the application)
echo.

if not exist "InterestCalendarLedger.exe" (
    echo ERROR: InterestCalendarLedger.exe not found!
    echo This file is required to run the application.
    echo.
    echo If you are trying to run this from the source code:
    echo 1. Run make_portable.bat first to build the executable
    echo 2. Or use 'streamlit run ledger_app_modular.py' to run directly
    echo.
    pause
    exit /b 1
)

start "" "InterestCalendarLedger.exe"

echo.
echo To close the application, press Ctrl+C in this window or close it. 