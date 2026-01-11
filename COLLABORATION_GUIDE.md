# Multi-Agent Collaboration System Guide

## Overview

The Voice-to-SQL system now features an advanced multi-agent collaboration architecture where specialized AI agents work together to solve complex problems. Agents can discuss, share insights, and build upon each other's expertise to provide comprehensive solutions.

## Architecture

### Three Specialized Agents

1. **SQL Agent** - Database and query expertise
   - Natural language to SQL translation
   - Database schema understanding
   - Query optimization
   - Data retrieval and formatting

2. **C# Agent** - Programming and .NET expertise
   - C# code generation
   - .NET framework guidance
   - LINQ patterns
   - Async/await best practices
   - API development

3. **Epicor P21 Agent** - ERP system expertise
   - P21 data export/import
   - P21 database schema
   - P21 API integration
   - ERP best practices
   - Business process automation

### Router Agent

The Router Agent analyzes incoming queries and determines:
- Which agent(s) should handle the query
- Whether multiple agents should collaborate
- The collaboration mode (single, sequential, or parallel)

### Collaboration Modes

#### 1. Single Agent Mode
- One agent handles the entire query
- Used for straightforward, domain-specific questions
- Fastest response time

**Example:**
```
Query: "Show me all customers"
→ SQL Agent only
```

#### 2. Sequential Collaboration
- Agents work in order, each building on previous responses
- Primary agent responds first
- Supporting agents add their expertise
- Creates a comprehensive, layered response

**Example:**
```
Query: "Write C# code to query P21 database for top customers"
→ Epicor P21 Agent (P21 schema and context)
→ SQL Agent (query structure)
→ C# Agent (code implementation)
```

#### 3. Parallel Collaboration
- Multiple agents work simultaneously
- Each provides independent perspective
- Responses are synthesized
- Used for complex, multi-faceted problems

**Example:**
```
Query: "Build a complete P21 integration solution"
→ All agents work in parallel
→ Combined insights provide full picture
```

## How Agents Collaborate

### Information Sharing

When agents collaborate, they share:
1. **Query Context**: The original user question
2. **Previous Responses**: What other agents have said
3. **Knowledge Base**: Relevant documentation
4. **Suggestions**: When to involve other agents

### Collaboration Flow

```
User Query
    ↓
Router Analysis
    ↓
┌─────────────────────────────────────┐
│  Determine Collaboration Strategy   │
│  - Primary Agent                    │
│  - Supporting Agents                │
│  - Collaboration Mode               │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Sequential Collaboration Example   │
│                                     │
│  1. Primary Agent Responds          │
│     - Provides domain expertise     │
│     - Identifies collaboration needs│
│                                     │
│  2. Supporting Agent 1              │
│     - Reviews primary response      │
│     - Adds complementary insights   │
│     - Builds upon previous work     │
│                                     │
│  3. Supporting Agent 2              │
│     - Reviews all previous responses│
│     - Provides final expertise      │
│     - Synthesizes complete solution │
└─────────────────────────────────────┘
    ↓
Final Synthesized Response
```

## Example Scenarios

### Scenario 1: Simple SQL Query
**Query:** "Show me all products"

**Routing Decision:**
- Mode: Single
- Agent: SQL

**Result:**
```sql
SELECT * FROM products WHERE delete_flag = 'N';
```

---

### Scenario 2: C# with Database Context
**Query:** "Write async C# code to query database"

**Routing Decision:**
- Mode: Sequential
- Primary: C# Agent
- Supporting: SQL Agent

**Collaboration:**

**C# Agent:**
```csharp
public async Task<List<Customer>> GetCustomersAsync()
{
    using var connection = new SqlConnection(connectionString);
    await connection.OpenAsync();
    
    // SQL Agent can provide the optimal query
    var command = new SqlCommand(query, connection);
    // ... implementation
}
```

**SQL Agent:**
```sql
-- Optimized query for the C# code above
SELECT customer_id, customer_name, email_address
FROM customer
WHERE active_flag = 'Y' AND delete_flag = 'N'
ORDER BY customer_name;
```

---

### Scenario 3: Complete P21 Integration
**Query:** "Build a P21 integration API to export sales data with caching"

**Routing Decision:**
- Mode: Sequential
- Primary: Epicor P21 Agent
- Supporting: C# Agent, SQL Agent

**Collaboration:**

**Epicor P21 Agent:**
"For P21 sales data export, you'll need to access the `oe_hdr` and `oe_line` tables. The P21 API provides REST endpoints, but direct database access is often more efficient for bulk exports. Key considerations:
- Use P21's standard views when available
- Implement proper authentication
- Handle P21-specific date formats
- Consider P21 version compatibility"

**SQL Agent:**
```sql
-- Efficient query for P21 sales data
SELECT 
    oh.order_no,
    oh.order_date,
    c.customer_name,
    SUM(ol.extended_price) AS total_amount
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
    oh.order_date DESC;
```

**C# Agent:**
```csharp
public class P21SalesExportService
{
    private readonly IMemoryCache _cache;
    private readonly string _connectionString;
    
    public async Task<List<SalesOrder>> GetSalesDataAsync(
        DateTime startDate, 
        DateTime endDate)
    {
        var cacheKey = $"sales_{startDate:yyyyMMdd}_{endDate:yyyyMMdd}";
        
        // Check cache first
        if (_cache.TryGetValue(cacheKey, out List<SalesOrder> cached))
        {
            return cached;
        }
        
        // Query P21 database (using SQL from SQL Agent)
        using var connection = new SqlConnection(_connectionString);
        await connection.OpenAsync();
        
        var command = new SqlCommand(sqlQuery, connection);
        command.Parameters.AddWithValue("@startDate", startDate);
        command.Parameters.AddWithValue("@endDate", endDate);
        
        var orders = new List<SalesOrder>();
        using var reader = await command.ExecuteReaderAsync();
        
        while (await reader.ReadAsync())
        {
            orders.Add(new SalesOrder
            {
                OrderNo = reader.GetString(0),
                OrderDate = reader.GetDateTime(1),
                CustomerName = reader.GetString(2),
                TotalAmount = reader.GetDecimal(3)
            });
        }
        
        // Cache for 5 minutes
        _cache.Set(cacheKey, orders, TimeSpan.FromMinutes(5));
        
        return orders;
    }
}
```

## Knowledge Base Integration

Each agent has access to a knowledge base with domain-specific documentation:

### SQL Agent Knowledge Base
- `knowledge_base/sql/`
  - Database best practices
  - Query optimization techniques
  - Schema design patterns

### C# Agent Knowledge Base
- `knowledge_base/csharp/`
  - LINQ patterns
  - Async/await guide
  - Design patterns

### Epicor P21 Agent Knowledge Base
- `knowledge_base/epicor/`
  - P21 export guide
  - P21 API integration
  - P21 database schema

### Shared Knowledge
- `knowledge_base/shared/`
  - Common errors and solutions
  - Integration patterns
  - Security best practices

## Adding New Documents

To add knowledge for agents:

1. Create a markdown file in the appropriate folder:
   ```bash
   knowledge_base/
   ├── sql/
   │   └── your_document.md
   ├── csharp/
   │   └── your_document.md
   ├── epicor/
   │   └── your_document.md
   └── shared/
       └── your_document.md
   ```

2. The system automatically indexes and retrieves relevant documents

3. Documents are matched based on:
   - Keyword relevance
   - Content similarity
   - Agent type

## Best Practices

### For Users

1. **Be Specific**: Clear queries get better routing
   - Good: "Write C# code to export P21 customer data"
   - Less Good: "Help with P21"

2. **Indicate Complexity**: Mention if you need multiple perspectives
   - "Build a complete solution for..."
   - "I need both SQL and C# help with..."

3. **Provide Context**: Mention relevant technologies
   - "Using Entity Framework Core"
   - "For P21 version 3.x"

### For Developers

1. **Agent Design**: Each agent should:
   - Have clear expertise boundaries
   - Recognize when to suggest collaboration
   - Build upon other agents' insights

2. **Knowledge Base**: Keep documents:
   - Focused and specific
   - Up-to-date
   - Well-organized

3. **Routing Logic**: The router should:
   - Prefer single agent when possible
   - Use sequential for dependent tasks
   - Use parallel for independent perspectives

## Web UI Features

The web interface shows:
- **Agent Badges**: Which agents are involved
- **Collaboration Mode**: Single, Sequential, or Parallel
- **Agent Discussions**: Each agent's contribution
- **Synthesized Response**: Combined final answer
- **Real-time Logging**: Watch agents collaborate live

## API Response Format

```json
{
  "success": true,
  "mode": "sequential",
  "agents_used": ["epicor", "sql", "csharp"],
  "confidence": "high",
  "collaboration_session": {
    "messages": [
      {
        "agent": "Epicor P21 Specialist",
        "content": "...",
        "timestamp": "2026-01-11T10:30:00"
      },
      {
        "agent": "SQL Specialist",
        "content": "...",
        "timestamp": "2026-01-11T10:30:05"
      }
    ]
  },
  "final_response": "..."
}
```

## Performance Considerations

- **Single Agent**: ~2-5 seconds
- **Sequential (2 agents)**: ~5-10 seconds
- **Sequential (3 agents)**: ~10-15 seconds
- **Parallel (3 agents)**: ~5-8 seconds

## Troubleshooting

### Agent Not Responding
- Check `ANTHROPIC_API_KEY` is set
- Verify API rate limits
- Check agent logs

### Wrong Agent Selected
- Router uses AI to classify
- Provide more specific keywords
- Check routing confidence score

### Collaboration Not Triggered
- Query may be too simple
- Router prefers efficiency
- Try explicitly mentioning multiple domains

## Future Enhancements

Potential additions:
- More specialized agents (Python, Java, etc.)
- Agent memory and learning
- User feedback on routing decisions
- Custom agent configurations
- Agent performance metrics

## Resources

- [Multi-Agent Architecture](MULTI_AGENT_ARCHITECTURE.md)
- [Knowledge Base Guide](KNOWLEDGE_BASE_GUIDE.md)
- [SQL Generation Explained](SQL_GENERATION_EXPLAINED.md)
- [Setup Guide](SETUP_GUIDE.md)
