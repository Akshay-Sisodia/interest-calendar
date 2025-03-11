import streamlit as st

# Set page configuration and styling
st.set_page_config(
    page_title="Interest Calendar Ledger",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import pandas as pd
from datetime import datetime, timedelta
import os
import json
import glob
import altair as alt
from streamlit_extras.colored_header import colored_header
from streamlit_extras.card import card
from streamlit_extras.metric_cards import style_metric_cards
import plotly.express as px
import plotly.graph_objects as go
import base64
from pathlib import Path

# Custom CSS styling
def load_custom_css():
    st.markdown("""
    <style>
    .main {
        background-color: #f5f7fa;
    }
    div[data-testid="stVerticalBlock"] div.element-container {margin: 0.5rem 0;}
    div.block-container {padding-top: 2rem; padding-bottom: 2rem;}
    div[data-testid="stExpander"] div.stExpanderContent {background-color: #ffffff; border-radius: 0.5rem;}
    .stTabs [data-baseweb="tab-list"] {gap: 3rem; margin-bottom: 1rem;}
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-bottom: 10px;
        padding-top: 10px;
        font-size: 16px;
    }
    div[data-testid="stForm"] {background-color: #ffffff; padding: 1.5rem; border-radius: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.05);}
    h1, h2, h3 {
        color: #1E3A8A;
    }
    .stTabs [data-baseweb="tab-panel"] {padding: 1rem 0;}
    div.stButton > button {background-color: #1E3A8A; color: white;}
    div.stButton > button:hover {background-color: #3151B7;}
    div.stButton > button:focus {box-shadow: 0 0 0 0.2rem rgba(49, 81, 183, 0.25);}
    .reportview-container .main {padding-top: 1rem;}
    </style>
    """, unsafe_allow_html=True)

# Function to convert image to base64
def img_to_base64(img_path):
    with open(img_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# File paths
INTEREST_CALENDARS_DIR = "interest_calendars"
TRANSACTIONS_FILE = "transactions.json"
CLIENTS_FILE = "clients.json"


# Function to load interest calendars
def load_interest_calendars():
    calendars = {
        'diwali': {},
        'financial': {},
        'merged_diwali': None,
        'merged_financial': None
    }
    calendar_files = glob.glob(f"{INTEREST_CALENDARS_DIR}/*.csv")
    
    if not calendar_files:
        st.warning("No interest calendars found in the interest_calendars directory.")
        return calendars
    
    for file_path in calendar_files:
        try:
            filename = os.path.basename(file_path)
            
            # Extract year range differently based on the file naming convention
            if "Financial_Year" in filename:
                year_range = filename.replace("Financial_Year_", "").replace(".csv", "")
                calendar_type = 'financial'
            else:
                year_range = filename.split('_')[0]  # Extract year range (e.g., "2023-2024")
                calendar_type = 'diwali'
            
            df = pd.read_csv(file_path)
            
            # Determine the date format based on calendar type
            if calendar_type == 'diwali':
                date_format = '%d-%m-%Y'  # DD-MM-YYYY
            else:  # financial
                date_format = '%Y-%m-%d'  # YYYY-MM-DD
            
            # Convert date strings to datetime objects using the appropriate format
            df['Date'] = pd.to_datetime(df['Date'], format=date_format)
            
            # Drop the Tithi column if it exists
            if 'Tithi' in df.columns:
                df = df.drop(columns=['Tithi'])
            
            # Add a source_file column to track which file each row came from
            df['source_file'] = filename
            calendars[calendar_type][year_range] = df
            
        except Exception as e:
            st.error(f"Error loading calendar {file_path}: {e}")
    
    # Create merged calendars for each type
    if calendars['diwali']:
        merged_diwali = pd.concat([df for df in calendars['diwali'].values()], ignore_index=True)
        calendars['merged_diwali'] = merged_diwali
    
    if calendars['financial']:
        merged_financial = pd.concat([df for df in calendars['financial'].values()], ignore_index=True)
        calendars['merged_financial'] = merged_financial
    
    return calendars


# Function to load clients
def load_clients():
    if os.path.exists(CLIENTS_FILE):
        with open(CLIENTS_FILE, "r") as f:
            try:
                data = json.load(f)
                # Initialize opening_balance if not present
                for client in data["clients"]:
                    if "opening_balance" not in client:
                        client["opening_balance"] = 0.0
                return data
            except json.JSONDecodeError:
                return {"clients": []}
    else:
        return {"clients": []}


# Function to save clients
def save_clients(data):
    with open(CLIENTS_FILE, "w") as f:
        json.dump(data, f, indent=4)


# Function to load transactions
def load_transactions():
    if os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"transactions": []}
    else:
        return {"transactions": []}


# Function to save transactions
def save_transactions(data):
    with open(TRANSACTIONS_FILE, "w") as f:
        json.dump(data, f, indent=4)


# Function to get interest value from calendar
def get_interest_value(date_str, interest_calendars):
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        year = date_obj.year
        
        # Initialize return values
        diwali_days = None
        financial_days = None
        
        # Check in Diwali calendar
        if interest_calendars['merged_diwali'] is not None:
            merged_diwali = interest_calendars['merged_diwali']
            date_match = merged_diwali[merged_diwali['Date'].dt.date == date_obj.date()]
            
            if not date_match.empty:
                diwali_days = float(date_match['Shadow Value'].iloc[0])
        
        # Check in Financial calendar
        if interest_calendars['merged_financial'] is not None:
            merged_financial = interest_calendars['merged_financial']
            date_match = merged_financial[merged_financial['Date'].dt.date == date_obj.date()]
            
            if not date_match.empty:
                financial_days = float(date_match['Shadow Value'].iloc[0])
        
        # If we didn't find values in merged calendars, try by year range
        if diwali_days is None and interest_calendars['diwali']:
            for year_range, calendar in interest_calendars['diwali'].items():
                start_year, end_year = map(int, year_range.split('-'))
                if start_year <= year <= end_year:
                    date_match = calendar[calendar['Date'].dt.date == date_obj.date()]
                    if not date_match.empty:
                        diwali_days = float(date_match['Shadow Value'].iloc[0])
                        break
        
        if financial_days is None and interest_calendars['financial']:
            for year_range, calendar in interest_calendars['financial'].items():
                start_year, end_year = map(int, year_range.split('-'))
                if start_year <= year <= end_year:
                    date_match = calendar[calendar['Date'].dt.date == date_obj.date()]
                    if not date_match.empty:
                        financial_days = float(date_match['Shadow Value'].iloc[0])
                        break
        
        return diwali_days, financial_days
    except Exception as e:
        st.error(f"Error getting shadow days value: {e}")
        return None, None


# Function to calculate interest
def calculate_interest(amount, rate, days, calendar_type="Diwali"):
    # Formula: (amount * rate * days) / (shadow value on first day of year)
    # For Diwali calendar, the first day shadow value is 360
    # For Financial calendar, the first day shadow value is 366 (or 365 for non-leap years)
    if calendar_type == "Financial":
        first_day_value = 366  # First day value for Financial calendar
    else:  # Diwali
        first_day_value = 360  # First day value for Diwali calendar
    
    # Convert rate from percentage to decimal (e.g., 5% -> 0.05)
    rate_decimal = rate / 100.0
    
    # The function will use the provided days value in the numerator
    # and the first day value (360 for Diwali, 366/365 for Financial) as the denominator
    return (amount * rate_decimal * days) / first_day_value


# Client Management Section
def client_management():
    colored_header(
        label="Client Management",
        description="Add, view and manage client information",
        color_name="blue-90"
    )
    
    # Create tabs for different client functions
    tab1, tab2 = st.tabs(["✏️ Add New Client", "📋 Client List"])
    
    with tab1:
        # Load clients data
        clients_data = load_clients()
        interest_calendars = load_interest_calendars()
        
        # Style the form container
        st.markdown("""
        <div style="background-color:#f8fafc; padding:1rem; border-radius:0.5rem; border-left:4px solid #2563EB;">
            <p style="margin:0; color:#1E3A8A;">Enter client details below. Fields marked with * are required.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Create form container
        with st.form("new_client_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_client_name = st.text_input("Client Name *")
                new_client_contact = st.text_input("Contact Number")
                
                # Opening balance section
                st.markdown("#### Opening Balance Details")
                opening_balance = st.number_input(
                    "Opening Balance (₹)", min_value=0.0, step=100.0, format="%.2f"
                )
                
                # Only show these fields if there's an opening balance
                show_balance_details = opening_balance > 0
                if show_balance_details:
                    opening_balance_date = st.date_input(
                        "Opening Balance Date", 
                        datetime.now().date(),
                        key="new_client_opening_date"
                    )
                    
                    opening_balance_interest_rate = st.number_input(
                        "Interest Rate (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=5.0,
                        step=0.25,
                    )
                    
                    opening_balance_calendar = st.selectbox(
                        "Calendar Type",
                        ["Diwali", "Financial"]
                    )
            
            with col2:
                new_client_email = st.text_input("Email")
                new_client_notes = st.text_area("Notes", key="new_client_notes", height=100)
                
                # Help info about opening balance interest
                if show_balance_details:
                    st.markdown("#### Interest Information")
                    st.markdown("""
                    <div style="background-color:#f0f9ff; padding:1rem; border-radius:0.5rem; height:135px;">
                        <p style="margin:0; font-size:0.9rem;">
                            <strong>Opening Balance Interest:</strong><br>
                            Interest will be calculated based on the opening balance, interest rate, and selected calendar.
                            This will be recorded as an initial transaction for the client.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Submit button
            submit_button = st.form_submit_button(
                "Add Client", 
                use_container_width=True,
                type="primary"
            )
            
            if submit_button:
                if not new_client_name:
                    st.error("Client name is required!")
                else:
                    # Get interest calendars for opening balance interest calculation
                    opening_balance_interest = 0.0
                    opening_balance_days = 0
                    
                    if opening_balance > 0:
                        # Get days value from appropriate calendar
                        diwali_days, financial_days = get_interest_value(
                            opening_balance_date.strftime("%Y-%m-%d"), 
                            interest_calendars
                        )
                        
                        if opening_balance_calendar == "Diwali" and diwali_days is not None:
                            opening_balance_days = int(diwali_days)
                            # Calculate interest on opening balance
                            opening_balance_interest = calculate_interest(
                                opening_balance, 
                                opening_balance_interest_rate, 
                                opening_balance_days, 
                                "Diwali"
                            )
                        elif opening_balance_calendar == "Financial" and financial_days is not None:
                            opening_balance_days = int(financial_days)
                            # Calculate interest on opening balance
                            opening_balance_interest = calculate_interest(
                                opening_balance, 
                                opening_balance_interest_rate, 
                                opening_balance_days, 
                                "Financial"
                            )
                    
                    new_client = {
                        "id": len(clients_data.get("clients", [])) + 1,
                        "name": new_client_name,
                        "contact": new_client_contact,
                        "email": new_client_email,
                        "notes": new_client_notes,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "opening_balance": float(opening_balance),
                        "opening_balance_details": {
                            "date": opening_balance_date.strftime("%Y-%m-%d") if opening_balance > 0 else "",
                            "interest_rate": float(opening_balance_interest_rate) if opening_balance > 0 else 0.0,
                            "calendar_type": opening_balance_calendar if opening_balance > 0 else "",
                            "days": opening_balance_days,
                            "interest": round(float(opening_balance_interest), 2),
                        } if opening_balance > 0 else None
                    }
                    
                    # Initialize clients list if not exists
                    if "clients" not in clients_data:
                        clients_data["clients"] = []
                    
                    clients_data["clients"].append(new_client)
                    save_clients(clients_data)
                    
                    # If there's an opening balance, add it as a transaction
                    if opening_balance > 0:
                        transactions_data = load_transactions()
                        
                        # Create an opening balance transaction
                        opening_transaction = {
                            "id": len(transactions_data.get("transactions", [])) + 1,
                            "client_id": new_client["id"],
                            "date": opening_balance_date.strftime("%Y-%m-%d"),
                            "received": float(opening_balance),
                            "paid": 0.0,
                            "interest_rate": float(opening_balance_interest_rate),
                            "calendar_type": opening_balance_calendar,
                            "days": opening_balance_days,
                            "interest": round(float(opening_balance_interest), 2),
                            "notes": "Opening Balance",
                        }
                        
                        if "transactions" not in transactions_data:
                            transactions_data["transactions"] = []
                        
                        transactions_data["transactions"].append(opening_transaction)
                        save_transactions(transactions_data)
                    
                    st.success("✅ Client added successfully!")
                    # Clear form 
                    st.rerun()
    
    with tab2:
        # Load clients data for listing
        clients_data = load_clients()
        
        if not clients_data.get("clients"):
            st.info("No clients added yet. Add your first client in the 'Add New Client' tab.")
            return
            
        # Preview client data for display
        preview_cols = ["name", "contact", "email", "opening_balance", "notes"]
        client_df = pd.DataFrame(clients_data["clients"])
        
        # Add search functionality
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            search_term = st.text_input("🔍 Search Clients", placeholder="Type to search by name, contact, or email...")
        
        with search_col2:
            sort_by = st.selectbox(
                "Sort By",
                ["Name (A-Z)", "Name (Z-A)", "Opening Balance (High-Low)", "Opening Balance (Low-High)"],
            )
        
        # Filter and sort the dataframe
        if search_term:
            mask = (
                client_df["name"].str.contains(search_term, case=False) | 
                client_df["contact"].str.contains(search_term, case=False) | 
                client_df["email"].str.contains(search_term, case=False)
            )
            client_df = client_df[mask]
        
        if sort_by == "Name (A-Z)":
            client_df = client_df.sort_values("name")
        elif sort_by == "Name (Z-A)":
            client_df = client_df.sort_values("name", ascending=False)
        elif sort_by == "Opening Balance (High-Low)":
            client_df = client_df.sort_values("opening_balance", ascending=False)
        elif sort_by == "Opening Balance (Low-High)":
            client_df = client_df.sort_values("opening_balance")
            
        if "opening_balance_details" in client_df.columns:
            # Handle the nested opening_balance_details
            opening_details = pd.json_normalize(
                client_df["opening_balance_details"].fillna({})
            )
            # Add relevant columns if they exist
            for col in ["date", "interest_rate", "calendar_type", "interest"]:
                if col in opening_details.columns:
                    client_df[f"opening_{col}"] = opening_details[col]
        
        # Show client count and summary
        st.markdown(f"""
        <div style="background-color:#f8fafc; padding:0.8rem; border-radius:0.5rem; margin-bottom:1rem;">
            <p style="margin:0;"><strong>Showing {len(client_df)} client(s)</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display client cards
        for i, row in client_df.iterrows():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <div style="background-color:#ffffff; padding:1.2rem; border-radius:0.5rem; box-shadow:0 2px 4px rgba(0,0,0,0.05); margin-bottom:1rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                        <h3 style="margin:0; color:#1E3A8A;">{row['name']}</h3>
                        <span style="background-color:#f0f9ff; color:#0369a1; padding:0.3rem 0.5rem; border-radius:1rem; font-size:0.8rem;">
                            ID: {row['id']}
                        </span>
                    </div>
                    <div style="display:flex; flex-wrap:wrap; gap:1rem; margin-bottom:0.5rem;">
                        <div style="min-width:200px;">
                            <p style="margin:0; color:#64748b; font-size:0.8rem;">Contact</p>
                            <p style="margin:0; font-weight:500;">{row['contact'] if row['contact'] else 'N/A'}</p>
                        </div>
                        <div style="min-width:200px;">
                            <p style="margin:0; color:#64748b; font-size:0.8rem;">Email</p>
                            <p style="margin:0; font-weight:500;">{row['email'] if row['email'] else 'N/A'}</p>
                        </div>
                        <div style="min-width:200px;">
                            <p style="margin:0; color:#64748b; font-size:0.8rem;">Opening Balance</p>
                            <p style="margin:0; font-weight:500; color:#{'047857' if row['opening_balance'] > 0 else '666'};">
                                ₹{row['opening_balance']:,.2f}
                            </p>
                        </div>
                    </div>
                    <p style="margin:0; color:#64748b; font-size:0.8rem;">Notes</p>
                    <p style="margin:0; font-size:0.9rem;">{row['notes'] if row['notes'] else 'No notes added.'}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Client actions and opening balance details
                if row["opening_balance"] > 0 and "opening_balance_details" in client_df.columns:
                    details = row.get("opening_balance_details", {})
                    if isinstance(details, dict) and details:
                        st.markdown(f"""
                        <div style="background-color:#f8fafc; padding:1rem; border-radius:0.5rem; margin-bottom:1rem;">
                            <h4 style="margin:0 0 0.5rem 0; font-size:0.9rem; color:#1E3A8A;">Opening Balance Details</h4>
                            <div style="display:flex; justify-content:space-between; margin-bottom:0.2rem;">
                                <span style="font-size:0.8rem; color:#64748b;">Date:</span>
                                <span style="font-size:0.8rem; font-weight:500;">{details.get('date', 'N/A')}</span>
                            </div>
                            <div style="display:flex; justify-content:space-between; margin-bottom:0.2rem;">
                                <span style="font-size:0.8rem; color:#64748b;">Interest Rate:</span>
                                <span style="font-size:0.8rem; font-weight:500;">{details.get('interest_rate', 0)}%</span>
                            </div>
                            <div style="display:flex; justify-content:space-between; margin-bottom:0.2rem;">
                                <span style="font-size:0.8rem; color:#64748b;">Calendar:</span>
                                <span style="font-size:0.8rem; font-weight:500;">{details.get('calendar_type', 'N/A')}</span>
                            </div>
                            <div style="display:flex; justify-content:space-between; margin-bottom:0.2rem;">
                                <span style="font-size:0.8rem; color:#64748b;">Interest:</span>
                                <span style="font-size:0.8rem; font-weight:500;">₹{details.get('interest', 0):,.2f}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Action buttons
                st.button(f"Edit {row['name']}", key=f"edit_client_{row['id']}")
                st.button(f"View Transactions", key=f"view_trans_{row['id']}")
        
        # Expand/collapse to show editable table view
        with st.expander("Edit All Clients"):
            # Edit the client data
            edited_df = st.data_editor(
                client_df[preview_cols],
                column_config={
                    "name": st.column_config.TextColumn("Name"),
                    "contact": st.column_config.TextColumn("Contact"),
                    "email": st.column_config.TextColumn("Email"),
                    "opening_balance": st.column_config.NumberColumn(
                        "Opening Balance (₹)",
                        format="%.2f",
                        step=100.0,
                        min_value=0.0,
                    ),
                    "notes": st.column_config.TextColumn("Notes"),
                },
                hide_index=True,
                use_container_width=True,
                num_rows="dynamic"
            )
    
            if st.button("Save Client Changes", type="primary"):
                # Preserve the fields that were not displayed in the editor
                for i, row in edited_df.iterrows():
                    if i < len(clients_data["clients"]):
                        for field in ["id", "created_at", "opening_balance_details"]:
                            if field in clients_data["clients"][i]:
                                # If opening balance changed, we need to update details and create/update transaction
                                if field == "opening_balance_details" and clients_data["clients"][i]["opening_balance"] != row["opening_balance"]:
                                    # Handle opening balance change
                                    if row["opening_balance"] > 0:
                                        # Ask for details if opening balance is increased
                                        st.warning(f"Opening balance changed for {row['name']}. Please add the client again with the new opening balance.")
                                else:
                                    # Preserve the existing field
                                    row[field] = clients_data["clients"][i][field]
                
                # Update the clients data
                clients_data["clients"] = edited_df.to_dict("records")
                save_clients(clients_data)
                st.success("✅ Client changes saved successfully!")
                st.rerun()


# Transaction Management Section for adding new transactions
def transaction_management():
    # Load data
    transactions_data = load_transactions()
    clients_data = load_clients()
    interest_calendars = load_interest_calendars()
    
    # Style the form container
    st.markdown("""
    <div style="background-color:#f8fafc; padding:1rem; border-radius:0.5rem; border-left:4px solid #2563EB;">
        <p style="margin:0; color:#1E3A8A;">Create a new transaction below. Select a client and enter the transaction details.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Get client options
    client_options = [client["name"] for client in clients_data.get("clients", [])]
    
    if not client_options:
        st.warning("⚠️ No clients available. Please add a client first in the Clients section.")
        return
    
    # Create the transaction form
    with st.form("new_transaction_form"):
        # Client selection with search
        selected_client = st.selectbox(
            "Select Client", 
            options=client_options, 
            key="transaction_client_select"
        )
        
        # Transaction details in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_date = st.date_input(
                "Transaction Date", 
                datetime.now(), 
                key="new_transaction_date",
                help="The date of the transaction"
            )
            
            transaction_type = st.selectbox(
                "Transaction Type",
                ["Received", "Paid"],
                help="Whether money was received or paid"
            )
            
            calendar_type = st.selectbox(
                "Calendar Type",
                ["Diwali", "Financial"],
                help="The calendar to use for interest calculation"
            )
        
        with col2:
            amount = st.number_input(
                "Amount (₹)",
                min_value=0.0,
                step=100.0,
                format="%.2f",
                help="Transaction amount"
            )
            
            interest_rate_pct = st.number_input(
                "Interest Rate (%)",
                min_value=0.0,
                max_value=100.0,
                value=5.0,
                step=0.25,
                help="Annual interest rate in percentage"
            )
            
            # Convert to decimal for calculations
            interest_rate = interest_rate_pct / 100.0
        
        with col3:
            notes = st.text_area(
                "Notes",
                key="new_transaction_notes",
                height=122,
                help="Optional notes about this transaction"
            )
        
        # Submit button
        submit_button = st.form_submit_button(
            "Add Transaction", 
            use_container_width=True,
            type="primary"
        )
        
        if submit_button:
            if amount <= 0:
                st.error("❌ Amount must be greater than zero.")
                return
                
            date_str = new_date.strftime("%Y-%m-%d")
            diwali_days, financial_days = get_interest_value(date_str, interest_calendars)
            
            if calendar_type == "Diwali" and diwali_days is None:
                st.error("❌ No Diwali calendar days value available for the selected date. Transaction not added.")
                return
            elif calendar_type == "Financial" and financial_days is None:
                st.error("❌ No Financial calendar days value available for the selected date. Transaction not added.")
                return
            
            # Calculate interest
            transaction_amount = amount if transaction_type == "Received" else -amount
            
            if calendar_type == "Diwali":
                interest = calculate_interest(abs(transaction_amount), interest_rate_pct, diwali_days, "Diwali")
                if transaction_type == "Paid":
                    interest = -interest
                days_value = diwali_days
            else:  # Financial
                interest = calculate_interest(abs(transaction_amount), interest_rate_pct, financial_days, "Financial")
                if transaction_type == "Paid":
                    interest = -interest
                days_value = financial_days
            
            # Find client ID
            client_id = next(
                client["id"]
                for client in clients_data["clients"]
                if client["name"] == selected_client
            )
            
            # Create transaction object
            new_transaction = {
                "id": len(transactions_data.get("transactions", [])) + 1,
                "client_id": client_id,
                "date": date_str,
                "received": float(amount) if transaction_type == "Received" else 0.0,
                "paid": float(amount) if transaction_type == "Paid" else 0.0,
                "interest_rate": float(interest_rate_pct),  # Store as percentage
                "calendar_type": calendar_type,
                "days": int(days_value) if days_value is not None else 0,  # Store as integer
                "interest": round(float(interest), 2),
                "notes": notes,
            }
            
            # Initialize transactions list if needed
            if "transactions" not in transactions_data:
                transactions_data["transactions"] = []
            
            # Add and save transaction
            transactions_data["transactions"].append(new_transaction)
            save_transactions(transactions_data)
            
            # Show success message with details
            st.success(f"""
            ✅ Transaction added successfully!
            
            **Details:**
            - Client: {selected_client}
            - Type: {transaction_type}
            - Amount: ₹{amount:,.2f}
            - Interest: ₹{interest:,.2f}
            - Calendar: {calendar_type} ({days_value} days)
            """)
            
            # Provide options to add another or view
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Add Another Transaction", key="add_another"):
                    st.rerun()
            with col2:
                if st.button("View All Transactions", key="view_all"):
                    st.session_state.action = "all_transactions"
                    st.rerun()


# Main App
def main():
    # Apply custom CSS
    load_custom_css()
    
    # Initialize session state for navigation if not already set
    if 'action' not in st.session_state:
        st.session_state.action = None
    
    # App header with logo and title
    st.markdown("""
    <div style="display:flex; align-items:center; padding:1rem 0; border-bottom:1px solid #e0e0e0; margin-bottom:1.5rem;">
        <h1 style="margin-bottom:0; flex-grow:1;">💰 Interest Calendar Ledger</h1>
        <div>
            <span style="color:#666; font-size:0.9rem;">Today: {}</span>
        </div>
    </div>
    """.format(datetime.now().strftime("%d %b, %Y")), unsafe_allow_html=True)
    
    # Recalculate all transaction interest values when the app starts
    with st.spinner("Updating calculations..."):
        recalculate_all_transaction_interest()
    
    # Handle quick action navigation from dashboard
    if st.session_state.action == "add_client":
        menu_selection = "👥 Clients"
        st.session_state.action = None  # Reset action after navigation
    elif st.session_state.action == "add_transaction":
        menu_selection = "💸 Transactions"
        # Set a sub-action to open the Add Transaction tab
        st.session_state.transaction_tab = "add"
        st.session_state.action = None  # Reset action after navigation
    elif st.session_state.action == "all_transactions":
        menu_selection = "💸 Transactions"
        # Set a sub-action to open the All Transactions tab
        st.session_state.transaction_tab = "view"
        st.session_state.action = None  # Reset action after navigation
    else:
        # Default selection if no action is specified
        menu_selection = "📊 Dashboard"
    
    # Side menu with icon buttons
    col_menu, col_content = st.columns([1, 5])
    
    with col_menu:
        st.markdown("""
        <div style="background-color:#ffffff; padding:1rem; border-radius:0.5rem; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
            <h3 style="margin-top:0; text-align:center; font-size:1rem;">Navigation</h3>
            <hr style="margin:0.5rem 0;">
        </div>
        """, unsafe_allow_html=True)
        
        menu_option = st.radio(
            "Choose a section:",
            ["📊 Dashboard", "👥 Clients", "💸 Transactions", "📅 Calendars"],
            index=["📊 Dashboard", "👥 Clients", "💸 Transactions", "📅 Calendars"].index(menu_selection),
            label_visibility="collapsed"
        )
    
    # Main content area
    with col_content:
        if menu_option == "📊 Dashboard":
            display_dashboard()
        elif menu_option == "👥 Clients":
            client_management()
        elif menu_option == "💸 Transactions":
            transactions_section()
        elif menu_option == "📅 Calendars":
            display_interest_calendars_tab()

# Dashboard overview section
def display_dashboard():
    colored_header(
        label="Dashboard Overview",
        description="Key metrics and recent activity",
        color_name="blue-90"
    )
    
    # Load data
    clients_data = load_clients()
    transactions_data = load_transactions()
    interest_calendars = load_interest_calendars()
    
    # Calculate key metrics
    total_clients = len(clients_data.get("clients", []))
    
    # Transaction metrics
    if transactions_data.get("transactions"):
        df = pd.DataFrame(transactions_data["transactions"])
        
        total_received = df["received"].sum()
        total_paid = df["paid"].sum()
        total_interest = df["interest"].sum()
        net_balance = total_received - total_paid
        
        # Create dataframe for recent transactions
        df["date"] = pd.to_datetime(df["date"])
        recent_transactions = df.sort_values("date", ascending=False).head(5)
        
        # Add client names
        client_map = {c["id"]: c["name"] for c in clients_data.get("clients", [])}
        recent_transactions["client_name"] = recent_transactions["client_id"].map(client_map)
    else:
        total_received = 0
        total_paid = 0 
        total_interest = 0
        net_balance = 0
        recent_transactions = pd.DataFrame()
    
    # Display metrics in cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="background-color:#ffffff; padding:1.5rem; border-radius:0.5rem; box-shadow:0 4px 6px rgba(0,0,0,0.05); text-align:center;">
            <h3 style="margin-top:0; font-size:1.2rem; color:#2563EB;">Total Clients</h3>
            <p style="font-size:2rem; font-weight:bold; margin:0; color:#1E3A8A;">{}</p>
        </div>
        """.format(total_clients), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background-color:#ffffff; padding:1.5rem; border-radius:0.5rem; box-shadow:0 4px 6px rgba(0,0,0,0.05); text-align:center;">
            <h3 style="margin-top:0; font-size:1.2rem; color:#2563EB;">Total Received</h3>
            <p style="font-size:2rem; font-weight:bold; margin:0; color:#047857;">₹{:,.2f}</p>
        </div>
        """.format(total_received), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background-color:#ffffff; padding:1.5rem; border-radius:0.5rem; box-shadow:0 4px 6px rgba(0,0,0,0.05); text-align:center;">
            <h3 style="margin-top:0; font-size:1.2rem; color:#2563EB;">Total Paid</h3>
            <p style="font-size:2rem; font-weight:bold; margin:0; color:#B91C1C;">₹{:,.2f}</p>
        </div>
        """.format(total_paid), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style="background-color:#ffffff; padding:1.5rem; border-radius:0.5rem; box-shadow:0 4px 6px rgba(0,0,0,0.05); text-align:center;">
            <h3 style="margin-top:0; font-size:1.2rem; color:#2563EB;">Net Balance</h3>
            <p style="font-size:2rem; font-weight:bold; margin:0; color:{};">₹{:,.2f}</p>
        </div>
        """.format("#047857" if net_balance >= 0 else "#B91C1C", net_balance), unsafe_allow_html=True)
    
    # Recent activity and quick actions
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("""
        <div style="background-color:#ffffff; padding:1.5rem; border-radius:0.5rem; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
            <h3 style="margin-top:0; font-size:1.2rem; color:#1E3A8A;">Recent Transactions</h3>
        """, unsafe_allow_html=True)
        
        if not recent_transactions.empty:
            st.dataframe(
                recent_transactions[["client_name", "date", "received", "paid", "interest", "calendar_type"]],
                column_config={
                    "client_name": "Client",
                    "date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
                    "received": st.column_config.NumberColumn("Received", format="₹%.2f"),
                    "paid": st.column_config.NumberColumn("Paid", format="₹%.2f"),
                    "interest": st.column_config.NumberColumn("Interest", format="₹%.2f"),
                    "calendar_type": "Calendar Type"
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No transactions recorded yet.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background-color:#ffffff; padding:1.5rem; border-radius:0.5rem; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
            <h3 style="margin-top:0; font-size:1.2rem; color:#1E3A8A;">Quick Actions</h3>
        """, unsafe_allow_html=True)
        
        quick_action = st.selectbox(
            "Choose an action", 
            ["Add New Client", "Add New Transaction", "View All Transactions"]
        )
        
        if st.button("Go", use_container_width=True):
            if quick_action == "Add New Client":
                st.session_state.action = "add_client"
                st.rerun()
            elif quick_action == "Add New Transaction":
                st.session_state.action = "add_transaction"
                st.rerun()
            elif quick_action == "View All Transactions":
                st.session_state.action = "all_transactions"
                st.rerun()
        
        # Interest stats
        st.markdown("<br><h3 style='font-size:1.2rem; color:#1E3A8A;'>Interest Summary</h3>", unsafe_allow_html=True)
        
        if transactions_data.get("transactions"):
            interest_fig = go.Figure()
            interest_fig.add_trace(go.Indicator(
                mode="number",
                value=total_interest,
                number={"prefix": "₹", "valueformat": ",.2f"},
                title={"text": "Total Interest Generated"},
                domain={'y': [0, 1], 'x': [0, 1]}
            ))
            st.plotly_chart(interest_fig, use_container_width=True)
        else:
            st.info("No interest data available.")
        
        st.markdown("</div>", unsafe_allow_html=True)

# Function to handle the Transactions section (combining Add Transaction and All Transactions)
def transactions_section():
    colored_header(
        label="Transaction Management",
        description="Add, view and manage all transactions",
        color_name="blue-90"
    )
    
    # Initialize transaction tab session state if not already set
    if 'transaction_tab' not in st.session_state:
        st.session_state.transaction_tab = "add"  # Default to add transaction tab
    
    # Determine which tab should be active
    tab_index = 0  # Default to first tab (Add Transaction)
    if st.session_state.transaction_tab == "view":
        tab_index = 1  # Set to second tab (All Transactions)
    
    # Create tabs for different transaction functions
    tab1, tab2 = st.tabs(["✏️ Add Transaction", "📋 All Transactions"])
    
    # Reset the transaction tab selection after this run
    current_tab = st.session_state.transaction_tab
    st.session_state.transaction_tab = "add"  # Reset to default for next time
    
    # Show the appropriate tab content based on selection
    if tab_index == 0:
        with tab1:
            transaction_management()
        with tab2:
            all_transactions_view()
    else:
        with tab2:
            all_transactions_view()
        with tab1:
            transaction_management()

# Main App section for Interest Calendars tab
def display_interest_calendars_tab():
    # Create a stylish header with an icon
    st.markdown("""
    <div style="background-color:#f0f2f6; padding:10px; border-radius:10px; margin-bottom:20px">
        <h1 style="color:#1E88E5; display:flex; align-items:center">
            <span style="margin-right:10px">📅</span> Interest Calendars Management
        </h1>
        <p style="color:#424242; font-size:16px">
            View and edit your interest calendars for Diwali and Financial Year calculations.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    interest_calendars = load_interest_calendars()
    
    if not interest_calendars:
        st.warning("No interest calendars found in the interest_calendars directory.")
        
        # Add helpful guidance for creating new calendars
        st.markdown("""
        <div style="background-color:#fff8e1; padding:15px; border-left:4px solid #ffb74d; border-radius:4px; margin-top:20px">
            <h3 style="color:#f57c00">Getting Started with Interest Calendars</h3>
            <p>Interest calendars are used to track the number of days for interest calculations based on different calendar systems:</p>
            <ul>
                <li><strong>Diwali Calendar:</strong> Based on traditional Hindu calendar used for festive calculations</li>
                <li><strong>Financial Year Calendar:</strong> Based on standard financial year (April-March)</li>
            </ul>
            <p>To create a new calendar, you need to place CSV files in the 'interest_calendars' directory with the appropriate format.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Create a nicer radio selection with custom styling
        st.markdown("<div style='background-color:white; padding:15px; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.1)'>", unsafe_allow_html=True)
        view_option = st.radio(
            "**Calendar View Options**",
            ["Combined Calendar", "Individual Calendars"],
            horizontal=True,
            help="Choose between viewing all calendars together or individual year calendars"
        )
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Display calendar information
        with st.expander("**ℹ️ About Interest Calendars**", expanded=False):
            st.markdown("""
            Interest calendars are used to determine the number of interest days for each date in the system.
            - **Diwali Calendar**: Used for traditional interest calculations based on the Hindu festival cycle
            - **Financial Calendar**: Used for interest calculations based on the standard financial year (April to March)
            
            When you edit a calendar, all transactions using that calendar type will automatically have their interest recalculated.
            """)
        
        # Create column layout for calendar stats
        col1, col2 = st.columns(2)
        
        # Calculate calendar stats
        with col1:
            diwali_years = list(interest_calendars['diwali'].keys()) if 'diwali' in interest_calendars else []
            diwali_count = len(diwali_years)
            
            st.markdown(f"""
            <div style="background-color:#e8f5e9; padding:15px; border-radius:8px; text-align:center; height:100%">
                <h3 style="color:#2e7d32">Diwali Calendars</h3>
                <h1 style="color:#2e7d32; font-size:2.5rem">{diwali_count}</h1>
                <p>{', '.join(diwali_years) if diwali_years else 'No calendars available'}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            financial_years = list(interest_calendars['financial'].keys()) if 'financial' in interest_calendars else []
            financial_count = len(financial_years)
            
            st.markdown(f"""
            <div style="background-color:#e3f2fd; padding:15px; border-radius:8px; text-align:center; height:100%">
                <h3 style="color:#1565c0">Financial Calendars</h3>
                <h1 style="color:#1565c0; font-size:2.5rem">{financial_count}</h1>
                <p>{', '.join(financial_years) if financial_years else 'No calendars available'}</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        if view_option == "Combined Calendar":
            # Create tabs for combined calendar views with custom styling
            tab_styles = """
            <style>
            .stTabs [data-baseweb="tab-list"] {
                gap: 2px;
            }
            .stTabs [data-baseweb="tab"] {
                padding: 10px 20px;
                background-color: #f5f5f5;
                border-radius: 5px 5px 0 0;
            }
            .stTabs [aria-selected="true"] {
                background-color: #1E88E5;
                color: white;
            }
            </style>
            """
            st.markdown(tab_styles, unsafe_allow_html=True)
            
            diwali_tab, financial_tab = st.tabs(["💫 Combined Diwali Calendar", "📊 Combined Financial Year Calendar"])
            
            with diwali_tab:
                # Get the merged Diwali calendar
                if interest_calendars['merged_diwali'] is not None:
                    merged_diwali = interest_calendars['merged_diwali']
                    
                    # Add description of the calendar
                    st.markdown("""
                    <div style="background-color:#f5f5f5; padding:10px; border-radius:5px; margin-bottom:15px">
                        The combined Diwali calendar shows all shadow values across all years. Edit values directly in the table below.
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Format the calendar for display (month-columns, day-rows)
                    display_matrix_diwali = format_calendar_for_display(merged_diwali)
                    
                    # Show calendar in editable format with improved styling
                    st.markdown("""
                    <h3 style="color:#1E88E5; margin-top:10px; display:flex; align-items:center">
                        <span style="margin-right:10px">📆</span> Combined Diwali Calendar
                    </h3>
                    """, unsafe_allow_html=True)
                    
                    # Add a filter for years if the matrix is large
                    available_years = sorted(set(col.split('-')[1] for col in display_matrix_diwali.columns))
                    if len(available_years) > 2:
                        selected_years = st.multiselect(
                            "Filter by Year",
                            options=available_years,
                            default=available_years,  # Default to all years
                            key="diwali_year_filter"
                        )
                        
                        if selected_years:
                            # Filter columns based on selected years
                            filtered_columns = [col for col in display_matrix_diwali.columns 
                                               if col.split('-')[1] in selected_years]
                            filtered_matrix = display_matrix_diwali[filtered_columns]
                        else:
                            filtered_matrix = display_matrix_diwali
                    else:
                        filtered_matrix = display_matrix_diwali
                    
                    edited_matrix_diwali = st.data_editor(
                        filtered_matrix,
                        use_container_width=True,
                        num_rows="dynamic",
                        disabled=False,
                        key="combined_diwali_calendar_editor",
                        column_config={col: st.column_config.NumberColumn(
                            col, 
                            help=f"Shadow value for {col}", 
                            min_value=0,
                            format="%.1f"
                        ) for col in filtered_matrix.columns}
                    )
                    
                    save_col1, save_col2 = st.columns([1, 5])
                    with save_col1:
                        save_button = st.button(
                            "💾 Save Changes", 
                            key="save_combined_diwali_btn",
                            use_container_width=True,
                            type="primary"
                        )
                    
                    if save_button:
                        with st.spinner("Saving calendar and recalculating transactions..."):
                            # Get the original data format
                            updated_df_diwali = merged_diwali.copy()
                            
                            # Update values based on the edited matrix
                            for day in edited_matrix_diwali.index:
                                for col in edited_matrix_diwali.columns:
                                    # Extract month and year from column name
                                    month_str, year_str = col.split('-')
                                    month_num = pd.to_datetime(month_str, format='%b').month
                                    year = int(year_str)
                                    
                                    value = edited_matrix_diwali.loc[day, col]
                                    if pd.notna(value):
                                        # Create the date to match
                                        match_date = pd.Timestamp(year=year, month=month_num, day=day).date()
                                        
                                        # Find any existing rows with this date
                                        mask = updated_df_diwali['Date'].dt.date == match_date
                                        
                                        if mask.any():
                                            # Update existing value
                                            updated_df_diwali.loc[mask, 'Shadow Value'] = value
                                        else:
                                            # Add new row - need to determine which file it should go to
                                            # Find the appropriate file based on the date
                                            year_key = None
                                            for key in interest_calendars['diwali'].keys():
                                                start_year, end_year = map(int, key.split('-'))
                                                if start_year <= year <= end_year:
                                                    year_key = key
                                                    break
                                            
                                            if year_key:
                                                # Get the source filename
                                                source_file = interest_calendars['diwali'][year_key]['source_file'].iloc[0]
                                                
                                                # Add new row
                                                new_row = pd.DataFrame({
                                                    'Date': [pd.Timestamp(year=year, month=month_num, day=day)],
                                                    'Shadow Value': [value],
                                                    'source_file': [source_file]
                                                })
                                                updated_df_diwali = pd.concat([updated_df_diwali, new_row], ignore_index=True)
                            
                            # Save the updated calendar
                            if save_interest_calendar(updated_df_diwali):
                                # Reload transactions and recalculate interest values
                                transactions_data = load_transactions()
                                interest_calendars = load_interest_calendars()  # Reload with updated values
                                
                                if transactions_data.get("transactions"):
                                    modified = False
                                    for transaction in transactions_data["transactions"]:
                                        if transaction["calendar_type"] == "Diwali":  # Only update Diwali transactions
                                            date_str = transaction["date"]
                                            diwali_days, _ = get_interest_value(date_str, interest_calendars)
                                            
                                            if diwali_days is not None and diwali_days != transaction["days"]:
                                                modified = True
                                                transaction["days"] = float(diwali_days)
                                                # Recalculate interest
                                                amount = (
                                                    transaction["received"] 
                                                    if transaction["received"] > 0 
                                                    else -transaction["paid"]
                                                )
                                                interest = calculate_interest(
                                                    abs(amount),
                                                    transaction["interest_rate"],
                                                    diwali_days,
                                                    "Diwali"
                                                )
                                                if amount < 0:  # For paid entries
                                                    interest = -interest
                                                transaction["interest"] = round(float(interest), 2)
                                    
                                    if modified:
                                        save_transactions(transactions_data)
                                        st.success("✅ Diwali calendar updated and relevant transactions recalculated!")
                                    else:
                                        st.success("✅ Diwali calendar updated successfully!")
                                else:
                                    st.success("✅ Diwali calendar updated successfully!")
                                
                                st.rerun()  # Refresh the page to show updated data
                else:
                    st.error("Could not create combined Diwali calendar view.")
            
            with financial_tab:
                # Get the merged Financial calendar
                if interest_calendars['merged_financial'] is not None:
                    merged_financial = interest_calendars['merged_financial']
                    
                    # Add description of the calendar
                    st.markdown("""
                    <div style="background-color:#f5f5f5; padding:10px; border-radius:5px; margin-bottom:15px">
                        The combined Financial calendar shows all shadow values across all years. Edit values directly in the table below.
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Format the calendar for display (month-columns, day-rows)
                    display_matrix_financial = format_calendar_for_display(merged_financial)
                    
                    # Show calendar in editable format with improved styling
                    st.markdown("""
                    <h3 style="color:#1565c0; margin-top:10px; display:flex; align-items:center">
                        <span style="margin-right:10px">📊</span> Combined Financial Year Calendar
                    </h3>
                    """, unsafe_allow_html=True)
                    
                    # Add a filter for years if the matrix is large
                    available_years = sorted(set(col.split('-')[1] for col in display_matrix_financial.columns))
                    if len(available_years) > 2:
                        selected_years = st.multiselect(
                            "Filter by Year",
                            options=available_years,
                            default=available_years,  # Default to all years
                            key="financial_year_filter"
                        )
                        
                        if selected_years:
                            # Filter columns based on selected years
                            filtered_columns = [col for col in display_matrix_financial.columns 
                                               if col.split('-')[1] in selected_years]
                            filtered_matrix = display_matrix_financial[filtered_columns]
                        else:
                            filtered_matrix = display_matrix_financial
                    else:
                        filtered_matrix = display_matrix_financial
                    
                    edited_matrix_financial = st.data_editor(
                        filtered_matrix,
                        use_container_width=True,
                        num_rows="dynamic",
                        disabled=False,
                        key="combined_financial_calendar_editor",
                        column_config={col: st.column_config.NumberColumn(
                            col, 
                            help=f"Shadow value for {col}", 
                            min_value=0,
                            format="%.1f"
                        ) for col in filtered_matrix.columns}
                    )
                    
                    save_col1, save_col2 = st.columns([1, 5])
                    with save_col1:
                        save_button = st.button(
                            "💾 Save Changes", 
                            key="save_combined_financial_btn",
                            use_container_width=True,
                            type="primary"
                        )
                    
                    if save_button:
                        with st.spinner("Saving calendar and recalculating transactions..."):
                            # Get the original data format
                            updated_df_financial = merged_financial.copy()
                            
                            # Update values based on the edited matrix
                            for day in edited_matrix_financial.index:
                                for col in edited_matrix_financial.columns:
                                    # Extract month and year from column name
                                    month_str, year_str = col.split('-')
                                    month_num = pd.to_datetime(month_str, format='%b').month
                                    year = int(year_str)
                                    
                                    value = edited_matrix_financial.loc[day, col]
                                    if pd.notna(value):
                                        # Create the date to match
                                        match_date = pd.Timestamp(year=year, month=month_num, day=day).date()
                                        
                                        # Find any existing rows with this date
                                        mask = updated_df_financial['Date'].dt.date == match_date
                                        
                                        if mask.any():
                                            # Update existing value
                                            updated_df_financial.loc[mask, 'Shadow Value'] = value
                                        else:
                                            # Add new row - need to determine which file it should go to
                                            # Find the appropriate file based on the date
                                            year_key = None
                                            for key in interest_calendars['financial'].keys():
                                                start_year, end_year = map(int, key.split('-'))
                                                if start_year <= year <= end_year:
                                                    year_key = key
                                                    break
                                            
                                            if year_key:
                                                # Get the source filename
                                                source_file = interest_calendars['financial'][year_key]['source_file'].iloc[0]
                                                
                                                # Add new row
                                                new_row = pd.DataFrame({
                                                    'Date': [pd.Timestamp(year=year, month=month_num, day=day)],
                                                    'Shadow Value': [value],
                                                    'source_file': [source_file]
                                                })
                                                updated_df_financial = pd.concat([updated_df_financial, new_row], ignore_index=True)
                            
                            # Save the updated calendar
                            if save_interest_calendar(updated_df_financial):
                                # Reload transactions and recalculate interest values
                                transactions_data = load_transactions()
                                interest_calendars = load_interest_calendars()  # Reload with updated values
                                
                                if transactions_data.get("transactions"):
                                    modified = False
                                    for transaction in transactions_data["transactions"]:
                                        if transaction["calendar_type"] == "Financial":  # Only update Financial transactions
                                            date_str = transaction["date"]
                                            _, financial_days = get_interest_value(date_str, interest_calendars)
                                            
                                            if financial_days is not None and financial_days != transaction["days"]:
                                                modified = True
                                                transaction["days"] = float(financial_days)
                                                # Recalculate interest
                                                amount = (
                                                    transaction["received"] 
                                                    if transaction["received"] > 0 
                                                    else -transaction["paid"]
                                                )
                                                interest = calculate_interest(
                                                    abs(amount),
                                                    transaction["interest_rate"],
                                                    financial_days,
                                                    "Financial"
                                                )
                                                if amount < 0:  # For paid entries
                                                    interest = -interest
                                                transaction["interest"] = round(float(interest), 2)
                                    
                                    if modified:
                                        save_transactions(transactions_data)
                                        st.success("✅ Financial calendar updated and relevant transactions recalculated!")
                                    else:
                                        st.success("✅ Financial calendar updated successfully!")
                                    
                                st.rerun()  # Refresh the page to show updated data
                else:
                    st.error("Could not create combined Financial calendar view.")
        
        else:  # Individual Calendars view
            # Create tabs for Diwali and Financial calendars with better styling
            diwali_tab, financial_tab = st.tabs(["💫 Diwali Calendars", "📊 Financial Year Calendars"])
            
            with diwali_tab:
                # Create a selectbox to choose which Diwali calendar to view
                diwali_options = list(interest_calendars['diwali'].keys())
                if diwali_options:
                    st.markdown("<div style='background-color:white; padding:15px; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.1)'>", unsafe_allow_html=True)
                    selected_diwali_calendar = st.selectbox(
                        "**Select Diwali Calendar Year Range**", 
                        options=diwali_options,
                        key="diwali_calendar_select"
                    )
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    if selected_diwali_calendar:
                        calendar_df = interest_calendars['diwali'][selected_diwali_calendar]
                        
                        # Format the calendar for display (month-columns, day-rows)
                        display_matrix = format_calendar_for_display(calendar_df)
                        
                        # Show calendar in editable format with improved styling
                        st.markdown(f"""
                        <h3 style="color:#2e7d32; margin-top:20px; display:flex; align-items:center">
                            <span style="margin-right:10px">📆</span> Diwali Calendar for {selected_diwali_calendar}
                        </h3>
                        <div style="background-color:#f5f5f5; padding:10px; border-radius:5px; margin-bottom:15px">
                            Edit shadow values directly in the table below. Changes will affect interest calculations for all Diwali transactions.
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Add a filter for years if the matrix is large
                        available_years = sorted(set(col.split('-')[1] for col in display_matrix.columns))
                        if len(available_years) > 1:
                            selected_years = st.multiselect(
                                "Filter by Year",
                                options=available_years,
                                default=available_years,
                                key=f"diwali_year_filter_{selected_diwali_calendar}"
                            )
                            
                            if selected_years:
                                # Filter columns based on selected years
                                filtered_columns = [col for col in display_matrix.columns 
                                                   if col.split('-')[1] in selected_years]
                                filtered_matrix = display_matrix[filtered_columns]
                            else:
                                filtered_matrix = display_matrix
                        else:
                            filtered_matrix = display_matrix
                        
                        edited_matrix = st.data_editor(
                            filtered_matrix,
                            use_container_width=True,
                            num_rows="dynamic",
                            disabled=False,
                            key=f"diwali_calendar_editor_{selected_diwali_calendar}",
                            column_config={col: st.column_config.NumberColumn(
                                col, 
                                help=f"Shadow value for {col}", 
                                min_value=0,
                                format="%.1f"
                            ) for col in filtered_matrix.columns}
                        )
                        
                        save_col1, save_col2 = st.columns([1, 5])
                        with save_col1:
                            save_button = st.button(
                                "💾 Save Changes", 
                                key=f"save_diwali_calendar_btn_{selected_diwali_calendar}",
                                use_container_width=True,
                                type="primary"
                            )
                        
                        if save_button:
                            with st.spinner("Saving calendar and recalculating transactions..."):
                                # Get the original data format
                                updated_df = calendar_df.copy()
                                
                                # Update values based on the edited matrix
                                for day in edited_matrix.index:
                                    for col in edited_matrix.columns:
                                        # Extract month and year from column name
                                        month_str, year_str = col.split('-')
                                        month_num = pd.to_datetime(month_str, format='%b').month
                                        year = int(year_str)
                                        
                                        value = edited_matrix.loc[day, col]
                                        if pd.notna(value):
                                            # Create the date to match
                                            match_date = pd.Timestamp(year=year, month=month_num, day=day).date()
                                            
                                            # Find any existing rows with this date
                                            mask = updated_df['Date'].dt.date == match_date
                                            
                                            if mask.any():
                                                # Update existing value
                                                updated_df.loc[mask, 'Shadow Value'] = value
                                            else:
                                                # Add new row
                                                new_row = pd.DataFrame({
                                                    'Date': [pd.Timestamp(year=year, month=month_num, day=day)],
                                                    'Shadow Value': [value],
                                                    'source_file': updated_df['source_file'].iloc[0]  # Use the same source file
                                                })
                                                updated_df = pd.concat([updated_df, new_row], ignore_index=True)
                                
                                # Save the updated calendar
                                if save_interest_calendar(updated_df):
                                    # Reload transactions and recalculate interest values
                                    transactions_data = load_transactions()
                                    interest_calendars = load_interest_calendars()  # Reload with updated values
                                    
                                    if transactions_data.get("transactions"):
                                        modified = False
                                        for transaction in transactions_data["transactions"]:
                                            if transaction["calendar_type"] == "Diwali":  # Only update Diwali transactions
                                                date_str = transaction["date"]
                                                diwali_days, _ = get_interest_value(date_str, interest_calendars)
                                                
                                                if diwali_days is not None and diwali_days != transaction["days"]:
                                                    modified = True
                                                    transaction["days"] = float(diwali_days)
                                                    # Recalculate interest
                                                    amount = (
                                                        transaction["received"] 
                                                        if transaction["received"] > 0 
                                                        else -transaction["paid"]
                                                    )
                                                    interest = calculate_interest(
                                                        abs(amount),
                                                        transaction["interest_rate"],
                                                        diwali_days,
                                                        "Diwali"
                                                    )
                                                    if amount < 0:  # For paid entries
                                                        interest = -interest
                                                    transaction["interest"] = round(float(interest), 2)
                                            
                                        if modified:
                                            save_transactions(transactions_data)
                                            st.success("✅ Diwali calendar updated and relevant transactions recalculated!")
                                        else:
                                            st.success("✅ Diwali calendar updated successfully!")
                                    
                                    st.rerun()  # Refresh the page to show updated data
                else:
                    st.warning("No Diwali calendars found.")
                    
                    # Add guidance for creating a new calendar
                    st.markdown("""
                    <div style="background-color:#fff8e1; padding:15px; border-left:4px solid #ffb74d; border-radius:4px; margin-top:20px">
                        <h4 style="color:#f57c00">How to Create a Diwali Calendar</h4>
                        <p>To create a new Diwali calendar:</p>
                        <ol>
                            <li>Create a CSV file with columns: <code>Date</code> (in DD-MM-YYYY format) and <code>Shadow Value</code></li>
                            <li>Name the file with pattern <code>diwali_YYYY-YYYY.csv</code></li>
                            <li>Place it in the <code>interest_calendars</code> directory</li>
                        </ol>
                    </div>
                    """, unsafe_allow_html=True)
            
            with financial_tab:
                # Create a selectbox to choose which Financial calendar to view
                financial_options = list(interest_calendars['financial'].keys())
                if financial_options:
                    st.markdown("<div style='background-color:white; padding:15px; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.1)'>", unsafe_allow_html=True)
                    selected_financial_calendar = st.selectbox(
                        "**Select Financial Calendar Year Range**", 
                        options=financial_options,
                        key="financial_calendar_select"
                    )
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    if selected_financial_calendar:
                        calendar_df = interest_calendars['financial'][selected_financial_calendar]
                        
                        # Format the calendar for display (month-columns, day-rows)
                        display_matrix = format_calendar_for_display(calendar_df)
                        
                        # Show calendar in editable format with improved styling
                        st.markdown(f"""
                        <h3 style="color:#1565c0; margin-top:20px; display:flex; align-items:center">
                            <span style="margin-right:10px">📊</span> Financial Calendar for {selected_financial_calendar}
                        </h3>
                        <div style="background-color:#f5f5f5; padding:10px; border-radius:5px; margin-bottom:15px">
                            Edit shadow values directly in the table below. Changes will affect interest calculations for all Financial transactions.
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Add a filter for years if the matrix is large
                        available_years = sorted(set(col.split('-')[1] for col in display_matrix.columns))
                        if len(available_years) > 1:
                            selected_years = st.multiselect(
                                "Filter by Year",
                                options=available_years,
                                default=available_years,
                                key=f"financial_year_filter_{selected_financial_calendar}"
                            )
                            
                            if selected_years:
                                # Filter columns based on selected years
                                filtered_columns = [col for col in display_matrix.columns 
                                                   if col.split('-')[1] in selected_years]
                                filtered_matrix = display_matrix[filtered_columns]
                            else:
                                filtered_matrix = display_matrix
                        else:
                            filtered_matrix = display_matrix
                        
                        edited_matrix = st.data_editor(
                            filtered_matrix,
                            use_container_width=True,
                            num_rows="dynamic",
                            disabled=False,
                            key=f"financial_calendar_editor_{selected_financial_calendar}",
                            column_config={col: st.column_config.NumberColumn(
                                col, 
                                help=f"Shadow value for {col}", 
                                min_value=0,
                                format="%.1f"
                            ) for col in filtered_matrix.columns}
                        )
                        
                        save_col1, save_col2 = st.columns([1, 5])
                        with save_col1:
                            save_button = st.button(
                                "💾 Save Changes", 
                                key=f"save_financial_calendar_btn_{selected_financial_calendar}",
                                use_container_width=True,
                                type="primary"
                            )
                        
                        if save_button:
                            with st.spinner("Saving calendar and recalculating transactions..."):
                                # Get the original data format
                                updated_df = calendar_df.copy()
                                
                                # Update values based on the edited matrix
                                for day in edited_matrix.index:
                                    for col in edited_matrix.columns:
                                        # Extract month and year from column name
                                        month_str, year_str = col.split('-')
                                        month_num = pd.to_datetime(month_str, format='%b').month
                                        year = int(year_str)
                                        
                                        value = edited_matrix.loc[day, col]
                                        if pd.notna(value):
                                            # Create the date to match
                                            match_date = pd.Timestamp(year=year, month=month_num, day=day).date()
                                            
                                            # Find any existing rows with this date
                                            mask = updated_df['Date'].dt.date == match_date
                                            
                                            if mask.any():
                                                # Update existing value
                                                updated_df.loc[mask, 'Shadow Value'] = value
                                            else:
                                                # Add new row
                                                new_row = pd.DataFrame({
                                                    'Date': [pd.Timestamp(year=year, month=month_num, day=day)],
                                                    'Shadow Value': [value],
                                                    'source_file': updated_df['source_file'].iloc[0]  # Use the same source file
                                                })
                                                updated_df = pd.concat([updated_df, new_row], ignore_index=True)
                                
                                # Save the updated calendar
                                if save_interest_calendar(updated_df):
                                    # Reload transactions and recalculate interest values
                                    transactions_data = load_transactions()
                                    interest_calendars = load_interest_calendars()  # Reload with updated values
                                    
                                    if transactions_data.get("transactions"):
                                        modified = False
                                        for transaction in transactions_data["transactions"]:
                                            if transaction["calendar_type"] == "Financial":  # Only update Financial transactions
                                                date_str = transaction["date"]
                                                _, financial_days = get_interest_value(date_str, interest_calendars)
                                                
                                                if financial_days is not None and financial_days != transaction["days"]:
                                                    modified = True
                                                    transaction["days"] = float(financial_days)
                                                    # Recalculate interest
                                                    amount = (
                                                        transaction["received"] 
                                                        if transaction["received"] > 0 
                                                        else -transaction["paid"]
                                                    )
                                                    interest = calculate_interest(
                                                        abs(amount),
                                                        transaction["interest_rate"],
                                                        financial_days,
                                                        "Financial"
                                                    )
                                                    if amount < 0:  # For paid entries
                                                        interest = -interest
                                                    transaction["interest"] = round(float(interest), 2)
                                        
                                        if modified:
                                            save_transactions(transactions_data)
                                            st.success("✅ Financial calendar updated and relevant transactions recalculated!")
                                        else:
                                            st.success("✅ Financial calendar updated successfully!")
                                    
                                    st.rerun()  # Refresh the page to show updated data
                else:
                    st.warning("No Financial calendars found.")
                    
                    # Add guidance for creating a new calendar
                    st.markdown("""
                    <div style="background-color:#fff8e1; padding:15px; border-left:4px solid #ffb74d; border-radius:4px; margin-top:20px">
                        <h4 style="color:#f57c00">How to Create a Financial Calendar</h4>
                        <p>To create a new Financial calendar:</p>
                        <ol>
                            <li>Create a CSV file with columns: <code>Date</code> (in YYYY-MM-DD format) and <code>Shadow Value</code></li>
                            <li>Name the file with pattern <code>financial_YYYY-YYYY.csv</code></li>
                            <li>Place it in the <code>interest_calendars</code> directory</li>
                        </ol>
                    </div>
                    """, unsafe_allow_html=True)


# Function for All Transactions tab with detailed view
def all_transactions_view():
    # Load data
    transactions_data = load_transactions()
    clients_data = load_clients()
    interest_calendars = load_interest_calendars()
    
    if not transactions_data.get("transactions"):
        st.info("💼 No transactions recorded yet. Add your first transaction in the 'Add Transaction' section.")
        return
    
    # Create DataFrame with client names
    df = pd.DataFrame(transactions_data["transactions"])
    df["date"] = pd.to_datetime(df["date"])
    
    # Add client names
    client_map = {c["id"]: c["name"] for c in clients_data.get("clients", [])}
    df["client_name"] = df["client_id"].map(client_map)
    
    # Create filter section with nice styling
    st.markdown("""
    <div style="background-color:#f8fafc; padding:1rem; border-radius:0.5rem; margin-bottom:1.5rem;">
        <h3 style="margin-top:0; margin-bottom:0.5rem; color:#1E3A8A; font-size:1.1rem;">Filter Transactions</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Advanced filters with 4 columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Multi-select for clients
        client_filter = st.multiselect(
            "Client", 
            options=sorted(df["client_name"].unique()),
            default=[],
            placeholder="All Clients"
        )
    
    with col2:
        # Calendar type filter
        calendar_filter = st.multiselect(
            "Calendar Type", 
            options=["Diwali", "Financial"],
            default=[],
            placeholder="All Calendars"
        )
    
    with col3:
        # Transaction type filter (Received/Paid)
        transaction_type_filter = st.multiselect(
            "Transaction Type", 
            options=["Received", "Paid"],
            default=[],
            placeholder="All Types"
        )
    
    with col4:
        # Amount range filter
        min_amount = st.number_input("Min Amount", value=0.0, format="%.2f")
        max_amount = st.number_input(
            "Max Amount", 
            value=float(df[["received", "paid"]].max().max() * 1.5) if not df.empty else 10000.0,
            format="%.2f"
        )
    
    # Date range filter
    date_col1, date_col2 = st.columns(2)
    with date_col1:
        start_date = st.date_input(
            "From Date", 
            min(df["date"]).date() if not df.empty else datetime.now().date() - timedelta(days=30),
            key="all_trans_start_date"
        )
    with date_col2:
        end_date = st.date_input(
            "To Date", 
            max(df["date"]).date() if not df.empty else datetime.now().date(),
            key="all_trans_end_date"
        )
    
    # Apply filters
    filtered_df = df.copy()
    
    # Client filter
    if client_filter:
        filtered_df = filtered_df[filtered_df["client_name"].isin(client_filter)]
    
    # Calendar type filter
    if calendar_filter:
        filtered_df = filtered_df[filtered_df["calendar_type"].isin(calendar_filter)]
    
    # Transaction type filter
    if transaction_type_filter:
        if "Received" in transaction_type_filter and "Paid" not in transaction_type_filter:
            filtered_df = filtered_df[filtered_df["received"] > 0]
        elif "Paid" in transaction_type_filter and "Received" not in transaction_type_filter:
            filtered_df = filtered_df[filtered_df["paid"] > 0]
    
    # Amount filter
    filtered_df = filtered_df[
        ((filtered_df["received"] >= min_amount) & (filtered_df["received"] <= max_amount)) |
        ((filtered_df["paid"] >= min_amount) & (filtered_df["paid"] <= max_amount))
    ]
    
    # Date filter
    filtered_df = filtered_df[
        (filtered_df["date"].dt.date >= start_date) & 
        (filtered_df["date"].dt.date <= end_date)
    ]
    
    # Sort by date descending (most recent first)
    filtered_df = filtered_df.sort_values("date", ascending=False)
    
    # Reorder columns to show client name first
    cols = [
        "client_name",
        "date",
        "received",
        "paid",
        "interest_rate",
        "calendar_type",
        "days",
        "interest",
        "notes",
    ]
    filtered_df = filtered_df[cols]
    
    # Summary metrics
    total_transactions = len(filtered_df)
    total_received = filtered_df["received"].sum()
    total_paid = filtered_df["paid"].sum()
    total_interest = filtered_df["interest"].sum()
    
    # Show transaction count and summary
    st.markdown(f"""
    <div style="background-color:#f0f9ff; padding:1rem; border-radius:0.5rem; margin:1.5rem 0; display:flex; justify-content:space-between;">
        <div>
            <p style="margin:0; font-size:0.9rem; color:#64748b;">Transactions</p>
            <p style="margin:0; font-weight:bold; color:#1E3A8A;">{total_transactions:,}</p>
        </div>
        <div>
            <p style="margin:0; font-size:0.9rem; color:#64748b;">Total Received</p>
            <p style="margin:0; font-weight:bold; color:#047857;">₹{total_received:,.2f}</p>
        </div>
        <div>
            <p style="margin:0; font-size:0.9rem; color:#64748b;">Total Paid</p>
            <p style="margin:0; font-weight:bold; color:#B91C1C;">₹{total_paid:,.2f}</p>
        </div>
        <div>
            <p style="margin:0; font-size:0.9rem; color:#64748b;">Total Interest</p>
            <p style="margin:0; font-weight:bold; color:#0369a1;">₹{total_interest:,.2f}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Warn if no transactions match filters
    if filtered_df.empty:
        st.warning("No transactions match the selected filters.")
        return
    
    # Display transactions in a tabbed view - List and Table
    view_tab1, view_tab2 = st.tabs(["Card View", "Table View"])
    
    with view_tab1:
        # Display transactions as cards
        for i, row in filtered_df.iterrows():
            transaction_type = "Received" if row["received"] > 0 else "Paid"
            amount = row["received"] if row["received"] > 0 else row["paid"]
            
            # Choose colors based on transaction type
            color_class = "bg-green-50 border-green-200" if transaction_type == "Received" else "bg-red-50 border-red-200"
            amount_color = "#047857" if transaction_type == "Received" else "#B91C1C"
            
            st.markdown(f"""
            <div style="background-color:{('#f0fdf4' if transaction_type == 'Received' else '#fef2f2')}; 
                       border-left:4px solid {('#047857' if transaction_type == 'Received' else '#B91C1C')}; 
                       padding:1.2rem; border-radius:0.5rem; margin-bottom:1rem;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <div style="margin-bottom:0.5rem;">
                            <span style="font-weight:bold; color:#1E3A8A; font-size:1.1rem;">{row['client_name']}</span>
                            <span style="margin-left:0.5rem; background-color:{'#dcfce7' if transaction_type == 'Received' else '#fee2e2'}; 
                                 color:{amount_color}; padding:0.2rem 0.5rem; border-radius:1rem; font-size:0.8rem;">
                                {transaction_type}
                            </span>
                        </div>
                        <div style="margin-bottom:0.5rem; color:#374151;">
                            <span style="font-weight:500; color:{amount_color};">₹{amount:,.2f}</span>
                            <span style="color:#64748b; margin-left:0.5rem; font-size:0.9rem;">
                                on {row['date'].strftime('%d %b, %Y')}
                            </span>
                        </div>
                        <div style="display:flex; gap:1.5rem; color:#64748b; font-size:0.85rem;">
                            <div>Interest Rate: <span style="font-weight:500; color:#374151;">{row['interest_rate']}%</span></div>
                            <div>Calendar: <span style="font-weight:500; color:#374151;">{row['calendar_type']}</span></div>
                            <div>Days: <span style="font-weight:500; color:#374151;">{row['days']}</span></div>
                            <div>Interest: <span style="font-weight:500; color:#374151;">₹{row['interest']:,.2f}</span></div>
                        </div>
                    </div>
                    <div style="text-align:center; min-width:4rem;">
                        <div style="font-size:0.8rem; color:#64748b;">ID</div>
                        <div style="font-weight:bold; color:#374151;">{row.get('id', i+1)}</div>
                    </div>
                </div>
                {f'<div style="margin-top:0.5rem; font-size:0.9rem; color:#64748b;"><strong>Notes:</strong> {row["notes"]}</div>' if row["notes"] else ''}
            </div>
            """, unsafe_allow_html=True)
    
    with view_tab2:
        # Show editable table view
        st.markdown("""
        <p style="color:#64748b; font-size:0.9rem; margin-bottom:0.5rem;">
            You can edit transaction details below. Click "Save Changes" when done.
        </p>
        """, unsafe_allow_html=True)
        
        # Display editable table
        edited_df = st.data_editor(
            filtered_df,
            column_config={
                "client_name": st.column_config.SelectboxColumn(
                    "Client", 
                    options=sorted(client_map.values()),
                    required=True
                ),
                "date": st.column_config.DateColumn("Date"),
                "received": st.column_config.NumberColumn(
                    "Received (₹)", format="%.2f"
                ),
                "paid": st.column_config.NumberColumn("Paid (₹)", format="%.2f"),
                "interest_rate": st.column_config.NumberColumn(
                    "Interest Rate (%)", format="%.2f", 
                    min_value=0.0, max_value=100.0,
                    help="Interest rate as percentage"
                ),
                "calendar_type": st.column_config.SelectboxColumn(
                    "Calendar Type",
                    options=["Diwali", "Financial"],
                    required=True
                ),
                "days": st.column_config.NumberColumn(
                    "Days", format="%d"
                ),
                "interest": st.column_config.NumberColumn(
                    "Interest (₹)", format="%.2f"
                ),
                "notes": st.column_config.TextColumn("Notes"),
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic"  # Allow adding new rows
        )
        
        # Calculate totals for display
        total_row = [
            {
                "client_name": "TOTAL",
                "received": edited_df["received"].sum(),
                "paid": edited_df["paid"].sum(),
                "interest": edited_df["interest"].sum(),
            }
        ]
        
        st.markdown("### Totals")
        st.dataframe(
            total_row,
            column_config={
                "client_name": st.column_config.Column("", disabled=True),
                "received": st.column_config.NumberColumn(
                    "Received (₹)", format="%.2f"
                ),
                "paid": st.column_config.NumberColumn("Paid (₹)", format="%.2f"),
                "interest": st.column_config.NumberColumn(
                    "Interest (₹)", format="%.2f"
                ),
            },
            hide_index=True,
            use_container_width=True,
        )
        
        # Save changes button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Save Changes", type="primary", use_container_width=True):
                interest_calendars = load_interest_calendars()
                
                # Update transactions with edited values
                edited_df["date"] = edited_df["date"].dt.strftime("%Y-%m-%d")
                
                # Map client names back to client_id
                reverse_client_map = {v: k for k, v in client_map.items()}
                edited_df["client_id"] = edited_df["client_name"].map(reverse_client_map)
                
                # Recalculate interest for each row
                for i, row in edited_df.iterrows():
                    # Get updated interest values
                    date_str = row["date"]
                    diwali_days, financial_days = get_interest_value(date_str, interest_calendars)
                    
                    if diwali_days is None and financial_days is None:
                        st.warning(f"No interest value available for date {date_str}. Using previous values.")
                        continue
                    
                    # Calculate interest with proper sign
                    amount = row["received"] if row["received"] > 0 else -row["paid"]
                    interest = calculate_interest(
                        abs(amount),
                        row["interest_rate"],
                        diwali_days if row["calendar_type"] == "Diwali" else financial_days,
                        row["calendar_type"]
                    )
                    if amount < 0:  # For paid entries
                        interest = -interest
                    edited_df.at[i, "interest"] = round(float(interest), 2)
                    
                    # Update days value based on selected calendar type
                    if row["calendar_type"] == "Diwali":
                        edited_df.at[i, "days"] = int(diwali_days) if diwali_days is not None else 0
                    else:
                        edited_df.at[i, "days"] = int(financial_days) if financial_days is not None else 0
                
                # Update transactions data
                new_transactions = []
                for i, row in edited_df.iterrows():
                    transaction = {
                        "id": i + 1,  # Reassign IDs based on the order
                        "client_id": int(row["client_id"]),
                        "date": row["date"],
                        "received": float(row["received"]),
                        "paid": float(row["paid"]),
                        "interest_rate": float(row["interest_rate"]),
                        "calendar_type": row["calendar_type"],
                        "days": int(row["days"]),
                        "interest": float(row["interest"]),
                        "notes": row["notes"],
                    }
                    new_transactions.append(transaction)
                
                transactions_data["transactions"] = new_transactions
                save_transactions(transactions_data)
                st.success("✅ Changes saved successfully!")
                st.rerun()
    
    # Export options
    with st.expander("Export Options"):
        export_format = st.radio(
            "Export Format",
            ["CSV", "Excel"],
            horizontal=True
        )
        
        if st.button("Export Filtered Data", use_container_width=True):
            if export_format == "CSV":
                csv = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Download CSV File",
                    csv,
                    f"transactions_export_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv",
                    key="download-csv"
                )
            else:
                # For Excel export, we'd need to use a BytesIO object
                # This is a placeholder - in a real app you'd implement Excel export
                st.info("Excel export functionality will be implemented soon.")


# Function to save interest calendar
def save_interest_calendar(calendar_df):
    try:
        # Group by source file
        grouped = calendar_df.groupby('source_file')
        
        for filename, group_df in grouped:
            # Prepare dataframe for saving
            save_df = group_df.copy()
            # Remove the source_file column
            save_df = save_df.drop(columns=['source_file'])
            
            # Determine the date format based on filename
            if 'diwali' in filename.lower():
                date_format = '%d-%m-%Y'  # DD-MM-YYYY
            else:  # financial year
                date_format = '%Y-%m-%d'  # YYYY-MM-DD
            
            # Format the Date column back to the appropriate format
            save_df['Date'] = save_df['Date'].dt.strftime(date_format)
            
            # Save the file
            file_path = os.path.join(INTEREST_CALENDARS_DIR, filename)
            save_df.to_csv(file_path, index=False)
        
        return True
    except Exception as e:
        st.error(f"Error saving calendar: {e}")
        return False


# Function to format calendar for display
def format_calendar_for_display(calendar_df):
    # Create a new dataframe with days as rows and months as columns
    calendar_matrix = pd.DataFrame()
    
    # Get unique months in the data, maintaining original order
    calendar_df['month'] = calendar_df['Date'].dt.month
    calendar_df['year'] = calendar_df['Date'].dt.year
    
    # Create a unique identifier for each month-year combination
    calendar_df['month_year'] = calendar_df['Date'].dt.strftime('%b-%Y')
    
    # Sort by date to ensure chronological order within the combined calendar
    calendar_df = calendar_df.sort_values('Date')
    
    # Get unique month-year combinations while preserving order
    unique_month_years = calendar_df['month_year'].unique()
    
    # For each unique month-year combination
    for month_year in unique_month_years:
        # Filter data for current month-year
        month_data = calendar_df[calendar_df['month_year'] == month_year]
        
        if not month_data.empty:
            # Create a series with day as index and shadow value as values
            month_series = pd.Series(
                month_data['Shadow Value'].values, 
                index=month_data['Date'].dt.day,
                name=month_year
            )
            
            # Add to the matrix
            calendar_matrix = pd.concat([calendar_matrix, month_series], axis=1)
    
    # Sort the day index
    calendar_matrix = calendar_matrix.sort_index()
    
    return calendar_matrix


# Function to recalculate all transaction interest values
def recalculate_all_transaction_interest():
    transactions_data = load_transactions()
    if not transactions_data or "transactions" not in transactions_data or not transactions_data["transactions"]:
        return
    
    modified = False
    for transaction in transactions_data["transactions"]:
        amount = transaction["received"] if transaction["received"] > 0 else -transaction["paid"]
        
        # Ensure days is stored as an integer
        if isinstance(transaction["days"], float):
            transaction["days"] = int(transaction["days"])
            modified = True
            
        days = transaction["days"]
        
        # Check if interest_rate is stored as decimal (< 1.0) and convert to percentage
        if transaction["interest_rate"] < 1.0:
            transaction["interest_rate"] = transaction["interest_rate"] * 100
            modified = True
            
        interest_rate = transaction["interest_rate"]
        calendar_type = transaction["calendar_type"]
        
        interest = calculate_interest(abs(amount), interest_rate, days, calendar_type)
        if amount < 0:  # For paid entries
            interest = -interest
        new_interest = round(float(interest), 2)
        
        if transaction["interest"] != new_interest:
            transaction["interest"] = new_interest
            modified = True
    
    if modified:
        save_transactions(transactions_data)
        st.success("All transaction interest values have been recalculated with the updated formula.")


if __name__ == "__main__":
    main()
