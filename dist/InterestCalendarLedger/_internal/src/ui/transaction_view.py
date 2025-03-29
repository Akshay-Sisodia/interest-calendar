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
from ..data.data_loader import save_transactions, load_transactions
from ..utils.helpers import sanitize_html, num_to_words_rupees  # Removed render_html_safely

def import_transactions_from_excel(uploaded_file, client_id, interest_calendars, interest_service, transactions_data):
    """Import transactions from an Excel file."""
    try:
        # Read the Excel file
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, header=0)
        else:
            df = pd.read_excel(uploaded_file, header=0)
        
        # Drop rows where all values are NaN
        df = df.dropna(how='all')
        
        # Initialize list for new transactions
        new_transactions = []
        next_id = max([t.get("id", 0) for t in transactions_data["transactions"]], default=0) + 1
        
        # Determine calendar type from the first valid entry
        calendar_type = None
        
        # Process each row except the last two summary rows
        for idx, row in df.iloc[:-2].iterrows():
            try:
                # Skip rows with no date
                if pd.isna(row.iloc[0]):
                    continue
                
                # Convert date to string format, ensuring dd-mm-yyyy interpretation
                try:
                    # First try parsing as dd-mm-yyyy
                    date_val = pd.to_datetime(row.iloc[0], format='%d-%m-%Y')
                except:
                    try:
                        # If that fails, try parsing as dd/mm/yyyy
                        date_val = pd.to_datetime(row.iloc[0], format='%d/%m/%Y')
                    except:
                        try:
                            # If both fail, let pandas try to parse it but force day-first
                            date_val = pd.to_datetime(row.iloc[0], dayfirst=True)
                        except:
                            st.warning(f"Error parsing date in row {idx + 1}. Using original date.")
                            date_val = pd.to_datetime(row.iloc[0])
                
                date_str = date_val.strftime('%Y-%m-%d')
                
                # Get transaction amounts
                issue_amount = float(row['Issue']) if not pd.isna(row['Issue']) else 0.0
                receipt_amount = float(row['Receipt']) if not pd.isna(row['Receipt']) else 0.0
                
                # Get interest days
                days = int(float(row['No of Days'])) if not pd.isna(row['No of Days']) else 0
                
                # Get monthly interest rate from the last column and convert to annual rate
                monthly_rate = float(row.iloc[-1]) if not pd.isna(row.iloc[-1]) else 0.0
                annual_interest_rate = monthly_rate * 12
                
                # Determine calendar type only for the first valid entry
                if calendar_type is None:
                    # In most cases:
                    # - Diwali calendar uses a base of 360 days
                    # - Financial calendar uses a base of 365 days
                    # We'll use a heuristic based on the days value
                    if days <= 360:
                        calendar_type = "Diwali"
                    else:
                        calendar_type = "Financial"
                    
                    st.info(f"Using {calendar_type} calendar for all imported transactions based on the first entry.")
                
                # Create transaction for paid amount (Issue)
                if issue_amount > 0:
                    # Calculate interest for paid amount
                    interest = interest_service.calculate_interest(
                        issue_amount,
                        annual_interest_rate,
                        days,
                        calendar_type  # Using determined calendar type
                    )
                    interest = -abs(interest)  # Make it negative for paid interest
                    
                    transaction = {
                        "id": next_id,
                        "client_id": client_id,
                        "date": date_str,
                        "received": 0.0,
                        "paid": issue_amount,
                        "amount_in_words": num_to_words_rupees(issue_amount),
                        "interest_rate": annual_interest_rate,
                        "calendar_type": calendar_type,
                        "days": days,
                        "interest": interest,  # Using calculated interest
                        "notes": "",  # No notes for imported transactions
                        "timestamp": datetime.now().isoformat()
                    }
                    new_transactions.append(transaction)
                    next_id += 1
                
                # Create transaction for received amount (Receipt)
                if receipt_amount > 0:
                    # Calculate interest for received amount
                    interest = interest_service.calculate_interest(
                        receipt_amount,
                        annual_interest_rate,
                        days,
                        calendar_type  # Using determined calendar type
                    )
                    interest = abs(interest)  # Make it positive for received interest
                    
                    transaction = {
                        "id": next_id,
                        "client_id": client_id,
                        "date": date_str,
                        "received": receipt_amount,
                        "paid": 0.0,
                        "amount_in_words": num_to_words_rupees(receipt_amount),
                        "interest_rate": annual_interest_rate,
                        "calendar_type": calendar_type,
                        "days": days,
                        "interest": interest,  # Using calculated interest
                        "notes": "",  # No notes for imported transactions
                        "timestamp": datetime.now().isoformat()
                    }
                    new_transactions.append(transaction)
                    next_id += 1
                
            except Exception as e:
                st.warning(f"Error processing row {idx + 1}: {str(e)}")
                continue
        
        return new_transactions
        
    except Exception as e:
        st.error(f"Error importing transactions: {str(e)}")
        return None

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
        background-color: #ffffff !important;
        color: #4b6bfb !important;
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
        border: 1px solid rgba(75, 107, 251, 0.1) !important;
        border-bottom: none !important;
        background-color: #f5f7fa !important;
        transition: all 0.2s ease !important;
        font-weight: 600 !important; /* Make all tab text bold */
        font-size: 1.05rem !important; /* Slightly larger font size */
        color: #485b73 !important;
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
        color: inherit !important;
    }
    
    /* Hover effect for tabs */
    .stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
        background-color: #ffffff !important;
        color: #3a5ae8 !important;
        border-bottom: 1px solid rgba(75, 107, 251, 0.3) !important;
    }
    
    /* Ensure no extra borders around tabs */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 1px solid #e0e6ef !important;
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
    
    /* Transaction table styles */
    div.transaction-table table {
        background-color: #ffffff !important;
        border-radius: 0.8rem !important;
        overflow: hidden !important;
        border-collapse: separate !important;
        border-spacing: 0 !important;
        box-shadow: 0 4px 12px rgba(58, 90, 232, 0.08) !important;
    }
    
    div.transaction-table th {
        background-color: #f5f7fa !important;
        color: #2c3e50 !important;
        font-weight: 700 !important;
        border-bottom: 2px solid #e0e6ef !important;
        padding: 12px 16px !important;
    }
    
    div.transaction-table td {
        padding: 12px 16px !important;
        border-bottom: 1px solid #e0e6ef !important;
        color: #2c3e50 !important;
        font-weight: 500 !important;
    }
    
    div.transaction-table tr:nth-child(even) {
        background-color: #f8f9fb !important;
    }
    
    div.transaction-table tr:hover {
        background-color: rgba(75, 107, 251, 0.05) !important;
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
    # Check if we need to handle navigation from client view to another page
    if (st.session_state.get("view_client_transactions") is not None and 
        st.session_state.page != "transactions"):
        # Clear client-specific state variables
        if "view_client_transactions" in st.session_state:
            del st.session_state.view_client_transactions
        if "selected_client" in st.session_state:
            del st.session_state.selected_client
        st.rerun()
    
    colored_header(
        label="Transactions Management",
        description="View and manage your transactions",
        color_name="gray-40"
    )
    
    # Add back button if we came from client view
    if st.session_state.get("view_client_transactions") is not None:
        if st.button("← Back to Clients", type="secondary"):
            # Only reset view-specific state variables
            if "view_client_transactions" in st.session_state:
                del st.session_state.view_client_transactions
            if "selected_client" in st.session_state:
                del st.session_state.selected_client
            st.session_state.page = "clients"
            st.session_state.nav_changed = True
            st.rerun()
    
    # Initialize transaction tab session state if not already set
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "all_transactions"  # Default to all transactions tab
    
    # Apply enhanced tab styling
    apply_tab_styling()
    
    # Create tabs for different transaction functions
    tab1, tab2, tab3 = st.tabs(["📋 All Transactions", "✏️ Add Transaction", "📥 Import Transactions"])
    
    # Show the appropriate tab content
    with tab1:
        all_transactions_view(transactions_data, clients_data, interest_service)
    with tab2:
        transaction_management(transactions_data, clients_data, interest_service, interest_calendars)
    with tab3:
        import_transactions_view(transactions_data, clients_data, interest_service, interest_calendars)

def import_transactions_view(transactions_data, clients_data, interest_service, interest_calendars):
    """Import transactions from Excel file."""
    st.markdown("### Import Transactions from Excel")
    
    # Initialize session state for import
    if 'import_confirmed' not in st.session_state:
        st.session_state.import_confirmed = False
    
    # If import was just confirmed, reset the state and show success message
    if st.session_state.import_confirmed:
        st.success("✅ Transactions have been imported successfully!")
        
        # Add buttons for navigation
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Back to Transactions", use_container_width=True):
                st.session_state.import_confirmed = False
                st.rerun()
        with col2:
            if st.button("Import More Transactions", type="primary", use_container_width=True):
                st.session_state.import_confirmed = False
                st.rerun()
        return
    
    # Client selection for import
    client_options = [(c["id"], c["name"]) for c in clients_data["clients"]]
    if not client_options:
        st.warning("Please add a client first before importing transactions.")
        return
        
    selected_client_id = st.selectbox(
        "Select Client for Import",
        options=[id for id, _ in client_options],
        format_func=lambda x: next((name for id, name in client_options if id == x), ""),
        key="import_client_select"
    )
    
    # File upload
    uploaded_file = st.file_uploader("Choose an Excel file", type=['xlsx', 'xls', 'csv'], key="file_uploader")
    
    if uploaded_file and selected_client_id:
        # Preview transactions first
        preview_transactions = import_transactions_from_excel(
            uploaded_file,
            selected_client_id,
            interest_calendars,
            interest_service,
            transactions_data
        )
        
        if preview_transactions:
            st.markdown("#### Preview Transactions")
            st.warning("Please review the transactions below before importing.")
            
            # Convert preview transactions to DataFrame for display
            preview_df = pd.DataFrame(preview_transactions)
            preview_df['date'] = pd.to_datetime(preview_df['date'])
            
            # Calculate totals for preview - using the same method as all_transactions_view
            total_received = preview_df['received'].fillna(0).sum()
            total_paid = preview_df['paid'].fillna(0).sum()
            total_interest = preview_df['interest'].fillna(0).sum()
            net_amount = total_received - total_paid + total_interest
            
            # Display summary
            st.markdown("##### Summary")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Received", f"₹{total_received:,.2f}")
            with col2:
                st.metric("Total Paid", f"₹{total_paid:,.2f}")
            with col3:
                st.metric("Total Interest", f"₹{total_interest:,.2f}")
            with col4:
                st.metric("Net Amount", f"₹{net_amount:,.2f}")
            
            # Display preview table
            st.markdown("##### Transaction Details")
            st.dataframe(
                preview_df[[
                    'date', 'received', 'paid', 'interest', 
                    'interest_rate', 'calendar_type', 'days', 'notes'
                ]].style.format({
                    'date': lambda x: x.strftime('%d %b %Y'),
                    'received': '₹{:,.2f}'.format,
                    'paid': '₹{:,.2f}'.format,
                    'interest': '₹{:,.2f}'.format,
                    'interest_rate': '{:.2f}%'.format
                }),
                use_container_width=True
            )
            
            # Confirmation buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Cancel Import", use_container_width=True):
                    st.rerun()
            
            with col2:
                if st.button("Confirm Import", type="primary", use_container_width=True):
                    # Add new transactions to existing ones
                    transactions_data["transactions"].extend(preview_transactions)
                    # Save updated transactions
                    save_transactions(transactions_data)
                    # Set import confirmed flag
                    st.session_state.import_confirmed = True
                    st.rerun()
    
    # If import was not confirmed, show the import form again
    if not st.session_state.import_confirmed:
        pass
    
    # If import was confirmed, show the import form again
    if st.session_state.import_confirmed:
        pass

def transaction_management(transactions_data, clients_data, interest_service, interest_calendars):
    """Transaction management UI component."""
    st.markdown("### Add New Transaction")
    
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
                    value=float(selected_transaction.get("interest_rate", 0.0)),
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

def all_transactions_view(transactions_data, clients_data, interest_service):
    """Display all transactions with filtering options."""
    st.markdown("""
    <style>
    /* Transaction table styles */
    .stDataFrame table {
        background-color: #ffffff !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 12px rgba(58, 90, 232, 0.08) !important;
        border-collapse: separate !important;
        border-spacing: 0 !important;
    }
    
    .stDataFrame thead tr th {
        background-color: #f5f7fa !important;
        color: #2c3e50 !important;
        font-weight: 600 !important;
        border-bottom: 2px solid #e0e6ef !important;
        text-align: center !important;
    }
    
    .stDataFrame tbody tr {
        border-bottom: 1px solid #e0e6ef !important;
    }
    
    .stDataFrame tbody tr:nth-child(even) {
        background-color: #f8f9fb !important;
    }
    
    .stDataFrame tbody tr:hover {
        background-color: rgba(75, 107, 251, 0.05) !important;
    }
    
    .stDataFrame tbody tr td {
        color: #2c3e50 !important;
        font-weight: 500 !important;
    }
    
    /* Filter container styling */
    .filter-container {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        border: 1px solid #e0e6ef;
        box-shadow: 0 4px 12px rgba(58, 90, 232, 0.08);
    }
    
    /* Metrics container styling */
    .metrics-container {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        border: 1px solid #e0e6ef;
        box-shadow: 0 4px 12px rgba(58, 90, 232, 0.08);
        color: #2c3e50;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #485b73;
        font-weight: 600;
    }
    
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
    }
    
    .metric-positive {
        color: #1e7e34;
    }
    
    .metric-negative {
        color: #dc3545;
    }
    
    .metric-neutral {
        color: #4b6bfb;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("### All Transactions")
        
    # Get all transactions
    transactions = transactions_data.get("transactions", [])
    
    if not transactions:
        st.info("No transactions found. Add some transactions to get started!")
        return
    
    # Initialize persistent filter session states if not set
    if "transaction_filter_client" not in st.session_state:
        # Use the selected client from view_client_transactions if available, otherwise default to "All Clients"
        if st.session_state.get("view_client_transactions") is not None:
            client_id = st.session_state.get("view_client_transactions")
            client_name = next((c["name"] for c in clients_data["clients"] if c["id"] == client_id), "All Clients")
            st.session_state.transaction_filter_client = client_name
        else:
            st.session_state.transaction_filter_client = "All Clients"
    
    if "transaction_filter_date_range" not in st.session_state:
        # Convert datetime objects to date objects for the date picker
        try:
            min_date = pd.to_datetime(min(t["date"] for t in transactions)).date()
            max_date = pd.to_datetime(max(t["date"] for t in transactions)).date()
            st.session_state.transaction_filter_date_range = (min_date, max_date)
        except (ValueError, TypeError):
            # Handle empty transactions list or other errors
            today = pd.Timestamp.now().date()
            st.session_state.transaction_filter_date_range = (today, today)
    
    if "transaction_filter_type" not in st.session_state:
        st.session_state.transaction_filter_type = "All"
    
    # Add filter options
    st.markdown("#### Filter Transactions")
    
    # Create columns for filters with Reset button aligned with inputs
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([1, 1, 1, 0.5])
    
    with filter_col1:
        # Client filter
        client_options = ["All Clients"] + [c["name"] for c in clients_data["clients"]]
        # Use the persisted client filter
        client_index = client_options.index(st.session_state.transaction_filter_client) if st.session_state.transaction_filter_client in client_options else 0
        selected_client = st.selectbox(
            "Client", 
            client_options, 
            index=client_index,
            key="client_filter_selectbox"
        )
        # Update session state
        st.session_state.transaction_filter_client = selected_client
    
    with filter_col2:
        # Date range filter - use persisted values
        try:
            date_range = st.date_input(
                "Date Range",
                value=st.session_state.transaction_filter_date_range,
                key="date_range_filter_input"
            )
            # Update session state
            st.session_state.transaction_filter_date_range = date_range
        except Exception as e:
            # Handle any errors by resetting the date range
            min_date = pd.to_datetime(min(t["date"] for t in transactions)).date()
            max_date = pd.to_datetime(max(t["date"] for t in transactions)).date()
            st.session_state.transaction_filter_date_range = (min_date, max_date)
            date_range = st.session_state.transaction_filter_date_range
            st.error(f"Date range reset due to error: {str(e)}")
    
    with filter_col3:
        # Transaction type filter - use persisted value
        transaction_types = ["All", "Received Only", "Paid Only", "With Interest"]
        type_index = transaction_types.index(st.session_state.transaction_filter_type) if st.session_state.transaction_filter_type in transaction_types else 0
        transaction_type = st.selectbox(
            "Transaction Type", 
            transaction_types,
            index=type_index,
            key="type_filter_selectbox"
        )
        # Update session state
        st.session_state.transaction_filter_type = transaction_type
    
    with filter_col4:
        def reset_transaction_filters():
            st.session_state.transaction_filter_client = "All Clients"
            # Convert to date objects for consistency
            try:
                min_date = pd.to_datetime(min(t["date"] for t in transactions)).date()
                max_date = pd.to_datetime(max(t["date"] for t in transactions)).date()
                st.session_state.transaction_filter_date_range = (min_date, max_date)
            except (ValueError, TypeError):
                # Handle empty transactions list or other errors
                today = pd.Timestamp.now().date()
                st.session_state.transaction_filter_date_range = (today, today)
            st.session_state.transaction_filter_type = "All"
        st.write("\n\t\t")
        st.button("🔄 Reset", on_click=reset_transaction_filters, help="Reset all filters to default values")
    
    # Convert transactions to DataFrame
    df = pd.DataFrame(transactions)
    
    # Apply filters
    if selected_client != "All Clients":
        client_id = next(c["id"] for c in clients_data["clients"] if c["name"] == selected_client)
        df = df[df["client_id"] == client_id]
    
    if len(date_range) == 2:
        df["date"] = pd.to_datetime(df["date"])
        start_date = pd.to_datetime(date_range[0])
        end_date = pd.to_datetime(date_range[1])
        # Set the time of end_date to 23:59:59 to include the entire day
        end_date = end_date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
    
    if transaction_type == "Received Only":
        df = df[df["received"] > 0]
    elif transaction_type == "Paid Only":
        df = df[df["paid"] > 0]
    elif transaction_type == "With Interest":
        df = df[df["interest"] != 0]
    
    # Create client names mapping here, before it's used
    client_names = {c['id']: c['name'] for c in clients_data['clients']}
    
    # Calculate totals
    total_received = df["received"].sum()
    total_paid = df["paid"].sum()
    total_interest = df["interest"].sum()
    net_balance = total_received - total_paid + total_interest
    
    # Display totals in a styled container
    st.markdown("""
    <style>
    .total-box {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border: 1px solid #333;
    }
    .total-amount {
        font-size: 1.2em;
        font-weight: bold;
        margin: 0;
    }
    .total-label {
        color: #000000;
        font-size: 0.9em;
        margin: 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("#### Transaction Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class='total-box'>
            <p class='total-label'>Total Received</p>
            <p class='total-amount' style='color: #2ea043;'>₹{total_received:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='total-box'>
            <p class='total-label'>Total Paid</p>
            <p class='total-amount' style='color: #f87171;'>₹{total_paid:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='total-box'>
            <p class='total-label'>Total Interest</p>
            <p class='total-amount' style='color: #4b6bfb;'>₹{total_interest:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class='total-box'>
            <p class='total-label'>Net Balance</p>
            <p class='total-amount' style='color: {"#2ea043" if net_balance >= 0 else "#f87171"};'>₹{net_balance:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Add action buttons row
    st.markdown("<div style='display: flex; justify-content: flex-end; margin: 10px 0;'>", unsafe_allow_html=True)
    
    # Create columns for the buttons - now including the delete button
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
    
    # Initialize delete confirmation state if not set
    if 'show_delete_confirmation' not in st.session_state:
        st.session_state.show_delete_confirmation = False
    
    with btn_col1:
        if st.button("🖨️ Print Transactions", help="Create a printable version of the current filtered transactions"):
            # Create a temporary HTML file with current filtered transactions
            print_html = create_printable_html(df, client_names, total_received, total_paid, total_interest, net_balance)
            
            # Use components to load and auto-print the HTML
            components.html(print_html, height=0, scrolling=False)
            
            st.success("Print dialog should open automatically. If it doesn't, check your browser settings.")
    
    with btn_col2:
        # Create a copy of the dataframe for Excel export
        export_df = df.copy()
        
        # Add client names to the export dataframe
        if 'client_id' in export_df.columns:
            export_df['client'] = export_df['client_id'].map(client_names)
            
        # Format the date column for Excel if present
        if 'date' in export_df.columns:
            export_df['date'] = pd.to_datetime(export_df['date'])
            
        # Reorder and select columns for export
        export_columns = [col for col in ['date', 'client', 'received', 'paid', 'interest', 'running_balance', 'notes', 'interest_rate', 'calendar_type', 'days'] if col in export_df.columns]
        export_df = export_df[export_columns]
        
        # Prepare Excel file download
        excel_data = export_to_excel(export_df)
        
        # Create a descriptive filename with date range
        try:
            start_date = date_range[0].strftime('%d-%m-%Y') if len(date_range) >= 1 else "all"
            end_date = date_range[1].strftime('%d-%m-%Y') if len(date_range) >= 2 else "all"
        except AttributeError:
            # Handle case where date_range is datetime or other type
            start_date = pd.to_datetime(date_range[0]).strftime('%d-%m-%Y') if len(date_range) >= 1 else "all"
            end_date = pd.to_datetime(date_range[1]).strftime('%d-%m-%Y') if len(date_range) >= 2 else "all"
        client_name = selected_client.replace(" ", "_") if selected_client != "All Clients" else "All_Clients"
        excel_filename = f"transactions_{client_name}_{start_date}_to_{end_date}.xlsx"
        
        # Download button
        st.download_button(
            label="📊 Export to Excel",
            data=excel_data,
            file_name=excel_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Download current filtered transactions as Excel file"
        )
    
    with btn_col3:
        # Delete all transactions button
        if st.button("🗑️ Delete All Transactions", type="secondary", help="This will delete all transactions for all clients"):
            st.session_state.show_delete_confirmation = True
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Show confirmation dialog if delete button was clicked
    if st.session_state.show_delete_confirmation:
        st.warning("⚠️ Are you sure you want to delete ALL transactions? This action cannot be undone!")
        confirm_col1, confirm_col2 = st.columns([1, 1])
        with confirm_col1:
            if st.button("Yes, Delete All", type="primary"):
                transactions_data["transactions"] = []
                save_transactions(transactions_data)
                st.session_state.show_delete_confirmation = False
                st.success("All transactions have been deleted!")
                st.rerun()
        with confirm_col2:
            if st.button("No, Cancel"):
                st.session_state.show_delete_confirmation = False
                st.rerun()
    
    st.markdown("#### Transaction Details")
    
    # Format DataFrame for display
    display_df = df.copy()
    
    # Add client names
    display_df['client'] = display_df['client_id'].map(client_names)
    
    # Convert date to datetime if not already
    display_df['date'] = pd.to_datetime(display_df['date'])
    
    # Sort by date
    display_df = display_df.sort_values('date')
    
    # Calculate running balance chronologically across all transactions
    display_df['running_balance'] = 0.0
    balance = 0.0
    # Loop through the sorted dataframe to calculate running balance
    for idx, row in display_df.iterrows():
        received = row['received'] if not pd.isna(row['received']) else 0
        paid = row['paid'] if not pd.isna(row['paid']) else 0
        interest = row['interest'] if not pd.isna(row['interest']) else 0
        balance += received - paid + interest
        display_df.loc[idx, 'running_balance'] = balance
    
    # Store original row indices to maintain relationship with original dataframe
    display_df['original_index'] = display_df.index
    
    # Reorder columns for display, but keep original columns in the dataframe
    columns_to_display = [
        'date', 'client', 'received', 'paid', 
        'interest', 'interest_rate', 'running_balance', 'notes'
    ]
    
    display_columns = [col for col in columns_to_display if col in display_df.columns]
    
    # Format numeric columns
    numeric_columns = ['received', 'paid', 'interest', 'running_balance']
    for col in numeric_columns:
        if col in display_df.columns:
            display_df[col] = display_df[col].fillna(0).round(2)
    
    # Format interest rate with percentage
    if 'interest_rate' in display_df.columns:
        display_df['interest_rate'] = display_df['interest_rate'].fillna(0).round(2)
    
    # Create an editable dataframe
    edited_df = st.data_editor(
        display_df[display_columns],
        use_container_width=True,
        hide_index=True,
        column_config={
            'date': st.column_config.DatetimeColumn(
                'Date',
                format="DD MMM YYYY"
            ),
            'client': st.column_config.SelectboxColumn(
                'Client',
                options=client_options,
                required=True
            ),
            'received': st.column_config.NumberColumn(
                'Received',
                format="₹%.2f",
                min_value=0
            ),
            'paid': st.column_config.NumberColumn(
                'Paid',
                format="₹%.2f",
                min_value=0
            ),
            'interest': st.column_config.NumberColumn(
                'Interest',
                format="₹%.2f"
            ),
            'interest_rate': st.column_config.NumberColumn(
                'Interest Rate',
                format="%.2f%%",
                min_value=0,
                max_value=100,
                step=0.25
            ),
            'running_balance': st.column_config.NumberColumn(
                'Running Balance',
                format="₹%.2f",
                disabled=True
            ),
            'notes': st.column_config.TextColumn(
                'Notes',
                max_chars=500
            )
        },
        num_rows="dynamic",
        key="transaction_data_editor"
    )
    
    # Check if there are any changes
    displayed_df = display_df[display_columns]
    if not displayed_df.equals(edited_df):
        # Update the transactions data
        updated_transactions = []
        
        # Get next available ID
        next_id = max([t.get("id", 0) for t in transactions_data["transactions"]], default=0) + 1
        
        # Store original indices to make matching more reliable
        original_indices = {}
        for i, idx in enumerate(display_df['original_index']):
            original_indices[i] = idx
            
        # Build a lookup map of original transactions by ID for quicker matching
        original_transactions_map = {t.get("id"): t for t in transactions_data["transactions"]}
            
        for idx, row in edited_df.iterrows():
            orig_transaction = None
            
            # Try to find the original transaction by its index first
            if idx in original_indices:
                orig_idx = original_indices[idx]
                if orig_idx in display_df.index:
                    # Get the transaction ID from the original data
                    if 'id' in display_df.loc[orig_idx]:
                        transaction_id = display_df.loc[orig_idx]['id']
                        if transaction_id in original_transactions_map:
                            orig_transaction = original_transactions_map[transaction_id]
            
            # If we couldn't find it by index, try the client+date approach as fallback
            if orig_transaction is None:
                client_id = next((c["id"] for c in clients_data["clients"] if c["name"] == row["client"]), None)
                date_str = pd.to_datetime(row["date"]).strftime("%Y-%m-%d")
                
                for t in transactions_data["transactions"]:
                    # Match on client and date
                    if t["client_id"] == client_id and t["date"] == date_str:
                        # Try to match transaction type (received vs paid)
                        is_receive_match = (t.get("received", 0) > 0 and not pd.isna(row["received"]) and float(row["received"]) > 0)
                        is_paid_match = (t.get("paid", 0) > 0 and not pd.isna(row["paid"]) and float(row["paid"]) > 0)
                        
                        if is_receive_match or is_paid_match:
                            orig_transaction = t
                            break
            
            # Process the transaction (either update existing or create new)
            if orig_transaction:
                # Determine if the transaction is received or paid in the edited version
                is_received = not pd.isna(row["received"]) and float(row["received"]) > 0
                
                # Get the new amount
                amount = float(row["received"]) if is_received else float(row["paid"])
                
                # Update interest rate if edited, otherwise keep the original
                if 'interest_rate' in row and not pd.isna(row['interest_rate']):
                    interest_rate = float(row['interest_rate'])
                else:
                    interest_rate = float(orig_transaction.get("interest_rate", 0.0))
                
                calendar_type = orig_transaction.get("calendar_type", "Financial")
                days = int(orig_transaction.get("days", 0))
                
                # Always recalculate interest based on the new amount using existing rate
                transaction_amount = amount if is_received else -amount
                
                if calendar_type == "Diwali":
                    interest = interest_service.calculate_interest(abs(transaction_amount), interest_rate, days, "Diwali")
                    if not is_received:  # If paid
                        interest = -interest
                else:  # Financial
                    interest = interest_service.calculate_interest(abs(transaction_amount), interest_rate, days, "Financial")
                    if not is_received:  # If paid
                        interest = -interest
                
                # Only use the interest from the data editor if it was explicitly modified
                # Otherwise use our calculated interest
                if 'interest' in row and not pd.isna(row['interest']) and abs(float(row['interest']) - float(orig_transaction.get('interest', 0))) > 0.01:
                    # User manually changed the interest, keep their value
                    interest = float(row["interest"])
                
                # Update the transaction
                updated_transaction = orig_transaction.copy()
                updated_transaction.update({
                    "date": pd.to_datetime(row["date"]).strftime("%Y-%m-%d"),
                    "received": float(row["received"]) if is_received else 0.0,
                    "paid": float(row["paid"]) if not is_received else 0.0,
                    "amount_in_words": num_to_words_rupees(amount),
                    "interest_rate": interest_rate,  # Keep original interest rate
                    "calendar_type": calendar_type,  # Keep original calendar type
                    "days": days,  # Keep original days
                    "interest": round(float(interest), 2),  # Recalculated interest
                    "notes": row["notes"] if "notes" in row and row["notes"] else orig_transaction.get("notes", ""),
                })
                
                updated_transactions.append(updated_transaction)
            else:
                # This is a new transaction
                client_id = next(c["id"] for c in clients_data["clients"] if c["name"] == row["client"])
                
                # For new transactions, we need to determine a default calendar type based on interest
                # If interest is explicitly set, determine calendar type based on provided values
                is_received = not pd.isna(row["received"]) and float(row["received"]) > 0
                amount = float(row["received"]) if is_received else float(row["paid"])
                interest = float(row["interest"]) if not pd.isna(row["interest"]) else 0.0
                
                # Use interest rate from input or a sensible default based on other transactions
                # Try to find an appropriate default interest rate
                default_rate = 0.0
                if len(transactions_data["transactions"]) > 0:
                    # Use the most recent transaction's interest rate as default
                    sorted_transactions = sorted(
                        transactions_data["transactions"], 
                        key=lambda t: datetime.strptime(t.get("date", "1900-01-01"), "%Y-%m-%d"),
                        reverse=True
                    )
                    if sorted_transactions:
                        default_rate = float(sorted_transactions[0].get("interest_rate", 0.0))
                
                # If we couldn't find a default from existing transactions, use 0.0
                if default_rate == 0.0:
                    default_rate = 0.0  # Remove the hardcoded 5.0
                
                interest_rate = float(row["interest_rate"]) if "interest_rate" in row and not pd.isna(row["interest_rate"]) else default_rate
                days = 0  # Default days
                
                # If we have a date, try to get the days value
                date_str = pd.to_datetime(row["date"]).strftime("%Y-%m-%d")
                diwali_days, financial_days = interest_service.get_interest_value(date_str)
                
                if calendar_type == "Financial" and financial_days is not None:
                    days = int(financial_days)
                
                # If interest wasn't explicitly provided, calculate it
                if interest == 0.0 and amount > 0:
                    if calendar_type == "Financial":
                        interest = interest_service.calculate_interest(amount, interest_rate, days, "Financial")
                        if not is_received:
                            interest = -interest
                
                new_transaction = {
                    "id": next_id,
                    "client_id": client_id,
                    "date": date_str,
                    "received": float(row["received"]) if is_received else 0.0,
                    "paid": float(row["paid"]) if not is_received else 0.0,
                    "amount_in_words": num_to_words_rupees(amount),
                    "interest_rate": interest_rate,
                    "calendar_type": calendar_type,
                    "days": days,
                    "interest": round(float(interest), 2),
                    "notes": row["notes"] if "notes" in row else "",
                    "timestamp": datetime.now().isoformat()
                }
                updated_transactions.append(new_transaction)
                next_id += 1
        
        # Save the updated transactions
        transactions_data["transactions"] = updated_transactions
        save_transactions(transactions_data)
        st.success("Transactions updated successfully!")
        st.rerun()

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
                <p style="color: {"#2ea043" if transaction.get('received', 0) > 0 else "#f87171"}; font-weight: 500; margin-top: 0;">₹{transaction.get('received', 0) if transaction.get('received', 0) > 0 else transaction.get('paid', 0):,.2f}</p>
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
        margin-bottom: 30px;
        box-shadow: 0 2px 15px rgba(0,0,0,0.05);
        border-radius: 5px;
        overflow: hidden;
        table-layout: auto;
    }
    
    th, td {
        padding: 12px 15px;
        text-align: left;
        border-bottom: 1px solid #ddd;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    /* Column-specific widths */
    th:nth-child(1), td:nth-child(1) { /* Date */
        width: 12%;
        min-width: 100px;
    }
    th:nth-child(2), td:nth-child(2) { /* Client */
        width: 18%;
        min-width: 120px;
    }
    th:nth-child(3), td:nth-child(3), /* Received */
    th:nth-child(4), td:nth-child(4), /* Paid */
    th:nth-child(5), td:nth-child(5), /* Interest */
    th:nth-child(6), td:nth-child(6) { /* Balance */
        width: 12%;
        min-width: 100px;
        text-align: right;
    }
    th:nth-child(7), td:nth-child(7) { /* Notes */
        width: auto;
        white-space: normal;
    }
    
    /* Notes can wrap */
    td:last-child {
        white-space: normal;
        word-break: break-word;
    }
    
    th {
        background-color: #f8f9fa;
        font-weight: bold;
        color: #2c3e50;
        border-top: 1px solid #dee2e6;
        position: relative;
    }
    
    th::after {
        content: "";
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 2px;
        background: linear-gradient(to right, #4b6bfb, transparent);
        opacity: 0.5;
    }
    
    tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    
    tr:hover {
        background-color: #f5f5f5;
    }
    
    .totals-row {
        background-color: #f2f7ff !important;
        border-top: 2px solid #dee2e6;
        font-weight: bold;
    }
    
    .total-cell {
        font-weight: bold;
    }
    
    .positive {
        color: #1e7e34;
    }
    
    .negative {
        color: #dc3545;
    }
    
    .neutral {
        color: #0066cc;
    }
    
    .footer {
        text-align: center;
        font-size: 12px;
        color: #666;
        margin-top: 40px;
        padding-top: 15px;
        border-top: 1px solid #eee;
        position: relative;
    }
    
    .footer::before {
        content: "";
        position: absolute;
        top: -1px;
        left: 30%;
        right: 30%;
        height: 1px;
        background: linear-gradient(to right, transparent, rgba(0,0,0,0.1), transparent);
    }
    
    @media print {
        body {
            padding: 10mm;
            background: none !important;
        }
        
        body::before,
        body::after,
        .vertical-line {
            display: none !important;
        }
        
        .no-print {
            display: none;
        }
        
        table {
            page-break-inside: auto;
            box-shadow: none;
            width: 100% !important;
            table-layout: fixed;
        }
        
        tr {
            page-break-inside: avoid;
            page-break-after: auto;
        }
        
        th, td {
            box-shadow: inset 0 0 0 1px rgba(0,0,0,0.1);
            font-size: 10pt;
            padding: 8px;
        }
        
        /* Ensure amount columns are aligned right when printing */
        td:nth-child(3), td:nth-child(4), td:nth-child(5), td:nth-child(6) {
            text-align: right !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Use an alternative approach by embedding in HTML components
    st.components.v1.html(transaction_html, height=550, scrolling=False)

def transaction_receipt(transaction, client_name):
    """Display a transaction receipt that can be printed or saved."""
    colored_header(
        label="Transaction Receipt",
        description="Transaction has been successfully recorded",
        color_name="green-90"
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

def create_printable_html(df, client_map, total_received, total_paid, total_interest, net_balance):
    """
    Create a printable HTML version of the transaction table
    
    Args:
        df: DataFrame with transaction data
        client_map: Dictionary mapping client IDs to names
        total_received: Total received amount
        total_paid: Total paid amount
        total_interest: Total interest amount
        net_balance: Net balance amount
        
    Returns:
        str: HTML string for printing
    """
    # Clone DataFrame and format it for display
    print_df = df.copy()
    
    # Add client names if not already present
    if 'client' not in print_df.columns and 'client_id' in print_df.columns:
        print_df['client'] = print_df['client_id'].map(client_map)
    
    # Ensure date is in datetime format and sort chronologically
    if 'date' in print_df.columns:
        print_df['date'] = pd.to_datetime(print_df['date'])
        print_df = print_df.sort_values('date')
        
    # Calculate running balance across all transactions chronologically
    print_df['running_balance'] = 0.0
    balance = 0.0
    
    # Loop through the sorted dataframe to calculate running balance
    for idx, row in print_df.iterrows():
        received = row['received'] if not pd.isna(row['received']) else 0
        paid = row['paid'] if not pd.isna(row['paid']) else 0
        # Exclude interest from running balance calculation
        balance += received - paid
        print_df.loc[idx, 'running_balance'] = balance
    
    # Format date after calculations
    print_df['date'] = print_df['date'].dt.strftime('%d %b %Y')
    
    # Select columns for display and rename them - exclude notes
    display_cols = []
    if 'date' in print_df.columns:
        display_cols.append('date')
    if 'client' in print_df.columns:
        display_cols.append('client')
    if 'received' in print_df.columns:
        display_cols.append('received')
    if 'paid' in print_df.columns:
        display_cols.append('paid')
    if 'interest' in print_df.columns:
        display_cols.append('interest')
    if 'interest_rate' in print_df.columns:
        display_cols.append('interest_rate')
    if 'running_balance' in print_df.columns:
        display_cols.append('running_balance')
    # Note: We're intentionally not including 'notes' column
    
    print_df = print_df[display_cols]
    
    # Format numeric columns for display
    for col in ['received', 'paid', 'interest', 'running_balance']:
        if col in print_df.columns:
            print_df[col] = print_df[col].apply(lambda x: f'₹{x:,.2f}' if pd.notnull(x) else '')
    
    # Format interest rate with percentage
    if 'interest_rate' in print_df.columns:
        print_df['interest_rate'] = print_df['interest_rate'].apply(lambda x: f'{x:.2f}%' if pd.notnull(x) else '')
    
    # Create HTML table rows
    table_rows = ""
    for _, row in print_df.iterrows():
        # Determine cell coloring for running balance
        balance = row['running_balance'].replace('₹', '').replace(',', '')
        try:
            balance_value = float(balance)
            balance_class = "positive" if balance_value >= 0 else "negative"
        except:
            balance_class = ""
            
        table_rows += "<tr>"
        for col in display_cols:
            if col == 'running_balance':
                table_rows += f"<td class='{balance_class}'>{row[col]}</td>"
            else:
                table_rows += f"<td>{row[col]}</td>"
        table_rows += "</tr>"
    
    # Add totals row at the bottom of the table
    totals_row = "<tr class='totals-row'>"
    for col in display_cols:
        if col == 'date':
            totals_row += "<td><strong>TOTALS</strong></td>"
        elif col == 'client':
            totals_row += "<td></td>"
        elif col == 'received':
            totals_row += f"<td class='total-cell positive'><strong>₹{total_received:,.2f}</strong></td>"
        elif col == 'paid':
            totals_row += f"<td class='total-cell negative'><strong>₹{total_paid:,.2f}</strong></td>"
        elif col == 'interest':
            totals_row += f"<td class='total-cell neutral'><strong>₹{total_interest:,.2f}</strong></td>"
        elif col == 'interest_rate':
            totals_row += "<td></td>"  # No total for interest rate
        elif col == 'running_balance':
            css_class = "positive" if net_balance >= 0 else "negative"
            totals_row += f"<td class='total-cell {css_class}'><strong>₹{net_balance:,.2f}</strong></td>"
        else:
            totals_row += "<td></td>"
    totals_row += "</tr>"
    
    # Create column headers
    header_mapping = {
        'date': 'Date',
        'client': 'Client',
        'received': 'Received',
        'paid': 'Paid',
        'interest': 'Interest',
        'interest_rate': 'Rate',
        'running_balance': 'Running Balance'
        # Note: We've removed the 'notes' entry
    }
    
    table_headers = ""
    for col in display_cols:
        table_headers += f"<th>{header_mapping.get(col, col)}</th>"
    
    # Create the CSS as a regular string (not an f-string)
    css = """
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            color: #333;
            background: linear-gradient(to right, rgba(240, 240, 245, 0.5) 0%, rgba(255, 255, 255, 0) 20%, rgba(255, 255, 255, 0) 80%, rgba(240, 240, 245, 0.5) 100%);
            position: relative;
            font-size: 14px;
        }
        
        body::before {
            content: "";
            position: fixed;
            top: 0;
            left: 5%;
            height: 100%;
            width: 1px;
            background: linear-gradient(to bottom, rgba(0,0,0,0.03), rgba(0,0,0,0.08), rgba(0,0,0,0.03));
            z-index: -1;
        }
        
        body::after {
            content: "";
            position: fixed;
            top: 0;
            right: 5%;
            height: 100%;
            width: 1px;
            background: linear-gradient(to bottom, rgba(0,0,0,0.03), rgba(0,0,0,0.08), rgba(0,0,0,0.03));
            z-index: -1;
        }
        
        .vertical-line {
            position: fixed;
            top: 0;
            height: 100%;
            width: 1px;
            background: linear-gradient(to bottom, rgba(0,0,0,0.02), rgba(0,0,0,0.05), rgba(0,0,0,0.02));
            z-index: -1;
        }
        
        .vertical-line.line1 { left: 20%; }
        .vertical-line.line2 { left: 40%; }
        .vertical-line.line3 { left: 60%; }
        .vertical-line.line4 { left: 80%; }
        
        .report-header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #eee;
        }
        
        .report-title {
            font-size: 22px;
            font-weight: bold;
            margin-bottom: 5px;
            color: #2c3e50;
        }
        
        .report-date {
            font-size: 12px;
            color: #666;
            margin-bottom: 10px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.05);
            border-radius: 5px;
            overflow: hidden;
            table-layout: auto;
            font-size: 13px;
        }
        
        th, td {
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
            white-space: nowrap;
        }
        
        /* Column-specific widths */
        th:nth-child(1), td:nth-child(1) { 
            width: 14%;
            min-width: 120px;
        }
        th:nth-child(2), td:nth-child(2) { 
            width: 16%;
            min-width: 120px;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        th:nth-child(3), td:nth-child(3),
        th:nth-child(4), td:nth-child(4),
        th:nth-child(5), td:nth-child(5) { 
            width: 14%;
            min-width: 120px;
            text-align: right;
        }
        th:nth-child(6), td:nth-child(6) { 
            width: 10%;
            min-width: 80px;
            text-align: right;
        }
        th:nth-child(7), td:nth-child(7) { 
            width: 18%;
            min-width: 140px;
            text-align: right;
            font-weight: bold;
        }
        
        th {
            background-color: #f8f9fa;
            font-weight: bold;
            color: #2c3e50;
            border-top: 1px solid #dee2e6;
            position: relative;
            font-size: 13px;
        }
        
        th::after {
            content: "";
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(to right, #4b6bfb, transparent);
            opacity: 0.5;
        }
        
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        
        tr:hover {
            background-color: #f5f5f5;
        }
        
        .totals-row {
            background-color: #f2f7ff !important;
            border-top: 2px solid #dee2e6;
            font-weight: bold;
        }
        
        .total-cell {
            font-weight: bold;
        }
        
        .positive {
            color: #1e7e34;
        }
        
        .negative {
            color: #dc3545;
        }
        
        .neutral {
            color: #0066cc;
        }
        
        .footer {
            text-align: center;
            font-size: 11px;
            color: #666;
            margin-top: 40px;
            padding-top: 15px;
            border-top: 1px solid #eee;
            position: relative;
        }
        
        .footer::before {
            content: "";
            position: absolute;
            top: -1px;
            left: 30%;
            right: 30%;
            height: 1px;
            background: linear-gradient(to right, transparent, rgba(0,0,0,0.1), transparent);
        }
        
        @media print {
            body {
                padding: 10mm;
                background: none !important;
                font-size: 12px;
            }
            
            body::before,
            body::after,
            .vertical-line {
                display: none !important;
            }
            
            .no-print {
                display: none;
            }
            
            table {
                page-break-inside: auto;
                box-shadow: none;
                width: 100% !important;
                table-layout: fixed;
                font-size: 11px;
            }
            
            tr {
                page-break-inside: avoid;
                page-break-after: auto;
            }
            
            th, td {
                box-shadow: inset 0 0 0 1px rgba(0,0,0,0.1);
                font-size: 9pt;
                padding: 6px;
                white-space: nowrap;
                overflow: visible !important;
                text-overflow: clip !important;
            }
            
            /* Ensure amount columns are aligned right when printing */
            td:nth-child(3), td:nth-child(4), td:nth-child(5), td:nth-child(6), td:nth-child(7) {
                text-align: right !important;
            }
            
            /* Keep the running balance column styling when printing */
            td.positive {
                color: #1e7e34 !important;
            }
            
            td.negative {
                color: #dc3545 !important;
            }
            
            /* Make sure totals row has proper visibility */
            .totals-row td {
                font-weight: bold !important;
                background-color: #f2f7ff !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }
            
            /* Add more space for numeric columns in print */
            th:nth-child(3), td:nth-child(3),
            th:nth-child(4), td:nth-child(4),
            th:nth-child(5), td:nth-child(5),
            th:nth-child(7), td:nth-child(7) {
                min-width: 100px !important;
            }
        }
    </style>
    """
    
    # Add JavaScript for auto-printing
    script = """
    <script>
        window.onload = function() {
            window.print();
        };
    </script>
    """
    
    # Get current date/time
    date_time = datetime.now().strftime('%d %b %Y, %I:%M %p')
    
    # HTML structure
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Transaction Report</title>
    {css}
    {script}
</head>
<body>
    <div class="vertical-line line1"></div>
    <div class="vertical-line line2"></div>
    <div class="vertical-line line3"></div>
    <div class="vertical-line line4"></div>
    
    <div class="report-header">
        <div class="report-title">Transaction Report</div>
        <div class="report-date">Generated on {date_time}</div>
    </div>
    
    <table>
        <thead>
            <tr>{table_headers}</tr>
        </thead>
        <tbody>
            {table_rows}
            {totals_row}
        </tbody>
    </table>
    
    <div class="footer">
        Interest Calendar Application — Printed Report
    </div>
    
    <div class="no-print" style="text-align: center; margin-top: 20px;">
        <button onclick="window.close()" style="padding: 8px 16px; background-color: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;">Close Window</button>
    </div>
</body>
</html>"""
    
    return html

def export_to_excel(df, filename="transactions_export.xlsx"):
    """
    Export a DataFrame to an Excel file for download
    
    Args:
        df: DataFrame with transaction data
        filename: Name of the Excel file to create
        
    Returns:
        BytesIO: Excel file as bytes for download
    """
    output = BytesIO()
    
    # Create Excel writer
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Convert all columns to appropriate types
        export_df = df.copy()
        
        # Format date column if present
        if 'date' in export_df.columns and not export_df['date'].empty:
            if isinstance(export_df['date'].iloc[0], str):
                export_df['date'] = pd.to_datetime(export_df['date'])
            export_df['date'] = export_df['date'].dt.strftime('%d-%m-%Y')
            
        # Remove any object columns that might cause issues
        cols_to_keep = [col for col in export_df.columns if col not in ['timestamp']]
        export_df = export_df[cols_to_keep]
        
        # Write the dataframe to Excel
        export_df.to_excel(writer, sheet_name='Transactions', index=False)
        
        # Get the worksheet to apply formatting
        workbook = writer.book
        worksheet = writer.sheets['Transactions']
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#f2f2f2',
            'border': 1,
            'font_size': 12
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'font_size': 11
        })
        
        number_format = workbook.add_format({
            'border': 1,
            'font_size': 11,
            'num_format': '₹#,##0.00'
        })
        
        percentage_format = workbook.add_format({
            'border': 1,
            'font_size': 11,
            'num_format': '0.00%'
        })
        
        date_format = workbook.add_format({
            'border': 1,
            'font_size': 11,
            'num_format': 'dd-mm-yyyy'
        })
        
        # Set column widths
        for i, col in enumerate(export_df.columns):
            max_len = max(
                export_df[col].astype(str).map(len).max(),
                len(str(col))
            ) + 2
            worksheet.set_column(i, i, max_len)
        
        # Apply formats to header and all cells
        for col_num, value in enumerate(export_df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Apply number format to numeric columns
        for row_num in range(1, len(export_df) + 1):
            for col_num, col in enumerate(export_df.columns):
                cell_value = export_df.iloc[row_num-1, col_num]
                
                if col in ['received', 'paid', 'interest', 'running_balance']:
                    worksheet.write(row_num, col_num, cell_value if not pd.isna(cell_value) else 0, number_format)
                elif col == 'interest_rate':
                    # Convert percentage value to decimal for Excel's percentage format
                    rate_value = cell_value if not pd.isna(cell_value) else 0
                    worksheet.write(row_num, col_num, rate_value / 100, percentage_format)
                elif col == 'date':
                    worksheet.write(row_num, col_num, cell_value, date_format)
                else:
                    worksheet.write(row_num, col_num, cell_value if not pd.isna(cell_value) else "", cell_format)
    
    # Reset pointer to the start
    output.seek(0)
    
    return output
