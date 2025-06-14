"""
Budget model with advanced tracking and alerting features.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
import uuid


@dataclass
class Budget:
    """Advanced budget model with comprehensive tracking."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    category: str = ""
    amount: Decimal = field(default=Decimal('0.00'))
    period: str = "monthly"  # 'weekly', 'monthly', 'quarterly', 'yearly'
    start_date: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d'))
    end_date: Optional[str] = None
    
    # Alert settings
    alert_threshold: float = 80.0  # Percentage
    alert_enabled: bool = True
    last_alert_sent: Optional[str] = None
    
    # Tracking
    current_spent: Decimal = field(default=Decimal('0.00'))
    last_reset_date: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d'))
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    is_active: bool = True
    
    # Advanced features
    rollover_unused: bool = False
    auto_adjust: bool = False
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        if isinstance(self.amount, (int, float)):
            self.amount = Decimal(str(self.amount))
        
        if isinstance(self.current_spent, (int, float)):
            self.current_spent = Decimal(str(self.current_spent))
        
        # Calculate end date if not provided
        if not self.end_date:
            self.end_date = self._calculate_end_date()
        
        # Normalize category
        self.category = self.category.title()
    
    def _calculate_end_date(self) -> str:
        """Calculate end date based on period."""
        start = datetime.strptime(self.start_date, '%Y-%m-%d')
        
        if self.period == 'weekly':
            end = start + timedelta(days=7)
        elif self.period == 'monthly':
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1)
            else:
                end = start.replace(month=start.month + 1)
        elif self.period == 'quarterly':
            end = start + timedelta(days=90)
        elif self.period == 'yearly':
            end = start.replace(year=start.year + 1)
        else:
            end = start + timedelta(days=30)  # Default to monthly
        
        return end.strftime('%Y-%m-%d')
    
    @property
    def remaining_amount(self) -> Decimal:
        """Calculate remaining budget amount."""
        return self.amount - self.current_spent
    
    @property
    def spent_percentage(self) -> float:
        """Calculate percentage of budget spent."""
        if self.amount == 0:
            return 0.0
        return float((self.current_spent / self.amount) * 100)
    
    @property
    def is_over_budget(self) -> bool:
        """Check if budget is exceeded."""
        return self.current_spent > self.amount
    
    @property
    def is_alert_threshold_reached(self) -> bool:
        """Check if alert threshold is reached."""
        return self.spent_percentage >= self.alert_threshold
    
    @property
    def days_remaining(self) -> int:
        """Calculate days remaining in budget period."""
        end = datetime.strptime(self.end_date, '%Y-%m-%d')
        today = datetime.now()
        return max(0, (end - today).days)
    
    @property
    def daily_budget_remaining(self) -> Decimal:
        """Calculate daily budget remaining."""
        days_left = self.days_remaining
        if days_left == 0:
            return Decimal('0.00')
        return self.remaining_amount / days_left
    
    def add_expense(self, amount: Decimal) -> None:
        """Add an expense to the budget tracking."""
        if isinstance(amount, (int, float)):
            amount = Decimal(str(amount))
        
        self.current_spent += amount
        self.updated_at = datetime.now().isoformat()
    
    def reset_period(self) -> None:
        """Reset budget for new period."""
        if self.rollover_unused and self.remaining_amount > 0:
            # Rollover unused amount to next period
            self.amount += self.remaining_amount
        
        self.current_spent = Decimal('0.00')
        self.last_reset_date = datetime.now().strftime('%Y-%m-%d')
        self.start_date = self.last_reset_date
        self.end_date = self._calculate_end_date()
        self.last_alert_sent = None
        self.updated_at = datetime.now().isoformat()
    
    def should_reset(self) -> bool:
        """Check if budget period should be reset."""
        end_date = datetime.strptime(self.end_date, '%Y-%m-%d')
        return datetime.now() > end_date
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive budget status."""
        return {
            'name': self.name,
            'category': self.category,
            'amount': float(self.amount),
            'spent': float(self.current_spent),
            'remaining': float(self.remaining_amount),
            'percentage_spent': self.spent_percentage,
            'is_over_budget': self.is_over_budget,
            'days_remaining': self.days_remaining,
            'daily_budget_remaining': float(self.daily_budget_remaining),
            'alert_threshold_reached': self.is_alert_threshold_reached,
            'status': self._get_status_text()
        }
    
    def _get_status_text(self) -> str:
        """Get status text description."""
        if self.is_over_budget:
            return "OVER BUDGET"
        elif self.is_alert_threshold_reached:
            return "WARNING"
        elif self.spent_percentage > 50:
            return "ON TRACK"
        else:
            return "GOOD"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert budget to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'amount': float(self.amount),
            'period': self.period,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'alert_threshold': self.alert_threshold,
            'alert_enabled': self.alert_enabled,
            'last_alert_sent': self.last_alert_sent,
            'current_spent': float(self.current_spent),
            'last_reset_date': self.last_reset_date,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'is_active': self.is_active,
            'rollover_unused': self.rollover_unused,
            'auto_adjust': self.auto_adjust,
            'tags': self.tags,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Budget':
        """Create budget from dictionary."""
        # Convert amounts to Decimal
        if 'amount' in data:
            data['amount'] = Decimal(str(data['amount']))
        if 'current_spent' in data:
            data['current_spent'] = Decimal(str(data['current_spent']))
        
        # Handle missing fields with defaults
        defaults = {
            'tags': [],
            'alert_enabled': True,
            'is_active': True,
            'rollover_unused': False,
            'auto_adjust': False,
            'alert_threshold': 80.0
        }
        
        for key, default_value in defaults.items():
            if key not in data:
                data[key] = default_value
        
        return cls(**data)
    
    def __str__(self) -> str:
        """String representation of the budget."""
        return f"{self.name} ({self.category}): ${self.current_spent}/{self.amount} ({self.spent_percentage:.1f}%)"
