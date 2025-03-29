@echo off
echo ===== Interest Calendar Ledger - Portable Build =====
echo.

rem Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python and try again.
    exit /b 1
)

rem Check if uv is installed
python -m uv --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Installing uv package manager...
    pip install uv
)

rem Create a virtual environment
echo Creating virtual environment...
python -m uv venv build_env
call build_env\Scripts\activate.bat

rem Install required packages
echo Installing required packages...
python -m uv pip install --upgrade pip
python -m uv pip install -r requirements.txt
python -m uv pip install pyinstaller importlib-metadata

rem Ensure data directories exist
if not exist "data\storage" (
    echo Creating data storage directory...
    mkdir "data\storage"
)

if not exist "interest_calendars" (
    echo Creating interest calendars directory...
    mkdir "interest_calendars"
)

rem Run PyInstaller with spec file
echo Building portable application using spec file...
pyinstaller --clean streamlit_app.spec

rem If dist directory exists, we have a successful build
if exist dist (
    echo.
    echo Copying data directories...
    
    rem Copy data directories
    xcopy /E /I /Y data dist\InterestCalendarLedger\data
    xcopy /E /I /Y interest_calendars dist\InterestCalendarLedger\interest_calendars
    
    echo.
    echo Creating launcher scripts...
    
    rem Create launcher script
    echo @echo off > dist\InterestCalendarLedger\run_app.bat
    echo cd /d "%%~dp0" >> dist\InterestCalendarLedger\run_app.bat
    echo start "" "InterestCalendarLedger.exe" >> dist\InterestCalendarLedger\run_app.bat
    
    echo.
    echo Creating README...
    
    rem Create README
    echo ===== Interest Calendar Ledger ===== > dist\InterestCalendarLedger\README.txt
    echo. >> dist\InterestCalendarLedger\README.txt
    echo Double-click on run_app.bat to start the application. >> dist\InterestCalendarLedger\README.txt
    echo. >> dist\InterestCalendarLedger\README.txt
    echo The application will open in your default web browser. >> dist\InterestCalendarLedger\README.txt
    echo Do not close the command window while using the application. >> dist\InterestCalendarLedger\README.txt
    
    echo.
    echo Packaging the application...
    python package.py --skip-build
)

rem Deactivate the virtual environment
call build_env\Scripts\deactivate.bat

echo.
echo Build process completed.
echo The portable application is available in the dist directory and as a ZIP package.
echo. 