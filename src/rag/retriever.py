"""Retrieval interface for RAG pipeline.

Provides high-level retrieval operations with context formatting,
result ranking, and query augmentation capabilities.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from .vectorstore import VectorStore
from .chunker import RSTChunker, DocumentChunk
from .embeddings import EmbeddingModel


@dataclass
class RetrievalResult:
    """A single retrieval result with formatted content."""
    content: str
    source_file: str
    section_title: str
    section_path: List[str]
    chunk_type: str
    score: float
    metadata: Dict[str, Any]
    
    def format_context(self, include_source: bool = True, include_score: bool = False) -> str:
        """Format the result as context text for LLM input."""
        parts = []
        
        if include_source:
            source = f"[{self.source_file}" 
            if self.section_title:
                source += f" > {self.section_title}"
            source += "]"
            parts.append(source)
        
        if include_score:
            parts.append(f"(relevance: {self.score:.3f})")
        
        if parts:
            parts.append("\n")
        
        parts.append(self.content)
        
        return " ".join(parts) if len(parts) == 2 else "\n".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'content': self.content,
            'source_file': self.source_file,
            'section_title': self.section_title,
            'section_path': self.section_path,
            'chunk_type': self.chunk_type,
            'score': self.score,
            'metadata': self.metadata
        }


class Retriever:
    """High-level retrieval interface for build123d documentation.
    
    Features:
    - Semantic search with ChromaDB
    - Context-aware result formatting
    - Query augmentation
    - Hybrid search (semantic + keyword)
    """
    
    DEFAULT_TOP_K = 5
    DEFAULT_TOP_K_CODE = 10
    
    def __init__(
        self,
        vectorstore: VectorStore,
        embedding_model: Optional[EmbeddingModel] = None
    ):
        """Initialize the retriever.
        
        Args:
            vectorstore: VectorStore instance for searching
            embedding_model: Optional embedding model for query augmentation
        """
        self.vectorstore = vectorstore
        self.embedding_model = embedding_model
    
    def retrieve(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        filter_code: bool = False,
        filter_file: Optional[str] = None,
        filter_section: Optional[str] = None,
        min_score: float = 0.0
    ) -> List[RetrievalResult]:
        """Retrieve relevant documents for a query.
        
        Args:
            query: Search query string
            top_k: Maximum number of results
            filter_code: If True, only return code chunks
            filter_file: Filter by source file
            filter_section: Filter by section title
            min_score: Minimum relevance score threshold
        
        Returns:
            List of RetrievalResult objects
        """
        # Build metadata filter
        where_filter = None
        if filter_code:
            where_filter = {"chunk_type": "code"}
        elif filter_file:
            where_filter = {"source_file": filter_file}
        elif filter_section:
            where_filter = {"section_title": filter_section}
        
        # Query vectorstore
        results = self.vectorstore.query(
            query,
            n_results=top_k,
            where=where_filter
        )
        
        # Parse results
        retrieval_results = []
        
        if not results['documents'][0]:
            return retrieval_results
        
        for i, doc in enumerate(results['documents'][0]):
            score = 1.0 - results['distances'][0][i]  # Convert distance to similarity
            
            if score < min_score:
                continue
            
            metadata = results['metadatas'][0][i]
            
            result = RetrievalResult(
                content=doc,
                source_file=metadata.get('source_file', 'unknown'),
                section_title=metadata.get('section_title', ''),
                section_path=metadata.get('section_path', '').split(', ') if metadata.get('section_path') else [],
                chunk_type=metadata.get('chunk_type', 'text'),
                score=score,
                metadata=metadata
            )
            retrieval_results.append(result)
        
        return retrieval_results
    
    def retrieve_code_examples(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K_CODE
    ) -> List[RetrievalResult]:
        """Retrieve code examples matching a query.
        
        Args:
            query: Search query
            top_k: Number of results
        
        Returns:
            List of code chunk results
        """
        return self.retrieve(query, top_k=top_k, filter_code=True)
    
    def retrieve_for_topic(
        self,
        topic: str,
        context_size: int = 5
    ) -> Tuple[str, List[RetrievalResult]]:
        """Retrieve context for a specific topic.
        
        Args:
            topic: Topic to search for
            context_size: Number of documents to include
        
        Returns:
            Tuple of (formatted context string, raw results)
        """
        results = self.retrieve(topic, top_k=context_size)
        
        # Format context
        context_parts = []
        for result in results:
            context_parts.append(result.format_context())
        
        context = "\n\n---\n\n".join(context_parts)
        return context, results
    
    def retrieve_hybrid(
        self,
        query: str,
        keywords: Optional[List[str]] = None,
        top_k: int = DEFAULT_TOP_K
    ) -> List[RetrievalResult]:
        """Hybrid retrieval combining semantic and keyword search.
        
        Args:
            query: Semantic search query
            keywords: Optional list of keywords to boost
            top_k: Number of results
        
        Returns:
            Ranked list of results
        """
        # Get semantic results
        semantic_results = self.retrieve(query, top_k=top_k * 2)
        
        if not keywords:
            return semantic_results[:top_k]
        
        # Boost results containing keywords
        for result in semantic_results:
            boost = 0.0
            content_lower = result.content.lower()
            
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    boost += 0.1
            
            result.score = min(1.0, result.score + boost)
        
        # Re-rank by boosted score
        semantic_results.sort(key=lambda x: x.score, reverse=True)
        
        return semantic_results[:top_k]
    
    def retrieve_with_expansion(
        self,
        query: str,
        expansion_terms: Optional[List[str]] = None,
        top_k: int = DEFAULT_TOP_K
    ) -> List[RetrievalResult]:
        """Retrieve with query expansion.
        
        Args:
            query: Original query
            expansion_terms: Terms to add to query
            top_k: Number of results
        
        Returns:
            List of results
        """
        # Expand query with related terms
        if expansion_terms:
            expanded_query = f"{query} {' '.join(expansion_terms)}"
        else:
            # Auto-expand based on build123d domain knowledge
            expanded_query = self._expand_query(query)
        
        return self.retrieve(expanded_query, top_k=top_k)
    
    def _expand_query(self, query: str) -> str:
        """Expand query with domain-specific terms."""
        # Domain-specific expansions
        expansions = {
            'sketch': ['BuildSketch', '2D profile', 'sketch'],
            'part': ['BuildPart', '3D object', 'solid'],
            'line': ['BuildLine', 'wire', 'edge'],
            'extrude': ['extrude', 'offset'],
            'revolve': ['revolve', 'axis'],
            'fillet': ['fillet', 'edge', 'round'],
            'chamfer': ['chamfer', 'edge', 'bevel'],
            'hole': ['Hole', 'bore', 'drill'],
            'box': ['Box', 'cube', 'rectangular'],
            'cylinder': ['Cylinder', 'circular', 'rotational'],
            'selector': ['selector', 'sort_by', 'filter', 'group'],
        }
        
        query_lower = query.lower()
        expansion_terms = []
        
        for key, terms in expansions.items():
            if key in query_lower:
                expansion_terms.extend(terms[:2])  # Add top 2 related terms
        
        if expansion_terms:
            return f"{query} {' '.join(expansion_terms)}"
        return query
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vectorstore."""
        return self.vectorstore.get_stats()
    
    def peek(self, n: int = 5) -> List[Dict[str, Any]]:
        """Preview documents in the store."""
        return self.vectorstore.peek(n)


def create_retriever(
    persist_dir: Path,
    collection_name: str = VectorStore.DEFAULT_COLLECTION
) -> Retriever:
    """Factory function to create a Retriever.
    
    Args:
        persist_dir: Directory containing ChromaDB
        collection_name: Collection name
    
    Returns:
        Configured Retriever instance
    """
    vectorstore = VectorStore(persist_dir, collection_name)
    return Retriever(vectorstore)


class ContextFormatter:
    """Format retrieval results for LLM context."""
    
    @staticmethod
    def format_for_chat(
        results: List[RetrievalResult],
        max_tokens: int = 4000,
        include_scores: bool = False
    ) -> str:
        """Format results for chat context.
        
        Args:
            results: Retrieval results
            max_tokens: Approximate max tokens (chars/4)
            include_scores: Include relevance scores
        
        Returns:
            Formatted context string
        """
        max_chars = max_tokens * 4  # Rough approximation
        context_parts = ["Here is relevant documentation from build123d:\n"]
        current_chars = 0
        
        for i, result in enumerate(results):
            formatted = result.format_context(include_score=include_scores)
            
            if current_chars + len(formatted) > max_chars:
                break
            
            context_parts.append(f"\n--- Document {i+1} ---")
            context_parts.append(formatted)
            current_chars += len(formatted) + 20
        
        return "\n".join(context_parts)
    
    @staticmethod
    def format_for_code(
        results: List[RetrievalResult],
        max_examples: int = 3
    ) -> str:
        """Format results focused on code examples.
        
        Args:
            results: Retrieval results
            max_examples: Maximum code examples to include
        
        Returns:
            Formatted context string
        """
        code_results = [r for r in results if r.chunk_type == 'code']
        code_results = code_results[:max_examples]
        
        if not code_results:
            return ""
        
        parts = ["Here are relevant code examples:\n"]
        
        for i, result in enumerate(code_results):
            parts.append(f"\n# From {result.source_file} - {result.section_title}")
            parts.append(result.content)
        
        return "\n".join(parts)


if __name__ == '__main__':
    # Test retriever with sample queries
    import sys
    
    persist_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/test_vectorstore")
    
    try:
        retriever = create_retriever(persist_dir)
        print(f"Retriever initialized with {retriever.vectorstore.count()} documents")
        
        # Test queries
        test_queries = [
            "How do I create a circle sketch?",
            "Extrude a sketch to 3D",
            "Select edges by length",
        ]
        
        for query in test_queries:
            print(f"\n=== Query: {query} ===")
            results = retriever.retrieve(query, top_k=3)
            for i, result in enumerate(results):
                print(f"\nResult {i+1} (score: {result.score:.3f}):")
                print(f"  Source: {result.source_file} > {result.section_title}")
                print(f"  Preview: {result.content[:150]}...")
    
    except Exception as e:
        print(f"Error: {e}")
        print("Note: VectorStore must be populated first using build_vectorstore.py")
