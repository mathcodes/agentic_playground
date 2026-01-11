# Voice-to-SQL Agent

An agentic AI application that converts spoken natural language into SQL queries and executes them against a database.

## Overview

This application:
1. **Captures audio** from your microphone (or accepts audio files)
2. **Transcribes speech** to text using OpenAI Whisper
3. **Interprets intent** and generates SQL using an LLM (Claude)
4. **Executes queries** against a PostgreSQL database
5. **Returns results** in a human-readable format

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

## Quick Start

```bash
# Clone and enter project
cd voice-to-sql

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Initialize the database
python scripts/init_db.py

# Run the app
python main.py
```

---

## Project Structure

```
voice-to-sql/
├── README.md
├── requirements.txt
├── .env.example
├── main.py                 # Entry point
├── config.py               # Configuration management
├── scripts/
│   └── init_db.py          # Database initialization
├── src/
│   ├── __init__.py
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── capture.py      # Microphone input
│   │   └── transcribe.py   # Speech-to-text (Whisper)
│   ├── sql/
│   │   ├── __init__.py
│   │   ├── generator.py    # LLM-based SQL generation
│   │   ├── executor.py     # Safe query execution
│   │   └── schema.py       # Schema introspection
│   └── agent/
│       ├── __init__.py
│       └── orchestrator.py # Main agent logic
└── tests/
    └── ...
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

## Example Usage

```
🎤 Listening... (speak your query, then pause)

You said: "Show me all products under fifty dollars"

Generated SQL:
  SELECT * FROM products WHERE price < 50;

Results:
  ┌────┬──────────────────┬───────┬──────────┐
  │ id │ name             │ price │ category │
  ├────┼──────────────────┼───────┼──────────┤
  │ 3  │ Safety Glasses   │ 12.99 │ PPE      │
  │ 7  │ Work Gloves      │ 8.50  │ PPE      │
  │ 12 │ Cable Ties (100) │ 4.99  │ Supplies │
  └────┴──────────────────┴───────┴──────────┘
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

## Next Steps / Future Enhancements

- [ ] Add conversation memory (multi-turn queries)
- [ ] Support for query refinement ("show me only the first 5")
- [ ] Voice output of results
- [ ] Web UI interface
- [ ] Support for multiple database backends

---

## License

MIT
