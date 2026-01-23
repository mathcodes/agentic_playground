# SQL Common Patterns

## Table of Contents
1. [Data Retrieval Patterns](#data-retrieval-patterns)
2. [Data Manipulation Patterns](#data-manipulation-patterns)
3. [Analytical Queries](#analytical-queries)
4. [Date and Time Patterns](#date-and-time-patterns)
5. [Text Search Patterns](#text-search-patterns)
6. [Hierarchical Data](#hierarchical-data)
7. [Pivot and Unpivot](#pivot-and-unpivot)
8. [Data Quality Checks](#data-quality-checks)

## Data Retrieval Patterns

### Top N Records

```sql
-- Get top 10 most expensive products
SELECT product_name, unit_price
FROM products
ORDER BY unit_price DESC
LIMIT 10;

-- Get top 5 customers by order count
SELECT 
    c.customer_id,
    c.company_name,
    COUNT(o.order_id) as order_count
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.company_name
ORDER BY order_count DESC
LIMIT 5;
```

### Top N Per Group

```sql
-- Top 3 products by sales in each category
WITH ranked_products AS (
    SELECT 
        p.category_id,
        p.product_name,
        SUM(oi.quantity * oi.unit_price) as total_sales,
        ROW_NUMBER() OVER (
            PARTITION BY p.category_id 
            ORDER BY SUM(oi.quantity * oi.unit_price) DESC
        ) as rank
    FROM products p
    INNER JOIN order_items oi ON p.product_id = oi.product_id
    GROUP BY p.category_id, p.product_id, p.product_name
)
SELECT category_id, product_name, total_sales, rank
FROM ranked_products
WHERE rank <= 3
ORDER BY category_id, rank;
```

### Pagination

```sql
-- Page 1 (records 1-20)
SELECT product_id, product_name, unit_price
FROM products
ORDER BY product_id
LIMIT 20 OFFSET 0;

-- Page 2 (records 21-40)
SELECT product_id, product_name, unit_price
FROM products
ORDER BY product_id
LIMIT 20 OFFSET 20;

-- More efficient for large offsets: Keyset pagination
SELECT product_id, product_name, unit_price
FROM products
WHERE product_id > 20  -- Last ID from previous page
ORDER BY product_id
LIMIT 20;
```

### Random Sampling

```sql
-- Get 100 random records
SELECT * FROM customers
ORDER BY RANDOM()
LIMIT 100;

-- More efficient for large tables: Use TABLESAMPLE
SELECT * FROM customers
TABLESAMPLE BERNOULLI (10);  -- 10% sample
```

### Duplicate Detection

```sql
-- Find duplicate email addresses
SELECT email, COUNT(*) as count
FROM customers
GROUP BY email
HAVING COUNT(*) > 1;

-- Find all records with duplicate emails
SELECT c1.*
FROM customers c1
INNER JOIN (
    SELECT email
    FROM customers
    GROUP BY email
    HAVING COUNT(*) > 1
) c2 ON c1.email = c2.email
ORDER BY c1.email, c1.customer_id;
```

### Gap Detection

```sql
-- Find missing order numbers
SELECT missing_id
FROM generate_series(
    (SELECT MIN(order_id) FROM orders),
    (SELECT MAX(order_id) FROM orders)
) missing_id
WHERE NOT EXISTS (
    SELECT 1 FROM orders WHERE order_id = missing_id
);
```

## Data Manipulation Patterns

### Upsert (Insert or Update)

```sql
-- PostgreSQL: INSERT ... ON CONFLICT
INSERT INTO products (product_id, product_name, unit_price, units_in_stock)
VALUES (1, 'Widget', 29.99, 100)
ON CONFLICT (product_id) DO UPDATE
SET 
    product_name = EXCLUDED.product_name,
    unit_price = EXCLUDED.unit_price,
    units_in_stock = EXCLUDED.units_in_stock,
    updated_at = CURRENT_TIMESTAMP;
```

### Bulk Insert from Select

```sql
-- Copy data from one table to another
INSERT INTO archived_orders (order_id, customer_id, order_date, total_amount)
SELECT order_id, customer_id, order_date, total_amount
FROM orders
WHERE order_date < '2020-01-01';
```

### Conditional Updates

```sql
-- Update with CASE statement
UPDATE products
SET discount_percentage = 
    CASE 
        WHEN units_in_stock > 100 THEN 15
        WHEN units_in_stock > 50 THEN 10
        WHEN units_in_stock > 20 THEN 5
        ELSE 0
    END
WHERE category_id = 5;
```

### Delete with Join

```sql
-- Delete orders for inactive customers
DELETE FROM orders
WHERE customer_id IN (
    SELECT customer_id 
    FROM customers 
    WHERE is_active = false
);

-- Alternative using EXISTS
DELETE FROM orders o
WHERE EXISTS (
    SELECT 1 
    FROM customers c 
    WHERE c.customer_id = o.customer_id 
      AND c.is_active = false
);
```

### Soft Delete Pattern

```sql
-- Instead of DELETE, mark as deleted
UPDATE orders
SET 
    is_deleted = true,
    deleted_at = CURRENT_TIMESTAMP,
    deleted_by = 'admin_user'
WHERE order_id = 12345;

-- Query active records only
SELECT * FROM orders 
WHERE is_deleted = false OR is_deleted IS NULL;

-- Create partial index for active records
CREATE INDEX idx_orders_active 
ON orders(order_date) 
WHERE is_deleted = false OR is_deleted IS NULL;
```

## Analytical Queries

### Running Total

```sql
-- Calculate running total of sales
SELECT 
    order_date,
    daily_total,
    SUM(daily_total) OVER (ORDER BY order_date) as running_total
FROM (
    SELECT 
        order_date,
        SUM(total_amount) as daily_total
    FROM orders
    GROUP BY order_date
) daily_sales
ORDER BY order_date;
```

### Moving Average

```sql
-- 7-day moving average of sales
SELECT 
    order_date,
    daily_total,
    AVG(daily_total) OVER (
        ORDER BY order_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as moving_avg_7day
FROM (
    SELECT 
        order_date,
        SUM(total_amount) as daily_total
    FROM orders
    GROUP BY order_date
) daily_sales
ORDER BY order_date;
```

### Percent of Total

```sql
-- Calculate each product's percentage of category sales
SELECT 
    p.category_id,
    p.product_name,
    SUM(oi.quantity * oi.unit_price) as product_sales,
    ROUND(
        100.0 * SUM(oi.quantity * oi.unit_price) / 
        SUM(SUM(oi.quantity * oi.unit_price)) OVER (PARTITION BY p.category_id),
        2
    ) as percent_of_category
FROM products p
INNER JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.category_id, p.product_id, p.product_name
ORDER BY p.category_id, product_sales DESC;
```

### Year-Over-Year Comparison

```sql
-- Compare sales year-over-year
WITH yearly_sales AS (
    SELECT 
        EXTRACT(YEAR FROM order_date) as year,
        EXTRACT(MONTH FROM order_date) as month,
        SUM(total_amount) as monthly_total
    FROM orders
    GROUP BY 
        EXTRACT(YEAR FROM order_date),
        EXTRACT(MONTH FROM order_date)
)
SELECT 
    current_year.year,
    current_year.month,
    current_year.monthly_total as current_year_sales,
    prior_year.monthly_total as prior_year_sales,
    current_year.monthly_total - prior_year.monthly_total as difference,
    ROUND(
        100.0 * (current_year.monthly_total - prior_year.monthly_total) / 
        NULLIF(prior_year.monthly_total, 0),
        2
    ) as percent_change
FROM yearly_sales current_year
LEFT JOIN yearly_sales prior_year 
    ON current_year.month = prior_year.month 
    AND current_year.year = prior_year.year + 1
ORDER BY current_year.year, current_year.month;
```

### Cohort Analysis

```sql
-- Customer retention cohort analysis
WITH first_purchase AS (
    SELECT 
        customer_id,
        DATE_TRUNC('month', MIN(order_date)) as cohort_month
    FROM orders
    GROUP BY customer_id
),
monthly_activity AS (
    SELECT 
        fp.cohort_month,
        DATE_TRUNC('month', o.order_date) as activity_month,
        COUNT(DISTINCT o.customer_id) as active_customers
    FROM first_purchase fp
    INNER JOIN orders o ON fp.customer_id = o.customer_id
    GROUP BY fp.cohort_month, DATE_TRUNC('month', o.order_date)
)
SELECT 
    cohort_month,
    activity_month,
    active_customers,
    EXTRACT(MONTH FROM AGE(activity_month, cohort_month)) as months_since_cohort,
    ROUND(
        100.0 * active_customers / 
        FIRST_VALUE(active_customers) OVER (
            PARTITION BY cohort_month 
            ORDER BY activity_month
        ),
        2
    ) as retention_rate
FROM monthly_activity
ORDER BY cohort_month, activity_month;
```

### Quartile Analysis

```sql
-- Divide customers into quartiles by spending
WITH customer_spending AS (
    SELECT 
        customer_id,
        SUM(total_amount) as total_spent
    FROM orders
    GROUP BY customer_id
)
SELECT 
    customer_id,
    total_spent,
    NTILE(4) OVER (ORDER BY total_spent) as quartile,
    CASE NTILE(4) OVER (ORDER BY total_spent)
        WHEN 4 THEN 'High Value'
        WHEN 3 THEN 'Medium-High Value'
        WHEN 2 THEN 'Medium-Low Value'
        WHEN 1 THEN 'Low Value'
    END as customer_segment
FROM customer_spending
ORDER BY total_spent DESC;
```

## Date and Time Patterns

### Date Range Queries

```sql
-- Last 30 days
SELECT * FROM orders
WHERE order_date >= CURRENT_DATE - INTERVAL '30 days';

-- Current month
SELECT * FROM orders
WHERE order_date >= DATE_TRUNC('month', CURRENT_DATE)
  AND order_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month';

-- Last complete month
SELECT * FROM orders
WHERE order_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
  AND order_date < DATE_TRUNC('month', CURRENT_DATE);

-- Year to date
SELECT * FROM orders
WHERE order_date >= DATE_TRUNC('year', CURRENT_DATE);

-- Last 12 months
SELECT * FROM orders
WHERE order_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '11 months');
```

### Date Grouping

```sql
-- Group by day
SELECT 
    DATE_TRUNC('day', order_date) as day,
    COUNT(*) as order_count,
    SUM(total_amount) as daily_total
FROM orders
GROUP BY DATE_TRUNC('day', order_date)
ORDER BY day;

-- Group by week
SELECT 
    DATE_TRUNC('week', order_date) as week_start,
    COUNT(*) as order_count,
    SUM(total_amount) as weekly_total
FROM orders
GROUP BY DATE_TRUNC('week', order_date)
ORDER BY week_start;

-- Group by month
SELECT 
    DATE_TRUNC('month', order_date) as month,
    COUNT(*) as order_count,
    SUM(total_amount) as monthly_total
FROM orders
GROUP BY DATE_TRUNC('month', order_date)
ORDER BY month;
```

### Business Days Calculation

```sql
-- Calculate business days between dates (excluding weekends)
CREATE OR REPLACE FUNCTION business_days_between(start_date DATE, end_date DATE)
RETURNS INTEGER AS $$
DECLARE
    total_days INTEGER;
    weekend_days INTEGER;
BEGIN
    total_days := end_date - start_date;
    
    -- Count Saturdays and Sundays
    weekend_days := (
        SELECT COUNT(*)
        FROM generate_series(start_date, end_date, '1 day'::interval) as d
        WHERE EXTRACT(DOW FROM d) IN (0, 6)
    );
    
    RETURN total_days - weekend_days;
END;
$$ LANGUAGE plpgsql;

-- Usage
SELECT 
    order_id,
    order_date,
    ship_date,
    business_days_between(order_date, ship_date) as days_to_ship
FROM orders;
```

### Generate Date Series

```sql
-- Generate complete date series (including missing dates)
SELECT 
    d.date,
    COALESCE(o.order_count, 0) as order_count,
    COALESCE(o.daily_total, 0) as daily_total
FROM generate_series(
    '2025-01-01'::date,
    '2025-12-31'::date,
    '1 day'::interval
) d(date)
LEFT JOIN (
    SELECT 
        order_date,
        COUNT(*) as order_count,
        SUM(total_amount) as daily_total
    FROM orders
    GROUP BY order_date
) o ON d.date = o.order_date
ORDER BY d.date;
```

## Text Search Patterns

### Basic Pattern Matching

```sql
-- Starts with
SELECT * FROM customers
WHERE company_name LIKE 'ABC%';

-- Ends with
SELECT * FROM customers
WHERE company_name LIKE '%Corp';

-- Contains
SELECT * FROM customers
WHERE company_name LIKE '%construction%';

-- Case-insensitive (PostgreSQL)
SELECT * FROM customers
WHERE company_name ILIKE '%construction%';
```

### Multiple Pattern Matching

```sql
-- Match any of multiple patterns
SELECT * FROM products
WHERE product_name ~* 'widget|gadget|device';

-- Match all keywords (PostgreSQL)
SELECT * FROM products
WHERE product_name ILIKE '%premium%'
  AND product_name ILIKE '%steel%';
```

### Full-Text Search

```sql
-- Create full-text search index
CREATE INDEX idx_products_fts 
ON products 
USING gin(to_tsvector('english', product_name || ' ' || description));

-- Search using full-text
SELECT 
    product_id,
    product_name,
    ts_rank(
        to_tsvector('english', product_name || ' ' || description),
        to_tsquery('english', 'premium & steel')
    ) as rank
FROM products
WHERE to_tsvector('english', product_name || ' ' || description) 
    @@ to_tsquery('english', 'premium & steel')
ORDER BY rank DESC;
```

### String Aggregation

```sql
-- Concatenate product names per category
SELECT 
    category_id,
    STRING_AGG(product_name, ', ' ORDER BY product_name) as products
FROM products
GROUP BY category_id;
```

### Regular Expression Extraction

```sql
-- Extract phone area code
SELECT 
    customer_id,
    phone,
    SUBSTRING(phone FROM '\(([0-9]{3})\)') as area_code
FROM customers;

-- Extract email domain
SELECT 
    customer_id,
    email,
    SUBSTRING(email FROM '@(.*)$') as email_domain
FROM customers;
```

## Hierarchical Data

### Adjacency List Model

```sql
-- Employees with manager relationship
CREATE TABLE employees (
    employee_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    manager_id INTEGER REFERENCES employees(employee_id)
);

-- Get direct reports
SELECT 
    e.name as employee,
    m.name as manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.employee_id;
```

### Recursive Queries (Organization Chart)

```sql
-- Get all employees in hierarchy under a specific manager
WITH RECURSIVE employee_hierarchy AS (
    -- Base case: Start with top-level manager
    SELECT 
        employee_id,
        name,
        manager_id,
        1 as level,
        name as path
    FROM employees
    WHERE employee_id = 1  -- CEO
    
    UNION ALL
    
    -- Recursive case: Get direct reports
    SELECT 
        e.employee_id,
        e.name,
        e.manager_id,
        eh.level + 1,
        eh.path || ' > ' || e.name
    FROM employees e
    INNER JOIN employee_hierarchy eh ON e.manager_id = eh.employee_id
)
SELECT 
    REPEAT('  ', level - 1) || name as employee,
    level,
    path
FROM employee_hierarchy
ORDER BY path;
```

### Category Tree (Recursive)

```sql
-- Get all subcategories of a parent category
WITH RECURSIVE category_tree AS (
    SELECT 
        category_id,
        category_name,
        parent_category_id,
        1 as level
    FROM categories
    WHERE category_id = 5  -- Starting category
    
    UNION ALL
    
    SELECT 
        c.category_id,
        c.category_name,
        c.parent_category_id,
        ct.level + 1
    FROM categories c
    INNER JOIN category_tree ct ON c.parent_category_id = ct.category_id
)
SELECT * FROM category_tree
ORDER BY level, category_name;
```

## Pivot and Unpivot

### Pivot (Rows to Columns)

```sql
-- Pivot monthly sales by category
SELECT 
    category_name,
    SUM(CASE WHEN month = 1 THEN sales ELSE 0 END) as jan,
    SUM(CASE WHEN month = 2 THEN sales ELSE 0 END) as feb,
    SUM(CASE WHEN month = 3 THEN sales ELSE 0 END) as mar,
    SUM(CASE WHEN month = 4 THEN sales ELSE 0 END) as apr,
    SUM(CASE WHEN month = 5 THEN sales ELSE 0 END) as may,
    SUM(CASE WHEN month = 6 THEN sales ELSE 0 END) as jun
FROM (
    SELECT 
        c.category_name,
        EXTRACT(MONTH FROM o.order_date) as month,
        SUM(oi.quantity * oi.unit_price) as sales
    FROM categories c
    INNER JOIN products p ON c.category_id = p.category_id
    INNER JOIN order_items oi ON p.product_id = oi.product_id
    INNER JOIN orders o ON oi.order_id = o.order_id
    WHERE EXTRACT(YEAR FROM o.order_date) = 2025
    GROUP BY c.category_name, EXTRACT(MONTH FROM o.order_date)
) monthly_sales
GROUP BY category_name;
```

### Unpivot (Columns to Rows)

```sql
-- Convert quarterly columns to rows
SELECT 
    product_id,
    'Q1' as quarter,
    q1_sales as sales
FROM product_quarterly_sales
UNION ALL
SELECT product_id, 'Q2', q2_sales FROM product_quarterly_sales
UNION ALL
SELECT product_id, 'Q3', q3_sales FROM product_quarterly_sales
UNION ALL
SELECT product_id, 'Q4', q4_sales FROM product_quarterly_sales
ORDER BY product_id, quarter;
```

## Data Quality Checks

### Null Value Analysis

```sql
-- Find columns with null values
SELECT 
    COUNT(*) as total_rows,
    COUNT(email) as email_count,
    COUNT(*) - COUNT(email) as email_nulls,
    ROUND(100.0 * (COUNT(*) - COUNT(email)) / COUNT(*), 2) as email_null_pct,
    COUNT(phone) as phone_count,
    COUNT(*) - COUNT(phone) as phone_nulls,
    ROUND(100.0 * (COUNT(*) - COUNT(phone)) / COUNT(*), 2) as phone_null_pct
FROM customers;
```

### Referential Integrity Check

```sql
-- Find orphaned records (orders with no customer)
SELECT order_id, customer_id
FROM orders o
WHERE NOT EXISTS (
    SELECT 1 FROM customers c WHERE c.customer_id = o.customer_id
);
```

### Data Consistency Checks

```sql
-- Find orders where total doesn't match sum of line items
SELECT 
    o.order_id,
    o.total_amount as order_total,
    SUM(oi.quantity * oi.unit_price) as calculated_total,
    o.total_amount - SUM(oi.quantity * oi.unit_price) as difference
FROM orders o
INNER JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY o.order_id, o.total_amount
HAVING ABS(o.total_amount - SUM(oi.quantity * oi.unit_price)) > 0.01;
```

### Outlier Detection

```sql
-- Find statistical outliers using IQR method
WITH stats AS (
    SELECT 
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY unit_price) as q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY unit_price) as q3
    FROM products
),
thresholds AS (
    SELECT 
        q1,
        q3,
        q3 - q1 as iqr,
        q1 - 1.5 * (q3 - q1) as lower_bound,
        q3 + 1.5 * (q3 - q1) as upper_bound
    FROM stats
)
SELECT 
    p.product_id,
    p.product_name,
    p.unit_price,
    CASE 
        WHEN p.unit_price < t.lower_bound THEN 'Below normal range'
        WHEN p.unit_price > t.upper_bound THEN 'Above normal range'
    END as outlier_type
FROM products p, thresholds t
WHERE p.unit_price < t.lower_bound OR p.unit_price > t.upper_bound
ORDER BY p.unit_price;
```

## Summary

These patterns cover the most common SQL operations you'll encounter:

**Data Retrieval:** Top N, pagination, sampling, deduplication
**Data Manipulation:** Upsert, bulk operations, soft deletes
**Analytics:** Running totals, moving averages, cohort analysis
**Date/Time:** Range queries, date grouping, business day calculations
**Text:** Pattern matching, full-text search, string aggregation
**Hierarchical:** Recursive queries, organization charts, category trees
**Pivoting:** Converting between row and column representations
**Quality:** Null analysis, integrity checks, outlier detection

Mastering these patterns will help you write efficient, maintainable SQL queries for most business scenarios.
