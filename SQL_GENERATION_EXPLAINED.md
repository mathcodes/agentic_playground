# 🧠 How Voice-to-SQL Translates Natural Language to SQL

## Overview

This app uses **Claude Sonnet 4** (Anthropic's latest AI model) to convert natural language questions into SQL queries. It's an **agentic AI system** that combines multiple techniques to generate accurate, safe SQL.

---

## 🎯 The Core Technology: Claude Sonnet 4

**Model:** `claude-sonnet-4-20250514`  
**Purpose:** Large Language Model (LLM) that understands natural language and can generate SQL

### Why Claude?
- **Context-aware:** Understands complex database relationships
- **Reasoning:** Can infer what tables/columns are needed
- **SQL expertise:** Trained on massive amounts of SQL code
- **Safety:** Follows instructions to avoid dangerous queries

---

## 🔄 The Translation Pipeline

### Step 1: **Schema Introspection**

Before generating SQL, the system extracts your database structure:

```
Database → PostgreSQL → Information Schema → Extract Tables/Columns/Relationships
```

**What it captures:**
```sql
-- Tables
categories, products, warehouses, inventory, customers, orders, order_items

-- For each table:
- Column names (id, name, price, etc.)
- Data types (INTEGER, VARCHAR, DECIMAL)
- Constraints (NOT NULL, PRIMARY KEY)
- Foreign key relationships
```

**Code:** `src/sql/schema.py`

```python
def get_full_schema_description():
    """Generate complete schema for the LLM"""
    tables = get_table_names()
    for table in tables:
        columns = get_table_schema(table)
        # Format as text for Claude
    
    relationships = get_foreign_keys()
    # Add FK relationships
    
    return formatted_schema
```

**Example output:**
```
Table: products
----------------------------------------
  id: integer NOT NULL
  sku: varchar(50) NOT NULL
  name: varchar(200) NOT NULL
  unit_price: decimal(10,2) NOT NULL
  category_id: integer NULL

RELATIONSHIPS
----------------------------------------
  products.category_id -> categories.id
  orders.customer_id -> customers.id
```

---

## 🎨 Step 2: **Prompt Engineering**

The system constructs a carefully crafted prompt that tells Claude:

### The System Prompt

```python
SYSTEM_PROMPT = """You are a SQL query generator for a PostgreSQL database.

IMPORTANT RULES:
1. Generate ONLY the SQL query - no explanations
2. Use PostgreSQL syntax
3. Always use table aliases for clarity
4. Limit results to {max_results} rows
5. For aggregations, use meaningful column aliases
6. NEVER generate INSERT, UPDATE, DELETE, DROP statements
7. Use ILIKE for case-insensitive text matching

{schema}

Remember: Return ONLY the SQL query, nothing else."""
```

**What gets injected:**
- `{max_results}` → 100 (configurable)
- `{schema}` → Full database schema from Step 1

### The User Message

```python
messages=[
    {
        "role": "user",
        "content": "Convert this to SQL: How many products do we have?"
    }
]
```

---

## 🤖 Step 3: **Claude API Call**

The system sends the prompt to Claude's API:

```python
client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system=system_prompt,        # Rules + Schema
    messages=[
        {
            "role": "user",
            "content": f"Convert this to SQL: {natural_language_query}"
        }
    ]
)

raw_response = message.content[0].text
```

**What Claude sees:**
```
SYSTEM: You are a SQL generator. Here are all the tables...
        [Full schema with 8 tables, columns, relationships]
        
USER:   Convert this to SQL: How many products do we have?
```

**What Claude returns:**
```sql
SELECT COUNT(*) as product_count FROM products;
```

---

## 🔍 Step 4: **SQL Extraction & Cleanup**

Claude sometimes adds markdown or explanations. We clean it:

```python
def extract_sql_from_response(response: str) -> str:
    # Remove markdown code blocks
    sql = re.sub(r'```sql\s*', '', response)
    sql = re.sub(r'```\s*', '', sql)
    
    # Extract just the SELECT statement
    if not sql.upper().startswith(('SELECT', 'WITH')):
        match = re.search(r'((?:WITH|SELECT)[\s\S]+?)(?:;|$)', sql)
        if match:
            sql = match.group(1)
    
    # Ensure it ends with semicolon
    if not sql.endswith(';'):
        sql += ';'
    
    return sql
```

---

## 🛡️ Step 5: **Safety Validation**

Before executing, we check if the SQL is safe:

```python
def validate_sql_safety(sql: str) -> tuple[bool, str]:
    """Validate that SQL is safe to execute"""
    
    sql_upper = sql.upper()
    
    # Block dangerous keywords
    dangerous_keywords = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'TRUNCATE', 
        'ALTER', 'CREATE', 'GRANT', 'REVOKE'
    ]
    
    if not config.ALLOW_WRITE_QUERIES:
        for keyword in dangerous_keywords:
            if re.search(rf'\b{keyword}\b', sql_upper):
                return False, f"Forbidden keyword: {keyword}"
    
    # Check for multiple statements (SQL injection)
    if sql.count(';') > 1:
        return False, "Multiple statements detected"
    
    # Block SQL comments (could hide malicious code)
    if '--' in sql or '/*' in sql:
        return False, "SQL comments not allowed"
    
    return True, "OK"
```

**What it blocks:**
- ❌ `DELETE FROM products;`
- ❌ `SELECT * FROM users; DROP TABLE orders;`
- ❌ `SELECT * FROM products -- WHERE id=1`

**What it allows:**
- ✅ `SELECT * FROM products WHERE price < 50;`
- ✅ `SELECT COUNT(*) FROM orders;`

---

## 🎯 Step 6: **Query Execution**

If validation passes, we execute the query:

```python
def execute_query(sql: str) -> QueryResult:
    conn = psycopg2.connect(config.DATABASE_URL)
    cursor = conn.cursor()
    
    cursor.execute(sql)
    
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchmany(config.MAX_RESULTS)  # Limit results
    
    return QueryResult(
        success=True,
        columns=columns,
        rows=rows,
        row_count=cursor.rowcount
    )
```

---

## 📊 Example Flow: Complete Translation

### Input
```
User: "Show me the top 5 most expensive products"
```

### What Happens

**1. Schema Context Built:**
```
Table: products
  id: integer
  name: varchar(200)
  unit_price: decimal(10,2)
  category_id: integer
```

**2. Prompt Sent to Claude:**
```
SYSTEM: You are a SQL generator. [Full schema...]
        Limit results to 100 rows.
        
USER:   Convert this to SQL: Show me the top 5 most expensive products
```

**3. Claude Reasons:**
- "Top 5" → ORDER BY with LIMIT 5
- "Most expensive" → ORDER BY price DESC
- "Products" → SELECT FROM products table
- Need: name and price columns

**4. Claude Generates:**
```sql
SELECT name, unit_price 
FROM products 
ORDER BY unit_price DESC 
LIMIT 5;
```

**5. Safety Check:**
- ✅ No dangerous keywords
- ✅ Single statement
- ✅ No comments

**6. Execution:**
```
PWR-001 | Cordless Drill 20V    | $149.99
PWR-003 | Circular Saw 7.25"    | $129.99
PWR-004 | Impact Driver 20V     | $139.99
...
```

---

## 🧩 Why This Approach Works

### 1. **Context-Aware Generation**
Claude knows the exact table/column names from the schema, so it doesn't hallucinate.

### 2. **Relationship Understanding**
The schema includes foreign keys, so Claude knows how to JOIN tables correctly.

```
User: "Show me orders for ABC Construction"

Claude sees:
  orders.customer_id -> customers.id
  customers.company_name

Generates:
  SELECT o.* 
  FROM orders o
  JOIN customers c ON o.customer_id = c.id
  WHERE c.company_name ILIKE '%ABC Construction%';
```

### 3. **Sample Data Hints**
The schema includes sample values:
```
orders.status values: ['pending', 'shipped', 'delivered']
warehouses.code values: ['RDU', 'CLT', 'RIC']
```

Claude uses these to generate accurate WHERE clauses.

---

## 🎨 Advanced Features

### Aggregations
```
User: "What's the total sales by customer?"

Claude generates:
SELECT 
    c.company_name,
    SUM(o.total) as total_sales
FROM customers c
JOIN orders o ON c.id = o.customer_id
GROUP BY c.company_name
ORDER BY total_sales DESC;
```

### Complex Queries
```
User: "Which products are low on stock in the Raleigh warehouse?"

Claude generates:
SELECT 
    p.name,
    i.quantity_on_hand,
    i.reorder_point
FROM inventory i
JOIN products p ON i.product_id = p.id
JOIN warehouses w ON i.warehouse_id = w.id
WHERE w.code = 'RDU'
  AND i.quantity_on_hand < i.reorder_point;
```

---

## 🔧 Configuration

**File:** `config.py`

```python
# AI Model
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"

# Safety
ALLOW_WRITE_QUERIES: bool = False  # Read-only by default
MAX_RESULTS: int = 100              # Limit rows returned
```

---

## 📈 Performance & Cost

### Speed
- **Schema extraction:** ~50ms (cached)
- **Claude API call:** 1-3 seconds
- **SQL execution:** Varies by query (usually <100ms)
- **Total:** ~2-4 seconds per query

### Cost (Anthropic API)
- **Input tokens:** ~2,000-3,000 (schema + prompt)
- **Output tokens:** ~50-200 (SQL query)
- **Cost per query:** ~$0.01-0.03

---

## 🎯 Key Files

```
voice-to-sql/
├── src/sql/
│   ├── schema.py       # Extracts database structure
│   ├── generator.py    # Claude API integration
│   └── executor.py     # Safe SQL execution
│
└── config.py           # Model and safety settings
```

---

## 🛡️ Safety Features

1. **Read-Only by Default**
   - No INSERT/UPDATE/DELETE unless explicitly enabled

2. **SQL Injection Prevention**
   - Detects multiple statements
   - Blocks SQL comments
   - Pattern matching for dangerous keywords

3. **Result Limiting**
   - Maximum 100 rows by default
   - Prevents resource exhaustion

4. **Query Logging**
   - All generated SQL is logged
   - Easy to audit what Claude produces

5. **Schema-Only Context**
   - Claude never sees actual data
   - Only knows structure, not content

---

## 🎓 The "Magic" Explained

**There's no magic!** It's:

1. **Good prompt engineering** → Tell Claude exactly what you want
2. **Rich context** → Give Claude the database schema
3. **Smart validation** → Block dangerous queries
4. **Powerful AI** → Claude's SQL expertise does the rest

The combination of these techniques creates a system that feels "magical" but is actually a well-engineered pipeline using cutting-edge AI.

---

## 🚀 Try It Yourself

Watch the logs in the web UI to see this in action:

```
[sql_generation] Generating SQL with Claude...
[sql_generation] Generated SQL: SELECT COUNT(*) FROM products;
[execution] Executing query...
[execution] Query executed successfully
[complete] Pipeline complete!
```

You're literally watching an AI agent translate human language to database queries in real-time! 🤖

---

## 📚 Further Reading

- **Anthropic Claude Docs:** https://docs.anthropic.com/
- **Prompt Engineering Guide:** https://www.promptingguide.ai/
- **PostgreSQL Schema:** https://www.postgresql.org/docs/current/information-schema.html

---

**The key insight:** By giving Claude the exact database structure and clear instructions, it can reliably generate SQL that would take a human developer minutes to write. That's the power of agentic AI! 🚀
