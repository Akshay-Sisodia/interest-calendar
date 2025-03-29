#!/bin/bash
echo "===== Interest Calendar Ledger ====="
echo "Starting the application..."
echo

# Change to the directory where this script is located
cd "$(dirname "$0")"

# Create data directories if they don't exist
if [ ! -d "data/storage" ]; then
    echo "Creating data directories..."
    mkdir -p "data/storage"
fi

if [ ! -d "interest_calendars" ]; then
    echo "Creating interest calendars directory..."
    mkdir -p "interest_calendars"
fi

echo "Opening application in your default browser..."
echo "(The terminal window must remain open while using the application)"
echo

# Check if executable exists
if [ ! -f "InterestCalendarLedger" ] && [ ! -f "InterestCalendarLedger.exe" ]; then
    echo "ERROR: InterestCalendarLedger executable not found!"
    echo "This file is required to run the application."
    echo
    echo "If you are trying to run this from the source code:"
    echo "1. Run 'python package.py' first to build the executable"
    echo "2. Or use 'streamlit run ledger_app_modular.py' to run directly"
    echo
    read -p "Press Enter to exit..."
    exit 1
fi

# Run the executable
if [ -f "InterestCalendarLedger" ]; then
    ./InterestCalendarLedger
elif [ -f "InterestCalendarLedger.exe" ]; then
    # For Windows executable in Wine or similar environment
    ./InterestCalendarLedger.exe
fi

echo
echo "To close the application, press Ctrl+C in this window or close it." 