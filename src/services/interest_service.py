from datetime import datetime
import pandas as pd
import streamlit as st

class InterestService:
    """Service for interest-related calculations and operations."""
    
    def __init__(self, interest_calendars=None):
        """Initialize with interest calendars data."""
        self.interest_calendars = interest_calendars or {}
    
    def get_interest_value(self, date_str):
        """Get interest value from calendar for a specific date."""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            year = date_obj.year
            
            # Initialize return values
            diwali_days = None
            financial_days = None
            
            # Check in Diwali calendar
            if self.interest_calendars['merged_diwali'] is not None:
                merged_diwali = self.interest_calendars['merged_diwali']
                date_match = merged_diwali[merged_diwali['Date'].dt.date == date_obj.date()]
                
                if not date_match.empty:
                    diwali_days = float(date_match['Shadow Value'].iloc[0])
            
            # Check in Financial calendar
            if self.interest_calendars['merged_financial'] is not None:
                merged_financial = self.interest_calendars['merged_financial']
                date_match = merged_financial[merged_financial['Date'].dt.date == date_obj.date()]
                
                if not date_match.empty:
                    financial_days = float(date_match['Shadow Value'].iloc[0])
            
            # If we didn't find values in merged calendars, try by year range
            if diwali_days is None and self.interest_calendars['diwali']:
                for year_range, calendar in self.interest_calendars['diwali'].items():
                    start_year, end_year = map(int, year_range.split('-'))
                    if start_year <= year <= end_year:
                        date_match = calendar[calendar['Date'].dt.date == date_obj.date()]
                        if not date_match.empty:
                            diwali_days = float(date_match['Shadow Value'].iloc[0])
                            break
            
            if financial_days is None and self.interest_calendars['financial']:
                for year_range, calendar in self.interest_calendars['financial'].items():
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
    
    def calculate_interest(self, amount, rate, days, calendar_type="Diwali"):
        """Calculate interest based on amount, rate, days and calendar type."""
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
    
    def recalculate_all_transaction_interest(self, transactions_data):
        """Recalculate interest for all transactions."""
        if not transactions_data.get("transactions"):
            return transactions_data
        
        for transaction in transactions_data["transactions"]:
            date_str = transaction["date"]
            diwali_days, financial_days = self.get_interest_value(date_str)
            
            if transaction["calendar_type"] == "Diwali" and diwali_days is not None:
                transaction["days"] = float(diwali_days)
                # Recalculate interest
                amount = transaction["received"] if transaction["received"] > 0 else -transaction["paid"]
                interest = self.calculate_interest(
                    abs(amount),
                    transaction["interest_rate"],
                    diwali_days,
                    "Diwali"
                )
                if amount < 0:  # For paid entries
                    interest = -interest
                transaction["interest"] = round(float(interest), 2)
            
            elif transaction["calendar_type"] == "Financial" and financial_days is not None:
                transaction["days"] = float(financial_days)
                # Recalculate interest
                amount = transaction["received"] if transaction["received"] > 0 else -transaction["paid"]
                interest = self.calculate_interest(
                    abs(amount),
                    transaction["interest_rate"],
                    financial_days,
                    "Financial"
                )
                if amount < 0:  # For paid entries
                    interest = -interest
                transaction["interest"] = round(float(interest), 2)
        
        return transactions_data
    
    def format_calendar_for_display(self, calendar_df):
        """Format calendar dataframe for display in the UI."""
        # Create a new dataframe with days as rows and months as columns
        # First, extract the day, month, and year from the Date column
        calendar_df['day'] = calendar_df['Date'].dt.day
        calendar_df['month'] = calendar_df['Date'].dt.month
        calendar_df['year'] = calendar_df['Date'].dt.year
        
        # Convert Shadow Value to integer
        calendar_df['Shadow Value'] = calendar_df['Shadow Value'].astype(int)
        
        # Create a month-year column for pivoting
        calendar_df['month_year'] = calendar_df['Date'].dt.strftime('%b-%Y')
        
        # Pivot the dataframe to have days as rows and month-year as columns
        pivot_df = calendar_df.pivot(
            index='day',
            columns='month_year',
            values='Shadow Value'
        )
        
        # Sort the columns by date (month and year)
        # First, create a helper dataframe to get the correct order
        month_year_df = pd.DataFrame({
            'month_year': pivot_df.columns,
            'date': pd.to_datetime(pivot_df.columns, format='%b-%Y')
        })
        month_year_df = month_year_df.sort_values('date')
        
        # Reorder the columns based on the sorted month-year values
        pivot_df = pivot_df[month_year_df['month_year'].tolist()]
        
        return pivot_df
