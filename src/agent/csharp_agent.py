"""
C# / .NET Specialized Agent
Handles questions about C# programming, .NET framework, and related technologies.
Supports multi-agent collaboration.
"""

import anthropic
from typing import Dict, Any, List, Optional
import os


class CSharpAgent:
    """Agent specialized in C# and .NET development"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the C# agent"""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"
        self.agent_name = "C# Specialist"
    
    def process(
        self, 
        query: str, 
        knowledge_context: str = "",
        collaboration_context: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Process a C#/.NET query
        
        Args:
            query: User's question about C#/.NET
            knowledge_context: Relevant documents from knowledge base
            collaboration_context: Previous agent responses for collaboration
            
        Returns:
            Dict with response, code examples, and collaboration info
        """
        system_prompt = self._build_system_prompt(knowledge_context, collaboration_context)
        user_message = self._build_user_message(query, collaboration_context)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": user_message
                }]
            )
            
            response_text = response.content[0].text
            
            # Extract code blocks
            code_example = None
            if '```csharp' in response_text or '```c#' in response_text:
                import re
                code_blocks = re.findall(r'```(?:csharp|c#)\n(.*?)```', response_text, re.DOTALL)
                if code_blocks:
                    code_example = '\n\n'.join(code_blocks)
            
            return {
                "agent": self.agent_name,
                "success": True,
                "response": response_text,
                "code_example": code_example,
                "has_code": code_example is not None,
                "collaboration_enabled": collaboration_context is not None
            }
            
        except Exception as e:
            return {
                "agent": self.agent_name,
                "success": False,
                "error": str(e),
                "response": f"Error processing C# query: {str(e)}"
            }
    
    def _build_system_prompt(self, knowledge_context: str, collaboration_context: Optional[List[Dict[str, str]]]) -> str:
        """Build the system prompt"""
        prompt = """You are an expert C# and .NET developer assistant.

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

        if collaboration_context:
            prompt += """

**Collaboration Mode**:
You are working with other specialist agents. Review their insights and build upon them with your C#/.NET expertise.
- Add value with C#-specific knowledge
- Reference other agents' contributions when relevant
- Suggest when additional expertise might be needed"""

        if knowledge_context:
            prompt += f"\n\n**Knowledge Base Context**:\n{knowledge_context}"
        
        return prompt
    
    def _build_user_message(self, query: str, collaboration_context: Optional[List[Dict[str, str]]]) -> str:
        """Build the user message with optional collaboration context"""
        message = f"User Query: {query}\n\n"
        
        if collaboration_context:
            message += "**Previous Agent Insights**:\n\n"
            for context in collaboration_context:
                agent = context.get("agent", "Unknown Agent")
                response = context.get("response", "")
                message += f"--- {agent} ---\n{response}\n\n"
            
            message += "**Your Task**: Provide your C#/.NET expertise, building upon the insights above.\n"
        
        return message


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
