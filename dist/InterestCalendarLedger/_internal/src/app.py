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
from .ui.report_view import display_report_view

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
    
    # App header with logo and title - styled light theme with blue accents
    st.markdown(f"""
    <div style="display:flex; align-items:center; padding:1.8rem; 
                margin-bottom:2rem; background: linear-gradient(90deg, #eef2f7, #e6ebf2); 
                border-radius:1rem; box-shadow: 0 8px 16px rgba(58, 90, 232, 0.1);
                border:1px solid #d1d9e6; position:relative; overflow:hidden;">
        <div style="position:absolute; top:0; right:0; bottom:0; left:0; background-image: 
                    radial-gradient(circle at 25px 25px, rgba(75, 107, 251, 0.03) 2%, transparent 0%), 
                    radial-gradient(circle at 75px 75px, rgba(75, 107, 251, 0.03) 2%, transparent 0%);
                    background-size: 100px 100px; opacity:0.8;"></div>
        <div style="display:flex; align-items:center; flex-grow:1; position:relative; z-index:1;">
            <div style="font-size:2.5rem; margin-right:1rem; color:#4b6bfb;">💰</div>
            <h1 style="margin:0; color:#2c3e50; font-weight:700; font-size:2.4rem;">Interest Calendar Ledger</h1>
        </div>
        <div style="background-color:#f8f9fb; padding:0.8rem 1.2rem; border-radius:0.8rem; 
                   border:1px solid #d1d9e6; box-shadow:0 4px 8px rgba(58, 90, 232, 0.05);
                   display:flex; align-items:center; position:relative; z-index:1;">
            <span style="color:#485b73; font-size:1rem; font-weight:500; margin-right:0.5rem;">
                📅
            </span>
            <span style="color:#2c3e50; font-size:1rem; font-weight:500;">
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
    
    # Side menu with icon buttons - updated for light theme
    col_menu, col_content = st.columns([1, 5])
    
    with col_menu:
        # Navigation header with styling consistent with Transaction Management
        colored_header(
            label=" Navigation",
            description="Track and manage interest calculations with ease",
            color_name="gray-40"
        )
    
        # Define on_click handlers for navigation
        def handle_nav_click(new_page):
            # Split the emoji from the page name
            page_name = new_page.split(" ")[1].lower()
            
            # Only prevent navigation from edit_client page, but allow navigation from transactions 
            # regardless of view_client_transactions state
            if st.session_state.page != "edit_client":
                # Remember previous page
                previous_page = st.session_state.page
                
                st.session_state.page = page_name
                st.session_state.menu_selection = new_page
                st.session_state.nav_changed = True
                
                # If navigating away from client-specific transactions, clear those states
                # but preserve filter settings
                if previous_page == "transactions" and st.session_state.get("view_client_transactions") is not None and page_name != "transactions":
                    # Remember the client for filter before clearing view_client_transactions
                    if "transaction_filter_client" not in st.session_state:
                        client_id = st.session_state.view_client_transactions
                        client_name = next((c["name"] for c in clients_data["clients"] if c["id"] == client_id), "All Clients")
                        st.session_state.transaction_filter_client = client_name
                        
                    # Clear navigation states but not filter states
                    st.session_state.view_client_transactions = None
                    if "selected_client" in st.session_state:
                        del st.session_state.selected_client
        
        # Navigation buttons with on_click handlers
        menu_options = ["📊 Dashboard", "👥 Clients", "💸 Transactions", "📅 Calendars", "📝 Reports"]
        
        current_menu = st.session_state.get("menu_selection", "📊 Dashboard")
        
        
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
            # Set the active tab to "All Transactions" when viewing client transactions
            if st.session_state.get("view_client_transactions") is not None:
                st.session_state.active_tab = "all_transactions"
            
            transactions_section(transactions_data, clients_data, interest_calendars, interest_service)
        elif st.session_state.page == "calendars":
            display_interest_calendars_tab(interest_calendars, interest_service)
        elif st.session_state.page == "reports":
            display_report_view(transactions_data, clients_data, interest_calendars)
        elif st.session_state.page == "edit_client":
            edit_client(clients_data, transactions_data, interest_calendars)

if __name__ == "__main__":
    main()
