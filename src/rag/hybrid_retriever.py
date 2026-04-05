"""Hybrid retriever combining local RAG with web search.

Integrates local vectorstore (ChromaDB) with DuckDuckGo web search
to provide comprehensive build123d documentation retrieval.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

from .retriever import Retriever, RetrievalResult, create_retriever
from .vectorstore import VectorStore

# Import web search from jadro module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "jadro" / "vyhledavani"))
from web_search import WebSearcher, WebSearchResult, create_web_searcher


@dataclass
class HybridRetrievalResult:
    """Combined result from local RAG and web search."""
    local_results: List[RetrievalResult]
    web_results: List[WebSearchResult]
    sources_used: List[str]  # 'local', 'web', or both
    
    def format_combined_context(
        self,
        max_local: int = 3,
        max_web: int = 2,
        include_scores: bool = False
    ) -> str:
        """Format combined results as context for LLM.
        
        Args:
            max_local: Maximum local results to include
            max_web: Maximum web results to include
            include_scores: Include relevance scores
        
        Returns:
            Formatted context string
        """
        parts = []
        
        # Local results first (more reliable)
        if self.local_results:
            parts.append("[Local Documentation Repository]\n")
            for i, result in enumerate(self.local_results[:max_local], 1):
                formatted = result.format_context(include_score=include_scores)
                parts.append(f"---\n{formatted}\n")
        
        # Web results as supplementary
        if self.web_results:
            parts.append("\n[Web Search Results - Current Documentation]\n")
            for i, result in enumerate(self.web_results[:max_web], 1):
                parts.append(f"{i}. {result.title}\n")
                parts.append(f"   Source: {result.url}\n")
                parts.append(f"   {result.snippet}\n")
                if include_scores:
                    parts.append(f"   (score: {result.relevance_score:.2f})\n")
                parts.append("")
        
        return "\n".join(parts)
    
    def needs_web_fallback(self, min_local_results: int = 2) -> bool:
        """Check if web results were needed as fallback.
        
        Args:
            min_local_results: Minimum expected local results
        
        Returns:
            True if web search provided significant fallback
        """
        local_count = len(self.local_results)
        web_count = len(self.web_results)
        
        # Web was needed if local results insufficient AND web has good results
        return local_count < min_local_results and web_count > 0


class HybridRetriever:
    """Hybrid retrieval combining local RAG and web search.
    
    Strategy:
    1. Always query local vectorstore first (fast, reliable)
    2. If local results insufficient or stale, query web
    3. Combine results with local prioritized
    """
    
    def __init__(
        self,
        persist_dir: Path,
        collection_name: str = VectorStore.DEFAULT_COLLECTION,
        enable_web_search: bool = True,
        web_results_limit: int = 3,
        local_results_limit: int = 5,
        min_local_score: float = 0.3
    ):
        """Initialize hybrid retriever.
        
        Args:
            persist_dir: Directory for ChromaDB vectorstore
            collection_name: ChromaDB collection name
            enable_web_search: Whether to enable web fallback
            web_results_limit: Max web results to include
            local_results_limit: Max local results to retrieve
            min_local_score: Minimum score for local result to count
        """
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.enable_web_search = enable_web_search
        self.web_results_limit = web_results_limit
        self.local_results_limit = local_results_limit
        self.min_local_score = min_local_score
        
        # Initialize components
        self.local_retriever = create_retriever(persist_dir, collection_name)
        self.web_searcher = create_web_searcher(max_results=web_results_limit) if enable_web_search else None
    
    def retrieve(
        self,
        query: str,
        use_web: Optional[bool] = None,
        top_k_local: Optional[int] = None,
        top_k_web: Optional[int] = None,
        min_local_score: Optional[float] = None
    ) -> HybridRetrievalResult:
        """Retrieve using hybrid approach.
        
        Args:
            query: Search query
            use_web: Override web search setting
            top_k_local: Override local results limit
            top_k_web: Override web results limit
            min_local_score: Override minimum local score
        
        Returns:
            HybridRetrievalResult with combined results
        """
        local_limit = top_k_local or self.local_results_limit
        web_limit = top_k_web or self.web_results_limit
        min_score = min_local_score or self.min_local_score
        should_use_web = use_web if use_web is not None else self.enable_web_search
        
        sources_used = []
        local_results = []
        web_results = []
        
        # Step 1: Query local vectorstore
        try:
            local_results = self.local_retriever.retrieve(
                query,
                top_k=local_limit,
                min_score=min_score
            )
            if local_results:
                sources_used.append('local')
        except Exception as e:
            print(f"Local retrieval error: {e}")
            local_results = []
        
        # Step 2: Decide if web search needed
        needs_web = should_use_web and (
            len(local_results) < 2 or  # Insufficient local results
            self._should_supplement(query, local_results)  # Query suggests need for current info
        )
        
        # Step 3: Web search if needed
        if needs_web and self.web_searcher:
            try:
                web_results = self.web_searcher.search_docs(
                    query,
                    max_results=web_limit
                )
                if web_results:
                    sources_used.append('web')
            except Exception as e:
                print(f"Web search error: {e}")
                web_results = []
        
        return HybridRetrievalResult(
            local_results=local_results,
            web_results=web_results,
            sources_used=sources_used
        )
    
    def retrieve_code_examples(
        self,
        query: str,
        use_web: bool = True
    ) -> HybridRetrievalResult:
        """Retrieve code examples (local first, web fallback).
        
        Args:
            query: Search query for code examples
            use_web: Whether to include web results
        
        Returns:
            HybridRetrievalResult with code examples
        """
        local_results = self.local_retriever.retrieve_code_examples(
            query,
            top_k=self.local_results_limit
        )
        
        sources_used = ['local'] if local_results else []
        web_results = []
        
        # Web search for code if local insufficient
        if use_web and len(local_results) < 3 and self.web_searcher:
            try:
                # Search GitHub specifically for code examples
                web_results = self.web_searcher.search_github(
                    f"{query} example python",
                    max_results=self.web_results_limit
                )
                if web_results:
                    sources_used.append('web')
            except Exception as e:
                print(f"Web code search error: {e}")
        
        return HybridRetrievalResult(
            local_results=local_results,
            web_results=web_results,
            sources_used=sources_used
        )
    
    def _should_supplement(self, query: str, local_results: List[RetrievalResult]) -> bool:
        """Determine if web supplement needed based on query and results.
        
        Args:
            query: Original query
            local_results: Results from local search
        
        Returns:
            True if web search should supplement
        """
        query_lower = query.lower()
        
        # Keywords that suggest need for current information
        current_info_keywords = [
            'latest', 'new', 'recent', 'version', 'release',
            'update', 'current', 'changelog', 'now', '2024', '2025'
        ]
        
        # Check if query asks for current info
        if any(kw in query_lower for kw in current_info_keywords):
            return True
        
        # Check if local results have low scores (might be outdated)
        if local_results and all(r.score < 0.5 for r in local_results):
            return True
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about retriever state.
        
        Returns:
            Stats dict with local and web status
        """
        stats = {
            'local': self.local_retriever.get_stats(),
            'web_enabled': self.enable_web_search,
            'web_available': self.web_searcher is not None
        }
        return stats
    
    def format_context_for_llm(
        self,
        result: HybridRetrievalResult,
        max_tokens: int = 4000
    ) -> str:
        """Format hybrid results for LLM context.
        
        Args:
            result: HybridRetrievalResult to format
            max_tokens: Approximate token limit
        
        Returns:
            Formatted context string
        """
        return result.format_combined_context(
            max_local=3,
            max_web=2,
            include_scores=False
        )


def create_hybrid_retriever(
    persist_dir: Optional[Path] = None,
    enable_web_search: bool = True
) -> HybridRetriever:
    """Factory function to create HybridRetriever.
    
    Args:
        persist_dir: Vectorstore directory (default: data/vectorstore)
        enable_web_search: Enable web search fallback
    
    Returns:
        Configured HybridRetriever
    """
    if persist_dir is None:
        persist_dir = Path("/a0/usr/projects/semishape/data/vectorstore")
    
    return HybridRetriever(
        persist_dir=persist_dir,
        enable_web_search=enable_web_search
    )


if __name__ == '__main__':
    # Test hybrid retriever
    import sys
    
    print("Testing Hybrid Retriever...\n")
    
    persist_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/a0/usr/projects/semishape/data/vectorstore")
    
    try:
        retriever = create_hybrid_retriever(
            persist_dir=persist_dir,
            enable_web_search=True
        )
        
        print(f"Local documents: {retriever.local_retriever.vectorstore.count()}")
        print(f"Web search: {'enabled' if retriever.enable_web_search else 'disabled'}")
        print()
        
        test_queries = [
            "How to use extrude function?",
            "BuildPart tutorial",
            "selectors sort_by example",
        ]
        
        for query in test_queries:
            print(f"=== Query: {query} ===")
            
            result = retriever.retrieve(query, top_k_local=2, top_k_web=2)
            
            print(f"Sources used: {', '.join(result.sources_used)}")
            print(f"Local results: {len(result.local_results)}")
            print(f"Web results: {len(result.web_results)}")
            
            if result.local_results:
                print("\nTop local result:")
                r = result.local_results[0]
                print(f"  - {r.source_file} > {r.section_title} (score: {r.score:.3f})")
            
            if result.web_results:
                print("\nTop web result:")
                w = result.web_results[0]
                print(f"  - {w.title} (score: {w.relevance_score:.2f})")
            
            print(f"\nWeb fallback needed: {result.needs_web_fallback()}")
            print("\n" + "="*50 + "\n")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
