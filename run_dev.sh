#!/bin/bash
echo "===== Interest Calendar Ledger (Development Mode) ====="
echo "Starting the application from source..."
echo

# Change to the directory where this script is located
cd "$(dirname "$0")"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH."
    echo "Please install Python 3 and try again."
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if the virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    
    # Check if uv is installed
    if ! python3 -m uv --version &> /dev/null; then
        echo "Installing uv package manager..."
        python3 -m pip install uv
    fi
    
    python3 -m uv venv .venv
    source .venv/bin/activate
    
    echo "Installing dependencies..."
    python3 -m uv pip install -r requirements.txt
else
    source .venv/bin/activate
fi

echo
echo "Starting Streamlit application..."
echo "Press Ctrl+C to stop the application."
echo

streamlit run ledger_app_modular.py

# Deactivate virtual environment
deactivate 