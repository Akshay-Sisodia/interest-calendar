import streamlit as st
import pandas as pd
from streamlit_extras.colored_header import colored_header
from streamlit_extras.card import card
from ..models.client import Client
from ..data.data_loader import save_clients, save_transactions
from ..services.interest_service import InterestService
from ..utils.helpers import sanitize_html, num_to_words_rupees
from datetime import datetime
from ..ui.transaction_view import apply_tab_styling
import streamlit.components.v1 as components

def client_management(clients_data, transactions_data, interest_calendars=None):
    """Client management UI component."""
    # Use colored_header instead of simple header
    colored_header(
        label="Clients Management",
        description="View and manage your clients",
        color_name="gray-40"
    )
    # Create a key for delete all confirmation
    delete_all_key = "confirm_delete_all_clients_state"
    
    # Initialize the confirmation state if not exists
    if delete_all_key not in st.session_state:
        st.session_state[delete_all_key] = False
    
    # Create a success message state
    success_key = "delete_all_success"
    if success_key not in st.session_state:
        st.session_state[success_key] = False
    
    # Add option to delete all clients at the top
    col_delete_all, col_spacer = st.columns([1, 3])
    
    with col_delete_all:
        # Define callback functions for delete all clients
        def show_delete_all_confirmation():
            st.session_state[delete_all_key] = True
            
        def cancel_delete_all():
            st.session_state[delete_all_key] = False
            
        def confirm_delete_all():
            # Delete all clients and their transactions
            clients_data["clients"] = []
            transactions_data["transactions"] = []
            save_clients(clients_data)
            save_transactions(transactions_data)
            # Set the success flag instead of using st.success()
            st.session_state[success_key] = True
            # Keep the confirmation dialog open to show the success message
            # st.session_state[delete_all_key] = False
        
        if not st.session_state[delete_all_key]:
            # Show delete all button
            if st.button("Delete All Clients", key="delete_all_clients", 
                       on_click=show_delete_all_confirmation):
                pass  # The on_click handler takes care of the action
        else:
            # Show confirmation dialog
            st.markdown("""
            <div style="background-color:#FEECEB; padding:0.7rem; border-radius:0.5rem; 
                      border-left:4px solid #FF5252; margin:0.25rem 0 0.5rem 0; color:#542726;">
                <p style="margin:0 0 0.25rem 0; font-size:0.9rem;"><strong>⚠️ Warning: Delete All Clients</strong></p>
                <p style="margin:0; font-size:0.8rem;">This will delete ALL clients and their transactions.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show success message if deletion was successful
            if st.session_state[success_key]:
                st.markdown("""
                <div style="background-color:#E7F9ED; padding:0.7rem; border-radius:0.5rem; 
                          border-left:4px solid #2ea043; margin:0.5rem 0; color:#1E4620;">
                    <p style="margin:0; font-size:0.9rem;"><strong>✅ Success!</strong> All clients and transactions have been deleted.</p>
                </div>
                """, unsafe_allow_html=True)
                # Reset the success flag after displaying
                st.session_state[success_key] = False
                # Close the confirmation dialog after showing success
                st.session_state[delete_all_key] = False
                # Force a rerun to update the UI
                st.rerun()
            
            # Place buttons side by side using HTML styling instead of columns
            st.markdown("""
            <div style="display: flex; gap: 10px; margin-bottom: 10px;">
                <div style="flex: 1;"></div>
                <div style="flex: 1;"></div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show the buttons without columns
            cancel_btn = st.button("Cancel", key="cancel_delete_all",
                                 on_click=cancel_delete_all)
            
            delete_btn = st.button("Delete All", key="confirm_delete_all_btn",
                                 type="primary", on_click=confirm_delete_all)
    
    
    # Create tabs for different client functions
    apply_tab_styling()
    tab1, tab2 = st.tabs(["📋 Client List", "✏️ Add New Client"])
    
    # Initialize interest service if calendars are provided
    interest_service = None
    if interest_calendars:
        interest_service = InterestService(interest_calendars)
    
    # Add custom styling for client cards
    st.markdown("""
    <style>
    /* Client card styling */
    .client-card {
        background-color: #ffffff !important;
        border-radius: 0.8rem !important;
        padding: 1.5rem !important;
        margin-bottom: 1.5rem !important;
        border: 1px solid #e0e6ef !important;
        box-shadow: 0 4px 12px rgba(58, 90, 232, 0.08) !important;
    }
    
    .client-card h2 {
        color: #2c3e50 !important;
        font-weight: 700 !important;
        margin-bottom: 1rem !important;
    }
    
    .client-card .client-label {
        color: #485b73 !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        margin-bottom: 0.2rem !important;
    }
    
    .client-card .client-value {
        color: #2c3e50 !important;
        font-weight: 500 !important;
        margin-bottom: 1rem !important;
    }
    
    .client-info {
        color: #2c3e50 !important;
    }
    
    .client-id-badge {
        background-color: rgba(75, 107, 251, 0.1) !important;
        color: #4b6bfb !important;
        padding: 0.3rem 0.8rem !important;
        border-radius: 1rem !important;
        font-size: 0.8rem !important;
        font-weight: 700 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    with tab2:
        # Check for success message from previous submission
        if st.session_state.get('client_added_success'):
            # Display success notification with better styling
            st.markdown("""
            <div style="background-color:#E7F9ED; padding:1rem; border-radius:0.5rem; 
                      border-left:4px solid #2ea043; margin:0 0 1rem 0; color:#1E4620;">
                <h4 style="margin:0 0 0.5rem 0; color:#1E4620;">✅ Client Added Successfully!</h4>
                <p style="margin:0; font-size:0.9rem;">
                    The new client has been added to your client list.
                </p>
            </div>
            """, unsafe_allow_html=True)
            # Clear the success flag after displaying
            st.session_state.client_added_success = False
            
        # Instruction for adding new client
        st.markdown("""
        <div style="background-color:#ffffff; padding:1rem; border-radius:0.5rem; border-left:4px solid #4b6bfb; box-shadow:0 4px 8px rgba(58, 90, 232, 0.08);">
            <p style="margin:0; color:#2c3e50;">Add a new client by filling in the details below.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create form container
        with st.form("new_client_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_client_name = st.text_input("Client Name *")
                new_client_contact = st.text_input("Contact Number")
                new_client_email = st.text_input("Email")
                new_client_notes = st.text_area("Notes", key="new_client_notes", height=100)
            
            with col2:
                # Help info about opening balance interest
                st.markdown("#### Interest Information")
                st.markdown("""
                <div style="background-color:#ffffff; padding:1rem; border-radius:0.5rem; height:135px; position:relative; border:1px solid #e0e6ef; box-shadow:0 4px 8px rgba(58, 90, 232, 0.08);">
                    <p style="margin:0; font-size:0.9rem; color:#2c3e50;">
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
                    new_client = {
                        "id": len(clients_data.get("clients", [])) + 1,
                        "name": new_client_name,
                        "contact": new_client_contact,
                        "email": new_client_email,
                        "notes": new_client_notes,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # Initialize clients list if not exists
                    if "clients" not in clients_data:
                        clients_data["clients"] = []
                    
                    clients_data["clients"].append(new_client)
                    save_clients(clients_data)
                    
                    # Set success flag in session state for after rerun
                    st.session_state.client_added_success = True
                    
                    # Clear form 
                    st.rerun()
    
    with tab1:
        if not clients_data.get("clients"):
            st.info("No clients added yet. Add your first client in the 'Add New Client' tab.")
            return
            
        # Preview client data for display
        preview_cols = ["name", "contact", "email", "notes"]
        client_df = pd.DataFrame(clients_data["clients"])
        
        # Add search functionality
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            search_term = st.text_input("🔍 Search Clients", placeholder="Type to search by name, contact, or email...")
        
        with search_col2:
            sort_by = st.selectbox(
                "Sort By",
                ["Name (A-Z)", "Name (Z-A)"],
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
            
        # Show client count and summary
        st.markdown(f"""
        <div style="background-color:#ffffff; padding:0.8rem; border-radius:0.5rem; margin-bottom:1rem; border:1px solid #e0e6ef; box-shadow:0 4px 8px rgba(58, 90, 232, 0.08);">
            <p style="margin:0; color:#2c3e50;"><strong>Showing {len(client_df)} client(s)</strong></p>
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
                        <div class="client-card">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                                <h3 style="margin:0; color:#2c3e50; font-family:'Geist Mono', monospace;">{row['name']}</h3>
                                <span class="client-id-badge">
                                    ID: {row.get('id', 'N/A')}
                                </span>
                            </div>
                            <div style="display:flex; flex-wrap:wrap; gap:1rem; margin-bottom:0.5rem;">
                                <div style="min-width:200px;">
                                    <p class="client-label">Contact</p>
                                    <p class="client-value">{row['contact'] if row['contact'] else 'N/A'}</p>
                                </div>
                                <div style="min-width:200px;">
                                    <p class="client-label">Email</p>
                                    <p class="client-value">{row['email'] if row['email'] else 'N/A'}</p>
                                </div>
                            </div>
                            <div>
                                <p class="client-label">Notes</p>
                                <p class="client-value">{row['notes'] if row['notes'] else 'No notes added.'}</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        # Action buttons using HTML/CSS instead of columns
                        st.markdown("""
                        <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px;">
                            <div style="flex: 1; min-width: 120px;"></div>
                            <div style="flex: 1; min-width: 120px;"></div>
                            <div style="flex: 1; min-width: 120px;"></div>
                            <div style="flex: 1; min-width: 120px;"></div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Edit client button
                        if st.button("Edit Client", key=f"edit_{row.get('id', f'unknown_{i}')}"):
                            st.session_state.edit_client_id = row.get('id')
                            st.session_state.page = "edit_client"
                            st.rerun()
                        
                        # View transactions button
                        if st.button("View Transactions", key=f"view_trans_{row.get('id', f'unknown_{i}')}"):
                            st.session_state.view_client_transactions = row.get('id')
                            st.session_state.selected_client = row['name']
                            st.session_state.page = "transactions"
                            st.rerun()
                        
                        # Delete all transactions button
                        if st.button("Delete Transactions", key=f"del_trans_{row.get('id', f'unknown_{i}')}"):
                            # Show confirmation checkbox
                            confirm_del_trans = st.checkbox(
                                f"Confirm deletion of all transactions for {row['name']}", 
                                key=f"confirm_del_trans_{row.get('id', f'unknown_{i}')}"
                            )
                            
                            if confirm_del_trans:
                                # Filter out transactions for this client
                                transactions_data["transactions"] = [
                                    t for t in transactions_data["transactions"] 
                                    if t.get("client_id") != row.get('id')
                                ]
                                save_transactions(transactions_data)
                                st.success(f"✅ All transactions for {row['name']} have been deleted.")
                                st.rerun()
                        
                        # Delete client button
                        if st.button("Delete Client", key=f"del_client_{row.get('id', f'unknown_{i}')}"):
                            # Show confirmation checkbox
                            confirm_del_client = st.checkbox(
                                f"Confirm deletion of {row['name']} and all their transactions", 
                                key=f"confirm_del_client_{row.get('id', f'unknown_{i}')}"
                            )
                            
                            if confirm_del_client:
                                # Filter out this client
                                clients_data["clients"] = [
                                    c for c in clients_data["clients"] 
                                    if c.get("id") != row.get('id')
                                ]
                                # Filter out transactions for this client
                                transactions_data["transactions"] = [
                                    t for t in transactions_data["transactions"] 
                                    if t.get("client_id") != row.get('id')
                                ]
                                save_clients(clients_data)
                                save_transactions(transactions_data)
                                st.success(f"✅ Client {row['name']} and all their transactions have been deleted.")
                                st.rerun()
                
                # Always add a separator after each client (except the last one)
                # This is outside the inner container but still within the main container for this client
                if i < len(client_df) - 1:  # Only add separator if this is not the last client
                    st.markdown("""
                    <div style="padding:0.75rem 0;">
                        <div style="width:100%; height:3px; background:linear-gradient(to right, 
                            rgba(120, 80, 30, 0), 
                            rgba(120, 80, 30, 0.4), 
                            rgba(150, 100, 40, 0.7), 
                            rgba(120, 80, 30, 0.4), 
                            rgba(120, 80, 30, 0)
                        ); border-radius:1.5px;"></div>
                    </div>
                    """, unsafe_allow_html=True)
        
            # Navigation rerun logic - moved outside all containers
            if st.session_state.get('nav_changed', False):
                st.rerun()

def display_client_details(client, transactions_data):
    """Display detailed information about a client."""
    # Create a card with client details
    st.markdown(f"""
    <div class="client-card">
        <h2 style="color:#2c3e50; margin-top:0; font-family:'Geist Mono', monospace;">{client['name']}</h2>
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
        if st.button("Back to Client List", type="primary"):
            # Reset the edit_client_id to ensure we fully exit edit mode
            st.session_state.edit_client_id = None
            st.session_state.page = "clients"
            st.session_state.nav_changed = True
            st.rerun()
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
        if st.button("Back to Client List", type="primary"):
            # Reset the edit_client_id to ensure we fully exit edit mode
            st.session_state.edit_client_id = None
            st.session_state.page = "clients"
            st.session_state.nav_changed = True
            st.rerun()
        return
    
    # Initialize interest service if calendars are provided
    interest_service = None
    if interest_calendars:
        interest_service = InterestService(interest_calendars)
    
    # Style the form container
    st.markdown("""
    <div style="background-color:#FFFFFF; padding:1rem; border-radius:0.5rem; 
              border-left:4px solid #1a1a1a; margin-bottom:1rem;">
        <p style="margin:0; color:#000000;">Edit client details below. Fields marked with * are required.</p>
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
        <div style="background-color:#FFFFFF; padding:1rem; border-radius:0.5rem; margin-top:1rem; margin-bottom:1rem; position:relative;">
            <div style="position:absolute; inset:0; border-radius:0.5rem; padding:1px; background:linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.95), rgba(255,255,255,0.1)); -webkit-mask:linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0); -webkit-mask-composite:xor; mask-composite:exclude; pointer-events:none;"></div>
            <p style="margin:0; font-size:0.9rem; color:#000000;">
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
    if st.button("Back to Client List", type="primary"):
        # Reset the edit_client_id to ensure we fully exit edit mode
        st.session_state.edit_client_id = None
        st.session_state.page = "clients"
        st.session_state.nav_changed = True
        st.rerun()

def display_client_row(client, transactions_data, all_clients_data):
    """Display a single client row with actions."""
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Create a toggle for expanded view
            is_expanded = st.checkbox(
                client["name"], 
                key=f"client_toggle_{client['id']}",
                help="Click to expand/collapse client details",
            )
            
            if is_expanded:
                # Calculate client balance
                balance = calculate_client_balance(client["id"], transactions_data)
                
                # Create an indented container for client details
                with st.container():
                    st.markdown(f"""
                    <div style="margin-left: 1.5rem; margin-top: 0.5rem; padding-left: 1rem; border-left: 2px solid #333;">
                        <div style="display: flex; margin-bottom: 0.5rem;">
                            <div style="min-width: 150px; color: #a0a0a0;">Contact</div>
                            <div>{client.get('contact', 'N/A')}</div>
                        </div>
                        <div style="display: flex; margin-bottom: 0.5rem;">
                            <div style="min-width: 150px; color: #a0a0a0;">Email</div>
                            <div>{client.get('email', 'N/A')}</div>
                        </div>
                        <div style="display: flex; margin-bottom: 0.5rem;">
                            <div style="min-width: 150px; color: #a0a0a0;">Balance</div>
                            <div style="color: {('#5bc299' if balance >= 0 else '#ff6b6b')};">₹{balance:,.2f}</div>
                        </div>
                        <div style="display: flex; margin-bottom: 0.5rem;">
                            <div style="min-width: 150px; color: #a0a0a0;">Created</div>
                            <div>{client.get('created_at', 'N/A')}</div>
                        </div>
                        {f'''
                        <div style="display: flex; margin-bottom: 0.5rem;">
                            <div style="min-width: 150px; color: #a0a0a0;">Notes</div>
                            <div>{client.get('notes', 'N/A')}</div>
                        </div>
                        ''' if client.get('notes') else ''}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Add a row of action buttons using HTML/CSS instead of columns
                    st.markdown("""
                    <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px;">
                        <div style="flex: 1; min-width: 120px;"></div>
                        <div style="flex: 1; min-width: 120px;"></div>
                        <div style="flex: 1; min-width: 120px;"></div>
                        <div style="flex: 1; min-width: 120px;"></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Edit client button
                    if st.button("Edit Client", key=f"edit_{client['id']}"):
                        st.session_state.edit_client_id = client["id"]
                        st.session_state.page = "edit_client"
                        st.rerun()
                    
                    # View transactions button
                    if st.button("View Transactions", key=f"view_trans_{client['id']}"):
                        st.session_state.view_client_transactions = client["id"]
                        st.session_state.page = "transactions"
                        st.rerun()
                    
                    # Print client summary button
                    if st.button("Print Summary", key=f"print_{client['id']}"):
                        # Create printable HTML content
                        print_html = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <title>Client Summary - {client['name']}</title>
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
                                    color: #4b6bfb;
                                }}
                                .print-header p {{
                                    font-size: 9px;
                                    color: #666;
                                    margin: 0;
                                }}
                                .client-info {{
                                    margin: 10px 0;
                                    padding: 10px;
                                    border: 1px solid #eee;
                                    border-radius: 4px;
                                }}
                                .info-row {{
                                    display: flex;
                                    margin-bottom: 5px;
                                    font-size: 9px;
                                }}
                                .info-label {{
                                    width: 120px;
                                    color: #666;
                                    font-weight: bold;
                                }}
                                .info-value {{
                                    flex: 1;
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
                                    background-color: #3d8b46;
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
                                <h2>Client Summary</h2>
                                <p>Generated: {datetime.now().strftime('%d %b %Y')}</p>
                            </div>
                            
                            <div class="client-info">
                                <div class="info-row">
                                    <div class="info-label">Client Name:</div>
                                    <div class="info-value">{client['name']}</div>
                                </div>
                                <div class="info-row">
                                    <div class="info-label">Contact:</div>
                                    <div class="info-value">{client.get('contact', 'N/A')}</div>
                                </div>
                                <div class="info-row">
                                    <div class="info-label">Email:</div>
                                    <div class="info-value">{client.get('email', 'N/A')}</div>
                                </div>
                                <div class="info-row">
                                    <div class="info-label">Created On:</div>
                                    <div class="info-value">{client.get('created_at', 'N/A')}</div>
                                </div>
                                <div class="info-row">
                                    <div class="info-label">Balance:</div>
                                    <div class="info-value" style="color: {'#1e7e34' if balance >= 0 else '#dc3545'};">₹{balance:,.2f}</div>
                                </div>
                                {f'''
                                <div class="info-row">
                                    <div class="info-label">Notes:</div>
                                    <div class="info-value">{client.get('notes', 'N/A')}</div>
                                </div>
                                ''' if client.get('notes') else ''}
                            </div>
                            
                            <div class="footer">
                                Interest Calendar Application
                            </div>
                            
                            <div class="no-print" style="text-align: center; margin-top: 10px;">
                                <button onclick="window.print()" class="print-button">Print</button>
                                <button onclick="window.close()" class="print-button" style="background-color: #555;">Close</button>
                            </div>
                        </body>
                        </html>
                        """
                        
                        # Use components.html to display the printable content
                        components.html(print_html, height=0, scrolling=False)
                        st.success("Print dialog should open automatically. If it doesn't, check your browser settings.")
                    
                    # Delete all transactions button
                    if st.button("Delete Transactions", key=f"del_trans_{client['id']}"):
                        # Show confirmation checkbox
                        confirm_del_trans = st.checkbox(
                            f"Confirm deletion of all transactions for {client['name']}", 
                            key=f"confirm_del_trans_{client['id']}"
                        )
                        
                        if confirm_del_trans:
                            # Filter out transactions for this client
                            transactions_data["transactions"] = [
                                t for t in transactions_data["transactions"] 
                                if t.get("client_id") != client["id"]
                            ]
                            save_transactions(transactions_data)
                            st.success(f"✅ All transactions for {client['name']} have been deleted.")
                            st.rerun()
                    
                    # Delete client button
                    if st.button("Delete Client", key=f"del_client_{client['id']}"):
                        # Show confirmation checkbox
                        confirm_del_client = st.checkbox(
                            f"Confirm deletion of {client['name']} and all their transactions", 
                            key=f"confirm_del_client_{client['id']}"
                        )
                        
                        if confirm_del_client:
                            # Filter out this client
                            all_clients_data["clients"] = [
                                c for c in all_clients_data["clients"] 
                                if c.get("id") != client["id"]
                            ]
                            # Filter out transactions for this client
                            transactions_data["transactions"] = [
                                t for t in transactions_data["transactions"] 
                                if t.get("client_id") != client["id"]
                            ]
                            save_clients(all_clients_data)
                            save_transactions(transactions_data)
                            st.success(f"✅ Client {client['name']} and all their transactions have been deleted.")
                            st.rerun()
        
        with col2:
            # Display client statistics
            client_stats = get_client_stats(client["id"], transactions_data)
            
            # Format the display with color-coded values
            st.markdown(f"""
            <div style="text-align: right;">
                <div style="color: #2ea043; margin-bottom: 0.25rem; font-size: 0.85rem;">Received: ₹{client_stats['total_received']:,.2f}</div>
                <div style="color: #f87171; margin-bottom: 0.25rem; font-size: 0.85rem;">Paid: ₹{client_stats['total_paid']:,.2f}</div>
                <div style="color: #4b6bfb; margin-bottom: 0.25rem; font-size: 0.85rem;">Interest: ₹{client_stats['total_interest']:,.2f}</div>
                <div style="color: {('#5bc299' if client_stats['balance'] >= 0 else '#ff6b6b')}; font-weight: 500; font-size: 0.95rem;">
                    Balance: ₹{client_stats['balance']:,.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)

