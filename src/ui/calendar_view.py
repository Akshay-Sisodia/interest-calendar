import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_extras.colored_header import colored_header
from ..utils.helpers import format_calendar_for_display
from ..services.interest_service import InterestService
from ..data.data_loader import save_interest_calendar, save_transactions, load_transactions

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
    
    # Add custom CSS to style tab highlights with gray-40
    st.markdown("""
    <style>
    /* Fix for duplicate highlight bars - explicitly target and hide all */
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }
    
    /* Add a custom border-bottom to the selected tab to replace the highlight */
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: rgba(200, 200, 200, 0.15) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-bottom: 3px solid #6e7681 !important; /* gray-40 color */
    }
    
    /* Style horizontal radio buttons to match app theme */
    div.row-widget.stRadio > div {
        flex-direction: row;
        background-color: #0a0a0a;
        border-radius: 6px;
        padding: 4px;
        border: 1px solid #1a1a1a;
    }
    
    div.row-widget.stRadio > div > label {
        padding: 8px 16px;
        margin: 0 4px;
        border-radius: 4px;
        color: #aaaaaa;
        font-size: 14px;
        transition: all 0.2s ease;
        border: 1px solid transparent;
    }
    
    div.row-widget.stRadio > div [data-baseweb="radio"] input:checked + label {
        background-color: #121212;
        color: #ffffff;
        border: 1px solid #333333;
        font-weight: 500;
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
    else:
        # Simple radio button for view options
        view_option = st.radio(
            "Calendar View Options",
            ["Combined Calendar", "Individual Calendars"],
            horizontal=True
        )
        
        # Display calendar information
        with st.expander("**ℹ️ About Interest Calendars**", expanded=False):
            st.markdown("""
            <div style="color:#cccccc; font-weight:500; line-height:1.5">
            Interest calendars are used to determine the number of interest days for each date in the system.
            <ul>
                <li><strong style="color:#e0e0e0;">Diwali Calendar</strong>: Used for traditional interest calculations based on the Hindu festival cycle</li>
                <li><strong style="color:#e0e0e0;">Financial Calendar</strong>: Used for interest calculations based on the standard financial year (April to March)</li>
            </ul>
            
            When you edit a calendar, all transactions using that calendar type will automatically have their interest recalculated.
            </div>
            """, unsafe_allow_html=True)
        
        # Create column layout for calendar stats
        col1, col2 = st.columns(2)
        
        # Calculate calendar stats
        with col1:
            diwali_years = list(interest_calendars['diwali'].keys()) if 'diwali' in interest_calendars else []
            diwali_count = len(diwali_years)
            
            st.markdown(f"""
            <div style="background-color:rgba(114, 226, 174, 0.08); padding:15px; border-radius:8px; text-align:center; height:100%; 
                      box-shadow:0 4px 10px rgba(0,0,0,0.15); border:1px solid rgba(114, 226, 174, 0.2);">
                <h3 style="color:#72e2ae; margin-top:0;">Diwali Calendars</h3>
                <h1 style="color:#72e2ae; font-size:2.5rem; text-shadow:0 2px 4px rgba(0,0,0,0.2); margin:10px 0;">{diwali_count}</h1>
                <p style="color:#cccccc; font-weight:500;">{', '.join(diwali_years) if diwali_years else 'No calendars available'}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            financial_years = list(interest_calendars['financial'].keys()) if 'financial' in interest_calendars else []
            financial_count = len(financial_years)
            
            st.markdown(f"""
            <div style="background-color:rgba(75, 107, 251, 0.08); padding:15px; border-radius:8px; text-align:center; height:100%; 
                      box-shadow:0 4px 10px rgba(0,0,0,0.15); border:1px solid rgba(75, 107, 251, 0.2);">
                <h3 style="color:#6c7eff; margin-top:0;">Financial Calendars</h3>
                <h1 style="color:#6c7eff; font-size:2.5rem; text-shadow:0 2px 4px rgba(0,0,0,0.2); margin:10px 0;">{financial_count}</h1>
                <p style="color:#cccccc; font-weight:500;">{', '.join(financial_years) if financial_years else 'No calendars available'}</p>
            </div>
            """, unsafe_allow_html=True)
        
        if view_option == "Combined Calendar":
            # Create tabs for combined calendar views with custom styling - no need for additional tab styling
            diwali_tab, financial_tab = st.tabs(["💫 Combined Diwali Calendar", "📊 Combined Financial Year Calendar"])
            
            with diwali_tab:
                display_combined_calendar(interest_calendars, interest_service, "diwali")
            
            with financial_tab:
                display_combined_calendar(interest_calendars, interest_service, "financial")
        
        else:  # Individual Calendars view
            # Create tabs for Diwali and Financial calendars
            diwali_tab, financial_tab = st.tabs(["💫 Diwali Calendars", "📊 Financial Year Calendars"])
            
            with diwali_tab:
                display_individual_calendars(interest_calendars, interest_service, "diwali")
            
            with financial_tab:
                display_individual_calendars(interest_calendars, interest_service, "financial")

def display_combined_calendar(interest_calendars, interest_service, calendar_type):
    """Display combined calendar view for a specific calendar type."""
    merged_key = f'merged_{calendar_type}'
    
    if interest_calendars[merged_key] is not None:
        merged_calendar = interest_calendars[merged_key]
        
        # Add description of the calendar
        st.markdown(f"""
        <div style="background-color:#252532; padding:15px; border-radius:5px; margin-bottom:15px; border-left:4px solid 
                   {'#72e2ae' if calendar_type == 'diwali' else '#4b6bfb'};">
            <p style="color:#e0e0e0; font-weight:500; margin:0;">
                The combined {calendar_type.title()} calendar shows all shadow values across all years. Edit values directly in the table below.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Format the calendar for display (month-columns, day-rows)
        display_matrix = interest_service.format_calendar_for_display(merged_calendar)
        
        # Show calendar in editable format with improved styling
        st.markdown(f"""
        <h3 style="color:{'#72e2ae' if calendar_type == 'diwali' else '#6c7eff'}; margin-top:10px; display:flex; align-items:center; 
                   background-color:{'rgba(114, 226, 174, 0.08)' if calendar_type == 'diwali' else 'rgba(75, 107, 251, 0.08)'}; 
                   padding:12px; border-radius:8px; border:1px solid 
                   {'rgba(114, 226, 174, 0.15)' if calendar_type == 'diwali' else 'rgba(75, 107, 251, 0.15)'};">
            <span style="margin-right:10px">{'📆' if calendar_type == 'diwali' else '📊'}</span> Combined {calendar_type.title()} Calendar
        </h3>
        """, unsafe_allow_html=True)
        
        # Add a filter for years if the matrix is large
        available_years = sorted(set(col.split('-')[1] for col in display_matrix.columns))
        if len(available_years) > 2:
            selected_years = st.multiselect(
                "Filter by Year",
                options=available_years,
                default=available_years,  # Default to all years
                key=f"{calendar_type}_year_filter"
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
        
        # Create a more modern data editor with enhanced styling
        edited_matrix = st.data_editor(
            filtered_matrix,
            use_container_width=True,
            num_rows="dynamic",
            disabled=False,
            key=f"combined_{calendar_type}_calendar_editor",
            column_config={col: st.column_config.NumberColumn(
                col, 
                help=f"Shadow value for {col}", 
                min_value=0,
                format="%.0f",
                step=1,
                width="small"
            ) for col in filtered_matrix.columns},
            hide_index=False,
            column_order=None
        )
        
        # Add save button - using Streamlit's built-in button for consistency
        save_col1, save_col2 = st.columns([1, 5])
        with save_col1:
            save_button = st.button(
                "💾 Save Changes", 
                key=f"save_combined_{calendar_type}_btn",
                use_container_width=True,
                type="primary"
            )
        
        if save_button:
            with st.spinner("Saving calendar and recalculating transactions..."):
                # Get the original data format
                updated_df = merged_calendar.copy()
                
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
                            value = int(value)
                            # Create the date to match
                            match_date = pd.Timestamp(year=year, month=month_num, day=day).date()
                            
                            # Find any existing rows with this date
                            mask = updated_df['Date'].dt.date == match_date
                            
                            if mask.any():
                                # Update existing value
                                updated_df.loc[mask, 'Shadow Value'] = value
                            else:
                                # Add new row - need to determine which file it should go to
                                # Find the appropriate file based on the date
                                year_key = None
                                for key in interest_calendars[calendar_type].keys():
                                    start_year, end_year = map(int, key.split('-'))
                                    if start_year <= year <= end_year:
                                        year_key = key
                                        break
                                
                                if year_key:
                                    # Get the source filename
                                    source_file = interest_calendars[calendar_type][year_key]['source_file'].iloc[0]
                                    
                                    # Add new row
                                    new_row = pd.DataFrame({
                                        'Date': [pd.Timestamp(year=year, month=month_num, day=day)],
                                        'Shadow Value': [value],
                                        'source_file': [source_file]
                                    })
                                    updated_df = pd.concat([updated_df, new_row], ignore_index=True)
                
                # Save the updated calendar
                if save_interest_calendar(updated_df):
                    # Reload transactions and recalculate interest values
                    transactions_data = load_transactions()
                    updated_transactions = interest_service.recalculate_all_transaction_interest(transactions_data)
                    save_transactions(updated_transactions)
                    
                    # Show success message
                    st.success(f"✅ {calendar_type.title()} calendar updated successfully! All transactions have been recalculated.")
                else:
                    st.error("Failed to save calendar changes. Please try again.")
    else:
        st.error(f"Could not create combined {calendar_type.title()} calendar view.")

def display_individual_calendars(interest_calendars, interest_service, calendar_type):
    """Display individual calendars for a specific calendar type."""
    # Create a selectbox to choose which calendar to view
    calendar_options = list(interest_calendars[calendar_type].keys())
    if calendar_options:
        selected_calendar = st.selectbox(
            f"**Select {calendar_type.title()} Calendar Year Range**", 
            options=calendar_options,
            key=f"{calendar_type}_calendar_select"
        )
        
        # Display the selected calendar
        if selected_calendar in interest_calendars[calendar_type]:
            calendar_data = interest_calendars[calendar_type][selected_calendar]
            
            # Format the calendar for display (month-columns, day-rows)
            display_matrix = interest_service.format_calendar_for_display(calendar_data)
            
            # Show calendar in editable format with improved styling
            st.markdown(f"""
            <div style="background-color:{'rgba(114, 226, 174, 0.08)' if calendar_type == 'diwali' else 'rgba(75, 107, 251, 0.08)'}; 
                       padding:15px; border-radius:8px; margin-top:20px; margin-bottom:15px; 
                       border-left:4px solid {'#72e2ae' if calendar_type == 'diwali' else '#4b6bfb'};
                       border:1px solid {'rgba(114, 226, 174, 0.15)' if calendar_type == 'diwali' else 'rgba(75, 107, 251, 0.15)'};">
                <h3 style="color:{'#72e2ae' if calendar_type == 'diwali' else '#6c7eff'}; margin:0; display:flex; align-items:center">
                    <span style="margin-right:10px">{'📆' if calendar_type == 'diwali' else '📊'}</span> {calendar_type.title()} Calendar: {selected_calendar}
                </h3>
                <p style="color:#e0e0e0; font-weight:500; margin-top:10px">
                    Edit shadow values directly in the table below. Changes will be saved to the original calendar file.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Create a more modern data editor with enhanced styling
            edited_matrix = st.data_editor(
                display_matrix,
                use_container_width=True,
                num_rows="dynamic",
                disabled=False,
                key=f"{calendar_type}_{selected_calendar}_calendar_editor",
                column_config={col: st.column_config.NumberColumn(
                    col, 
                    help=f"Shadow value for {col}", 
                    min_value=0,
                    format="%.0f",
                    step=1,
                    width="small"
                ) for col in display_matrix.columns},
                hide_index=False,
                column_order=None
            )
            
            # Add save button - using Streamlit's built-in button for consistency
            save_col1, save_col2 = st.columns([1, 5])
            with save_col1:
                save_button = st.button(
                    "💾 Save Changes", 
                    key=f"save_{calendar_type}_{selected_calendar}_btn",
                    use_container_width=True,
                    type="primary"
                )
            
            if save_button:
                with st.spinner("Saving calendar and recalculating transactions..."):
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
                                value = int(value)
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
                    
                    # Save the updated calendar
                    if save_interest_calendar(updated_df):
                        # Reload transactions and recalculate interest values
                        transactions_data = load_transactions()
                        updated_transactions = interest_service.recalculate_all_transaction_interest(transactions_data)
                        save_transactions(updated_transactions)
                        
                        # Show success message
                        st.success(f"✅ {calendar_type.title()} calendar for {selected_calendar} updated successfully! All transactions have been recalculated.")
                    else:
                        st.error("Failed to save calendar changes. Please try again.")
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
