"""
SQL Generator using Claude.
Converts natural language queries to SQL using LLM reasoning.
"""

import anthropic
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import config
from src.sql.schema import get_full_schema_description


# System prompt for SQL generation
SYSTEM_PROMPT = """You are a SQL query generator for a PostgreSQL database. Your job is to convert natural language questions into valid SQL queries.

IMPORTANT RULES:
1. Generate ONLY the SQL query - no explanations, no markdown, no code blocks
2. Use PostgreSQL syntax
3. Always use table aliases for clarity in joins
4. Limit results to {max_results} rows unless the user specifies otherwise
5. For aggregations, always include meaningful column aliases
6. Be conservative - if unsure about the user's intent, generate a safer/simpler query
7. NEVER generate INSERT, UPDATE, DELETE, DROP, TRUNCATE, or ALTER statements unless explicitly allowed
8. Use ILIKE for case-insensitive text matching
9. When joining tables, always specify the join condition

{schema}

Remember: Return ONLY the SQL query, nothing else."""


def extract_sql_from_response(response: str) -> str:
    """
    Extract SQL from the response, handling cases where the model
    might wrap it in markdown or add explanations.
    """
    # Remove markdown code blocks if present
    sql = re.sub(r'```sql\s*', '', response)
    sql = re.sub(r'```\s*', '', sql)
    
    # Remove any leading/trailing whitespace
    sql = sql.strip()
    
    # If there's text before the SELECT, try to extract just the query
    if not sql.upper().startswith(('SELECT', 'WITH')):
        # Look for SELECT or WITH statement
        match = re.search(r'((?:WITH|SELECT)[\s\S]+?)(?:;|$)', sql, re.IGNORECASE)
        if match:
            sql = match.group(1)
    
    # Ensure it ends with semicolon
    if not sql.endswith(';'):
        sql += ';'
    
    return sql


def validate_sql_safety(sql: str) -> tuple[bool, str]:
    """
    Comprehensive SQL safety validation to prevent injection attacks.
    
    SECURITY: Multi-layer validation:
    1. Keyword blacklist (write operations)
    2. Multiple statement detection (injection)
    3. Comment detection (obfuscation)
    4. Stored procedure calls (command execution)
    5. Union-based injection detection
    6. Stacked queries detection
    
    Returns:
        Tuple of (is_safe, reason_if_unsafe)
    """
    if not sql or not sql.strip():
        return False, "Empty query"
    
    sql_upper = sql.upper()
    sql_stripped = sql.strip()
    
    # SECURITY: List of dangerous keywords
    dangerous_keywords = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'TRUNCATE', 
        'ALTER', 'CREATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE',
        'CALL',  # Stored procedures
        'COPY',  # File operations
        'LOAD',  # Data loading
        'IMPORT',  # Import data
        'EXPORT',  # Export data
    ]
    
    # SECURITY: Block write operations unless explicitly allowed
    if not config.ALLOW_WRITE_QUERIES:
        for keyword in dangerous_keywords:
            # SECURITY: Check for keyword as a whole word (not part of column name)
            # Use word boundaries to match only complete keywords
            if re.search(rf'\b{keyword}\b', sql_upper):
                return False, f"Query contains forbidden keyword: {keyword}"
    
    # SECURITY: Check for multiple statements (SQL injection attempt)
    # Multiple statements separated by semicolons are a classic injection vector
    # Example: "SELECT * FROM users; DROP TABLE users;--"
    semicolons = sql.count(';')
    if semicolons > 1:
        return False, "Multiple statements detected - potential SQL injection"
    
    # SECURITY: Check for SQL comments (could hide malicious code)
    # Comments can be used to bypass security checks and hide malicious queries
    # Example: "SELECT * FROM users WHERE id=1 OR 1=1 --"
    if '--' in sql or '/*' in sql or '*/' in sql:
        return False, "SQL comments not allowed"
    
    # SECURITY: Check for UNION-based SQL injection
    # UNION attacks combine multiple SELECT statements to extract data
    # Example: "' UNION SELECT password FROM users--"
    if 'UNION' in sql_upper and 'SELECT' in sql_upper:
        # Allow legitimate UNION queries but be suspicious
        # Count SELECT statements - should be balanced with UNION
        select_count = len(re.findall(r'\bSELECT\b', sql_upper))
        union_count = len(re.findall(r'\bUNION\b', sql_upper))
        if select_count != union_count + 1:
            return False, "Suspicious UNION query structure"
    
    # SECURITY: Check for stacked queries (PostgreSQL specific)
    # Example: "SELECT * FROM users WHERE id=1; DELETE FROM users;--"
    if ';' in sql_stripped[:-1]:  # Semicolon not at the end
        return False, "Stacked queries detected"
    
    # SECURITY: Check for hexadecimal/binary literals (obfuscation technique)
    # Attackers use hex/binary to hide keywords from detection
    # Example: "SELECT 0x61646d696e" (hex for "admin")
    if re.search(r'0x[0-9a-f]+', sql, re.IGNORECASE):
        return False, "Hexadecimal literals not allowed"
    
    # SECURITY: Check for SQL Server extended stored procedures
    # These can execute system commands
    # Example: "xp_cmdshell 'dir'"
    if re.search(r'\bxp_\w+', sql_upper):
        return False, "Extended stored procedures not allowed"
    
    # SECURITY: Check for PostgreSQL specific dangerous functions
    dangerous_pg_functions = [
        'pg_read_file',    # Read files from filesystem
        'pg_write_file',   # Write files to filesystem
        'pg_ls_dir',       # List directory contents
        'copy_from',       # Copy data from files
        'copy_to',         # Copy data to files
        'lo_import',       # Import large objects
        'lo_export',       # Export large objects
    ]
    
    for func in dangerous_pg_functions:
        if func in sql.lower():
            return False, f"Dangerous function not allowed: {func}"
    
    # SECURITY: Check for information schema queries (information disclosure)
    # While not always malicious, restrict access to schema information
    # Example: "SELECT * FROM information_schema.tables"
    if 'information_schema' in sql.lower() or 'pg_catalog' in sql.lower():
        return False, "Schema information queries not allowed"
    
    # SECURITY: Check for time-based blind SQL injection indicators
    # Example: "SELECT * FROM users WHERE id=1 AND SLEEP(5)"
    time_functions = ['sleep', 'pg_sleep', 'waitfor', 'delay', 'benchmark']
    for func in time_functions:
        if func in sql.lower():
            return False, f"Time-based attack detected: {func}"
    
    # SECURITY: Check for boolean-based blind SQL injection
    # Example: "SELECT * FROM users WHERE id=1 AND 1=1"
    # Look for suspicious boolean expressions
    if re.search(r'\b1\s*=\s*1\b', sql) or re.search(r'\b1\s*=\s*0\b', sql):
        return False, "Boolean-based injection pattern detected"
    
    # SECURITY: Check for NULL byte injection
    # NULL bytes can truncate strings and bypass filters
    if '\x00' in sql:
        return False, "NULL byte detected in query"
    
    # SECURITY: Query must start with SELECT (in read-only mode)
    if not config.ALLOW_WRITE_QUERIES:
        # Allow WITH (CTEs) and SELECT
        if not (sql_stripped.startswith('SELECT') or sql_stripped.startswith('WITH')):
            return False, "Query must start with SELECT or WITH"
    
    return True, "OK"


def generate_sql(natural_language_query: str) -> dict:
    """
    Convert a natural language query to SQL.
    
    Args:
        natural_language_query: The user's question in plain English
        
    Returns:
        dict with keys:
            - success: bool
            - sql: str (the generated SQL, if successful)
            - error: str (error message, if failed)
            - raw_response: str (the raw LLM response)
    """
    # Validate API key
    if not config.ANTHROPIC_API_KEY:
        return {
            'success': False,
            'sql': None,
            'error': 'ANTHROPIC_API_KEY not configured',
            'raw_response': None
        }
    
    # Get schema
    try:
        schema = get_full_schema_description()
    except Exception as e:
        return {
            'success': False,
            'sql': None,
            'error': f'Failed to get database schema: {e}',
            'raw_response': None
        }
    
    # Build the prompt
    system = SYSTEM_PROMPT.format(
        max_results=config.MAX_RESULTS,
        schema=schema
    )
    
    # Call Claude
    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        
        message = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=1024,
            system=system,
            messages=[
                {
                    "role": "user",
                    "content": f"Convert this to SQL: {natural_language_query}"
                }
            ]
        )
        
        raw_response = message.content[0].text
        
    except anthropic.APIError as e:
        return {
            'success': False,
            'sql': None,
            'error': f'API error: {e}',
            'raw_response': None
        }
    
    # Extract and validate SQL
    sql = extract_sql_from_response(raw_response)
    
    is_safe, safety_message = validate_sql_safety(sql)
    if not is_safe:
        return {
            'success': False,
            'sql': sql,
            'error': f'Safety check failed: {safety_message}',
            'raw_response': raw_response
        }
    
    return {
        'success': True,
        'sql': sql,
        'error': None,
        'raw_response': raw_response
    }


if __name__ == "__main__":
    # Test the generator
    test_queries = [
        "How many products do we have?",
        "Show me all orders from last month",
        "What are the top 5 customers by total order value?",
        "Which products are low on stock in the Raleigh warehouse?",
    ]
    
    print("Testing SQL Generator")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        
        result = generate_sql(query)
        
        if result['success']:
            print(f"SQL: {result['sql']}")
        else:
            print(f"Error: {result['error']}")
        
        print()
