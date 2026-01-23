"""
Router Agent - Multi-Agent Classification and Orchestration

This agent analyzes user queries and determines:
1. Which agent(s) should handle the query
2. Whether multiple agents should collaborate
3. The order of agent involvement
"""

import anthropic
from typing import Dict, Any, List
import os


class RouterAgent:
    """Routes queries to appropriate specialist agent(s) and manages collaboration"""
    
    def __init__(self, api_key: str = None):
        """Initialize the router agent"""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"
        
        # Available agents
        # ENHANCEMENT: Added general agent for conversational queries that don't require specialized expertise
        self.available_agents = {
            "sql": {
                "name": "SQL Agent",
                "expertise": ["database queries", "SQL", "data retrieval", "schema", "postgresql", "database design", "select", "join", "where"],
                "description": "Converts natural language to SQL queries and executes them"
            },
            "csharp": {
                "name": "C# Agent",
                "expertise": ["c#", "csharp", ".net", "programming", "linq", "async", "await", "code examples", "entity framework", "asp.net"],
                "description": "Provides C# and .NET programming help, code generation, and explanations"
            },
            "epicor": {
                "name": "Epicor P21 Agent",
                "expertise": ["epicor", "p21", "erp", "export", "import", "p21 api", "p21 database", "erp integration"],
                "description": "Specializes in Epicor P21 ERP system, exports, database, and API integration"
            },
            "general": {
                "name": "General AI Chat Agent",
                "expertise": ["general", "explain", "what is", "how do", "help", "question", "discussion", "brainstorm", "advice"],
                "description": "Handles general conversational queries, explanations, and questions that don't require specialized technical expertise"
            }
        }
    
    def route(self, query: str) -> Dict[str, Any]:
        """
        Analyze query and determine routing strategy
        
        Returns:
            Dict with:
                - primary_agent: Main agent to handle query
                - supporting_agents: List of agents that should collaborate
                - collaboration_mode: 'sequential', 'parallel', or 'single'
                - reasoning: Explanation of routing decision
        """
        try:
            # Build the routing prompt
            system_prompt = self._build_routing_prompt()
            user_message = f"Analyze this query and determine routing:\n\nQuery: {query}"
            
            # Call Claude to analyze the query
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": user_message
                }]
            )
            
            response_text = response.content[0].text
            
            # Parse the routing decision
            routing = self._parse_routing_response(response_text, query)
            
            return routing
            
        except Exception as e:
            # ENHANCEMENT: Default to general agent on error (more appropriate for unknown queries)
            return {
                "primary_agent": "general",
                "supporting_agents": [],
                "collaboration_mode": "single",
                "reasoning": f"Error in routing, defaulting to general agent: {str(e)}",
                "confidence": "low"
            }
    
    def _build_routing_prompt(self) -> str:
        """Build the system prompt for routing decisions"""
        agents_desc = "\n".join([
            f"- **{info['name']}**: {info['description']}\n  Expertise: {', '.join(info['expertise'])}"
            for info in self.available_agents.values()
        ])
        
        return f"""You are an intelligent routing agent that analyzes user queries and determines the best agent(s) to handle them.

**Available Agents**:
{agents_desc}

**Routing Modes**:
1. **Single Agent**: One agent can fully handle the query
2. **Sequential Collaboration**: Agents work in order, each building on previous responses
3. **Parallel Collaboration**: Multiple agents work simultaneously, then synthesize results

**Analysis Guidelines**:

1. **Identify Query Intent**: What is the user really asking for?

2. **Match to Expertise**: Which agent(s) have the relevant knowledge?

3. **Consider Complexity**: 
   - Simple, focused queries → Single agent
   - Queries spanning multiple domains → Collaboration
   - Queries needing integration → Sequential collaboration
   
4. **Common Collaboration Scenarios**:
   - P21 + SQL: Querying Epicor P21 database directly
   - P21 + C#: Building P21 integrations or APIs
   - SQL + C#: Database operations with C# code
   - All three: Complete P21 integration solution with database and code

**Response Format** (STRICT - must follow this format):
```
PRIMARY: <agent_key>
SUPPORTING: <comma-separated agent_keys or "none">
MODE: <single|sequential|parallel>
CONFIDENCE: <high|medium|low>
REASONING: <one sentence explanation>
```

**Examples**:

Query: "Show me all customers"
```
PRIMARY: sql
SUPPORTING: none
MODE: single
CONFIDENCE: high
REASONING: Simple database query, SQL agent can handle alone
```

Query: "What is the difference between AI and ML?"
```
PRIMARY: general
SUPPORTING: none
MODE: single
CONFIDENCE: high
REASONING: General knowledge question, no specialized technical expertise needed
```

Query: "How do I export P21 sales data using C#?"
```
PRIMARY: epicor
SUPPORTING: csharp, sql
MODE: sequential
CONFIDENCE: high
REASONING: P21 export is primary need, C# for implementation, SQL for query structure
```

Query: "Write async code to query database"
```
PRIMARY: csharp
SUPPORTING: sql
MODE: sequential
CONFIDENCE: high
REASONING: C# async is primary, SQL for query syntax support
```

Query: "Build a P21 integration API with database caching"
```
PRIMARY: epicor
SUPPORTING: csharp, sql
MODE: sequential
CONFIDENCE: medium
REASONING: Complex integration requiring P21, API code, and database knowledge
```

Query: "Explain best practices for team productivity"
```
PRIMARY: general
SUPPORTING: none
MODE: single
CONFIDENCE: high
REASONING: General business question, no technical specialization required
```

Remember: More agents = better coverage but slower response. Only use collaboration when truly beneficial. Use the general agent for conversational queries, explanations, and general advice."""
    
    def _parse_routing_response(self, response_text: str, query: str) -> Dict[str, Any]:
        """Parse Claude's routing decision"""
        result = {
            "primary_agent": "sql",  # Default
            "supporting_agents": [],
            "collaboration_mode": "single",
            "reasoning": "Parsed from router response",
            "confidence": "medium"
        }
        
        lines = response_text.strip().split('\n')
        
        for line in lines:
            line = line.strip().strip('`')
            if not line:
                continue
                
            if line.startswith("PRIMARY:"):
                agent = line.split(":", 1)[1].strip().lower()
                if agent in self.available_agents:
                    result["primary_agent"] = agent
                    
            elif line.startswith("SUPPORTING:"):
                agents_str = line.split(":", 1)[1].strip().lower()
                if agents_str != "none" and agents_str:
                    agents = [a.strip() for a in agents_str.split(",")]
                    result["supporting_agents"] = [a for a in agents if a in self.available_agents]
                    
            elif line.startswith("MODE:"):
                mode = line.split(":", 1)[1].strip().lower()
                if mode in ["single", "sequential", "parallel"]:
                    result["collaboration_mode"] = mode
                    
            elif line.startswith("CONFIDENCE:"):
                confidence = line.split(":", 1)[1].strip().lower()
                if confidence in ["high", "medium", "low"]:
                    result["confidence"] = confidence
                    
            elif line.startswith("REASONING:"):
                result["reasoning"] = line.split(":", 1)[1].strip()
        
        # Fallback: Use keyword matching if parsing failed
        # ENHANCEMENT: Changed default from SQL to general for better routing
        if result["primary_agent"] in ["sql", "general"] and result["confidence"] == "medium":
            result = self._fallback_routing(query)
        
        return result
    
    def _fallback_routing(self, query: str) -> Dict[str, Any]:
        """
        Fallback routing using keyword matching.
        
        ENHANCEMENT: Improved to default to general agent if no clear match found.
        """
        query_lower = query.lower()
        
        # Count matches for each agent
        scores = {agent: 0 for agent in self.available_agents.keys()}
        
        for agent_key, agent_info in self.available_agents.items():
            for keyword in agent_info["expertise"]:
                if keyword in query_lower:
                    scores[agent_key] += 1
        
        # Determine primary agent (highest score)
        # ENHANCEMENT: If no clear winner (all scores are 0 or tied), default to general
        max_score = max(scores.values())
        
        if max_score == 0:
            # No keyword matches, use general agent
            primary = "general"
        else:
            primary = max(scores.items(), key=lambda x: x[1])[0]
        
        # Determine supporting agents (score > 0 and not primary)
        supporting = [agent for agent, score in scores.items() 
                     if score > 0 and agent != primary]
        
        # Determine mode
        if len(supporting) == 0:
            mode = "single"
        elif len(supporting) <= 2:
            mode = "sequential"
        else:
            mode = "sequential"  # Default to sequential for complex queries
        
        return {
            "primary_agent": primary,
            "supporting_agents": supporting,
            "collaboration_mode": mode,
            "reasoning": f"Keyword matching: {primary} has {scores[primary]} matches" + (" (defaulted to general)" if max_score == 0 else ""),
            "confidence": "low"
        }


def create_router(api_key: str = None) -> RouterAgent:
    """Factory function to create a router agent"""
    return RouterAgent(api_key=api_key)
