"""
Agent Collaboration System

Manages multi-agent discussions and collaborative problem-solving.
Agents can share insights, build on each other's responses, and
collectively arrive at comprehensive solutions.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AgentMessage:
    """Represents a message from an agent in a collaboration"""
    agent_name: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    message_type: str = "response"  # response, question, suggestion, handoff
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "agent": self.agent_name,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "type": self.message_type,
            "metadata": self.metadata
        }


@dataclass
class CollaborationSession:
    """Manages a multi-agent collaboration session"""
    query: str
    primary_agent: str
    supporting_agents: List[str]
    mode: str  # single, sequential, parallel
    messages: List[AgentMessage] = field(default_factory=list)
    status: str = "active"  # active, completed, failed
    final_response: Optional[str] = None
    
    def add_message(self, message: AgentMessage):
        """Add a message to the collaboration"""
        self.messages.append(message)
    
    def get_context_for_agent(self, agent_name: str) -> List[Dict[str, str]]:
        """
        Get relevant context for an agent to review before responding
        
        Returns messages from other agents that this agent should consider
        """
        context = []
        for msg in self.messages:
            if msg.agent_name != agent_name:
                context.append({
                    "agent": msg.agent_name,
                    "response": msg.content,
                    "type": msg.message_type
                })
        return context
    
    def get_all_responses(self) -> List[Dict[str, Any]]:
        """Get all agent responses in order"""
        return [msg.to_dict() for msg in self.messages]
    
    def synthesize_responses(self) -> str:
        """
        Combine all agent responses into a coherent final response
        """
        if not self.messages:
            return "No responses available."
        
        if len(self.messages) == 1:
            return self.messages[0].content
        
        # Build a structured response showing each agent's contribution
        synthesis = f"**Multi-Agent Collaboration Response**\n\n"
        synthesis += f"Query: {self.query}\n\n"
        synthesis += "---\n\n"
        
        for i, msg in enumerate(self.messages, 1):
            synthesis += f"### {msg.agent_name}\n\n"
            synthesis += f"{msg.content}\n\n"
            if i < len(self.messages):
                synthesis += "---\n\n"
        
        return synthesis
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            "query": self.query,
            "primary_agent": self.primary_agent,
            "supporting_agents": self.supporting_agents,
            "mode": self.mode,
            "messages": [msg.to_dict() for msg in self.messages],
            "status": self.status,
            "final_response": self.final_response or self.synthesize_responses()
        }


class CollaborationManager:
    """Manages agent collaboration workflows"""
    
    def __init__(self):
        """Initialize the collaboration manager"""
        self.active_sessions: Dict[str, CollaborationSession] = {}
    
    def create_session(
        self,
        query: str,
        primary_agent: str,
        supporting_agents: List[str],
        mode: str
    ) -> CollaborationSession:
        """Create a new collaboration session"""
        session = CollaborationSession(
            query=query,
            primary_agent=primary_agent,
            supporting_agents=supporting_agents,
            mode=mode
        )
        
        # Store session with timestamp-based ID
        session_id = f"{datetime.now().timestamp()}"
        self.active_sessions[session_id] = session
        
        return session
    
    def execute_sequential_collaboration(
        self,
        session: CollaborationSession,
        agents: Dict[str, Any],
        knowledge_retriever: Any = None
    ) -> CollaborationSession:
        """
        Execute sequential collaboration where agents work in order
        
        Flow:
        1. Primary agent responds first
        2. Each supporting agent reviews previous responses and adds their expertise
        3. Final synthesis combines all insights
        """
        # Determine agent order: primary first, then supporting
        agent_order = [session.primary_agent] + session.supporting_agents
        
        for agent_key in agent_order:
            if agent_key not in agents:
                continue
            
            agent = agents[agent_key]
            agent_name = agent.agent_name if hasattr(agent, 'agent_name') else agent_key.upper()
            
            # Get knowledge context if available
            knowledge_context = ""
            if knowledge_retriever:
                try:
                    knowledge_context = knowledge_retriever.retrieve(
                        session.query,
                        agent_type=agent_key
                    )
                except:
                    pass
            
            # Get collaboration context (previous agent responses)
            collaboration_context = session.get_context_for_agent(agent_name)
            
            try:
                # Agent processes with context from previous agents
                if hasattr(agent, 'process'):
                    result = agent.process(
                        session.query,
                        knowledge_context=knowledge_context,
                        collaboration_context=collaboration_context if collaboration_context else None
                    )
                    
                    # Add agent's response to session
                    message = AgentMessage(
                        agent_name=agent_name,
                        content=result.get("response", "No response"),
                        message_type="response",
                        metadata={
                            "success": result.get("success", False),
                            "has_code": result.get("has_code", False),
                            "suggests_collaboration": result.get("suggests_collaboration", False)
                        }
                    )
                    session.add_message(message)
                    
            except Exception as e:
                # Log error but continue with other agents
                error_message = AgentMessage(
                    agent_name=agent_name,
                    content=f"Error: {str(e)}",
                    message_type="error",
                    metadata={"error": str(e)}
                )
                session.add_message(error_message)
        
        session.status = "completed"
        session.final_response = session.synthesize_responses()
        
        return session
    
    def execute_parallel_collaboration(
        self,
        session: CollaborationSession,
        agents: Dict[str, Any],
        knowledge_retriever: Any = None
    ) -> CollaborationSession:
        """
        Execute parallel collaboration where agents work simultaneously
        
        Note: In this implementation, we simulate parallel by running sequentially
        without sharing context between agents (they all see only the original query)
        """
        # All agents work on original query without seeing each other's responses
        all_agents = [session.primary_agent] + session.supporting_agents
        
        for agent_key in all_agents:
            if agent_key not in agents:
                continue
            
            agent = agents[agent_key]
            agent_name = agent.agent_name if hasattr(agent, 'agent_name') else agent_key.upper()
            
            # Get knowledge context if available
            knowledge_context = ""
            if knowledge_retriever:
                try:
                    knowledge_context = knowledge_retriever.retrieve(
                        session.query,
                        agent_type=agent_key
                    )
                except:
                    pass
            
            try:
                # Agent processes without collaboration context (parallel mode)
                if hasattr(agent, 'process'):
                    result = agent.process(
                        session.query,
                        knowledge_context=knowledge_context,
                        collaboration_context=None  # No context in parallel mode
                    )
                    
                    message = AgentMessage(
                        agent_name=agent_name,
                        content=result.get("response", "No response"),
                        message_type="response",
                        metadata={
                            "success": result.get("success", False),
                            "has_code": result.get("has_code", False)
                        }
                    )
                    session.add_message(message)
                    
            except Exception as e:
                error_message = AgentMessage(
                    agent_name=agent_name,
                    content=f"Error: {str(e)}",
                    message_type="error",
                    metadata={"error": str(e)}
                )
                session.add_message(error_message)
        
        session.status = "completed"
        session.final_response = session.synthesize_responses()
        
        return session
    
    def execute_single_agent(
        self,
        session: CollaborationSession,
        agents: Dict[str, Any],
        knowledge_retriever: Any = None
    ) -> CollaborationSession:
        """Execute with a single agent (no collaboration)"""
        agent_key = session.primary_agent
        
        if agent_key not in agents:
            session.status = "failed"
            return session
        
        agent = agents[agent_key]
        agent_name = agent.agent_name if hasattr(agent, 'agent_name') else agent_key.upper()
        
        # Get knowledge context if available
        knowledge_context = ""
        if knowledge_retriever:
            try:
                knowledge_context = knowledge_retriever.retrieve(
                    session.query,
                    agent_type=agent_key
                )
            except:
                pass
        
        try:
            if hasattr(agent, 'process'):
                result = agent.process(
                    session.query,
                    knowledge_context=knowledge_context,
                    collaboration_context=None
                )
                
                message = AgentMessage(
                    agent_name=agent_name,
                    content=result.get("response", "No response"),
                    message_type="response",
                    metadata={
                        "success": result.get("success", False),
                        "has_code": result.get("has_code", False)
                    }
                )
                session.add_message(message)
                
        except Exception as e:
            error_message = AgentMessage(
                agent_name=agent_name,
                content=f"Error: {str(e)}",
                message_type="error",
                metadata={"error": str(e)}
            )
            session.add_message(error_message)
        
        session.status = "completed"
        session.final_response = session.synthesize_responses()
        
        return session
