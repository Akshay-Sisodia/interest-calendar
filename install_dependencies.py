import os
import sys
import subprocess
import platform
import tempfile

def get_python_executable():
    """Get the path to the Python executable."""
    return sys.executable

def install_uv():
    """Install the uv package manager if it's not already installed."""
    try:
        subprocess.run([sys.executable, "-m", "uv", "--version"], 
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("uv is already installed")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Installing uv package manager...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "uv"], check=True)
            print("uv installed successfully")
        except subprocess.SubprocessError as e:
            print(f"Error installing uv: {e}")
            return False
    return True

def install_dependencies():
    """Install required dependencies for the Interest Calendar Ledger."""
    print("=" * 60)
    print("Installing dependencies for Interest Calendar Ledger")
    print("=" * 60)
    print()
    
    # Get the Python executable
    python = get_python_executable()
    
    # Ensure uv is installed
    if not install_uv():
        print("Failed to install the uv package manager. Falling back to pip.")
        use_uv = False
    else:
        use_uv = True
    
    # Create a temporary requirements file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as temp:
        temp.write("streamlit-extras\n")
        temp.write("streamlit>=1.12.0\n")
        temp.write("pandas>=1.3.0\n")
        temp.write("openpyxl>=3.0.0\n")
        temp.write("plotly>=5.3.0\n")
        temp.write("altair>=4.1.0\n")
        temp.write("xlsxwriter>=3.0.0\n")
        temp_path = temp.name
    
    try:
        # Install the dependencies
        print("Installing required Python packages...")
        if use_uv:
            subprocess.run([python, "-m", "uv", "pip", "install", "-r", temp_path, "--user"], check=True)
        else:
            subprocess.run([python, "-m", "pip", "install", "-r", temp_path, "--user"], check=True)
        print("\nDependencies installation completed!")
    except subprocess.CalledProcessError as e:
        print(f"\nError installing dependencies: {e}")
        print("Please try running the script again with administrator privileges.")
        return False
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    print("\nYou can now run the Interest Calendar Ledger application.")
    return True

if __name__ == "__main__":
    install_dependencies() 