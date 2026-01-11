"""
C# / .NET Specialized Agent
Handles questions about C# programming, .NET framework, and related technologies.
"""

import anthropic
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import config


CSHARP_SYSTEM_PROMPT = """You are an expert C# and .NET developer assistant.

Your expertise includes:
- C# language features (all versions up to C# 12)
- .NET Framework and .NET Core/.NET 6+
- ASP.NET Core (Web API, MVC, Blazor)
- Entity Framework Core
- LINQ (Language Integrated Query)
- Async/await patterns
- Dependency Injection
- Design patterns in C#
- Best practices and modern conventions

When answering:
1. Provide clear, concise explanations
2. Include code examples when relevant
3. Use modern C# features and best practices
4. Explain the "why" behind your recommendations
5. Format code with proper syntax highlighting hints

Keep responses focused and practical. If asked for code, provide complete, working examples."""


def process_csharp_query(user_query: str) -> dict:
    """
    Process a C#/.NET related query.
    
    Args:
        user_query: The user's question about C#/.NET
        
    Returns:
        dict with keys:
            - success: bool
            - response: str (the answer)
            - code_example: str (if code was generated)
            - error: str (if failed)
    """
    if not config.ANTHROPIC_API_KEY:
        return {
            'success': False,
            'response': None,
            'code_example': None,
            'error': 'ANTHROPIC_API_KEY not configured'
        }
    
    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        
        message = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=2048,
            system=CSHARP_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": user_query
                }
            ]
        )
        
        response_text = message.content[0].text
        
        # Try to extract code blocks
        code_example = None
        if '```csharp' in response_text or '```c#' in response_text:
            # Extract code blocks
            import re
            code_blocks = re.findall(r'```(?:csharp|c#)\n(.*?)```', response_text, re.DOTALL)
            if code_blocks:
                code_example = '\n\n'.join(code_blocks)
        
        return {
            'success': True,
            'response': response_text,
            'code_example': code_example,
            'error': None
        }
        
    except anthropic.APIError as e:
        return {
            'success': False,
            'response': None,
            'code_example': None,
            'error': f'API error: {e}'
        }
    except Exception as e:
        return {
            'success': False,
            'response': None,
            'code_example': None,
            'error': f'Error: {str(e)}'
        }


def generate_csharp_code(description: str, context: str = None) -> dict:
    """
    Generate C# code based on a description.
    
    Args:
        description: What the code should do
        context: Optional additional context (framework version, constraints, etc.)
        
    Returns:
        dict with generated code and explanation
    """
    prompt = f"Generate C# code for: {description}"
    if context:
        prompt += f"\n\nContext: {context}"
    
    prompt += "\n\nProvide complete, working code with comments."
    
    return process_csharp_query(prompt)


# Common C# patterns and examples
CSHARP_EXAMPLES = {
    "list": "How to create and use a List<T> in C#",
    "linq": "Common LINQ query examples",
    "async": "Async/await pattern examples",
    "di": "Dependency injection in ASP.NET Core",
    "ef": "Entity Framework Core basic setup",
    "api": "Create a simple ASP.NET Core Web API",
}


if __name__ == "__main__":
    # Test the C# agent
    test_queries = [
        "How do I create a List of strings in C#?",
        "Write a LINQ query to filter users older than 18",
        "Explain the difference between IEnumerable and IQueryable",
        "Create a simple ASP.NET Core controller",
    ]
    
    print("Testing C# Agent")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        
        result = process_csharp_query(query)
        
        if result['success']:
            print(result['response'])
            if result['code_example']:
                print("\nCode Example:")
                print(result['code_example'])
        else:
            print(f"Error: {result['error']}")
        
        print()
