# Epicor P21 Database Schema Reference

## Overview
Epicor P21 uses Microsoft SQL Server as its database platform. This guide covers the most commonly used tables and their relationships.

## Core Tables

### Customer Module

#### `customer` - Customer Master
Primary customer information table.

**Key Columns:**
- `customer_id` (PK) - Unique customer identifier
- `customer_name` - Customer business name
- `phone_number` - Primary phone
- `email_address` - Primary email
- `address_id` (FK) - Links to address table
- `terms_id` (FK) - Payment terms
- `credit_limit` - Customer credit limit
- `active_flag` - Y/N active status
- `delete_flag` - Y/N deletion flag

**Common Query:**
```sql
SELECT 
    c.customer_id,
    c.customer_name,
    c.phone_number,
    c.email_address,
    c.credit_limit,
    a.mail_address1,
    a.city,
    a.state_id,
    a.postal_code
FROM 
    customer c
    LEFT JOIN address a ON c.address_id = a.address_id
WHERE 
    c.delete_flag = 'N'
    AND c.active_flag = 'Y'
```

### Order Management

#### `oe_hdr` - Order Header
Main order header information.

**Key Columns:**
- `order_no` (PK) - Unique order number
- `customer_id` (FK) - Customer reference
- `order_date` - Date order was placed
- `po_no` - Customer PO number
- `order_status` - Order status code
- `ship_to_id` (FK) - Shipping address
- `order_total` - Total order amount
- `delete_flag` - Y/N deletion flag

#### `oe_line` - Order Lines
Individual line items for orders.

**Key Columns:**
- `order_no` (FK) - Links to oe_hdr
- `line_no` (PK) - Line number within order
- `item_id` (FK) - Product identifier
- `qty_ordered` - Quantity ordered
- `qty_shipped` - Quantity shipped
- `unit_price` - Price per unit
- `extended_price` - Line total (qty * price)
- `line_status` - Line status code

**Common Query:**
```sql
SELECT 
    oh.order_no,
    oh.order_date,
    c.customer_name,
    ol.line_no,
    ol.item_id,
    i.item_desc,
    ol.qty_ordered,
    ol.unit_price,
    ol.extended_price
FROM 
    oe_hdr oh
    INNER JOIN customer c ON oh.customer_id = c.customer_id
    INNER JOIN oe_line ol ON oh.order_no = ol.order_no
    INNER JOIN item i ON ol.item_id = i.item_id
WHERE 
    oh.order_date >= DATEADD(day, -30, GETDATE())
    AND oh.delete_flag = 'N'
ORDER BY 
    oh.order_date DESC, oh.order_no, ol.line_no
```

### Inventory Management

#### `inv_mast` - Inventory Master
Main item/product information.

**Key Columns:**
- `inv_mast_uid` (PK) - Unique identifier
- `item_id` - Item number/SKU
- `item_desc` - Item description
- `product_group_id` (FK) - Product category
- `unit_of_measure` - Base UOM
- `unit_weight` - Weight per unit
- `unit_cost` - Current cost
- `unit_price` - Current price
- `delete_flag` - Y/N deletion flag

#### `inv_loc` - Inventory Location
Inventory quantities by location.

**Key Columns:**
- `inv_mast_uid` (FK) - Links to inv_mast
- `location_id` (FK) - Warehouse/location
- `qty_on_hand` - Physical quantity
- `qty_allocated` - Allocated/reserved qty
- `qty_on_order` - Quantity on purchase orders
- `qty_available` - Available for sale

**Common Query:**
```sql
SELECT 
    i.item_id,
    i.item_desc,
    il.location_id,
    il.qty_on_hand,
    il.qty_allocated,
    il.qty_on_order,
    (il.qty_on_hand - il.qty_allocated) AS qty_available,
    i.unit_cost,
    (il.qty_on_hand * i.unit_cost) AS inventory_value
FROM 
    inv_mast i
    INNER JOIN inv_loc il ON i.inv_mast_uid = il.inv_mast_uid
WHERE 
    i.delete_flag = 'N'
    AND il.qty_on_hand > 0
ORDER BY 
    inventory_value DESC
```

### Invoicing

#### `invoice_hdr` - Invoice Header
Main invoice information.

**Key Columns:**
- `invoice_no` (PK) - Unique invoice number
- `customer_id` (FK) - Customer reference
- `invoice_date` - Invoice date
- `order_no` (FK) - Related order
- `invoice_total` - Total invoice amount
- `amount_paid` - Amount paid to date
- `balance_due` - Remaining balance
- `due_date` - Payment due date

#### `invoice_line` - Invoice Lines
Individual invoice line items.

**Key Columns:**
- `invoice_no` (FK) - Links to invoice_hdr
- `line_no` (PK) - Line number
- `item_id` (FK) - Product identifier
- `qty_invoiced` - Quantity invoiced
- `unit_price` - Price per unit
- `extended_price` - Line total

**Common Query:**
```sql
SELECT 
    ih.invoice_no,
    ih.invoice_date,
    c.customer_name,
    ih.invoice_total,
    ih.amount_paid,
    ih.balance_due,
    ih.due_date,
    CASE 
        WHEN ih.balance_due = 0 THEN 'Paid'
        WHEN ih.due_date < GETDATE() THEN 'Overdue'
        ELSE 'Open'
    END AS status
FROM 
    invoice_hdr ih
    INNER JOIN customer c ON ih.customer_id = c.customer_id
WHERE 
    ih.balance_due > 0
ORDER BY 
    ih.due_date ASC
```

### Purchasing

#### `po_hdr` - Purchase Order Header
Purchase order header information.

**Key Columns:**
- `po_no` (PK) - PO number
- `supplier_id` (FK) - Vendor reference
- `po_date` - PO date
- `po_status` - Status code
- `po_total` - Total PO amount

#### `po_line` - Purchase Order Lines
PO line items.

**Key Columns:**
- `po_no` (FK) - Links to po_hdr
- `line_no` (PK) - Line number
- `item_id` (FK) - Product identifier
- `qty_ordered` - Quantity ordered
- `qty_received` - Quantity received
- `unit_cost` - Cost per unit

## Common Views

### `v_customer_summary`
Pre-built view with customer summary data.

### `v_order_summary`
Pre-built view with order summary data.

### `v_inventory_summary`
Pre-built view with inventory summary data.

## Relationships

```
customer (1) ----< (N) oe_hdr (1) ----< (N) oe_line
    |                                           |
    |                                           |
    v                                           v
address                                       item
                                                |
                                                v
                                            inv_mast (1) ----< (N) inv_loc
```

## Best Practices

### 1. Always Filter Deleted Records
```sql
WHERE delete_flag = 'N'
```

### 2. Use NOLOCK for Read-Only Queries
```sql
SELECT * FROM customer WITH (NOLOCK)
WHERE customer_id = '12345'
```

### 3. Index Usage
- Always filter on indexed columns (customer_id, order_no, item_id)
- Use date ranges on indexed date columns
- Avoid functions on indexed columns in WHERE clause

### 4. Join Optimization
```sql
-- Good: Use INNER JOIN for required relationships
SELECT * 
FROM oe_hdr oh
INNER JOIN customer c ON oh.customer_id = c.customer_id

-- Good: Use LEFT JOIN for optional relationships
SELECT *
FROM customer c
LEFT JOIN address a ON c.address_id = a.address_id
```

### 5. Date Filtering
```sql
-- Efficient date range
WHERE order_date >= '2024-01-01' 
  AND order_date < '2024-02-01'

-- Avoid functions on date columns
-- Bad: WHERE YEAR(order_date) = 2024
-- Good: WHERE order_date >= '2024-01-01' AND order_date < '2025-01-01'
```

## Performance Tips

1. **Use Appropriate Indexes**: Ensure indexes exist on frequently queried columns
2. **Limit Result Sets**: Use TOP or WHERE clauses to limit rows
3. **Avoid SELECT ***: Select only needed columns
4. **Use EXISTS Instead of IN**: For large subqueries
5. **Batch Large Operations**: Process in chunks for bulk updates

## Common Queries

### Top Customers by Revenue
```sql
SELECT TOP 10
    c.customer_id,
    c.customer_name,
    SUM(ih.invoice_total) AS total_revenue,
    COUNT(DISTINCT ih.invoice_no) AS invoice_count
FROM 
    customer c
    INNER JOIN invoice_hdr ih ON c.customer_id = ih.customer_id
WHERE 
    ih.invoice_date >= DATEADD(year, -1, GETDATE())
    AND c.delete_flag = 'N'
GROUP BY 
    c.customer_id, c.customer_name
ORDER BY 
    total_revenue DESC
```

### Slow-Moving Inventory
```sql
SELECT 
    i.item_id,
    i.item_desc,
    SUM(il.qty_on_hand) AS total_qty,
    MAX(ol.order_date) AS last_sold_date,
    DATEDIFF(day, MAX(ol.order_date), GETDATE()) AS days_since_sold
FROM 
    inv_mast i
    INNER JOIN inv_loc il ON i.inv_mast_uid = il.inv_mast_uid
    LEFT JOIN oe_line ol_line ON i.item_id = ol_line.item_id
    LEFT JOIN oe_hdr ol ON ol_line.order_no = ol.order_no
WHERE 
    i.delete_flag = 'N'
    AND il.qty_on_hand > 0
GROUP BY 
    i.item_id, i.item_desc
HAVING 
    DATEDIFF(day, MAX(ol.order_date), GETDATE()) > 180
ORDER BY 
    days_since_sold DESC
```

### Order Fulfillment Status
```sql
SELECT 
    oh.order_no,
    oh.order_date,
    c.customer_name,
    COUNT(ol.line_no) AS total_lines,
    SUM(CASE WHEN ol.qty_shipped >= ol.qty_ordered THEN 1 ELSE 0 END) AS shipped_lines,
    CASE 
        WHEN SUM(CASE WHEN ol.qty_shipped >= ol.qty_ordered THEN 1 ELSE 0 END) = COUNT(ol.line_no) 
        THEN 'Complete'
        WHEN SUM(ol.qty_shipped) > 0 
        THEN 'Partial'
        ELSE 'Pending'
    END AS fulfillment_status
FROM 
    oe_hdr oh
    INNER JOIN customer c ON oh.customer_id = c.customer_id
    INNER JOIN oe_line ol ON oh.order_no = ol.order_no
WHERE 
    oh.order_date >= DATEADD(day, -30, GETDATE())
    AND oh.delete_flag = 'N'
GROUP BY 
    oh.order_no, oh.order_date, c.customer_name
ORDER BY 
    oh.order_date DESC
```

## Resources
- P21 Database Documentation
- SQL Server Performance Tuning
- T-SQL Best Practices
- P21 Data Dictionary
