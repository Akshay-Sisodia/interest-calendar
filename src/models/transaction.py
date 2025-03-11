from datetime import datetime
import uuid

class Transaction:
    """
    Class representing a financial transaction.
    Handles operations related to transaction data.
    """
    
    def __init__(self, transaction_id=None, client_id=None, date=None, amount=None, 
                 rate=None, days=None, interest=None, calendar_type=None, 
                 shadow_value=None, calendar_name=None, notes=None):
        """
        Initialize a Transaction object.
        
        Args:
            transaction_id: Unique identifier for the transaction
            client_id: ID of the client associated with the transaction
            date: Date of the transaction
            amount: Transaction amount
            rate: Interest rate
            days: Number of days for interest calculation
            interest: Calculated interest
            calendar_type: Type of calendar used ('Diwali' or 'Financial')
            shadow_value: Shadow value from the calendar
            calendar_name: Name of the specific calendar used
            notes: Additional notes
        """
        self.transaction_id = transaction_id or str(uuid.uuid4())
        self.client_id = client_id
        self.date = date
        self.amount = amount
        self.rate = rate
        self.days = days
        self.interest = interest
        self.calendar_type = calendar_type
        self.shadow_value = shadow_value
        self.calendar_name = calendar_name
        self.notes = notes
    
    @classmethod
    def from_dict(cls, data):
        """
        Create a Transaction object from a dictionary.
        
        Args:
            data: Dictionary containing transaction data
            
        Returns:
            Transaction: A new Transaction object
        """
        return cls(
            transaction_id=data.get('transaction_id'),
            client_id=data.get('client_id'),
            date=data.get('date'),
            amount=data.get('amount'),
            rate=data.get('rate'),
            days=data.get('days'),
            interest=data.get('interest'),
            calendar_type=data.get('calendar_type'),
            shadow_value=data.get('shadow_value'),
            calendar_name=data.get('calendar_name'),
            notes=data.get('notes')
        )
    
    def to_dict(self):
        """
        Convert the Transaction object to a dictionary.
        
        Returns:
            dict: Dictionary representation of the transaction
        """
        return {
            'transaction_id': self.transaction_id,
            'client_id': self.client_id,
            'date': self.date,
            'amount': self.amount,
            'rate': self.rate,
            'days': self.days,
            'interest': self.interest,
            'calendar_type': self.calendar_type,
            'shadow_value': self.shadow_value,
            'calendar_name': self.calendar_name,
            'notes': self.notes
        }
    
    def calculate_interest(self, shadow_value=None):
        """
        Calculate interest for the transaction.
        
        Args:
            shadow_value: Optional shadow value to use for calculation
            
        Returns:
            float: Calculated interest
        """
        if shadow_value is None:
            shadow_value = self.shadow_value
        
        if not all([self.amount, self.rate, self.days, shadow_value]):
            return None
        
        # Formula: (amount * rate * days) / shadow_value
        interest = (float(self.amount) * float(self.rate) * float(self.days)) / float(shadow_value)
        self.interest = round(interest, 2)
        return self.interest
    
    def update_from_dict(self, data):
        """
        Update the Transaction object from a dictionary.
        
        Args:
            data: Dictionary containing updated transaction data
            
        Returns:
            Transaction: The updated Transaction object
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        return self
    
    @staticmethod
    def get_transactions_for_client(transactions, client_id):
        """
        Get all transactions for a specific client.
        
        Args:
            transactions: List of Transaction objects
            client_id: ID of the client
            
        Returns:
            list: List of Transaction objects for the client
        """
        return [t for t in transactions if t.client_id == client_id]
