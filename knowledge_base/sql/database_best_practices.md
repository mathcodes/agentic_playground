# SQL Database Best Practices

## Query Optimization

### Use Indexes Wisely
- Index columns used in WHERE, JOIN, and ORDER BY clauses
- Don't over-index (slows down writes)
- Use composite indexes for multiple column searches

### Avoid SELECT *
Always specify the columns you need:
```sql
-- Bad
SELECT * FROM products;

-- Good
SELECT id, name, price FROM products;
```

### Use LIMIT for Large Results
Always limit results in production queries:
```sql
SELECT * FROM orders 
WHERE status = 'pending'
LIMIT 100;
```

## JOIN Best Practices

### Always Specify JOIN Type
Be explicit about your joins:
```sql
-- Good
SELECT p.name, c.name as category
FROM products p
INNER JOIN categories c ON p.category_id = c.id;
```

### Use Table Aliases
Make queries more readable:
```sql
SELECT 
    o.order_number,
    c.company_name,
    p.name as product
FROM orders o
INNER JOIN customers c ON o.customer_id = c.id
INNER JOIN order_items oi ON o.id = oi.order_id
INNER JOIN products p ON oi.product_id = p.id;
```

## Aggregation Queries

### Always Use Meaningful Aliases
```sql
SELECT 
    c.company_name,
    COUNT(o.id) as total_orders,
    SUM(o.total) as total_revenue
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id, c.company_name
ORDER BY total_revenue DESC;
```

## Common Patterns

### Top N Records
```sql
SELECT name, unit_price
FROM products
ORDER BY unit_price DESC
LIMIT 5;
```

### Date Filtering
```sql
SELECT *
FROM orders
WHERE order_date >= CURRENT_DATE - INTERVAL '30 days';
```

### Case-Insensitive Search
```sql
SELECT * FROM customers
WHERE company_name ILIKE '%construction%';
```
