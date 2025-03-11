"""
Interest Calendar Ledger - Modular Version
A Streamlit application for managing interest calculations using custom calendars.
"""

import streamlit as st

# Set page configuration - this must be the first Streamlit command
st.set_page_config(
    page_title="Interest Calendar Ledger",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed",
    # Setting theme to dark
    menu_items={
        'Get Help': 'https://www.example.com/help',
        'Report a bug': 'https://www.example.com/bug',
        'About': 'Interest Calendar Ledger - A tool for managing interest calculations with custom calendars'
    }
)

import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import the main application
from src.app import main

# Run the application
if __name__ == "__main__":
    # Force dark theme with custom color scheme
    st.markdown("""
    <style>
    /* Import Geist Mono font */
    @import url('https://fonts.googleapis.com/css2?family=Geist+Mono:wght@300;400;500;600;700&display=swap');
    
    /* Apply Geist Mono font to all elements */
    html, body, [class*="css"], .stMarkdown, .stText, .stButton, .stInput, .stSelectbox, .stTable, .stDataFrame, code, pre {
        font-family: 'Geist Mono', monospace !important;
    }
    
    /* Enhanced styling for tables and dataframes */
    div[data-testid="stDataFrame"] table {
        font-family: 'Geist Mono', monospace !important;
        font-size: 1.1rem !important;
        width: 100% !important;
    }
    
    div[data-testid="stDataFrame"] th,
    div[data-testid="stDataFrame"] td {
        font-family: 'Geist Mono', monospace !important;
        font-size: 1.1rem !important;
        padding: 12px 16px !important;
    }
    
    /* Super aggressive table styling for transaction view */
    .stDataFrame > div > div > div > div > div > div > div table,
    .element-container div[data-testid="stDataFrame"] table,
    [data-testid="stVerticalBlock"] table {
        font-family: 'Geist Mono', monospace !important;
        font-size: 1.2rem !important;
    }
    
    .stDataFrame > div > div > div > div > div > div > div th,
    .stDataFrame > div > div > div > div > div > div > div td,
    .element-container div[data-testid="stDataFrame"] th,
    .element-container div[data-testid="stDataFrame"] td,
    [data-testid="stVerticalBlock"] th,
    [data-testid="stVerticalBlock"] td {
        font-family: 'Geist Mono', monospace !important;
        font-size: 1.2rem !important;
        padding: 12px 16px !important;
        line-height: 1.4 !important;
    }
    
    /* Force text based columns to use our font */
    .cell-text-container {
        font-family: 'Geist Mono', monospace !important;
        font-size: 1.2rem !important;
    }
    
    /* Data cell specific styling */
    .data-cell {
        font-family: 'Geist Mono', monospace !important;
        font-size: 1.2rem !important;
    }
    
    /* Force dark theme base */
    html, body, [class*="css"] {
        color: #e0e0e0;
        background-color: #000000;
    }
    
    /* Ensure dark theme is properly applied to all containers */
    .stApp {
        background-color: #000000;
    }
    
    /* Override any light theme elements */
    .st-emotion-cache-eczf16 {
        background-color: #000000;
    }
    
    /* Make scrollbars match the dark theme */
    ::-webkit-scrollbar {
        background-color: #000000;
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background-color: #0a0a0a;
    }
    
    ::-webkit-scrollbar-thumb {
        background-color: #232323;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    main() 