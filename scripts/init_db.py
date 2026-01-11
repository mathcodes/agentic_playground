"""
Database initialization script.
Creates tables and loads dummy data for testing the Voice-to-SQL agent.

Run with: python scripts/init_db.py
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config


# =============================================================================
# Schema Definition
# =============================================================================

SCHEMA_SQL = """
-- Drop existing tables (for clean reset)
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS inventory CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS warehouses CASCADE;
DROP TABLE IF EXISTS categories CASCADE;

-- Categories
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- Products (industrial distribution items)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category_id INTEGER REFERENCES categories(id),
    unit_price DECIMAL(10, 2) NOT NULL,
    unit_of_measure VARCHAR(20) DEFAULT 'EA',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Warehouses
CREATE TABLE warehouses (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    city VARCHAR(100),
    state VARCHAR(2)
);

-- Inventory (stock levels by product and warehouse)
CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    warehouse_id INTEGER REFERENCES warehouses(id),
    quantity_on_hand INTEGER DEFAULT 0,
    quantity_allocated INTEGER DEFAULT 0,
    reorder_point INTEGER DEFAULT 10,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, warehouse_id)
);

-- Customers
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    customer_number VARCHAR(20) UNIQUE NOT NULL,
    company_name VARCHAR(200) NOT NULL,
    contact_name VARCHAR(100),
    email VARCHAR(200),
    phone VARCHAR(20),
    city VARCHAR(100),
    state VARCHAR(2),
    credit_limit DECIMAL(12, 2) DEFAULT 10000.00,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(20) UNIQUE NOT NULL,
    customer_id INTEGER REFERENCES customers(id),
    order_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    ship_to_city VARCHAR(100),
    ship_to_state VARCHAR(2),
    subtotal DECIMAL(12, 2),
    tax DECIMAL(12, 2),
    total DECIMAL(12, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order Items
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    line_total DECIMAL(12, 2) NOT NULL
);

-- Create indexes for common queries
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_inventory_product ON inventory(product_id);
CREATE INDEX idx_inventory_warehouse ON inventory(warehouse_id);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_order_items_order ON order_items(order_id);
"""


# =============================================================================
# Dummy Data
# =============================================================================

DUMMY_DATA_SQL = """
-- Categories
INSERT INTO categories (name, description) VALUES
    ('Safety & PPE', 'Personal protective equipment and safety gear'),
    ('Hand Tools', 'Manual tools for various applications'),
    ('Power Tools', 'Electric and pneumatic powered tools'),
    ('Fasteners', 'Bolts, screws, nuts, and related hardware'),
    ('Electrical', 'Electrical supplies and components'),
    ('Plumbing', 'Pipes, fittings, and plumbing supplies'),
    ('Abrasives', 'Grinding, cutting, and sanding products'),
    ('Lubricants', 'Oils, greases, and lubricating products');

-- Warehouses
INSERT INTO warehouses (code, name, city, state) VALUES
    ('RDU', 'Raleigh Distribution Center', 'Raleigh', 'NC'),
    ('CLT', 'Charlotte Warehouse', 'Charlotte', 'NC'),
    ('RIC', 'Richmond Facility', 'Richmond', 'VA');

-- Products (Industrial Distribution items)
INSERT INTO products (sku, name, description, category_id, unit_price, unit_of_measure) VALUES
    ('SAF-001', 'Safety Glasses - Clear', 'ANSI Z87.1 rated clear safety glasses', 1, 8.99, 'EA'),
    ('SAF-002', 'Safety Glasses - Tinted', 'ANSI Z87.1 rated tinted safety glasses', 1, 9.99, 'EA'),
    ('SAF-003', 'Hard Hat - White', 'Type I Class E hard hat, white', 1, 24.99, 'EA'),
    ('SAF-004', 'Hard Hat - Yellow', 'Type I Class E hard hat, yellow', 1, 24.99, 'EA'),
    ('SAF-005', 'Nitrile Gloves - Large', 'Disposable nitrile gloves, box of 100', 1, 18.50, 'BX'),
    ('SAF-006', 'Leather Work Gloves', 'Premium leather work gloves', 1, 22.99, 'PR'),
    ('SAF-007', 'Ear Plugs - Foam', 'Disposable foam ear plugs, 200 pair box', 1, 45.00, 'BX'),
    ('SAF-008', 'Safety Vest - Hi-Vis', 'Class 2 high visibility safety vest', 1, 15.99, 'EA'),
    
    ('HND-001', '10" Adjustable Wrench', 'Chrome vanadium adjustable wrench', 2, 18.99, 'EA'),
    ('HND-002', 'Claw Hammer 16oz', 'Fiberglass handle claw hammer', 2, 14.99, 'EA'),
    ('HND-003', 'Screwdriver Set 6pc', '6 piece screwdriver set, Phillips and flat', 2, 24.99, 'SET'),
    ('HND-004', 'Tape Measure 25ft', '25 foot tape measure with magnetic tip', 2, 12.99, 'EA'),
    ('HND-005', 'Utility Knife', 'Retractable utility knife with 5 blades', 2, 8.99, 'EA'),
    ('HND-006', 'Pliers Set 3pc', 'Slip joint, needle nose, diagonal cutters', 2, 29.99, 'SET'),
    ('HND-007', 'Pry Bar 18"', '18 inch flat pry bar', 2, 16.99, 'EA'),
    ('HND-008', 'Socket Set 40pc', '40 piece SAE/Metric socket set', 2, 89.99, 'SET'),
    
    ('PWR-001', 'Cordless Drill 20V', '20V lithium-ion cordless drill kit', 3, 149.99, 'EA'),
    ('PWR-002', 'Angle Grinder 4.5"', '4.5 inch angle grinder, 11 amp', 3, 79.99, 'EA'),
    ('PWR-003', 'Circular Saw 7.25"', '7.25 inch circular saw, 15 amp', 3, 129.99, 'EA'),
    ('PWR-004', 'Impact Driver 20V', '20V lithium-ion impact driver kit', 3, 139.99, 'EA'),
    ('PWR-005', 'Reciprocating Saw', 'Corded reciprocating saw, 12 amp', 3, 89.99, 'EA'),
    ('PWR-006', 'Heat Gun', 'Variable temperature heat gun', 3, 44.99, 'EA'),
    
    ('FST-001', 'Hex Bolts 1/4-20 x 1"', 'Grade 5 hex bolts, box of 100', 4, 12.99, 'BX'),
    ('FST-002', 'Hex Bolts 3/8-16 x 2"', 'Grade 5 hex bolts, box of 50', 4, 18.99, 'BX'),
    ('FST-003', 'Lag Screws 1/4 x 3"', 'Zinc plated lag screws, box of 50', 4, 14.99, 'BX'),
    ('FST-004', 'Wood Screws #8 x 2"', 'Phillips wood screws, box of 100', 4, 8.99, 'BX'),
    ('FST-005', 'Hex Nuts 1/4-20', 'Grade 5 hex nuts, box of 100', 4, 6.99, 'BX'),
    ('FST-006', 'Flat Washers 1/4"', 'Zinc flat washers, box of 100', 4, 4.99, 'BX'),
    ('FST-007', 'Lock Washers 1/4"', 'Split lock washers, box of 100', 4, 5.99, 'BX'),
    ('FST-008', 'Anchor Bolts 3/8 x 4"', 'Wedge anchor bolts, box of 25', 4, 32.99, 'BX'),
    
    ('ELC-001', 'Wire 12 AWG Black', '12 AWG THHN wire, 500ft spool', 5, 89.99, 'RL'),
    ('ELC-002', 'Wire 14 AWG White', '14 AWG THHN wire, 500ft spool', 5, 69.99, 'RL'),
    ('ELC-003', 'Outlet Box - Metal', 'Single gang metal outlet box', 5, 2.49, 'EA'),
    ('ELC-004', 'Duplex Outlet', '15A 125V duplex receptacle', 5, 1.99, 'EA'),
    ('ELC-005', 'Light Switch', 'Single pole light switch, 15A', 5, 1.49, 'EA'),
    ('ELC-006', 'Wire Nuts Assorted', 'Wire nut assortment, 160 piece', 5, 12.99, 'PK'),
    ('ELC-007', 'Electrical Tape', 'Black electrical tape, 10 pack', 5, 9.99, 'PK'),
    ('ELC-008', 'Circuit Breaker 20A', '20 amp single pole breaker', 5, 8.99, 'EA'),
    
    ('ABR-001', 'Cut-Off Wheels 4.5"', '4.5" cut-off wheels, 25 pack', 7, 24.99, 'PK'),
    ('ABR-002', 'Grinding Wheels 4.5"', '4.5" grinding wheels, 10 pack', 7, 19.99, 'PK'),
    ('ABR-003', 'Flap Disc 4.5" 60 Grit', '4.5" flap disc, 60 grit, 10 pack', 7, 34.99, 'PK'),
    ('ABR-004', 'Sandpaper Sheets Asst', 'Assorted grit sandpaper, 50 sheets', 7, 14.99, 'PK'),
    ('ABR-005', 'Wire Wheel 4"', '4" crimped wire wheel', 7, 12.99, 'EA'),
    
    ('LUB-001', 'WD-40 11oz', 'WD-40 multi-purpose lubricant', 8, 6.99, 'EA'),
    ('LUB-002', 'Motor Oil 10W-30', '10W-30 motor oil, quart', 8, 5.99, 'QT'),
    ('LUB-003', 'Grease Cartridge', 'Multi-purpose grease cartridge', 8, 4.99, 'EA'),
    ('LUB-004', 'Penetrating Oil', 'PB Blaster penetrating catalyst', 8, 8.99, 'EA'),
    ('LUB-005', 'Silicone Spray', 'Silicone lubricant spray', 8, 7.99, 'EA');

-- Inventory (distribute across warehouses)
INSERT INTO inventory (product_id, warehouse_id, quantity_on_hand, quantity_allocated, reorder_point) VALUES
    -- RDU warehouse (main)
    (1, 1, 250, 20, 50), (2, 1, 180, 15, 40), (3, 1, 85, 5, 20), (4, 1, 75, 8, 20),
    (5, 1, 120, 30, 30), (6, 1, 65, 10, 15), (7, 1, 45, 5, 10), (8, 1, 90, 12, 20),
    (9, 1, 55, 8, 15), (10, 1, 80, 5, 20), (11, 1, 40, 6, 10), (12, 1, 95, 15, 25),
    (13, 1, 70, 8, 15), (14, 1, 35, 4, 10), (15, 1, 45, 3, 10), (16, 1, 25, 2, 8),
    (17, 1, 18, 3, 5), (18, 1, 22, 4, 8), (19, 1, 15, 2, 5), (20, 1, 20, 3, 6),
    (21, 1, 12, 1, 4), (22, 1, 28, 5, 8), (23, 1, 200, 40, 50), (24, 1, 150, 25, 40),
    (25, 1, 180, 30, 45), (26, 1, 300, 50, 75), (27, 1, 280, 45, 70), (28, 1, 250, 35, 60),
    (29, 1, 220, 30, 50), (30, 1, 45, 8, 12), (31, 1, 40, 6, 10), (32, 1, 35, 5, 10),
    (33, 1, 85, 12, 20), (34, 1, 150, 25, 40), (35, 1, 180, 20, 45), (36, 1, 120, 15, 30),
    (37, 1, 140, 18, 35), (38, 1, 90, 10, 25), (39, 1, 60, 8, 15), (40, 1, 100, 12, 25),
    (41, 1, 75, 10, 20), (42, 1, 55, 6, 15), (43, 1, 65, 8, 18), (44, 1, 200, 30, 50),
    (45, 1, 180, 25, 45), (46, 1, 150, 20, 40), (47, 1, 120, 15, 30), (48, 1, 95, 10, 25),
    
    -- CLT warehouse
    (1, 2, 120, 10, 30), (2, 2, 100, 8, 25), (3, 2, 45, 3, 12), (4, 2, 40, 5, 12),
    (5, 2, 65, 15, 20), (9, 2, 30, 4, 10), (10, 2, 45, 3, 12), (12, 2, 50, 8, 15),
    (17, 2, 10, 2, 4), (18, 2, 12, 2, 5), (23, 2, 100, 20, 30), (24, 2, 80, 15, 25),
    (33, 2, 45, 6, 12), (34, 2, 80, 12, 22), (44, 2, 100, 15, 28), (45, 2, 90, 12, 25),
    
    -- RIC warehouse  
    (1, 3, 80, 5, 20), (2, 3, 60, 4, 15), (5, 3, 40, 10, 12), (8, 3, 35, 5, 10),
    (9, 3, 25, 3, 8), (12, 3, 40, 5, 12), (17, 3, 8, 1, 3), (23, 3, 75, 12, 20),
    (26, 3, 120, 20, 35), (33, 3, 35, 5, 10), (44, 3, 80, 10, 22);

-- Customers
INSERT INTO customers (customer_number, company_name, contact_name, email, phone, city, state, credit_limit) VALUES
    ('C-1001', 'ABC Construction', 'John Smith', 'jsmith@abcconstruction.com', '919-555-0101', 'Raleigh', 'NC', 50000.00),
    ('C-1002', 'Delta Manufacturing', 'Sarah Johnson', 'sjohnson@deltamfg.com', '704-555-0102', 'Charlotte', 'NC', 75000.00),
    ('C-1003', 'Precision Welding Inc', 'Mike Davis', 'mdavis@precisionweld.com', '919-555-0103', 'Durham', 'NC', 25000.00),
    ('C-1004', 'Thompson Electric', 'Lisa Thompson', 'lisa@thompsonelectric.com', '804-555-0104', 'Richmond', 'VA', 40000.00),
    ('C-1005', 'Carolina Contractors', 'Bob Williams', 'bob@carolinacontractors.com', '910-555-0105', 'Wilmington', 'NC', 60000.00),
    ('C-1006', 'Summit Builders', 'Amy Chen', 'achen@summitbuilders.com', '828-555-0106', 'Asheville', 'NC', 35000.00),
    ('C-1007', 'Industrial Solutions LLC', 'Tom Brown', 'tbrown@industrialsolutions.com', '336-555-0107', 'Greensboro', 'NC', 100000.00),
    ('C-1008', 'Coastal Plumbing', 'Nancy White', 'nwhite@coastalplumbing.com', '252-555-0108', 'Greenville', 'NC', 20000.00),
    ('C-1009', 'Metro Maintenance', 'James Wilson', 'jwilson@metromaint.com', '919-555-0109', 'Cary', 'NC', 30000.00),
    ('C-1010', 'Apex Fabrication', 'Karen Miller', 'kmiller@apexfab.com', '919-555-0110', 'Apex', 'NC', 55000.00);

-- Orders
INSERT INTO orders (order_number, customer_id, order_date, status, ship_to_city, ship_to_state, subtotal, tax, total) VALUES
    ('ORD-2024-001', 1, '2024-01-15', 'shipped', 'Raleigh', 'NC', 524.85, 36.74, 561.59),
    ('ORD-2024-002', 2, '2024-01-18', 'shipped', 'Charlotte', 'NC', 1289.45, 90.26, 1379.71),
    ('ORD-2024-003', 3, '2024-01-20', 'shipped', 'Durham', 'NC', 245.90, 17.21, 263.11),
    ('ORD-2024-004', 4, '2024-01-22', 'shipped', 'Richmond', 'VA', 892.50, 53.55, 946.05),
    ('ORD-2024-005', 5, '2024-01-25', 'shipped', 'Wilmington', 'NC', 1567.80, 109.75, 1677.55),
    ('ORD-2024-006', 1, '2024-02-01', 'shipped', 'Raleigh', 'NC', 334.95, 23.45, 358.40),
    ('ORD-2024-007', 7, '2024-02-05', 'shipped', 'Greensboro', 'NC', 2145.60, 150.19, 2295.79),
    ('ORD-2024-008', 2, '2024-02-08', 'shipped', 'Charlotte', 'NC', 678.25, 47.48, 725.73),
    ('ORD-2024-009', 6, '2024-02-12', 'shipped', 'Asheville', 'NC', 456.70, 31.97, 488.67),
    ('ORD-2024-010', 8, '2024-02-15', 'delivered', 'Greenville', 'NC', 289.90, 20.29, 310.19),
    ('ORD-2024-011', 9, '2024-02-18', 'delivered', 'Cary', 'NC', 1023.45, 71.64, 1095.09),
    ('ORD-2024-012', 10, '2024-02-22', 'delivered', 'Apex', 'NC', 834.60, 58.42, 893.02),
    ('ORD-2024-013', 3, '2024-02-28', 'delivered', 'Durham', 'NC', 567.80, 39.75, 607.55),
    ('ORD-2024-014', 1, '2024-03-05', 'delivered', 'Raleigh', 'NC', 1456.90, 101.98, 1558.88),
    ('ORD-2024-015', 4, '2024-03-10', 'pending', 'Richmond', 'VA', 723.40, 43.40, 766.80),
    ('ORD-2024-016', 7, '2024-03-12', 'pending', 'Greensboro', 'NC', 1890.25, 132.32, 2022.57),
    ('ORD-2024-017', 5, '2024-03-15', 'pending', 'Wilmington', 'NC', 445.60, 31.19, 476.79),
    ('ORD-2024-018', 2, '2024-03-18', 'pending', 'Charlotte', 'NC', 2234.80, 156.44, 2391.24);

-- Order Items (sample line items)
INSERT INTO order_items (order_id, product_id, quantity, unit_price, line_total) VALUES
    -- Order 1: ABC Construction
    (1, 1, 25, 8.99, 224.75), (1, 5, 10, 18.50, 185.00), (1, 12, 5, 12.99, 64.95), (1, 13, 3, 8.99, 26.97),
    -- Order 2: Delta Manufacturing  
    (2, 17, 3, 149.99, 449.97), (2, 18, 2, 79.99, 159.98), (2, 39, 15, 24.99, 374.85), (2, 40, 15, 19.99, 299.85),
    -- Order 3: Precision Welding
    (3, 18, 1, 79.99, 79.99), (3, 39, 5, 24.99, 124.95), (3, 41, 3, 12.99, 38.97),
    -- Order 4: Thompson Electric
    (4, 31, 3, 89.99, 269.97), (4, 32, 4, 69.99, 279.96), (4, 33, 50, 2.49, 124.50), (4, 34, 50, 1.99, 99.50), (4, 37, 10, 9.99, 99.90),
    -- Order 5: Carolina Contractors
    (5, 3, 20, 24.99, 499.80), (5, 4, 20, 24.99, 499.80), (5, 8, 25, 15.99, 399.75), (5, 6, 8, 22.99, 183.92),
    -- Order 6: ABC Construction (repeat)
    (6, 5, 15, 18.50, 277.50), (6, 7, 1, 45.00, 45.00),
    -- Order 7: Industrial Solutions
    (7, 16, 10, 89.99, 899.90), (7, 17, 5, 149.99, 749.95), (7, 20, 3, 139.99, 419.97),
    -- Order 8: Delta Manufacturing (repeat)
    (8, 23, 20, 12.99, 259.80), (8, 24, 15, 18.99, 284.85), (8, 28, 4, 32.99, 131.96),
    -- Order 9: Summit Builders
    (9, 9, 10, 18.99, 189.90), (9, 10, 8, 14.99, 119.92), (9, 11, 4, 24.99, 99.96), (9, 15, 3, 16.99, 50.97),
    -- Order 10: Coastal Plumbing
    (10, 44, 20, 6.99, 139.80), (10, 46, 15, 4.99, 74.85), (10, 47, 10, 8.99, 89.90),
    -- More orders...
    (11, 1, 50, 8.99, 449.50), (11, 2, 30, 9.99, 299.70), (11, 5, 15, 18.50, 277.50),
    (12, 17, 2, 149.99, 299.98), (12, 19, 2, 129.99, 259.98), (12, 22, 5, 44.99, 224.95),
    (13, 39, 10, 24.99, 249.90), (13, 40, 8, 19.99, 159.92), (13, 41, 12, 12.99, 155.88),
    (14, 31, 5, 89.99, 449.95), (14, 32, 6, 69.99, 419.94), (14, 35, 25, 1.49, 37.25), (14, 38, 5, 8.99, 44.95),
    (15, 9, 15, 18.99, 284.85), (15, 14, 8, 29.99, 239.92), (15, 16, 2, 89.99, 179.98),
    (16, 17, 6, 149.99, 899.94), (16, 20, 4, 139.99, 559.96), (16, 21, 3, 89.99, 269.97),
    (17, 1, 20, 8.99, 179.80), (17, 8, 10, 15.99, 159.90), (17, 12, 8, 12.99, 103.92),
    (18, 3, 30, 24.99, 749.70), (18, 6, 25, 22.99, 574.75), (18, 5, 50, 18.50, 925.00);
"""


def create_database_if_not_exists():
    """Create the voice_sql_test database if it doesn't exist."""
    # Parse connection string to get database name
    db_url = config.DATABASE_URL
    db_name = db_url.rsplit('/', 1)[-1]
    base_url = db_url.rsplit('/', 1)[0]
    
    # Connect to default 'postgres' database
    conn = psycopg2.connect(f"{base_url}/postgres")
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Check if database exists
    cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
    exists = cursor.fetchone()
    
    if not exists:
        print(f"Creating database '{db_name}'...")
        cursor.execute(f'CREATE DATABASE "{db_name}"')
        print(f"Database '{db_name}' created.")
    else:
        print(f"Database '{db_name}' already exists.")
    
    cursor.close()
    conn.close()


def init_schema():
    """Create tables and indexes."""
    print("Creating schema...")
    conn = psycopg2.connect(config.DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(SCHEMA_SQL)
    conn.commit()
    cursor.close()
    conn.close()
    print("Schema created.")


def load_dummy_data():
    """Load dummy data into tables."""
    print("Loading dummy data...")
    conn = psycopg2.connect(config.DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(DUMMY_DATA_SQL)
    conn.commit()
    cursor.close()
    conn.close()
    print("Dummy data loaded.")


def print_summary():
    """Print summary of loaded data."""
    conn = psycopg2.connect(config.DATABASE_URL)
    cursor = conn.cursor()
    
    tables = ['categories', 'products', 'warehouses', 'inventory', 'customers', 'orders', 'order_items']
    
    print("\n" + "=" * 50)
    print("DATABASE SUMMARY")
    print("=" * 50)
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} rows")
    
    print("=" * 50)
    print("\nDatabase ready for testing!")
    print("Try queries like:")
    print("  - 'How many products do we have?'")
    print("  - 'Show me all orders from ABC Construction'")
    print("  - 'What products are low on stock in Raleigh?'")
    print("  - 'What's our total sales by customer?'")
    
    cursor.close()
    conn.close()


def main():
    """Main initialization function."""
    print("=" * 50)
    print("VOICE-TO-SQL DATABASE INITIALIZATION")
    print("=" * 50)
    
    try:
        create_database_if_not_exists()
        init_schema()
        load_dummy_data()
        print_summary()
        return 0
    except psycopg2.OperationalError as e:
        print(f"\n❌ Database connection failed: {e}")
        print("\nMake sure PostgreSQL is running and the connection string is correct.")
        print(f"Current DATABASE_URL: {config.DATABASE_URL}")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
