import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re
from streamlit_extras.colored_header import colored_header
from streamlit_extras.card import card
from io import BytesIO
import streamlit.components.v1 as components
from ..models.transaction import Transaction
from ..models.client import Client
from ..services.interest_service import InterestService
from ..data.data_loader import save_transactions
from ..utils.helpers import sanitize_html, num_to_words_rupees, render_html_safely  # Import the new function

def apply_tab_styling():
    """Apply enhanced tab styling to Streamlit tabs."""
    st.markdown("""
    <style>
    /* Fix for duplicate highlight bars - explicitly target and hide all */
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }
    
    /* Add a custom border-bottom to the selected tab to replace the highlight */
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: rgba(45, 45, 60, 0.7) !important;
        color: #ffffff !important;
        font-weight: 700 !important; /* Increased weight for selected tab */
        border-bottom: 3px solid #4b6bfb !important; /* Blue highlight */
        box-shadow: 0 -10px 20px rgba(75, 107, 251, 0.1) !important;
        transition: all 0.3s ease !important;
    }
    
    /* Style for all tabs to make them more visible */
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px !important;
        border-radius: 5px 5px 0 0 !important;
        margin-right: 5px !important;
        border: 1px solid rgba(75, 75, 90, 0.2) !important;
        border-bottom: none !important;
        background-color: rgba(25, 25, 35, 0.4) !important;
        transition: all 0.2s ease !important;
        font-weight: 600 !important; /* Make all tab text bold */
        font-size: 1.05rem !important; /* Slightly larger font size */
    }
    
    /* More specific rules for the tab text to ensure it's bold */
    .stTabs [data-baseweb="tab"] div[data-testid="stMarkdownContainer"] p,
    .stTabs [data-baseweb="tab"] div,
    .stTabs [data-baseweb="tab"] span {
        font-weight: 700 !important; /* Definitely bold */
        font-family: 'Geist Mono', monospace !important; /* Consistent font */
    }
    
    /* Explicitly target the text elements inside tabs */
    .stTabs button[role="tab"] span,
    .stTabs button[role="tab"] p {
        font-weight: 800 !important; /* Extra bold */
        letter-spacing: 0.02em !important; /* Slightly increase letter spacing */
    }
    
    /* Hover effect for tabs */
    .stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
        background-color: rgba(35, 35, 50, 0.6) !important;
        color: #e0e0e0 !important;
        border-bottom: 1px solid rgba(75, 107, 251, 0.3) !important;
    }
    
    /* Ensure no extra borders around tabs */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 1px solid #333340 !important;
        padding-bottom: 0 !important;
        margin-bottom: 20px !important;
    }
    
    /* Add a subtle glow to active tab */
    .stTabs [data-baseweb="tab"][aria-selected="true"]::after {
        content: "";
        position: absolute;
        bottom: -3px;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, rgba(75, 107, 251, 0.3), rgba(75, 107, 251, 0.8), rgba(75, 107, 251, 0.3));
        border-radius: 3px;
    }
    </style>
    """, unsafe_allow_html=True)

def get_amount_in_words(row):
    """
    Convert transaction amount to words.
    
    Handles both received and paid transactions by picking the non-zero amount.
    Returns formatted amount in words using the num_to_words_rupees function.
    
    Args:
        row (pd.Series): A pandas Series representing a transaction row
        
    Returns:
        str: The amount formatted in words
    """
    # Check for received amount first, then paid amount
    if 'received' in row and row['received'] > 0:
        amount = row['received']
    elif 'paid' in row and row['paid'] > 0:
        amount = row['paid']
    else:
        # Default to 0 if neither received nor paid has a value
        amount = 0
    
    return num_to_words_rupees(amount)

def sanitize_notes(notes):
    """
    Prepare notes for display in HTML
    
    Args:
        notes: The notes text to prepare for HTML display
        
    Returns:
        str: Notes text properly prepared for HTML display
    """
    if not notes:
        return ""
        
    # Convert to string if not already
    notes_text = str(notes).strip()
    
    # Check if the content already contains HTML
    if notes_text.startswith('<div') or notes_text.startswith('<p') or '<div' in notes_text or '<span' in notes_text:
        # If it already has HTML, return it directly for rendering
        return notes_text
    else:
        # If it's just plain text, format it nicely
        try:
            formatted_text = sanitize_html(notes_text, is_html=False)
            return f"""<div style="color: #e0e0e0; background-color: rgba(30, 30, 40, 0.5); padding: 8px; border-radius: 4px; white-space: pre-wrap;">{formatted_text}</div>"""
        except (ImportError, AttributeError):
            # Fallback
            notes_text = notes_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            notes_text = notes_text.replace('\n', '<br>')
            return f"""<div style="color: #e0e0e0; background-color: rgba(30, 30, 40, 0.5); padding: 8px; border-radius: 4px; white-space: pre-wrap;">{notes_text}</div>"""

def transactions_section(transactions_data, clients_data, interest_calendars, interest_service):
    """Transaction management UI component."""
    colored_header(
        label="Transactions Management",
        description="View and manage your transactions",
        color_name="gray-40"
    )
    
    # Initialize transaction tab session state if not already set
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "all_transactions"  # Default to all transactions tab
    
    # If coming from client view, switch to all transactions tab
    if st.session_state.get("view_client_transactions") is not None:
        st.session_state.active_tab = "all_transactions"
    
    # Determine which tab should be active
    tab_index = 1  # Default to second tab (All Transactions)
    if st.session_state.active_tab == "add_transaction":
        tab_index = 0  # Set to first tab (Add Transaction)
    
    # Apply enhanced tab styling
    apply_tab_styling()
    
    # Create tabs for different transaction functions - rearranged order
    tab1, tab2 = st.tabs(["📋 All Transactions", "✏️ Add Transaction"])
    
    # Reset the transaction tab selection after this run
    current_tab = st.session_state.active_tab
    st.session_state.active_tab = "all_transactions"  # Reset to default for next time
    
    # Show the appropriate tab content based on selection
    if tab_index == 0:
        with tab1:
            all_transactions_view(transactions_data, clients_data)
        with tab2:
            transaction_management(transactions_data, clients_data, interest_service)
    else:
        with tab2:
            transaction_management(transactions_data, clients_data, interest_service)
        with tab1:
            all_transactions_view(transactions_data, clients_data)

def transaction_management(transactions_data, clients_data, interest_service):
    """UI component for adding new transactions."""
    st.markdown("""
    <div style="background-color:#0a0a0a; padding:1rem; border-radius:0.5rem; border-left:4px solid #1a1a1a;">
        <p style="margin:0; color:#e0e0e0;">Create a new transaction below. Select a client and enter the transaction details.</p>
    </div>
    """, unsafe_allow_html=True)
    
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
        col1, col2, col3 = st.columns([1.2, 1, 0.8])
        
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
        
        with col2:
            # Amount input with proper spacing
            amount = st.number_input(
                "Amount (₹)",
                min_value=0.0,
                step=100.0,
                format="%.2f",
                help="Transaction amount",
                key="transaction_amount"
            )
            
            # Display amount in words with better styling
            if amount > 0:
                amount_in_words = num_to_words_rupees(amount)
                st.markdown("""
                <div style='background-color: rgba(15, 15, 20, 0.7); 
                            padding: 12px 15px; 
                            border-radius: 6px; 
                            border: 1px solid rgba(25, 25, 30, 0.8);
                            margin: 8px 0;'>
                    <div style='color: #a0a0a0; font-size: 0.85em; margin-bottom: 4px;">Amount in words</div>
                    <div style='color: #e0e0e0; font-size: 0.95em; line-height: 1.4;'>{}</div>
                </div>
                """.format(amount_in_words), unsafe_allow_html=True)
        
        with col3:
            notes = st.text_area(
                "Notes",
                key="new_transaction_notes",
                height=205,  # Adjusted height to match other columns
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
            diwali_days, financial_days = interest_service.get_interest_value(date_str)
            
            if calendar_type == "Diwali" and diwali_days is None:
                st.error("❌ No Diwali calendar days value available for the selected date. Transaction not added.")
                return
            elif calendar_type == "Financial" and financial_days is None:
                st.error("❌ No Financial calendar days value available for the selected date. Transaction not added.")
                return
            
            # Calculate interest
            transaction_amount = amount if transaction_type == "Received" else -amount
            
            if calendar_type == "Diwali":
                interest = interest_service.calculate_interest(abs(transaction_amount), interest_rate_pct, diwali_days, "Diwali")
                if transaction_type == "Paid":
                    interest = -interest
                days_value = diwali_days
            else:  # Financial
                interest = interest_service.calculate_interest(abs(transaction_amount), interest_rate_pct, financial_days, "Financial")
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
                "amount_in_words": num_to_words_rupees(amount),
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
            - Amount in Words: {num_to_words_rupees(amount)}
            - Interest: ₹{interest:,.2f}
            - Calendar: {calendar_type} ({int(days_value)} days)
            """)
            
            # Set session state to control what happens next
            st.session_state.transaction_added = True
            st.session_state.last_action = "add_another"  # Default action

def all_transactions_view(transactions_data, clients_data):
    """UI component for viewing all transactions."""
    if not transactions_data.get("transactions"):
        st.info("💼 No transactions recorded yet. Add your first transaction in the 'Add Transaction' section.")
        return
    
    # Create DataFrame with client names
    df = pd.DataFrame(transactions_data["transactions"])
    df["date"] = pd.to_datetime(df["date"])
    
    # Add client names
    client_map = {c["id"]: c["name"] for c in clients_data.get("clients", [])}
    df["client_name"] = df["client_id"].map(client_map)
    
    # Check if we need to filter by specific client (from VIEW TRANSACTIONS button)
    view_client_id = st.session_state.get("view_client_transactions")
    
    # Create filter section with nice styling
    st.markdown("""
    <div style="background-color:#0a0a0a; padding:1rem; border-radius:0.5rem; margin-bottom:1.5rem; border:1px solid #1a1a1a;">
        <h3 style="margin-top:0; margin-bottom:0.5rem; color:#e0e0e0; font-size:1.1rem;">Filter Transactions</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state for filters if not already set
    if 'transaction_filters' not in st.session_state:
        st.session_state.transaction_filters = {
            'client_filter': [],
            'calendar_filter': [],
            'transaction_type_filter': [],
            'min_amount': 0.0,
            'max_amount': float(df[["received", "paid"]].max().max() * 1.5) if not df.empty else 10000.0,
            'start_date': min(df["date"]).date() if not df.empty else datetime.now().date() - timedelta(days=30),
            'end_date': max(df["date"]).date() if not df.empty else datetime.now().date(),
            'filters_applied': False
        }
    
    # If view_client_id is set, pre-filter for that client
    client_name_to_filter = None
    if view_client_id and view_client_id in client_map:
        client_name_to_filter = client_map[view_client_id]
        # Display which client we're filtering for
        st.info(f"Showing transactions for client: {client_name_to_filter}")
        
        # Automatically apply the filter by updating session state
        st.session_state.transaction_filters['client_filter'] = [client_name_to_filter]
        st.session_state.transaction_filters['filters_applied'] = True
        
        # Clear the filter trigger once used
        st.session_state.view_client_transactions = None
    
    # Place all non-date filters on a single line (5 columns)
    filt_col1, filt_col2, filt_col3, filt_col4, filt_col5 = st.columns([2, 1, 1, 1, 1])
    
    with filt_col1:
        # Multi-select for clients
        client_filter = st.multiselect(
            "Client", 
            options=sorted(df["client_name"].unique()),
            default=st.session_state.transaction_filters['client_filter'],
            placeholder="All Clients",
            key="client_filter_select"
        )
    
    with filt_col2:
        # Calendar type filter
        calendar_filter = st.multiselect(
            "Calendar Type", 
            options=["Diwali", "Financial"],
            default=st.session_state.transaction_filters['calendar_filter'],
            placeholder="All Calendars",
            key="calendar_filter_select"
        )
    
    with filt_col3:
        # Transaction type filter (Received/Paid)
        transaction_type_filter = st.multiselect(
            "Transaction Type", 
            options=["Received", "Paid"],
            default=st.session_state.transaction_filters['transaction_type_filter'],
            placeholder="All Types",
            key="transaction_type_filter_select"
        )
    
    with filt_col4:
        # Min amount filter
        min_amount = st.number_input(
            "Min Amount", 
            value=st.session_state.transaction_filters['min_amount'], 
            format="%.2f",
            key="min_amount_input"
        )
    
    with filt_col5:
        # Max amount filter
        max_amount = st.number_input(
            "Max Amount", 
            value=st.session_state.transaction_filters['max_amount'],
            format="%.2f",
            key="max_amount_input"
        )
    
    # Date range filter on a separate line
    date_col1, date_col2 = st.columns(2)
    with date_col1:
        start_date = st.date_input(
            "From Date (DD/MM/YYYY)",  # Include format in the label itself
            value=st.session_state.transaction_filters['start_date'],
            key="all_trans_start_date",
            format="DD/MM/YYYY"  # Keep the format specification
        )
    with date_col2:
        end_date = st.date_input(
            "To Date (DD/MM/YYYY)",  # Include format in the label itself
            value=st.session_state.transaction_filters['end_date'],
            key="all_trans_end_date",
            format="DD/MM/YYYY"  # Keep the format specification
        )
    
    # Add apply and reset filter buttons
    filter_btn_col1, filter_btn_col2 = st.columns([1, 5])
    with filter_btn_col1:
        apply_filter = st.button("Apply Filters", type="primary", key="apply_transaction_filters")
        
    with filter_btn_col2:
        reset_filter = st.button("Reset Filters", key="reset_transaction_filters")
        
    # Update session state if Apply button is clicked
    if apply_filter:
        st.session_state.transaction_filters = {
            'client_filter': client_filter,
            'calendar_filter': calendar_filter,
            'transaction_type_filter': transaction_type_filter,
            'min_amount': min_amount,
            'max_amount': max_amount,
            'start_date': start_date,
            'end_date': end_date,
            'filters_applied': True
        }
        
    # Reset filters if Reset button is clicked
    if reset_filter:
        st.session_state.transaction_filters = {
            'client_filter': [],
            'calendar_filter': [],
            'transaction_type_filter': [],
            'min_amount': 0.0,
            'max_amount': float(df[["received", "paid"]].max().max() * 1.5) if not df.empty else 10000.0,
            'start_date': min(df["date"]).date() if not df.empty else datetime.now().date() - timedelta(days=30),
            'end_date': max(df["date"]).date() if not df.empty else datetime.now().date(),
            'filters_applied': True
        }
    
    # Apply filters - but only use session state values for consistency
    filtered_df = df.copy()
    
    # Apply filters only if they have been set before
    if st.session_state.transaction_filters['filters_applied']:
        # Use filter values from session state
        client_filter = st.session_state.transaction_filters['client_filter']
        calendar_filter = st.session_state.transaction_filters['calendar_filter']
        transaction_type_filter = st.session_state.transaction_filters['transaction_type_filter']
        min_amount = st.session_state.transaction_filters['min_amount']
        max_amount = st.session_state.transaction_filters['max_amount']
        start_date = st.session_state.transaction_filters['start_date']
        end_date = st.session_state.transaction_filters['end_date']
        
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
        
        # Amount filter - improved logic to properly filter by amount
        # Create a new column for effective amount (either received or paid)
        filtered_df["effective_amount"] = filtered_df.apply(
            lambda x: x["received"] if x["received"] > 0 else x["paid"], 
            axis=1
        )
        
        # Now filter based on the effective amount
        filtered_df = filtered_df[
            (filtered_df["effective_amount"] >= min_amount) & 
            (filtered_df["effective_amount"] <= max_amount)
        ]
        
        # Date filter
        filtered_df = filtered_df[
            (filtered_df["date"].dt.date >= start_date) & 
            (filtered_df["date"].dt.date <= end_date)
        ]
    
    # Sort by date descending (most recent first)
    filtered_df = filtered_df.sort_values("date", ascending=False)
    
    # Ensure amount_in_words is present for all transactions (for backwards compatibility)
    if 'amount_in_words' not in filtered_df.columns:
        # Use the helper function to calculate amount in words for each transaction
        filtered_df['amount_in_words'] = filtered_df.apply(get_amount_in_words, axis=1)
    
    # Reorder columns to show client name first
    cols = [
        "client_name",
        "date",
        "received",
        "paid",
        "amount_in_words",
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
    
    # Show transaction summary
    st.markdown(f"""
    <div style="background-color:#0a0a0a; padding:1rem; border-radius:0.5rem; margin:1.5rem 0; display:flex; justify-content:space-between; border:1px solid #1a1a1a;">
        <div>
            <p style="margin:0; font-size:0.9rem; color:#a0a0a0;">Transactions</p>
            <p style="margin:0; font-weight:bold; color:#e0e0e0;">{total_transactions:,}</p>
        </div>
        <div>
            <p style="margin:0; font-size:0.9rem; color:#a0a0a0;">Total Received</p>
            <p style="margin:0; font-weight:bold; color:#4ade80;">₹{total_received:,.2f}</p>
        </div>
        <div>
            <p style="margin:0; font-size:0.9rem; color:#a0a0a0;">Total Paid</p>
            <p style="margin:0; font-weight:bold; color:#f87171;">₹{total_paid:,.2f}</p>
        </div>
        <div>
            <p style="margin:0; font-size:0.9rem; color:#a0a0a0;">Total Interest</p>
            <p style="margin:0; font-weight:bold; color:#4b6bfb;">₹{total_interest:,.2f}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Export transactions functionality
    with st.expander("**💾 Export Transactions**", expanded=False):
        st.markdown("""
        <div style="background-color:#252532; padding:12px; border-radius:5px; margin-bottom:15px;">
            <p style="color:#e0e0e0; margin:0; font-weight:500;">
                Export transactions to a CSV file for record keeping, reporting, or backup purposes.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        export_col1, export_col2 = st.columns([1, 1])
        
        with export_col1:
            export_format = st.selectbox(
                "Export Format",
                ["CSV", "Excel"],
                key="export_format"
            )
        
        with export_col2:
            what_to_export = st.radio(
                "What to Export",
                ["Current Filtered Transactions", "All Transactions"],
                horizontal=True,
                key="what_to_export"
            )
        
        # Create the export file
        if what_to_export == "Current Filtered Transactions":
            export_df = filtered_df.copy()
        else:  # All Transactions
            export_df = df.copy()
            # Apply the amount_in_words logic to all transactions too
            if 'amount_in_words' not in export_df.columns:
                # Use the shared helper function 
                export_df['amount_in_words'] = export_df.apply(get_amount_in_words, axis=1)
        
        # Format the date column for the export
        export_df['date'] = export_df['date'].dt.strftime('%d %b %Y')
        
        # Convert to the proper format
        if export_format == "CSV":
            export_data = export_df.to_csv(index=False)
            file_extension = "csv"
            mime_type = "text/csv"
        else:  # Excel
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                export_df.to_excel(writer, index=False, sheet_name="Transactions")
                writer.save()
            export_data = buffer.getvalue()
            file_extension = "xlsx"
            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        # Download button
        st.download_button(
            label=f"📥 Download {export_format} ({len(export_df)} transactions)",
            data=export_data,
            file_name=f"transactions_export_{datetime.now().strftime('%Y%m%d')}.{file_extension}",
            mime=mime_type,
            use_container_width=True
        )
    
    # Warn if no transactions match filters
    if filtered_df.empty:
        st.warning("No transactions match the selected filters.")
        return
    
    # Display transactions in table view
    # Custom CSS for table styling
    st.markdown("""
    <style>
    /* Transaction table specific styling */
    div[data-testid="stDataFrame"] table {
        font-family: 'Geist Mono', monospace !important;
        font-size: 1.2rem !important;
    }
    
    div[data-testid="stDataFrame"] th,
    div[data-testid="stDataFrame"] td {
        font-family: 'Geist Mono', monospace !important;
        font-size: 1.2rem !important;
        padding: 12px 16px !important;
        line-height: 1.4 !important;
    }
    
    /* Force CSS for table cells */
    .cell-text-container {
        font-family: 'Geist Mono', monospace !important;
        font-size: 1.2rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display as a table
    st.dataframe(
        filtered_df,
        column_config={
            "client_name": "Client",
            "date": st.column_config.DateColumn("Date", format="DD MMM YYYY"),
            "received": st.column_config.NumberColumn("Received", format="₹%.2f"),
            "paid": st.column_config.NumberColumn("Paid", format="₹%.2f"),
            "amount_in_words": "Amount in Words",
            "interest_rate": st.column_config.NumberColumn("Interest Rate", format="%.2f%%"),
            "calendar_type": "Calendar Type",
            "days": "Days",
            "interest": st.column_config.NumberColumn("Interest", format="₹%.2f"),
            "notes": "Notes"
        },
        hide_index=True,
        use_container_width=True
    )
