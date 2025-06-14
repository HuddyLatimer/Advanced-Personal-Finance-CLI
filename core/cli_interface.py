"""
Advanced CLI interface with rich formatting and interactive features.
"""

import asyncio
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
import shlex

from .command_processor import CommandProcessor
from .config import Config
from utils.logger import get_logger
from utils.formatters import TableFormatter, ChartFormatter, ColorFormatter
from utils.input_validator import InputValidator
from utils.autocomplete import AutoCompleter


class CLIInterface:
    """Advanced command-line interface with rich features."""
    
    def __init__(self, command_processor: CommandProcessor, config: Config):
        self.command_processor = command_processor
        self.config = config
        self.logger = get_logger(__name__)
        
        # Formatters
        self.table_formatter = TableFormatter(config.ui)
        self.chart_formatter = ChartFormatter(config.ui)
        self.color_formatter = ColorFormatter(config.ui.show_colors)
        
        # Input handling
        self.input_validator = InputValidator()
        self.autocompleter = AutoCompleter()
        
        # Session state
        self.session_active = True
        self.command_history = []
        self.current_context = "main"
        
        # Command aliases
        self.aliases = {
            'a': 'add',
            'l': 'list',
            'e': 'edit',
            'd': 'delete',
            's': 'summary',
            'r': 'report',
            'b': 'budget',
            'g': 'goal',
            'h': 'help',
            'q': 'quit',
            'x': 'exit'
        }
    
    async def run(self):
        """Run the main CLI loop."""
        await self._show_welcome()
        
        while self.session_active:
            try:
                # Get user input
                prompt = self._get_prompt()
                user_input = await self._get_input(prompt)
                
                if not user_input.strip():
                    continue
                
                # Add to history
                self.command_history.append(user_input)
                
                # Process command
                await self._process_command(user_input)
                
            except KeyboardInterrupt:
                await self._handle_interrupt()
            except EOFError:
                break
            except Exception as e:
                self.logger.error(f"CLI error: {e}")
                self._print_error(f"An error occurred: {e}")
        
        await self._show_goodbye()
    
    async def _show_welcome(self):
        """Display welcome message."""
        welcome_text = f"""
{self.color_formatter.header('='*80)}
{self.color_formatter.title(f'{self.config.app_name} v{self.config.version}'):^80}
{self.color_formatter.subtitle('Advanced Personal Finance Management System'):^80}
{self.color_formatter.header('='*80)}

{self.color_formatter.info('💡 Quick Start:')}
  • Type {self.color_formatter.command('help')} to see all available commands
  • Type {self.color_formatter.command('tutorial')} for a guided tour
  • Type {self.color_formatter.command('add')} to create your first transaction
  • Type {self.color_formatter.command('quit')} to exit

{self.color_formatter.success('🚀 Ready to manage your finances!')}
"""
        print(welcome_text)
    
    async def _show_goodbye(self):
        """Display goodbye message."""
        goodbye_text = f"""
{self.color_formatter.header('='*60)}
{self.color_formatter.title('Thank you for using Personal Finance CLI!'):^60}
{self.color_formatter.subtitle('Your financial data has been saved securely.'):^60}
{self.color_formatter.header('='*60)}

{self.color_formatter.info('💰 Keep tracking your finances for better financial health!')}
"""
        print(goodbye_text)
    
    def _get_prompt(self) -> str:
        """Generate the command prompt."""
        timestamp = datetime.now().strftime("%H:%M")
        context_indicator = f"[{self.current_context}]" if self.current_context != "main" else ""
        
        return self.color_formatter.prompt(f"finance{context_indicator} ({timestamp})> ")
    
    async def _get_input(self, prompt: str) -> str:
        """Get user input with autocomplete support."""
        try:
            # For now, use simple input - in a real implementation,
            # you might use readline or prompt_toolkit for advanced features
            return input(prompt)
        except (KeyboardInterrupt, EOFError):
            raise
    
    async def _process_command(self, user_input: str):
        """Process a user command."""
        try:
            # Parse command and arguments
            parts = shlex.split(user_input)
            if not parts:
                return
            
            command = parts[0].lower()
            args = parts[1:]
            
            # Handle aliases
            command = self.aliases.get(command, command)
            
            # Handle built-in CLI commands
            if await self._handle_builtin_command(command, args):
                return
            
            # Process through command processor
            result = await self.command_processor.process_command(command, args)
            
            if result:
                await self._display_result(result)
                
        except Exception as e:
            self.logger.error(f"Command processing error: {e}")
            self._print_error(f"Error processing command: {e}")
    
    async def _handle_builtin_command(self, command: str, args: List[str]) -> bool:
        """Handle built-in CLI commands."""
        if command in ['quit', 'exit']:
            self.session_active = False
            return True
        
        elif command == 'help':
            await self._show_help(args)
            return True
        
        elif command == 'history':
            await self._show_history()
            return True
        
        elif command == 'clear':
            os.system('cls' if os.name == 'nt' else 'clear')
            return True
        
        elif command == 'config':
            await self._handle_config_command(args)
            return True
        
        elif command == 'tutorial':
            await self._show_tutorial()
            return True
        
        return False
    
    async def _show_help(self, args: List[str]):
        """Display help information."""
        if not args:
            help_text = f"""
{self.color_formatter.header('AVAILABLE COMMANDS')}
{self.color_formatter.header('='*50)}

{self.color_formatter.section('📊 TRANSACTION MANAGEMENT')}
  {self.color_formatter.command('add')}           Add new income or expense transaction
  {self.color_formatter.command('list')}          List transactions with filters
  {self.color_formatter.command('edit')}          Edit existing transaction
  {self.color_formatter.command('delete')}        Delete transaction
  {self.color_formatter.command('search')}        Search transactions

{self.color_formatter.section('💰 BUDGET MANAGEMENT')}
  {self.color_formatter.command('budget create')} Create new budget
  {self.color_formatter.command('budget list')}   List all budgets
  {self.color_formatter.command('budget status')} Check budget status
  {self.color_formatter.command('budget alert')}  Set budget alerts

{self.color_formatter.section('🎯 GOAL TRACKING')}
  {self.color_formatter.command('goal create')}   Create financial goal
  {self.color_formatter.command('goal list')}     List all goals
  {self.color_formatter.command('goal progress')} Check goal progress
  {self.color_formatter.command('goal update')}   Update goal status

{self.color_formatter.section('📈 ANALYTICS & REPORTS')}
  {self.color_formatter.command('summary')}       Financial summary
  {self.color_formatter.command('report')}        Detailed reports
  {self.color_formatter.command('analytics')}     Advanced analytics
  {self.color_formatter.command('trends')}        Spending trends
  {self.color_formatter.command('forecast')}      Financial forecasting

{self.color_formatter.section('💾 DATA MANAGEMENT')}
  {self.color_formatter.command('export')}        Export data
  {self.color_formatter.command('import')}        Import data
  {self.color_formatter.command('backup')}        Create backup
  {self.color_formatter.command('restore')}       Restore from backup

{self.color_formatter.section('⚙️  SYSTEM')}
  {self.color_formatter.command('config')}        Configuration settings
  {self.color_formatter.command('history')}       Command history
  {self.color_formatter.command('clear')}         Clear screen
  {self.color_formatter.command('help')}          Show this help
  {self.color_formatter.command('quit')}          Exit application

{self.color_formatter.info('💡 Use')} {self.color_formatter.command('help <command>')} {self.color_formatter.info('for detailed help on specific commands')}
{self.color_formatter.info('💡 Use')} {self.color_formatter.command('tutorial')} {self.color_formatter.info('for a guided tour')}
"""
            print(help_text)
        else:
            # Show help for specific command
            command = args[0]
            detailed_help = await self.command_processor.get_command_help(command)
            if detailed_help:
                print(detailed_help)
            else:
                self._print_error(f"No help available for command: {command}")
    
    async def _show_history(self):
        """Display command history."""
        if not self.command_history:
            print(self.color_formatter.info("No command history available."))
            return
        
        print(f"\n{self.color_formatter.header('COMMAND HISTORY')}")
        print(self.color_formatter.header('='*40))
        
        for i, command in enumerate(self.command_history[-20:], 1):  # Show last 20 commands
            print(f"{i:2d}. {command}")
        print()
    
    async def _handle_config_command(self, args: List[str]):
        """Handle configuration commands."""
        if not args:
            await self._show_config()
        elif args[0] == 'set' and len(args) >= 3:
            section, key, value = args[1], args[2], args[3]
            try:
                self.config.update_setting(section, key, value)
                print(self.color_formatter.success(f"✅ Updated {section}.{key} = {value}"))
            except Exception as e:
                self._print_error(f"Error updating configuration: {e}")
        elif args[0] == 'get' and len(args) >= 2:
            section, key = args[1], args[2] if len(args) > 2 else None
            if key:
                value = self.config.get_setting(section, key)
                print(f"{section}.{key} = {value}")
            else:
                section_obj = getattr(self.config, section, None)
                if section_obj:
                    for attr, value in section_obj.__dict__.items():
                        print(f"{section}.{attr} = {value}")
        else:
            self._print_error("Usage: config [set <section> <key> <value>] [get <section> [key]]")
    
    async def _show_config(self):
        """Display current configuration."""
        config_text = f"""
{self.color_formatter.header('CURRENT CONFIGURATION')}
{self.color_formatter.header('='*50)}

{self.color_formatter.section('Database Settings:')}
  Path: {self.config.database.path}
  Backup Interval: {self.config.database.backup_interval_hours} hours
  Max Backups: {self.config.database.max_backups}

{self.color_formatter.section('UI Settings:')}
  Theme: {self.config.ui.theme}
  Currency: {self.config.ui.currency_symbol}
  Date Format: {self.config.ui.date_format}
  Colors: {'Enabled' if self.config.ui.show_colors else 'Disabled'}

{self.color_formatter.section('Notifications:')}
  Budget Alerts: {'Enabled' if self.config.notifications.enable_budget_alerts else 'Disabled'}
  Goal Reminders: {'Enabled' if self.config.notifications.enable_goal_reminders else 'Disabled'}
  Budget Threshold: {self.config.notifications.budget_threshold_percentage}%
"""
        print(config_text)
    
    async def _show_tutorial(self):
        """Display interactive tutorial."""
        tutorial_steps = [
            {
                'title': 'Welcome to Personal Finance CLI!',
                'content': 'This tutorial will guide you through the main features.',
                'action': None
            },
            {
                'title': 'Adding Your First Transaction',
                'content': 'Let\'s add an income transaction. Try: add --type income --amount 1000 --category Salary --description "Monthly salary"',
                'action': 'add'
            },
            {
                'title': 'Viewing Transactions',
                'content': 'Now let\'s see your transactions. Try: list',
                'action': 'list'
            },
            {
                'title': 'Creating a Budget',
                'content': 'Set up a budget to track spending. Try: budget create --category Food --amount 500 --period monthly',
                'action': 'budget'
            },
            {
                'title': 'Viewing Summary',
                'content': 'Get an overview of your finances. Try: summary',
                'action': 'summary'
            }
        ]
        
        print(f"\n{self.color_formatter.header('🎓 PERSONAL FINANCE CLI TUTORIAL')}")
        print(self.color_formatter.header('='*60))
        
        for i, step in enumerate(tutorial_steps, 1):
            print(f"\n{self.color_formatter.section(f'Step {i}: {step[\"title\"]}')}")
            print(step['content'])
            
            if step['action']:
                response = input(f"\nPress Enter to continue or type the command to try it: ")
                if response.strip():
                    await self._process_command(response)
            else:
                input("\nPress Enter to continue...")
        
        print(f"\n{self.color_formatter.success('🎉 Tutorial completed! You\'re ready to manage your finances.')}")
    
    async def _display_result(self, result: Dict[str, Any]):
        """Display command result."""
        if result.get('type') == 'table':
            self.table_formatter.print_table(
                result['headers'],
                result['rows'],
                result.get('title')
            )
        elif result.get('type') == 'chart':
            self.chart_formatter.print_chart(
                result['data'],
                result.get('title'),
                result.get('chart_type', 'bar')
            )
        elif result.get('type') == 'message':
            if result.get('level') == 'success':
                print(self.color_formatter.success(result['content']))
            elif result.get('level') == 'error':
                print(self.color_formatter.error(result['content']))
            elif result.get('level') == 'warning':
                print(self.color_formatter.warning(result['content']))
            else:
                print(self.color_formatter.info(result['content']))
        elif result.get('type') == 'text':
            print(result['content'])
    
    def _print_error(self, message: str):
        """Print error message."""
        print(self.color_formatter.error(f"❌ {message}"))
    
    async def _handle_interrupt(self):
        """Handle Ctrl+C interrupt."""
        response = input(f"\n{self.color_formatter.warning('Are you sure you want to exit? (y/N): ')}")
        if response.lower() in ['y', 'yes']:
            self.session_active = False
        else:
            print(self.color_formatter.info("Continuing..."))
