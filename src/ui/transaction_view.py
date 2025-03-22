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
from ..utils.helpers import sanitize_html, num_to_words_rupees  # Removed render_html_safely

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
    """
    if not notes:
        return ""
    
    # Sanitize the notes to prevent HTML injection
    sanitized_notes = sanitize_html(notes)
    
    # Format as HTML
    return f"""
    <div style="margin-top: 10px;">
        <p style="color: #a0a0a0; margin-bottom: 5px; font-size: 0.9rem;">Notes</p>
        <p style="color: #e0e0e0; margin-top: 0;">{sanitized_notes}</p>
    </div>
    """

def field_exists(transaction, field):
    """
    Check if a field exists and has a non-empty value in the transaction
    
    Args:
        transaction: The transaction object
        field: The field name to check
        
    Returns:
        bool: True if the field exists and has a value, False otherwise
    """
    return field in transaction and transaction[field]

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
    elif st.session_state.active_tab == "edit_transaction":
        tab_index = 2  # Set to third tab (Edit Transaction)
    
    # Apply enhanced tab styling
    apply_tab_styling()
    
    # Create tabs for different transaction functions - rearranged order with edit tab
    tab1, tab2, tab3 = st.tabs(["📋 All Transactions", "✏️ Add Transaction", "🔄 Edit Transaction"])
    
    # Reset the transaction tab selection after this run
    current_tab = st.session_state.active_tab
    st.session_state.active_tab = "all_transactions"  # Reset to default for next time
    
    # Show the appropriate tab content based on selection
    if tab_index == 0:
        with tab1:
            all_transactions_view(transactions_data, clients_data)
        with tab2:
            transaction_management(transactions_data, clients_data, interest_service)
        with tab3:
            edit_transaction_view(transactions_data, clients_data, interest_service)
    elif tab_index == 2:
        with tab3:
            edit_transaction_view(transactions_data, clients_data, interest_service)
        with tab1:
            all_transactions_view(transactions_data, clients_data)
        with tab2:
            transaction_management(transactions_data, clients_data, interest_service)
    else:
        with tab2:
            transaction_management(transactions_data, clients_data, interest_service)
        with tab1:
            all_transactions_view(transactions_data, clients_data)
        with tab3:
            edit_transaction_view(transactions_data, clients_data, interest_service)

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
    
    # Handle form reset if needed
    if 'reset_transaction_form' not in st.session_state:
        st.session_state.reset_transaction_form = False
    
    # Initialize confirmation state
    if 'show_transaction_confirmation' not in st.session_state:
        st.session_state.show_transaction_confirmation = False
    
    # Initialize transaction data state
    if 'pending_transaction_data' not in st.session_state:
        st.session_state.pending_transaction_data = {}
    
    # If reset flag is set, clear all form-related session state values
    if st.session_state.reset_transaction_form:
        if 'transaction_client_select' in st.session_state:
            del st.session_state.transaction_client_select
        if 'new_transaction_date' in st.session_state:
            del st.session_state.new_transaction_date
        if 'new_transaction_notes' in st.session_state:
            del st.session_state.new_transaction_notes
        st.session_state.show_transaction_confirmation = False
        
        # Reset the flag
        st.session_state.reset_transaction_form = False
    
    # Initialize other session state variables
    if 'amount_in_words' not in st.session_state:
        st.session_state.amount_in_words = ""
    if 'transaction_data' not in st.session_state:
        st.session_state.transaction_data = {}
    
    # Show confirmation screen if needed
    if st.session_state.show_transaction_confirmation:
        client_name = st.session_state.pending_transaction_data.get("client_name", "")
        
        # Define back callback function
        def back_to_form():
            st.session_state.show_transaction_confirmation = False
        
        # Show confirmation screen and get result
        confirm_button = confirm_transaction_screen(
            client_name, 
            st.session_state.pending_transaction_data, 
            back_callback=back_to_form
        )
        
        # If confirmed, add the transaction
        if confirm_button:
            # Add and save transaction
            if "transactions" not in transactions_data:
                transactions_data["transactions"] = []
            
            transactions_data["transactions"].append(st.session_state.pending_transaction_data)
            save_transactions(transactions_data)
            
            # Show success message with details
            st.success(f"""
            ✅ Transaction added successfully!
            
            **Details:**
            - Client: {client_name}
            - Type: {"Received" if st.session_state.pending_transaction_data.get('received', 0) > 0 else "Paid"}
            - Amount: ₹{(st.session_state.pending_transaction_data.get('received', 0) or st.session_state.pending_transaction_data.get('paid', 0)):,.2f}
            - Interest: ₹{abs(st.session_state.pending_transaction_data.get('interest', 0)):,.2f}
            - Calendar: {st.session_state.pending_transaction_data.get('calendar_type')} ({st.session_state.pending_transaction_data.get('days')} days)
            """)
            
            # Reset form for next transaction
            st.session_state.reset_transaction_form = True
            
            # Set session state to control what happens next
            st.session_state.transaction_added = True
            st.session_state.last_action = "add_another"
            
            # Refresh the page to clear the form
            st.rerun()
        
        return
    
    # Create the transaction form
    with st.form("new_transaction_form", clear_on_submit=False):
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
            # Amount input without on_change callback (can't use callbacks in forms)
            amount = st.number_input(
                "Amount (₹)",
                min_value=0.0,
                step=100.0,
                format="%.2f",
                help="Transaction amount",
                key="transaction_amount"
            )
            
            # Display amount in words in real-time
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
        
        # Submit button - renamed to Review Transaction
        submit_button = st.form_submit_button(
            "Review Transaction", 
            use_container_width=True,
            type="primary"
        )
    
    # If submit button is clicked, show confirmation
    if submit_button:
        # Validate amount
        if amount <= 0:
            st.error("❌ Amount must be greater than zero.")
            return
            
        # Calculate everything for the transaction
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
        transaction_data = {
            "id": len(transactions_data.get("transactions", [])) + 1,
            "client_id": client_id,
            "client_name": selected_client,
            "date": date_str,
            "received": float(amount) if transaction_type == "Received" else 0.0,
            "paid": float(amount) if transaction_type == "Paid" else 0.0,
            "amount_in_words": num_to_words_rupees(amount),
            "interest_rate": float(interest_rate_pct),
            "calendar_type": calendar_type,
            "days": int(days_value) if days_value is not None else 0,
            "interest": round(float(interest), 2),
            "notes": notes,
        }
        
        # Store the transaction data in session state for confirmation
        st.session_state.pending_transaction_data = transaction_data
        
        # Show confirmation screen
        st.session_state.show_transaction_confirmation = True
        
        # Refresh the page to show confirmation
        st.rerun()

def edit_transaction_view(transactions_data, clients_data, interest_service):
    """UI component for editing existing transactions."""
    if not transactions_data.get("transactions"):
        st.info("💼 No transactions recorded yet. Add your first transaction in the 'Add Transaction' section.")
        return
    
    st.markdown("""
    <div style="background-color:#0a0a0a; padding:1rem; border-radius:0.5rem; border-left:4px solid #1a1a1a;">
        <p style="margin:0; color:#e0e0e0;">Edit an existing transaction by selecting it below.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create DataFrame with client names for selection
    df = pd.DataFrame(transactions_data["transactions"])
    df["date"] = pd.to_datetime(df["date"])
    
    # Add client names
    client_map = {c["id"]: c["name"] for c in clients_data.get("clients", [])}
    df["client_name"] = df["client_id"].map(client_map)
    
    # Sort by date (newest first)
    df = df.sort_values("date", ascending=False)
    
    # Create a selection field that shows relevant transaction info
    transaction_options = []
    for i, row in df.iterrows():
        trans_type = "Received" if row.get("received", 0) > 0 else "Paid"
        amount = row.get("received", 0) if trans_type == "Received" else row.get("paid", 0)
        date_str = row["date"].strftime("%d %b %Y")
        client_name = row.get("client_name", "Unknown")
        option_text = f"{date_str} - {client_name} - {trans_type} ₹{amount:,.2f}"
        transaction_options.append({"label": option_text, "value": row.get("id")})
    
    # Select transaction to edit
    selected_transaction_id = st.selectbox(
        "Select Transaction to Edit",
        options=[opt["value"] for opt in transaction_options],
        format_func=lambda x: next((opt["label"] for opt in transaction_options if opt["value"] == x), ""),
        key="edit_transaction_select"
    )
    
    if selected_transaction_id:
        # Get the selected transaction
        selected_transaction = next(
            (t for t in transactions_data["transactions"] if t.get("id") == selected_transaction_id),
            None
        )
        
        if not selected_transaction:
            st.error("Transaction not found!")
            return
        
        # Get the client
        client = next(
            (c for c in clients_data["clients"] if c.get("id") == selected_transaction.get("client_id")),
            None
        )
        
        client_name = client.get("name", "Unknown") if client else "Unknown"
        
        # Initialize form values
        is_received = selected_transaction.get("received", 0) > 0
        transaction_type = "Received" if is_received else "Paid"
        amount = selected_transaction.get("received", 0) if is_received else selected_transaction.get("paid", 0)
        
        st.markdown("### Edit Transaction")
        
        # Create the edit form
        with st.form("edit_transaction_form"):
            # Columns for form inputs
            col1, col2, col3 = st.columns([1.2, 1, 0.8])
            
            with col1:
                # Convert the date string to datetime object
                date_value = datetime.strptime(selected_transaction.get("date", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d")
                
                new_date = st.date_input(
                    "Transaction Date", 
                    date_value, 
                    key="edit_transaction_date"
                )
                
                transaction_type = st.selectbox(
                    "Transaction Type",
                    ["Received", "Paid"],
                    index=0 if is_received else 1,
                    key="edit_transaction_type"
                )
                
                calendar_type = st.selectbox(
                    "Calendar Type",
                    ["Diwali", "Financial"],
                    index=0 if selected_transaction.get("calendar_type") == "Diwali" else 1,
                    key="edit_calendar_type"
                )
                
                interest_rate_pct = st.number_input(
                    "Interest Rate (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(selected_transaction.get("interest_rate", 5.0)),
                    step=0.25,
                    key="edit_interest_rate"
                )
            
            with col2:
                # Amount input
                edit_amount = st.number_input(
                    "Amount (₹)",
                    min_value=0.0,
                    value=float(amount),
                    step=100.0,
                    format="%.2f",
                    key="edit_amount"
                )
                
                # Display amount in words
                if edit_amount > 0:
                    amount_in_words = num_to_words_rupees(edit_amount)
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
                    value=selected_transaction.get("notes", ""),
                    height=205,
                    key="edit_transaction_notes"
                )
            
            # Submit button
            update_button = st.form_submit_button(
                "Update Transaction", 
                use_container_width=True,
                type="primary"
            )
            
            if update_button:
                if edit_amount <= 0:
                    st.error("❌ Amount must be greater than zero.")
                    return
                    
                # Recalculate interest
                date_str = new_date.strftime("%Y-%m-%d")
                diwali_days, financial_days = interest_service.get_interest_value(date_str)
                
                if calendar_type == "Diwali" and diwali_days is None:
                    st.error("❌ No Diwali calendar days value available for the selected date. Transaction not updated.")
                    return
                elif calendar_type == "Financial" and financial_days is None:
                    st.error("❌ No Financial calendar days value available for the selected date. Transaction not updated.")
                    return
                
                # Calculate interest
                transaction_amount = edit_amount if transaction_type == "Received" else -edit_amount
                
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
                
                # Update transaction
                for i, transaction in enumerate(transactions_data["transactions"]):
                    if transaction.get("id") == selected_transaction_id:
                        transactions_data["transactions"][i].update({
                            "date": date_str,
                            "received": float(edit_amount) if transaction_type == "Received" else 0.0,
                            "paid": float(edit_amount) if transaction_type == "Paid" else 0.0,
                            "amount_in_words": num_to_words_rupees(edit_amount),
                            "interest_rate": float(interest_rate_pct),
                            "calendar_type": calendar_type,
                            "days": int(days_value) if days_value is not None else 0,
                            "interest": round(float(interest), 2),
                            "notes": notes,
                        })
                        break
                
                # Save changes
                save_transactions(transactions_data)
                
                # Show success message
                st.success(f"""
                ✅ Transaction updated successfully!
                
                **Updated Details:**
                - Client: {client_name}
                - Type: {transaction_type}
                - Amount: ₹{edit_amount:,.2f}
                - Interest: ₹{abs(interest):,.2f}
                - Calendar: {calendar_type} ({int(days_value)} days)
                """)
                
        # Add a separate form for deletion to avoid conflicts with the edit form
        st.markdown("<hr style='margin: 2rem 0; border-color: #333;'>", unsafe_allow_html=True)
        st.markdown("### Delete Transaction")
        
        # Warning about deletion
        st.warning("⚠️ **Warning:** Deleting a transaction cannot be undone. This action is permanent.")
        
        # Add deletion form
        with st.form("delete_transaction_form"):
            # Confirmation checkbox
            delete_confirm = st.checkbox(
                "I understand that this action cannot be undone",
                key="delete_transaction_confirm"
            )
            
            # Delete button
            delete_button = st.form_submit_button(
                "Delete Transaction", 
                use_container_width=True, 
                type="primary", 
                help="Permanently delete this transaction"
            )
            
            if delete_button:
                if not delete_confirm:
                    st.error("❌ Please confirm that you understand this action cannot be undone.")
                    return
                
                # Delete the transaction
                transactions_data["transactions"] = [t for t in transactions_data["transactions"] if t.get("id") != selected_transaction_id]
                
                # Save changes
                save_transactions(transactions_data)
                
                # Show success message
                st.success(f"""
                ✅ Transaction deleted successfully!
                
                The transaction for {client_name} on {date_value.strftime("%d %b %Y")} has been permanently removed.
                """)
                
                # Clear the form and reset the view after a short delay
                st.session_state.reset_transaction_form = True
                st.rerun()

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
    
    # Sort by date (oldest first) to calculate running balance properly
    filtered_df = filtered_df.sort_values("date", ascending=True)
    
    # Calculate net amount for each transaction (received - paid)
    filtered_df["net_amount"] = filtered_df["received"] - filtered_df["paid"]
    
    # Calculate running balance for each transaction
    filtered_df["running_balance"] = filtered_df["net_amount"].cumsum()
    
    # Add opening and closing balance for each transaction
    filtered_df["opening_balance"] = filtered_df["running_balance"] - filtered_df["net_amount"]
    filtered_df["closing_balance"] = filtered_df["running_balance"]
    
    # Sort by date descending (most recent first) for display
    filtered_df = filtered_df.sort_values("date", ascending=False)
    
    # Ensure amount_in_words is present for all transactions (for backwards compatibility)
    if 'amount_in_words' not in filtered_df.columns:
        # Use the helper function to calculate amount in words for each transaction
        filtered_df['amount_in_words'] = filtered_df.apply(get_amount_in_words, axis=1)
    
    # Reorder columns to show client name, date, and balance columns
    cols = [
        "client_name",
        "date",
        "opening_balance",
        "received",
        "paid",
        "closing_balance",
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
    final_balance = filtered_df["closing_balance"].iloc[0] if not filtered_df.empty else 0
    
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
        <div>
            <p style="margin:0; font-size:0.9rem; color:#a0a0a0;">Current Balance</p>
            <p style="margin:0; font-weight:bold; color:{('#4ade80' if final_balance >= 0 else '#f87171')};">₹{final_balance:,.2f}</p>
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
            # Calculate running balance for all transactions
            export_df["net_amount"] = export_df["received"] - export_df["paid"]
            export_df = export_df.sort_values("date", ascending=True)
            export_df["running_balance"] = export_df["net_amount"].cumsum()
            export_df["opening_balance"] = export_df["running_balance"] - export_df["net_amount"]
            export_df["closing_balance"] = export_df["running_balance"]
            export_df = export_df.sort_values("date", ascending=False)
            
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
            "opening_balance": st.column_config.NumberColumn("Opening Balance", format="₹%.2f"),
            "received": st.column_config.NumberColumn("Received", format="₹%.2f"),
            "paid": st.column_config.NumberColumn("Paid", format="₹%.2f"),
            "closing_balance": st.column_config.NumberColumn("Closing Balance", format="₹%.2f"),
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

def confirm_transaction_screen(client_name, transaction_data, back_callback=None):
    """Display the transaction confirmation screen."""
    colored_header(
        label="Confirm Transaction Details",
        description="Review and confirm transaction information",
        color_name="gray-40"
    )
    
    # Display transaction details instead of preview
    display_transaction_details(transaction_data, client_name)
    
    # Add a confirmation message with warning styling
    warning_html = """
    <div style="background-color:#121212; padding:1rem; border-radius:0.5rem; border-left:4px solid #f59e0b; margin-bottom:1rem;">
        <p style="margin:0; color:#e0e0e0; font-weight:500;">⚠️ Please review the transaction details carefully before confirming.</p>
    </div>
    """
    
    # Try to use the render_html_safely function if available
    try:
        from src.utils.helpers import render_html_safely
        warning_html = render_html_safely(warning_html)
        st.components.v1.html(warning_html, height=80, scrolling=False)
    except ImportError:
        # Fall back to standard markdown
        st.markdown(warning_html, unsafe_allow_html=True)
    
    # Create buttons for back and confirm
    col1, col2 = st.columns(2)
    
    with col1:
        if back_callback:
            if st.button("Back", use_container_width=True):
                back_callback()
                
    with col2:
        confirm_button = st.button("Confirm Transaction", type="primary", use_container_width=True)
        
    return confirm_button

def transaction_receipt(transaction, client_name):
    """Display a transaction receipt that can be printed or saved."""
    colored_header(
        label="Transaction Receipt",
        description="Transaction has been successfully recorded",
        color_name="green-70"
    )
    
    # Success message
    success_html = """
    <div style="background-color:#052e16; padding:1rem; border-radius:0.5rem; border-left:4px solid #10b981; margin-bottom:1.5rem;">
        <p style="margin:0; color:#d1fae5; font-weight:500;">✅ Transaction has been successfully recorded.</p>
    </div>
    """
    st.markdown(success_html, unsafe_allow_html=True)
    
    # Print receipt button
    if st.button("Print Receipt", use_container_width=True):
        # JavaScript to trigger printing
        js_print = """
        <script>
            window.print();
        </script>
        """
        st.markdown(js_print, unsafe_allow_html=True)
    
    # Display formatted receipt
    receipt_html = f"""
    <div style="background-color:#f8fafc; color:#1e293b; padding:2rem; border-radius:0.5rem; margin:1.5rem 0; max-width:800px; font-family:system-ui,-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
        <div style="text-align:center; margin-bottom:2rem;">
            <h2 style="color:#0f172a; margin-bottom:0.5rem;">Transaction Receipt</h2>
            <p style="color:#64748b; margin:0;">{datetime.now().strftime('%d %b %Y, %I:%M %p')}</p>
        </div>
        
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:1.5rem; margin-bottom:1.5rem;">
            <div>
                <p style="color:#64748b; margin-bottom:0.25rem; font-size:0.875rem;">Client</p>
                <p style="color:#0f172a; font-weight:600; margin-top:0; font-size:1.125rem;">{client_name}</p>
            </div>
            <div>
                <p style="color:#64748b; margin-bottom:0.25rem; font-size:0.875rem;">Date</p>
                <p style="color:#0f172a; font-weight:600; margin-top:0; font-size:1.125rem;">{transaction['date']}</p>
            </div>
        </div>
        
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:1.5rem; margin-bottom:1.5rem;">
            <div>
                <p style="color:#64748b; margin-bottom:0.25rem; font-size:0.875rem;">Transaction Type</p>
                <p style="color:#0f172a; font-weight:600; margin-top:0; font-size:1.125rem;">
                    {"Received" if transaction.get('received', 0) > 0 else "Paid"}
                </p>
            </div>
            <div>
                <p style="color:#64748b; margin-bottom:0.25rem; font-size:0.875rem;">Amount</p>
                <p style="color:{'#047857' if transaction.get('received', 0) > 0 else '#b91c1c'}; font-weight:600; margin-top:0; font-size:1.125rem;">
                    ₹{transaction.get('received', 0) if transaction.get('received', 0) > 0 else transaction.get('paid', 0):,.2f}
                </p>
            </div>
        </div>
        
        {f'''
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:1.5rem; margin-bottom:1.5rem;">
            <div>
                <p style="color:#64748b; margin-bottom:0.25rem; font-size:0.875rem;">Interest Rate</p>
                <p style="color:#0f172a; font-weight:600; margin-top:0; font-size:1.125rem;">{transaction.get('interest_rate', 0)}%</p>
            </div>
            <div>
                <p style="color:#64748b; margin-bottom:0.25rem; font-size:0.875rem;">Calendar</p>
                <p style="color:#0f172a; font-weight:600; margin-top:0; font-size:1.125rem;">{transaction.get('calendar_type', 'N/A')}</p>
            </div>
        </div>
        
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:1.5rem; margin-bottom:1.5rem;">
            <div>
                <p style="color:#64748b; margin-bottom:0.25rem; font-size:0.875rem;">Days</p>
                <p style="color:#0f172a; font-weight:600; margin-top:0; font-size:1.125rem;">{transaction.get('days', 'N/A')}</p>
            </div>
            <div>
                <p style="color:#64748b; margin-bottom:0.25rem; font-size:0.875rem;">Interest</p>
                <p style="color:#2563eb; font-weight:600; margin-top:0; font-size:1.125rem;">₹{transaction.get('interest', 0):,.2f}</p>
            </div>
        </div>
        ''' if transaction.get('interest') is not None else ''}
        
        {f'''
        <div style="margin-bottom:1.5rem;">
            <p style="color:#64748b; margin-bottom:0.25rem; font-size:0.875rem;">Notes</p>
            <p style="color:#0f172a; margin-top:0;">{sanitize_html(transaction.get('notes', 'No notes'))}</p>
        </div>
        ''' if transaction.get('notes') else ''}
        
        {f'''
        <div style="margin-top:1.5rem; padding-top:1.5rem; border-top:1px solid #e2e8f0;">
            <p style="color:#64748b; margin-bottom:0.25rem; font-size:0.875rem;">Amount in Words</p>
            <p style="color:#0f172a; margin-top:0; font-style:italic;">{transaction.get('amount_in_words', '')}</p>
        </div>
        ''' if transaction.get('amount_in_words') else ''}
        
        <div style="text-align:center; margin-top:3rem; padding-top:1.5rem; border-top:1px dashed #e2e8f0;">
            <p style="color:#64748b; margin:0; font-size:0.875rem;">This is a system-generated receipt.</p>
        </div>
    </div>
    """
    
    st.markdown(receipt_html, unsafe_allow_html=True)
    
    # Add buttons for navigation
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Back to Transactions", use_container_width=True):
            st.session_state.page = "transactions"
            st.session_state.receipt_view = False
            st.session_state.nav_changed = True
            
    with col2:
        if st.button("Add Another Transaction", type="primary", use_container_width=True):
            st.session_state.page = "transactions"
            st.session_state.receipt_view = False
            st.session_state.add_transaction_mode = True
            st.session_state.nav_changed = True

def display_transaction_details(transaction, client_name):
    """Display detailed information about a transaction."""
    # Create a styled container for the transaction details with additional background styling
    transaction_html = f"""
    <div style="background-color:#121212; padding:1.5rem; border-radius:0.8rem; margin-bottom:1.5rem; box-shadow:0 4px 8px rgba(0,0,0,0.2); position:relative;">
        <div style="position:absolute; inset:0; border-radius:0.8rem; padding:1.5px; background:linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.95), rgba(255,255,255,0.1)); -webkit-mask:linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0); -webkit-mask-composite:xor; mask-composite:exclude; pointer-events:none;"></div>
        
        <h2 style="color:#e0e0e0; margin-top:0;">Transaction Details</h2>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 10px;">
            <div>
                <p style="color: #a0a0a0; margin-bottom: 5px; font-size: 0.9rem;">Client</p>
                <p style="color: #e0e0e0; font-weight: 500; margin-top: 0;">{client_name}</p>
            </div>
            <div>
                <p style="color: #a0a0a0; margin-bottom: 5px; font-size: 0.9rem;">Date</p>
                <p style="color: #e0e0e0; font-weight: 500; margin-top: 0;">{transaction['date']}</p>
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 10px;">
            <div>
                <p style="color: #a0a0a0; margin-bottom: 5px; font-size: 0.9rem;">Transaction Type</p>
                <p style="color: #e0e0e0; font-weight: 500; margin-top: 0;">{"Received" if transaction.get('received', 0) > 0 else "Paid"}</p>
            </div>
            <div>
                <p style="color: #a0a0a0; margin-bottom: 5px; font-size: 0.9rem;">Amount</p>
                <p style="color: {"#4ade80" if transaction.get('received', 0) > 0 else "#f87171"}; font-weight: 500; margin-top: 0;">₹{transaction.get('received', 0) if transaction.get('received', 0) > 0 else transaction.get('paid', 0):,.2f}</p>
            </div>
        </div>
        
        {f'''
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 10px;">
            <div>
                <p style="color: #a0a0a0; margin-bottom: 5px; font-size: 0.9rem;">Interest Rate</p>
                <p style="color: #e0e0e0; font-weight: 500; margin-top: 0;">{transaction.get('interest_rate', 0)}%</p>
            </div>
            <div>
                <p style="color: #a0a0a0; margin-bottom: 5px; font-size: 0.9rem;">Calendar</p>
                <p style="color: #e0e0e0; font-weight: 500; margin-top: 0;">{transaction.get('calendar_type', 'N/A')}</p>
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 10px;">
            <div>
                <p style="color: #a0a0a0; margin-bottom: 5px; font-size: 0.9rem;">Days</p>
                <p style="color: #e0e0e0; font-weight: 500; margin-top: 0;">{transaction.get('days', 'N/A')}</p>
            </div>
            <div>
                <p style="color: #a0a0a0; margin-bottom: 5px; font-size: 0.9rem;">Interest</p>
                <p style="color: #4b6bfb; font-weight: 500; margin-top: 0;">₹{transaction.get('interest', 0):,.2f}</p>
            </div>
        </div>
        ''' if transaction.get('interest') is not None else ''}
        
        {f'''
        <div style="margin-top: 10px;">
            <p style="color: #a0a0a0; margin-bottom: 5px; font-size: 0.9rem;">Notes</p>
            <p style="color: #e0e0e0; margin-top: 0;">{sanitize_html(transaction.get('notes', 'No notes'))}</p>
        </div>
        ''' if transaction.get('notes') else ''}
        
        {f'''
        <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #2a2a2a;">
            <p style="color: #a0a0a0; margin-bottom: 5px; font-size: 0.9rem;">Amount in Words</p>
            <p style="color: #e0e0e0; margin-top: 0; font-style: italic;">{transaction.get('amount_in_words', '')}</p>
        </div>
        ''' if transaction.get('amount_in_words') else ''}
    </div>
    """
    
    # Try to import the render_html_safely function from helpers
    try:
        from src.utils.helpers import render_html_safely
        # Use the safer render function if available
        transaction_html = render_html_safely(transaction_html)
    except ImportError:
        # If function not available, clean up HTML directly
        import re
        # Remove excess whitespace and newlines between tags to improve rendering
        transaction_html = re.sub(r'>\s+<', '><', transaction_html.strip())
    
    # Add table styling separately
    st.markdown("""
    <style>
    /* Table styling */
    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 1.2rem !important;
    }
    
    th, td {
        padding: 12px 16px;
        text-align: left;
        font-size: 1.2rem !important;
        line-height: 1.4;
    }
    
    th {
        font-weight: 600;
        background-color: #121212;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Use an alternative approach by embedding in HTML components
    st.components.v1.html(transaction_html, height=550, scrolling=False)
