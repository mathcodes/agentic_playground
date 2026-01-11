#!/usr/bin/env python3
"""
Demo script to show Voice-to-SQL capabilities without database setup.
This demonstrates the SQL generation using Claude.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import config
from src.sql.generator import generate_sql

def main():
    print("=" * 60)
    print("VOICE-TO-SQL DEMO (SQL Generation Only)")
    print("=" * 60)
    print()
    
    # Check API key
    if not config.ANTHROPIC_API_KEY:
        print("❌ ANTHROPIC_API_KEY is not set!")
        print("Please set it:")
        print('  export ANTHROPIC_API_KEY="your_key_here"')
        return 1
    
    print("✅ Anthropic API configured")
    print(f"   Model: {config.ANTHROPIC_MODEL}")
    print()
    
    # Sample queries
    test_queries = [
        "How many products do we have?",
        "Show me all orders from last month",
        "What are the top 5 customers by total order value?",
        "Which products are low on stock in the Raleigh warehouse?",
        "List all safety equipment products with their prices",
    ]
    
    print("Generating SQL for sample questions...")
    print("=" * 60)
    print()
    
    for i, query in enumerate(test_queries, 1):
        print(f"{i}. Question: {query}")
        print("-" * 60)
        
        result = generate_sql(query)
        
        if result['success']:
            print(f"Generated SQL:")
            print(f"  {result['sql']}")
        else:
            print(f"❌ Error: {result['error']}")
        
        print()
    
    print("=" * 60)
    print("✅ SQL Generation Demo Complete!")
    print()
    print("Next steps:")
    print("  1. Fix PostgreSQL authentication (run ./fix_postgres.sh)")
    print("  2. Initialize database (python scripts/init_db.py)")
    print("  3. Run full app (python main.py --text-mode)")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
