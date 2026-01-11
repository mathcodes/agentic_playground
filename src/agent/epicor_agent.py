"""
Epicor P21 Specialist Agent

This agent specializes in:
- Epicor P21 ERP system operations
- Data export and import processes
- P21 database schema and queries
- P21 API integration and usage
- ERP best practices
"""

import anthropic
from typing import Dict, Any, List, Optional
import os


class EpicorP21Agent:
    """Agent specialized in Epicor P21 ERP system"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Epicor P21 agent"""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"
        self.agent_name = "Epicor P21 Specialist"
        
    def process(
        self, 
        query: str, 
        knowledge_context: str = "",
        collaboration_context: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Process a query related to Epicor P21
        
        Args:
            query: User's question about Epicor P21
            knowledge_context: Relevant documents from knowledge base
            collaboration_context: Previous agent responses for collaboration
            
        Returns:
            Dict with response, code examples, suggestions, and collaboration info
        """
        # Build the system prompt
        system_prompt = self._build_system_prompt(knowledge_context)
        
        # Build the user message with collaboration context if available
        user_message = self._build_user_message(query, collaboration_context)
        
        try:
            # Call Claude API
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
            
            # Parse the response
            result = self._parse_response(response_text)
            result["agent"] = self.agent_name
            result["collaboration_enabled"] = collaboration_context is not None
            
            return result
            
        except Exception as e:
            return {
                "agent": self.agent_name,
                "success": False,
                "error": str(e),
                "response": f"Error processing Epicor P21 query: {str(e)}"
            }
    
    def _build_system_prompt(self, knowledge_context: str) -> str:
        """Build the system prompt for the Epicor P21 agent"""
        prompt = f"""You are an expert Epicor P21 ERP specialist with deep knowledge of:

1. **Epicor P21 ERP System**:
   - Business processes and workflows
   - Modules: Inventory, Sales, Purchasing, Manufacturing, Finance
   - Configuration and customization
   - Best practices and common patterns

2. **Data Export/Import**:
   - Export data from P21 to various formats (CSV, XML, JSON)
   - Import data into P21 safely
   - Data transformation and mapping
   - Scheduled exports and automation

3. **P21 Database**:
   - P21 database schema (SQL Server)
   - Key tables and relationships
   - Writing efficient queries against P21 data
   - Views and stored procedures
   - Data integrity and constraints

4. **P21 API Integration**:
   - P21 Web Services API
   - RESTful endpoints
   - Authentication and security
   - Common API operations (CRUD)
   - Error handling and retry logic
   - Rate limiting considerations

5. **ERP Best Practices**:
   - Data validation and quality
   - Performance optimization
   - Security considerations
   - Integration patterns
   - Change management

**Collaboration Mode**:
When working with other agents:
- Build upon insights from SQL, C#, or other agents
- Identify areas where P21-specific knowledge adds value
- Suggest when other agents' expertise would be helpful
- Provide clear handoff points for complex tasks

**Response Format**:
Structure your responses with:
- **Explanation**: Clear overview of the solution
- **P21 Context**: How this relates to P21 specifically
- **Code/Query**: Practical examples (SQL, C#, Python, etc.)
- **Best Practices**: P21-specific recommendations
- **Integration Notes**: How this connects to other systems
- **Collaboration**: When to involve other agents or need additional expertise

**Important**:
- Always consider P21 version compatibility
- Prioritize data integrity and business rule compliance
- Include error handling and validation
- Consider performance impact on production systems
- Mention when to involve P21 support or consultants"""

        if knowledge_context:
            prompt += f"\n\n**Knowledge Base Context**:\n{knowledge_context}"
        
        return prompt
    
    def _build_user_message(
        self, 
        query: str, 
        collaboration_context: Optional[List[Dict[str, str]]]
    ) -> str:
        """Build the user message with optional collaboration context"""
        message = f"User Query: {query}\n\n"
        
        if collaboration_context:
            message += "**Previous Agent Insights** (use these to build your response):\n\n"
            for context in collaboration_context:
                agent = context.get("agent", "Unknown Agent")
                response = context.get("response", "")
                message += f"--- {agent} ---\n{response}\n\n"
            
            message += "**Your Task**:\n"
            message += "Review the insights above and provide your Epicor P21 expertise. "
            message += "Build upon what others have said, add P21-specific context, and "
            message += "identify if other agents should be consulted for a complete solution.\n"
        
        return message
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the agent's response into structured format"""
        result = {
            "success": True,
            "response": response_text,
            "suggestions": []
        }
        
        # Extract code blocks if present
        if "```" in response_text:
            result["has_code"] = True
            # Extract code blocks
            code_blocks = []
            lines = response_text.split("```")
            for i in range(1, len(lines), 2):
                if i < len(lines):
                    code_blocks.append(lines[i].strip())
            result["code_blocks"] = code_blocks
        
        # Extract collaboration suggestions
        if "other agent" in response_text.lower() or "collaborate" in response_text.lower():
            result["suggests_collaboration"] = True
        
        # Extract next steps or recommendations
        if "next step" in response_text.lower() or "recommendation" in response_text.lower():
            result["has_recommendations"] = True
        
        return result
    
    def suggest_collaboration(self, query: str, current_response: str) -> List[str]:
        """
        Analyze if other agents should be involved
        
        Returns:
            List of agent names that might be helpful
        """
        suggested_agents = []
        
        query_lower = query.lower()
        response_lower = current_response.lower()
        
        # Check if SQL agent might help
        if any(word in query_lower for word in ["query", "select", "database", "table", "join"]):
            if "p21" in query_lower or "epicor" in query_lower:
                suggested_agents.append("SQL Agent")
        
        # Check if C# agent might help
        if any(word in query_lower for word in ["c#", "csharp", ".net", "api", "integration", "code"]):
            suggested_agents.append("C# Agent")
        
        # Check if response indicates need for collaboration
        if any(phrase in response_lower for phrase in ["would also need", "might also", "could use", "work with"]):
            # Could suggest specific agents based on context
            pass
        
        return suggested_agents


def create_epicor_agent(api_key: Optional[str] = None) -> EpicorP21Agent:
    """Factory function to create an Epicor P21 agent"""
    return EpicorP21Agent(api_key=api_key)
