import pandas as pd
from datetime import datetime
import os

class Calendar:
    """
    Class representing an interest calendar.
    Handles operations related to calendar data.
    """
    
    def __init__(self, data=None, calendar_type=None, year_range=None):
        """
        Initialize a Calendar object.
        
        Args:
            data: DataFrame containing calendar data
            calendar_type: Type of calendar ('Diwali' or 'Financial')
            year_range: Year range string (e.g., '2022-2023')
        """
        self.data = data if data is not None else pd.DataFrame(columns=['Date', 'Shadow Value', 'Filename'])
        self.calendar_type = calendar_type
        self.year_range = year_range
        
        # Ensure Date column is datetime
        if 'Date' in self.data.columns and not pd.api.types.is_datetime64_any_dtype(self.data['Date']):
            try:
                # Try multiple date formats
                self.data['Date'] = pd.to_datetime(self.data['Date'], format='mixed', errors='coerce')
            except Exception:
                # Try ISO format
                try:
                    self.data['Date'] = pd.to_datetime(self.data['Date'], format='%Y-%m-%d', errors='coerce')
                except Exception:
                    # Try with day first
                    self.data['Date'] = pd.to_datetime(self.data['Date'], dayfirst=True, errors='coerce')
    
    @classmethod
    def from_file(cls, file_path):
        """
        Create a Calendar object from a CSV file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Calendar: A new Calendar object
        """
        try:
            filename = os.path.basename(file_path)
            
            # Extract calendar type and year range from filename
            if "Financial_Year" in filename:
                calendar_type = 'Financial'
                year_range = filename.replace("Financial_Year_", "").replace(".csv", "")
            else:  # Diwali calendar
                calendar_type = 'Diwali'
                # Handle different naming conventions
                if "Diwali_" in filename:
                    year_range = filename.replace("Diwali_", "").replace(".csv", "")
                else:
                    # Try to extract year range from filename (e.g., 2024-2025_diwali.csv)
                    year_range = filename.split("_")[0]
            
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            # Convert date strings to datetime objects with flexible parsing
            try:
                # First try with format='mixed' which will infer the format for each date
                df['Date'] = pd.to_datetime(df['Date'], format='mixed', errors='coerce')
            except Exception:
                try:
                    # Try YYYY-MM-DD format (ISO format)
                    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors='coerce')
                except Exception:
                    try:
                        # Try DD-MM-YYYY format
                        df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y', errors='coerce')
                    except Exception:
                        # Last resort: try with dayfirst=True
                        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
            
            # Add filename column if not present
            if 'Filename' not in df.columns:
                df['Filename'] = filename
            
            return cls(df, calendar_type, year_range)
        
        except Exception as e:
            raise ValueError(f"Error loading calendar file {file_path}: {e}")
    
    def save(self, directory="interest_calendars"):
        """
        Save the calendar to a CSV file.
        
        Args:
            directory: Directory to save the file in
            
        Returns:
            str: Path to the saved file
        """
        try:
            # Ensure the directory exists
            os.makedirs(directory, exist_ok=True)
            
            # Determine filename
            if self.calendar_type and self.year_range:
                if self.calendar_type == 'Financial':
                    filename = f"Financial_Year_{self.year_range}.csv"
                else:
                    filename = f"Diwali_{self.year_range}.csv"
            else:
                # If calendar type or year range not specified, determine from data
                first_date = self.data.iloc[0]['Date']
                last_date = self.data.iloc[-1]['Date']
                year_range = f"{first_date.year}-{last_date.year}"
                
                # Determine calendar type based on date patterns
                if first_date.month >= 10 or first_date.month <= 3:
                    filename = f"Diwali_{year_range}.csv"
                else:
                    filename = f"Financial_Year_{year_range}.csv"
            
            # Save the calendar
            file_path = os.path.join(directory, filename)
            self.data.to_csv(file_path, index=False)
            
            return file_path
        
        except Exception as e:
            raise ValueError(f"Error saving calendar: {e}")
    
    def get_shadow_value(self, date):
        """
        Get the shadow value for a specific date.
        
        Args:
            date: Date object or string in format 'YYYY-MM-DD'
            
        Returns:
            float: Shadow value for the date
        """
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Find the matching date in the calendar
        match = self.data[self.data['Date'].dt.date == date]
        
        if not match.empty:
            return match.iloc[0]['Shadow Value']
        
        return None
    
    def update_shadow_value(self, date, value):
        """
        Update the shadow value for a specific date.
        
        Args:
            date: Date object or string in format 'YYYY-MM-DD'
            value: New shadow value
            
        Returns:
            bool: True if successful, False otherwise
        """
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Find the matching date in the calendar
        mask = self.data['Date'].dt.date == date
        
        if mask.any():
            # Update existing value
            self.data.loc[mask, 'Shadow Value'] = value
            return True
        
        # Date not found
        return False
    
    def add_date(self, date, value, filename=None):
        """
        Add a new date to the calendar.
        
        Args:
            date: Date object or string in format 'YYYY-MM-DD'
            value: Shadow value
            filename: Optional filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d')
        
        # Check if date already exists
        if (self.data['Date'].dt.date == date.date()).any():
            return False
        
        # Add new row
        new_row = pd.DataFrame({
            'Date': [date],
            'Shadow Value': [value],
            'Filename': [filename or '']
        })
        
        self.data = pd.concat([self.data, new_row]).sort_values('Date')
        return True
    
    @staticmethod
    def merge_calendars(calendars):
        """
        Merge multiple calendars into one.
        
        Args:
            calendars: List of Calendar objects
            
        Returns:
            Calendar: A new merged Calendar object
        """
        if not calendars:
            return Calendar()
        
        # Extract DataFrames from Calendar objects
        dfs = [cal.data for cal in calendars]
        
        # Concatenate and sort
        merged_df = pd.concat(dfs).sort_values('Date')
        
        # Determine calendar type (use the type of the first calendar)
        calendar_type = calendars[0].calendar_type if calendars else None
        
        # Create year range spanning all calendars
        min_year = min(cal.data['Date'].dt.year.min() for cal in calendars if not cal.data.empty)
        max_year = max(cal.data['Date'].dt.year.max() for cal in calendars if not cal.data.empty)
        year_range = f"{min_year}-{max_year}"
        
        return Calendar(merged_df, calendar_type, year_range)
