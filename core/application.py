"""
Main application controller that orchestrates all components.
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from .config import Config
from .cli_interface import CLIInterface
from .command_processor import CommandProcessor
from data.database_manager import DatabaseManager
from data.transaction_repository import TransactionRepository
from data.budget_repository import BudgetRepository
from data.goal_repository import GoalRepository
from services.transaction_service import TransactionService
from services.budget_service import BudgetService
from services.analytics_service import AnalyticsService
from services.goal_service import GoalService
from services.notification_service import NotificationService
from services.backup_service import BackupService
from services.import_export_service import ImportExportService
from utils.logger import get_logger
from utils.performance import PerformanceMonitor


class FinanceApplication:
    """Main application class that coordinates all components."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        self.performance_monitor = PerformanceMonitor()
        
        # Initialize core components
        self._initialize_components()
        
        # Setup CLI interface
        self.cli = CLIInterface(self.command_processor, config)
        
        self.logger.info("Finance application initialized successfully")
    
    def _initialize_components(self):
        """Initialize all application components."""
        # Database and repositories
        self.db_manager = DatabaseManager(self.config.database_path)
        self.transaction_repo = TransactionRepository(self.db_manager)
        self.budget_repo = BudgetRepository(self.db_manager)
        self.goal_repo = GoalRepository(self.db_manager)
        
        # Services
        self.transaction_service = TransactionService(self.transaction_repo)
        self.budget_service = BudgetService(self.budget_repo, self.transaction_repo)
        self.analytics_service = AnalyticsService(self.transaction_repo)
        self.goal_service = GoalService(self.goal_repo, self.transaction_repo)
        self.notification_service = NotificationService(self.config)
        self.backup_service = BackupService(self.config)
        self.import_export_service = ImportExportService(
            self.transaction_repo, self.budget_repo, self.goal_repo
        )
        
        # Command processor
        self.command_processor = CommandProcessor(
            transaction_service=self.transaction_service,
            budget_service=self.budget_service,
            analytics_service=self.analytics_service,
            goal_service=self.goal_service,
            notification_service=self.notification_service,
            backup_service=self.backup_service,
            import_export_service=self.import_export_service
        )
    
    async def run(self):
        """Run the main application loop."""
        try:
            # Perform startup tasks
            await self._startup_tasks()
            
            # Run CLI interface
            await self.cli.run()
            
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            raise
        finally:
            await self._shutdown_tasks()
    
    async def _startup_tasks(self):
        """Perform startup tasks."""
        self.logger.info("Performing startup tasks...")
        
        # Initialize database
        await self.db_manager.initialize()
        
        # Check for pending notifications
        await self.notification_service.check_pending_notifications()
        
        # Auto-backup if enabled
        if self.config.auto_backup_enabled:
            await self.backup_service.create_backup()
        
        # Performance monitoring
        self.performance_monitor.start_monitoring()
        
        self.logger.info("Startup tasks completed")
    
    async def _shutdown_tasks(self):
        """Perform cleanup tasks."""
        self.logger.info("Performing shutdown tasks...")
        
        # Stop performance monitoring
        self.performance_monitor.stop_monitoring()
        
        # Close database connections
        await self.db_manager.close()
        
        self.logger.info("Shutdown tasks completed")
