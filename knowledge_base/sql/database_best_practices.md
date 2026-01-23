# SQL Database Best Practices

## Table of Contents
1. [Query Optimization](#query-optimization)
2. [Indexing Strategies](#indexing-strategies)
3. [JOIN Operations](#join-operations)
4. [Transaction Management](#transaction-management)
5. [Security Practices](#security-practices)
6. [Data Integrity](#data-integrity)
7. [Performance Monitoring](#performance-monitoring)

## Query Optimization

### Select Only Required Columns

Always specify exact columns instead of using SELECT *:

```sql
-- Bad: Retrieves unnecessary data
SELECT * FROM products WHERE category_id = 5;

-- Good: Only retrieve what you need
SELECT product_id, product_name, unit_price 
FROM products 
WHERE category_id = 5;
```

**Benefits:**
- Reduces network traffic
- Minimizes memory usage
- Improves query performance
- Makes intentions clearer

### Use LIMIT/TOP for Large Result Sets

Always limit results when you don't need all rows:

```sql
-- PostgreSQL/MySQL
SELECT product_name, unit_price 
FROM products 
WHERE category_id = 5
ORDER BY unit_price DESC
LIMIT 100;

-- SQL Server
SELECT TOP 100 product_name, unit_price 
FROM products 
WHERE category_id = 5
ORDER BY unit_price DESC;
```

### Avoid Functions on Indexed Columns in WHERE Clause

Functions on indexed columns prevent index usage:

```sql
-- Bad: Function prevents index usage
SELECT * FROM orders 
WHERE YEAR(order_date) = 2025;

-- Good: Index can be used
SELECT * FROM orders 
WHERE order_date >= '2025-01-01' 
  AND order_date < '2026-01-01';
```

### Use EXISTS Instead of COUNT for Existence Checks

When checking if records exist:

```sql
-- Bad: Counts all matching rows
SELECT CASE WHEN COUNT(*) > 0 THEN 'Y' ELSE 'N' END
FROM orders WHERE customer_id = 123;

-- Good: Stops after finding first match
SELECT CASE WHEN EXISTS (
    SELECT 1 FROM orders WHERE customer_id = 123
) THEN 'Y' ELSE 'N' END;
```

### Optimize LIKE Queries

```sql
-- Bad: Leading wildcard prevents index usage
SELECT * FROM customers 
WHERE company_name LIKE '%construction%';

-- Better: Trailing wildcard can use index
SELECT * FROM customers 
WHERE company_name LIKE 'construction%';

-- Best: Full-text search for complex text searches
SELECT * FROM customers 
WHERE to_tsvector('english', company_name) @@ to_tsquery('construction');
```

## Indexing Strategies

### Single Column Indexes

Create indexes on columns used in WHERE, JOIN, and ORDER BY:

```sql
-- Index for frequent WHERE clause
CREATE INDEX idx_products_category 
ON products(category_id);

-- Index for sorting
CREATE INDEX idx_orders_date 
ON orders(order_date DESC);

-- Index for foreign key (improves JOIN performance)
CREATE INDEX idx_order_items_product 
ON order_items(product_id);
```

### Composite Indexes

Order matters - most selective column first:

```sql
-- Good: Supports queries filtering by status and date
CREATE INDEX idx_orders_status_date 
ON orders(status, order_date);

-- Supports queries like:
-- WHERE status = 'pending'
-- WHERE status = 'pending' AND order_date >= '2025-01-01'

-- Does NOT efficiently support:
-- WHERE order_date >= '2025-01-01' (only uses first column)
```

### Covering Indexes

Include frequently accessed columns:

```sql
-- Covering index includes all columns needed by query
CREATE INDEX idx_products_cover 
ON products(category_id) 
INCLUDE (product_name, unit_price);

-- Query can be satisfied entirely from index (index-only scan)
SELECT product_name, unit_price 
FROM products 
WHERE category_id = 5;
```

### Partial Indexes

Index only relevant subset of data:

```sql
-- Index only active products
CREATE INDEX idx_products_active 
ON products(category_id) 
WHERE is_active = true;

-- Smaller index, faster queries for active products
SELECT * FROM products 
WHERE category_id = 5 AND is_active = true;
```

### Index Maintenance

```sql
-- Check index usage (PostgreSQL)
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY idx_tup_read DESC;

-- Rebuild fragmented indexes
REINDEX INDEX idx_orders_date;

-- Update statistics
ANALYZE products;
```

## JOIN Operations

### Inner Join

Returns only matching rows from both tables:

```sql
SELECT 
    o.order_id,
    o.order_date,
    c.company_name,
    c.contact_name
FROM orders o
INNER JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_date >= CURRENT_DATE - INTERVAL '30 days';
```

### Left Outer Join

Returns all rows from left table, matching rows from right:

```sql
-- Get all customers and their order count (including customers with no orders)
SELECT 
    c.customer_id,
    c.company_name,
    COUNT(o.order_id) as order_count,
    COALESCE(SUM(o.total_amount), 0) as total_spent
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.company_name
ORDER BY total_spent DESC;
```

### Multiple Joins

Proper table order and join conditions:

```sql
SELECT 
    o.order_id,
    o.order_date,
    c.company_name,
    p.product_name,
    oi.quantity,
    oi.unit_price,
    (oi.quantity * oi.unit_price) as line_total
FROM orders o
INNER JOIN customers c ON o.customer_id = c.customer_id
INNER JOIN order_items oi ON o.order_id = oi.order_id
INNER JOIN products p ON oi.product_id = p.product_id
WHERE o.order_date >= '2025-01-01'
  AND c.country = 'USA'
ORDER BY o.order_date DESC, o.order_id, oi.line_number;
```

### Cross Join (Cartesian Product)

Use sparingly - generates all combinations:

```sql
-- Generate all possible product-warehouse combinations
SELECT 
    p.product_name,
    w.warehouse_name
FROM products p
CROSS JOIN warehouses w;

-- Better: Use with WHERE to filter
SELECT 
    p.product_name,
    w.warehouse_name,
    i.quantity_on_hand
FROM products p
CROSS JOIN warehouses w
LEFT JOIN inventory i 
    ON p.product_id = i.product_id 
    AND w.warehouse_id = i.warehouse_id;
```

### Self Join

Join table to itself:

```sql
-- Find employees and their managers
SELECT 
    e.employee_id,
    e.first_name || ' ' || e.last_name as employee,
    m.first_name || ' ' || m.last_name as manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.employee_id
ORDER BY e.employee_id;
```

## Transaction Management

### Basic Transaction

```sql
BEGIN TRANSACTION;

-- Multiple related operations
UPDATE accounts SET balance = balance - 100 WHERE account_id = 1;
UPDATE accounts SET balance = balance + 100 WHERE account_id = 2;
INSERT INTO transactions (from_account, to_account, amount, trans_date)
VALUES (1, 2, 100, CURRENT_TIMESTAMP);

-- Commit if all succeed
COMMIT;

-- Or rollback if error
ROLLBACK;
```

### Transaction Isolation Levels

```sql
-- Read Uncommitted (lowest isolation, highest concurrency)
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

-- Read Committed (default in PostgreSQL)
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- Repeatable Read (prevents non-repeatable reads)
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

-- Serializable (highest isolation, lowest concurrency)
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
```

### Savepoints

```sql
BEGIN TRANSACTION;

INSERT INTO orders (customer_id, order_date) 
VALUES (123, CURRENT_DATE);

SAVEPOINT order_created;

INSERT INTO order_items (order_id, product_id, quantity)
VALUES (1001, 5, 10);

-- If error occurs, rollback to savepoint
ROLLBACK TO SAVEPOINT order_created;

-- Or continue
COMMIT;
```

### Deadlock Prevention

```sql
-- Always access tables in same order across transactions
-- Transaction 1:
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE account_id = 1;
UPDATE accounts SET balance = balance + 100 WHERE account_id = 2;
COMMIT;

-- Transaction 2: Same order prevents deadlock
BEGIN;
UPDATE accounts SET balance = balance - 50 WHERE account_id = 1;
UPDATE accounts SET balance = balance + 50 WHERE account_id = 2;
COMMIT;
```

## Security Practices

### SQL Injection Prevention

Always use parameterized queries:

```sql
-- Bad: Direct string concatenation (vulnerable to SQL injection)
-- query = "SELECT * FROM users WHERE username = '" + input + "';"

-- Good: Parameterized query (safe)
-- Prepared statement with parameter binding
PREPARE get_user AS
SELECT user_id, username, email 
FROM users 
WHERE username = $1;

EXECUTE get_user('john_doe');
```

### Principle of Least Privilege

Grant minimum necessary permissions:

```sql
-- Create read-only user for reporting
CREATE USER report_user WITH PASSWORD 'secure_password';

-- Grant only SELECT on specific tables
GRANT SELECT ON customers, orders, products TO report_user;

-- Revoke write permissions
REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM report_user;
```

### Sensitive Data Protection

```sql
-- Use views to hide sensitive columns
CREATE VIEW customer_public AS
SELECT 
    customer_id,
    company_name,
    contact_name,
    city,
    country
    -- Excludes: credit_card, ssn, etc.
FROM customers;

GRANT SELECT ON customer_public TO app_user;
REVOKE SELECT ON customers FROM app_user;
```

### Audit Logging

```sql
-- Create audit log table
CREATE TABLE audit_log (
    log_id SERIAL PRIMARY KEY,
    table_name VARCHAR(50),
    operation VARCHAR(10),
    old_data JSONB,
    new_data JSONB,
    changed_by VARCHAR(50),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create trigger for audit logging
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (table_name, operation, old_data, new_data, changed_by)
    VALUES (
        TG_TABLE_NAME,
        TG_OP,
        row_to_json(OLD),
        row_to_json(NEW),
        current_user
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to sensitive tables
CREATE TRIGGER customers_audit
AFTER INSERT OR UPDATE OR DELETE ON customers
FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
```

## Data Integrity

### Primary Keys

```sql
-- Single column primary key
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL
);

-- Composite primary key
CREATE TABLE order_items (
    order_id INTEGER,
    line_number INTEGER,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    PRIMARY KEY (order_id, line_number)
);
```

### Foreign Keys

```sql
-- Foreign key with referential integrity
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    CONSTRAINT fk_customer
        FOREIGN KEY (customer_id) 
        REFERENCES customers(customer_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);
```

### Check Constraints

```sql
-- Ensure data validity
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    units_in_stock INTEGER NOT NULL DEFAULT 0,
    reorder_level INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT chk_price_positive 
        CHECK (unit_price >= 0),
    CONSTRAINT chk_stock_nonnegative 
        CHECK (units_in_stock >= 0),
    CONSTRAINT chk_reorder_valid 
        CHECK (reorder_level >= 0)
);
```

### Unique Constraints

```sql
-- Ensure uniqueness
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    tax_id VARCHAR(20),
    CONSTRAINT uk_email UNIQUE (email),
    CONSTRAINT uk_tax_id UNIQUE (tax_id)
);
```

### Not Null Constraints

```sql
-- Prevent null values where inappropriate
CREATE TABLE employees (
    employee_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    hire_date DATE NOT NULL,
    manager_id INTEGER,  -- Can be null for CEO
    CONSTRAINT uk_email UNIQUE (email)
);
```

## Performance Monitoring

### Query Execution Plans

```sql
-- PostgreSQL: View execution plan
EXPLAIN ANALYZE
SELECT c.company_name, COUNT(o.order_id) as order_count
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.company_name
HAVING COUNT(o.order_id) > 10;

-- Look for:
-- - Sequential Scans (consider adding index)
-- - High cost operations
-- - Excessive rows processed
```

### Slow Query Log

```sql
-- PostgreSQL: Enable slow query logging
ALTER SYSTEM SET log_min_duration_statement = 1000; -- Log queries > 1 second
SELECT pg_reload_conf();

-- View slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Index Usage Statistics

```sql
-- Check which indexes are being used
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Find unused indexes (candidates for removal)
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexrelname NOT LIKE '%_pkey'
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Table Statistics

```sql
-- View table sizes and row counts
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - 
                   pg_relation_size(schemaname||'.'||tablename)) as index_size,
    n_live_tup as row_count,
    n_dead_tup as dead_rows
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Connection Monitoring

```sql
-- View current connections
SELECT 
    datname,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    state_change,
    query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY query_start;

-- Kill long-running query
SELECT pg_cancel_backend(pid);  -- Try to cancel gracefully
SELECT pg_terminate_backend(pid);  -- Force terminate
```

## Common Anti-Patterns to Avoid

### 1. EAV (Entity-Attribute-Value) Pattern

```sql
-- Bad: Generic key-value storage
CREATE TABLE entity_attributes (
    entity_id INTEGER,
    attribute_name VARCHAR(50),
    attribute_value TEXT
);

-- Good: Proper columns
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    product_name VARCHAR(100),
    unit_price DECIMAL(10,2),
    category_id INTEGER
);
```

### 2. Storing Arrays/Lists as Delimited Strings

```sql
-- Bad: Comma-separated values
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    product_ids VARCHAR(255)  -- '1,3,5,7'
);

-- Good: Proper relationship table
CREATE TABLE order_items (
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    PRIMARY KEY (order_id, product_id)
);
```

### 3. Using FLOAT for Money

```sql
-- Bad: Floating point for currency
CREATE TABLE products (
    price FLOAT  -- Precision errors!
);

-- Good: Use DECIMAL/NUMERIC
CREATE TABLE products (
    price DECIMAL(10,2)  -- Exact precision
);
```

### 4. Not Using Transactions for Related Operations

```sql
-- Bad: No transaction
UPDATE accounts SET balance = balance - 100 WHERE account_id = 1;
UPDATE accounts SET balance = balance + 100 WHERE account_id = 2;
-- If second update fails, money is lost!

-- Good: Use transaction
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE account_id = 1;
UPDATE accounts SET balance = balance + 100 WHERE account_id = 2;
COMMIT;
```

## Summary Checklist

Performance:
- [ ] Use indexes on frequently queried columns
- [ ] Select only needed columns
- [ ] Use LIMIT for large result sets
- [ ] Avoid functions on indexed columns in WHERE
- [ ] Use EXPLAIN to analyze query plans

Security:
- [ ] Always use parameterized queries
- [ ] Apply principle of least privilege
- [ ] Protect sensitive data
- [ ] Implement audit logging
- [ ] Regular security reviews

Data Integrity:
- [ ] Define primary keys on all tables
- [ ] Use foreign keys for referential integrity
- [ ] Add check constraints for data validation
- [ ] Use NOT NULL where appropriate
- [ ] Implement unique constraints

Monitoring:
- [ ] Enable slow query logging
- [ ] Monitor index usage
- [ ] Track table bloat
- [ ] Review execution plans
- [ ] Monitor connections and locks
