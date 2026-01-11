# 🚀 Web UI Quick Start Guide

## What You Just Got

A **beautiful, interactive web interface** for your Voice-to-SQL Agent with:

✅ **Real-time agent logging** - Watch each step as it happens  
✅ **Clear instructions** - Built-in help and example queries  
✅ **One-click examples** - Click any example to try it  
✅ **Visual progress tracking** - Color-coded status updates  
✅ **Clean, modern design** - Professional gradient UI  
✅ **Formatted results** - SQL and results displayed beautifully  

---

## 🎯 How to Start the UI

### Option 1: Quick Start (One Command)

```bash
./start_ui.sh
```

Then open: **http://localhost:5000**

### Option 2: Manual Start

```bash
cd /Users/jonchristie/Desktop/playground/voice-to-sql
source venv/bin/activate
python web_ui.py
```

Then open: **http://localhost:5000**

---

## 📋 Before You Start

Make sure you've completed the database setup:

```bash
# Run the PostgreSQL setup script
./fix_postgres.sh

# OR manually set the database URL
export DATABASE_URL="postgresql://jonchristie:yourpassword@localhost:5432/voice_sql_test"

# Initialize the database
python scripts/init_db.py
```

---

## 🎨 UI Features

### 1. **Status Indicator**
   - **Green** ✅ = System ready (API key set, database connected)
   - **Red** ⚠️ = Configuration issue (check the message)

### 2. **Query Input Panel** (Left Side)
   - Type your natural language question
   - Click example queries to auto-fill
   - Press the blue button to execute
   - Test database connection with the gray button

### 3. **Agent Progress Log** (Right Side)
   - **Blue** = Information/status updates
   - **Yellow** = Agent working on a step
   - **Green** = Step completed successfully
   - **Red** = Error occurred

### 4. **Results Panel** (Bottom)
   - Shows your original question
   - Displays the generated SQL
   - Presents formatted query results

---

## 💡 Example Queries to Try

Click these in the UI or type them:

```
How many products do we have?
Show me all orders from last month
What are the top 5 customers by sales?
List products under $50
Which warehouses are low on inventory?
Show me all safety equipment
What's the total revenue by customer?
List orders for ABC Construction
Which products are out of stock?
Show me the most expensive products
```

---

## 🔍 What Happens When You Submit

Watch the log panel to see the agent work:

1. **[start]** - Query received
2. **[sql_generation]** - Claude AI generates SQL (blue → yellow → green)
3. **[execution]** - Query executed against PostgreSQL
4. **[complete]** - Pipeline finished
5. **Results displayed** - SQL and data shown below

---

## 🛠️ Troubleshooting

### "ANTHROPIC_API_KEY is not set"
```bash
export ANTHROPIC_API_KEY="your_key_here"
```

### "Database connection failed"
Run the database setup:
```bash
./fix_postgres.sh
```

### "No module named 'flask'"
Flask should be installed. If not:
```bash
./venv/bin/pip install flask
```

### UI won't load
Make sure port 5000 isn't in use:
```bash
lsof -ti:5000 | xargs kill -9  # Kill anything on port 5000
./start_ui.sh                   # Restart
```

---

## 🎬 Architecture Flow

```
┌─────────────────┐
│   Browser UI    │
│  (You type      │
│   question)     │
└────────┬────────┘
         │
         ↓ HTTP POST /api/query
┌─────────────────┐
│  Flask Server   │ ← Sends real-time logs via Server-Sent Events
│   (web_ui.py)   │
└────────┬────────┘
         │
         ↓ Calls orchestrator
┌─────────────────┐
│  Agent Pipeline │
│  • SQL Gen      │ ← Logs each step
│  • Execution    │ ← Real-time updates
│  • Formatting   │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   PostgreSQL    │
│   (Database)    │
└─────────────────┘
```

---

## 🎯 Keyboard Shortcuts

- **Ctrl + Enter** in the text area = Submit query

---

## 📁 UI Files Created

```
voice-to-sql/
├── web_ui.py               # Flask backend
├── start_ui.sh             # Startup script
├── templates/
│   └── index.html          # Web interface
└── UI_INSTRUCTIONS.md      # This file
```

---

## 🚀 Next Steps

1. **Start the UI**: `./start_ui.sh`
2. **Open browser**: http://localhost:5000
3. **Try an example**: Click any example query
4. **Watch the logs**: See the agent work in real-time
5. **View results**: SQL and data appear below

---

## 💡 Pro Tips

- The log panel updates in **real-time** - watch Claude generate SQL!
- Click **example queries** instead of typing
- Use **"Test Database Connection"** to verify setup
- The status indicator at the top shows system health
- **Ctrl+Enter** to quickly submit queries

---

**Have fun exploring your agentic AI system! 🎉**
