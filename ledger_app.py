import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json

# Set page configuration
st.set_page_config(page_title="Client Ledger System", layout="wide")

# File paths
INTEREST_CALENDAR_FILE = "interest_calendar.csv"
TRANSACTIONS_FILE = "transactions.json"
CLIENTS_FILE = "clients.json"


# Function to load interest calendar
def load_interest_calendar():
    if os.path.exists(INTEREST_CALENDAR_FILE):
        return pd.read_csv(INTEREST_CALENDAR_FILE, index_col=0)
    else:
        # Use the provided data as default
        data = """Day/Month,Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec
1,311,280,251,219,189,157,126,94,62,32,1,-29"""
        import io

        df = pd.read_csv(io.StringIO(data), index_col=0)
        df.to_csv(INTEREST_CALENDAR_FILE)
        return df


# Function to load clients
def load_clients():
    if os.path.exists(CLIENTS_FILE):
        with open(CLIENTS_FILE, "r") as f:
            try:
                data = json.load(f)
                # Initialize opening_balance if not present
                for client in data["clients"]:
                    if "opening_balance" not in client:
                        client["opening_balance"] = 0.0
                return data
            except json.JSONDecodeError:
                return {"clients": []}
    else:
        return {"clients": []}


# Function to save clients
def save_clients(data):
    with open(CLIENTS_FILE, "w") as f:
        json.dump(data, f, indent=4)


# Function to load transactions
def load_transactions():
    if os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"transactions": []}
    else:
        return {"transactions": []}


# Function to save transactions
def save_transactions(data):
    with open(TRANSACTIONS_FILE, "w") as f:
        json.dump(data, f, indent=4)


# Function to get interest value from calendar
def get_interest_value(date_str, interest_calendar):
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        day = date_obj.day
        month = date_obj.strftime("%b")
        month = month.title()
        month_map = {m[:3].title(): m for m in interest_calendar.columns}
        month_key = month_map.get(month)

        if month_key and day in interest_calendar.index:
            return float(interest_calendar.loc[day, month_key])
        else:
            st.warning(f"Interest value not found for date: {date_str}")
            return 0.0
    except Exception as e:
        st.error(f"Error getting interest value: {e}")
        return 0.0


# Function to calculate interest
def calculate_interest(amount, rate, interest_value):
    return (amount * rate * interest_value) / 360.0


# Client Management Section
def client_management():
    st.header("Client Management")

    # Load clients data
    clients_data = load_clients()

    # Add new client section
    st.subheader("Add New Client")
    col1, col2 = st.columns(2)

    with col1:
        new_client_name = st.text_input("Client Name")
        new_client_contact = st.text_input("Contact Number")
        opening_balance = st.number_input(
            "Opening Balance (₹)", min_value=0.0, step=100.0, format="%.2f"
        )

    with col2:
        new_client_email = st.text_input("Email")
        new_client_notes = st.text_area("Notes", key="new_client_notes")

    if st.button("Add Client"):
        if new_client_name:
            new_client = {
                "id": len(clients_data["clients"]) + 1,
                "name": new_client_name,
                "contact": new_client_contact,
                "email": new_client_email,
                "notes": new_client_notes,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "opening_balance": float(opening_balance),
            }
            clients_data["clients"].append(new_client)
            save_clients(clients_data)
            st.success("Client added successfully!")
            st.rerun()
        else:
            st.error("Client name is required!")

    # View/Edit clients section
    st.subheader("Client List")
    if clients_data["clients"]:
        client_df = pd.DataFrame(clients_data["clients"])
        edited_df = st.data_editor(
            client_df,
            column_config={
                "id": None,
                "name": st.column_config.TextColumn("Name"),
                "contact": st.column_config.TextColumn("Contact"),
                "email": st.column_config.TextColumn("Email"),
                "notes": st.column_config.TextColumn("Notes"),
                "created_at": st.column_config.TextColumn("Created At", disabled=True),
                "opening_balance": st.column_config.NumberColumn(
                    "Opening Balance (₹)",
                    format="%.2f",
                    step=100.0,
                    min_value=0.0,
                ),
            },
            hide_index=True,
            use_container_width=True,
        )

        if st.button("Save Client Changes"):
            clients_data["clients"] = edited_df.to_dict("records")
            save_clients(clients_data)
            st.success("Changes saved successfully!")
    else:
        st.info("No clients added yet.")


# Transaction Management Section
def transaction_management():
    st.header("Transaction Management")

    # Load data
    clients_data = load_clients()
    transactions_data = load_transactions()
    interest_calendar = load_interest_calendar()

    # Add new transaction section
    st.subheader("Add New Transaction")

    # Client selection with search/autocomplete
    client_names = [client["name"] for client in clients_data["clients"]]
    selected_client = (
        st.selectbox("Select Client", options=client_names, key="client_select")
        if client_names
        else st.error("Please add clients first!")
    )

    if selected_client:
        col1, col2, col3 = st.columns(3)

        with col1:
            new_date = st.date_input("Date", datetime.now())
            transaction_type = st.selectbox("Transaction Type", ["Received", "Paid"])

        with col2:
            amount = st.number_input(
                "Amount (₹)", min_value=0.0, step=100.0, format="%.2f"
            )
            interest_rate = (
                st.number_input(
                    "Interest Rate (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=5.0,
                    step=0.25,
                )
                / 100.0
            )

        with col3:
            notes = st.text_area("Notes", key="new_transaction_notes")

        if st.button("Add Transaction"):
            date_str = new_date.strftime("%Y-%m-%d")
            interest_value = get_interest_value(date_str, interest_calendar)

            # Calculate interest
            transaction_amount = amount if transaction_type == "Received" else -amount
            # Make interest negative for paid transactions
            interest = calculate_interest(
                abs(transaction_amount), interest_rate, interest_value
            )
            if transaction_type == "Paid":
                interest = -interest

            # Find client ID
            client_id = next(
                client["id"]
                for client in clients_data["clients"]
                if client["name"] == selected_client
            )

            new_transaction = {
                "id": len(transactions_data["transactions"]) + 1,
                "client_id": client_id,
                "date": date_str,
                "received": float(amount) if transaction_type == "Received" else 0.0,
                "paid": float(amount) if transaction_type == "Paid" else 0.0,
                "interest_rate": float(interest_rate),
                "interest_value": float(interest_value),
                "interest": round(float(interest), 2),
                "notes": notes,
            }

            if "transactions" not in transactions_data:
                transactions_data["transactions"] = []

            transactions_data["transactions"].append(new_transaction)
            save_transactions(transactions_data)
            st.success("Transaction added successfully!")
            st.rerun()

    # View all transactions
    st.subheader("All Transactions")
    if transactions_data.get("transactions"):
        # Create DataFrame with client names
        df = pd.DataFrame(transactions_data["transactions"])
        df["date"] = pd.to_datetime(df["date"])

        # Add client names
        client_map = {c["id"]: c["name"] for c in clients_data["clients"]}
        df["client_name"] = df["client_id"].map(client_map)

        # Reorder columns to show client name first
        cols = [
            "client_name",
            "date",
            "received",
            "paid",
            "interest_rate",
            "interest_value",
            "interest",
            "notes",
        ]
        df = df[cols]

        # Display editable table
        edited_df = st.data_editor(
            df,
            column_config={
                "client_name": st.column_config.Column("Client", disabled=True),
                "date": st.column_config.DateColumn("Date"),
                "received": st.column_config.NumberColumn(
                    "Received (₹)", format="%.2f"
                ),
                "paid": st.column_config.NumberColumn("Paid (₹)", format="%.2f"),
                "interest_rate": st.column_config.NumberColumn(
                    "Interest Rate (%)", format="%.2f"
                ),
                "interest_value": st.column_config.NumberColumn(
                    "Interest Value", format="%.2f"
                ),
                "interest": st.column_config.NumberColumn(
                    "Interest (₹)", format="%.2f", disabled=True
                ),
                "notes": st.column_config.TextColumn("Notes"),
            },
            hide_index=True,
            use_container_width=True,
        )

        # Calculate totals
        total_row = pd.DataFrame(
            [
                {
                    "client_name": "Total",
                    "received": edited_df["received"].sum(),
                    "paid": edited_df["paid"].sum(),
                    "interest": edited_df["interest"].sum(),
                }
            ]
        )

        st.markdown("### Totals")
        st.dataframe(
            total_row,
            column_config={
                "received": st.column_config.NumberColumn(
                    "Received (₹)", format="%.2f"
                ),
                "paid": st.column_config.NumberColumn("Paid (₹)", format="%.2f"),
                "interest": st.column_config.NumberColumn(
                    "Interest (₹)", format="%.2f"
                ),
            },
            hide_index=True,
            use_container_width=True,
        )

        if st.button("Save Changes"):
            # Update transactions with edited values
            edited_df["date"] = edited_df["date"].dt.strftime("%Y-%m-%d")
            # Recalculate interest for each row
            for i, row in edited_df.iterrows():
                # Calculate interest with proper sign
                amount = row["received"] if row["received"] > 0 else -row["paid"]
                interest = calculate_interest(
                    abs(amount),
                    row["interest_rate"],
                    row["interest_value"],
                )
                if amount < 0:  # For paid entries
                    interest = -interest
                edited_df.at[i, "interest"] = round(float(interest), 2)

            # Update transactions data
            for i, row in edited_df.iterrows():
                client_id = next(
                    client["id"]
                    for client in clients_data["clients"]
                    if client["name"] == row["client_name"]
                )
                transactions_data["transactions"][i] = {
                    "id": i + 1,
                    "client_id": client_id,
                    "date": row["date"],
                    "received": float(row["received"]),
                    "paid": float(row["paid"]),
                    "interest_rate": float(row["interest_rate"]),
                    "interest_value": float(row["interest_value"]),
                    "interest": float(row["interest"]),
                    "notes": row["notes"],
                }

            save_transactions(transactions_data)
            st.success("Changes saved successfully!")
            st.rerun()
    else:
        st.info("No transactions yet.")


# Reports Section
def reports_section():
    st.header("Reports")

    # Load data
    clients_data = load_clients()
    transactions_data = load_transactions()

    if not transactions_data.get("transactions"):
        st.info("No transactions available for reporting.")
        return

    # Create DataFrame with client names
    df = pd.DataFrame(transactions_data["transactions"])
    df["date"] = pd.to_datetime(df["date"])
    client_map = {c["id"]: c["name"] for c in clients_data["clients"]}
    df["client_name"] = df["client_id"].map(client_map)

    # Client selection for ledger view
    st.subheader("Client Ledger")
    selected_client = st.selectbox(
        "Select Client", options=list(client_map.values()), key="report_client_select"
    )

    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", df["date"].min())
    with col2:
        end_date = st.date_input("End Date", df["date"].max())

    # Filter data
    mask = (
        (df["client_name"] == selected_client)
        & (df["date"].dt.date >= start_date)
        & (df["date"].dt.date <= end_date)
    )
    filtered_df = df[mask].copy()

    if not filtered_df.empty:
        # Get client's opening balance
        client_data = next(
            client
            for client in clients_data["clients"]
            if client["name"] == selected_client
        )
        opening_balance = float(client_data.get("opening_balance", 0.0))

        # Calculate running balance including opening balance
        filtered_df["balance"] = opening_balance + (
            filtered_df["received"].cumsum() - filtered_df["paid"].cumsum()
        )
        filtered_df["interest_balance"] = filtered_df["interest"].cumsum()

        # Display ledger
        st.dataframe(
            filtered_df[
                [
                    "date",
                    "received",
                    "paid",
                    "interest",
                    "balance",
                    "interest_balance",
                    "notes",
                ]
            ],
            column_config={
                "date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
                "received": st.column_config.NumberColumn(
                    "Received (₹)", format="%.2f"
                ),
                "paid": st.column_config.NumberColumn("Paid (₹)", format="%.2f"),
                "interest": st.column_config.NumberColumn(
                    "Interest (₹)", format="%.2f"
                ),
                "balance": st.column_config.NumberColumn("Balance (₹)", format="%.2f"),
                "interest_balance": st.column_config.NumberColumn(
                    "Interest Balance (₹)", format="%.2f"
                ),
            },
            hide_index=True,
            use_container_width=True,
        )

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Opening Balance", f"₹{opening_balance:,.2f}")
            st.metric("Total Received", f"₹{filtered_df['received'].sum():,.2f}")
        with col2:
            st.metric("Total Paid", f"₹{filtered_df['paid'].sum():,.2f}")
        with col3:
            st.metric("Balance", f"₹{filtered_df['balance'].iloc[-1]:,.2f}")
        with col4:
            st.metric("Total Interest", f"₹{filtered_df['interest'].sum():,.2f}")

        # Export option
        if st.button("Export to Excel"):
            output_file = (
                f"ledger_{selected_client}_{datetime.now().strftime('%Y%m%d')}.xlsx"
            )
            filtered_df.to_excel(output_file, index=False)
            st.success(f"Exported to {output_file}")
    else:
        st.info("No transactions found for the selected criteria.")


# Main App
def main():
    st.title("Client Ledger System")

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Clients", "Transactions", "Reports", "Interest Calendar"]
    )

    with tab1:
        client_management()

    with tab2:
        transaction_management()

    with tab3:
        reports_section()

    with tab4:
        st.header("Interest Calendar")
        interest_calendar = load_interest_calendar()

        # Show current calendar in editable format
        edited_calendar = st.data_editor(
            interest_calendar,
            key="interest_calendar_editor",
            use_container_width=True,
            num_rows="fixed",
            hide_index=False,
        )

        if st.button("Save Calendar Changes"):
            # Save calendar changes
            edited_calendar.to_csv(INTEREST_CALENDAR_FILE)

            # Load transactions and recalculate interest
            transactions_data = load_transactions()
            if transactions_data.get("transactions"):
                modified = False
                for transaction in transactions_data["transactions"]:
                    date_str = transaction["date"]
                    new_interest_value = get_interest_value(date_str, edited_calendar)

                    # Only update if interest value has changed
                    if new_interest_value != transaction["interest_value"]:
                        modified = True
                        transaction["interest_value"] = float(new_interest_value)
                        # Recalculate interest
                        amount = (
                            transaction["received"]
                            if transaction["received"] > 0
                            else -transaction["paid"]
                        )
                        interest = calculate_interest(
                            abs(amount),
                            transaction["interest_rate"],
                            new_interest_value,
                        )
                        if amount < 0:  # For paid entries
                            interest = -interest
                        transaction["interest"] = round(float(interest), 2)

                if modified:
                    save_transactions(transactions_data)
                    st.success("Calendar updated and all transactions recalculated!")
                else:
                    st.success("Calendar updated successfully!")
            else:
                st.success("Calendar updated successfully!")


if __name__ == "__main__":
    main()
