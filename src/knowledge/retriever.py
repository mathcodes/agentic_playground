"""
Knowledge Base Retriever
Manages agent-specific documentation and knowledge retrieval.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
import re


class KnowledgeBase:
    """
    Simple file-based knowledge base for agents.
    Each agent has its own folder with markdown/text documents.
    """
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            # Default to knowledge_base folder in project root
            base_path = Path(__file__).parent.parent.parent / "knowledge_base"
        
        self.base_path = Path(base_path)
        self.sql_path = self.base_path / "sql"
        self.csharp_path = self.base_path / "csharp"
        self.epicor_path = self.base_path / "epicor"
        self.shared_path = self.base_path / "shared"
        
        # Create directories if they don't exist
        for path in [self.sql_path, self.csharp_path, self.epicor_path, self.shared_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def get_agent_docs(self, agent_type: str) -> List[Dict[str, str]]:
        """
        Get all documents for a specific agent.
        
        Args:
            agent_type: 'sql', 'csharp', 'epicor', or 'shared'
            
        Returns:
            List of dicts with 'title', 'content', 'path'
        """
        if agent_type == 'sql':
            path = self.sql_path
        elif agent_type == 'csharp':
            path = self.csharp_path
        elif agent_type == 'epicor':
            path = self.epicor_path
        elif agent_type == 'shared':
            path = self.shared_path
        else:
            return []
        
        docs = []
        for file_path in path.glob('**/*.md'):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                docs.append({
                    'title': file_path.stem,
                    'content': content,
                    'path': str(file_path.relative_to(self.base_path))
                })
        
        return docs
    
    def search_docs(self, agent_type: str, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """
        Simple keyword-based search through agent documents.
        
        Args:
            agent_type: 'sql', 'csharp', 'epicor', or 'shared'
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of relevant documents with relevance scores
        """
        docs = self.get_agent_docs(agent_type)
        
        if not docs:
            return []
        
        # Simple keyword matching (upgrade to embeddings later)
        query_lower = query.lower()
        query_terms = set(re.findall(r'\w+', query_lower))
        
        scored_docs = []
        for doc in docs:
            content_lower = doc['content'].lower()
            title_lower = doc['title'].lower()
            
            # Calculate relevance score
            score = 0
            
            # Title matches are worth more
            for term in query_terms:
                if term in title_lower:
                    score += 5
                if term in content_lower:
                    score += content_lower.count(term)
            
            if score > 0:
                doc['relevance_score'] = score
                scored_docs.append(doc)
        
        # Sort by relevance and return top results
        scored_docs.sort(key=lambda x: x['relevance_score'], reverse=True)
        return scored_docs[:max_results]
    
    def add_document(self, agent_type: str, title: str, content: str) -> str:
        """
        Add a new document to an agent's knowledge base.
        
        Args:
            agent_type: 'sql', 'csharp', or 'shared'
            title: Document title (will be used as filename)
            content: Document content (markdown)
            
        Returns:
            Path to created file
        """
        if agent_type == 'sql':
            path = self.sql_path
        elif agent_type == 'csharp':
            path = self.csharp_path
        elif agent_type == 'shared':
            path = self.shared_path
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Sanitize title for filename
        filename = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
        file_path = path / f"{filename}.md"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(file_path)
    
    def get_context_for_query(self, agent_type: str, query: str) -> Optional[str]:
        """
        Get relevant context from knowledge base for a query.
        This is injected into the agent's prompt.
        
        Args:
            agent_type: 'sql', 'csharp', or 'shared'
            query: User's query
            
        Returns:
            Formatted context string to add to prompt
        """
        relevant_docs = self.search_docs(agent_type, query, max_results=2)
        
        if not relevant_docs:
            return None
        
        context_parts = ["RELEVANT KNOWLEDGE BASE DOCUMENTS:\n"]
        
        for doc in relevant_docs:
            context_parts.append(f"\n## {doc['title']}")
            context_parts.append(doc['content'][:500])  # Limit length
            context_parts.append("...\n")
        
        return "\n".join(context_parts)


# Vector-based retrieval (advanced option)
class VectorKnowledgeBase:
    """
    Advanced knowledge base using embeddings for semantic search.
    Requires sentence-transformers or OpenAI embeddings.
    """
    
    def __init__(self, base_path: str = None, use_embeddings: bool = False):
        self.base_kb = KnowledgeBase(base_path)
        self.use_embeddings = use_embeddings
        
        if use_embeddings:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                self.embeddings_cache = {}
            except ImportError:
                print("Warning: sentence-transformers not installed. Falling back to keyword search.")
                self.use_embeddings = False
    
    def search_semantic(self, agent_type: str, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """
        Semantic search using embeddings.
        Much better than keyword matching.
        """
        if not self.use_embeddings:
            return self.base_kb.search_docs(agent_type, query, max_results)
        
        docs = self.base_kb.get_agent_docs(agent_type)
        
        if not docs:
            return []
        
        # Generate embeddings
        query_embedding = self.model.encode(query)
        
        scored_docs = []
        for doc in docs:
            doc_key = f"{agent_type}:{doc['title']}"
            
            # Cache embeddings
            if doc_key not in self.embeddings_cache:
                self.embeddings_cache[doc_key] = self.model.encode(doc['content'])
            
            doc_embedding = self.embeddings_cache[doc_key]
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            doc['relevance_score'] = similarity
            scored_docs.append(doc)
        
        scored_docs.sort(key=lambda x: x['relevance_score'], reverse=True)
        return scored_docs[:max_results]
    
    def _cosine_similarity(self, a, b):
        """Calculate cosine similarity between two vectors"""
        import numpy as np
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


if __name__ == "__main__":
    # Test the knowledge base
    kb = KnowledgeBase()
    
    print("Knowledge Base System")
    print("=" * 60)
    
    # Check what documents exist
    for agent_type in ['sql', 'csharp', 'shared']:
        docs = kb.get_agent_docs(agent_type)
        print(f"\n{agent_type.upper()} Agent: {len(docs)} documents")
        for doc in docs:
            print(f"  - {doc['title']}")
    
    # Test search
    print("\n" + "=" * 60)
    print("Testing search for 'LINQ':")
    results = kb.search_docs('csharp', 'LINQ query', max_results=3)
    for result in results:
        print(f"  - {result['title']} (score: {result.get('relevance_score', 0)})")


# Alias for backward compatibility
# The class was originally designed as KnowledgeBase but other code expects KnowledgeRetriever
KnowledgeRetriever = KnowledgeBase
