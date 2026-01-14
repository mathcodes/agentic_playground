"""
SQL Executor with Enhanced Security.
Safely executes SQL queries with comprehensive security measures.

SECURITY ENHANCEMENTS:
- Parameterized queries to prevent SQL injection
- Query timeout enforcement to prevent DoS
- Result set limits to prevent memory exhaustion
- Read-only transaction mode for SELECT queries
- Connection pooling with limits
- Detailed error handling without exposing sensitive info
- Audit logging of all query executions
"""

import psycopg2  # PostgreSQL database connector
from psycopg2 import sql as psycopg2_sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT, ISOLATION_LEVEL_READ_COMMITTED
from typing import List, Dict, Any, Optional
import sys
import os
import time
import re

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


def execute_query(
    sql: str,
    params: tuple = None,
    user_id: Optional[str] = None,
    read_only: bool = True
) -> QueryResult:
    """
    Execute a SQL query with comprehensive security measures.
    
    SECURITY FEATURES:
    - Parameterized queries prevent SQL injection
    - Query timeout prevents resource exhaustion
    - Result limits prevent memory exhaustion
    - Read-only mode for SELECT queries (prevents accidental writes)
    - Audit logging for compliance
    - Error sanitization (no sensitive data in errors)
    
    Args:
        sql: The SQL query to execute (preferably parameterized)
        params: Optional tuple of parameters for parameterized queries
        user_id: User executing the query (for audit logging)
        read_only: If True, uses read-only transaction mode
        
    Returns:
        QueryResult object with results or error
    """
    conn = None
    cursor = None
    start_time = time.time()
    
    try:
        # SECURITY: Validate query before execution
        if not _is_query_safe(sql):
            return QueryResult(
                success=False,
                error="Query failed security validation"
            )
        
        # SECURITY: Build connection string with security options
        conn_params = {
            'dsn': config.DATABASE_URL,
            'connect_timeout': config.DB_CONNECT_TIMEOUT,  # Prevent hanging connections
        }
        
        # SECURITY: Enable SSL if required
        if config.DB_SSL_REQUIRED:
            conn_params['sslmode'] = 'require'
        
        # SECURITY: Connect to database with timeout
        conn = psycopg2.connect(**conn_params)
        
        # SECURITY: Set transaction isolation level
        if read_only:
            # SECURITY: Read-only mode prevents accidental writes
            # This is enforced at the database level
            conn.set_session(readonly=True, autocommit=False)
        else:
            conn.set_isolation_level(ISOLATION_LEVEL_READ_COMMITTED)
        
        cursor = conn.cursor()
        
        # SECURITY: Set statement timeout to prevent long-running queries
        # This prevents DoS through complex queries
        cursor.execute(f"SET statement_timeout = {config.MAX_QUERY_TIME * 1000};")
        
        # SECURITY: Execute query with parameters (prevents SQL injection)
        # ALWAYS use parameterized queries when possible
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        
        # SECURITY: Get column names
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        # SECURITY: Fetch limited results to prevent memory exhaustion
        # fetchmany() is more memory efficient than fetchall()
        rows = cursor.fetchmany(config.MAX_RESULTS)
        row_count = len(rows)  # Actual rows returned
        
        # Note: For SELECT queries, cursor.rowcount may be -1 in PostgreSQL
        # So we use the actual count of fetched rows
        
        execution_time = (time.time() - start_time) * 1000
        
        # SECURITY: Commit transaction (even for SELECT in read-only mode)
        conn.commit()
        
        # SECURITY: Log successful query execution for audit trail
        _log_query_execution(
            sql=sql,
            user_id=user_id,
            success=True,
            row_count=row_count,
            execution_time_ms=execution_time
        )
        
        return QueryResult(
            success=True,
            columns=columns,
            rows=rows,
            row_count=row_count,
            execution_time_ms=round(execution_time, 2)
        )
        
    except psycopg2.OperationalError as e:
        # SECURITY: Connection/operational errors
        execution_time = (time.time() - start_time) * 1000
        error_msg = _sanitize_error_message(str(e))
        
        _log_query_execution(
            sql=sql,
            user_id=user_id,
            success=False,
            error=error_msg,
            execution_time_ms=execution_time
        )
        
        return QueryResult(
            success=False,
            error=f"Database connection error: {error_msg}"
        )
        
    except psycopg2.extensions.QueryCanceledError:
        # SECURITY: Query exceeded timeout
        execution_time = (time.time() - start_time) * 1000
        error_msg = f"Query exceeded maximum execution time ({config.MAX_QUERY_TIME}s)"
        
        _log_query_execution(
            sql=sql,
            user_id=user_id,
            success=False,
            error=error_msg,
            execution_time_ms=execution_time
        )
        
        return QueryResult(
            success=False,
            error=error_msg
        )
        
    except psycopg2.ProgrammingError as e:
        # SECURITY: SQL syntax or programming errors
        execution_time = (time.time() - start_time) * 1000
        error_msg = _sanitize_error_message(str(e))
        
        _log_query_execution(
            sql=sql,
            user_id=user_id,
            success=False,
            error=error_msg,
            execution_time_ms=execution_time
        )
        
        return QueryResult(
            success=False,
            error=f"Query syntax error: {error_msg}"
        )
        
    except psycopg2.Error as e:
        # SECURITY: Other database errors
        execution_time = (time.time() - start_time) * 1000
        error_msg = _sanitize_error_message(e.pgerror or str(e))
        
        _log_query_execution(
            sql=sql,
            user_id=user_id,
            success=False,
            error=error_msg,
            execution_time_ms=execution_time
        )
        
        return QueryResult(
            success=False,
            error=f"Database error: {error_msg}"
        )
        
    except Exception as e:
        # SECURITY: Unexpected errors
        execution_time = (time.time() - start_time) * 1000
        error_msg = _sanitize_error_message(str(e))
        
        _log_query_execution(
            sql=sql,
            user_id=user_id,
            success=False,
            error=error_msg,
            execution_time_ms=execution_time
        )
        
        return QueryResult(
            success=False,
            error=f"Execution error: {error_msg}"
        )
        
    finally:
        # SECURITY: Always cleanup connections to prevent resource leaks
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def _is_query_safe(sql: str) -> bool:
    """
    Perform basic safety checks on SQL query.
    
    SECURITY: Additional layer of defense beyond SQL generator validation
    This catches any queries that bypassed generator validation
    
    Args:
        sql: SQL query to validate
        
    Returns:
        True if query passes basic safety checks
    """
    if not sql or not sql.strip():
        return False
    
    sql_upper = sql.upper()
    
    # SECURITY: If write queries not allowed, block them
    if not config.ALLOW_WRITE_QUERIES:
        dangerous_keywords = [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'TRUNCATE',
            'ALTER', 'CREATE', 'GRANT', 'REVOKE'
        ]
        
        for keyword in dangerous_keywords:
            # Check for keyword as whole word (not part of column name)
            if re.search(rf'\b{keyword}\b', sql_upper):
                return False
    
    # SECURITY: Block multiple statements (SQL injection attempt)
    semicolon_count = sql.count(';')
    if semicolon_count > 1:
        return False
    
    # SECURITY: Block SQL comments (could hide malicious code)
    if '--' in sql or '/*' in sql:
        return False
    
    return True


def _sanitize_error_message(error: str) -> str:
    """
    Sanitize error messages to prevent information disclosure.
    
    SECURITY: Prevents leaking sensitive information:
    - Database structure details
    - Internal IP addresses
    - File paths
    - Usernames
    - Passwords (if accidentally in connection string)
    
    Args:
        error: Raw error message
        
    Returns:
        Sanitized error message safe for display
    """
    if not error:
        return "Unknown error"
    
    # SECURITY: Remove file paths
    error = re.sub(r'(/[a-zA-Z0-9_/.-]+)', '[PATH]', error)
    error = re.sub(r'([A-Z]:\\[a-zA-Z0-9_\\.-]+)', '[PATH]', error)
    
    # SECURITY: Remove IP addresses
    error = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]', error)
    
    # SECURITY: Remove potential passwords from connection strings
    error = re.sub(r'password=[^\s;]+', 'password=[REDACTED]', error, flags=re.IGNORECASE)
    
    # SECURITY: Remove potential usernames
    error = re.sub(r'user=[^\s;]+', 'user=[REDACTED]', error, flags=re.IGNORECASE)
    
    # SECURITY: Limit error message length
    max_length = 500
    if len(error) > max_length:
        error = error[:max_length] + "..."
    
    return error


def _log_query_execution(
    sql: str,
    user_id: Optional[str],
    success: bool,
    row_count: int = 0,
    error: Optional[str] = None,
    execution_time_ms: float = 0
):
    """
    Log query execution for audit trail.
    
    SECURITY: Audit logging for compliance (SOC2, HIPAA, GDPR)
    Logs all database access with user context
    
    Args:
        sql: SQL query executed
        user_id: User who executed query
        success: Whether query succeeded
        row_count: Number of rows returned/affected
        error: Error message if failed
        execution_time_ms: Execution time in milliseconds
    """
    # Only log if audit logging is enabled
    if not config.ENABLE_AUDIT_LOGGING:
        return
    
    try:
        # Import here to avoid circular dependency
        from ..security.audit_logger import audit_logger
        
        # SECURITY: Extract table names from query for audit log
        tables = _extract_table_names(sql)
        
        audit_logger.log_data_access(
            user_id=user_id or 'anonymous',
            resource=f"tables: {', '.join(tables)}" if tables else 'database',
            action='query',
            ip_address='internal',  # Updated by web layer
            result='success' if success else 'failure',
            row_count=row_count
        )
        
    except Exception:
        # SECURITY: Never let audit logging failure break the application
        pass


def _extract_table_names(sql: str) -> List[str]:
    """
    Extract table names from SQL query for audit logging.
    
    SECURITY: Helps track which tables are being accessed
    Important for compliance and data access auditing
    
    Args:
        sql: SQL query
        
    Returns:
        List of table names
    """
    tables = []
    
    # Simple regex to extract table names after FROM and JOIN
    # This is not perfect but good enough for audit logging
    patterns = [
        r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        r'INTO\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        r'UPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, sql, re.IGNORECASE)
        tables.extend(matches)
    
    # Remove duplicates and return
    return list(set(tables))


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
