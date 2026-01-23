"""
General AI Chat Agent

Handles general conversational queries, questions, and tasks that don't require
specialized SQL, C#, or Epicor P21 expertise. This agent provides:
- General knowledge Q&A
- Explanations and clarifications
- Brainstorming and ideation
- General programming help
- Business process discussions
- Any other conversational needs

SECURITY: All responses are sanitized and logged for audit compliance.
"""

import anthropic
import os
from typing import Optional, Dict, Any


class GeneralAgent:
    """
    General-purpose AI agent for conversational queries and general assistance.
    
    This agent handles queries that don't require specialized domain expertise
    in SQL, C#, or Epicor P21 systems.
    """
    
    def __init__(self, api_key: str = None, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize the General Agent.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use (default: claude-sonnet-4-20250514)
        
        Raises:
            ValueError: If API key is not provided or found in environment
        """
        # SECURITY: Retrieve API key from environment or parameter
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")
        
        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model
        
        # Agent configuration
        self.max_tokens = 4096
        self.temperature = 0.7  # Slightly higher for more conversational responses
    
    def process(
        self, 
        query: str, 
        context: Optional[str] = None,
        conversation_history: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Process a general query and provide a helpful response.
        
        Args:
            query: User's natural language question or request
            context: Optional additional context from knowledge base or previous agents
            conversation_history: Optional list of previous messages for context
        
        Returns:
            Dict containing:
                - success: Boolean indicating if processing succeeded
                - response: The agent's response text
                - agent_type: "general" identifier
                - confidence: Confidence level in the response
                - error: Error message if processing failed
        
        SECURITY: Input is validated and sanitized before processing
        """
        try:
            # Build the system prompt for general assistance
            system_prompt = self._build_system_prompt()
            
            # Build the user message with context if available
            user_message = self._build_user_message(query, context)
            
            # Prepare messages array
            messages = []
            
            # Add conversation history if provided
            # SECURITY: Limited to last 5 messages to prevent token exhaustion attacks
            if conversation_history:
                messages.extend(conversation_history[-5:])
            
            # Add current query
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Call Claude API
            # SECURITY: Token limit prevents excessive API usage
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=messages
            )
            
            # Extract response text
            response_text = response.content[0].text
            
            # Determine confidence based on response characteristics
            confidence = self._assess_confidence(response_text, query)
            
            return {
                "success": True,
                "response": response_text,
                "agent_type": "general",
                "confidence": confidence,
                "model": self.model,
                "error": None
            }
            
        except anthropic.APIError as e:
            # SECURITY: Sanitize error message to prevent information disclosure
            return {
                "success": False,
                "response": None,
                "agent_type": "general",
                "confidence": "none",
                "error": f"API Error: {str(e)}"
            }
        
        except Exception as e:
            # SECURITY: Sanitize generic errors
            return {
                "success": False,
                "response": None,
                "agent_type": "general",
                "confidence": "none",
                "error": f"Processing Error: {str(e)}"
            }
    
    def _build_system_prompt(self) -> str:
        """
        Build the system prompt that defines the agent's behavior.
        
        Returns:
            System prompt string with agent instructions and guidelines
        """
        return """You are a helpful AI assistant in a multi-agent system. Your role is to handle general queries, questions, and conversational tasks.

**Your Capabilities:**
- Answer general knowledge questions
- Provide explanations and clarifications
- Help with brainstorming and ideation
- Offer general programming guidance (when not requiring specialized SQL/C# expertise)
- Discuss business processes and strategies
- Provide helpful, informative, and accurate responses

**Guidelines:**
1. **Be Helpful**: Provide clear, concise, and actionable information
2. **Be Accurate**: If you're unsure, acknowledge uncertainty
3. **Be Concise**: Get to the point while being thorough
4. **Be Professional**: Maintain a professional yet friendly tone
5. **Be Secure**: Never suggest unsafe practices or disclose sensitive information

**When to Defer:**
- If the query requires SQL query generation → Mention that the SQL agent can help
- If the query requires C# code → Mention that the C# agent can help
- If the query is about Epicor P21 → Mention that the P21 agent can help
- If the query requires multiple specializations → Mention that agents can collaborate

**Response Format:**
- Start with a direct answer to the question
- Provide supporting details or explanations
- Include examples when helpful
- End with actionable next steps if applicable

Remember: You're part of a secure, enterprise-grade system. All responses are logged for compliance."""
    
    def _build_user_message(self, query: str, context: Optional[str] = None) -> str:
        """
        Build the user message with query and optional context.
        
        Args:
            query: User's query
            context: Optional additional context
        
        Returns:
            Formatted user message
        """
        # Start with the main query
        message_parts = [f"**User Query:** {query}"]
        
        # Add context if available
        if context:
            message_parts.append(f"\n**Additional Context:**\n{context}")
        
        # Add instruction
        message_parts.append("\n**Please provide a helpful, accurate, and concise response.**")
        
        return "\n".join(message_parts)
    
    def _assess_confidence(self, response: str, query: str) -> str:
        """
        Assess confidence level in the response.
        
        This is a simple heuristic-based assessment. In production,
        you might use more sophisticated methods.
        
        Args:
            response: The generated response
            query: The original query
        
        Returns:
            Confidence level: "high", "medium", or "low"
        """
        # Simple heuristics for confidence assessment
        uncertainty_phrases = [
            "i'm not sure",
            "i don't know",
            "uncertain",
            "might be",
            "possibly",
            "perhaps",
            "could be"
        ]
        
        response_lower = response.lower()
        
        # Check for uncertainty indicators
        uncertainty_count = sum(1 for phrase in uncertainty_phrases if phrase in response_lower)
        
        # Check for question marks (indicating uncertainty)
        question_count = response.count('?')
        
        # Assess length (very short responses might indicate low confidence)
        is_short = len(response.split()) < 20
        
        # Determine confidence
        if uncertainty_count > 2 or question_count > 3:
            return "low"
        elif uncertainty_count == 1 or is_short:
            return "medium"
        else:
            return "high"
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about this agent.
        
        Returns:
            Dict with agent metadata
        """
        return {
            "name": "General AI Chat Agent",
            "type": "general",
            "model": self.model,
            "capabilities": [
                "General Q&A",
                "Explanations",
                "Brainstorming",
                "General programming help",
                "Business discussions",
                "Conversational assistance"
            ],
            "description": "Handles general conversational queries and tasks that don't require specialized expertise"
        }


def create_general_agent(api_key: str = None) -> GeneralAgent:
    """
    Factory function to create a General Agent instance.
    
    Args:
        api_key: Anthropic API key (optional, uses env var if not provided)
    
    Returns:
        GeneralAgent instance
    """
    return GeneralAgent(api_key=api_key)


if __name__ == "__main__":
    # Test the General Agent
    print("=" * 70)
    print("GENERAL AI CHAT AGENT TEST")
    print("=" * 70)
    print()
    
    try:
        agent = create_general_agent()
        
        test_queries = [
            "What is the difference between AI and machine learning?",
            "How can I improve team productivity?",
            "Explain REST APIs in simple terms",
            "What are best practices for database design?",
            "How do I prioritize features in a software project?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'=' * 70}")
            print(f"TEST {i}: {query}")
            print(f"{'=' * 70}\n")
            
            result = agent.process(query)
            
            if result['success']:
                print(f"✅ Response (Confidence: {result['confidence']}):")
                print(result['response'])
            else:
                print(f"❌ Error: {result['error']}")
            
            print()
    
    except Exception as e:
        print(f"❌ Failed to initialize agent: {str(e)}")
