import os
import sys
import shutil
import zipfile
import subprocess
import platform
import argparse
from datetime import datetime

def ensure_uv_installed():
    """Ensure uv package manager is installed."""
    try:
        subprocess.run([sys.executable, "-m", "uv", "--version"], 
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Installing uv package manager...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "uv"], check=True)
            return True
        except subprocess.SubprocessError as e:
            print(f"Error installing uv: {e}")
            return False

def run_build():
    """Run the build_portable.py script."""
    print("Building the portable application...")
    
    # Ensure uv is installed
    ensure_uv_installed()
    
    # Run the build script
    build_cmd = [sys.executable, "build_portable.py"]
    subprocess.run(build_cmd, check=True)

def create_distribution_package():
    """Create a ZIP file containing the portable application."""
    print("Creating distribution package...")
    
    # Create a version string for the filename (YYYY-MM-DD)
    version = datetime.now().strftime("%Y-%m-%d")
    
    # Determine package name based on platform
    if platform.system() == "Windows":
        package_name = f"InterestCalendarLedger_Windows_{version}.zip"
    elif platform.system() == "Darwin":
        package_name = f"InterestCalendarLedger_MacOS_{version}.zip"
    else:
        package_name = f"InterestCalendarLedger_Linux_{version}.zip"
    
    # Create a ZIP file
    with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add files from the dist directory
        for root, dirs, files in os.walk("dist"):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, "dist")
                zipf.write(file_path, arcname)
    
    print(f"Package created: {package_name}")
    return package_name

def create_sample_data():
    """Create sample data directories if they don't exist."""
    print("Creating sample data directories...")
    
    # Create storage directory if it doesn't exist
    storage_dir = os.path.join("dist", "data", "storage")
    os.makedirs(storage_dir, exist_ok=True)
    
    # Create interest_calendars directory if it doesn't exist
    calendars_dir = os.path.join("dist", "interest_calendars")
    os.makedirs(calendars_dir, exist_ok=True)
    
    # Create sample clients.json if it doesn't exist
    clients_file = os.path.join(storage_dir, "clients.json")
    if not os.path.exists(clients_file):
        with open(clients_file, "w") as f:
            f.write('{"clients": []}')
    
    # Create sample transactions.json if it doesn't exist
    transactions_file = os.path.join(storage_dir, "transactions.json")
    if not os.path.exists(transactions_file):
        with open(transactions_file, "w") as f:
            f.write('{"transactions": []}')

def main():
    """Main packaging function."""
    parser = argparse.ArgumentParser(description="Package Interest Calendar Ledger application")
    parser.add_argument("--skip-build", action="store_true", help="Skip building the executable")
    args = parser.parse_args()
    
    # Run the build process if not skipped
    if not args.skip_build:
        run_build()
    
    # Create sample data directories and files
    create_sample_data()
    
    # Create the distribution package
    package_name = create_distribution_package()
    
    print("=" * 60)
    print(f"Packaging completed successfully!")
    print(f"Distribution package: {package_name}")
    print("=" * 60)

if __name__ == "__main__":
    main() 