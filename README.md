# Multi-Agent AI System: Voice-to-SQL + C# + Epicor P21

An advanced agentic AI application featuring **multi-agent collaboration** where specialized AI agents work together to solve complex problems involving databases, programming, and ERP systems.

## 🎯 Overview

This application features **three specialized AI agents** that can work independently or collaborate:

### 🤖 Specialized Agents

1. **SQL Agent** - Database & Query Expert
   - Converts natural language to SQL
   - Executes queries against PostgreSQL
   - Provides schema-aware query generation
   - Optimizes and validates SQL

2. **C# Agent** - Programming & .NET Expert
   - Generates C# code examples
   - Explains .NET concepts
   - Provides LINQ patterns
   - Demonstrates async/await best practices

3. **Epicor P21 Agent** - ERP System Expert
   - P21 data export/import guidance
   - P21 database schema expertise
   - P21 API integration examples
   - ERP best practices

### 🤝 Collaboration Modes

- **Single Agent**: One agent handles straightforward queries
- **Sequential Collaboration**: Agents work in order, building on each other's insights
- **Parallel Collaboration**: Multiple agents provide independent perspectives

### 🎙️ Voice & Text Input

- Voice input via microphone (OpenAI Whisper)
- Text input via web UI
- Audio file processing

---

## Build Steps

We'll build this incrementally. Each step is self-contained and testable.

### Step 1: Environment Setup
- [ ] Create Python virtual environment
- [ ] Install base dependencies
- [ ] Verify PostgreSQL is running locally

### Step 2: Database Setup
- [ ] Create test database
- [ ] Load dummy data (sample inventory/sales data)
- [ ] Test basic connectivity

### Step 3: Text-to-SQL (Core Logic)
- [ ] Connect to Claude API
- [ ] Build prompt for SQL generation
- [ ] Test with hardcoded text queries

### Step 4: Speech-to-Text
- [ ] Install Whisper
- [ ] Test transcription with audio files
- [ ] Integrate with text-to-SQL pipeline

### Step 5: Live Audio Capture
- [ ] Add microphone input
- [ ] Handle recording start/stop
- [ ] Connect full pipeline

### Step 6: Safety & Polish
- [ ] Add query validation (read-only by default)
- [ ] Improve error handling
- [ ] Add result formatting

---

## Prerequisites

- Python 3.10+
- PostgreSQL 14+ (running locally)
- Anthropic API key (for Claude)
- Microphone (for live audio)

---

## 🚀 Quick Start

### Option 1: Web UI (Recommended)

```bash
# Clone and enter project
cd voice-to-sql

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export ANTHROPIC_API_KEY="your_key_here"
export DATABASE_URL="postgresql://your_user@localhost:5432/voice_sql_test"

# Initialize the database
python scripts/init_db.py

# Start the web UI
./start_ui.sh
# Or: python web_ui.py

# Open browser to http://localhost:5000
```

### Option 2: Command Line

```bash
# Text mode
python main.py --text "Show me all products"

# Voice mode (interactive)
python main.py --mode interactive

# Audio file
python main.py --audio query.wav
```

---

## 📁 Project Structure

```
voice-to-sql/
├── README.md
├── requirements.txt
├── main.py                        # CLI entry point
├── web_ui.py                      # Web UI server
├── config.py                      # Configuration
├── scripts/
│   └── init_db.py                 # Database initialization
├── src/
│   ├── audio/
│   │   ├── capture.py             # Microphone input
│   │   └── transcribe.py          # Speech-to-text (Whisper)
│   ├── sql/
│   │   ├── generator.py           # SQL generation
│   │   ├── executor.py            # Query execution
│   │   └── schema.py              # Schema introspection
│   ├── agent/
│   │   ├── router.py              # 🧠 Router Agent (multi-agent routing)
│   │   ├── orchestrator.py        # SQL Agent
│   │   ├── csharp_agent.py        # C# Agent
│   │   ├── epicor_agent.py        # Epicor P21 Agent
│   │   ├── multi_agent_orchestrator.py  # Collaboration orchestrator
│   │   └── collaboration.py       # Collaboration system
│   └── knowledge/
│       └── retriever.py           # Knowledge base retrieval
├── knowledge_base/
│   ├── sql/                       # SQL documentation
│   ├── csharp/                    # C# documentation
│   ├── epicor/                    # Epicor P21 documentation
│   └── shared/                    # Shared knowledge
├── templates/
│   └── index.html                 # Web UI template
└── docs/
    ├── MULTI_AGENT_ARCHITECTURE.md
    ├── COLLABORATION_GUIDE.md
    ├── KNOWLEDGE_BASE_GUIDE.md
    └── SQL_GENERATION_EXPLAINED.md
```

---

## Detailed Build Guide

### Step 1: Environment Setup

**1.1 Create the project directory and virtual environment:**

```bash
mkdir voice-to-sql
cd voice-to-sql
python -m venv venv
source venv/bin/activate
```

**1.2 Create requirements.txt with initial dependencies:**

See `requirements.txt` in this repo.

**1.3 Verify PostgreSQL:**

```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT version();"
```

If not installed, install PostgreSQL for your OS.

---

### Step 2: Database Setup

**2.1 Create the test database:**

```bash
psql -U postgres -c "CREATE DATABASE voice_sql_test;"
```

**2.2 Run the initialization script:**

```bash
python scripts/init_db.py
```

This creates sample tables with dummy data representing a simplified distribution/inventory scenario.

**Tables created:**
- `products` - Product catalog
- `inventory` - Stock levels by location  
- `customers` - Customer information
- `orders` - Order headers
- `order_items` - Order line items

---

### Step 3: Text-to-SQL (Core Logic)

This is the heart of the application. We use Claude to:
1. Understand the user's natural language question
2. Reference the database schema
3. Generate safe, valid SQL

**Key files:**
- `src/sql/schema.py` - Extracts schema from PostgreSQL
- `src/sql/generator.py` - LLM prompt construction and SQL generation

**Test independently:**

```bash
python -c "from src.sql.generator import generate_sql; print(generate_sql('How many products do we have?'))"
```

---

### Step 4: Speech-to-Text

We use OpenAI's Whisper model (runs locally, no API needed).

**Key files:**
- `src/audio/transcribe.py` - Whisper integration

**Test with an audio file:**

```bash
python -c "from src.audio.transcribe import transcribe; print(transcribe('test.wav'))"
```

---

### Step 5: Live Audio Capture

Using `sounddevice` for cross-platform microphone access.

**Key files:**
- `src/audio/capture.py` - Microphone recording

**Test recording:**

```bash
python -c "from src.audio.capture import record_audio; record_audio('test.wav', duration=5)"
```

---

### Step 6: Full Pipeline

The orchestrator ties everything together:

```
Audio Input → Transcribe → Generate SQL → Execute → Format Results
```

---

## Configuration

All configuration via environment variables (`.env` file):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/voice_sql_test` |
| `ANTHROPIC_API_KEY` | Your Claude API key | (required) |
| `WHISPER_MODEL` | Whisper model size | `base` |
| `ALLOW_WRITE_QUERIES` | Allow INSERT/UPDATE/DELETE | `false` |

---

## Safety Considerations

By default, this application:
- ✅ Only executes SELECT queries
- ✅ Uses parameterized queries where possible
- ✅ Limits result set size
- ✅ Logs all generated SQL

To enable write operations, set `ALLOW_WRITE_QUERIES=true` (use with caution).

---

## 💡 Example Usage

### Single Agent (SQL)
```
Query: "Show me all products under $50"

🤖 Agent: SQL
📊 Mode: SINGLE

Generated SQL:
  SELECT * FROM products WHERE price < 50 AND delete_flag = 'N';

Results:
  ┌────┬──────────────────┬───────┬──────────┐
  │ id │ name             │ price │ category │
  ├────┼──────────────────┼───────┼──────────┤
  │ 3  │ Safety Glasses   │ 12.99 │ PPE      │
  │ 7  │ Work Gloves      │ 8.50  │ PPE      │
  │ 12 │ Cable Ties (100) │ 4.99  │ Supplies │
  └────┴──────────────────┴───────┴──────────┘
```

### Multi-Agent Collaboration
```
Query: "Write C# code to query P21 database for top customers"

🤖 Agents: EPICOR, SQL, C#
🔄 Mode: SEQUENTIAL COLLABORATION

--- Epicor P21 Specialist ---
For P21 customer queries, use the `customer` table joined with `invoice_hdr`
for revenue calculations. Key considerations:
- Filter by delete_flag = 'N' and active_flag = 'Y'
- Use proper date ranges for revenue calculations
- Consider P21 version-specific schema differences

--- SQL Specialist ---
SELECT TOP 10
    c.customer_id,
    c.customer_name,
    SUM(ih.invoice_total) AS total_revenue
FROM customer c
INNER JOIN invoice_hdr ih ON c.customer_id = ih.customer_id
WHERE c.delete_flag = 'N' AND c.active_flag = 'Y'
    AND ih.invoice_date >= DATEADD(year, -1, GETDATE())
GROUP BY c.customer_id, c.customer_name
ORDER BY total_revenue DESC;

--- C# Specialist ---
public async Task<List<Customer>> GetTopCustomersAsync()
{
    using var connection = new SqlConnection(_p21ConnectionString);
    await connection.OpenAsync();
    
    var query = @"
        SELECT TOP 10
            c.customer_id AS CustomerId,
            c.customer_name AS CustomerName,
            SUM(ih.invoice_total) AS TotalRevenue
        FROM customer c
        INNER JOIN invoice_hdr ih ON c.customer_id = ih.customer_id
        WHERE c.delete_flag = 'N' AND c.active_flag = 'Y'
            AND ih.invoice_date >= DATEADD(year, -1, GETDATE())
        GROUP BY c.customer_id, c.customer_name
        ORDER BY TotalRevenue DESC";
    
    var customers = new List<Customer>();
    using var command = new SqlCommand(query, connection);
    using var reader = await command.ExecuteReaderAsync();
    
    while (await reader.ReadAsync())
    {
        customers.Add(new Customer
        {
            CustomerId = reader.GetString(0),
            CustomerName = reader.GetString(1),
            TotalRevenue = reader.GetDecimal(2)
        });
    }
    
    return customers;
}
```

---

## Troubleshooting

### "No microphone found"
- Check your system audio settings
- On Linux, you may need to install `portaudio`: `sudo apt install portaudio19-dev`

### "Database connection failed"
- Verify PostgreSQL is running: `pg_isready`
- Check your `DATABASE_URL` in `.env`

### "Whisper is slow"
- Use a smaller model: set `WHISPER_MODEL=tiny`
- For production, consider using an API-based transcription service

---

## 📚 Documentation

- **[Collaboration Guide](COLLABORATION_GUIDE.md)** - How agents work together
- **[Multi-Agent Architecture](MULTI_AGENT_ARCHITECTURE.md)** - System design
- **[Knowledge Base Guide](KNOWLEDGE_BASE_GUIDE.md)** - Adding documents
- **[SQL Generation Explained](SQL_GENERATION_EXPLAINED.md)** - AI reasoning
- **[Setup Guide](SETUP_GUIDE.md)** - Detailed setup instructions

## 🎨 Web UI Features

- **Real-time Agent Logging**: Watch agents collaborate live
- **Agent Badges**: See which agents are involved
- **Collaboration Mode Indicators**: Single, Sequential, or Parallel
- **Agent Discussions**: View each agent's contribution
- **Formatted Results**: SQL, code, and data beautifully displayed
- **Example Queries**: One-click examples for each agent

## 🔧 Key Features

✅ **Multi-Agent Collaboration** - Agents discuss and build on each other's insights  
✅ **Intelligent Routing** - AI determines which agents to involve  
✅ **Knowledge Base** - Each agent has domain-specific documentation  
✅ **Voice Input** - Speak your queries naturally  
✅ **Web UI** - Beautiful, real-time interface  
✅ **Safety First** - Read-only by default, validated queries  
✅ **Schema-Aware** - Understands your database structure  
✅ **Extensible** - Easy to add new agents  

## 🚀 Next Steps / Future Enhancements

- [ ] Add more specialized agents (Python, Java, etc.)
- [ ] Agent memory and learning
- [ ] Conversation history (multi-turn queries)
- [ ] Voice output of results
- [ ] Support for multiple database backends
- [ ] Agent performance metrics
- [ ] Custom agent configurations

## 🤝 Contributing

Contributions welcome! Areas of interest:
- New specialized agents
- Knowledge base documents
- UI improvements
- Performance optimizations

## 📄 License

MIT

---

**Built with:** Python, Flask, Anthropic Claude Sonnet 4, PostgreSQL, OpenAI Whisper
