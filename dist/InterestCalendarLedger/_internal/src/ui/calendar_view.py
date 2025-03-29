import streamlit as st
import pandas as pd
from datetime import datetime
import os
from streamlit_extras.colored_header import colored_header
import streamlit.components.v1 as components
from ..utils.helpers import format_calendar_for_display
from ..services.interest_service import InterestService
from ..data.data_loader import save_interest_calendar, save_transactions, load_transactions
from io import BytesIO
import numpy as np

def display_interest_calendars_tab(interest_calendars, interest_service):
    """
    Display the interest calendars tab with calendar management functionality.
    
    Args:
        interest_calendars: Dictionary containing calendar data
        interest_service: InterestService instance for calendar operations
    """
    # Use colored_header for consistent styling with other components
    colored_header(
        label="Interest Calendars Management",
        description="View and edit your interest calendars for Diwali and Financial Year calculations",
        color_name="gray-40"
    )
    
    # Add custom CSS to style tab highlights with accent colors
    st.markdown("""
    <style>
    /* Fix for duplicate highlight bars - explicitly target and hide all */
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }
    
    /* Add a custom border-bottom to the selected tab to replace the highlight */
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #ffffff !important;
        color: #4b6bfb !important;
        font-weight: 700 !important;
        border-bottom: 3px solid #4b6bfb !important;
    }
    
    /* Style horizontal radio buttons to match app theme */
    div.row-widget.stRadio > div {
        flex-direction: row;
        background-color: #f5f7fa;
        border-radius: 6px;
        padding: 4px;
        border: 1px solid #e0e6ef;
    }
    
    div.row-widget.stRadio > div > label {
        padding: 8px 16px;
        margin: 0 4px;
        border-radius: 4px;
        color: #485b73;
        font-size: 14px;
        transition: all 0.2s ease;
        border: 1px solid transparent;
        font-weight: 600;
    }
    
    div.row-widget.stRadio > div [data-baseweb="radio"] input:checked + label {
        background-color: #ffffff;
        color: #4b6bfb;
        border: 1px solid rgba(75, 107, 251, 0.3);
        font-weight: 700;
    }
    
    /* Custom styling for data editors in calendar view */
    [data-testid="stDataEditor"] {
        background-color: #ffffff !important;
        border-radius: 0.8rem !important;
        overflow: hidden !important;
        box-shadow: 0 4px 12px rgba(58, 90, 232, 0.08) !important;
    }
    
    [data-testid="stDataEditor"] table th {
        background-color: #f5f7fa !important;
        color: #2c3e50 !important;
        font-weight: 700 !important;
        text-align: center !important;
        border-bottom: 2px solid #e0e6ef !important;
    }
    
    [data-testid="stDataEditor"] table td {
        background-color: #ffffff !important;
        color: #2c3e50 !important;
        font-weight: 500 !important;
    }
    
    [data-testid="stDataEditor"] table tr:nth-child(even) td {
        background-color: #f8f9fb !important;
    }
    
    [data-testid="stDataEditor"] table tr:hover td {
        background-color: rgba(75, 107, 251, 0.05) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if not interest_calendars:
        st.warning("No interest calendars found in the interest_calendars directory.")
        
        # Add helpful guidance for creating new calendars
        st.markdown("""
        <div style="background-color: rgba(255, 208, 102, 0.1); padding:15px; border-left:4px solid #ffd166; border-radius:4px; margin-top:20px">
            <h3 style="color:#ffd166; margin-top:0;">Getting Started with Interest Calendars</h3>
            <p style="color:#e0e0e0; font-weight:500;">Interest calendars are used to track the number of days for interest calculations based on different calendar systems:</p>
            <ul style="color:#cccccc; font-weight:500;">
                <li><strong style="color:#e0e0e0;">Diwali Calendar:</strong> Based on traditional Hindu calendar used for festive calculations</li>
                <li><strong style="color:#e0e0e0;">Financial Year Calendar:</strong> Based on standard financial year (April-March)</li>
            </ul>
            <p style="color:#cccccc; font-weight:500;">To create a new calendar, you need to place CSV files in the 'interest_calendars' directory with the appropriate format.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Create main tabs for different calendar management sections
    tabs = ["📅 Calendars", "✨ Create Calendar", "📤 Upload Calendar"]
    
    # Determine which tab to show based on session state
    if 'current_tab' in st.session_state and st.session_state['current_tab'] is not None:
        try:
            # Force the specified tab to be shown
            tab_index = tabs.index(st.session_state['current_tab'])
            # Clear the flag after using it
            st.session_state['current_tab'] = None
        except ValueError:
            # If the tab name is not found, default to first tab
            tab_index = 0
    else:
        tab_index = 0
    
    # Create tabs with the selected tab first
    selected_tab = tabs[tab_index]
    other_tabs = [t for t in tabs if t != selected_tab]
    all_tabs = [selected_tab] + other_tabs
    
    # Create the tabs
    calendar_tab, create_tab, upload_tab = st.tabs(all_tabs)
    
    with calendar_tab:
        if interest_calendars:
            # Create tabs for calendar types
            calendar_types = ["💫 Diwali Calendars", "📊 Financial Year Calendars"]
            
            # Determine which calendar type tab to show based on session state
            if 'current_calendar_type' in st.session_state and st.session_state['current_calendar_type'] is not None:
                # Force the specific calendar type tab to be shown
                selected_type = st.session_state['current_calendar_type']
                if selected_type == 'diwali':
                    diwali_tab, financial_tab = st.tabs(calendar_types)
                    with diwali_tab:
                        display_calendar_type_view(interest_calendars, interest_service, "diwali")
                    with financial_tab:
                        display_calendar_type_view(interest_calendars, interest_service, "financial")
                    # Clear the flag after using it
                    st.session_state['current_calendar_type'] = None
                else:
                    financial_tab, diwali_tab = st.tabs(calendar_types)
                    with financial_tab:
                        display_calendar_type_view(interest_calendars, interest_service, "financial")
                    with diwali_tab:
                        display_calendar_type_view(interest_calendars, interest_service, "diwali")
                    # Clear the flag after using it
                    st.session_state['current_calendar_type'] = None
            else:
                # Normal tab selection
                diwali_tab, financial_tab = st.tabs(calendar_types)
                with diwali_tab:
                    display_calendar_type_view(interest_calendars, interest_service, "diwali")
                with financial_tab:
                    display_calendar_type_view(interest_calendars, interest_service, "financial")
        else:
            st.warning("No calendars available. Please upload a calendar file first.")
    
    with create_tab:
        display_create_calendar_section(interest_calendars)
    
    with upload_tab:
        display_calendar_upload_section(interest_calendars)

def display_calendar_type_view(interest_calendars, interest_service, calendar_type):
    """Display view for a specific calendar type (Diwali or Financial)."""
    # Check if we need to show the newly created calendar
    if 'calendar_created' in st.session_state and st.session_state['calendar_created']:
        if st.session_state['new_calendar_type'] == calendar_type.lower():
            # Clear the flag
            st.session_state['calendar_created'] = False
            # Show success message
            st.success(f"✅ New calendar '{st.session_state['new_calendar_filename']}' has been created!")
            
            # Set the calendar to show in the selectbox
            if 'selected_calendar' in st.session_state:
                st.session_state[f"individual_{calendar_type}_calendar_select"] = st.session_state['selected_calendar']
                # Clear the flag after using it
                st.session_state['selected_calendar'] = None
    
    # Display individual calendars directly without tabs
    display_individual_calendars(interest_calendars, interest_service, calendar_type)

def display_individual_calendars(interest_calendars, interest_service, calendar_type):
    """Display individual calendars for a specific calendar type."""
    # Create a selectbox to choose which calendar to view
    calendar_options = list(interest_calendars[calendar_type].keys())
    if calendar_options:
        selected_calendar = st.selectbox(
            f"**Select {calendar_type.title()} Calendar Year Range**", 
            options=calendar_options,
            key=f"individual_{calendar_type}_calendar_select"
        )
        
        # Display the selected calendar
        if selected_calendar in interest_calendars[calendar_type]:
            calendar_data = interest_calendars[calendar_type][selected_calendar]
            
            # Format the calendar for display (month-columns, day-rows)
            display_matrix = interest_service.format_calendar_for_display(calendar_data)
            
            # Show calendar in editable format with improved styling
            st.markdown(f"""
            <div style="background-color:#ffffff; 
                       padding:15px; border-radius:8px; margin-top:20px; margin-bottom:15px; 
                       border-left:4px solid {'#72e2ae' if calendar_type == 'diwali' else '#4b6bfb'};
                       border:1px solid {'#e0e6ef' if calendar_type == 'diwali' else '#e0e6ef'};
                       box-shadow: 0 4px 12px rgba(58, 90, 232, 0.08);">
                <h3 style="color:{'#28a745' if calendar_type == 'diwali' else '#4b6bfb'}; margin:0; display:flex; align-items:center">
                    <span style="margin-right:10px">{'📆' if calendar_type == 'diwali' else '📊'}</span> {calendar_type.title()} Calendar: {selected_calendar}
                </h3>
                <p style="color:#2c3e50; font-weight:500; margin-top:10px">
                    Edit shadow values directly in the table below. Changes will be saved to the original calendar file.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Initialize matrices in session state
            editor_key = f"{calendar_type}_{selected_calendar}_calendar_editor"
            prev_key = f"prev_matrix_{calendar_type}_{selected_calendar}"
            values_key = f"prev_values_{calendar_type}_{selected_calendar}"
            update_ui_key = f"{editor_key}_needs_update"
            
            # Check if we need to force update the UI
            if update_ui_key in st.session_state and st.session_state[update_ui_key]:
                # Use the previously updated matrix
                updated_matrix_key = f"{editor_key}_updated_matrix"
                if updated_matrix_key in st.session_state:
                    display_matrix = st.session_state[updated_matrix_key]
                    # Clear the updated matrix from session state
                    st.session_state[prev_key] = display_matrix.copy()
                
                # Clear the flag
                st.session_state[update_ui_key] = False
            
            if prev_key not in st.session_state:
                st.session_state[prev_key] = display_matrix.copy()
            
            # Store values before edit in a simpler format for direct comparison
            if values_key not in st.session_state:
                st.session_state[values_key] = display_matrix.to_dict()
            
            # Display data editor
            edited_matrix = st.data_editor(
                display_matrix,
                use_container_width=True,
                num_rows="dynamic",
                disabled=False,
                key=editor_key,
                column_config={col: st.column_config.NumberColumn(
                    col, 
                    help=f"Shadow value for {col}", 
                    min_value=0,
                    format="%.0f",
                    step=1,
                    width="small"
                ) for col in display_matrix.columns},
                hide_index=False,
                column_order=None,
                height=1132  # Increase height to show more rows
            )
            
            # Check if values have changed - DataFrame comparison
            if editor_key in st.session_state:
                try:
                    # Compare only the values, not the structure
                    prev_values = st.session_state[prev_key].values
                    curr_values = edited_matrix.values
                    
                    # Find differences in values, ignoring NaN values
                    diff_mask = np.where(
                        ~(np.isnan(prev_values) & np.isnan(curr_values)),  # Not both NaN
                        prev_values != curr_values,  # Different values
                        False  # Both NaN = no difference
                    )
                    
                    if diff_mask.any():
                        # Get positions of changed cells
                        changed_positions = np.where(diff_mask)
                        row_idx, col_idx = changed_positions[0][0], changed_positions[1][0]
                        
                        # Get the new value that was entered
                        new_value = edited_matrix.iloc[row_idx, col_idx]
                        
                        # Only proceed if the new value is not NaN
                        if pd.notna(new_value):
                            # Update the next day (if not at the end of month)
                            day = edited_matrix.index[row_idx]
                            col_name = edited_matrix.columns[col_idx]
                            
                            # Check if there's a next day in the same month
                            if row_idx + 1 < len(edited_matrix):
                                next_day = edited_matrix.index[row_idx + 1]
                                # Update the next day's value
                                next_value = max(1, int(float(new_value)) - 1)
                                edited_matrix.loc[next_day, col_name] = next_value
                                
                                # Store updated matrix for next rerun
                                st.session_state[f"{editor_key}_updated_matrix"] = edited_matrix.copy()
                                # Set flag to update UI on next run
                                st.session_state[update_ui_key] = True
                                
                                # Save changes immediately
                                save_calendar_changes(edited_matrix, calendar_data, calendar_type, selected_calendar, interest_calendars, interest_service)
                                
                                # Force rerun to update the UI
                                st.rerun()
                            # If it's the last day of the month, update the first day of next month
                            elif col_idx + 1 < len(edited_matrix.columns):
                                next_col = edited_matrix.columns[col_idx + 1]
                                # Find the first valid row in the next month
                                for i, idx in enumerate(edited_matrix.index):
                                    if not pd.isna(edited_matrix.loc[idx, next_col]):
                                        next_value = max(1, int(float(new_value)) - 1)
                                        edited_matrix.loc[idx, next_col] = next_value
                                        
                                        # Store updated matrix for next rerun
                                        st.session_state[f"{editor_key}_updated_matrix"] = edited_matrix.copy()
                                        # Set flag to update UI on next run
                                        st.session_state[update_ui_key] = True
                                        
                                        # Save changes immediately
                                        save_calendar_changes(edited_matrix, calendar_data, calendar_type, selected_calendar, interest_calendars, interest_service)
                                        
                                        # Force rerun to update the UI
                                        st.rerun()
                                        break
                except Exception as e:
                    st.error(f"Error updating next day's value: {str(e)}")
            
            # Store the data for next comparison
            st.session_state[prev_key] = edited_matrix.copy()
            st.session_state[values_key] = edited_matrix.to_dict()
            
            # Add save and print buttons
            save_col1, print_col1, _ = st.columns([1, 1, 4])
            
            with save_col1:
                save_button = st.button(
                    "💾 Save Changes", 
                    key=f"save_{calendar_type}_{selected_calendar}_btn",
                    use_container_width=True,
                    type="primary"
                )
            
            with print_col1:
                if st.button("🖨️ Print Calendar", key=f"print_{calendar_type}_{selected_calendar}_btn"):
                    # We'll use the same display_matrix that is used in the data editor
                    # This ensures the print layout matches exactly what the user sees
                    
                    # Create table HTML from the display matrix with more compact styling
                    matrix_html = """
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
                        <thead>
                            <tr>
                                <th style="border: 1px solid #ddd; padding: 5px; background-color: #f8f9fa; text-align: center; font-size: 10px; white-space: normal; word-wrap: break-word;">Day</th>
                    """
                    
                    # Add column headers (months) with smaller font
                    for col in display_matrix.columns:
                        matrix_html += f'<th style="border: 1px solid #ddd; padding: 5px; background-color: #f8f9fa; text-align: center; font-size: 10px; white-space: normal; word-wrap: break-word;">{col}</th>'
                    
                    matrix_html += """
                            </tr>
                        </thead>
                        <tbody>
                    """
                    
                    # Add data rows with smaller font and padding
                    for day in display_matrix.index:
                        matrix_html += f'<tr><td style="border: 1px solid #ddd; padding: 3px; font-weight: bold; background-color: #f8f9fa; text-align: center; font-size: 9px; white-space: normal; word-wrap: break-word;">{day}</td>'
                        
                        for col in display_matrix.columns:
                            value = display_matrix.loc[day, col]
                            # Use different background for even/odd rows
                            bg_color = '#ffffff' if day % 2 == 0 else '#f9f9f9'
                            if pd.isna(value):
                                matrix_html += f'<td style="border: 1px solid #ddd; padding: 3px; background-color: {bg_color}; text-align: center; font-size: 9px; white-space: normal; word-wrap: break-word;">-</td>'
                            else:
                                matrix_html += f'<td style="border: 1px solid #ddd; padding: 3px; background-color: {bg_color}; text-align: center; font-size: 9px; white-space: normal; word-wrap: break-word;">{int(value)}</td>'
                        
                        matrix_html += '</tr>'
                    
                    matrix_html += """
                        </tbody>
                    </table>
                    """
                    
                    # Get current date/time
                    date_time = datetime.now().strftime('%d %b %Y')
                    
                    # Create complete HTML document with compact CSS and print script
                    complete_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{calendar_type.title()} Calendar: {selected_calendar}</title>
    <style>
        @page {{
            size: portrait;
            margin: 10mm 5mm;
        }}
        body {{ 
            font-family: 'Segoe UI', Arial, sans-serif; 
            background-color: white; 
            color: black;
            margin: 0;
            padding: 10px;
            font-size: 10px;
        }}
        @media print {{
            body {{ 
                print-color-adjust: exact; 
                -webkit-print-color-adjust: exact;
                padding: 0;
            }}
            .no-print {{ display: none; }}
            button {{ display: none; }}
        }}
        .print-header {{ 
            text-align: center;
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }}
        .print-header h2 {{
            font-size: 14px;
            font-weight: bold;
            margin: 0 0 3px 0;
            color: {'#72e2ae' if calendar_type == 'diwali' else '#4b6bfb'};
        }}
        .print-header p {{
            font-size: 9px;
            color: #666;
            margin: 0;
        }}
        .calendar-container {{
            padding: 5px;
            background-color: white;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 10px;
            table-layout: fixed;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 2px 3px;
            text-align: center;
            font-size: 8px;
            white-space: normal;
            word-wrap: break-word;
            overflow-wrap: break-word;
            max-width: 30px;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
            height: auto;
            vertical-align: middle;
        }}
        th:first-child {{
            background-color: #f0f0f0;
            width: 20px;
        }}
        td:first-child {{
            font-weight: bold;
            background-color: #f8f9fa;
            width: 20px;
        }}
        tr:nth-child(even) td {{
            background-color: #f9f9f9;
        }}
        .footer {{
            text-align: center;
            font-size: 8px;
            color: #666;
            margin-top: 10px;
            padding-top: 5px;
            border-top: 1px solid #eee;
        }}
        .print-button {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 8px 16px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }}
    </style>
    <script>
        window.onload = function() {{
            window.print();
        }};
    </script>
</head>
<body>
    <div class="print-header">
        <h2>{calendar_type.title()} Calendar: {selected_calendar}</h2>
        <p>Generated: {date_time}</p>
    </div>
    
    <div class="calendar-container">
        {matrix_html}
    </div>
    
    <div class="footer">
        Interest Calendar Application
    </div>
    
    <div class="no-print" style="text-align: center; margin-top: 10px;">
        <button onclick="window.print()" class="print-button">Print</button>
        <button onclick="window.close()" class="print-button" style="background-color: #555;">Close</button>
    </div>
</body>
</html>"""
                    
                    # Use components.html to display the printable content
                    components.html(complete_html, height=0, scrolling=False)
                    
                    st.success("Print dialog should open automatically. If it doesn't, check your browser settings.")
            
            if save_button:
                # Save changes when save button is clicked
                save_calendar_changes(edited_matrix, calendar_data, calendar_type, selected_calendar, interest_calendars, interest_service)
    else:
        st.warning(f"No {calendar_type.title()} calendars found.")
        
        # Add guidance for creating a new calendar
        st.markdown(f"""
        <div style="background-color: rgba(255, 208, 102, 0.1); padding:15px; border-left:4px solid #ffd166; border-radius:4px; margin-top:20px">
            <h4 style="color:#ffd166; margin-top:0;">How to Create a {calendar_type.title()} Calendar</h4>
            <p style="color:#e0e0e0; font-weight:500;">To create a new {calendar_type.title()} calendar:</p>
            <ol style="color:#cccccc; font-weight:500;">
                <li>Create a CSV file with columns: <code style="background-color:#252532; padding:2px 4px; border-radius:3px;">Date</code> (in {'DD-MM-YYYY' if calendar_type == 'diwali' else 'YYYY-MM-DD'} format) and <code style="background-color:#252532; padding:2px 4px; border-radius:3px;">Shadow Value</code></li>
                <li>Name the file with pattern <code style="background-color:#252532; padding:2px 4px; border-radius:3px;">{calendar_type.lower()}_YYYY-YYYY.csv</code></li>
                <li>Place it in the <code style="background-color:#252532; padding:2px 4px; border-radius:3px;">interest_calendars</code> directory</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

def save_calendar_changes(edited_matrix, calendar_data, calendar_type, selected_calendar, interest_calendars, interest_service):
    """Save changes to the calendar file."""
    with st.spinner("Saving calendar and recalculating transactions..."):
        try:
            # Get the original data format
            updated_df = calendar_data.copy()
            
            # Update values based on the edited matrix
            for day in edited_matrix.index:
                for col in edited_matrix.columns:
                    # Extract month and year from column name
                    month_str, year_str = col.split('-')
                    month_num = pd.to_datetime(month_str, format='%b').month
                    year = int(year_str)
                    
                    value = edited_matrix.loc[day, col]
                    if pd.notna(value):
                        # Convert value to integer
                        value = int(float(value))
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
                                'source_file': [updated_df['source_file'].iloc[0]]  # Use the same source file
                            })
                            updated_df = pd.concat([updated_df, new_row], ignore_index=True)
            
            # Sort the DataFrame by date to ensure proper order
            updated_df = updated_df.sort_values('Date')
            
            # Save the updated calendar
            if save_interest_calendar(updated_df):
                # Reload transactions and recalculate interest values
                transactions_data = load_transactions()
                updated_transactions = interest_service.recalculate_all_transaction_interest(transactions_data)
                save_transactions(updated_transactions)
                
                # Update the calendar data in memory
                interest_calendars[calendar_type][selected_calendar] = updated_df
                
                # Show success message
                st.success(f"✅ {calendar_type.title()} calendar for {selected_calendar} updated successfully! All transactions have been recalculated.")
            else:
                st.error("Failed to save calendar changes. Please try again.")
        except Exception as e:
            st.error(f"Error saving calendar changes: {str(e)}")
            st.error("Please check the console for more details.")

def display_create_calendar_section(interest_calendars):
    """Display the calendar creation section."""
    st.markdown("""
    <div style="background-color:#ffffff; padding:1rem; border-radius:0.5rem; border-left:4px solid #1a1a1a;">
        <h3 style="color:#000000; margin-top:0;">Create New Calendar</h3>
        <p style="color:#000000;">Create a new calendar by specifying the date range and initial shadow value.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Calendar type selection
    calendar_type = st.radio(
        "Calendar Type",
        ["Financial", "Diwali"],
        horizontal=True,
        key="create_calendar_type"
    )
    
    # Start date selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now().replace(day=1),
            key="create_calendar_start_date"
        )
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now().replace(day=1).replace(year=datetime.now().year + 1),
            key="create_calendar_end_date"
        )
    
    # Initial shadow value
    initial_shadow_value = st.number_input(
        "Initial Shadow Value",
        min_value=1,
        max_value=360,
        value=360,
        step=1,
        help="The shadow value for the first day. Subsequent days will automatically decrease by 1."
    )
    
    if st.button("Create Calendar", type="primary", key="create_calendar_btn"):
        if start_date >= end_date:
            st.error("End date must be after start date.")
            return
        
        try:
            # Check for date overlaps with existing calendars
            has_overlap = False
            overlapping_calendars = []
            
            # Generate the date range for the new calendar
            new_dates = pd.date_range(start=start_date, end=end_date)
            
            # Check overlaps with existing calendars of the same type
            if calendar_type.lower() in interest_calendars:
                for existing_calendar_name, existing_calendar_data in interest_calendars[calendar_type.lower()].items():
                    # Convert existing calendar dates to datetime if they're strings
                    existing_dates = pd.to_datetime(existing_calendar_data['Date'])
                    
                    # Check for any overlap
                    if any(date in existing_dates for date in new_dates):
                        has_overlap = True
                        overlapping_calendars.append(existing_calendar_name)
            
            if has_overlap:
                # Show error with details about overlapping calendars
                st.error(f"""
                Cannot create calendar: Date range overlaps with existing calendar(s):
                {', '.join(overlapping_calendars)}
                
                Please choose a different date range or modify the existing calendar(s).
                """)
                return
            
            # Create the interest_calendars directory if it doesn't exist
            os.makedirs("interest_calendars", exist_ok=True)
            
            # Generate dates between start and end dates
            dates = pd.date_range(start=start_date, end=end_date)
            
            # Create shadow values (decreasing from initial value)
            shadow_values = list(range(initial_shadow_value, initial_shadow_value - len(dates), -1))
            
            # Create DataFrame
            df = pd.DataFrame({
                'Date': dates,
                'Shadow Value': shadow_values[:len(dates)]  # Ensure we don't exceed the date range
            })
            
            # Format dates based on calendar type
            if calendar_type == "Diwali":
                df['Date'] = df['Date'].dt.strftime('%d-%m-%Y')
                year_range = f"{start_date.year}-{end_date.year}"
                filename = f"{year_range}_diwali.csv"
            else:
                df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
                year_range = f"{start_date.year}-{end_date.year}"
                filename = f"Financial_Year_{year_range}.csv"
            
            # Add source file column for tracking
            df['source_file'] = filename
            
            # Save the file
            file_path = os.path.join("interest_calendars", filename)
            
            # Check if file already exists
            if os.path.exists(file_path):
                st.warning(f"A calendar file with name '{filename}' already exists. It will be overwritten.")
            
            # Save the file
            df.to_csv(file_path, index=False)
            
            # Verify file was created
            if os.path.exists(file_path):
                # Store success message and navigation info in session state
                st.session_state['calendar_created'] = True
                st.session_state['new_calendar_filename'] = filename
                st.session_state['new_calendar_type'] = calendar_type.lower()
                st.session_state['new_calendar_year_range'] = year_range
                
                # Set the main tab to show calendars
                st.session_state['current_tab'] = "📅 Calendars"
                
                # Set the calendar type tab
                st.session_state['current_calendar_type'] = calendar_type.lower()
                
                # Set the calendar to show
                st.session_state['selected_calendar'] = year_range
                
                # Show success message
                st.success(f"✅ Calendar file '{filename}' created successfully!")
                st.info("Redirecting to calendar view...")
                
                # Force rerun to update the view
                st.rerun()
            else:
                st.error("Failed to create the calendar file. Please check file permissions.")
                
        except Exception as e:
            st.error(f"Error creating calendar: {str(e)}")
            st.error("Please check the console for more details.")

def display_calendar_upload_section(interest_calendars):
    """Display section for uploading calendar files."""
    st.markdown("""
    <div style="background-color:#FFFFFF; padding:1rem; border-radius:0.5rem; border-left:4px solid #1a1a1a;">
        <h3 style="color:#000000; margin-top:0;">Upload Calendar File</h3>
        <p style="color:#000000;">Upload a CSV file containing interest calendar data.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # File uploader for calendar files
    uploaded_file = st.file_uploader(
        "Upload a CSV file", 
        type=["csv"], 
        key="calendar_file_uploader",
        help="Select a CSV file containing calendar data. The file should have 'Date' and 'Shadow Value' columns."
    )
    
    # Instructions for file format
    with st.expander("File Format Instructions", expanded=False):
        st.markdown("""
        ### CSV File Format Requirements
        
        Your CSV file should contain the following columns:
        
        - **Date**: In the format `YYYY-MM-DD` for Financial calendars or `DD-MM-YYYY` for Diwali calendars
        - **Shadow Value**: Integer values representing shadow days (typically between 1-360)
        
        #### Example CSV content:
        
        ```
        Date,Shadow Value
        2023-04-01,360
        2023-04-02,359
        2023-04-03,358
        ...
        ```
        
        #### File Naming:
        
        For automatic detection of calendar type, use one of these naming patterns:
        - Financial Year: `Financial_Year_YYYY-YYYY.csv` (e.g., Financial_Year_2023-2024.csv)
        - Diwali: `YYYY-YYYY_diwali.csv` (e.g., 2023-2024_diwali.csv)
        """)
    
    # Calendar type selection (for manual selection if filename doesn't match patterns)
    calendar_type = st.radio(
        "Calendar Type",
        ["Financial", "Diwali"],
        horizontal=True,
        key="upload_calendar_type"
    )
    
    if uploaded_file is not None:
        try:
            # Process the uploaded file
            filename = uploaded_file.name
            
            # Try to detect calendar type from filename
            detected_type = None
            if "financial" in filename.lower() or "financial_year" in filename.lower():
                detected_type = "Financial"
            elif "diwali" in filename.lower():
                detected_type = "Diwali"
            
            # Use detected type or user selection
            final_type = detected_type or calendar_type
            
            # Read CSV data
            df = pd.read_csv(uploaded_file)
            
            # Validate required columns
            if "Date" not in df.columns or "Shadow Value" not in df.columns:
                st.error("The CSV file must contain 'Date' and 'Shadow Value' columns.")
                return
            
            # Convert Date column to datetime based on calendar type
            if final_type == "Diwali":
                try:
                    df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y')
                except:
                    df['Date'] = pd.to_datetime(df['Date'])
            else:
                try:
                    df['Date'] = pd.to_datetime(df['Date'])
                except:
                    st.error("Could not parse dates. Please check the date format.")
                    return
            
            # Extract year range from the data
            start_year = df['Date'].dt.year.min()
            end_year = df['Date'].dt.year.max()
            year_range = f"{start_year}-{end_year}"
            
            # Determine target filename
            if final_type == "Diwali":
                target_filename = f"{year_range}_diwali.csv"
            else:
                target_filename = f"Financial_Year_{year_range}.csv"
            
            # Add source file column for tracking
            df['source_file'] = target_filename
            
            # Confirm upload
            if st.button("Save Calendar", type="primary", key="save_uploaded_calendar"):
                # Create directory if it doesn't exist
                os.makedirs("interest_calendars", exist_ok=True)
                
                # Save to file
                file_path = os.path.join("interest_calendars", target_filename)
                df.to_csv(file_path, index=False)
                
                st.success(f"✅ Calendar file '{target_filename}' saved successfully!")
                st.info("The application will reload to include the new calendar.")
                st.rerun()  # Refresh to load the new calendar
                
        except Exception as e:
            st.error(f"Error processing uploaded file: {str(e)}")
            st.error("Please ensure the CSV file is properly formatted.")
