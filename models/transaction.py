"""
Transaction model with advanced features.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import uuid


@dataclass
class Transaction:
    """Advanced transaction model with comprehensive features."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    amount: Decimal = field(default=Decimal('0.00'))
    category: str = ""
    description: str = ""
    transaction_type: str = ""  # 'income' or 'expense'
    date: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d'))
    account: str = "default"
    tags: List[str] = field(default_factory=list)
    location: Optional[str] = None
    receipt_path: Optional[str] = None
    notes: Optional[str] = None
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Recurring transaction info
    is_recurring: bool = False
    recurring_frequency: Optional[str] = None  # 'daily', 'weekly', 'monthly', 'yearly'
    recurring_end_date: Optional[str] = None
    parent_transaction_id: Optional[str] = None
    
    # Classification
    subcategory: Optional[str] = None
    merchant: Optional[str] = None
    payment_method: Optional[str] = None
    
    # Analysis fields
    is_essential: bool = True
    confidence_score: float = 1.0  # For auto-categorization
    
    def __post_init__(self):
        """Post-initialization processing."""
        if isinstance(self.amount, (int, float)):
            self.amount = Decimal(str(self.amount))
        
        # Ensure amount is positive
        if self.amount < 0:
            self.amount = abs(self.amount)
        
        # Normalize category
        self.category = self.category.title()
        
        # Update timestamp
        self.updated_at = datetime.now().isoformat()
    
    @property
    def type(self) -> str:
        """Alias for transaction_type for backward compatibility."""
        return self.transaction_type
    
    @type.setter
    def type(self, value: str):
        """Setter for type property."""
        self.transaction_type = value
    
    @property
    def signed_amount(self) -> Decimal:
        """Get amount with appropriate sign based on transaction type."""
        return self.amount if self.transaction_type == 'income' else -self.amount
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary."""
        return {
            'id': self.id,
            'amount': float(self.amount),
            'category': self.category,
            'description': self.description,
            'transaction_type': self.transaction_type,
            'date': self.date,
            'account': self.account,
            'tags': self.tags,
            'location': self.location,
            'receipt_path': self.receipt_path,
            'notes': self.notes,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'is_recurring': self.is_recurring,
            'recurring_frequency': self.recurring_frequency,
            'recurring_end_date': self.recurring_end_date,
            'parent_transaction_id': self.parent_transaction_id,
            'subcategory': self.subcategory,
            'merchant': self.merchant,
            'payment_method': self.payment_method,
            'is_essential': self.is_essential,
            'confidence_score': self.confidence_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        """Create transaction from dictionary."""
        # Handle legacy data format
        if 'type' in data and 'transaction_type' not in data:
            data['transaction_type'] = data.pop('type')
        
        # Convert amount to Decimal
        if 'amount' in data:
            data['amount'] = Decimal(str(data['amount']))
        
        # Handle missing fields with defaults
        defaults = {
            'tags': [],
            'account': 'default',
            'is_recurring': False,
            'is_essential': True,
            'confidence_score': 1.0
        }
        
        for key, default_value in defaults.items():
            if key not in data:
                data[key] = default_value
        
        return cls(**data)
    
    def update(self, **kwargs):
        """Update transaction fields."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                if key == 'amount' and not isinstance(value, Decimal):
                    value = Decimal(str(value))
                setattr(self, key, value)
        
        self.updated_at = datetime.now().isoformat()
    
    def add_tag(self, tag: str):
        """Add a tag to the transaction."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now().isoformat()
    
    def remove_tag(self, tag: str):
        """Remove a tag from the transaction."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now().isoformat()
    
    def __str__(self) -> str:
        """String representation of the transaction."""
        sign = '+' if self.transaction_type == 'income' else '-'
        tags_str = f" [{', '.join(self.tags)}]" if self.tags else ""
        return f"{self.date} | {sign}${self.amount} | {self.category} | {self.description}{tags_str}"
    
    def __repr__(self) -> str:
        """Detailed representation of the transaction."""
        return f"Transaction(id='{self.id}', amount={self.amount}, type='{self.transaction_type}', category='{self.category}')"
