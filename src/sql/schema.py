"""
Schema introspection utilities.
Extracts database schema information to provide context to the LLM.
"""

import psycopg2
from typing import Dict, List, Any
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import config


def get_connection():
    """Get a database connection."""
    return psycopg2.connect(config.DATABASE_URL)


def get_table_names() -> List[str]:
    """Get all table names in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    
    return tables


def get_table_schema(table_name: str) -> List[Dict[str, Any]]:
    """Get column information for a table."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    
    columns = []
    for row in cursor.fetchall():
        columns.append({
            'name': row[0],
            'type': row[1],
            'nullable': row[2] == 'YES',
            'default': row[3],
            'max_length': row[4]
        })
    
    cursor.close()
    conn.close()
    
    return columns


def get_foreign_keys() -> List[Dict[str, str]]:
    """Get all foreign key relationships."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT
            tc.table_name AS from_table,
            kcu.column_name AS from_column,
            ccu.table_name AS to_table,
            ccu.column_name AS to_column
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
    """)
    
    relationships = []
    for row in cursor.fetchall():
        relationships.append({
            'from_table': row[0],
            'from_column': row[1],
            'to_table': row[2],
            'to_column': row[3]
        })
    
    cursor.close()
    conn.close()
    
    return relationships


def get_sample_values(table_name: str, column_name: str, limit: int = 5) -> List[Any]:
    """Get sample distinct values from a column (useful for enums/categories)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Safe query construction (table/column names validated elsewhere)
    cursor.execute(f"""
        SELECT DISTINCT {column_name} 
        FROM {table_name} 
        WHERE {column_name} IS NOT NULL 
        LIMIT %s
    """, (limit,))
    
    values = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    
    return values


def get_full_schema_description() -> str:
    """
    Generate a complete schema description for the LLM.
    This is what gets injected into the prompt.
    """
    lines = []
    lines.append("DATABASE SCHEMA")
    lines.append("=" * 50)
    
    tables = get_table_names()
    
    for table in tables:
        lines.append(f"\nTable: {table}")
        lines.append("-" * 40)
        
        columns = get_table_schema(table)
        for col in columns:
            type_str = col['type']
            if col['max_length']:
                type_str += f"({col['max_length']})"
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            lines.append(f"  {col['name']}: {type_str} {nullable}")
    
    # Add relationships
    relationships = get_foreign_keys()
    if relationships:
        lines.append("\n" + "=" * 50)
        lines.append("RELATIONSHIPS (Foreign Keys)")
        lines.append("-" * 40)
        for rel in relationships:
            lines.append(f"  {rel['from_table']}.{rel['from_column']} -> {rel['to_table']}.{rel['to_column']}")
    
    # Add some sample data hints
    lines.append("\n" + "=" * 50)
    lines.append("SAMPLE DATA HINTS")
    lines.append("-" * 40)
    
    # Order statuses
    try:
        statuses = get_sample_values('orders', 'status')
        lines.append(f"  orders.status values: {statuses}")
    except:
        pass
    
    # Warehouse codes
    try:
        warehouses = get_sample_values('warehouses', 'code')
        lines.append(f"  warehouses.code values: {warehouses}")
    except:
        pass
    
    # Category names
    try:
        categories = get_sample_values('categories', 'name')
        lines.append(f"  categories.name values: {categories}")
    except:
        pass
    
    return "\n".join(lines)


if __name__ == "__main__":
    # Test schema extraction
    print(get_full_schema_description())
