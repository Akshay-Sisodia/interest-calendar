import uuid

class Client:
    """
    Class representing a client.
    Handles operations related to client data.
    """
    
    def __init__(self, client_id=None, name=None, contact=None, address=None, notes=None):
        """
        Initialize a Client object.
        
        Args:
            client_id: Unique identifier for the client
            name: Client's name
            contact: Client's contact information
            address: Client's address
            notes: Additional notes
        """
        self.client_id = client_id or str(uuid.uuid4())
        self.name = name
        self.contact = contact
        self.address = address
        self.notes = notes
    
    @classmethod
    def from_dict(cls, data):
        """
        Create a Client object from a dictionary.
        
        Args:
            data: Dictionary containing client data
            
        Returns:
            Client: A new Client object
        """
        return cls(
            client_id=data.get('client_id'),
            name=data.get('name'),
            contact=data.get('contact'),
            address=data.get('address'),
            notes=data.get('notes')
        )
    
    def to_dict(self):
        """
        Convert the Client object to a dictionary.
        
        Returns:
            dict: Dictionary representation of the client
        """
        return {
            'client_id': self.client_id,
            'name': self.name,
            'contact': self.contact,
            'address': self.address,
            'notes': self.notes
        }
    
    def update_from_dict(self, data):
        """
        Update the Client object from a dictionary.
        
        Args:
            data: Dictionary containing updated client data
            
        Returns:
            Client: The updated Client object
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        return self
    
    @staticmethod
    def find_by_id(clients, client_id):
        """
        Find a client by ID.
        
        Args:
            clients: List of Client objects
            client_id: ID of the client to find
            
        Returns:
            Client: The found Client object, or None if not found
        """
        for client in clients:
            if client.client_id == client_id:
                return client
        return None
    
    @staticmethod
    def find_by_name(clients, name):
        """
        Find clients by name (partial match).
        
        Args:
            clients: List of Client objects
            name: Name to search for
            
        Returns:
            list: List of matching Client objects
        """
        if not name:
            return []
        
        name_lower = name.lower()
        return [c for c in clients if c.name and name_lower in c.name.lower()]
