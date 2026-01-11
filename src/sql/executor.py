"""
SQL Executor.
Safely executes SQL queries and formats results.
"""

import psycopg2 # this is the database connector
from psycopg2 import sql as psycopg2_sql
from typing import List, Dict, Any, Optional # this is the type hinting
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import config


class QueryResult:
    """Container for query results."""
    
    def __init__(
        self,
        success: bool,
        columns: Optional[List[str]] = None,
        rows: Optional[List[tuple]] = None,
        row_count: int = 0,
        error: Optional[str] = None,
        execution_time_ms: float = 0
    ):
        self.success = success
        self.columns = columns or []
        self.rows = rows or []
        self.row_count = row_count
        self.error = error
        self.execution_time_ms = execution_time_ms
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'columns': self.columns,
            'rows': [list(row) for row in self.rows],
            'row_count': self.row_count,
            'error': self.error,
            'execution_time_ms': self.execution_time_ms
        }
    
    def to_dicts(self) -> List[Dict[str, Any]]:
        """Convert rows to list of dictionaries."""
        return [dict(zip(self.columns, row)) for row in self.rows]


def execute_query(sql: str, params: tuple = None) -> QueryResult:
    """
    Execute a SQL query and return results.
    
    Args:
        sql: The SQL query to execute
        params: Optional tuple of parameters for parameterized queries
        
    Returns:
        QueryResult object with results or error
    """
    import time
    
    conn = None
    cursor = None
    
    try:
        start_time = time.time()
        
        # Connect to database
        conn = psycopg2.connect(config.DATABASE_URL)
        cursor = conn.cursor()
        
        # Execute query
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        
        # Get column names
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        # Fetch results (with limit)
        rows = cursor.fetchmany(config.MAX_RESULTS)
        row_count = cursor.rowcount
        
        execution_time = (time.time() - start_time) * 1000
        
        return QueryResult(
            success=True,
            columns=columns,
            rows=rows,
            row_count=row_count,
            execution_time_ms=round(execution_time, 2)
        )
        
    except psycopg2.Error as e:
        return QueryResult(
            success=False,
            error=f"Database error: {e.pgerror or str(e)}"
        )
    except Exception as e:
        return QueryResult(
            success=False,
            error=f"Execution error: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def format_results_table(result: QueryResult, max_width: int = 80) -> str:
    """
    Format query results as a nice ASCII table.
    """
    if not result.success:
        return f"Error: {result.error}"
    
    if not result.rows:
        return "No results found."
    
    try:
        from tabulate import tabulate
        table = tabulate(
            result.rows,
            headers=result.columns,
            tablefmt="simple",
            maxcolwidths=30
        )
        return table
    except ImportError:
        # Fallback if tabulate not installed
        lines = []
        lines.append(" | ".join(result.columns))
        lines.append("-" * 60)
        for row in result.rows[:20]:
            lines.append(" | ".join(str(v)[:30] for v in row))
        return "\n".join(lines)


def format_results_natural(result: QueryResult) -> str:
    """
    Format results in a more natural, conversational way.
    Good for single-value or small result sets.
    """
    if not result.success:
        return f"I encountered an error: {result.error}"
    
    if not result.rows:
        return "I didn't find any results matching your query."
    
    # Single value result (e.g., COUNT, SUM)
    if len(result.columns) == 1 and len(result.rows) == 1:
        col = result.columns[0]
        val = result.rows[0][0]
        
        # Try to make it conversational
        if 'count' in col.lower():
            return f"There are {val} records."
        elif 'sum' in col.lower() or 'total' in col.lower():
            return f"The total is {val}."
        elif 'avg' in col.lower() or 'average' in col.lower():
            return f"The average is {val}."
        else:
            return f"The result is: {val}"
    
    # Small result set
    if len(result.rows) <= 5:
        return format_results_table(result)
    
    # Larger result set
    summary = f"Found {result.row_count} results. Here are the first few:\n\n"
    summary += format_results_table(QueryResult(
        success=True,
        columns=result.columns,
        rows=result.rows[:10],
        row_count=10
    ))
    
    if result.row_count > 10:
        summary += f"\n\n... and {result.row_count - 10} more rows."
    
    return summary


if __name__ == "__main__":
    # Test queries
    print("Testing SQL Executor")
    print("=" * 60)
    
    # Test 1: Simple count
    print("\nTest 1: Count products")
    result = execute_query("SELECT COUNT(*) as product_count FROM products;")
    print(format_results_natural(result))
    
    # Test 2: Select with limit
    print("\nTest 2: List products")
    result = execute_query("SELECT sku, name, unit_price FROM products LIMIT 5;")
    print(format_results_table(result))
    
    # Test 3: Aggregation
    print("\nTest 3: Sales by customer")
    result = execute_query("""
        SELECT c.company_name, COUNT(o.id) as order_count, SUM(o.total) as total_sales
        FROM customers c
        JOIN orders o ON c.id = o.customer_id
        GROUP BY c.company_name
        ORDER BY total_sales DESC
        LIMIT 5;
    """)
    print(format_results_table(result))
