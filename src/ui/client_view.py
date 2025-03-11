import streamlit as st
import pandas as pd
from streamlit_extras.colored_header import colored_header
from streamlit_extras.card import card
from ..models.client import Client
from ..data.data_loader import save_clients, save_transactions
from ..services.interest_service import InterestService
from ..utils.helpers import sanitize_html, num_to_words_rupees
from datetime import datetime

def client_management(clients_data, transactions_data, interest_calendars=None):
    """Client management UI component."""
    # Use colored_header instead of simple header
    colored_header(
        label="Clients Management",
        description="View and manage your clients",
        color_name="gray-40"
    )
    
    # Add custom CSS to style tab highlights with gray-40
    st.markdown("""
    <style>
    /* Fix for duplicate highlight bars - explicitly target and hide all but one */
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }
    
    /* Add a custom border-bottom to the selected tab to replace the highlight */
    button[aria-selected="true"] {
        box-shadow: none !important;
        border-bottom: 2px solid #808495 !important;
        background-color: rgba(35, 35, 35, 0.1) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create tabs for different client functions
    tab1, tab2 = st.tabs(["📋 Client List", "✏️ Add New Client"])
    
    # Initialize interest service if calendars are provided
    interest_service = None
    if interest_calendars:
        interest_service = InterestService(interest_calendars)
    
    with tab2:
        # Instruction for adding new client
        st.markdown("""
        <div style="background-color:#0a0a0a; padding:1rem; border-radius:0.5rem; border-left:4px solid #1a1a1a;">
            <p style="margin:0; color:#e0e0e0;">Add a new client by filling in the details below.</p>
        </div>
        """, unsafe_allow_html=True)
        
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
                
                # Always show opening balance details, regardless of balance amount
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
                st.markdown("#### Interest Information")
                st.markdown("""
                <div style="background-color:#121212; padding:1rem; border-radius:0.5rem; height:135px; position:relative;">
                    <div style="position:absolute; inset:0; border-radius:0.5rem; padding:1px; background:linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.95), rgba(255,255,255,0.1)); -webkit-mask:linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0); -webkit-mask-composite:xor; mask-composite:exclude; pointer-events:none;"></div>
                    <p style="margin:0; font-size:0.9rem; color:#e0e0e0;">
                        <strong>Opening Balance Interest:</strong><br>
                        Interest will be calculated based on the opening balance, interest rate, and selected calendar.
                        This will be recorded as an initial transaction for the client.
                        If you don't have an opening balance, you can leave it as 0.
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
                    
                    if opening_balance > 0 and interest_service:
                        # Get days value from appropriate calendar
                        diwali_days, financial_days = interest_service.get_interest_value(
                            opening_balance_date.strftime("%Y-%m-%d")
                        )
                        
                        if opening_balance_calendar == "Diwali" and diwali_days is not None:
                            opening_balance_days = int(diwali_days)
                            # Calculate interest on opening balance
                            opening_balance_interest = interest_service.calculate_interest(
                                opening_balance, 
                                opening_balance_interest_rate, 
                                opening_balance_days, 
                                "Diwali"
                            )
                        elif opening_balance_calendar == "Financial" and financial_days is not None:
                            opening_balance_days = int(financial_days)
                            # Calculate interest on opening balance
                            opening_balance_interest = interest_service.calculate_interest(
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
                            "date": opening_balance_date.strftime("%Y-%m-%d"),
                            "interest_rate": float(opening_balance_interest_rate),
                            "calendar_type": opening_balance_calendar,
                            "days": opening_balance_days,
                            "interest": round(float(opening_balance_interest), 2),
                        } if opening_balance > 0 else {
                            "date": opening_balance_date.strftime("%Y-%m-%d"),
                            "interest_rate": float(opening_balance_interest_rate),
                            "calendar_type": opening_balance_calendar,
                            "days": 0,
                            "interest": 0,
                        }
                    }
                    
                    # Initialize clients list if not exists
                    if "clients" not in clients_data:
                        clients_data["clients"] = []
                    
                    clients_data["clients"].append(new_client)
                    save_clients(clients_data)
                    
                    # If there's an opening balance, add it as a transaction
                    if opening_balance > 0:
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
                            "amount_in_words": num_to_words_rupees(float(opening_balance))
                        }
                        
                        if "transactions" not in transactions_data:
                            transactions_data["transactions"] = []
                        
                        transactions_data["transactions"].append(opening_transaction)
                        save_transactions(transactions_data)
                    
                    st.success("✅ Client added successfully!")
                    # Clear form 
                    st.rerun()
    
    with tab1:
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
        <div style="background-color:#0a0a0a; padding:0.8rem; border-radius:0.5rem; margin-bottom:1rem; border:1px solid #1a1a1a;">
            <p style="margin:0; color:#e0e0e0;"><strong>Showing {len(client_df)} client(s)</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display client cards
        for i, row in client_df.iterrows():
            # Create a container for each client to contain all elements
            with st.container():
                # Main client content container
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"""
                        <div style="background-color:#121212; padding:1.2rem; border-radius:0.5rem; box-shadow:0 2px 4px rgba(0,0,0,0.2); margin-bottom:1rem; position:relative;">
                            <div style="position:absolute; inset:0; border-radius:0.5rem; padding:1px; background:linear-gradient(45deg, rgba(255,255,255,0.1), rgba(255,255,255,0.98), rgba(255,255,255,0.1)); -webkit-mask:linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0); -webkit-mask-composite:xor; mask-composite:exclude; pointer-events:none;"></div>
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                                <h3 style="margin:0; color:#e0e0e0; font-family:'Geist Mono', monospace;">{row['name']}</h3>
                                <span style="background-color:#1e2130; color:#4b6bfb; padding:0.3rem 0.5rem; border-radius:1rem; font-size:0.8rem; font-family:'Geist Mono', monospace;">
                                    ID: {row.get('id', 'N/A')}
                                </span>
                            </div>
                            <div style="display:flex; flex-wrap:wrap; gap:1rem; margin-bottom:0.5rem;">
                                <div style="min-width:200px;">
                                    <p style="margin:0; color:#a0a0a0; font-size:0.8rem; font-family:'Geist Mono', monospace;">Contact</p>
                                    <p style="margin:0; font-weight:500; color:#e0e0e0; font-family:'Geist Mono', monospace;">{row['contact'] if row['contact'] else 'N/A'}</p>
                                </div>
                                <div style="min-width:200px;">
                                    <p style="margin:0; color:#a0a0a0; font-size:0.8rem; font-family:'Geist Mono', monospace;">Email</p>
                                    <p style="margin:0; font-weight:500; color:#e0e0e0; font-family:'Geist Mono', monospace;">{row['email'] if row['email'] else 'N/A'}</p>
                                </div>
                                <div style="min-width:200px;">
                                    <p style="margin:0; color:#a0a0a0; font-size:0.8rem; font-family:'Geist Mono', monospace;">Opening Balance</p>
                                    <p style="margin:0; font-weight:500; color:#{'4b6bfb' if row['opening_balance'] > 0 else '#a0a0a0'}; font-family:'Geist Mono', monospace;">
                                        ₹{row['opening_balance']:,.2f}
                                    </p>
                                </div>
                            </div>
                            <div>
                                <p style="margin:0; color:#a0a0a0; font-size:0.8rem; font-family:'Geist Mono', monospace;">Notes</p>
                                <p style="margin:0; font-size:0.9rem; color:#e0e0e0; font-family:'Geist Mono', monospace;">{row['notes'] if row['notes'] else 'No notes added.'}</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Add opening balance details section separately after the main card
                    if row["opening_balance"] > 0 and "opening_balance_details" in client_df.columns and isinstance(row.get("opening_balance_details", {}), dict) and row.get("opening_balance_details", {}):
                        # Custom opening balance details layout with consistent fonts
                        with col1:
                            st.markdown(f"""
                            <div style="background-color:#121212; padding:1rem; border-radius:0.5rem; position:relative; margin-top:-0.5rem; margin-bottom:1rem;">
                                <div style="position:absolute; inset:0; border-radius:0.5rem; padding:1px; background:linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.95), rgba(255,255,255,0.1)); -webkit-mask:linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0); -webkit-mask-composite:xor; mask-composite:exclude; pointer-events:none;"></div>
                                <h3 style="margin:0 0 0.8rem 0; color:#4b6bfb; font-size:1rem; font-family:'Geist Mono', monospace;">Opening Balance Details</h3>
                                <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.8rem;">
                                    <div>
                                        <p style="margin:0 0 0.3rem 0; color:#a0a0a0; font-size:0.9rem; font-family:'Geist Mono', monospace;">Date:</p>
                                        <p style="margin:0; color:#e0e0e0; font-weight:500; font-size:0.9rem; font-family:'Geist Mono', monospace;">{row['opening_balance_details'].get('date', 'N/A')}</p>
                                    </div>
                                    <div>
                                        <p style="margin:0 0 0.3rem 0; color:#a0a0a0; font-size:0.9rem; font-family:'Geist Mono', monospace;">Interest Rate:</p>
                                        <p style="margin:0; color:#e0e0e0; font-weight:500; font-size:0.9rem; font-family:'Geist Mono', monospace;">{row['opening_balance_details'].get('interest_rate', 0)}%</p>
                                    </div>
                                    <div>
                                        <p style="margin:0 0 0.3rem 0; color:#a0a0a0; font-size:0.9rem; font-family:'Geist Mono', monospace;">Calendar:</p>
                                        <p style="margin:0; color:#e0e0e0; font-weight:500; font-size:0.9rem; font-family:'Geist Mono', monospace;">{row['opening_balance_details'].get('calendar_type', 'N/A')}</p>
                                    </div>
                                    <div>
                                        <p style="margin:0 0 0.3rem 0; color:#a0a0a0; font-size:0.9rem; font-family:'Geist Mono', monospace;">Interest:</p>
                                        <p style="margin:0; color:#4b6bfb; font-weight:500; font-size:0.9rem; font-family:'Geist Mono', monospace;">₹{row['opening_balance_details'].get('interest', 0):,.2f}</p>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with col2:
                        # Action buttons with consistent styling
                        def handle_edit_click(client_id, client_name):
                            st.session_state.edit_client_id = client_id
                            st.session_state.page = "edit_client"
                            st.session_state.nav_changed = True
                        
                        def handle_view_click(client_id, client_name):
                            st.session_state.view_client_transactions = client_id
                            st.session_state.page = "transactions"
                            st.session_state.nav_changed = True
                        
                        edit_btn = st.button(
                            f"EDIT {row['name'].upper()}", 
                            key=f"edit_client_{row.get('id', f'unknown_{i}')}",
                            type="primary",
                            on_click=handle_edit_click,
                            args=(row.get('id'), row['name'])
                        )
                        
                        view_btn = st.button(
                            f"VIEW TRANSACTIONS", 
                            key=f"view_trans_{row.get('id', f'unknown_{i}')}",
                            on_click=handle_view_click,
                            args=(row.get('id'), row['name'])
                        )
                
                # Always add a separator after each client (except the last one)
                # This is outside the inner container but still within the main container for this client
                if i < len(client_df) - 1:  # Only add separator if this is not the last client
                    st.markdown("""
                    <div style="padding:2rem 0;">
                        <div style="width:100%; height:1px; background:linear-gradient(to right, 
                            rgba(255,255,255,0), 
                            rgba(255,255,255,0.2), 
                            rgba(255,255,255,0.5), 
                            rgba(255,255,255,0.2), 
                            rgba(255,255,255,0)
                        );"></div>
                        <div style="width:100%; height:1px; margin-top:1px; background:linear-gradient(to right, 
                            rgba(255,255,255,0), 
                            rgba(255,255,255,0.05), 
                            rgba(255,255,255,0.1), 
                            rgba(255,255,255,0.05), 
                            rgba(255,255,255,0)
                        );"></div>
                    </div>
                    """, unsafe_allow_html=True)
        
            # Navigation rerun logic - moved outside all containers
            if st.session_state.get('nav_changed', False):
                st.rerun()
        
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

def display_client_details(client, transactions_data):
    """Display detailed information about a client."""
    # Create a card with client details
    st.markdown(f"""
    <div style="background-color:#121212; padding:1.5rem; border-radius:0.8rem; margin-bottom:1.5rem; box-shadow:0 4px 8px rgba(0,0,0,0.2); position:relative;">
        <div style="position:absolute; inset:0; border-radius:0.8rem; padding:1.5px; background:linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.95), rgba(255,255,255,0.1)); -webkit-mask:linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0); -webkit-mask-composite:xor; mask-composite:exclude; pointer-events:none;"></div>
        <h2 style="color:#e0e0e0; margin-top:0; font-family:'Geist Mono', monospace;">{client['name']}</h2>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem; margin-top:1rem;">
            <div>
                <p style="color:#aaaaaa; margin-bottom:0.3rem; font-family:'Geist Mono', monospace;">Contact</p>
                <p style="color:#e0e0e0; font-weight:500; margin-top:0; font-family:'Geist Mono', monospace;">{client['contact'] if client['contact'] else 'Not provided'}</p>
            </div>
            <div>
                <p style="color:#aaaaaa; margin-bottom:0.3rem; font-family:'Geist Mono', monospace;">Email</p>
                <p style="color:#e0e0e0; font-weight:500; margin-top:0; font-family:'Geist Mono', monospace;">{client['email'] if client['email'] else 'Not provided'}</p>
            </div>
        </div>
        
        <div style="margin-top:1rem;">
            <p style="color:#aaaaaa; margin-bottom:0.3rem; font-family:'Geist Mono', monospace;">Notes</p>
            <p style="color:#e0e0e0; margin-top:0; font-family:'Geist Mono', monospace;">{client['notes'] if client['notes'] else 'No notes'}</p>
        </div>
        
        <div style="margin-top:1rem;">
            <p style="color:#aaaaaa; margin-bottom:0.3rem; font-family:'Geist Mono', monospace;">Created On</p>
            <p style="color:#e0e0e0; margin-top:0; font-family:'Geist Mono', monospace;">{datetime.strptime(client['created_at'].split()[0], '%Y-%m-%d').strftime('%d %b %Y') if 'created_at' in client else 'Unknown'}</p>
        </div>
        
        {f'''
        <div style="margin-top:1rem; background-color:#121212; padding:1rem; border-radius:0.5rem; position:relative;">
            <div style="position:absolute; inset:0; border-radius:0.5rem; padding:1px; background:linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.95), rgba(255,255,255,0.1)); -webkit-mask:linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0); -webkit-mask-composite:xor; mask-composite:exclude; pointer-events:none;"></div>
            <h3 style="color:#4b6bfb; margin-top:0; margin-bottom:0.5rem; font-family:'Geist Mono', monospace;">Opening Balance Details</h3>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem;">
                <div>
                    <p style="color:#aaaaaa; margin-bottom:0.3rem; font-family:'Geist Mono', monospace;">Amount</p>
                    <p style="color:#e0e0e0; font-weight:500; margin-top:0; font-family:'Geist Mono', monospace;">₹{client["opening_balance"]:,.2f}</p>
                </div>
                <div>
                    <p style="color:#aaaaaa; margin-bottom:0.3rem; font-family:'Geist Mono', monospace;">Date</p>
                    <p style="color:#e0e0e0; font-weight:500; margin-top:0; font-family:'Geist Mono', monospace;">{datetime.strptime(client["opening_balance_details"]["date"], '%Y-%m-%d').strftime('%d %b %Y') if client["opening_balance_details"]["date"] else 'Not provided'}</p>
                </div>
                <div>
                    <p style="color:#aaaaaa; margin-bottom:0.3rem; font-family:'Geist Mono', monospace;">Interest Rate</p>
                    <p style="color:#e0e0e0; font-weight:500; margin-top:0; font-family:'Geist Mono', monospace;">{client["opening_balance_details"]["interest_rate"]}%</p>
                </div>
                <div>
                    <p style="color:#aaaaaa; margin-bottom:0.3rem; font-family:'Geist Mono', monospace;">Calendar Type</p>
                    <p style="color:#e0e0e0; font-weight:500; margin-top:0; font-family:'Geist Mono', monospace;">{client["opening_balance_details"]["calendar_type"]}</p>
                </div>
                <div>
                    <p style="color:#aaaaaa; margin-bottom:0.3rem; font-family:'Geist Mono', monospace;">Days</p>
                    <p style="color:#e0e0e0; font-weight:500; margin-top:0; font-family:'Geist Mono', monospace;">{client["opening_balance_details"]["days"]}</p>
                </div>
                <div>
                    <p style="color:#aaaaaa; margin-bottom:0.3rem; font-family:'Geist Mono', monospace;">Interest</p>
                    <p style="color:#4b6bfb; font-weight:500; margin-top:0; font-family:'Geist Mono', monospace;">₹{client["opening_balance_details"]["interest"]:,.2f}</p>
                </div>
            </div>
        </div>
        ''' if client.get('opening_balance_details') else ''}
    </div>
    """, unsafe_allow_html=True)

def edit_client(clients_data, transactions_data, interest_calendars=None):
    """Client edit UI component."""
    # Use colored_header for consistent styling
    colored_header(
        label="Edit Client",
        description="Update client information",
        color_name="gray-40"
    )
    
    # Get the client ID from session state
    client_id = st.session_state.get("edit_client_id")
    
    if not client_id:
        st.error("No client selected for editing!")
        # Add a button to go back to client list
        if st.button("Back to Client List", type="primary", on_click=lambda: setattr(st.session_state, 'nav_changed', True)):
            st.session_state.page = "clients"
        return
    
    # Find the client in the clients_data
    client = None
    client_index = None
    for i, c in enumerate(clients_data.get("clients", [])):
        if c.get("id") == client_id:
            client = c
            client_index = i
            break
    
    if not client:
        st.error(f"Client with ID {client_id} not found!")
        # Add a button to go back to client list
        if st.button("Back to Client List", type="primary", on_click=lambda: setattr(st.session_state, 'nav_changed', True)):
            st.session_state.page = "clients"
        return
    
    # Initialize interest service if calendars are provided
    interest_service = None
    if interest_calendars:
        interest_service = InterestService(interest_calendars)
    
    # Style the form container
    st.markdown("""
    <div style="background-color:#252532; padding:1rem; border-radius:0.5rem; 
              border-left:4px solid #1a1a1a; margin-bottom:1rem;">
        <p style="margin:0; color:#e0e0e0;">Edit client details below. Fields marked with * are required.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create edit form
    with st.form("edit_client_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            client_name = st.text_input("Client Name *", value=client.get("name", ""))
            client_contact = st.text_input("Contact Number", value=client.get("contact", ""))
        
        with col2:
            client_email = st.text_input("Email", value=client.get("email", ""))
            client_notes = st.text_area("Notes", value=client.get("notes", ""), height=100)
        
        # Submit buttons
        col_cancel, col_save = st.columns(2)
        with col_cancel:
            cancel_btn = st.form_submit_button(
                "Cancel", 
                use_container_width=True
            )
        
        with col_save:
            save_btn = st.form_submit_button(
                "Save Changes", 
                use_container_width=True,
                type="primary"
            )
        
        if cancel_btn:
            st.session_state.page = "clients"
            st.session_state.nav_changed = True
        
        if save_btn:
            if not client_name:
                st.error("Client name is required!")
            else:
                # Update client data
                client["name"] = client_name
                client["contact"] = client_contact
                client["email"] = client_email
                client["notes"] = client_notes
                
                # Update the client in clients_data
                clients_data["clients"][client_index] = client
                
                # Save clients data
                save_clients(clients_data)
                
                st.success("✅ Client updated successfully!")
                
                # Return to client list
                st.session_state.page = "clients"
                st.session_state.nav_changed = True
    
    # Display current opening balance info (read-only)
    if client.get("opening_balance", 0) > 0:
        st.markdown("### Current Opening Balance")
        st.markdown("""
        <div style="background-color:#121212; padding:1rem; border-radius:0.5rem; margin-top:1rem; margin-bottom:1rem; position:relative;">
            <div style="position:absolute; inset:0; border-radius:0.5rem; padding:1px; background:linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.95), rgba(255,255,255,0.1)); -webkit-mask:linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0); -webkit-mask-composite:xor; mask-composite:exclude; pointer-events:none;"></div>
            <p style="margin:0; font-size:0.9rem; color:#e0e0e0;">
                <strong>Note:</strong> Opening balance details cannot be edited directly.
                If you need to change the opening balance, please delete this client and create a new one.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Opening Balance", f"₹{client.get('opening_balance', 0):,.2f}")
        
        # Display opening balance details if available
        if client.get("opening_balance_details"):
            with col2:
                st.metric("Interest Rate", f"{client['opening_balance_details'].get('interest_rate', 0)}%")
            with col3:
                st.metric("Calendar Type", client['opening_balance_details'].get('calendar_type', 'N/A'))
    
    # Add a button to go back to client list
    if st.button("Back to Client List", on_click=lambda: setattr(st.session_state, 'nav_changed', True)):
        st.session_state.page = "clients"

