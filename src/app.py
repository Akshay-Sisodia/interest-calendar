"""
Main application module for the Interest Calendar Ledger.
This module serves as the entry point for the Streamlit application.
"""

import streamlit as st
from datetime import datetime
from streamlit_extras.colored_header import colored_header

# Import utility functions
from .utils.helpers import load_custom_css

# Import data loaders
from .data.data_loader import (
    load_interest_calendars,
    load_clients,
    load_transactions,
    save_transactions
)

# Import services
from .services.interest_service import InterestService

# Import UI components
from .ui.dashboard import display_dashboard
from .ui.client_view import client_management, edit_client
from .ui.transaction_view import transactions_section
from .ui.calendar_view import display_interest_calendars_tab

def main():
    """Main application entry point."""
    # Apply custom CSS
    load_custom_css()
    
    # Initialize session state for navigation if not already set
    if 'page' not in st.session_state:
        st.session_state.page = "dashboard"
    
    # Initialize other session state variables if needed
    if 'edit_client_id' not in st.session_state:
        st.session_state.edit_client_id = None
    
    if 'view_client_transactions' not in st.session_state:
        st.session_state.view_client_transactions = None
    
    # App header with logo and title - enigmatic black theme
    st.markdown(f"""
    <div style="display:flex; align-items:center; padding:1.8rem; 
                margin-bottom:2rem; background: linear-gradient(90deg, #000000, #0a0a0a); 
                border-radius:1rem; box-shadow: 0 8px 16px rgba(0,0,0,0.3);
                border:1px solid #1a1a1a;">
        <div style="display:flex; align-items:center; flex-grow:1;">
            <div style="font-size:2.5rem; margin-right:1rem; color: white;">💰</div>
            <h1 style="margin:0; color: white;
                      font-weight:700; font-size:2.4rem;">Interest Calendar Ledger</h1>
        </div>
        <div style="background-color:#121212; padding:0.8rem 1.2rem; border-radius:0.8rem; 
                   border:1px solid #1a1a1a; box-shadow:0 4px 8px rgba(0,0,0,0.15);
                   display:flex; align-items:center;">
            <span style="color:#cccccc; font-size:1rem; font-weight:500; margin-right:0.5rem;">
                📅
            </span>
            <span style="color:#e0e0e0; font-size:1rem; font-weight:500;">
                {datetime.now().strftime("%d %b %Y")}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    interest_calendars = load_interest_calendars()
    clients_data = load_clients()
    transactions_data = load_transactions()
    
    # Initialize services
    interest_service = InterestService(interest_calendars)
    
    # Recalculate all transaction interest values when the app starts
    with st.spinner("Updating calculations..."):
        updated_transactions = interest_service.recalculate_all_transaction_interest(transactions_data)
        if updated_transactions != transactions_data:
            save_transactions(updated_transactions)
            transactions_data = updated_transactions
    
    # Side menu with icon buttons - updated for dark theme
    col_menu, col_content = st.columns([1, 5])
    
    with col_menu:
        # Navigation header with styling consistent with Transaction Management
        colored_header(
            label=" Navigation",
            description="Track and manage interest calculations with ease",
            color_name="gray-40"
        )
        
        # Style the navigation buttons like dashboard cards
        st.markdown("""
        <style>
        /* Custom styling for navigation buttons to look like cards */
        div.nav-button-container .stButton > button {
            width: 100%;
            background-color: var(--bg-secondary) !important;
            border-radius: 0.8rem !important;
            padding: 0.75rem 1rem !important;
            margin-bottom: 0.5rem !important;
            border: 1px solid var(--border-color) !important;
            box-shadow: 0 4px 8px var(--shadow-color) !important;
            transition: all 0.3s ease !important;
            display: flex !important;
            align-items: center !important;
            text-transform: none !important;
            font-size: 1rem !important;
            justify-content: flex-start !important;
            letter-spacing: normal !important;
        }
        
        div.nav-button-container .stButton > button:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 8px 16px rgba(0,0,0,0.25) !important;
            border-color: var(--accent-secondary) !important;
        }
        
        div.nav-button-container .stButton > button.active {
            border-left: 4px solid var(--accent-primary) !important;
            background-color: var(--bg-tertiary) !important;
        }
        
        div.nav-button-container .stButton > button .icon {
            font-size: 1.5rem;
            margin-right: 0.8rem;
            opacity: 0.9;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Define on_click handlers for navigation
        def handle_nav_click(new_page):
            # Split the emoji from the page name
            page_name = new_page.split(" ")[1].lower()
            
            # Only change page if needed or if we're not on a special page
            if st.session_state.page not in ["edit_client", "transactions"] or \
               (st.session_state.page == "transactions" and st.session_state.get("view_client_transactions") is None):
                st.session_state.page = page_name
                st.session_state.menu_selection = new_page
                st.session_state.nav_changed = True
        
        # Navigation buttons with on_click handlers
        menu_options = ["📊 Dashboard", "👥 Clients", "💸 Transactions", "📅 Calendars"]
        
        current_menu = st.session_state.get("menu_selection", "📊 Dashboard")
        
        # Add custom container class for targeting
        st.markdown('<div class="nav-button-container">', unsafe_allow_html=True)
        
        for option in menu_options:
            # Check if this option is the current page
            is_active = option == current_menu
            button_type = "primary" if is_active else "secondary"
            
            # Use standard Streamlit buttons but style them like cards
            st.button(
                option,
                key=f"nav_{option}",
                type=button_type,
                on_click=handle_nav_click,
                args=(option,),
                use_container_width=True
            )
            
        # Close the custom container div
        st.markdown('</div>', unsafe_allow_html=True)
            
        # Check if we need to rerun based on navigation state changes
        if 'nav_changed' not in st.session_state:
            st.session_state.nav_changed = False
            
        if st.session_state.nav_changed:
            st.session_state.nav_changed = False
            st.rerun()
    
    # Main content area - wrapped in a container for better styling
    with col_content:
        if st.session_state.page == "dashboard":
            display_dashboard(transactions_data, clients_data, interest_calendars)
        elif st.session_state.page == "clients":
            client_management(clients_data, transactions_data, interest_calendars)
        elif st.session_state.page == "transactions":
            # Add back button if viewing client-specific transactions
            if st.session_state.get("view_client_transactions") is not None:
                def handle_back_click():
                    st.session_state.view_client_transactions = None
                    st.session_state.page = "clients"
                    st.session_state.nav_changed = True
                
                st.button(
                    "← Back to Clients", 
                    type="primary",
                    on_click=handle_back_click
                )
                # Set the active tab to "All Transactions" when viewing client transactions
                st.session_state.active_tab = "all_transactions"
            
            transactions_section(transactions_data, clients_data, interest_calendars, interest_service)
        elif st.session_state.page == "calendars":
            display_interest_calendars_tab(interest_calendars, interest_service)
        elif st.session_state.page == "edit_client":
            edit_client(clients_data, transactions_data, interest_calendars)

if __name__ == "__main__":
    main()
