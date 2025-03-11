import os
import json
import glob
import pandas as pd
import streamlit as st
from datetime import datetime
import uuid

# File paths
INTEREST_CALENDARS_DIR = "interest_calendars"
TRANSACTIONS_FILE = "transactions.json"
CLIENTS_FILE = "clients.json"

def load_interest_calendars():
    """
    Load interest calendars from CSV files.
    Returns a dictionary with calendar data.
    """
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

def load_clients():
    """
    Load client data from JSON file.
    Returns a dictionary with a 'clients' key containing a list of client dictionaries.
    """
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

def save_clients(data):
    """Save client data to JSON file."""
    with open(CLIENTS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_transactions():
    """
    Load transaction data from JSON file.
    Returns a dictionary with a 'transactions' key containing a list of transaction dictionaries.
    """
    if os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"transactions": []}
    else:
        return {"transactions": []}

def save_transactions(data):
    """Save transaction data to JSON file."""
    with open(TRANSACTIONS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_interest_value(date_str, interest_calendars):
    """
    Get the shadow value for a specific date from the interest calendars.
    
    Args:
        date_str: Date string in format 'YYYY-MM-DD'
        interest_calendars: Dictionary containing calendar data
        
    Returns:
        tuple: (diwali_days, financial_days)
    """
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

def save_interest_calendar(calendar_df):
    """Save interest calendar data back to CSV files."""
    try:
        # Convert Shadow Value to integer
        calendar_df['Shadow Value'] = calendar_df['Shadow Value'].astype(int)
        
        # Group the dataframe by source_file
        grouped = calendar_df.groupby('source_file')
        
        # For each group, save to the corresponding file
        for source_file, group_df in grouped:
            # Create a copy of the dataframe without the source_file column
            save_df = group_df.drop(columns=['source_file']).copy()
            
            # Determine the calendar type based on the filename
            if "Financial_Year" in source_file:
                # For Financial calendar, format date as YYYY-MM-DD
                save_df['Date'] = save_df['Date'].dt.strftime('%Y-%m-%d')
            else:
                # For Diwali calendar, format date as DD-MM-YYYY
                save_df['Date'] = save_df['Date'].dt.strftime('%d-%m-%Y')
            
            # Save to file
            file_path = os.path.join(INTEREST_CALENDARS_DIR, source_file)
            save_df.to_csv(file_path, index=False)
        
        return True
    except Exception as e:
        st.error(f"Error saving calendar: {e}")
        return False
