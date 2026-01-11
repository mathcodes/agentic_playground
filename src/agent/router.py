"""
Router Agent - Determines which specialized agent to use.
Analyzes user input and routes to SQL or C#/.NET agent.
"""

import anthropic
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import config


ROUTER_PROMPT = """You are a routing agent that classifies user queries into categories.

Analyze the user's question and determine if it's about:
1. **SQL/Database** - Questions about querying data, database operations, SQL syntax
2. **C#/.NET** - Questions about C# code, .NET framework, ASP.NET, LINQ, etc.

Respond with ONLY one word: "SQL" or "CSHARP"

Examples:
- "How many products are in the database?" → SQL
- "Show me all orders from last month" → SQL
- "How do I create a List in C#?" → CSHARP
- "Write a LINQ query to filter users" → CSHARP
- "What's the difference between IEnumerable and IQueryable?" → CSHARP
- "Create an ASP.NET Core controller" → CSHARP
- "Get the top 5 customers by revenue" → SQL

Remember: Respond with ONLY "SQL" or "CSHARP", nothing else."""


def route_query(user_input: str) -> dict:
    """
    Route the query to the appropriate agent.
    
    Args:
        user_input: The user's natural language question
        
    Returns:
        dict with keys:
            - agent: str ("sql" or "csharp")
            - confidence: str (reasoning from Claude)
            - error: str (if routing failed)
    """
    if not config.ANTHROPIC_API_KEY:
        return {
            'agent': 'sql',  # Default fallback
            'confidence': 'No API key, defaulting to SQL',
            'error': 'ANTHROPIC_API_KEY not configured'
        }
    
    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        
        message = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=50,
            system=ROUTER_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": user_input
                }
            ]
        )
        
        response = message.content[0].text.strip().upper()
        
        # Parse response
        if 'SQL' in response:
            return {
                'agent': 'sql',
                'confidence': 'High - SQL/Database query detected',
                'error': None
            }
        elif 'CSHARP' in response or 'C#' in response:
            return {
                'agent': 'csharp',
                'confidence': 'High - C#/.NET query detected',
                'error': None
            }
        else:
            # Default to SQL if unclear
            return {
                'agent': 'sql',
                'confidence': f'Unclear response: {response}, defaulting to SQL',
                'error': None
            }
            
    except Exception as e:
        return {
            'agent': 'sql',  # Default fallback
            'confidence': 'Error occurred, defaulting to SQL',
            'error': str(e)
        }


if __name__ == "__main__":
    # Test the router
    test_queries = [
        "How many products do we have?",
        "Show me all orders from last month",
        "How do I create a List<string> in C#?",
        "Write a LINQ query to filter users by age",
        "What's the difference between IEnumerable and IQueryable?",
        "Get the top 5 customers by revenue",
        "Create an ASP.NET Core Web API controller",
        "How do I use Entity Framework Core?",
    ]
    
    print("Testing Router Agent")
    print("=" * 60)
    
    for query in test_queries:
        result = route_query(query)
        print(f"\nQuery: {query}")
        print(f"  → Agent: {result['agent'].upper()}")
        print(f"  → Confidence: {result['confidence']}")
        if result['error']:
            print(f"  → Error: {result['error']}")
