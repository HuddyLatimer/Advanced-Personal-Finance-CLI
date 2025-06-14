"""
Advanced database manager with SQLite backend and connection pooling.
"""

import sqlite3
import asyncio
import aiosqlite
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from contextlib import asynccontextmanager
import json
from datetime import datetime

from utils.logger import get_logger
from utils.exceptions import DatabaseError


class DatabaseManager:
    """Advanced database manager with async support and connection pooling."""
    
    def __init__(self, database_path: str):
        self.database_path = Path(database_path)
        self.logger = get_logger(__name__)
        self._connection_pool = []
        self._pool_size = 5
        self._initialized = False
        
        # Ensure database directory exists
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """Initialize database with tables and indexes."""
        if self._initialized:
            return
        
        try:
            async with aiosqlite.connect(self.database_path) as db:
                # Enable WAL mode for better concurrency
                await db.execute("PRAGMA journal_mode=WAL")
                await db.execute("PRAGMA synchronous=NORMAL")
                await db.execute("PRAGMA cache_size=10000")
                await db.execute("PRAGMA temp_store=MEMORY")
                
                # Create tables
                await self._create_tables(db)
                
                # Create indexes
                await self._create_indexes(db)
                
                await db.commit()
            
            self._initialized = True
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Database initialization error: {e}")
            raise DatabaseError(f"Failed to initialize database: {e}")
    
    async def _create_tables(self, db: aiosqlite.Connection):
        """Create all database tables."""
        
        # Transactions table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                transaction_type TEXT NOT NULL CHECK (transaction_type IN ('income', 'expense')),
                date TEXT NOT NULL,
                account TEXT DEFAULT 'default',
                tags TEXT DEFAULT '[]',
                location TEXT,
                receipt_path TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                is_recurring BOOLEAN DEFAULT FALSE,
                recurring_frequency TEXT,
                recurring_end_date TEXT,
                parent_transaction_id TEXT,
                subcategory TEXT,
                merchant TEXT,
                payment_method TEXT,
                is_essential BOOLEAN DEFAULT TRUE,
                confidence_score REAL DEFAULT 1.0,
                FOREIGN KEY (parent_transaction_id) REFERENCES transactions (id)
            )
        """)
        
        # Budgets table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                period TEXT NOT NULL CHECK (period IN ('weekly', 'monthly', 'quarterly', 'yearly')),
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                alert_threshold REAL DEFAULT 80.0,
                alert_enabled BOOLEAN DEFAULT TRUE,
                last_alert_sent TEXT,
                current_spent REAL DEFAULT 0.0,
                last_reset_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                rollover_unused BOOLEAN DEFAULT FALSE,
                auto_adjust BOOLEAN DEFAULT FALSE,
                tags TEXT DEFAULT '[]',
                notes TEXT
            )
        """)
        
        # Goals table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                target_amount REAL NOT NULL,
                current_amount REAL DEFAULT 0.0,
                target_date TEXT NOT NULL,
                category TEXT,
                goal_type TEXT DEFAULT 'savings',
                priority TEXT DEFAULT 'medium',
                milestones TEXT DEFAULT '[]',
                contributions TEXT DEFAULT '[]',
                auto_contribute BOOLEAN DEFAULT FALSE,
                auto_contribute_amount REAL DEFAULT 0.0,
                auto_contribute_frequency TEXT DEFAULT 'monthly',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                tags TEXT DEFAULT '[]',
                notes TEXT,
                linked_account TEXT,
                reminder_frequency INTEGER DEFAULT 7,
                last_reminder_sent TEXT
            )
        """)
        
        # Categories table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
                parent_category TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Accounts table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                type TEXT NOT NULL,
                balance REAL DEFAULT 0.0,
                currency TEXT DEFAULT 'USD',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Recurring transactions table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS recurring_transactions (
                id TEXT PRIMARY KEY,
                template_transaction_id TEXT NOT NULL,
                frequency TEXT NOT NULL,
                next_due_date TEXT NOT NULL,
                end_date TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (template_transaction_id) REFERENCES transactions (id)
            )
        """)
        
        # System settings table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Audit log table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                record_id TEXT NOT NULL,
                action TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
                old_values TEXT,
                new_values TEXT,
                user_id TEXT,
                timestamp TEXT NOT NULL
            )
        """)
    
    async def _create_indexes(self, db: aiosqlite.Connection):
        """Create database indexes for better performance."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions (date)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions (category)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions (transaction_type)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions (account)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions (created_at)",
            "CREATE INDEX IF NOT EXISTS idx_budgets_category ON budgets (category)",
            "CREATE INDEX IF NOT EXISTS idx_budgets_period ON budgets (period)",
            "CREATE INDEX IF NOT EXISTS idx_budgets_active ON budgets (is_active)",
            "CREATE INDEX IF NOT EXISTS idx_goals_target_date ON goals (target_date)",
            "CREATE INDEX IF NOT EXISTS idx_goals_active ON goals (is_active)",
            "CREATE INDEX IF NOT EXISTS idx_categories_type ON categories (type)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_table_record ON audit_log (table_name, record_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log (timestamp)"
        ]
        
        for index_sql in indexes:
            await db.execute(index_sql)
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection from the pool."""
        try:
            conn = await aiosqlite.connect(self.database_path)
            conn.row_factory = aiosqlite.Row
            yield conn
        finally:
            await conn.close()
    
    async def execute_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results."""
        try:
            async with self.get_connection() as db:
                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Query execution error: {e}")
            raise DatabaseError(f"Query failed: {e}")
    
    async def execute_command(self, command: str, params: Tuple = ()) -> int:
        """Execute an INSERT, UPDATE, or DELETE command."""
        try:
            async with self.get_connection() as db:
                cursor = await db.execute(command, params)
                await db.commit()
                return cursor.rowcount
        except Exception as e:
            self.logger.error(f"Command execution error: {e}")
            raise DatabaseError(f"Command failed: {e}")
    
    async def execute_many(self, command: str, params_list: List[Tuple]) -> int:
        """Execute a command with multiple parameter sets."""
        try:
            async with self.get_connection() as db:
                cursor = await db.executemany(command, params_list)
                await db.commit()
                return cursor.rowcount
        except Exception as e:
            self.logger.error(f"Batch execution error: {e}")
            raise DatabaseError(f"Batch command failed: {e}")
    
    async def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema information."""
        query = f"PRAGMA table_info({table_name})"
        return await self.execute_query(query)
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = {}
        
        # Table row counts
        tables = ['transactions', 'budgets', 'goals', 'categories', 'accounts']
        for table in tables:
            result = await self.execute_query(f"SELECT COUNT(*) as count FROM {table}")
            stats[f"{table}_count"] = result[0]['count'] if result else 0
        
        # Database size
        result = await self.execute_query("PRAGMA page_count")
        page_count = result[0]['page_count'] if result else 0
        
        result = await self.execute_query("PRAGMA page_size")
        page_size = result[0]['page_size'] if result else 0
        
        stats['database_size_bytes'] = page_count * page_size
        stats['database_size_mb'] = round((page_count * page_size) / (1024 * 1024), 2)
        
        return stats
    
    async def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database."""
        try:
            backup_path = Path(backup_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with self.get_connection() as source:
                async with aiosqlite.connect(backup_path) as backup:
                    await source.backup(backup)
            
            self.logger.info(f"Database backed up to {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Backup error: {e}")
            return False
    
    async def restore_database(self, backup_path: str) -> bool:
        """Restore database from backup."""
        try:
            backup_path = Path(backup_path)
            if not backup_path.exists():
                raise DatabaseError(f"Backup file not found: {backup_path}")
            
            # Close current connections and replace database
            await self.close()
            
            # Copy backup to current database location
            import shutil
            shutil.copy2(backup_path, self.database_path)
            
            # Reinitialize
            await self.initialize()
            
            self.logger.info(f"Database restored from {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Restore error: {e}")
            return False
    
    async def vacuum_database(self) -> bool:
        """Vacuum the database to reclaim space."""
        try:
            async with self.get_connection() as db:
                await db.execute("VACUUM")
            
            self.logger.info("Database vacuumed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Vacuum error: {e}")
            return False
    
    async def close(self):
        """Close all database connections."""
        # In aiosqlite, connections are closed automatically
        # This method is here for interface compatibility
        self.logger.info("Database connections closed")
