# 📚 Knowledge Base System Guide

## Overview

Your agents now have **persistent knowledge bases** - collections of documents they can reference when answering questions!

```
knowledge_base/
├── sql/           # SQL Agent's documents
├── csharp/        # C# Agent's documents
└── shared/        # Shared across all agents
```

---

## 🎯 How It Works

### 1. **Document Storage**
Each agent has its own folder with markdown files containing specialized knowledge:

```
knowledge_base/
├── sql/
│   ├── database_best_practices.md
│   ├── query_optimization.md
│   └── common_patterns.md
│
├── csharp/
│   ├── linq_patterns.md
│   ├── async_await_patterns.md
│   └── entity_framework_tips.md
│
└── shared/
    └── common_errors.md
```

### 2. **Retrieval System**
When a query comes in, the system:
1. Searches the relevant agent's knowledge base
2. Finds the most relevant documents
3. Injects them into the agent's prompt as context

```python
# Example flow
user_query = "How do I write a LINQ query?"

# System searches csharp/ folder
relevant_docs = knowledge_base.search("csharp", "LINQ query")

# Adds to prompt
prompt = f"""
{relevant_docs}

User Question: {user_query}
"""
```

---

## 📂 File Organization

### Markdown Format
All knowledge base documents use markdown (`.md`) for easy editing:

```markdown
# Title

## Section

Content here with code examples:

```language
code here
```

### Naming Convention
- Use descriptive filenames: `linq_patterns.md` not `doc1.md`
- Use underscores: `async_await_patterns.md`
- Keep titles clear and searchable

---

## 🔍 Retrieval Methods

### Method 1: Simple Keyword Search (Current)

**How it works:**
```python
kb = KnowledgeBase()
results = kb.search_docs('csharp', 'LINQ query', max_results=3)
```

- Searches filenames and content for keywords
- Scores matches based on frequency
- Fast and simple
- No external dependencies

**Best for:**
- Small to medium knowledge bases (< 100 docs)
- Well-organized documents with clear titles
- Direct keyword matches

### Method 2: Semantic Search (Advanced)

**How it works:**
```python
kb = VectorKnowledgeBase(use_embeddings=True)
results = kb.search_semantic('csharp', 'filter data by condition', max_results=3)
```

- Uses AI embeddings to understand meaning
- Finds semantically similar content
- Matches concepts, not just keywords
- Requires `sentence-transformers` library

**Best for:**
- Large knowledge bases (100+ docs)
- Conceptual searches
- When users don't know exact terms

### Installing Semantic Search

```bash
pip install sentence-transformers
```

Then update your code:
```python
from src.knowledge.retriever import VectorKnowledgeBase

kb = VectorKnowledgeBase(use_embeddings=True)
```

---

## 📝 Adding New Documents

### Option 1: Manual Creation

Create a new file in the appropriate folder:

```bash
# For SQL agent
nano knowledge_base/sql/window_functions.md

# For C# agent
nano knowledge_base/csharp/dependency_injection.md
```

### Option 2: Programmatic Addition

```python
from src.knowledge.retriever import KnowledgeBase

kb = KnowledgeBase()

content = """
# Dependency Injection in ASP.NET Core

## Constructor Injection
```csharp
public class UserController : ControllerBase
{
    private readonly IUserService _userService;
    
    public UserController(IUserService userService)
    {
        _userService = userService;
    }
}
```
"""

kb.add_document('csharp', 'Dependency Injection', content)
```

---

## 🔗 Integration with Agents

### SQL Agent Integration

```python
# In src/sql/generator.py

from src.knowledge.retriever import KnowledgeBase

kb = KnowledgeBase()

def generate_sql(query: str):
    # Get relevant context
    context = kb.get_context_for_query('sql', query)
    
    # Build enhanced prompt
    prompt = f"""
    {SYSTEM_PROMPT}
    
    {context}  # Relevant docs injected here
    
    User question: {query}
    """
```

### C# Agent Integration

```python
# In src/agent/csharp_agent.py

from src.knowledge.retriever import KnowledgeBase

kb = KnowledgeBase()

def process_csharp_query(query: str):
    # Get relevant context
    context = kb.get_context_for_query('csharp', query)
    
    # Enhanced system prompt
    system = f"""
    {CSHARP_SYSTEM_PROMPT}
    
    {context}  # Relevant docs injected here
    """
```

---

## 📊 Document Structure Best Practices

### 1. **Start with Clear Titles**
```markdown
# LINQ Query Patterns
```

### 2. **Use Sections**
```markdown
## Filtering
## Projecting
## Ordering
```

### 3. **Include Code Examples**
```markdown
### Example: Filter by Age
```csharp
var adults = users.Where(u => u.Age >= 18).ToList();
```
```

### 4. **Add Context**
```markdown
**When to use:** For filtering collections based on conditions
**Best practice:** Always specify the condition clearly
```

### 5. **Cross-Reference**
```markdown
See also: `async_await_patterns.md` for async LINQ operations
```

---

## 🎯 Example Use Cases

### Use Case 1: SQL Best Practices

**Document:** `sql/database_best_practices.md`

When user asks: "What's the best way to query products?"

System retrieves and injects:
```
RELEVANT KNOWLEDGE BASE:

## Query Optimization
- Always use indexes on WHERE clauses
- Use LIMIT to restrict results
- Avoid SELECT *
```

### Use Case 2: LINQ Patterns

**Document:** `csharp/linq_patterns.md`

When user asks: "How do I filter a list in C#?"

System retrieves and injects:
```
RELEVANT KNOWLEDGE BASE:

### Filtering with Where
```csharp
var filtered = list.Where(x => x.Property == value).ToList();
```
```

### Use Case 3: Async Patterns

**Document:** `csharp/async_await_patterns.md`

When user asks: "Explain async await"

System retrieves and injects full patterns and examples.

---

## 🚀 Advanced: Vector Embeddings

### Why Use Embeddings?

**Keyword Search:**
- User: "filter data by condition"
- Matches: documents containing "filter", "condition"
- Misses: documents about `Where()` that don't use those words

**Semantic Search:**
- User: "filter data by condition"
- Matches: documents about LINQ Where, filtering, predicates
- Understands concepts, not just words

### Setup

1. Install dependencies:
```bash
pip install sentence-transformers
```

2. Update your agents:
```python
from src.knowledge.retriever import VectorKnowledgeBase

kb = VectorKnowledgeBase(use_embeddings=True)
```

3. First run will download the embedding model (~80MB)

### Performance

- **First search:** ~1-2 seconds (loads model)
- **Subsequent searches:** ~100-300ms
- **Memory:** ~400MB for model
- **Accuracy:** Much better than keywords

---

## 📈 Scaling Your Knowledge Base

### Small (< 20 docs)
- Use keyword search
- No special requirements
- Manual organization

### Medium (20-100 docs)
- Use keyword search
- Organize into subfolders
- Clear naming conventions

### Large (100+ docs)
- Use semantic search (embeddings)
- Consider vector database (Pinecone, Weaviate)
- Implement document versioning

---

## 🔧 Maintenance

### Regular Updates
```bash
# Update existing document
nano knowledge_base/csharp/linq_patterns.md

# Git commit
git add knowledge_base/
git commit -m "Updated LINQ patterns with new examples"
```

### Testing Retrieval
```python
# Test what docs are found
kb = KnowledgeBase()
results = kb.search_docs('csharp', 'LINQ')

for result in results:
    print(f"{result['title']}: score={result['relevance_score']}")
```

### Monitoring
- Log which documents are retrieved most often
- Identify gaps in knowledge base
- Add documents for frequently asked topics

---

## 💡 Tips for Great Documents

1. **Be Specific:** Focus each document on one topic
2. **Use Examples:** Code examples are most valuable
3. **Keep Updated:** Revise when technologies change
4. **Cross-Reference:** Link related documents
5. **Test Retrieval:** Make sure docs are findable

---

## 🎯 Starter Documents Included

### SQL Agent (`sql/`)
- ✅ `database_best_practices.md` - Query optimization, indexing
- Ready to add: Connection pooling, transaction patterns, migrations

### C# Agent (`csharp/`)
- ✅ `linq_patterns.md` - All LINQ operations
- ✅ `async_await_patterns.md` - Async/await best practices
- Ready to add: EF Core, DI, testing, design patterns

### Shared (`shared/`)
- ✅ `common_errors.md` - Common mistakes and solutions
- Ready to add: Security best practices, performance tips

---

## 🔮 Future Enhancements

1. **RAG (Retrieval Augmented Generation)**
   - Automatically cite sources
   - Show which document was used

2. **Document Versioning**
   - Track changes over time
   - Rollback if needed

3. **Multi-Modal**
   - Add images/diagrams
   - Video transcripts

4. **Collaborative Editing**
   - Team contributions
   - Review process

---

## 📚 Summary

**Current Setup:**
- ✅ Organized folder structure
- ✅ Markdown documents
- ✅ Simple keyword search
- ✅ Easy to add new docs
- ✅ Integrates with agents

**To Upgrade:**
- Install `sentence-transformers` for semantic search
- Add more documents as you encounter new topics
- Monitor what users ask to identify knowledge gaps

**Your agents are now smarter with persistent knowledge!** 🧠

---

**Try it:** Add a document and ask a related question to see it in action!
