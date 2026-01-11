# 🤖 Multi-Agent Architecture

## Overview

This application now uses a **multi-agent system** with specialized agents for different types of queries:

```
User Query → Router Agent → [ SQL Agent | C#/.NET Agent ] → Response
```

---

## 🎯 The Three Agents

### 1. **Router Agent** (`src/agent/router.py`)

**Role:** Classifier / Traffic Director

**What it does:**
- Analyzes the user's input
- Determines if it's a SQL/database question or a C#/.NET question
- Routes to the appropriate specialized agent

**How it works:**
```python
def route_query(user_input: str) -> dict:
    # Uses Claude to classify the query
    response = claude.classify(user_input)
    
    if "SQL" in response:
        return {'agent': 'sql'}
    elif "CSHARP" in response:
        return {'agent': 'csharp'}
```

**Example classifications:**
- "How many products?" → **SQL Agent**
- "Show me all orders" → **SQL Agent**
- "How do I create a List in C#?" → **C# Agent**
- "Write a LINQ query" → **C# Agent**
- "Explain async/await" → **C# Agent**

---

### 2. **SQL Agent** (`src/agent/orchestrator.py`)

**Role:** Database Query Specialist

**Capabilities:**
- Converts natural language to SQL
- Understands database schema
- Executes queries safely
- Formats results

**Technology:**
- Claude Sonnet 4 for SQL generation
- PostgreSQL for query execution
- Schema introspection for context

**Example:**
```
Input:  "How many products do we have?"
Output: SELECT COUNT(*) as product_count FROM products;
Result: 48 products
```

---

### 3. **C#/.NET Agent** (`src/agent/csharp_agent.py`)

**Role:** C# and .NET Expert

**Capabilities:**
- Answers C# programming questions
- Generates C# code examples
- Explains .NET concepts
- Provides best practices

**Expertise Areas:**
- C# language features (all versions)
- .NET Core/.NET 6+
- ASP.NET Core (Web API, MVC, Blazor)
- Entity Framework Core
- LINQ
- Async/await patterns
- Dependency Injection
- Design patterns

**Example:**
```
Input:  "How do I create a List of strings in C#?"
Output: 
  To create a List<string> in C#:
  
  ```csharp
  // Using collection initializer
  List<string> names = new List<string> 
  { 
      "Alice", 
      "Bob", 
      "Charlie" 
  };
  
  // Using Add method
  List<string> cities = new List<string>();
  cities.Add("New York");
  cities.Add("London");
  ```
```

---

## 🔄 The Complete Flow

### Step 1: User Input
```
User: "Write a LINQ query to filter users by age"
```

### Step 2: Router Analysis
```python
router_agent.classify(query)
# Analyzes keywords: "LINQ", "query" → C# related
# Decision: Route to C# Agent
```

### Step 3: Specialized Processing
```python
if agent_type == 'csharp':
    result = csharp_agent.process_query(query)
    # Claude generates C# code and explanation
```

### Step 4: Response Formatting
```
Agent: C#/.NET Agent
Response: Here's how to filter users by age using LINQ...
Code: var adults = users.Where(u => u.Age >= 18).ToList();
```

---

## 📊 Architecture Diagram

```
┌─────────────────┐
│   User Input    │
│  "LINQ query?"  │
└────────┬────────┘
         │
         ↓
┌─────────────────────────┐
│    Router Agent         │
│  (Claude Classifier)    │
│  Analyzes: SQL vs C#    │
└────────┬────────────────┘
         │
         ├─ SQL? ────────→ ┌──────────────────┐
         │                 │   SQL Agent      │
         │                 │  • Schema context│
         │                 │  • SQL generation│
         │                 │  • Query exec    │
         │                 └──────────────────┘
         │
         └─ C#? ─────────→ ┌──────────────────┐
                           │  C#/.NET Agent   │
                           │  • Code gen      │
                           │  • Explanation   │
                           │  • Best practices│
                           └──────────────────┘
```

---

## 🎨 Multi-Agent Orchestrator

**File:** `src/agent/multi_agent_orchestrator.py`

The orchestrator coordinates all agents:

```python
class MultiAgentOrchestrator:
    def __init__(self):
        self.sql_agent = VoiceToSQLAgent()
        # C# agent is stateless, called as needed
    
    def process_query(self, query: str) -> MultiAgentResult:
        # 1. Route the query
        routing = route_query(query)
        
        # 2. Use appropriate agent
        if routing['agent'] == 'sql':
            return self._process_with_sql_agent(query)
        else:
            return self._process_with_csharp_agent(query)
```

---

## 🔍 How the Router Works

### Prompt to Claude

```
You are a routing agent. Classify queries as:
1. SQL/Database - questions about data, queries, databases
2. C#/.NET - questions about C# code, .NET framework

Examples:
- "How many products?" → SQL
- "Create a List in C#?" → CSHARP

Respond with ONLY: "SQL" or "CSHARP"
```

### Classification Logic

```python
# Claude analyzes the query
response = claude.classify(user_query)

# Parse the response
if 'SQL' in response:
    agent = 'sql'
elif 'CSHARP' in response:
    agent = 'csharp'
else:
    agent = 'sql'  # Default fallback
```

---

## 💡 Why Multi-Agent?

### Benefits

1. **Specialization**
   - Each agent is expert in its domain
   - Better, more accurate responses

2. **Scalability**
   - Easy to add new agents (Python, Java, etc.)
   - Modular architecture

3. **Context Optimization**
   - SQL agent gets database schema
   - C# agent gets .NET knowledge
   - No context pollution

4. **Better User Experience**
   - One interface for multiple capabilities
   - Automatic routing (no manual selection)

---

## 🧪 Testing the Multi-Agent System

### Test Script

```python
orchestrator = MultiAgentOrchestrator()

# SQL query
result = orchestrator.process_query("How many orders?")
# → Routes to SQL Agent → Generates SQL → Executes

# C# query
result = orchestrator.process_query("Explain LINQ")
# → Routes to C# Agent → Generates explanation + code
```

### In the Web UI

The UI now handles both agent types:

**SQL Response:**
```
📝 Your Question: How many products?
🔍 Generated SQL: SELECT COUNT(*) FROM products;
📊 Results: 48 products
```

**C# Response:**
```
📝 Your Question: How do I create a List in C#?
💡 C# Expert Response: [Explanation]
💻 Code Example: List<string> items = new List<string>();
```

---

## 🎯 Example Queries for Each Agent

### SQL Agent Examples

```
✅ "How many products do we have?"
✅ "Show me all orders from last month"
✅ "What are the top 5 customers by sales?"
✅ "List products under $50"
✅ "Which warehouses are low on inventory?"
```

### C# Agent Examples

```
✅ "How do I create a List in C#?"
✅ "Write a LINQ query to filter users by age"
✅ "Explain async/await in C#"
✅ "Create an ASP.NET Core Web API controller"
✅ "What's the difference between IEnumerable and IQueryable?"
✅ "How do I use dependency injection in .NET?"
✅ "Generate a C# class for a Product entity"
```

---

## 🔧 Configuration

No special configuration needed! The multi-agent system uses the same `ANTHROPIC_API_KEY`:

```python
# config.py
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
```

All agents use Claude Sonnet 4 with specialized prompts.

---

## 📈 Performance

### Routing
- **Time:** ~200-500ms
- **Tokens:** ~50-100 input, ~10 output
- **Cost:** <$0.001 per route

### SQL Agent
- **Time:** ~2-4 seconds
- **Tokens:** ~2000-3000 input, ~50-200 output
- **Cost:** ~$0.01-0.03 per query

### C# Agent
- **Time:** ~2-5 seconds
- **Tokens:** ~1000-2000 input, ~500-2000 output
- **Cost:** ~$0.02-0.05 per query

---

## 🚀 Future Enhancements

Easily add more specialized agents:

```python
# Future additions:
class PythonAgent:
    """Python programming expert"""
    
class JavaAgent:
    """Java programming expert"""
    
class DevOpsAgent:
    """CI/CD, Docker, Kubernetes expert"""
```

Update the router to handle new agent types:

```python
# router.py
ROUTER_PROMPT = """
Classify as: SQL, CSHARP, PYTHON, JAVA, or DEVOPS
"""
```

---

## 🎯 Key Files

```
voice-to-sql/
├── src/agent/
│   ├── router.py                 # NEW: Routing logic
│   ├── csharp_agent.py           # NEW: C#/.NET specialist
│   ├── multi_agent_orchestrator.py  # NEW: Coordinates agents
│   └── orchestrator.py           # EXISTING: SQL agent
│
├── web_ui.py                     # UPDATED: Multi-agent support
└── templates/index.html          # UPDATED: C# response display
```

---

## 💡 The Power of Multi-Agent Systems

This architecture demonstrates key AI agent patterns:

1. **Divide and Conquer** - Each agent masters one domain
2. **Intelligent Routing** - AI decides which expert to use
3. **Composability** - Agents work together seamlessly
4. **Extensibility** - Easy to add new capabilities

**You now have an agentic AI system that can:**
- ✅ Generate SQL from natural language
- ✅ Answer C# programming questions
- ✅ Generate C# code examples
- ✅ Automatically route to the right expert
- ✅ All through one unified interface!

---

This is the future of AI assistants: **specialized agents working together** to provide expert help across multiple domains! 🚀
