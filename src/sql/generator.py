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
    Validate that the SQL is safe to execute.
    Returns (is_safe, reason).
    """
    sql_upper = sql.upper()
    
    # List of dangerous keywords
    dangerous_keywords = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'TRUNCATE', 
        'ALTER', 'CREATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE'
    ]
    
    if not config.ALLOW_WRITE_QUERIES:
        for keyword in dangerous_keywords:
            # Check for keyword as a whole word
            if re.search(rf'\b{keyword}\b', sql_upper):
                return False, f"Query contains forbidden keyword: {keyword}"
    
    # Check for multiple statements (SQL injection attempt)
    # Count semicolons not at the end
    semicolons = sql.count(';')
    if semicolons > 1:
        return False, "Multiple statements detected - potential SQL injection"
    
    # Check for comments (could hide malicious code)
    if '--' in sql or '/*' in sql:
        return False, "SQL comments not allowed"
    
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
