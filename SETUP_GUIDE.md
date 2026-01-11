# Voice-to-SQL Setup Guide

## Current Status

✅ **Completed:**
- PostgreSQL is installed and running
- Python 3.9 is available  
- Virtual environment created
- All Python dependencies installed (torch, whisper, anthropic, etc.)

⚠️ **Issue:** PostgreSQL authentication needs configuration

---

## PostgreSQL Authentication Setup

Your PostgreSQL installation requires password authentication. Here are two options:

### Option 1: Set Password for Current User (Recommended)

Run these commands in your terminal:

```bash
# First, temporarily allow trust authentication
sudo sed -i.backup 's/md5/trust/g' /usr/local/var/postgresql@15/pg_hba.conf

# Restart PostgreSQL
brew services restart postgresql@15

# Set a password for your user
psql postgres -c "ALTER USER jonchristie WITH PASSWORD 'postgres';"

# Create the database
psql postgres -c "CREATE DATABASE voice_sql_test;"

# Restore md5 authentication (optional for security)
sudo sed -i '' 's/trust/md5/g' /usr/local/var/postgresql@15/pg_hba.conf
brew services restart postgresql@15
```

### Option 2: Use Environment Variable

Set the database URL with password:

```bash
export DATABASE_URL="postgresql://jonchristie:postgres@localhost:5432/voice_sql_test"
```

Then run the initialization:

```bash
cd /Users/jonchristie/Desktop/playground/voice-to-sql
source venv/bin/activate
python scripts/init_db.py
```

---

## Quick Start (After Database Setup)

1. **Set your Anthropic API key:**
   ```bash
   export ANTHROPIC_API_KEY="your_key_here"
   ```

2. **Run tests:**
   ```bash
   python main.py --test
   ```

3. **Try text mode (no microphone needed):**
   ```bash
   python main.py --text "How many products do we have?"
   ```

4. **Interactive text mode:**
   ```bash
   python main.py --text-mode
   ```

5. **Full voice mode:**
   ```bash
   python main.py
   ```

---

## Alternative: Quick Demo Without Database Setup

You can test the SQL generation without database by checking the LLM integration:

```bash
source venv/bin/activate
export ANTHROPIC_API_KEY="your_key_here"

# Test SQL generation only
python -c "
from src.sql.generator import generate_sql
result = generate_sql('Show me all products under 50 dollars')
print(f'Generated SQL: {result[\"sql\"]}')
"
```

---

## Architecture Overview

```
Voice/Text Input → Whisper (STT) → Claude (SQL Gen) → PostgreSQL → Formatted Output
```

**Agent Pipeline:**
1. **Audio Capture** (`src/audio/capture.py`) - Voice activity detection
2. **Transcription** (`src/audio/transcribe.py`) - Whisper local model
3. **SQL Generation** (`src/sql/generator.py`) - Claude Sonnet 4  
4. **Schema Context** (`src/sql/schema.py`) - Database introspection
5. **Safe Execution** (`src/sql/executor.py`) - Read-only by default
6. **Orchestration** (`src/agent/orchestrator.py`) - Coordinates full pipeline

**Safety Features:**
- Read-only queries by default
- SQL injection prevention
- Query validation before execution
- Result limiting (100 rows default)

---

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
Get your key from https://console.anthropic.com/ and set it as an environment variable.

### "No microphone found"
On macOS, grant microphone permissions in System Preferences → Security & Privacy → Microphone.

### Whisper is slow
Use a smaller model: `export WHISPER_MODEL=tiny`

---

## Project Files

- `main.py` - Entry point with CLI
- `config.py` - Configuration management
- `src/agent/orchestrator.py` - Main agent logic
- `src/sql/generator.py` - LLM-powered SQL generation
- `src/audio/transcribe.py` - Speech-to-text
- `scripts/init_db.py` - Database initialization

