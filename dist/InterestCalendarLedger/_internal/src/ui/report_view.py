"""
Report view module for the Interest Calendar Ledger application.
This module handles the report generation view that shows client summaries.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components
from streamlit_extras.colored_header import colored_header
from streamlit_extras.card import card
from ..utils.helpers import sanitize_html

def display_report_view(transactions_data, clients_data, interest_calendars):
    """Display the financial report view."""
    # Use colored_header for consistent styling
    colored_header(
        label="Financial Reports",
        description="Generate financial reports for your clients",
        color_name="gray-40"
    )
    
    # Get client data
    clients = clients_data.get("clients", [])
    transactions = transactions_data.get("transactions", [])
    
    if not clients:
        st.warning("No clients available. Please add clients in the Clients section.")
        return
    
    # Create client map for easy lookup
    client_map = {client["id"]: client["name"] for client in clients}
    
    # Calculate financial data for all clients regardless of transaction activity
    client_financial_data = []
    
    for client in clients:
        client_id = client.get("id")
        client_name = client.get("name")
        
        # Filter transactions for this client
        client_transactions = [t for t in transactions if t.get("client_id") == client_id]
        
        # Calculate components
        received = sum(t.get("received", 0) for t in client_transactions)
        paid = sum(t.get("paid", 0) for t in client_transactions)
        interest = sum(t.get("interest", 0) for t in client_transactions)
        
        # Calculate principal (received - paid)
        principal = received - paid
        
        # Total balance is principal + interest
        balance = principal + interest
        
        # Get the most recent transaction to determine interest rate
        if client_transactions:
            recent_txn = max(client_transactions, key=lambda x: x.get("date", ""))
            interest_rate = recent_txn.get("interest_rate", 0)
        else:
            # Default interest rate if no transactions
            interest_rate = 0
            
        client_financial_data.append({
            "client_id": client_id,
            "client_name": client_name,
            "principal": principal,
            "interest": interest,
            "balance": balance,
            "interest_rate": interest_rate
        })
    
    # Convert to DataFrame for display
    df = pd.DataFrame(client_financial_data)
    
    # Show print button
    col_print, _ = st.columns([1, 5])
    with col_print:
        if st.button("Print Report", key="print_report",):
            # Generate the HTML report
            html_report = generate_html_report(df)
            
            # Escape any backticks in the HTML report to prevent JavaScript template literal issues
            html_report = html_report.replace("`", "\\`")
            
            # Use a direct approach to open the print window
            components.html(
                """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Printing Client Report</title>
                    <script>
                        // Create and open print window immediately when this component loads
                        (function() {
                            var reportWindow = window.open('', '_blank');
                            if (!reportWindow) {
                                alert("Pop-up blocked! Please allow pop-ups for this site to print reports.");
                                return;
                            }
                            
                            var reportContent = `
                                <!DOCTYPE html>
                                <html>
                                <head>
                                    <title>Client Financial Report</title>
                                    <style>
                                        body { 
                                            font-family: Arial, sans-serif; 
                                            background-color: white; 
                                            color: black;
                                            padding: 20px;
                                        }
                                        table { 
                                            width: 100%; 
                                            border-collapse: collapse; 
                                            margin-bottom: 30px;
                                        }
                                        th, td { 
                                            border: 1px solid #ddd; 
                                            padding: 8px; 
                                            text-align: left; 
                                        }
                                        th { 
                                            background-color: #f2f2f2; 
                                            font-weight: bold;
                                        }
                                        tr:nth-child(even) { 
                                            background-color: #f9f9f9; 
                                        }
                                        h2 { 
                                            text-align: center; 
                                            margin-bottom: 5px;
                                        }
                                        .print-header { 
                                            margin-bottom: 20px; 
                                            text-align: center; 
                                        }
                                        .summary { 
                                            margin: 20px 0; 
                                            padding: 10px; 
                                            background-color: #f8f9fa; 
                                            border-radius: 5px; 
                                        }
                                        @media print {
                                            body { 
                                                print-color-adjust: exact; 
                                                -webkit-print-color-adjust: exact; 
                                            }
                                            .no-print { 
                                                display: none; 
                                            }
                                            button { 
                                                display: none; 
                                            }
                                        }
                                    </style>
                                </head>
                                <body>
                                    <div class="print-header">
                                        <h2>Client Financial Report</h2>
                                        <p>Date: """ + datetime.now().strftime('%d %b %Y') + """</p>
                                    </div>
                                    """ + html_report + """
                                    <div class="no-print" style="margin-top: 20px; text-align: center;">
                                        <button onclick="window.close()" style="padding: 10px 20px; background-color: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;">Close Window</button>
                                    </div>
                                </body>
                                </html>
                            `;
                            
                            reportWindow.document.open();
                            reportWindow.document.write(reportContent);
                            reportWindow.document.close();
                            
                            // Automatically trigger print
                            setTimeout(function() {
                                reportWindow.print();
                            }, 500);
                        })();
                    </script>
                </head>
                <body>
                    <div style="text-align: center; padding: 10px;">
                        <p>Opening print window... If nothing happens, please check your pop-up blocker settings.</p>
                    </div>
                </body>
                </html>
                """,
                height=50,
                scrolling=False,
            )
            
            # Show a success message in the main interface
            st.success("Print window opened. If nothing happened, please check your pop-up blocker settings.")
    
    # Display the client financial report as a table
    st.markdown("### Client Financial Summary")
    
    # Display the report as a DataFrame
    st.dataframe(
        df,
        column_config={
            "client_name": "Client",
            "principal": st.column_config.NumberColumn("Principal", format="₹%.2f"),
            "interest": st.column_config.NumberColumn("Interest", format="₹%.2f"),
            "balance": st.column_config.NumberColumn("Total Balance", format="₹%.2f"),
            "interest_rate": st.column_config.NumberColumn("Rate of Interest", format="%.2f%%")
        },
        hide_index=True,
        use_container_width=True
    )

def generate_html_report(df):
    """Generate HTML representation of the client financial report."""
    # Create a copy of the DataFrame for formatting
    df_copy = df.copy()
    
    # Format numeric columns
    df_copy['principal'] = df_copy['principal'].apply(lambda x: f"₹{x:,.2f}")
    df_copy['interest'] = df_copy['interest'].apply(lambda x: f"₹{x:,.2f}")
    df_copy['balance'] = df_copy['balance'].apply(lambda x: f"₹{x:,.2f}")
    df_copy['interest_rate'] = df_copy['interest_rate'].apply(lambda x: f"{x}%")
    
    # Create HTML table
    html = '<table border="1" cellspacing="0" cellpadding="5" style="width:100%;">'
    
    # Add header row
    html += '''
    <thead>
        <tr>
            <th>Client</th>
            <th>Principal</th>
            <th>Interest</th>
            <th>Total Balance</th>
            <th>Rate of Interest</th>
        </tr>
    </thead>
    '''
    
    # Add data rows
    html += '<tbody>'
    for _, row in df_copy.iterrows():
        html += f'''
        <tr>
            <td>{row['client_name']}</td>
            <td>{row['principal']}</td>
            <td>{row['interest']}</td>
            <td>{row['balance']}</td>
            <td>{row['interest_rate']}</td>
        </tr>
        '''
    html += '</tbody>'
    
    # Add totals row
    total_principal = sum(df['principal'])
    total_interest = sum(df['interest'])
    total_balance = sum(df['balance'])
    
    html += f'''
    <tfoot>
        <tr style="font-weight:bold; background-color:#f2f2f2;">
            <td>Totals</td>
            <td>₹{total_principal:,.2f}</td>
            <td>₹{total_interest:,.2f}</td>
            <td>₹{total_balance:,.2f}</td>
            <td></td>
        </tr>
    </tfoot>
    '''
    
    # Close the table
    html += '</table>'
    
    # Add summary section
    html += f'''
    <div class="summary">
        <h3>Financial Summary</h3>
        <p><strong>Total Clients:</strong> {len(df)}</p>
        <p><strong>Total Principal:</strong> ₹{total_principal:,.2f}</p>
        <p><strong>Total Interest:</strong> ₹{total_interest:,.2f}</p>
        <p><strong>Grand Total Balance:</strong> ₹{total_balance:,.2f}</p>
        <p><strong>Report Date:</strong> {datetime.now().strftime('%d %b %Y')}</p>
    </div>
    '''
    
    return html 