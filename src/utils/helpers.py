import streamlit as st
import base64
import pandas as pd
from datetime import datetime

def load_custom_css():
    """Apply custom CSS styling to the Streamlit app with dark theme."""
    st.markdown("""
    <style>
    /* Import Geist Mono font */
    @import url('https://fonts.googleapis.com/css2?family=Geist+Mono:wght@300;400;500;600;700&display=swap');
    
    /* Dark theme base colors */
    :root {
        --bg-primary: #000000;
        --bg-secondary: #0a0a0a;
        --bg-tertiary: #121212;
        --accent-primary: #232323;
        --accent-secondary: #2c2c2c;
        --accent-tertiary: #363636;
        --text-primary: #e0e0e0;
        --text-secondary: #cccccc;
        --text-tertiary: #aaaaaa;
        --border-color: #1a1a1a;
        --border-gradient-1: linear-gradient(to right, rgba(255,255,255,0.1), rgba(255,255,255,0.95), rgba(255,255,255,0.1));
        --border-gradient-2: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.95), rgba(255,255,255,0.1));
        --border-gradient-blue: linear-gradient(to right, rgba(255,255,255,0.1), rgba(255,255,255,0.98), rgba(255,255,255,0.1));
        --shadow-color: rgba(0, 0, 0, 0.3);
        --success-color: #72e2ae;
        --warning-color: #ffd166;
        --error-color: #ff6b6b;
        --font-family: 'Geist Mono', monospace;
    }
    
    /* Apply Geist Mono font to all elements */
    html, body, [class*="css"], .stMarkdown, .stText, .stButton, .stInput, .stSelectbox, .stTable, .stDataFrame, code, pre {
        font-family: var(--font-family) !important;
    }
    
    /* Ensure specific Streamlit components use Geist Mono */
    .streamlit-expanderHeader, 
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div,
    .stMultiSelect > div > div > div,
    .stDateInput > div > div > input,
    .stTimeInput > div > div > input,
    .stNumberInput > div > div > input,
    .stFileUploader > div > div,
    .stWidgetLabel,
    .stRadio > div,
    .stCheckbox > div,
    .stTextArea > div > div > textarea,
    .stSlider > div,
    .stTabs > div > div > div,
    .stTab,
    .stDataFrame,
    [data-testid="stSidebar"] {
        font-family: var(--font-family) !important;
    }
    
    /* Enhanced table styling with proper font and size */
    .dataframe, 
    table,
    .stDataFrame > div,
    div[data-testid="stTable"] {
        font-family: var(--font-family) !important;
        font-size: 1rem !important;
    }
    
    /* Target table cells for better readability */
    .dataframe td, 
    .dataframe th,
    table td, 
    table th,
    div[data-testid="stTable"] td,
    div[data-testid="stTable"] th {
        font-family: var(--font-family) !important;
        font-size: 1rem !important;
        padding: 0.5rem 0.75rem !important;
        white-space: nowrap !important;
    }
    
    /* Ensure header cells use the font */
    .dataframe thead th,
    table thead th,
    div[data-testid="stTable"] thead th {
        font-family: var(--font-family) !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        background-color: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
    }
    
    /* Streamlit's native DataFrame stylings */
    div[data-testid="stDataFrame"] {
        font-family: var(--font-family) !important;
    }
    
    div[data-testid="stDataFrame"] th,
    div[data-testid="stDataFrame"] td {
        font-family: var(--font-family) !important;
        font-size: 1rem !important;
    }
    
    /* Fix column headers in DataFrames */
    .stDataFrame [data-testid="column"] {
        font-family: var(--font-family) !important;
        font-size: 1rem !important;
    }
    
    /* Fix for table container sizing */
    .stDataFrame > div:first-child,
    div[data-testid="stTable"] > div:first-child {
        width: 100% !important;
        max-width: 100% !important;
    }
    
    /* Fix for ReactTable which Streamlit uses */
    .ReactTable {
        font-family: var(--font-family) !important;
        font-size: 1.2rem !important;
    }
    
    .ReactTable .rt-th,
    .ReactTable .rt-td {
        font-family: var(--font-family) !important;
        font-size: 1.2rem !important;
        padding: 12px 16px !important;
        line-height: 1.4 !important;
    }
    
    /* Transaction view specific table styling */
    div[data-testid="stDataFrame"] > div > div > div > div {
        font-family: var(--font-family) !important;
    }
    
    /* Target the actual table cells */
    div[data-testid="stDataFrame"] div[role="row"] div[role="cell"],
    div[data-testid="stDataFrame"] div[role="columnheader"] {
        font-family: var(--font-family) !important;
        font-size: 1.2rem !important;
        padding: 12px 16px !important;
    }
    
    /* Target the cell contents */
    div[data-testid="stDataFrame"] div[role="cell"] > div,
    div[data-testid="stDataFrame"] div[role="columnheader"] > div {
        font-family: var(--font-family) !important;
        font-size: 1.2rem !important;
    }
    
    /* Force the font on the specific text elements */
    .css-36z8fk, .css-10oheav, .css-ue6h4q, .css-1p0wxre {
        font-family: var(--font-family) !important;
        font-size: 1.2rem !important;
    }
    
    /* Style for plotly charts, matplotlib plots and altair visualizations */
    .js-plotly-plot, .plotly-graph-div, canvas {
        font-family: var(--font-family) !important;
    }
    
    /* Any SVG text elements */
    svg text, g text {
        font-family: var(--font-family) !important;
    }
    
    /* Headers, inputs, form elements */
    h1, h2, h3, h4, h5, h6, p, input, button, select, textarea, label {
        font-family: var(--font-family) !important;
    }
    
    /* Global styles */
    .main {
        background-color: var(--bg-primary);
        color: var(--text-primary);
    }
    
    /* Spacing and container styling */
    div[data-testid="stVerticalBlock"] div.element-container {margin: 0.6rem 0;}
    div.block-container {padding-top: 2rem; padding-bottom: 2rem;}
    
    /* Card and panel styling with enhanced borders */
    div[data-testid="stExpander"] {
        border: none;
        border-radius: 0.6rem;
        position: relative;
        overflow: hidden;
        margin-bottom: 1rem;
        box-shadow: 0 4px 8px var(--shadow-color);
        background-color: var(--bg-secondary);
    }
    
    div[data-testid="stExpander"]::before {
        content: "";
        position: absolute;
        inset: 0;
        border-radius: 0.6rem;
        padding: 1px;
        background: var(--border-gradient-1);
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor;
        mask-composite: exclude;
        pointer-events: none;
    }
    
    div[data-testid="stExpander"] div.stExpanderContent {
        background-color: var(--bg-secondary);
        border-radius: 0 0 0.6rem 0.6rem;
        border-top: 1px solid var(--border-color);
        padding: 1.2rem;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        margin-bottom: 1rem;
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        border-radius: 0.5rem 0.5rem 0 0;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        font-size: 1rem;
        color: var(--text-secondary);
        transition: all 0.2s ease;
        font-weight: 500;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--accent-tertiary);
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: var(--text-primary);
        border-bottom: 3px solid #6e7681; /* gray-40 color */
    }
    
    .stTabs [data-baseweb="tab-panel"] {
        padding: 1rem;
        background-color: var(--bg-secondary);
        border-radius: 0 0 0.6rem 0.6rem;
        border: 1px solid var(--border-color);
        border-top: none;
    }
    
    /* Form styling with gradient borders */
    div[data-testid="stForm"] {
        background-color: var(--bg-secondary);
        padding: 1.5rem;
        border-radius: 0.8rem;
        position: relative;
        box-shadow: 0 8px 16px var(--shadow-color);
    }
    
    div[data-testid="stForm"]::before {
        content: "";
        position: absolute;
        inset: 0;
        border-radius: 0.8rem;
        padding: 1px;
        background: var(--border-gradient-2);
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor;
        mask-composite: exclude;
        pointer-events: none;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: var(--text-primary);
        font-weight: 600;
    }
    
    h1 {
        font-size: 2.2rem;
        margin-bottom: 1.2rem;
    }
    
    h2 {
        font-size: 1.8rem;
        margin-bottom: 1rem;
    }
    
    h3 {
        font-size: 1.4rem;
        margin-bottom: 0.8rem;
    }
    
    /* Text styling */
    p {
        color: var(--text-primary);
        line-height: 1.6;
        margin-bottom: 1rem;
    }
    
    a {
        color: var(--text-secondary);
        text-decoration: none;
        transition: all 0.2s ease;
    }
    
    a:hover {
        color: var(--text-primary);
        text-decoration: underline;
    }
    
    /* Button styling */
    div.stButton > button {
        background-color: var(--accent-primary);
        color: #ffffff;
        border: none;
        border-radius: 0.5rem;
        padding: 0.6rem 1.2rem;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px var(--shadow-color);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.9rem;
    }
    
    div.stButton > button:hover {
        background-color: var(--accent-secondary);
        transform: translateY(-2px);
        box-shadow: 0 6px 12px var(--shadow-color);
    }
    
    div.stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px var(--shadow-color);
    }
    
    div.stButton > button:focus {
        box-shadow: 0 0 0 0.2rem rgba(35, 35, 35, 0.3);
    }
    
    /* Text inputs */
    div[data-baseweb="input"] {
        background-color: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 0.5rem;
        transition: all 0.2s ease;
        box-shadow: 0 2px 5px var(--shadow-color);
    }
    
    div[data-baseweb="input"]:focus-within {
        border-color: var(--accent-primary);
        box-shadow: 0 0 0 0.2rem rgba(35, 35, 35, 0.2);
    }
    
    div[data-baseweb="input"] input {
        color: var(--text-primary);
    }
    
    /* Number inputs */
    div[data-testid="stNumberInput"] div, div[data-testid="stNumberInput"] input {
        background-color: var(--bg-tertiary);
        color: var(--text-primary);
        border-color: var(--border-color);
    }
    
    div[data-testid="stNumberInput"] div:hover, div[data-testid="stNumberInput"] input:hover {
        border-color: var(--accent-primary);
    }
    
    /* Modern table styling */
    [data-testid="stDataFrame"] table, [data-testid="stDataEditor"] table {
        border-collapse: separate !important;
        border-spacing: 0 !important;
        border-radius: 0.8rem !important;
        overflow: hidden !important;
        box-shadow: 0 4px 12px var(--shadow-color) !important;
        background-color: var(--bg-secondary) !important;
        margin-bottom: 1.5rem !important;
    }
    
    [data-testid="stDataFrame"] thead tr th, [data-testid="stDataEditor"] thead tr th {
        background-color: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        text-align: center !important;
        padding: 1rem 0.8rem !important;
        border-top: none !important;
        border-bottom: 2px solid var(--border-color) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        font-size: 0.9rem !important;
    }
    
    [data-testid="stDataFrame"] tbody tr:nth-child(odd), [data-testid="stDataEditor"] tbody tr:nth-child(odd) {
        background-color: var(--bg-secondary) !important;
    }
    
    [data-testid="stDataFrame"] tbody tr:nth-child(even), [data-testid="stDataEditor"] tbody tr:nth-child(even) {
        background-color: rgba(15, 15, 15, 0.6) !important;
    }
    
    [data-testid="stDataFrame"] tbody tr:hover, [data-testid="stDataEditor"] tbody tr:hover {
        background-color: rgba(35, 35, 35, 0.1) !important;
    }
    
    [data-testid="stDataFrame"] tbody tr td, [data-testid="stDataEditor"] tbody tr td {
        padding: 0.8rem !important;
        text-align: center !important;
        border-bottom: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
        font-size: 0.95rem !important;
    }
    
    /* Input styling for data editors */
    [data-testid="stDataEditor"] tbody tr td[data-testid="cell"] input,
    [data-testid="stDataEditor"] tbody tr td[data-testid="cell"] div[data-testid="stNumberInput"] input {
        background-color: transparent !important;
        border: 1px solid transparent !important;
        transition: all 0.2s ease !important;
        text-align: center !important;
        font-weight: 500 !important;
        color: var(--text-primary) !important;
    }
    
    [data-testid="stDataEditor"] tbody tr td[data-testid="cell"] input:focus,
    [data-testid="stDataEditor"] tbody tr td[data-testid="cell"] div[data-testid="stNumberInput"] input:focus {
        background-color: rgba(35, 35, 35, 0.1) !important;
        border: 1px solid var(--accent-primary) !important;
        box-shadow: 0 0 0 2px rgba(35, 35, 35, 0.2) !important;
    }
    
    /* Selectbox styling */
    div[data-baseweb="select"] {
        background-color: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 0.5rem;
        transition: all 0.2s ease;
    }
    
    div[data-baseweb="select"]:focus-within {
        border-color: var(--accent-primary);
        box-shadow: 0 0 0 0.2rem rgba(35, 35, 35, 0.2);
    }
    
    div[data-baseweb="select"] div[data-baseweb="value"] {
        color: var(--text-primary);
    }
    
    div[data-baseweb="menu"] {
        background-color: var(--bg-tertiary) !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: 0 8px 16px var(--shadow-color) !important;
    }
    
    div[data-baseweb="menu"] ul li {
        color: var(--text-primary) !important;
    }
    
    div[data-baseweb="menu"] ul li:hover {
        background-color: rgba(35, 35, 35, 0.1) !important;
    }
    
    /* Dashboard card styling with gradient borders */
    .dashboard-card {
        background-color: var(--bg-secondary);
        border-radius: 0.8rem;
        padding: 1.5rem;
        box-shadow: 0 8px 16px var(--shadow-color);
        transition: all 0.3s ease;
        height: 100%;
        position: relative;
    }
    
    .dashboard-card::before {
        content: "";
        position: absolute;
        inset: 0;
        border-radius: 0.8rem;
        padding: 1px;
        background: var(--border-gradient-1);
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor;
        mask-composite: exclude;
        pointer-events: none;
        transition: all 0.3s ease;
    }
    
    .dashboard-card:hover::before {
        background: var(--border-gradient-blue);
        padding: 1.5px;
    }
    
    .dashboard-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 20px rgba(0,0,0,0.25);
    }
    
    .dashboard-card h3 {
        color: var(--text-primary);
        font-size: 1.3rem;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    
    .dashboard-card p.metric {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 1rem 0;
    }
    
    .dashboard-card p.label {
        color: var(--text-tertiary);
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    
    /* Slider styling */
    div[data-testid="stSlider"] {
        padding: 1.2rem 0;
    }
    
    div[data-testid="stSlider"] div[data-baseweb="slider"] div {
        background-color: var(--border-color);
    }
    
    div[data-testid="stSlider"] div[data-baseweb="slider"] div[data-testid="stThumbValue"] {
        background-color: var(--accent-primary);
    }
    
    /* Date input styling */
    div[data-testid="stDateInput"] div[data-baseweb="input"] {
        background-color: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 0.5rem;
    }
    
    div[data-testid="stDateInput"] div[data-baseweb="input"]:focus-within {
        border-color: var(--accent-primary);
        box-shadow: 0 0 0 0.2rem rgba(35, 35, 35, 0.2);
    }
    
    div[data-testid="stDateInput"] input {
        color: var(--text-primary);
    }
    
    /* Radio button & checkbox styling */
    div[data-testid="stRadio"] label span span:first-child,
    div[data-testid="stCheckbox"] label span span:first-child {
        background-color: var(--bg-tertiary) !important;
        border-color: var(--border-color) !important;
    }
    
    div[data-testid="stRadio"] label:hover span span:first-child,
    div[data-testid="stCheckbox"] label:hover span span:first-child {
        border-color: var(--accent-secondary) !important;
    }
    
    div[data-testid="stRadio"] label span span:first-child span,
    div[data-testid="stCheckbox"] label span span:first-child span {
        background-color: var(--accent-primary) !important;
    }
    
    /* Spinner & progress bar */
    div.stProgress div {
        background-color: var(--accent-primary);
    }
    
    .stSpinner > div > div {
        border-top-color: var(--accent-primary) !important;
    }
    
    /* Metric styling */
    div[data-testid="stMetric"] {
        background-color: var(--bg-secondary);
        border-radius: 0.7rem;
        padding: 1rem;
        border: 1px solid var(--border-color);
        box-shadow: 0 4px 8px var(--shadow-color);
        transition: all 0.2s ease;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px var(--shadow-color);
        border-color: var(--accent-secondary);
    }
    
    div[data-testid="stMetric"] label {
        color: var(--text-tertiary);
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--text-primary);
    }
    
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"] {
        color: var(--success-color);
    }
    
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"][data-direction="down"] {
        color: var(--error-color);
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-secondary);
        border-right: 1px solid var(--border-color);
    }
    
    section[data-testid="stSidebar"] > div {
        padding: 2rem 1rem;
    }
    
    section[data-testid="stSidebar"] hr {
        margin: 1rem 0;
        border-color: var(--border-color);
    }
    
    /* Tooltip styling */
    div[data-baseweb="tooltip"] {
        background-color: var(--bg-tertiary) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
        box-shadow: 0 4px 8px var(--shadow-color) !important;
    }
    
    /* Status indicator colors */
    .status-success {
        color: var(--success-color) !important;
    }
    
    .status-warning {
        color: var(--warning-color) !important;
    }
    
    .status-error {
        color: var(--error-color) !important;
    }
    </style>
    """, unsafe_allow_html=True)

def img_to_base64(img_path):
    """Convert an image file to base64 encoding."""
    with open(img_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def format_calendar_for_display(calendar_df):
    """
    Create a new dataframe with days as rows and months as columns.
    This formats the calendar data for display in the UI.
    """
    # Create a new dataframe with days as rows and months as columns
    days = sorted(set(calendar_df['Date'].dt.day))
    
    # Create a matrix with days as rows and month-year as columns
    matrix = pd.DataFrame(index=days)
    
    # Group by month and year
    for (year, month), group in calendar_df.groupby([calendar_df['Date'].dt.year, calendar_df['Date'].dt.month]):
        month_name = pd.Timestamp(year=year, month=month, day=1).strftime('%b')
        col_name = f"{month_name}-{year}"
        
        # Create a series with day as index and shadow value as values
        day_values = group.set_index(group['Date'].dt.day)['Shadow Value']
        
        # Add to the matrix
        matrix[col_name] = day_values
    
    # Sort columns by date to ensure chronological order
    month_order = {month: i for i, month in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])}
    
    # Sort columns by year and month
    sorted_columns = sorted(matrix.columns, key=lambda x: (int(x.split('-')[1]), month_order[x.split('-')[0]]))
    matrix = matrix[sorted_columns]
    
    return matrix

def calculate_interest(amount, rate, days, calendar_type="Diwali"):
    """
    Calculate interest based on the formula:
    (amount * rate * days) / (shadow value on first day of year)
    
    For Diwali calendar, the first day shadow value is 360
    For Financial calendar, the first day shadow value is 366 (or 365 for non-leap years)
    """
    if calendar_type == "Diwali":
        base_value = 360
    else:  # Financial
        # Check if it's a leap year
        current_year = datetime.now().year
        if (current_year % 4 == 0 and current_year % 100 != 0) or (current_year % 400 == 0):
            base_value = 366
        else:
            base_value = 365
    
    interest = (amount * rate * days) / base_value
    return interest

def sanitize_html(html_content, is_html=False):
    """
    Sanitizes HTML content to either:
    1. Properly escape it to display as raw text (when is_html=False)
    2. Ensure it's properly formatted to be rendered (when is_html=True)
    
    Args:
        html_content (str): The HTML content to sanitize
        is_html (bool): Whether the content should be treated as HTML to be rendered
        
    Returns:
        str: The sanitized content
    """
    if not html_content:
        return ""
    
    import re
    from html import escape
    
    if not is_html:
        # Escape HTML to display as text
        return escape(html_content)
    else:
        # Clean up HTML to be properly rendered
        # Remove excess whitespace and newlines between tags
        html_content = re.sub(r'>\s+<', '><', html_content.strip())
        return html_content

def num_to_words_rupees(number):
    """
    Convert a number to words in Indian currency format (Rupees).
    
    Args:
        number (float): The amount to convert to words
        
    Returns:
        str: The amount in words with "Rupees" and "Paise" labels
    """
    def get_words(n):
        units = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 
                'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
        tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
        
        if n < 20:
            return units[n]
        elif n < 100:
            return tens[n // 10] + (' ' + units[n % 10] if n % 10 != 0 else '')
        elif n < 1000:
            return units[n // 100] + ' Hundred' + (' and ' + get_words(n % 100) if n % 100 != 0 else '')
        elif n < 100000:
            return get_words(n // 1000) + ' Thousand' + (' ' + get_words(n % 1000) if n % 1000 != 0 else '')
        elif n < 10000000:
            return get_words(n // 100000) + ' Lakh' + (' ' + get_words(n % 100000) if n % 100000 != 0 else '')
        else:
            return get_words(n // 10000000) + ' Crore' + (' ' + get_words(n % 10000000) if n % 10000000 != 0 else '')
    
    # Handle negative numbers
    if number < 0:
        return "Minus " + num_to_words_rupees(abs(number))
    
    # Split the number into rupees and paise
    rupees = int(number)
    paise = int(round((number - rupees) * 100))
    
    rupees_text = get_words(rupees) + " Rupees" if rupees > 0 else ""
    paise_text = get_words(paise) + " Paise" if paise > 0 else ""
    
    # Combine rupees and paise
    if rupees > 0 and paise > 0:
        return f"{rupees_text} and {paise_text} Only"
    elif rupees > 0:
        return f"{rupees_text} Only"
    elif paise > 0:
        return f"{paise_text} Only"
    else:
        return "Zero Rupees Only"

def render_html_safely(html_content):
    """
    Renders HTML content safely in Streamlit.
    This function creates a special HTML container that forces Streamlit to render
    HTML content properly without escaping it.
    
    Args:
        html_content (str): The HTML content to render
        
    Returns:
        str: HTML that will render correctly in Streamlit
    """
    # If the content is empty, return empty string
    if not html_content:
        return ""
    
    # Convert to string if not already
    html_str = str(html_content).strip()
    
    # Create an iframe-based approach that forces correct rendering
    iframe_html = f"""
    <iframe srcdoc='
    <!DOCTYPE html>
    <html>
    <head>
        <style>
        @import url("https://fonts.googleapis.com/css2?family=Geist+Mono:wght@300;400;500;600;700&display=swap");
        body, p, div, span, h1, h2, h3, h4, h5, h6, table, tr, td, th, ul, ol, li, a, button, input, select, textarea {{
            font-family: "Geist Mono", monospace !important;
        }}
        body {{
            color: #e0e0e0;
            background-color: transparent;
            margin: 0;
            padding: 0;
        }}
        
        /* Table styling */
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 1.2rem !important;
        }}
        
        th, td {{
            padding: 12px 16px;
            text-align: left;
            font-size: 1.2rem !important;
            line-height: 1.4;
        }}
        
        th {{
            font-weight: 600;
            background-color: #121212;
        }}
        </style>
    </head>
    <body>
        {html_str}
    </body>
    </html>'
    style="width:100%; border:none; overflow:hidden; background:transparent;"
    onload="this.style.height=this.contentDocument.body.scrollHeight + 'px'">
    </iframe>
    """
    
    return iframe_html
