@echo off
echo ===== Interest Calendar Ledger - Direct Build =====
echo.

rem Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.8+ and try again.
    pause
    exit /b 1
)

rem Install all required packages globally
echo Installing required packages...
python -m pip install --upgrade pip
python -m pip install streamlit==1.31.0 streamlit-extras==0.3.6 pyinstaller==6.3.0 importlib-metadata pandas plotly altair openpyxl xlsxwriter

rem Ensure data directories exist
if not exist "data\storage" (
    echo Creating data storage directory...
    mkdir "data\storage"
)

if not exist "interest_calendars" (
    echo Creating interest calendars directory...
    mkdir "interest_calendars"
)

rem Clean existing builds
if exist "dist" (
    echo Cleaning previous builds...
    rmdir /S /Q dist
)
if exist "build" (
    echo Cleaning build directory...
    rmdir /S /Q build
)

rem Run PyInstaller with spec file
echo Building portable application...
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
    echo Creating ZIP package...
    
    rem Create a ZIP file with the date
    for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
    powershell -command "Compress-Archive -Path 'dist\InterestCalendarLedger' -DestinationPath 'InterestCalendarLedger_Windows_%mydate%.zip' -Force"
)

echo.
echo Build process completed.
echo The portable application is available in the dist directory and as a ZIP package.
echo.
pause 