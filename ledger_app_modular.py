"""
Interest Calendar Ledger - Modular Version
A Streamlit application for managing interest calculations using custom calendars.
"""

import os
import sys

# Apply metadata patches for PyInstaller bundles
try:
    # We need to patch importlib.metadata before importing streamlit
    import importlib.metadata
    # Check if we're in a PyInstaller bundle
    if getattr(sys, 'frozen', False):
        # Try to handle the metadata error
        if not os.path.exists(os.path.join(sys._MEIPASS, 'importlib_metadata')):
            import fix_streamlit
            fix_streamlit.patch_metadata()
except ImportError:
    print("Warning: importlib.metadata not available")
except Exception as e:
    print(f"Warning: Error while patching metadata: {e}")

# Import streamlit after patching
import streamlit as st

# Set page configuration - this must be the first Streamlit command
st.set_page_config(
    page_title="Interest Calendar Ledger",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://www.example.com/help',
        'Report a bug': 'https://www.example.com/bug',
        'About': 'Interest Calendar Ledger - A tool for managing interest calculations with custom calendars'
    }
)

# Get the base directory for resolving paths
def get_base_dir():
    """
    Get the base directory for resolving file paths.
    When running as a PyInstaller executable, this will be the directory where the executable is located.
    When running as a script, this will be the script's directory.
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))

# Add the src directory to the Python path
base_dir = get_base_dir()
src_dir = os.path.join(base_dir, 'src')
sys.path.insert(0, src_dir)

# Import the main application
from src.app import main

# Run the application
if __name__ == "__main__":
    # Add minimal CSS for colors not covered by Streamlit theme settings
    st.markdown("""
    <style>
    /* Paragraph text color */
    p {
        color: #5f6c7b;
    }
    
    /* Tertiary color for highlights, warnings, etc */
    .streamlit-expanderContent, .stAlert, .stWarning {
        border-color: #ef4565 !important;
    }
    
    /* Button text color */
    button {
        color: #fffffe !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    main() 