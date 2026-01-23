# SQL Query Optimization Guide

## Table of Contents
1. [Understanding Query Execution](#understanding-query-execution)
2. [Index Optimization](#index-optimization)
3. [Query Rewriting Techniques](#query-rewriting-techniques)
4. [Subquery Optimization](#subquery-optimization)
5. [Aggregation Optimization](#aggregation-optimization)
6. [Join Optimization](#join-optimization)
7. [Partitioning Strategies](#partitioning-strategies)
8. [Caching Strategies](#caching-strategies)

## Understanding Query Execution

### Reading Execution Plans

#### PostgreSQL EXPLAIN Output

```sql
EXPLAIN (ANALYZE, BUFFERS, VERBOSE) 
SELECT c.company_name, SUM(o.total_amount) as total
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_date >= '2025-01-01'
GROUP BY c.customer_id, c.company_name
HAVING SUM(o.total_amount) > 10000;
```

**Key Metrics to Watch:**
- **Seq Scan:** Sequential scan (consider adding index)
- **Index Scan:** Using index (good)
- **Index Only Scan:** Best - query satisfied entirely from index
- **Nested Loop:** Good for small datasets
- **Hash Join:** Good for large datasets
- **Merge Join:** Good for sorted data
- **Cost:** Estimated execution cost
- **Rows:** Estimated rows processed
- **Actual Time:** Real execution time

### Execution Order

SQL executes in this order (not written order):

```sql
-- Written order
SELECT c.company_name, COUNT(*) as order_count
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_date >= '2025-01-01'
GROUP BY c.customer_id, c.company_name
HAVING COUNT(*) > 5
ORDER BY order_count DESC
LIMIT 10;

-- Execution order:
-- 1. FROM - Load base tables
-- 2. JOIN - Combine tables
-- 3. WHERE - Filter rows
-- 4. GROUP BY - Group rows
-- 5. HAVING - Filter groups
-- 6. SELECT - Choose columns
-- 7. ORDER BY - Sort results
-- 8. LIMIT - Limit results
```

## Index Optimization

### Single vs Composite Indexes

```sql
-- Scenario: Frequent queries on status and date

-- Option 1: Two single-column indexes
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_date ON orders(order_date);

-- Option 2: One composite index (better for combined queries)
CREATE INDEX idx_orders_status_date ON orders(status, order_date);

-- This composite index supports:
SELECT * FROM orders WHERE status = 'pending';  -- Uses index
SELECT * FROM orders WHERE status = 'pending' AND order_date >= '2025-01-01';  -- Efficient
SELECT * FROM orders WHERE order_date >= '2025-01-01';  -- Less efficient
```

### Index Column Order

Put most selective column first:

```sql
-- Assume: 
-- - 5 distinct status values (low selectivity)
-- - 10,000 distinct dates (high selectivity)

-- Good: High selectivity first
CREATE INDEX idx_orders_date_status ON orders(order_date, status);

-- Less optimal: Low selectivity first
CREATE INDEX idx_orders_status_date ON orders(status, order_date);

-- Test selectivity:
SELECT 
    COUNT(DISTINCT status) as status_cardinality,
    COUNT(DISTINCT order_date) as date_cardinality,
    COUNT(*) as total_rows
FROM orders;
```

### Covering Indexes

Include frequently accessed columns:

```sql
-- Query that needs optimization
SELECT order_id, customer_id, order_date, total_amount
FROM orders
WHERE status = 'completed'
  AND order_date >= '2025-01-01';

-- Covering index includes all needed columns
CREATE INDEX idx_orders_covering ON orders(status, order_date) 
INCLUDE (order_id, customer_id, total_amount);

-- Result: Index-only scan (fastest)
```

### Partial Indexes

Index only relevant subset:

```sql
-- Most queries only care about active products
CREATE INDEX idx_products_active ON products(category_id, unit_price)
WHERE is_active = true;

-- Benefits:
-- - Smaller index size
-- - Faster updates
-- - Better cache utilization

-- Also useful for:
-- - Current year data only
-- - Non-null values only
-- - Specific status values
```

### Functional Indexes

Index computed values:

```sql
-- Queries often use LOWER() for case-insensitive search
CREATE INDEX idx_customers_email_lower 
ON customers(LOWER(email));

-- Now this query uses the index:
SELECT * FROM customers 
WHERE LOWER(email) = 'john@example.com';

-- Other functional index examples:
CREATE INDEX idx_orders_year ON orders(EXTRACT(YEAR FROM order_date));
CREATE INDEX idx_products_name_trgm ON products USING gin(product_name gin_trgm_ops);
```

## Query Rewriting Techniques

### EXISTS vs IN

```sql
-- Scenario: Find customers who have orders

-- Using IN (can be slow for large subqueries)
SELECT * FROM customers
WHERE customer_id IN (
    SELECT customer_id FROM orders WHERE order_date >= '2025-01-01'
);

-- Using EXISTS (often faster - stops after first match)
SELECT * FROM customers c
WHERE EXISTS (
    SELECT 1 FROM orders o 
    WHERE o.customer_id = c.customer_id 
      AND o.order_date >= '2025-01-01'
);

-- Using JOIN (best for returning related data)
SELECT DISTINCT c.*
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_date >= '2025-01-01';
```

### NOT EXISTS vs NOT IN

```sql
-- Find customers with no orders

-- Using NOT IN (NULL values cause issues!)
SELECT * FROM customers
WHERE customer_id NOT IN (
    SELECT customer_id FROM orders
    -- If any customer_id is NULL, query returns no rows!
);

-- Using NOT EXISTS (handles NULLs correctly)
SELECT * FROM customers c
WHERE NOT EXISTS (
    SELECT 1 FROM orders o 
    WHERE o.customer_id = c.customer_id
);

-- Using LEFT JOIN (also handles NULLs)
SELECT c.*
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL;
```

### UNION ALL vs UNION

```sql
-- UNION removes duplicates (slower)
SELECT product_name FROM products WHERE category_id = 1
UNION
SELECT product_name FROM products WHERE category_id = 2;

-- UNION ALL keeps duplicates (faster - no deduplication)
SELECT product_name FROM products WHERE category_id = 1
UNION ALL
SELECT product_name FROM products WHERE category_id = 2;

-- Use UNION ALL when:
-- - You know there are no duplicates
-- - Duplicates are acceptable
-- - Performance is critical
```

### Eliminate OR Conditions

```sql
-- Using OR (may prevent index usage)
SELECT * FROM orders
WHERE customer_id = 123 OR order_date >= '2025-01-01';

-- Rewrite as UNION ALL (can use different indexes)
SELECT * FROM orders WHERE customer_id = 123
UNION ALL
SELECT * FROM orders 
WHERE order_date >= '2025-01-01' 
  AND customer_id != 123;  -- Avoid duplicates
```

### Push Predicates Down

```sql
-- Bad: Filter after aggregation
SELECT * FROM (
    SELECT c.customer_id, c.company_name, SUM(o.total_amount) as total
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_id, c.company_name
) sub
WHERE total > 10000;

-- Good: Filter before aggregation
SELECT c.customer_id, c.company_name, SUM(o.total_amount) as total
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.company_name
HAVING SUM(o.total_amount) > 10000;
```

## Subquery Optimization

### Correlated vs Non-Correlated Subqueries

```sql
-- Correlated subquery (runs for each row - slow!)
SELECT c.company_name,
    (SELECT COUNT(*) FROM orders o WHERE o.customer_id = c.customer_id) as order_count
FROM customers c;

-- Non-correlated with JOIN (runs once - fast!)
SELECT c.company_name, COUNT(o.order_id) as order_count
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.company_name;
```

### Common Table Expressions (CTEs)

```sql
-- Using CTE for readability and reusability
WITH high_value_customers AS (
    SELECT customer_id, SUM(total_amount) as lifetime_value
    FROM orders
    GROUP BY customer_id
    HAVING SUM(total_amount) > 50000
),
recent_orders AS (
    SELECT customer_id, COUNT(*) as recent_count
    FROM orders
    WHERE order_date >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY customer_id
)
SELECT 
    c.company_name,
    h.lifetime_value,
    r.recent_count
FROM customers c
INNER JOIN high_value_customers h ON c.customer_id = h.customer_id
LEFT JOIN recent_orders r ON c.customer_id = r.customer_id
ORDER BY h.lifetime_value DESC;
```

### Materialized CTEs (PostgreSQL)

```sql
-- Force CTE to be materialized (computed once)
WITH recent_orders AS MATERIALIZED (
    SELECT customer_id, COUNT(*) as order_count, SUM(total_amount) as total
    FROM orders
    WHERE order_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY customer_id
)
SELECT c.company_name, ro.order_count, ro.total
FROM customers c
INNER JOIN recent_orders ro ON c.customer_id = ro.customer_id
WHERE ro.order_count > 10;
```

## Aggregation Optimization

### Filter Before Aggregate

```sql
-- Bad: Aggregate then filter
SELECT customer_id, COUNT(*) as order_count
FROM orders
GROUP BY customer_id
HAVING COUNT(*) > 10;

-- Better: Filter first, then aggregate (if possible)
SELECT customer_id, COUNT(*) as order_count
FROM orders
WHERE order_date >= '2024-01-01'  -- Filter first
GROUP BY customer_id
HAVING COUNT(*) > 10;
```

### Use Partial Aggregates

```sql
-- Instead of one large aggregate:
SELECT 
    category_id,
    SUM(units_in_stock * unit_price) as inventory_value
FROM products
GROUP BY category_id;

-- Pre-compute and store in summary table:
CREATE TABLE category_inventory_summary (
    category_id INTEGER PRIMARY KEY,
    inventory_value DECIMAL(15,2),
    last_updated TIMESTAMP
);

-- Update periodically or via trigger
CREATE OR REPLACE FUNCTION update_category_summary()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO category_inventory_summary (category_id, inventory_value, last_updated)
    SELECT 
        NEW.category_id,
        SUM(units_in_stock * unit_price),
        CURRENT_TIMESTAMP
    FROM products
    WHERE category_id = NEW.category_id
    GROUP BY category_id
    ON CONFLICT (category_id) DO UPDATE
    SET inventory_value = EXCLUDED.inventory_value,
        last_updated = EXCLUDED.last_updated;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### Window Functions vs Subqueries

```sql
-- Using subquery (less efficient)
SELECT 
    o.*,
    (SELECT SUM(total_amount) 
     FROM orders o2 
     WHERE o2.customer_id = o.customer_id) as customer_total
FROM orders o;

-- Using window function (more efficient)
SELECT 
    o.*,
    SUM(total_amount) OVER (PARTITION BY customer_id) as customer_total
FROM orders o;
```

### Optimize DISTINCT

```sql
-- DISTINCT on all columns (expensive)
SELECT DISTINCT customer_id, order_date, total_amount
FROM orders;

-- Better: Use GROUP BY if you need aggregates
SELECT customer_id, order_date, SUM(total_amount) as total
FROM orders
GROUP BY customer_id, order_date;

-- Best: Eliminate need for DISTINCT with proper joins
SELECT c.customer_id, c.company_name
FROM customers c
WHERE EXISTS (
    SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id
);
```

## Join Optimization

### Join Order Matters

```sql
-- Database chooses join order, but you can influence it

-- Start with most restrictive table
SELECT p.*
FROM orders o
INNER JOIN order_items oi ON o.order_id = oi.order_id
INNER JOIN products p ON oi.product_id = p.product_id
WHERE o.order_date >= CURRENT_DATE - INTERVAL '7 days'  -- Very restrictive
  AND p.category_id = 5;

-- Optimizer should start with orders (filtered by recent date)
-- Then join to order_items
-- Finally join to products
```

### JOIN vs Subquery

```sql
-- Subquery approach
SELECT *
FROM products
WHERE category_id IN (
    SELECT category_id 
    FROM categories 
    WHERE category_name = 'Electronics'
);

-- JOIN approach (often faster with indexes)
SELECT p.*
FROM products p
INNER JOIN categories c ON p.category_id = c.category_id
WHERE c.category_name = 'Electronics';
```

### Avoid Unnecessary JOINs

```sql
-- Bad: JOIN just to filter
SELECT p.*
FROM products p
INNER JOIN categories c ON p.category_id = c.category_id
WHERE c.category_name = 'Electronics';

-- Good: Use subquery if only filtering
SELECT *
FROM products
WHERE category_id = (
    SELECT category_id FROM categories WHERE category_name = 'Electronics'
);
```

### JOIN with Derived Tables

```sql
-- Aggregate before joining (reduce rows early)
SELECT 
    c.company_name,
    customer_stats.order_count,
    customer_stats.total_amount
FROM customers c
INNER JOIN (
    SELECT 
        customer_id,
        COUNT(*) as order_count,
        SUM(total_amount) as total_amount
    FROM orders
    WHERE order_date >= '2025-01-01'
    GROUP BY customer_id
) customer_stats ON c.customer_id = customer_stats.customer_id
WHERE customer_stats.order_count > 5;
```

## Partitioning Strategies

### Range Partitioning

```sql
-- Partition orders table by year
CREATE TABLE orders (
    order_id SERIAL,
    customer_id INTEGER,
    order_date DATE NOT NULL,
    total_amount DECIMAL(10,2)
) PARTITION BY RANGE (order_date);

-- Create partitions
CREATE TABLE orders_2023 PARTITION OF orders
    FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');

CREATE TABLE orders_2024 PARTITION OF orders
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE orders_2025 PARTITION OF orders
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

-- Queries automatically use appropriate partition
SELECT * FROM orders 
WHERE order_date >= '2025-01-01' AND order_date < '2025-02-01';
-- Only scans orders_2025 partition
```

### List Partitioning

```sql
-- Partition by discrete values
CREATE TABLE customers (
    customer_id SERIAL,
    company_name VARCHAR(100),
    country VARCHAR(50) NOT NULL
) PARTITION BY LIST (country);

CREATE TABLE customers_usa PARTITION OF customers
    FOR VALUES IN ('USA', 'United States');

CREATE TABLE customers_canada PARTITION OF customers
    FOR VALUES IN ('Canada');

CREATE TABLE customers_other PARTITION OF customers
    DEFAULT;
```

### Hash Partitioning

```sql
-- Distribute data evenly across partitions
CREATE TABLE events (
    event_id BIGSERIAL,
    user_id INTEGER,
    event_type VARCHAR(50),
    event_data JSONB,
    created_at TIMESTAMP
) PARTITION BY HASH (user_id);

-- Create 4 partitions
CREATE TABLE events_p0 PARTITION OF events
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);

CREATE TABLE events_p1 PARTITION OF events
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);

CREATE TABLE events_p2 PARTITION OF events
    FOR VALUES WITH (MODULUS 4, REMAINDER 2);

CREATE TABLE events_p3 PARTITION OF events
    FOR VALUES WITH (MODULUS 4, REMAINDER 3);
```

## Caching Strategies

### Materialized Views

```sql
-- Create materialized view for expensive query
CREATE MATERIALIZED VIEW customer_summary AS
SELECT 
    c.customer_id,
    c.company_name,
    COUNT(o.order_id) as total_orders,
    SUM(o.total_amount) as lifetime_value,
    MAX(o.order_date) as last_order_date,
    AVG(o.total_amount) as avg_order_value
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.company_name;

-- Create index on materialized view
CREATE INDEX idx_customer_summary_lifetime 
ON customer_summary(lifetime_value DESC);

-- Refresh materialized view (periodically)
REFRESH MATERIALIZED VIEW customer_summary;

-- Refresh concurrently (allows reads during refresh)
REFRESH MATERIALIZED VIEW CONCURRENTLY customer_summary;
```

### Query Result Caching

```sql
-- Application-level caching strategy

-- 1. Check cache
-- 2. If miss, execute query:
SELECT * FROM products WHERE category_id = 5 ORDER BY unit_price DESC LIMIT 20;

-- 3. Store result in cache (Redis, Memcached) with TTL
-- 4. Subsequent requests served from cache
-- 5. Invalidate cache on data changes
```

### Temporary Tables for Complex Queries

```sql
-- Store intermediate results in temp table
CREATE TEMPORARY TABLE temp_high_value_customers AS
SELECT customer_id, SUM(total_amount) as lifetime_value
FROM orders
GROUP BY customer_id
HAVING SUM(total_amount) > 50000;

CREATE INDEX idx_temp_customers ON temp_high_value_customers(customer_id);

-- Use temp table in subsequent queries
SELECT c.*, t.lifetime_value
FROM customers c
INNER JOIN temp_high_value_customers t ON c.customer_id = t.customer_id;

-- Temp table automatically dropped at end of session
```

## Performance Monitoring

### Find Slow Queries

```sql
-- PostgreSQL: View slowest queries
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time,
    rows
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;
```

### Find Missing Indexes

```sql
-- Tables with sequential scans that might need indexes
SELECT 
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    seq_tup_read / seq_scan as avg_seq_read,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size
FROM pg_stat_user_tables
WHERE seq_scan > 0
ORDER BY seq_tup_read DESC
LIMIT 20;
```

### Index Health Check

```sql
-- Find bloated indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan < 50  -- Rarely used
  AND pg_relation_size(indexrelid) > 1000000  -- Larger than 1MB
ORDER BY pg_relation_size(indexrelid) DESC;
```

## Quick Optimization Checklist

Query Structure:
- [ ] SELECT only needed columns
- [ ] Use WHERE to filter early
- [ ] Avoid functions on indexed columns
- [ ] Use EXISTS instead of COUNT for existence checks
- [ ] Use UNION ALL instead of UNION when appropriate

Indexes:
- [ ] Index columns in WHERE, JOIN, ORDER BY
- [ ] Create composite indexes for multi-column queries
- [ ] Consider covering indexes for frequently run queries
- [ ] Use partial indexes for subset queries
- [ ] Remove unused indexes

Joins:
- [ ] Use appropriate join type
- [ ] Ensure join columns are indexed
- [ ] Start with most restrictive table
- [ ] Avoid unnecessary joins

Aggregations:
- [ ] Filter before aggregating
- [ ] Use window functions instead of subqueries
- [ ] Consider materialized views for complex aggregates
- [ ] Pre-aggregate when possible

Advanced:
- [ ] Use partitioning for very large tables
- [ ] Implement caching for read-heavy workloads
- [ ] Monitor slow queries regularly
- [ ] Analyze execution plans
- [ ] Update statistics regularly
