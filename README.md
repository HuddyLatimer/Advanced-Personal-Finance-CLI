# 💰 Advanced Personal Finance CLI

A comprehensive command-line application for managing personal finances with advanced features including budget tracking, goal setting, analytics, and automated insights.


## 🌟 Features

### 📊 Transaction Management
- **Add, edit, and delete** income and expense transactions
- **Advanced filtering** by date, category, amount, tags, and more
- **Full-text search** across descriptions, categories, and notes
- **Recurring transactions** with flexible scheduling
- **Multi-account support** for different financial accounts
- **Receipt and location tracking** for detailed records

### 💰 Budget Management
- **Create flexible budgets** with weekly, monthly, quarterly, or yearly periods
- **Real-time budget tracking** with automatic expense categorization
- **Smart alerts** when approaching budget limits
- **Budget rollover** for unused amounts
- **Auto-adjustment** based on spending patterns

### 🎯 Goal Tracking
- **Set financial goals** with target amounts and dates
- **Milestone tracking** with automatic progress updates
- **Multiple goal types**: savings, debt payoff, investment, purchases
- **Automated contributions** with flexible scheduling
- **Progress visualization** and completion forecasting

### 📈 Advanced Analytics
- **Comprehensive financial summaries** with key metrics
- **Spending pattern analysis** and trend identification
- **Category breakdown** with percentage distributions
- **Monthly/yearly trend analysis** with visual charts
- **Savings rate calculation** and financial health scoring
- **Predictive forecasting** based on historical data

### 🔧 System Features
- **Async/await architecture** for optimal performance
- **SQLite database** with connection pooling and WAL mode
- **Intelligent caching** for faster data retrieval
- **Comprehensive logging** with configurable levels
- **Automatic backups** with retention policies
- **Data import/export** in multiple formats (CSV, JSON, Excel, PDF)
- **Rich CLI interface** with colors and interactive features

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager


### First Time Setup

When you first run the application, it will:
- Create necessary directories (`finance_data`, `logs`, `backups`)
- Initialize the SQLite database with all required tables
- Create a default configuration file (`config.json`)
- Display a welcome message with quick start tips

## 📖 Usage Guide

### Interactive Mode (Recommended)

Launch the application without arguments to enter interactive mode:

\`\`\`bash
python scripts/main.py
\`\`\`

You'll see a rich interface with:
- **Colored output** for better readability
- **Command suggestions** and autocomplete
- **Context-aware prompts** with timestamps
- **Built-in help system** with examples

### Command Line Mode

Execute commands directly from the terminal:

\`\`\`bash
# Add a transaction
python scripts/main.py add --type income --amount 5000 --category Salary --description "Monthly salary"

# List recent transactions
python scripts/main.py list --limit 10

# Generate monthly summary
python scripts/main.py summary --period month

# Create a budget
python scripts/main.py budget create --name "Food Budget" --category Food --amount 500 --period monthly
\`\`\`

## 🎮 Command Reference

### Transaction Commands

#### Add Transaction
\`\`\`bash
add --type <income|expense> --amount <amount> --category <category> --description <description> [options]
\`\`\`

**Options:**
- `--date`: Transaction date (YYYY-MM-DD, default: today)
- `--tags`: Space-separated tags
- `--recurring`: Make recurring (daily, weekly, monthly, yearly)
- `--account`: Account name (default: 'default')
- `--location`: Transaction location
- `--merchant`: Merchant name
- `--payment-method`: Payment method used

**Examples:**
\`\`\`bash
# Basic income transaction
add --type income --amount 5000 --category Salary --description "Monthly salary"

# Expense with tags and location
add --type expense --amount 50 --category Food --description "Grocery shopping" --tags grocery essentials --location "Whole Foods"

# Recurring rent payment
add --type expense --amount 1200 --category Rent --description "Monthly rent" --recurring monthly
\`\`\`

#### List Transactions
\`\`\`bash
list [options]
\`\`\`

**Options:**
- `--type`: Filter by income/expense
- `--category`: Filter by category
- `--start-date`, `--end-date`: Date range filters
- `--limit`: Maximum results (default: 50)
- `--sort`: Sort by date, amount, or category
- `--order`: asc or desc (default: desc)
- `--account`: Filter by account
- `--tags`: Filter by tags

**Examples:**
\`\`\`bash
# List all transactions
list

# List expenses from last month
list --type expense --start-date 2024-01-01 --end-date 2024-01-31

# List top 10 largest expenses
list --type expense --sort amount --order desc --limit 10

# List transactions with specific tags
list --tags grocery restaurant
\`\`\`

#### Search Transactions
\`\`\`bash
search <query>
\`\`\`

**Examples:**
\`\`\`bash
# Search by description
search "coffee"

# Search by merchant
search "Amazon"
\`\`\`

#### Edit Transaction
\`\`\`bash
edit <transaction_id> [options]
\`\`\`

**Examples:**
\`\`\`bash
# Update amount and category
edit abc123def --amount 75.50 --category Entertainment

# Add tags to existing transaction
edit abc123def --tags movie date-night
\`\`\`

### Budget Commands

#### Create Budget
\`\`\`bash
budget create --name <name> --category <category> --amount <amount> [options]
\`\`\`

**Options:**
- `--period`: weekly, monthly, quarterly, yearly (default: monthly)
- `--start-date`: Budget start date
- `--alert-threshold`: Alert percentage (default: 80)

**Examples:**
\`\`\`bash
# Monthly food budget
budget create --name "Food Budget" --category Food --amount 500 --period monthly

# Quarterly entertainment budget with custom alert
budget create --name "Fun Money" --category Entertainment --amount 300 --period quarterly --alert-threshold 75
\`\`\`

#### List Budgets
\`\`\`bash
budget list
\`\`\`

#### Check Budget Status
\`\`\`bash
budget status [budget_name]
\`\`\`

### Goal Commands

#### Create Goal
\`\`\`bash
goal create --name <name> --target-amount <amount> --target-date <date> [options]
\`\`\`

**Options:**
- `--category`: Goal category
- `--description`: Detailed description
- `--priority`: low, medium, high, critical

**Examples:**
\`\`\`bash
# Emergency fund goal
goal create --name "Emergency Fund" --target-amount 10000 --target-date 2024-12-31 --priority high

# Vacation savings goal
goal create --name "Europe Trip" --target-amount 5000 --target-date 2024-06-01 --category Travel --description "2-week Europe vacation"
\`\`\`

#### List Goals
\`\`\`bash
goal list
\`\`\`

#### Check Goal Progress
\`\`\`bash
goal progress [goal_name]
\`\`\`

### Analytics Commands

#### Financial Summary
\`\`\`bash
summary [options]
\`\`\`

**Options:**
- `--period`: week, month, quarter, year, all (default: month)
- `--start-date`, `--end-date`: Custom date range
- `--account`: Filter by account

**Examples:**
\`\`\`bash
# Current month summary
summary

# Yearly summary
summary --period year

# Custom date range
summary --start-date 2024-01-01 --end-date 2024-03-31
\`\`\`

#### Detailed Reports
\`\`\`bash
report [options]
\`\`\`

#### Advanced Analytics
\`\`\`bash
analytics --type <spending|income|trends|patterns> [options]
\`\`\`

**Examples:**
\`\`\`bash
# Spending pattern analysis
analytics --type spending --period month

# Income trend analysis
analytics --type income --period quarter

# Detect spending patterns
analytics --type patterns
\`\`\`

### Data Management Commands

#### Export Data
\`\`\`bash
export --format <csv|json|xlsx|pdf> [options]
\`\`\`

**Options:**
- `--filename`: Output filename
- `--start-date`, `--end-date`: Date range
- `--include`: transactions, budgets, goals (default: transactions)

**Examples:**
\`\`\`bash
# Export all transactions to CSV
export --format csv --filename my_finances

# Export specific date range to Excel
export --format xlsx --start-date 2024-01-01 --end-date 2024-12-31 --filename 2024_finances

# Export everything to JSON
export --format json --include transactions budgets goals
\`\`\`

#### Import Data
\`\`\`bash
import --format <csv|json> --file <filename> [options]
\`\`\`

#### Backup & Restore
\`\`\`bash
# Create backup
backup

# Restore from backup
restore --file <backup_filename>
\`\`\`

### System Commands

#### Configuration
\`\`\`bash
# View current configuration
config

# Update a setting
config set ui currency_symbol €

# Get specific setting
config get database backup_interval_hours
\`\`\`

#### System Statistics
\`\`\`bash
stats
\`\`\`

#### Help System
\`\`\`bash
# General help
help

# Command-specific help
help add
help budget
help goal
\`\`\`

## ⚙️ Configuration

The application uses a JSON configuration file (`config.json`) with the following sections:

### Database Configuration
\`\`\`json
{
  "database": {
    "path": "finance_data.db",
    "backup_interval_hours": 24,
    "max_backups": 30,
    "enable_wal_mode": true
  }
}
\`\`\`

### UI Configuration
\`\`\`json
{
  "ui": {
    "theme": "default",
    "currency_symbol": "$",
    "date_format": "%Y-%m-%d",
    "decimal_places": 2,
    "show_colors": true
  }
}
\`\`\`

### Notification Configuration
\`\`\`json
{
  "notifications": {
    "enable_budget_alerts": true,
    "enable_goal_reminders": true,
    "budget_threshold_percentage": 80.0,
    "reminder_frequency_days": 7
  }
}
\`\`\`

### Security Configuration
\`\`\`json
{
  "security": {
    "enable_encryption": false,
    "session_timeout_minutes": 60,
    "max_login_attempts": 3
  }
}
\`\`\`

## 🔧 Advanced Features

### Recurring Transactions
Set up automatic recurring transactions for regular income and expenses:

\`\`\`bash
# Monthly salary
add --type income --amount 5000 --category Salary --description "Monthly salary" --recurring monthly

# Weekly grocery budget
add --type expense --amount 100 --category Food --description "Weekly groceries" --recurring weekly
\`\`\`

### Smart Categorization
The system learns from your transaction patterns and can automatically suggest categories for new transactions based on:
- Description keywords
- Merchant names
- Transaction amounts
- Historical patterns

### Budget Alerts
Receive notifications when:
- Approaching budget limits (configurable threshold)
- Budget periods are ending
- Budgets are exceeded
- Unusual spending patterns are detected

### Goal Milestones
Goals automatically create milestones at 25%, 50%, 75%, and 100% completion, with:
- Achievement tracking
- Progress notifications
- Projected completion dates
- Contribution recommendations

### Financial Health Scoring
The system calculates various financial health metrics:
- Savings rate percentage
- Budget adherence score
- Goal progress rating
- Spending consistency index
- Emergency fund ratio

### Data Analytics
Advanced analytics features include:
- Spending trend analysis
- Seasonal pattern detection
- Category distribution analysis
- Income vs. expense correlation
- Financial forecasting
- Anomaly detection

## 🛠️ Development

### Running Tests
\`\`\`bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=scripts

# Run specific test file
python -m pytest tests/test_transaction_service.py
\`\`\`

### Code Quality
\`\`\`bash
# Format code
black scripts/

# Lint code
flake8 scripts/

# Type checking
mypy scripts/
\`\`\`

### Database Migrations
When adding new features that require database changes:

1. Update the table creation SQL in `database_manager.py`
2. Add migration logic for existing databases
3. Update the corresponding repository classes
4. Test with both new and existing databases

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Style
- Follow PEP 8 guidelines
- Use type hints for all functions
- Write docstrings for all classes and methods
- Keep functions focused and small
- Use meaningful variable and function names

## 🗺️ Roadmap

### Version 2.1 (Planned)
- [ ] Web dashboard interface
- [ ] Mobile app companion
- [ ] Bank account integration
- [ ] Investment tracking
- [ ] Tax reporting features

### Version 2.2 (Future)
- [ ] Multi-currency support
- [ ] Advanced forecasting with ML
- [ ] Collaborative budgets
- [ ] API for third-party integrations
- [ ] Cloud synchronization

### Version 3.0 (Vision)
- [ ] AI-powered financial advisor
- [ ] Automated bill management
- [ ] Credit score monitoring
- [ ] Investment recommendations
- [ ] Comprehensive financial planning

---

