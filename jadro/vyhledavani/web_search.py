"""Web search module for build123d documentation.

Provides DuckDuckGo-based search for up-to-date build123d documentation.
Integrates with RAG retriever for hybrid local + web retrieval.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class WebSearchResult:
    """A single web search result."""
    title: str
    url: str
    snippet: str
    source: str  # 'duckduckgo', 'github', etc.
    relevance_score: float = 0.0
    fetched_at: datetime = None
    
    def __post_init__(self):
        if self.fetched_at is None:
            self.fetched_at = datetime.now()
    
    def format_context(self) -> str:
        """Format result as context for LLM."""
        return f"""[{self.title}]
Zdroj: {self.url}
{self.snippet}
"""


class WebSearcher:
    """Web search interface for build123d documentation.
    
    Uses DuckDuckGo for searches without requiring API keys.
    """
    
    BUILD123D_DOMAINS = [
        "build123d.readthedocs.io",
        "github.com/gumyr/build123d",
        "readthedocs.io",
    ]
    
    def __init__(self, max_results: int = 5):
        """Initialize web searcher.
        
        Args:
            max_results: Maximum results per query
        """
        self.max_results = max_results
        self._ddgs = None  # Lazy import
    
    def _get_ddgs(self):
        """Lazy import duckduckgo-search."""
        if self._ddgs is None:
            try:
                from duckduckgo_search import DDGS
                self._ddgs = DDGS()
            except ImportError:
                raise ImportError(
                    "duckduckgo-search not installed. "
                    "Run: pip install duckduckgo-search"
                )
        return self._ddgs
    
    def search(
        self,
        query: str,
        site_filter: Optional[str] = None,
        max_results: Optional[int] = None
    ) -> List[WebSearchResult]:
        """Search web for build123d documentation.
        
        Args:
            query: Search query
            site_filter: Restrict to specific site (e.g., 'build123d.readthedocs.io')
            max_results: Override default max_results
        
        Returns:
            List of WebSearchResult objects
        """
        max_res = max_results or self.max_results
        
        # Enhance query for build123d context
        enhanced_query = self._enhance_query(query, site_filter)
        
        try:
            ddgs = self._get_ddgs()
            results = []
            
            # Perform search
            search_results = ddgs.text(
                enhanced_query,
                max_results=max_res * 2  # Get more to filter
            )
            
            for i, result in enumerate(search_results):
                if len(results) >= max_res:
                    break
                
                # Filter for relevant domains if no site_filter
                if site_filter is None:
                    if not any(d in result.get('href', '') for d in self.BUILD123D_DOMAINS):
                        continue
                
                web_result = WebSearchResult(
                    title=result.get('title', 'Unknown'),
                    url=result.get('href', ''),
                    snippet=self._clean_snippet(result.get('body', '')),
                    source='duckduckgo',
                    relevance_score=self._calculate_relevance(query, result)
                )
                results.append(web_result)
            
            # Sort by relevance
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            return results[:max_res]
            
        except Exception as e:
            print(f"Web search error: {e}")
            return []
    
    def search_docs(self, query: str, max_results: int = 3) -> List[WebSearchResult]:
        """Search specifically in build123d readthedocs.
        
        Args:
            query: Search query
            max_results: Number of results
        
        Returns:
            Documentation search results
        """
        return self.search(
            query,
            site_filter="build123d.readthedocs.io",
            max_results=max_results
        )
    
    def search_github(
        self,
        query: str,
        max_results: int = 3
    ) -> List[WebSearchResult]:
        """Search in build123d GitHub repository.
        
        Args:
            query: Search query  
            max_results: Number of results
        
        Returns:
            GitHub search results
        """
        return self.search(
            query,
            site_filter="github.com/gumyr/build123d",
            max_results=max_results
        )
    
    def _enhance_query(
        self,
        query: str,
        site_filter: Optional[str] = None
    ) -> str:
        """Enhance query with build123d context."""
        enhanced = query
        
        # Add build123d context if not present
        if 'build123d' not in query.lower():
            enhanced = f"build123d {query}"
        
        # Add site filter if specified
        if site_filter:
            enhanced = f"{enhanced} site:{site_filter}"
        
        return enhanced
    
    def _clean_snippet(self, snippet: str) -> str:
        """Clean and truncate snippet."""
        # Remove excessive whitespace
        snippet = re.sub(r'\s+', ' ', snippet).strip()
        
        # Truncate if too long
        if len(snippet) > 500:
            snippet = snippet[:497] + "..."
        
        return snippet
    
    def _calculate_relevance(
        self,
        query: str,
        result: Dict[str, str]
    ) -> float:
        """Calculate relevance score for result."""
        score = 0.5  # Base score
        query_lower = query.lower()
        title = result.get('title', '').lower()
        body = result.get('body', '').lower()
        
        # Title matches are more important
        if any(term in title for term in query_lower.split()):
            score += 0.3
        
        # Body matches
        body_matches = sum(1 for term in query_lower.split() if term in body)
        score += min(0.2, body_matches * 0.05)
        
        # Prefer official documentation
        url = result.get('href', '').lower()
        if 'readthedocs' in url:
            score += 0.1
        if 'github.com/gumyr' in url:
            score += 0.05
        
        return min(1.0, score)
    
    def format_for_rag(
        self,
        results: List[WebSearchResult],
        max_chars: int = 2000
    ) -> str:
        """Format web results for RAG context.
        
        Args:
            results: Web search results
            max_chars: Maximum characters
        
        Returns:
            Formatted context string
        """
        if not results:
            return ""
        
        parts = ["\n[Web Search Results]\n"]
        current_chars = len(parts[0])
        
        for i, result in enumerate(results, 1):
            formatted = f"\n{i}. {result.title}\n"
            formatted += f"   URL: {result.url}\n"
            formatted += f"   {result.snippet}\n"
            
            if current_chars + len(formatted) > max_chars:
                parts.append(f"\n... ({len(results) - i + 1} more results)\n")
                break
            
            parts.append(formatted)
            current_chars += len(formatted)
        
        return "".join(parts)


def create_web_searcher(max_results: int = 5) -> WebSearcher:
    """Factory function to create WebSearcher."""
    return WebSearcher(max_results=max_results)


if __name__ == '__main__':
    # Test web search
    print("Testing Web Search for build123d documentation...\n")
    
    searcher = create_web_searcher(max_results=3)
    
    test_queries = [
        "extrude function parameters",
        "BuildPart tutorial",
        "selectors sort_by",
    ]
    
    for query in test_queries:
        print(f"\n=== Query: {query} ===")
        results = searcher.search_docs(query, max_results=2)
        
        if results:
            for r in results:
                print(f"  - {r.title} (score: {r.relevance_score:.2f})")
                print(f"    {r.url}")
                print(f"    {r.snippet[:100]}...")
        else:
            print("  No results found")
