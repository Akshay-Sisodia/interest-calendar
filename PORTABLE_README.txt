===== Interest Calendar Ledger - Portable Application =====

This README explains how to build and use the portable version of the Interest Calendar Ledger application.

== BUILDING THE PORTABLE APP ==

To build the portable application, you have several options:

1. Automatic Build (Windows):
   - Simply double-click on "make_portable.bat"
   - This will create a virtual environment, install required packages, and build the application
   - The portable application will be in the "dist" directory and as a ZIP package

2. Manual Build (All Platforms):
   - Install Python 3.8 or newer
   - Install required packages: pip install -r requirements.txt
   - Install PyInstaller: pip install pyinstaller
   - Run the build script: python build_portable.py
   - Package the application: python package.py

== DISTRIBUTING THE APP ==

The portable app can be distributed in several ways:

1. ZIP Package:
   - The package.py script creates a ZIP file with all required files
   - This ZIP can be distributed to users
   - Users only need to extract the ZIP and run the application

2. Directory Copy:
   - You can also copy the "dist" directory to another location
   - All files in this directory are required for the application to run

== RUNNING THE PORTABLE APP ==

To run the portable application:

1. Windows:
   - Double-click on "run_app.bat"
   - The application will open in your default web browser

2. macOS/Linux:
   - Run "run_app.sh" from a terminal: ./run_app.sh
   - The application will open in your default web browser

== DATA STORAGE ==

The portable application stores all data in two directories:

1. data/ - Contains client and transaction data
2. interest_calendars/ - Contains calendar data

These directories must remain in the same location as the executable. Data is stored locally and not sent to any external servers.

== TROUBLESHOOTING ==

If you encounter issues:

1. Check that all files are in the correct directories
2. Ensure the data/storage and interest_calendars directories exist
3. The command window must remain open while the application is running
4. If the application fails to start, try running the install_dependencies.py script 