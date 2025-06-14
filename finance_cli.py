#!/usr/bin/env python3
"""
Personal Finance CLI Application
A command-line tool for managing personal finances with income/expense tracking,
categorization, and comprehensive reporting features.
"""

import json
import csv
import argparse
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import sys


class Transaction:
    """Represents a financial transaction (income or expense)."""
    
    def __init__(self, amount: float, category: str, description: str, 
                 transaction_type: str, date: str = None, transaction_id: str = None):
        self.id = transaction_id or self._generate_id()
        self.amount = float(amount)
        self.category = category.title()
        self.description = description
        self.type = transaction_type.lower()  # 'income' or 'expense'
        self.date = date or datetime.now().strftime('%Y-%m-%d')
    
    def _generate_id(self) -> str:
        """Generate a unique transaction ID."""
        return f"{datetime.now().strftime('%Y%m%d%H%M%S')}{hash(self.description) % 1000:03d}"
    
    def to_dict(self) -> Dict:
        """Convert transaction to dictionary for JSON storage."""
        return {
            'id': self.id,
            'amount': self.amount,
            'category': self.category,
            'description': self.description,
            'type': self.type,
            'date': self.date
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Transaction':
        """Create transaction from dictionary."""
        return cls(
            amount=data['amount'],
            category=data['category'],
            description=data['description'],
            transaction_type=data['type'],
            date=data['date'],
            transaction_id=data['id']
        )
    
    def __str__(self) -> str:
        sign = '+' if self.type == 'income' else '-'
        return f"{self.date} | {sign}${self.amount:,.2f} | {self.category} | {self.description}"


class FinanceManager:
    """Main class for managing financial transactions and data persistence."""
    
    def __init__(self, data_file: str = 'finance_data.json'):
        self.data_file = data_file
        self.transactions: List[Transaction] = []
        self.categories = {
            'income': ['Salary', 'Freelance', 'Investment', 'Gift', 'Other Income'],
            'expense': ['Food', 'Rent', 'Transportation', 'Entertainment', 'Healthcare', 
                       'Shopping', 'Utilities', 'Education', 'Other Expense']
        }
        self.load_data()
    
    def load_data(self) -> None:
        """Load transactions from JSON file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.transactions = [Transaction.from_dict(t) for t in data.get('transactions', [])]
                    # Load custom categories if they exist
                    if 'categories' in data:
                        self.categories.update(data['categories'])
                print(f"Loaded {len(self.transactions)} transactions from {self.data_file}")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading data: {e}. Starting with empty data.")
                self.transactions = []
        else:
            print("No existing data file found. Starting fresh!")
    
    def save_data(self) -> None:
        """Save transactions to JSON file."""
        data = {
            'transactions': [t.to_dict() for t in self.transactions],
            'categories': self.categories,
            'last_updated': datetime.now().isoformat()
        }
        try:
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Data saved to {self.data_file}")
        except IOError as e:
            print(f"Error saving data: {e}")
    
    def add_transaction(self, amount: float, category: str, description: str, 
                       transaction_type: str) -> None:
        """Add a new transaction."""
        # Validate transaction type
        if transaction_type.lower() not in ['income', 'expense']:
            raise ValueError("Transaction type must be 'income' or 'expense'")
        
        # Add category if it doesn't exist
        if category not in self.categories[transaction_type.lower()]:
            self.categories[transaction_type.lower()].append(category)
        
        transaction = Transaction(amount, category, description, transaction_type)
        self.transactions.append(transaction)
        self.save_data()
        print(f"✅ Added {transaction_type}: ${amount:,.2f} in {category}")
    
    def edit_transaction(self, transaction_id: str, **kwargs) -> bool:
        """Edit an existing transaction."""
        for transaction in self.transactions:
            if transaction.id == transaction_id:
                for key, value in kwargs.items():
                    if hasattr(transaction, key) and value is not None:
                        setattr(transaction, key, value)
                self.save_data()
                print(f"✅ Transaction {transaction_id} updated successfully")
                return True
        print(f"❌ Transaction {transaction_id} not found")
        return False
    
    def delete_transaction(self, transaction_id: str) -> bool:
        """Delete a transaction by ID."""
        for i, transaction in enumerate(self.transactions):
            if transaction.id == transaction_id:
                deleted = self.transactions.pop(i)
                self.save_data()
                print(f"✅ Deleted transaction: {deleted}")
                return True
        print(f"❌ Transaction {transaction_id} not found")
        return False
    
    def get_transactions_by_date_range(self, start_date: str = None, 
                                     end_date: str = None) -> List[Transaction]:
        """Get transactions within a date range."""
        if not start_date:
            start_date = '1900-01-01'
        if not end_date:
            end_date = '2100-12-31'
        
        return [t for t in self.transactions 
                if start_date <= t.date <= end_date]
    
    def get_summary(self, start_date: str = None, end_date: str = None) -> Dict:
        """Generate financial summary for given date range."""
        transactions = self.get_transactions_by_date_range(start_date, end_date)
        
        total_income = sum(t.amount for t in transactions if t.type == 'income')
        total_expenses = sum(t.amount for t in transactions if t.type == 'expense')
        net_balance = total_income - total_expenses
        
        # Category breakdown
        income_by_category = defaultdict(float)
        expense_by_category = defaultdict(float)
        
        for t in transactions:
            if t.type == 'income':
                income_by_category[t.category] += t.amount
            else:
                expense_by_category[t.category] += t.amount
        
        return {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_balance': net_balance,
            'income_by_category': dict(income_by_category),
            'expense_by_category': dict(expense_by_category),
            'transaction_count': len(transactions),
            'date_range': f"{start_date or 'All time'} to {end_date or 'Present'}"
        }


class ReportGenerator:
    """Generate and format financial reports."""
    
    @staticmethod
    def print_table(headers: List[str], rows: List[List[str]], title: str = None) -> None:
        """Print a formatted table."""
        if title:
            print(f"\n{'='*60}")
            print(f"{title:^60}")
            print(f"{'='*60}")
        
        # Calculate column widths
        col_widths = [len(header) for header in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Print headers
        header_row = " | ".join(header.ljust(col_widths[i]) for i, header in enumerate(headers))
        print(f"\n{header_row}")
        print("-" * len(header_row))
        
        # Print rows
        for row in rows:
            formatted_row = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
            print(formatted_row)
        print()
    
    @staticmethod
    def print_bar_chart(data: Dict[str, float], title: str, max_width: int = 50) -> None:
        """Print a text-based bar chart."""
        if not data:
            print(f"\n{title}: No data available\n")
            return
        
        print(f"\n{'='*60}")
        print(f"{title:^60}")
        print(f"{'='*60}")
        
        max_value = max(data.values()) if data.values() else 1
        
        for category, amount in sorted(data.items(), key=lambda x: x[1], reverse=True):
            bar_length = int((amount / max_value) * max_width) if max_value > 0 else 0
            bar = "█" * bar_length
            print(f"{category:<20} | {bar:<{max_width}} | ${amount:>10,.2f}")
        print()
    
    @staticmethod
    def generate_summary_report(summary: Dict) -> str:
        """Generate a formatted summary report."""
        report = f"""
{'='*60}
                    FINANCIAL SUMMARY
{'='*60}
Date Range: {summary['date_range']}
Total Transactions: {summary['transaction_count']}

OVERVIEW:
---------
Total Income:     ${summary['total_income']:>12,.2f}
Total Expenses:   ${summary['total_expenses']:>12,.2f}
{'─'*35}
Net Balance:      ${summary['net_balance']:>12,.2f}

INCOME BREAKDOWN:
"""
        
        if summary['income_by_category']:
            for category, amount in sorted(summary['income_by_category'].items(), 
                                         key=lambda x: x[1], reverse=True):
                percentage = (amount / summary['total_income'] * 100) if summary['total_income'] > 0 else 0
                report += f"  {category:<20} ${amount:>10,.2f} ({percentage:>5.1f}%)\n"
        else:
            report += "  No income recorded\n"
        
        report += "\nEXPENSE BREAKDOWN:\n"
        if summary['expense_by_category']:
            for category, amount in sorted(summary['expense_by_category'].items(), 
                                         key=lambda x: x[1], reverse=True):
                percentage = (amount / summary['total_expenses'] * 100) if summary['total_expenses'] > 0 else 0
                report += f"  {category:<20} ${amount:>10,.2f} ({percentage:>5.1f}%)\n"
        else:
            report += "  No expenses recorded\n"
        
        report += f"\n{'='*60}\n"
        return report


class FinanceCLI:
    """Command-line interface for the Personal Finance app."""
    
    def __init__(self):
        self.finance_manager = FinanceManager()
        self.report_generator = ReportGenerator()
    
    def run_interactive_mode(self) -> None:
        """Run the interactive CLI loop."""
        print("🏦 Welcome to Personal Finance CLI!")
        print("Type 'help' for available commands or 'quit' to exit.\n")
        
        while True:
            try:
                command = input("finance> ").strip().lower()
                
                if command in ['quit', 'exit', 'q']:
                    print("💰 Thanks for using Personal Finance CLI! Goodbye!")
                    break
                elif command == 'help':
                    self.show_help()
                elif command == 'add':
                    self.interactive_add_transaction()
                elif command == 'list':
                    self.interactive_list_transactions()
                elif command == 'edit':
                    self.interactive_edit_transaction()
                elif command == 'delete':
                    self.interactive_delete_transaction()
                elif command == 'summary':
                    self.interactive_summary()
                elif command == 'report':
                    self.interactive_report()
                elif command == 'export':
                    self.interactive_export()
                elif command == 'categories':
                    self.show_categories()
                elif command == '':
                    continue
                else:
                    print(f"Unknown command: {command}. Type 'help' for available commands.")
            
            except KeyboardInterrupt:
                print("\n💰 Thanks for using Personal Finance CLI! Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def show_help(self) -> None:
        """Display help information."""
        help_text = """
📋 AVAILABLE COMMANDS:
─────────────────────
add        - Add a new income or expense transaction
list       - List all transactions (with optional filters)
edit       - Edit an existing transaction
delete     - Delete a transaction
summary    - Show financial summary
report     - Generate detailed reports with charts
export     - Export data to CSV file
categories - Show available categories
help       - Show this help message
quit/exit  - Exit the application

💡 TIP: You can also use command-line arguments for quick operations!
"""
        print(help_text)
    
    def show_categories(self) -> None:
        """Display available categories."""
        print("\n📂 AVAILABLE CATEGORIES:")
        print("─" * 30)
        print("INCOME CATEGORIES:")
        for cat in self.finance_manager.categories['income']:
            print(f"  • {cat}")
        
        print("\nEXPENSE CATEGORIES:")
        for cat in self.finance_manager.categories['expense']:
            print(f"  • {cat}")
        print()
    
    def interactive_add_transaction(self) -> None:
        """Interactive transaction addition."""
        try:
            print("\n➕ ADD NEW TRANSACTION")
            print("─" * 25)
            
            # Get transaction type
            while True:
                trans_type = input("Type (income/expense): ").strip().lower()
                if trans_type in ['income', 'expense']:
                    break
                print("Please enter 'income' or 'expense'")
            
            # Show relevant categories
            print(f"\nAvailable {trans_type} categories:")
            for i, cat in enumerate(self.finance_manager.categories[trans_type], 1):
                print(f"  {i}. {cat}")
            
            # Get category
            category = input(f"\nCategory (or enter new): ").strip()
            if category.isdigit():
                idx = int(category) - 1
                if 0 <= idx < len(self.finance_manager.categories[trans_type]):
                    category = self.finance_manager.categories[trans_type][idx]
            
            # Get amount
            while True:
                try:
                    amount = float(input("Amount: $"))
                    if amount > 0:
                        break
                    print("Amount must be positive")
                except ValueError:
                    print("Please enter a valid number")
            
            # Get description
            description = input("Description: ").strip()
            if not description:
                description = f"{trans_type.title()} - {category}"
            
            self.finance_manager.add_transaction(amount, category, description, trans_type)
            
        except KeyboardInterrupt:
            print("\n❌ Transaction cancelled")
    
    def interactive_list_transactions(self) -> None:
        """Interactive transaction listing."""
        print("\n📋 TRANSACTION LIST")
        print("─" * 20)
        
        # Ask for filters
        filter_type = input("Filter by type (income/expense/all): ").strip().lower()
        if filter_type not in ['income', 'expense', 'all', '']:
            filter_type = 'all'
        
        start_date = input("Start date (YYYY-MM-DD, or press Enter for all): ").strip()
        end_date = input("End date (YYYY-MM-DD, or press Enter for all): ").strip()
        
        # Get filtered transactions
        transactions = self.finance_manager.get_transactions_by_date_range(
            start_date if start_date else None,
            end_date if end_date else None
        )
        
        if filter_type != 'all':
            transactions = [t for t in transactions if t.type == filter_type]
        
        if not transactions:
            print("No transactions found matching your criteria.")
            return
        
        # Display transactions
        headers = ["ID", "Date", "Type", "Amount", "Category", "Description"]
        rows = []
        
        for t in sorted(transactions, key=lambda x: x.date, reverse=True):
            sign = "+" if t.type == "income" else "-"
            rows.append([
                t.id[:8] + "...",
                t.date,
                t.type.title(),
                f"{sign}${t.amount:,.2f}",
                t.category,
                t.description[:30] + "..." if len(t.description) > 30 else t.description
            ])
        
        self.report_generator.print_table(headers, rows, f"TRANSACTIONS ({len(transactions)} found)")
    
    def interactive_edit_transaction(self) -> None:
        """Interactive transaction editing."""
        if not self.finance_manager.transactions:
            print("No transactions to edit.")
            return
        
        print("\n✏️  EDIT TRANSACTION")
        print("─" * 20)
        
        # Show recent transactions for reference
        recent = sorted(self.finance_manager.transactions, key=lambda x: x.date, reverse=True)[:10]
        print("Recent transactions:")
        for i, t in enumerate(recent, 1):
            print(f"  {i}. {t.id[:8]}... | {t.date} | {t.type} | ${t.amount:,.2f} | {t.description[:30]}")
        
        transaction_id = input("\nEnter transaction ID (or number from list above): ").strip()
        
        # Handle numeric selection
        if transaction_id.isdigit():
            idx = int(transaction_id) - 1
            if 0 <= idx < len(recent):
                transaction_id = recent[idx].id
        
        # Find the transaction
        transaction = None
        for t in self.finance_manager.transactions:
            if t.id.startswith(transaction_id):
                transaction = t
                break
        
        if not transaction:
            print("Transaction not found.")
            return
        
        print(f"\nCurrent transaction: {transaction}")
        print("\nEnter new values (press Enter to keep current value):")
        
        # Get new values
        new_amount = input(f"Amount (current: ${transaction.amount:,.2f}): ").strip()
        new_category = input(f"Category (current: {transaction.category}): ").strip()
        new_description = input(f"Description (current: {transaction.description}): ").strip()
        
        # Update transaction
        updates = {}
        if new_amount:
            try:
                updates['amount'] = float(new_amount)
            except ValueError:
                print("Invalid amount, keeping current value.")
        
        if new_category:
            updates['category'] = new_category
        
        if new_description:
            updates['description'] = new_description
        
        if updates:
            self.finance_manager.edit_transaction(transaction.id, **updates)
        else:
            print("No changes made.")
    
    def interactive_delete_transaction(self) -> None:
        """Interactive transaction deletion."""
        if not self.finance_manager.transactions:
            print("No transactions to delete.")
            return
        
        print("\n🗑️  DELETE TRANSACTION")
        print("─" * 22)
        
        # Show recent transactions
        recent = sorted(self.finance_manager.transactions, key=lambda x: x.date, reverse=True)[:10]
        print("Recent transactions:")
        for i, t in enumerate(recent, 1):
            print(f"  {i}. {t.id[:8]}... | {t.date} | {t.type} | ${t.amount:,.2f} | {t.description[:30]}")
        
        transaction_id = input("\nEnter transaction ID (or number from list above): ").strip()
        
        # Handle numeric selection
        if transaction_id.isdigit():
            idx = int(transaction_id) - 1
            if 0 <= idx < len(recent):
                transaction_id = recent[idx].id
        
        # Confirm deletion
        for t in self.finance_manager.transactions:
            if t.id.startswith(transaction_id):
                confirm = input(f"Delete this transaction? {t} (y/N): ").strip().lower()
                if confirm == 'y':
                    self.finance_manager.delete_transaction(t.id)
                else:
                    print("Deletion cancelled.")
                return
        
        print("Transaction not found.")
    
    def interactive_summary(self) -> None:
        """Interactive summary generation."""
        print("\n📊 FINANCIAL SUMMARY")
        print("─" * 21)
        
        period = input("Period (all/month/year/custom): ").strip().lower()
        
        start_date = None
        end_date = None
        
        if period == 'month':
            # Current month
            now = datetime.now()
            start_date = now.replace(day=1).strftime('%Y-%m-%d')
            end_date = now.strftime('%Y-%m-%d')
        elif period == 'year':
            # Current year
            now = datetime.now()
            start_date = now.replace(month=1, day=1).strftime('%Y-%m-%d')
            end_date = now.strftime('%Y-%m-%d')
        elif period == 'custom':
            start_date = input("Start date (YYYY-MM-DD): ").strip()
            end_date = input("End date (YYYY-MM-DD): ").strip()
        
        summary = self.finance_manager.get_summary(start_date, end_date)
        report = self.report_generator.generate_summary_report(summary)
        print(report)
    
    def interactive_report(self) -> None:
        """Interactive report generation with charts."""
        print("\n📈 DETAILED REPORT")
        print("─" * 18)
        
        period = input("Period (all/month/year/custom): ").strip().lower()
        
        start_date = None
        end_date = None
        
        if period == 'month':
            now = datetime.now()
            start_date = now.replace(day=1).strftime('%Y-%m-%d')
            end_date = now.strftime('%Y-%m-%d')
        elif period == 'year':
            now = datetime.now()
            start_date = now.replace(month=1, day=1).strftime('%Y-%m-%d')
            end_date = now.strftime('%Y-%m-%d')
        elif period == 'custom':
            start_date = input("Start date (YYYY-MM-DD): ").strip()
            end_date = input("End date (YYYY-MM-DD): ").strip()
        
        summary = self.finance_manager.get_summary(start_date, end_date)
        
        # Print summary
        report = self.report_generator.generate_summary_report(summary)
        print(report)
        
        # Print charts
        if summary['income_by_category']:
            self.report_generator.print_bar_chart(
                summary['income_by_category'], 
                "INCOME BY CATEGORY"
            )
        
        if summary['expense_by_category']:
            self.report_generator.print_bar_chart(
                summary['expense_by_category'], 
                "EXPENSES BY CATEGORY"
            )
    
    def interactive_export(self) -> None:
        """Interactive data export."""
        print("\n💾 EXPORT DATA")
        print("─" * 14)
        
        format_type = input("Export format (csv/json/txt): ").strip().lower()
        filename = input("Filename (without extension): ").strip()
        
        if not filename:
            filename = f"finance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if format_type == 'csv':
            self.export_to_csv(f"{filename}.csv")
        elif format_type == 'json':
            self.export_to_json(f"{filename}.json")
        elif format_type == 'txt':
            self.export_to_txt(f"{filename}.txt")
        else:
            print("Invalid format. Supported formats: csv, json, txt")
    
    def export_to_csv(self, filename: str) -> None:
        """Export transactions to CSV file."""
        try:
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = ['id', 'date', 'type', 'amount', 'category', 'description']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for transaction in self.finance_manager.transactions:
                    writer.writerow(transaction.to_dict())
            
            print(f"✅ Data exported to {filename}")
        except IOError as e:
            print(f"❌ Error exporting to CSV: {e}")
    
    def export_to_json(self, filename: str) -> None:
        """Export transactions to JSON file."""
        try:
            data = {
                'transactions': [t.to_dict() for t in self.finance_manager.transactions],
                'categories': self.finance_manager.categories,
                'export_date': datetime.now().isoformat(),
                'total_transactions': len(self.finance_manager.transactions)
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"✅ Data exported to {filename}")
        except IOError as e:
            print(f"❌ Error exporting to JSON: {e}")
    
    def export_to_txt(self, filename: str) -> None:
        """Export summary report to text file."""
        try:
            summary = self.finance_manager.get_summary()
            report = self.report_generator.generate_summary_report(summary)
            
            with open(filename, 'w') as f:
                f.write("PERSONAL FINANCE REPORT\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(report)
                
                f.write("\n\nDETAILED TRANSACTION LIST:\n")
                f.write("=" * 60 + "\n")
                
                for transaction in sorted(self.finance_manager.transactions, 
                                        key=lambda x: x.date, reverse=True):
                    f.write(f"{transaction}\n")
            
            print(f"✅ Report exported to {filename}")
        except IOError as e:
            print(f"❌ Error exporting to TXT: {e}")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Personal Finance CLI - Manage your income and expenses",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python finance_cli.py add --type income --amount 5000 --category Salary --description "Monthly salary"
  python finance_cli.py add --type expense --amount 50 --category Food --description "Grocery shopping"
  python finance_cli.py list --type expense --start-date 2024-01-01
  python finance_cli.py summary --period month
  python finance_cli.py export --format csv --filename my_finances
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add transaction command
    add_parser = subparsers.add_parser('add', help='Add a new transaction')
    add_parser.add_argument('--type', choices=['income', 'expense'], required=True,
                           help='Transaction type')
    add_parser.add_argument('--amount', type=float, required=True,
                           help='Transaction amount')
    add_parser.add_argument('--category', required=True,
                           help='Transaction category')
    add_parser.add_argument('--description', required=True,
                           help='Transaction description')
    
    # List transactions command
    list_parser = subparsers.add_parser('list', help='List transactions')
    list_parser.add_argument('--type', choices=['income', 'expense'],
                            help='Filter by transaction type')
    list_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    list_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    list_parser.add_argument('--category', help='Filter by category')
    
    # Summary command
    summary_parser = subparsers.add_parser('summary', help='Show financial summary')
    summary_parser.add_argument('--period', choices=['all', 'month', 'year'],
                               default='all', help='Summary period')
    summary_parser.add_argument('--start-date', help='Custom start date (YYYY-MM-DD)')
    summary_parser.add_argument('--end-date', help='Custom end date (YYYY-MM-DD)')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export data')
    export_parser.add_argument('--format', choices=['csv', 'json', 'txt'],
                              default='csv', help='Export format')
    export_parser.add_argument('--filename', help='Output filename')
    
    # Interactive mode (default)
    subparsers.add_parser('interactive', help='Run in interactive mode')
    
    return parser


def main():
    """Main entry point for the CLI application."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    cli = FinanceCLI()
    
    try:
        if args.command == 'add':
            cli.finance_manager.add_transaction(
                args.amount, args.category, args.description, args.type
            )
        
        elif args.command == 'list':
            transactions = cli.finance_manager.get_transactions_by_date_range(
                args.start_date, args.end_date
            )
            
            if args.type:
                transactions = [t for t in transactions if t.type == args.type]
            
            if args.category:
                transactions = [t for t in transactions if t.category.lower() == args.category.lower()]
            
            if not transactions:
                print("No transactions found matching your criteria.")
            else:
                headers = ["ID", "Date", "Type", "Amount", "Category", "Description"]
                rows = []
                
                for t in sorted(transactions, key=lambda x: x.date, reverse=True):
                    sign = "+" if t.type == "income" else "-"
                    rows.append([
                        t.id[:8] + "...",
                        t.date,
                        t.type.title(),
                        f"{sign}${t.amount:,.2f}",
                        t.category,
                        t.description[:40] + "..." if len(t.description) > 40 else t.description
                    ])
                
                cli.report_generator.print_table(headers, rows, f"TRANSACTIONS ({len(transactions)} found)")
        
        elif args.command == 'summary':
            start_date = args.start_date
            end_date = args.end_date
            
            if args.period == 'month':
                now = datetime.now()
                start_date = now.replace(day=1).strftime('%Y-%m-%d')
                end_date = now.strftime('%Y-%m-%d')
            elif args.period == 'year':
                now = datetime.now()
                start_date = now.replace(month=1, day=1).strftime('%Y-%m-%d')
                end_date = now.strftime('%Y-%m-%d')
            
            summary = cli.finance_manager.get_summary(start_date, end_date)
            report = cli.report_generator.generate_summary_report(summary)
            print(report)
            
            # Show charts
            if summary['income_by_category']:
                cli.report_generator.print_bar_chart(
                    summary['income_by_category'], 
                    "INCOME BY CATEGORY"
                )
            
            if summary['expense_by_category']:
                cli.report_generator.print_bar_chart(
                    summary['expense_by_category'], 
                    "EXPENSES BY CATEGORY"
                )
        
        elif args.command == 'export':
            filename = args.filename or f"finance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if args.format == 'csv':
                cli.export_to_csv(f"{filename}.csv")
            elif args.format == 'json':
                cli.export_to_json(f"{filename}.json")
            elif args.format == 'txt':
                cli.export_to_txt(f"{filename}.txt")
        
        else:
            # Default to interactive mode
            cli.run_interactive_mode()
    
    except KeyboardInterrupt:
        print("\n💰 Thanks for using Personal Finance CLI! Goodbye!")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
