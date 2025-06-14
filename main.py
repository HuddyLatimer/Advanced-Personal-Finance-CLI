#!/usr/bin/env python3
"""
Advanced Personal Finance CLI Application
Main entry point for the comprehensive financial management system.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.application import FinanceApplication
from core.config import Config
from utils.logger import setup_logging
from utils.exceptions import FinanceAppError


async def main():
    """Main entry point for the application."""
    try:
        # Setup logging
        logger = setup_logging()
        logger.info("Starting Advanced Personal Finance CLI")
        
        # Load configuration
        config = Config()
        
        # Initialize and run application
        app = FinanceApplication(config)
        await app.run()
        
    except FinanceAppError as e:
        print(f"❌ Application Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n💰 Thanks for using Advanced Personal Finance CLI! Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
