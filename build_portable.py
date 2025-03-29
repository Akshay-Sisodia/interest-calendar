import os
import sys
import shutil
import subprocess
import platform
import argparse
from pathlib import Path
import site

def create_executable(one_file=False, console=True):
    """Create the executable using PyInstaller."""
    print("Building executable...")
    
    # Define PyInstaller command
    pyinstaller_cmd = [
        "pyinstaller",
        "--name=InterestCalendarLedger",
    ]
    
    # Add icon if it exists
    if os.path.exists("src/assets/icon.ico"):
        pyinstaller_cmd.append("--icon=src/assets/icon.ico")
    
    # Add data files with correct platform-specific separator
    separator = ";" if platform.system() == "Windows" else ":"
    pyinstaller_cmd.append(f"--add-data=src{separator}src")
    pyinstaller_cmd.append(f"--add-data=.streamlit{separator}.streamlit")
    
    # Add hidden imports needed for Streamlit
    pyinstaller_cmd.append("--hidden-import=importlib.metadata")
    pyinstaller_cmd.append("--hidden-import=importlib.resources")
    pyinstaller_cmd.append("--hidden-import=pkg_resources.py2_warn")
    pyinstaller_cmd.append("--hidden-import=streamlit")
    pyinstaller_cmd.append("--hidden-import=streamlit.runtime")
    
    # Get site-packages directory
    site_packages = site.getsitepackages()[0]
    print(f"Using site packages path: {site_packages}")
    
    # Add Streamlit package data
    streamlit_path = os.path.join(site_packages, "streamlit")
    if os.path.exists(streamlit_path):
        pyinstaller_cmd.append(f"--add-data={streamlit_path}{separator}streamlit")
    
    # Add platform-specific options for Streamlit static files
    if platform.system() == "Windows":
        # For Windows
        streamlit_static = os.path.join(site_packages, "streamlit", "runtime", "static")
        if os.path.exists(streamlit_static):
            pyinstaller_cmd.append(f"--add-binary={streamlit_static}{separator}streamlit/runtime/static")
        
        # Add site-packages directory
        pyinstaller_cmd.append(f"--add-data={site_packages}{separator}site-packages")
    else:
        # For Unix systems
        streamlit_static = os.path.join(site_packages, "streamlit", "runtime", "static")
        if os.path.exists(streamlit_static):
            pyinstaller_cmd.append(f"--add-binary={streamlit_static}{separator}streamlit/runtime/static")
        
        # Add site-packages directory
        pyinstaller_cmd.append(f"--add-data={site_packages}{separator}site-packages")
    
    # One-file or one-directory mode
    if one_file:
        pyinstaller_cmd.append("--onefile")
    else:
        pyinstaller_cmd.append("--onedir")
    
    # Console or windowed mode
    if not console:
        pyinstaller_cmd.append("--noconsole")
    
    # Add the main script
    pyinstaller_cmd.append("ledger_app_modular.py")
    
    # Run PyInstaller
    print("Running command: " + " ".join(pyinstaller_cmd))
    subprocess.run(pyinstaller_cmd)

def copy_data_directories():
    """Copy data directories to the distribution folder."""
    print("Copying data directories...")
    
    # Determine the output directory
    if os.path.exists("dist/InterestCalendarLedger"):
        # For one-directory mode
        dist_dir = "dist"
    else:
        # For one-file mode
        dist_dir = "dist"
    
    # Copy data directories
    for data_dir in ["data", "interest_calendars"]:
        src_path = data_dir
        dst_path = os.path.join(dist_dir, data_dir)
        
        # Create directory if it doesn't exist
        if not os.path.exists(dst_path):
            os.makedirs(dst_path, exist_ok=True)
        
        # Copy files
        if os.path.exists(src_path):
            if os.path.isdir(src_path):
                for item in os.listdir(src_path):
                    s = os.path.join(src_path, item)
                    d = os.path.join(dst_path, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        shutil.copy2(s, d)
            else:
                shutil.copy2(src_path, dst_path)

def create_launcher():
    """Create launcher scripts for Windows and Unix."""
    print("Creating launcher scripts...")
    
    # Windows batch file
    with open("dist/run_app.bat", "w") as f:
        f.write('@echo off\n')
        f.write('echo Starting Interest Calendar Ledger...\n')
        f.write('cd %~dp0\n')  # Change to script directory
        f.write('InterestCalendarLedger.exe\n')
        f.write('if %ERRORLEVEL% neq 0 pause\n')
    
    # Unix shell script
    with open("dist/run_app.sh", "w") as f:
        f.write('#!/bin/bash\n')
        f.write('echo "Starting Interest Calendar Ledger..."\n')
        f.write('cd "$(dirname "$0")"\n')  # Change to script directory
        f.write('./InterestCalendarLedger\n')
    
    # Make shell script executable on Unix
    if platform.system() != "Windows":
        os.chmod("dist/run_app.sh", 0o755)

def create_readme():
    """Create a README file for the portable app."""
    print("Creating README...")
    
    readme_content = """===== Interest Calendar Ledger Application =====

This is a portable application that manages interest calculations and client information.

== RUNNING THE APPLICATION ==

1. Simply double-click on "run_app.bat" (Windows) or "run_app.sh" (macOS/Linux)
2. The application will launch automatically
3. The application will open in your default web browser
   - If it doesn't open automatically, navigate to: http://localhost:8501

== REQUIREMENTS ==

- Windows 7/macOS 10.14/Linux (Ubuntu 18.04 or equivalent) or newer
- 500MB of free disk space
- No administrator privileges required
- No installation needed - just extract and run!

== TROUBLESHOOTING ==

If you encounter issues:

1. If a Windows Defender SmartScreen warning appears, click "More info" and "Run anyway"
2. The command window must remain open while the application is running
3. To close the application completely, close the command window

== DATA STORAGE ==

All your data is stored locally in the "data" and "interest_calendars" folders within this directory.
These folders must remain in the same directory as the executable.
No data is sent to external servers.

== BACKUP ==

To back up your data, simply copy the entire application folder.
"""
    
    with open("dist/README.txt", "w") as f:
        f.write(readme_content)

def main():
    """Main build function."""
    parser = argparse.ArgumentParser(description="Build portable Interest Calendar Ledger application")
    parser.add_argument("--one-file", action="store_true", help="Build as a single executable file")
    parser.add_argument("--no-console", action="store_true", help="Hide console window when running")
    args = parser.parse_args()
    
    # Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "uv", "pip", "install", "pyinstaller"])
    
    # Ensure importlib-metadata is installed
    try:
        import importlib.metadata
    except ImportError:
        print("importlib-metadata not found. Installing...")
        subprocess.run([sys.executable, "-m", "uv", "pip", "install", "importlib-metadata"])
    
    # Create the executable
    create_executable(one_file=args.one_file, console=not args.no_console)
    
    # Copy data directories to dist folder
    copy_data_directories()
    
    # Create launcher scripts
    create_launcher()
    
    # Create README
    create_readme()
    
    print("Build completed successfully!")
    print(f"The portable application is available in the 'dist' directory.")

if __name__ == "__main__":
    main() 