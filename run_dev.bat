@echo off
echo ===== Interest Calendar Ledger (Development Mode) =====
echo Starting the application from source...
echo.

cd /d "%~dp0"

rem Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python and try again.
    pause
    exit /b 1
)

rem Check if the virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    
    rem Check if uv is installed
    python -m uv --version >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo Installing uv package manager...
        pip install uv
    )
    
    python -m uv venv .venv
    call .venv\Scripts\activate.bat
    
    echo Installing dependencies...
    python -m uv pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

echo.
echo Starting Streamlit application...
echo Press Ctrl+C to stop the application.
echo.

streamlit run ledger_app_modular.py

rem Deactivate virtual environment
call .venv\Scripts\deactivate.bat 