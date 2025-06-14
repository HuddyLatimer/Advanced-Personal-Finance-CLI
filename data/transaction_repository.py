"""
Transaction repository with advanced querying and caching capabilities.
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
from decimal import Decimal

from .database_manager import DatabaseManager
from models.transaction import Transaction
from utils.logger import get_logger
from utils.exceptions import RepositoryError
from utils.cache import CacheManager


class TransactionRepository:
    """Advanced transaction repository with caching and complex queries."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = get_logger(__name__)
        self.cache = CacheManager(max_size=1000, ttl_seconds=300)  # 5 minute cache
    
    async def create(self, transaction: Transaction) -> Transaction:
        """Create a new transaction."""
        try:
            command = """
                INSERT INTO transactions (
                    id, amount, category, description, transaction_type, date, account,
                    tags, location, receipt_path, notes, created_at, updated_at,
                    is_recurring, recurring_frequency, recurring_end_date, parent_transaction_id,
                    subcategory, merchant, payment_method, is_essential, confidence_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                transaction.id,
                float(transaction.amount),
                transaction.category,
                transaction.description,
                transaction.transaction_type,
                transaction.date,
                transaction.account,
                json.dumps(transaction.tags),
                transaction.location,
                transaction.receipt_path,
                transaction.notes,
                transaction.created_at,
                transaction.updated_at,
                transaction.is_recurring,
                transaction.recurring_frequency,
                transaction.recurring_end_date,
                transaction.parent_transaction_id,
                transaction.subcategory,
                transaction.merchant,
                transaction.payment_method,
                transaction.is_essential,
                transaction.confidence_score
            )
            
            await self.db_manager.execute_command(command, params)
            
            # Invalidate cache
            self.cache.clear()
            
            self.logger.info(f"Created transaction: {transaction.id}")
            return transaction
            
        except Exception as e:
            self.logger.error(f"Error creating transaction: {e}")
            raise RepositoryError(f"Failed to create transaction: {e}")
    
    async def get_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """Get transaction by ID."""
        cache_key = f"transaction:{transaction_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        try:
            query = "SELECT * FROM transactions WHERE id = ?"
            results = await self.db_manager.execute_query(query, (transaction_id,))
            
            if not results:
                return None
            
            transaction = self._row_to_transaction(results[0])
            self.cache.set(cache_key, transaction)
            
            return transaction
            
        except Exception as e:
            self.logger.error(f"Error getting transaction by ID: {e}")
            raise RepositoryError(f"Failed to get transaction: {e}")
    
    async def get_all(self, limit: int = None, offset: int = 0) -> List[Transaction]:
        """Get all transactions with optional pagination."""
        try:
            query = "SELECT * FROM transactions ORDER BY date DESC, created_at DESC"
            params = ()
            
            if limit:
                query += " LIMIT ? OFFSET ?"
                params = (limit, offset)
            
            results = await self.db_manager.execute_query(query, params)
            return [self._row_to_transaction(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Error getting all transactions: {e}")
            raise RepositoryError(f"Failed to get transactions: {e}")
    
    async def get_by_filters(self, filters: Dict[str, Any], 
                           limit: int = None, offset: int = 0,
                           sort_by: str = 'date', order: str = 'desc') -> List[Transaction]:
        """Get transactions with complex filtering."""
        try:
            where_clauses = []
            params = []
            
            # Build WHERE clauses
            if filters.get('type'):
                where_clauses.append("transaction_type = ?")
                params.append(filters['type'])
            
            if filters.get('category'):
                where_clauses.append("category = ?")
                params.append(filters['category'])
            
            if filters.get('account'):
                where_clauses.append("account = ?")
                params.append(filters['account'])
            
            if filters.get('start_date'):
                where_clauses.append("date >= ?")
                params.append(filters['start_date'])
            
            if filters.get('end_date'):
                where_clauses.append("date <= ?")
                params.append(filters['end_date'])
            
            if filters.get('min_amount'):
                where_clauses.append("amount >= ?")
                params.append(float(filters['min_amount']))
            
            if filters.get('max_amount'):
                where_clauses.append("amount <= ?")
                params.append(float(filters['max_amount']))
            
            if filters.get('tags'):
                # Search for any of the provided tags
                tag_conditions = []
                for tag in filters['tags']:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f'%"{tag}"%')
                if tag_conditions:
                    where_clauses.append(f"({' OR '.join(tag_conditions)})")
            
            if filters.get('merchant'):
                where_clauses.append("merchant = ?")
                params.append(filters['merchant'])
            
            if filters.get('is_essential') is not None:
                where_clauses.append("is_essential = ?")
                params.append(filters['is_essential'])
            
            # Build query
            query = "SELECT * FROM transactions"
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            # Add sorting
            valid_sort_fields = ['date', 'amount', 'category', 'created_at']
            if sort_by in valid_sort_fields:
                query += f" ORDER BY {sort_by} {order.upper()}"
            else:
                query += " ORDER BY date DESC"
            
            # Add pagination
            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            results = await self.db_manager.execute_query(query, tuple(params))
            return [self._row_to_transaction(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Error getting filtered transactions: {e}")
            raise RepositoryError(f"Failed to get filtered transactions: {e}")
    
    async def search(self, query_text: str, limit: int = 50) -> List[Transaction]:
        """Search transactions by text."""
        try:
            query = """
                SELECT * FROM transactions 
                WHERE description LIKE ? 
                   OR category LIKE ? 
                   OR notes LIKE ?
                   OR merchant LIKE ?
                ORDER BY date DESC
                LIMIT ?
            """
            
            search_term = f"%{query_text}%"
            params = (search_term, search_term, search_term, search_term, limit)
            
            results = await self.db_manager.execute_query(query, params)
            return [self._row_to_transaction(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Error searching transactions: {e}")
            raise RepositoryError(f"Failed to search transactions: {e}")
    
    async def update(self, transaction: Transaction) -> bool:
        """Update an existing transaction."""
        try:
            transaction.updated_at = datetime.now().isoformat()
            
            command = """
                UPDATE transactions SET
                    amount = ?, category = ?, description = ?, transaction_type = ?,
                    date = ?, account = ?, tags = ?, location = ?, receipt_path = ?,
                    notes = ?, updated_at = ?, is_recurring = ?, recurring_frequency = ?,
                    recurring_end_date = ?, subcategory = ?, merchant = ?, payment_method = ?,
                    is_essential = ?, confidence_score = ?
                WHERE id = ?
            """
            
            params = (
                float(transaction.amount),
                transaction.category,
                transaction.description,
                transaction.transaction_type,
                transaction.date,
                transaction.account,
                json.dumps(transaction.tags),
                transaction.location,
                transaction.receipt_path,
                transaction.notes,
                transaction.updated_at,
                transaction.is_recurring,
                transaction.recurring_frequency,
                transaction.recurring_end_date,
                transaction.subcategory,
                transaction.merchant,
                transaction.payment_method,
                transaction.is_essential,
                transaction.confidence_score,
                transaction.id
            )
            
            rows_affected = await self.db_manager.execute_command(command, params)
            
            if rows_affected > 0:
                # Invalidate cache
                self.cache.delete(f"transaction:{transaction.id}")
                self.cache.clear()  # Clear all cache for simplicity
                
                self.logger.info(f"Updated transaction: {transaction.id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error updating transaction: {e}")
            raise RepositoryError(f"Failed to update transaction: {e}")
    
    async def delete(self, transaction_id: str) -> bool:
        """Delete a transaction."""
        try:
            command = "DELETE FROM transactions WHERE id = ?"
            rows_affected = await self.db_manager.execute_command(command, (transaction_id,))
            
            if rows_affected > 0:
                # Invalidate cache
                self.cache.delete(f"transaction:{transaction_id}")
                self.cache.clear()
                
                self.logger.info(f"Deleted transaction: {transaction_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error deleting transaction: {e}")
            raise RepositoryError(f"Failed to delete transaction: {e}")
    
    async def get_categories(self) -> Dict[str, List[str]]:
        """Get all unique categories grouped by type."""
        try:
            query = """
                SELECT DISTINCT category, transaction_type 
                FROM transactions 
                ORDER BY transaction_type, category
            """
            
            results = await self.db_manager.execute_query(query)
            
            categories = {'income': [], 'expense': []}
            for row in results:
                categories[row['transaction_type']].append(row['category'])
            
            return categories
            
        except Exception as e:
            self.logger.error(f"Error getting categories: {e}")
            raise RepositoryError(f"Failed to get categories: {e}")
    
    async def get_summary_stats(self, start_date: str = None, end_date: str = None,
                              account: str = None) -> Dict[str, Any]:
        """Get summary statistics for transactions."""
        try:
            where_clauses = []
            params = []
            
            if start_date:
                where_clauses.append("date >= ?")
                params.append(start_date)
            
            if end_date:
                where_clauses.append("date <= ?")
                params.append(end_date)
            
            if account:
                where_clauses.append("account = ?")
                params.append(account)
            
            where_clause = ""
            if where_clauses:
                where_clause = "WHERE " + " AND ".join(where_clauses)
            
            # Get basic stats
            query = f"""
                SELECT 
                    transaction_type,
                    COUNT(*) as count,
                    SUM(amount) as total,
                    AVG(amount) as average,
                    MIN(amount) as minimum,
                    MAX(amount) as maximum
                FROM transactions 
                {where_clause}
                GROUP BY transaction_type
            """
            
            results = await self.db_manager.execute_query(query, tuple(params))
            
            stats = {
                'total_income': 0.0,
                'total_expenses': 0.0,
                'income_count': 0,
                'expense_count': 0,
                'average_income': 0.0,
                'average_expense': 0.0,
                'max_income': 0.0,
                'max_expense': 0.0
            }
            
            for row in results:
                if row['transaction_type'] == 'income':
                    stats['total_income'] = row['total'] or 0.0
                    stats['income_count'] = row['count'] or 0
                    stats['average_income'] = row['average'] or 0.0
                    stats['max_income'] = row['maximum'] or 0.0
                else:
                    stats['total_expenses'] = row['total'] or 0.0
                    stats['expense_count'] = row['count'] or 0
                    stats['average_expense'] = row['average'] or 0.0
                    stats['max_expense'] = row['maximum'] or 0.0
            
            stats['net_balance'] = stats['total_income'] - stats['total_expenses']
            stats['total_count'] = stats['income_count'] + stats['expense_count']
            
            if stats['total_income'] > 0:
                stats['savings_rate'] = (stats['net_balance'] / stats['total_income']) * 100
            else:
                stats['savings_rate'] = 0.0
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting summary stats: {e}")
            raise RepositoryError(f"Failed to get summary stats: {e}")
    
    async def get_category_breakdown(self, transaction_type: str = None,
                                   start_date: str = None, end_date: str = None) -> Dict[str, float]:
        """Get spending/income breakdown by category."""
        try:
            where_clauses = []
            params = []
            
            if transaction_type:
                where_clauses.append("transaction_type = ?")
                params.append(transaction_type)
            
            if start_date:
                where_clauses.append("date >= ?")
                params.append(start_date)
            
            if end_date:
                where_clauses.append("date <= ?")
                params.append(end_date)
            
            where_clause = ""
            if where_clauses:
                where_clause = "WHERE " + " AND ".join(where_clauses)
            
            query = f"""
                SELECT category, SUM(amount) as total
                FROM transactions 
                {where_clause}
                GROUP BY category
                ORDER BY total DESC
            """
            
            results = await self.db_manager.execute_query(query, tuple(params))
            
            return {row['category']: row['total'] for row in results}
            
        except Exception as e:
            self.logger.error(f"Error getting category breakdown: {e}")
            raise RepositoryError(f"Failed to get category breakdown: {e}")
    
    async def get_monthly_trends(self, months: int = 12) -> List[Dict[str, Any]]:
        """Get monthly spending/income trends."""
        try:
            # Calculate start date
            start_date = (datetime.now() - timedelta(days=months * 30)).strftime('%Y-%m-%d')
            
            query = """
                SELECT 
                    strftime('%Y-%m', date) as month,
                    transaction_type,
                    SUM(amount) as total,
                    COUNT(*) as count
                FROM transactions 
                WHERE date >= ?
                GROUP BY strftime('%Y-%m', date), transaction_type
                ORDER BY month DESC
            """
            
            results = await self.db_manager.execute_query(query, (start_date,))
            
            # Organize by month
            trends = {}
            for row in results:
                month = row['month']
                if month not in trends:
                    trends[month] = {'income': 0.0, 'expenses': 0.0, 'income_count': 0, 'expense_count': 0}
                
                if row['transaction_type'] == 'income':
                    trends[month]['income'] = row['total']
                    trends[month]['income_count'] = row['count']
                else:
                    trends[month]['expenses'] = row['total']
                    trends[month]['expense_count'] = row['count']
            
            # Convert to list and add net balance
            trend_list = []
            for month, data in sorted(trends.items(), reverse=True):
                data['month'] = month
                data['net_balance'] = data['income'] - data['expenses']
                trend_list.append(data)
            
            return trend_list
            
        except Exception as e:
            self.logger.error(f"Error getting monthly trends: {e}")
            raise RepositoryError(f"Failed to get monthly trends: {e}")
    
    def _row_to_transaction(self, row: Dict[str, Any]) -> Transaction:
        """Convert database row to Transaction object."""
        # Parse JSON fields
        tags = json.loads(row.get('tags', '[]'))
        
        return Transaction(
            id=row['id'],
            amount=Decimal(str(row['amount'])),
            category=row['category'],
            description=row['description'],
            transaction_type=row['transaction_type'],
            date=row['date'],
            account=row.get('account', 'default'),
            tags=tags,
            location=row.get('location'),
            receipt_path=row.get('receipt_path'),
            notes=row.get('notes'),
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            is_recurring=bool(row.get('is_recurring', False)),
            recurring_frequency=row.get('recurring_frequency'),
            recurring_end_date=row.get('recurring_end_date'),
            parent_transaction_id=row.get('parent_transaction_id'),
            subcategory=row.get('subcategory'),
            merchant=row.get('merchant'),
            payment_method=row.get('payment_method'),
            is_essential=bool(row.get('is_essential', True)),
            confidence_score=float(row.get('confidence_score', 1.0))
        )
