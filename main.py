#!/usr/bin/env python3
"""
Voice-to-SQL Agent - Main Entry Point

An agentic AI application that converts spoken natural language
into SQL queries and executes them against a PostgreSQL database.

Usage:
    python main.py                  # Interactive voice mode
    python main.py --text "query"   # Text mode
    python main.py --file audio.wav # Process audio file
    python main.py --test           # Run test queries
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config, config
from src.agent.orchestrator import VoiceToSQLAgent, run_interactive_session


def print_banner():
    """Print the application banner."""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                   VOICE-TO-SQL AGENT                      ║
║        Convert natural language to SQL queries            ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def run_text_query(query: str):
    """Run a single text query."""
    agent = VoiceToSQLAgent(verbose=True)
    result = agent.process_text(query)
    
    print("\n" + "=" * 60)
    print(result)
    print("=" * 60)
    
    return 0 if result.success else 1


def run_audio_file(file_path: str):
    """Process an audio file."""
    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}")
        return 1
    
    agent = VoiceToSQLAgent(verbose=True)
    result = agent.process_audio_file(file_path)
    
    print("\n" + "=" * 60)
    print(result)
    print("=" * 60)
    
    return 0 if result.success else 1


def run_tests():
    """Run test queries to verify the system works."""
    print("Running system tests...\n")
    
    # Test database connection
    print("1. Testing database connection...")
    try:
        from src.sql.executor import execute_query
        result = execute_query("SELECT 1 as test;")
        if result.success:
            print("   ✅ Database connection OK")
        else:
            print(f"   ❌ Database error: {result.error}")
            return 1
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return 1
    
    # Test schema extraction
    print("\n2. Testing schema extraction...")
    try:
        from src.sql.schema import get_table_names
        tables = get_table_names()
        if tables:
            print(f"   ✅ Found {len(tables)} tables: {', '.join(tables[:5])}...")
        else:
            print("   ⚠️  No tables found (run init_db.py first)")
    except Exception as e:
        print(f"   ❌ Schema extraction failed: {e}")
        return 1
    
    # Test SQL generation (requires API key)
    print("\n3. Testing SQL generation...")
    if not config.ANTHROPIC_API_KEY:
        print("   ⚠️  Skipping (ANTHROPIC_API_KEY not set)")
    else:
        try:
            from src.sql.generator import generate_sql
            result = generate_sql("How many products are there?")
            if result['success']:
                print(f"   ✅ SQL generated: {result['sql'][:50]}...")
            else:
                print(f"   ❌ Generation failed: {result['error']}")
        except Exception as e:
            print(f"   ❌ SQL generation error: {e}")
    
    # Test full pipeline with text input
    print("\n4. Testing full pipeline (text mode)...")
    if not config.ANTHROPIC_API_KEY:
        print("   ⚠️  Skipping (ANTHROPIC_API_KEY not set)")
    else:
        try:
            agent = VoiceToSQLAgent(verbose=False)
            result = agent.process_text("What are the top 3 products by price?")
            if result.success:
                print(f"   ✅ Pipeline OK")
                print(f"      Query: What are the top 3 products by price?")
                print(f"      SQL: {result.generated_sql}")
            else:
                print(f"   ❌ Pipeline failed")
                if result.sql_generation_error:
                    print(f"      SQL error: {result.sql_generation_error}")
                if result.execution_error:
                    print(f"      Execution error: {result.execution_error}")
        except Exception as e:
            print(f"   ❌ Pipeline error: {e}")
    
    # Check audio dependencies
    print("\n5. Checking audio dependencies...")
    try:
        import sounddevice
        print("   ✅ sounddevice installed")
    except ImportError:
        print("   ⚠️  sounddevice not installed (audio capture won't work)")
    
    try:
        import whisper
        print(f"   ✅ whisper installed")
    except ImportError:
        print("   ⚠️  whisper not installed (transcription won't work)")
    
    print("\n" + "=" * 60)
    print("Tests complete!")
    print("=" * 60)
    
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Voice-to-SQL Agent - Convert speech to SQL queries',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Start interactive voice mode
  python main.py -t "Show all products"   # Run a text query
  python main.py -f recording.wav         # Process an audio file
  python main.py --test                   # Run system tests
  python main.py --config                 # Show current configuration
        """
    )
    
    parser.add_argument(
        '-t', '--text',
        type=str,
        help='Run a text query directly (skip audio)'
    )
    
    parser.add_argument(
        '-f', '--file',
        type=str,
        help='Process an audio file'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run system tests'
    )
    
    parser.add_argument(
        '--config',
        action='store_true',
        help='Show current configuration'
    )
    
    parser.add_argument(
        '--text-mode',
        action='store_true',
        help='Run in text-only interactive mode (no audio)'
    )
    
    args = parser.parse_args()
    
    # Show config
    if args.config:
        Config.print_config()
        return 0
    
    # Run tests
    if args.test:
        return run_tests()
    
    # Validate configuration
    errors = Config.validate()
    if errors and not args.test:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease set up your .env file (see .env.example)")
        return 1
    
    print_banner()
    
    # Single text query
    if args.text:
        return run_text_query(args.text)
    
    # Audio file
    if args.file:
        return run_audio_file(args.file)
    
    # Text-only interactive mode
    if args.text_mode:
        return run_text_interactive()
    
    # Interactive voice mode (default)
    try:
        run_interactive_session()
        return 0
    except KeyboardInterrupt:
        print("\nGoodbye!")
        return 0


def run_text_interactive():
    """Run interactive text-only mode."""
    print("Text-only mode (type your queries)\n")
    print("Commands: 'quit' to exit, 'help' for help\n")
    
    agent = VoiceToSQLAgent(verbose=False)
    
    while True:
        try:
            query = input("Query> ").strip()
            
            if not query:
                continue
            
            if query.lower() in ('quit', 'exit', 'q'):
                print("Goodbye!")
                break
            
            if query.lower() == 'help':
                print("\nEnter natural language questions about the database.")
                print("Examples:")
                print("  - How many products do we have?")
                print("  - Show me orders from last month")
                print("  - What customers have the highest order totals?")
                print("  - Which products are low on stock?\n")
                continue
            
            result = agent.process_text(query)
            
            print()
            if result.success:
                print(f"SQL: {result.generated_sql}")
                print(f"\nResults:\n{result.formatted_output}")
            else:
                print(f"Error: {result}")
            print()
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
