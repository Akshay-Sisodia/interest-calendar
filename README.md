# Interest Calendar Ledger

A Streamlit application for managing interest calculations using custom calendars.

## Overview

This application helps manage interest calculations for financial transactions using custom interest calendars. It supports both Diwali and Financial Year calendars, and provides functionality for managing clients, transactions, and calendars.

## Features

- Dashboard with key metrics and visualizations
- Client management (add, edit, view, delete)
- Transaction management with interest calculations
- Interest calendar management with support for Diwali and Financial Year calendars
- Combined and individual calendar views

## Project Structure

The application has been modularized for better maintainability and organization:

```
interest-calendar/
├── src/                      # Source code directory
│   ├── utils/                # Utility functions
│   │   ├── __init__.py
│   │   └── helpers.py        # Helper functions (CSS, formatting, etc.)
│   ├── data/                 # Data access layer
│   │   ├── __init__.py
│   │   └── data_loader.py    # Functions for loading and saving data
│   ├── models/               # Data models
│   │   ├── __init__.py
│   │   ├── calendar.py       # Calendar model
│   │   ├── client.py         # Client model
│   │   └── transaction.py    # Transaction model
│   ├── services/             # Business logic
│   │   ├── __init__.py
│   │   └── interest_service.py # Interest calculation service
│   ├── ui/                   # User interface components
│   │   ├── __init__.py
│   │   ├── dashboard.py      # Dashboard UI
│   │   ├── calendar_view.py  # Calendar management UI
│   │   ├── client_view.py    # Client management UI
│   │   └── transaction_view.py # Transaction management UI
│   ├── __init__.py
│   └── app.py                # Main application logic
├── interest_calendars/       # Directory for calendar CSV files
├── clients.json              # Client data
├── transactions.json         # Transaction data
├── ledger_app.py             # Original monolithic application
├── ledger_app_modular.py     # Entry point for modular application
└── README.md                 # This file
```

## Running the Application

To run the application, use the following command:

```bash
streamlit run ledger_app_modular.py
```

## Data Files

- `clients.json`: Contains client information
- `transactions.json`: Contains transaction data
- `interest_calendars/`: Directory containing CSV files for different calendars
  - `Diwali_YYYY-YYYY.csv`: Diwali calendar files
  - `Financial_Year_YYYY-YYYY.csv`: Financial Year calendar files

## Dependencies

- streamlit
- pandas
- plotly
- altair
- streamlit-extras 