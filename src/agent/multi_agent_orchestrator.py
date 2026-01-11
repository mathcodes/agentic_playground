"""
Multi-Agent Orchestrator with Collaboration Support

Routes queries to specialized agents and manages multi-agent collaboration.
Supports single agent, sequential collaboration, and parallel collaboration modes.
"""

import sys
import os
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import config
from src.agent.router import RouterAgent
from src.agent.orchestrator import VoiceToSQLAgent
from src.agent.csharp_agent import CSharpAgent
from src.agent.epicor_agent import EpicorP21Agent
from src.agent.collaboration import CollaborationManager, CollaborationSession
from src.knowledge.retriever import KnowledgeRetriever


class AgentType(Enum):
    """Types of specialized agents"""
    SQL = "sql"
    CSHARP = "csharp"
    EPICOR = "epicor"


@dataclass
class MultiAgentResult:
    """Result from the multi-agent system"""
    success: bool
    mode: str  # single, sequential, parallel
    agents_used: list
    routing_confidence: str
    
    # Original query
    query: str
    
    # Collaboration session
    collaboration_session: Optional[Dict[str, Any]] = None
    
    # Final synthesized response
    final_response: Optional[str] = None
    
    # SQL-specific (if SQL agent was used)
    sql: Optional[str] = None
    sql_results: Optional[str] = None
    
    # C#-specific (if C# agent was used)
    csharp_response: Optional[str] = None
    code_example: Optional[str] = None
    
    # Epicor-specific (if Epicor agent was used)
    epicor_response: Optional[str] = None
    
    # Errors
    routing_error: Optional[str] = None
    execution_error: Optional[str] = None
    
    def __str__(self):
        lines = []
        
        lines.append(f"🤖 Agents: {', '.join([a.upper() for a in self.agents_used])}")
        lines.append(f"🔄 Mode: {self.mode.upper()}")
        lines.append(f"📊 Confidence: {self.routing_confidence}")
        lines.append("")
        
        if self.final_response:
            lines.append(self.final_response)
        
        if not self.success:
            if self.routing_error:
                lines.append(f"❌ Routing Error: {self.routing_error}")
            if self.execution_error:
                lines.append(f"❌ Execution Error: {self.execution_error}")
        
        return "\n".join(lines)


class MultiAgentOrchestrator:
    """
    Orchestrates multiple specialized agents with collaboration support.
    Routes queries and manages agent discussions.
    """
    
    def __init__(
        self,
        on_status: Optional[Callable[[str], None]] = None,
        verbose: bool = True
    ):
        self.on_status = on_status
        self.verbose = verbose
        
        # Initialize router
        self.router = RouterAgent(api_key=config.ANTHROPIC_API_KEY)
        
        # Initialize specialized agents
        self.agents = {
            "sql": VoiceToSQLAgent(on_status=on_status, verbose=verbose),
            "csharp": CSharpAgent(api_key=config.ANTHROPIC_API_KEY),
            "epicor": EpicorP21Agent(api_key=config.ANTHROPIC_API_KEY)
        }
        
        # Initialize collaboration manager
        self.collaboration_manager = CollaborationManager()
        
        # Initialize knowledge retriever
        try:
            self.knowledge_retriever = KnowledgeRetriever()
        except:
            self.knowledge_retriever = None
            self._status("⚠️  Knowledge base not available")
    
    def _status(self, message: str):
        """Emit a status message."""
        if self.verbose:
            print(message)
        if self.on_status:
            self.on_status(message)
    
    def process_query(self, query: str) -> MultiAgentResult:
        """
        Process a query using the multi-agent system with collaboration
        
        Args:
            query: User's natural language question
            
        Returns:
            MultiAgentResult with responses from all involved agents
        """
        self._status("🔍 Analyzing query and determining agent strategy...")
        
        # Route the query
        routing = self.router.route(query)
        
        primary_agent = routing["primary_agent"]
        supporting_agents = routing["supporting_agents"]
        mode = routing["collaboration_mode"]
        confidence = routing["confidence"]
        reasoning = routing["reasoning"]
        
        self._status(f"📋 Routing Decision:")
        self._status(f"   Primary: {primary_agent.upper()}")
        if supporting_agents:
            self._status(f"   Supporting: {', '.join([a.upper() for a in supporting_agents])}")
        self._status(f"   Mode: {mode.upper()}")
        self._status(f"   Reasoning: {reasoning}")
        self._status("")
        
        # Create collaboration session
        session = self.collaboration_manager.create_session(
            query=query,
            primary_agent=primary_agent,
            supporting_agents=supporting_agents,
            mode=mode
        )
        
        # Execute based on mode
        try:
            if mode == "single":
                self._status(f"🤖 {primary_agent.upper()} Agent processing...")
                session = self.collaboration_manager.execute_single_agent(
                    session, self.agents, self.knowledge_retriever
                )
                
            elif mode == "sequential":
                self._status(f"🔄 Sequential collaboration: {primary_agent.upper()} → {' → '.join([a.upper() for a in supporting_agents])}")
                session = self.collaboration_manager.execute_sequential_collaboration(
                    session, self.agents, self.knowledge_retriever
                )
                
            elif mode == "parallel":
                self._status(f"⚡ Parallel collaboration: {', '.join([primary_agent.upper()] + [a.upper() for a in supporting_agents])}")
                session = self.collaboration_manager.execute_parallel_collaboration(
                    session, self.agents, self.knowledge_retriever
                )
            
            self._status("✅ Collaboration complete!")
            
            # Build result
            result = self._build_result(session, routing)
            return result
            
        except Exception as e:
            self._status(f"❌ Error during collaboration: {str(e)}")
            return MultiAgentResult(
                success=False,
                mode=mode,
                agents_used=[primary_agent],
                routing_confidence=confidence,
                query=query,
                execution_error=str(e)
            )
    
    def _build_result(self, session: CollaborationSession, routing: Dict[str, Any]) -> MultiAgentResult:
        """Build a MultiAgentResult from the collaboration session"""
        
        agents_used = [session.primary_agent] + session.supporting_agents
        
        # Extract specific responses
        sql_response = None
        sql_results = None
        csharp_response = None
        epicor_response = None
        
        for msg in session.messages:
            if "SQL" in msg.agent_name.upper():
                sql_response = msg.content
                # Try to extract SQL and results
                if "```sql" in msg.content.lower():
                    sql_response = msg.content
            elif "C#" in msg.agent_name.upper() or "CSHARP" in msg.agent_name.upper():
                csharp_response = msg.content
            elif "EPICOR" in msg.agent_name.upper() or "P21" in msg.agent_name.upper():
                epicor_response = msg.content
        
        return MultiAgentResult(
            success=session.status == "completed",
            mode=session.mode,
            agents_used=agents_used,
            routing_confidence=routing.get("confidence", "unknown"),
            query=session.query,
            collaboration_session=session.to_dict(),
            final_response=session.final_response,
            sql=sql_response,
            csharp_response=csharp_response,
            epicor_response=epicor_response
        )
    
    def process_text(self, text: str) -> MultiAgentResult:
        """Process text input (alias for process_query)"""
        return self.process_query(text)


def create_orchestrator(
    on_status: Optional[Callable[[str], None]] = None,
    verbose: bool = True
) -> MultiAgentOrchestrator:
    """Factory function to create a multi-agent orchestrator"""
    return MultiAgentOrchestrator(on_status=on_status, verbose=verbose)


if __name__ == "__main__":
    # Test the multi-agent system
    print("=" * 70)
    print("MULTI-AGENT COLLABORATION SYSTEM TEST")
    print("=" * 70)
    print()
    
    orchestrator = create_orchestrator(verbose=True)
    
    test_queries = [
        "Show me all products",
        "How do I use LINQ in C#?",
        "How do I export P21 sales data?",
        "Write C# code to query P21 database for top customers",
        "Build a P21 integration API with async database operations"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 70}")
        print(f"TEST {i}: {query}")
        print(f"{'=' * 70}\n")
        
        result = orchestrator.process_query(query)
        print(f"\n{result}")
        print()
