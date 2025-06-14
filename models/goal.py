"""
Financial goal model with progress tracking and milestone features.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
import uuid


@dataclass
class Goal:
    """Advanced financial goal model with comprehensive tracking."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    target_amount: Decimal = field(default=Decimal('0.00'))
    current_amount: Decimal = field(default=Decimal('0.00'))
    target_date: str = ""
    category: Optional[str] = None
    
    # Goal type and priority
    goal_type: str = "savings"  # 'savings', 'debt_payoff', 'investment', 'purchase'
    priority: str = "medium"  # 'low', 'medium', 'high', 'critical'
    
    # Progress tracking
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    contributions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Automation settings
    auto_contribute: bool = False
    auto_contribute_amount: Decimal = field(default=Decimal('0.00'))
    auto_contribute_frequency: str = "monthly"  # 'weekly', 'monthly', 'quarterly'
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    is_active: bool = True
    
    # Additional features
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    linked_account: Optional[str] = None
    reminder_frequency: int = 7  # Days between reminders
    last_reminder_sent: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        if isinstance(self.target_amount, (int, float)):
            self.target_amount = Decimal(str(self.target_amount))
        
        if isinstance(self.current_amount, (int, float)):
            self.current_amount = Decimal(str(self.current_amount))
        
        if isinstance(self.auto_contribute_amount, (int, float)):
            self.auto_contribute_amount = Decimal(str(self.auto_contribute_amount))
        
        # Create default milestones if none exist
        if not self.milestones and self.target_amount > 0:
            self._create_default_milestones()
    
    def _create_default_milestones(self):
        """Create default milestones at 25%, 50%, 75%, and 100%."""
        percentages = [25, 50, 75, 100]
        for pct in percentages:
            milestone_amount = (self.target_amount * pct) / 100
            self.milestones.append({
                'id': str(uuid.uuid4()),
                'name': f"{pct}% Complete",
                'amount': float(milestone_amount),
                'percentage': pct,
                'achieved': False,
                'achieved_date': None,
                'description': f"Reach {pct}% of your goal (${milestone_amount:,.2f})"
            })
    
    @property
    def remaining_amount(self) -> Decimal:
        """Calculate remaining amount to reach goal."""
        return max(Decimal('0.00'), self.target_amount - self.current_amount)
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.target_amount == 0:
            return 0.0
        return min(100.0, float((self.current_amount / self.target_amount) * 100))
    
    @property
    def is_completed(self) -> bool:
        """Check if goal is completed."""
        return self.current_amount >= self.target_amount
    
    @property
    def days_remaining(self) -> int:
        """Calculate days remaining to target date."""
        if not self.target_date:
            return 0
        
        target = datetime.strptime(self.target_date, '%Y-%m-%d')
        today = datetime.now()
        return max(0, (target - today).days)
    
    @property
    def daily_savings_needed(self) -> Decimal:
        """Calculate daily savings needed to reach goal."""
        days_left = self.days_remaining
        if days_left == 0:
            return Decimal('0.00')
        return self.remaining_amount / days_left
    
    @property
    def is_on_track(self) -> bool:
        """Check if goal is on track based on time elapsed."""
        if not self.target_date:
            return True
        
        start_date = datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
        target_date = datetime.strptime(self.target_date, '%Y-%m-%d')
        today = datetime.now()
        
        total_days = (target_date - start_date).days
        elapsed_days = (today - start_date).days
        
        if total_days <= 0:
            return True
        
        expected_progress = (elapsed_days / total_days) * 100
        return self.progress_percentage >= expected_progress * 0.9  # 10% tolerance
    
    def add_contribution(self, amount: Decimal, description: str = "", date: str = None) -> None:
        """Add a contribution to the goal."""
        if isinstance(amount, (int, float)):
            amount = Decimal(str(amount))
        
        contribution = {
            'id': str(uuid.uuid4()),
            'amount': float(amount),
            'description': description or f"Contribution of ${amount}",
            'date': date or datetime.now().strftime('%Y-%m-%d'),
            'timestamp': datetime.now().isoformat()
        }
        
        self.contributions.append(contribution)
        self.current_amount += amount
        self.updated_at = datetime.now().isoformat()
        
        # Check for milestone achievements
        self._check_milestones()
        
        # Check if goal is completed
        if self.is_completed and not self.completed_at:
            self.completed_at = datetime.now().isoformat()
    
    def _check_milestones(self):
        """Check and update milestone achievements."""
        for milestone in self.milestones:
            if not milestone['achieved'] and self.current_amount >= Decimal(str(milestone['amount'])):
                milestone['achieved'] = True
                milestone['achieved_date'] = datetime.now().strftime('%Y-%m-%d')
    
    def get_next_milestone(self) -> Optional[Dict[str, Any]]:
        """Get the next unachieved milestone."""
        unachieved = [m for m in self.milestones if not m['achieved']]
        if unachieved:
            return min(unachieved, key=lambda x: x['percentage'])
        return None
    
    def get_achieved_milestones(self) -> List[Dict[str, Any]]:
        """Get all achieved milestones."""
        return [m for m in self.milestones if m['achieved']]
    
    def calculate_projected_completion(self) -> Optional[str]:
        """Calculate projected completion date based on current progress."""
        if len(self.contributions) < 2:
            return None
        
        # Calculate average contribution per day
        recent_contributions = self.contributions[-10:]  # Last 10 contributions
        if not recent_contributions:
            return None
        
        total_amount = sum(Decimal(str(c['amount'])) for c in recent_contributions)
        
        # Calculate time span of recent contributions
        dates = [datetime.fromisoformat(c['timestamp']) for c in recent_contributions]
        time_span = (max(dates) - min(dates)).days
        
        if time_span == 0:
            time_span = 1
        
        daily_rate = total_amount / time_span
        
        if daily_rate <= 0:
            return None
        
        days_needed = float(self.remaining_amount / daily_rate)
        projected_date = datetime.now() + timedelta(days=days_needed)
        
        return projected_date.strftime('%Y-%m-%d')
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive goal status."""
        next_milestone = self.get_next_milestone()
        projected_completion = self.calculate_projected_completion()
        
        return {
            'name': self.name,
            'target_amount': float(self.target_amount),
            'current_amount': float(self.current_amount),
            'remaining_amount': float(self.remaining_amount),
            'progress_percentage': self.progress_percentage,
            'is_completed': self.is_completed,
            'is_on_track': self.is_on_track,
            'days_remaining': self.days_remaining,
            'daily_savings_needed': float(self.daily_savings_needed),
            'next_milestone': next_milestone,
            'achieved_milestones_count': len(self.get_achieved_milestones()),
            'total_milestones': len(self.milestones),
            'projected_completion': projected_completion,
            'status': self._get_status_text()
        }
    
    def _get_status_text(self) -> str:
        """Get status text description."""
        if self.is_completed:
            return "COMPLETED"
        elif not self.is_on_track:
            return "BEHIND SCHEDULE"
        elif self.progress_percentage > 75:
            return "ALMOST THERE"
        elif self.progress_percentage > 50:
            return "GOOD PROGRESS"
        elif self.progress_percentage > 25:
            return "GETTING STARTED"
        else:
            return "JUST STARTED"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert goal to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'target_amount': float(self.target_amount),
            'current_amount': float(self.current_amount),
            'target_date': self.target_date,
            'category': self.category,
            'goal_type': self.goal_type,
            'priority': self.priority,
            'milestones': self.milestones,
            'contributions': self.contributions,
            'auto_contribute': self.auto_contribute,
            'auto_contribute_amount': float(self.auto_contribute_amount),
            'auto_contribute_frequency': self.auto_contribute_frequency,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'completed_at': self.completed_at,
            'is_active': self.is_active,
            'tags': self.tags,
            'notes': self.notes,
            'linked_account': self.linked_account,
            'reminder_frequency': self.reminder_frequency,
            'last_reminder_sent': self.last_reminder_sent
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Goal':
        """Create goal from dictionary."""
        # Convert amounts to Decimal
        for field in ['target_amount', 'current_amount', 'auto_contribute_amount']:
            if field in data:
                data[field] = Decimal(str(data[field]))
        
        # Handle missing fields with defaults
        defaults = {
            'milestones': [],
            'contributions': [],
            'tags': [],
            'goal_type': 'savings',
            'priority': 'medium',
            'auto_contribute': False,
            'is_active': True,
            'reminder_frequency': 7
        }
        
        for key, default_value in defaults.items():
            if key not in data:
                data[key] = default_value
        
        return cls(**data)
    
    def __str__(self) -> str:
        """String representation of the goal."""
        return f"{self.name}: ${self.current_amount:,.2f}/${self.target_amount:,.2f} ({self.progress_percentage:.1f}%)"
