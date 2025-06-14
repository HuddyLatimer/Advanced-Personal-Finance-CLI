"""
Advanced command processor with comprehensive command handling.
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import argparse
import shlex

from services.transaction_service import TransactionService
from services.budget_service import BudgetService
from services.analytics_service import AnalyticsService
from services.goal_service import GoalService
from services.notification_service import NotificationService
from services.backup_service import BackupService
from services.import_export_service import ImportExportService
from utils.logger import get_logger
from utils.exceptions import CommandError, ValidationError


class CommandProcessor:
    """Advanced command processor with comprehensive command handling."""
    
    def __init__(self, **services):
        self.transaction_service = services['transaction_service']
        self.budget_service = services['budget_service']
        self.analytics_service = services['analytics_service']
        self.goal_service = services['goal_service']
        self.notification_service = services['notification_service']
        self.backup_service = services['backup_service']
        self.import_export_service = services['import_export_service']
        
        self.logger = get_logger(__name__)
        
        # Command registry
        self.commands = {
            'add': self._handle_add_command,
            'list': self._handle_list_command,
            'edit': self._handle_edit_command,
            'delete': self._handle_delete_command,
            'search': self._handle_search_command,
            'summary': self._handle_summary_command,
            'report': self._handle_report_command,
            'analytics': self._handle_analytics_command,
            'trends': self._handle_trends_command,
            'forecast': self._handle_forecast_command,
            'budget': self._handle_budget_command,
            'goal': self._handle_goal_command,
            'export': self._handle_export_command,
            'import': self._handle_import_command,
            'backup': self._handle_backup_command,
            'restore': self._handle_restore_command,
            'categories': self._handle_categories_command,
            'stats': self._handle_stats_command
        }
        
        # Command help registry
        self.command_help = {
            'add': self._get_add_help,
            'list': self._get_list_help,
            'budget': self._get_budget_help,
            'goal': self._get_goal_help,
            'analytics': self._get_analytics_help
        }
    
    async def process_command(self, command: str, args: List[str]) -> Optional[Dict[str, Any]]:
        """Process a command and return the result."""
        try:
            if command not in self.commands:
                raise CommandError(f"Unknown command: {command}")
            
            handler = self.commands[command]
            result = await handler(args)
            
            self.logger.info(f"Command '{command}' executed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Command processing error: {e}")
            return {
                'type': 'message',
                'level': 'error',
                'content': str(e)
            }
    
    async def get_command_help(self, command: str) -> Optional[str]:
        """Get help for a specific command."""
        if command in self.command_help:
            return self.command_help[command]()
        return None
    
    # Transaction Commands
    async def _handle_add_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle add transaction command."""
        parser = argparse.ArgumentParser(description='Add a new transaction')
        parser.add_argument('--type', choices=['income', 'expense'], required=True)
        parser.add_argument('--amount', type=float, required=True)
        parser.add_argument('--category', required=True)
        parser.add_argument('--description', required=True)
        parser.add_argument('--date', help='Date in YYYY-MM-DD format')
        parser.add_argument('--tags', nargs='*', help='Transaction tags')
        parser.add_argument('--recurring', choices=['daily', 'weekly', 'monthly', 'yearly'])
        parser.add_argument('--account', help='Account name')
        
        try:
            parsed_args = parser.parse_args(args)
            
            transaction_data = {
                'type': parsed_args.type,
                'amount': parsed_args.amount,
                'category': parsed_args.category,
                'description': parsed_args.description,
                'date': parsed_args.date or datetime.now().strftime('%Y-%m-%d'),
                'tags': parsed_args.tags or [],
                'account': parsed_args.account or 'default'
            }
            
            transaction = await self.transaction_service.create_transaction(transaction_data)
            
            # Handle recurring transactions
            if parsed_args.recurring:
                await self.transaction_service.create_recurring_transaction(
                    transaction, parsed_args.recurring
                )
            
            return {
                'type': 'message',
                'level': 'success',
                'content': f"✅ Added {parsed_args.type}: ${parsed_args.amount:,.2f} in {parsed_args.category}"
            }
            
        except Exception as e:
            raise CommandError(f"Error adding transaction: {e}")
    
    async def _handle_list_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle list transactions command."""
        parser = argparse.ArgumentParser(description='List transactions')
        parser.add_argument('--type', choices=['income', 'expense'])
        parser.add_argument('--category')
        parser.add_argument('--start-date')
        parser.add_argument('--end-date')
        parser.add_argument('--limit', type=int, default=50)
        parser.add_argument('--sort', choices=['date', 'amount', 'category'], default='date')
        parser.add_argument('--order', choices=['asc', 'desc'], default='desc')
        parser.add_argument('--account')
        parser.add_argument('--tags', nargs='*')
        
        try:
            parsed_args = parser.parse_args(args)
            
            filters = {
                'type': parsed_args.type,
                'category': parsed_args.category,
                'start_date': parsed_args.start_date,
                'end_date': parsed_args.end_date,
                'account': parsed_args.account,
                'tags': parsed_args.tags
            }
            
            transactions = await self.transaction_service.get_transactions(
                filters=filters,
                limit=parsed_args.limit,
                sort_by=parsed_args.sort,
                order=parsed_args.order
            )
            
            if not transactions:
                return {
                    'type': 'message',
                    'level': 'info',
                    'content': "No transactions found matching your criteria."
                }
            
            headers = ["ID", "Date", "Type", "Amount", "Category", "Description", "Account"]
            rows = []
            
            for t in transactions:
                sign = "+" if t.type == "income" else "-"
                rows.append([
                    t.id[:8] + "...",
                    t.date,
                    t.type.title(),
                    f"{sign}${t.amount:,.2f}",
                    t.category,
                    t.description[:30] + "..." if len(t.description) > 30 else t.description,
                    t.account
                ])
            
            return {
                'type': 'table',
                'title': f'TRANSACTIONS ({len(transactions)} found)',
                'headers': headers,
                'rows': rows
            }
            
        except Exception as e:
            raise CommandError(f"Error listing transactions: {e}")
    
    async def _handle_edit_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle edit transaction command."""
        parser = argparse.ArgumentParser(description='Edit a transaction')
        parser.add_argument('transaction_id', help='Transaction ID to edit')
        parser.add_argument('--amount', type=float)
        parser.add_argument('--category')
        parser.add_argument('--description')
        parser.add_argument('--date')
        parser.add_argument('--tags', nargs='*')
        parser.add_argument('--account')
        
        try:
            parsed_args = parser.parse_args(args)
            
            updates = {}
            for field in ['amount', 'category', 'description', 'date', 'tags', 'account']:
                value = getattr(parsed_args, field)
                if value is not None:
                    updates[field] = value
            
            if not updates:
                return {
                    'type': 'message',
                    'level': 'warning',
                    'content': "No updates provided."
                }
            
            success = await self.transaction_service.update_transaction(
                parsed_args.transaction_id, updates
            )
            
            if success:
                return {
                    'type': 'message',
                    'level': 'success',
                    'content': f"✅ Transaction {parsed_args.transaction_id} updated successfully"
                }
            else:
                return {
                    'type': 'message',
                    'level': 'error',
                    'content': f"❌ Transaction {parsed_args.transaction_id} not found"
                }
                
        except Exception as e:
            raise CommandError(f"Error editing transaction: {e}")
    
    async def _handle_delete_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle delete transaction command."""
        if not args:
            raise CommandError("Transaction ID required")
        
        transaction_id = args[0]
        
        try:
            success = await self.transaction_service.delete_transaction(transaction_id)
            
            if success:
                return {
                    'type': 'message',
                    'level': 'success',
                    'content': f"✅ Transaction {transaction_id} deleted successfully"
                }
            else:
                return {
                    'type': 'message',
                    'level': 'error',
                    'content': f"❌ Transaction {transaction_id} not found"
                }
                
        except Exception as e:
            raise CommandError(f"Error deleting transaction: {e}")
    
    async def _handle_search_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle search transactions command."""
        if not args:
            raise CommandError("Search query required")
        
        query = ' '.join(args)
        
        try:
            transactions = await self.transaction_service.search_transactions(query)
            
            if not transactions:
                return {
                    'type': 'message',
                    'level': 'info',
                    'content': f"No transactions found for query: '{query}'"
                }
            
            headers = ["ID", "Date", "Type", "Amount", "Category", "Description"]
            rows = []
            
            for t in transactions:
                sign = "+" if t.type == "income" else "-"
                rows.append([
                    t.id[:8] + "...",
                    t.date,
                    t.type.title(),
                    f"{sign}${t.amount:,.2f}",
                    t.category,
                    t.description[:40] + "..." if len(t.description) > 40 else t.description
                ])
            
            return {
                'type': 'table',
                'title': f'SEARCH RESULTS for "{query}" ({len(transactions)} found)',
                'headers': headers,
                'rows': rows
            }
            
        except Exception as e:
            raise CommandError(f"Error searching transactions: {e}")
    
    # Analytics Commands
    async def _handle_summary_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle summary command."""
        parser = argparse.ArgumentParser(description='Generate financial summary')
        parser.add_argument('--period', choices=['week', 'month', 'quarter', 'year', 'all'], default='month')
        parser.add_argument('--start-date')
        parser.add_argument('--end-date')
        parser.add_argument('--account')
        
        try:
            parsed_args = parser.parse_args(args)
            
            # Calculate date range based on period
            end_date = datetime.now()
            if parsed_args.period == 'week':
                start_date = end_date - timedelta(days=7)
            elif parsed_args.period == 'month':
                start_date = end_date.replace(day=1)
            elif parsed_args.period == 'quarter':
                quarter_start_month = ((end_date.month - 1) // 3) * 3 + 1
                start_date = end_date.replace(month=quarter_start_month, day=1)
            elif parsed_args.period == 'year':
                start_date = end_date.replace(month=1, day=1)
            else:
                start_date = None
            
            # Override with custom dates if provided
            if parsed_args.start_date:
                start_date = datetime.strptime(parsed_args.start_date, '%Y-%m-%d')
            if parsed_args.end_date:
                end_date = datetime.strptime(parsed_args.end_date, '%Y-%m-%d')
            
            summary = await self.analytics_service.generate_summary(
                start_date=start_date.strftime('%Y-%m-%d') if start_date else None,
                end_date=end_date.strftime('%Y-%m-%d'),
                account=parsed_args.account
            )
            
            # Format summary as text
            content = f"""
{'='*60}
                    FINANCIAL SUMMARY
{'='*60}
Period: {parsed_args.period.title()} ({summary.get('date_range', 'All time')})
Account: {parsed_args.account or 'All accounts'}

OVERVIEW:
---------
Total Income:     ${summary['total_income']:>12,.2f}
Total Expenses:   ${summary['total_expenses']:>12,.2f}
{'─'*35}
Net Balance:      ${summary['net_balance']:>12,.2f}
Savings Rate:     {summary.get('savings_rate', 0):>11.1f}%

TRANSACTION COUNT:
------------------
Income Transactions:  {summary['income_count']:>8}
Expense Transactions: {summary['expense_count']:>8}
Total Transactions:   {summary['total_count']:>8}

TOP INCOME CATEGORIES:
"""
            
            for category, amount in list(summary.get('top_income_categories', {}).items())[:5]:
                percentage = (amount / summary['total_income'] * 100) if summary['total_income'] > 0 else 0
                content += f"  {category:<20} ${amount:>10,.2f} ({percentage:>5.1f}%)\n"
            
            content += "\nTOP EXPENSE CATEGORIES:\n"
            for category, amount in list(summary.get('top_expense_categories', {}).items())[:5]:
                percentage = (amount / summary['total_expenses'] * 100) if summary['total_expenses'] > 0 else 0
                content += f"  {category:<20} ${amount:>10,.2f} ({percentage:>5.1f}%)\n"
            
            content += f"\n{'='*60}\n"
            
            return {
                'type': 'text',
                'content': content
            }
            
        except Exception as e:
            raise CommandError(f"Error generating summary: {e}")
    
    async def _handle_analytics_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle analytics command."""
        parser = argparse.ArgumentParser(description='Generate advanced analytics')
        parser.add_argument('--type', choices=['spending', 'income', 'trends', 'patterns'], default='spending')
        parser.add_argument('--period', choices=['month', 'quarter', 'year'], default='month')
        parser.add_argument('--category')
        
        try:
            parsed_args = parser.parse_args(args)
            
            if parsed_args.type == 'spending':
                data = await self.analytics_service.analyze_spending_patterns(
                    period=parsed_args.period,
                    category=parsed_args.category
                )
            elif parsed_args.type == 'income':
                data = await self.analytics_service.analyze_income_patterns(
                    period=parsed_args.period
                )
            elif parsed_args.type == 'trends':
                data = await self.analytics_service.analyze_trends(
                    period=parsed_args.period
                )
            else:
                data = await self.analytics_service.detect_patterns()
            
            return {
                'type': 'chart',
                'title': f'{parsed_args.type.title()} Analytics - {parsed_args.period.title()}',
                'data': data,
                'chart_type': 'bar'
            }
            
        except Exception as e:
            raise CommandError(f"Error generating analytics: {e}")
    
    # Budget Commands
    async def _handle_budget_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle budget commands."""
        if not args:
            raise CommandError("Budget subcommand required (create, list, status, update, delete)")
        
        subcommand = args[0]
        subargs = args[1:]
        
        if subcommand == 'create':
            return await self._handle_budget_create(subargs)
        elif subcommand == 'list':
            return await self._handle_budget_list(subargs)
        elif subcommand == 'status':
            return await self._handle_budget_status(subargs)
        elif subcommand == 'update':
            return await self._handle_budget_update(subargs)
        elif subcommand == 'delete':
            return await self._handle_budget_delete(subargs)
        else:
            raise CommandError(f"Unknown budget subcommand: {subcommand}")
    
    async def _handle_budget_create(self, args: List[str]) -> Dict[str, Any]:
        """Handle budget creation."""
        parser = argparse.ArgumentParser(description='Create a new budget')
        parser.add_argument('--name', required=True)
        parser.add_argument('--category', required=True)
        parser.add_argument('--amount', type=float, required=True)
        parser.add_argument('--period', choices=['weekly', 'monthly', 'quarterly', 'yearly'], default='monthly')
        parser.add_argument('--start-date')
        parser.add_argument('--alert-threshold', type=float, default=80.0)
        
        try:
            parsed_args = parser.parse_args(args)
            
            budget_data = {
                'name': parsed_args.name,
                'category': parsed_args.category,
                'amount': parsed_args.amount,
                'period': parsed_args.period,
                'start_date': parsed_args.start_date or datetime.now().strftime('%Y-%m-%d'),
                'alert_threshold': parsed_args.alert_threshold
            }
            
            budget = await self.budget_service.create_budget(budget_data)
            
            return {
                'type': 'message',
                'level': 'success',
                'content': f"✅ Created budget '{parsed_args.name}' for {parsed_args.category}: ${parsed_args.amount:,.2f}/{parsed_args.period}"
            }
            
        except Exception as e:
            raise CommandError(f"Error creating budget: {e}")
    
    async def _handle_budget_list(self, args: List[str]) -> Dict[str, Any]:
        """Handle budget listing."""
        try:
            budgets = await self.budget_service.get_all_budgets()
            
            if not budgets:
                return {
                    'type': 'message',
                    'level': 'info',
                    'content': "No budgets found. Create one with 'budget create'."
                }
            
            headers = ["Name", "Category", "Amount", "Period", "Spent", "Remaining", "Status"]
            rows = []
            
            for budget in budgets:
                status = await self.budget_service.get_budget_status(budget.id)
                spent = status.get('spent', 0)
                remaining = budget.amount - spent
                status_text = status.get('status', 'OK')
                
                rows.append([
                    budget.name,
                    budget.category,
                    f"${budget.amount:,.2f}",
                    budget.period,
                    f"${spent:,.2f}",
                    f"${remaining:,.2f}",
                    status_text
                ])
            
            return {
                'type': 'table',
                'title': 'BUDGET OVERVIEW',
                'headers': headers,
                'rows': rows
            }
            
        except Exception as e:
            raise CommandError(f"Error listing budgets: {e}")
    
    # Goal Commands
    async def _handle_goal_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle goal commands."""
        if not args:
            raise CommandError("Goal subcommand required (create, list, progress, update, delete)")
        
        subcommand = args[0]
        subargs = args[1:]
        
        if subcommand == 'create':
            return await self._handle_goal_create(subargs)
        elif subcommand == 'list':
            return await self._handle_goal_list(subargs)
        elif subcommand == 'progress':
            return await self._handle_goal_progress(subargs)
        else:
            raise CommandError(f"Unknown goal subcommand: {subcommand}")
    
    async def _handle_goal_create(self, args: List[str]) -> Dict[str, Any]:
        """Handle goal creation."""
        parser = argparse.ArgumentParser(description='Create a new financial goal')
        parser.add_argument('--name', required=True)
        parser.add_argument('--target-amount', type=float, required=True)
        parser.add_argument('--target-date', required=True)
        parser.add_argument('--category')
        parser.add_argument('--description')
        
        try:
            parsed_args = parser.parse_args(args)
            
            goal_data = {
                'name': parsed_args.name,
                'target_amount': parsed_args.target_amount,
                'target_date': parsed_args.target_date,
                'category': parsed_args.category,
                'description': parsed_args.description or f"Save ${parsed_args.target_amount:,.2f} by {parsed_args.target_date}"
            }
            
            goal = await self.goal_service.create_goal(goal_data)
            
            return {
                'type': 'message',
                'level': 'success',
                'content': f"✅ Created goal '{parsed_args.name}': ${parsed_args.target_amount:,.2f} by {parsed_args.target_date}"
            }
            
        except Exception as e:
            raise CommandError(f"Error creating goal: {e}")
    
    # Export/Import Commands
    async def _handle_export_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle export command."""
        parser = argparse.ArgumentParser(description='Export financial data')
        parser.add_argument('--format', choices=['csv', 'json', 'xlsx', 'pdf'], default='csv')
        parser.add_argument('--filename')
        parser.add_argument('--start-date')
        parser.add_argument('--end-date')
        parser.add_argument('--include', nargs='*', choices=['transactions', 'budgets', 'goals'], 
                           default=['transactions'])
        
        try:
            parsed_args = parser.parse_args(args)
            
            filename = parsed_args.filename or f"finance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            result = await self.import_export_service.export_data(
                format=parsed_args.format,
                filename=filename,
                start_date=parsed_args.start_date,
                end_date=parsed_args.end_date,
                include=parsed_args.include
            )
            
            return {
                'type': 'message',
                'level': 'success',
                'content': f"✅ Data exported to {result['filename']}"
            }
            
        except Exception as e:
            raise CommandError(f"Error exporting data: {e}")
    
    # Backup Commands
    async def _handle_backup_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle backup command."""
        try:
            backup_file = await self.backup_service.create_backup()
            
            return {
                'type': 'message',
                'level': 'success',
                'content': f"✅ Backup created: {backup_file}"
            }
            
        except Exception as e:
            raise CommandError(f"Error creating backup: {e}")
    
    # Utility Commands
    async def _handle_categories_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle categories command."""
        try:
            categories = await self.transaction_service.get_categories()
            
            content = "\n📂 AVAILABLE CATEGORIES:\n" + "─" * 30 + "\n"
            content += "INCOME CATEGORIES:\n"
            for cat in categories.get('income', []):
                content += f"  • {cat}\n"
            
            content += "\nEXPENSE CATEGORIES:\n"
            for cat in categories.get('expense', []):
                content += f"  • {cat}\n"
            
            return {
                'type': 'text',
                'content': content
            }
            
        except Exception as e:
            raise CommandError(f"Error getting categories: {e}")
    
    async def _handle_stats_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle stats command."""
        try:
            stats = await self.analytics_service.get_system_stats()
            
            content = f"""
📊 SYSTEM STATISTICS
{'='*40}
Total Transactions: {stats['total_transactions']:,}
Total Income:       ${stats['total_income']:,.2f}
Total Expenses:     ${stats['total_expenses']:,.2f}
Active Budgets:     {stats['active_budgets']}
Active Goals:       {stats['active_goals']}
Database Size:      {stats['database_size']} MB
Last Backup:        {stats['last_backup']}
"""
            
            return {
                'type': 'text',
                'content': content
            }
            
        except Exception as e:
            raise CommandError(f"Error getting stats: {e}")
    
    # Help methods
    def _get_add_help(self) -> str:
        return """
ADD COMMAND HELP
================

Usage: add --type <income|expense> --amount <amount> --category <category> --description <description> [options]

Required Arguments:
  --type              Transaction type (income or expense)
  --amount            Transaction amount (positive number)
  --category          Transaction category
  --description       Transaction description

Optional Arguments:
  --date              Transaction date (YYYY-MM-DD format, default: today)
  --tags              Space-separated list of tags
  --recurring         Make transaction recurring (daily, weekly, monthly, yearly)
  --account           Account name (default: 'default')

Examples:
  add --type income --amount 5000 --category Salary --description "Monthly salary"
  add --type expense --amount 50 --category Food --description "Grocery shopping" --tags grocery essentials
  add --type expense --amount 1200 --category Rent --description "Monthly rent" --recurring monthly
"""
    
    def _get_list_help(self) -> str:
        return """
LIST COMMAND HELP
=================

Usage: list [options]

Optional Arguments:
  --type              Filter by transaction type (income or expense)
  --category          Filter by category
  --start-date        Start date filter (YYYY-MM-DD)
  --end-date          End date filter (YYYY-MM-DD)
  --limit             Maximum number of transactions to show (default: 50)
  --sort              Sort by field (date, amount, category)
  --order             Sort order (asc or desc, default: desc)
  --account           Filter by account
  --tags              Filter by tags (space-separated)

Examples:
  list
  list --type expense --category Food
  list --start-date 2024-01-01 --end-date 2024-01-31
  list --sort amount --order desc --limit 10
"""
    
    def _get_budget_help(self) -> str:
        return """
BUDGET COMMAND HELP
===================

Usage: budget <subcommand> [options]

Subcommands:
  create              Create a new budget
  list                List all budgets
  status              Check budget status
  update              Update existing budget
  delete              Delete a budget

Create Budget:
  budget create --name <name> --category <category> --amount <amount> [options]
  
  Required:
    --name              Budget name
    --category          Budget category
    --amount            Budget amount
  
  Optional:
    --period            Budget period (weekly, monthly, quarterly, yearly)
    --start-date        Budget start date
    --alert-threshold   Alert threshold percentage (default: 80)

Examples:
  budget create --name "Food Budget" --category Food --amount 500 --period monthly
  budget list
  budget status
"""
