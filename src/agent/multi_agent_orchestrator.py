"""
Multi-Agent Orchestrator
Routes queries to specialized agents (SQL or C#/.NET)
"""

import sys
import os
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import config
from src.agent.router import route_query
from src.agent.orchestrator import VoiceToSQLAgent, PipelineResult
from src.agent.csharp_agent import process_csharp_query


class AgentType(Enum):
    """Types of specialized agents"""
    SQL = "sql"
    CSHARP = "csharp"


@dataclass
class MultiAgentResult:
    """Result from the multi-agent system"""
    success: bool
    agent_used: AgentType
    routing_confidence: str
    
    # Original query
    query: str
    
    # SQL-specific (if SQL agent was used)
    sql: Optional[str] = None
    sql_results: Optional[str] = None
    
    # C#-specific (if C# agent was used)
    csharp_response: Optional[str] = None
    code_example: Optional[str] = None
    
    # Errors
    routing_error: Optional[str] = None
    execution_error: Optional[str] = None
    
    def __str__(self):
        lines = []
        
        lines.append(f"🤖 Agent Used: {self.agent_used.value.upper()}")
        lines.append(f"📊 Routing Confidence: {self.routing_confidence}")
        lines.append("")
        
        if self.agent_used == AgentType.SQL:
            if self.sql:
                lines.append(f"🔍 Generated SQL:")
                lines.append(f"   {self.sql}")
                lines.append("")
            if self.sql_results:
                lines.append(f"📊 Results:")
                lines.append(self.sql_results)
        
        elif self.agent_used == AgentType.CSHARP:
            if self.csharp_response:
                lines.append(f"💡 C# Expert Response:")
                lines.append(self.csharp_response)
                lines.append("")
            if self.code_example:
                lines.append(f"💻 Code Example:")
                lines.append(self.code_example)
        
        if not self.success:
            if self.routing_error:
                lines.append(f"❌ Routing Error: {self.routing_error}")
            if self.execution_error:
                lines.append(f"❌ Execution Error: {self.execution_error}")
        
        return "\n".join(lines)


class MultiAgentOrchestrator:
    """
    Orchestrates multiple specialized agents.
    Routes queries to the appropriate agent based on content.
    """
    
    def __init__(
        self,
        on_status: Optional[Callable[[str], None]] = None,
        verbose: bool = True
    ):
        self.on_status = on_status
        self.verbose = verbose
        
        # Initialize specialized agents
        self.sql_agent = VoiceToSQLAgent(on_status=on_status, verbose=verbose)
    
    def _status(self, message: str):
        """Emit a status message."""
        if self.verbose:
            print(message)
        if self.on_status:
            self.on_status(message)
    
    def process_query(self, query: str) -> MultiAgentResult:
        """
        Process a query by routing to the appropriate specialized agent.
        
        Args:
            query: User's natural language query
            
        Returns:
            MultiAgentResult with agent response
        """
        # Step 1: Route the query
        self._status("🔀 Routing query to appropriate agent...")
        routing_result = route_query(query)
        
        agent_type = AgentType.SQL if routing_result['agent'] == 'sql' else AgentType.CSHARP
        
        self._status(f"   → Routed to: {agent_type.value.upper()} agent")
        self._status(f"   → Confidence: {routing_result['confidence']}")
        
        # Step 2: Process with the appropriate agent
        if agent_type == AgentType.SQL:
            return self._process_with_sql_agent(query, routing_result)
        else:
            return self._process_with_csharp_agent(query, routing_result)
    
    def _process_with_sql_agent(self, query: str, routing_result: dict) -> MultiAgentResult:
        """Process query with SQL agent"""
        self._status("📊 Processing with SQL Agent...")
        
        try:
            result = self.sql_agent.process_text(query)
            
            return MultiAgentResult(
                success=result.success,
                agent_used=AgentType.SQL,
                routing_confidence=routing_result['confidence'],
                query=query,
                sql=result.generated_sql,
                sql_results=result.formatted_output,
                routing_error=routing_result.get('error'),
                execution_error=result.sql_generation_error or result.execution_error
            )
        except Exception as e:
            return MultiAgentResult(
                success=False,
                agent_used=AgentType.SQL,
                routing_confidence=routing_result['confidence'],
                query=query,
                routing_error=routing_result.get('error'),
                execution_error=str(e)
            )
    
    def _process_with_csharp_agent(self, query: str, routing_result: dict) -> MultiAgentResult:
        """Process query with C# agent"""
        self._status("💻 Processing with C#/.NET Agent...")
        
        try:
            result = process_csharp_query(query)
            
            return MultiAgentResult(
                success=result['success'],
                agent_used=AgentType.CSHARP,
                routing_confidence=routing_result['confidence'],
                query=query,
                csharp_response=result['response'],
                code_example=result['code_example'],
                routing_error=routing_result.get('error'),
                execution_error=result.get('error')
            )
        except Exception as e:
            return MultiAgentResult(
                success=False,
                agent_used=AgentType.CSHARP,
                routing_confidence=routing_result['confidence'],
                query=query,
                routing_error=routing_result.get('error'),
                execution_error=str(e)
            )


if __name__ == "__main__":
    # Test the multi-agent orchestrator
    test_queries = [
        "How many products do we have?",
        "How do I create a List in C#?",
        "Show me all orders from last month",
        "Write a LINQ query to filter users",
        "What are the top 5 customers by revenue?",
        "Explain async/await in C#",
    ]
    
    print("=" * 60)
    print("MULTI-AGENT ORCHESTRATOR TEST")
    print("=" * 60)
    
    orchestrator = MultiAgentOrchestrator(verbose=True)
    
    for query in test_queries:
        print(f"\n{'=' * 60}")
        print(f"Query: {query}")
        print(f"{'=' * 60}\n")
        
        result = orchestrator.process_query(query)
        print(result)
        print()
