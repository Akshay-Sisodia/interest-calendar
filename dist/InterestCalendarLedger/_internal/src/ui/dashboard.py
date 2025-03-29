import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import altair as alt
from datetime import datetime, timedelta
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.colored_header import colored_header
from streamlit_extras.card import card

def display_dashboard(transactions_data, clients_data, interest_calendars):
    """Display the dashboard overview with key metrics and recent activity."""
    colored_header(
        label="Dashboard Overview",
        description="Key metrics and recent activity",
        color_name="gray-40"
    )
    
    # Calculate key metrics
    total_clients = len(clients_data.get("clients", []))
    
    # Transaction metrics
    if transactions_data.get("transactions"):
        df = pd.DataFrame(transactions_data["transactions"])
        
        total_received = df["received"].sum()
        total_paid = df["paid"].sum()
        total_interest = df["interest"].sum()
        net_balance = total_received - total_paid + total_interest
        
        # Create dataframe for recent transactions
        df["date"] = pd.to_datetime(df["date"])
        recent_transactions = df.sort_values("date", ascending=False).head(5)
        
        # Add client names
        client_map = {c["id"]: c["name"] for c in clients_data.get("clients", [])}
        recent_transactions["client_name"] = recent_transactions["client_id"].map(client_map)
    else:
        total_received = 0
        total_paid = 0 
        total_interest = 0
        net_balance = 0
        recent_transactions = pd.DataFrame()
    
    # Display metrics in cards - updated for dark theme
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="dashboard-card">
            <p class="label">Total Clients</p>
            <p class="metric">{total_clients}</p>
            <div style="font-size:1.75rem; margin-bottom:0.5rem; opacity:0.7;">👥</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="dashboard-card">
            <p class="label">Total Received</p>
            <p class="metric">₹{total_received:,.2f}</p>
            <div style="font-size:1.75rem; margin-bottom:0.5rem; opacity:0.7;">💵</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="dashboard-card">
            <p class="label">Total Paid</p>
            <p class="metric">₹{total_paid:,.2f}</p>
            <div style="font-size:1.75rem; margin-bottom:0.5rem; opacity:0.7;">💸</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="dashboard-card">
            <p class="label">Total Interest</p>
            <p class="metric">₹{total_interest:,.2f}</p>
            <div style="font-size:1.75rem; margin-bottom:0.5rem; opacity:0.7;">💰</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        # Color based on balance
        balance_color = "#5bc299" if net_balance >= 0 else "#ff6b6b"
        
        st.markdown(f"""
        <div class="dashboard-card">
            <p class="label">Net Balance</p>
            <p class="metric" style="color:{balance_color};">₹{net_balance:,.2f}</p>
            <div style="font-size:1.75rem; margin-bottom:0.5rem; opacity:0.7;">⚖️</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Transaction history graph - updated for dark theme
    
    if not recent_transactions.empty:
        # Display recent transactions table below
        st.markdown("""
        <h3 style="margin-top:2rem; margin-bottom:1rem;">Recent Transactions</h3>
        """, unsafe_allow_html=True)
        
        # Check available columns and create a display-friendly copy
        available_columns = ['client_name', 'date', 'received', 'paid', 'interest']
        if 'notes' in recent_transactions.columns:
            available_columns.append('notes')
        
        # Create a cleaner table for recent transactions
        recent_display = recent_transactions[available_columns].copy()
        
        # Format the date column to DD MM YYYY format without time
        if 'date' in recent_display.columns:
            recent_display['date'] = recent_display['date'].dt.strftime('%d %b %Y')
        
        # Rename columns for display
        column_mapping = {
            'client_name': 'Client',
            'date': 'Date',
            'notes': 'Notes',
            'received': 'Received (₹)',
            'paid': 'Paid (₹)',
            'interest': 'Interest (₹)'
        }
        
        # Apply only the mappings that exist in our DataFrame
        display_columns = {col: column_mapping[col] for col in available_columns if col in column_mapping}
        recent_display.rename(columns=display_columns, inplace=True)
        
        # Format the currency columns if they exist
        if 'Received (₹)' in recent_display.columns:
            recent_display['Received (₹)'] = recent_display['Received (₹)'].apply(lambda x: f"{x:,.2f}" if x > 0 else "-")
        if 'Paid (₹)' in recent_display.columns:
            recent_display['Paid (₹)'] = recent_display['Paid (₹)'].apply(lambda x: f"{x:,.2f}" if x > 0 else "-")
        if 'Interest (₹)' in recent_display.columns:
            recent_display['Interest (₹)'] = recent_display['Interest (₹)'].apply(lambda x: f"{x:,.2f}")
        
        # Style and display the table
        st.dataframe(
            recent_display,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No transaction data available. Add transactions to see the dashboard.")
