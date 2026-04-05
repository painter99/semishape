"""SemiShape RAG Search Tool - Tool pro vyhledávání v build123d dokumentaci.

Tento tool vyhledává v lokální build123d dokumentaci pomocí RAG
(Retrieval-Augmented Generation) a volitelně také na webu.

Použití v Agent Zero:
    Agent použije tento tool když uživatel potřebuje najít informace
    o build123d API, příklady použití, nebo řešení problémů.
    Např.: "Jak funguje fillet v build123d?"
"""

import sys
from pathlib import Path

# Přidáme project root do path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Importujeme base Tool class z Agent Zero nebo vytvoříme fallback
try:
    sys.path.insert(0, "/a0")
    from helpers.tool import Tool, Response
except ImportError:
    # Fallback pro vývoj/testování mimo Agent Zero
    from dataclasses import dataclass
    from abc import abstractmethod, ABC
    
    @dataclass
    class Response:
        message: str
        break_loop: bool
        additional: dict = None
        
        def __post_init__(self):
            if self.additional is None:
                self.additional = {}
    
    class Tool(ABC):
        def __init__(self, agent=None, name="", method=None, args=None, 
                     message="", loop_data=None, **kwargs):
            self.agent = agent
            self.name = name
            self.method = method
            self.args = args or {}
            self.message = message
            self.loop_data = loop_data
            self.progress = ""
        
        @abstractmethod
        async def execute(self, **kwargs) -> Response:
            pass
        
        async def set_progress(self, content):
            self.progress = content or ""
        
        async def before_execution(self, **kwargs):
            pass
        
        async def after_execution(self, response, **kwargs):
            pass

# Importujeme náš SemiShape client
from helpers.semishape_client import SemiShapeClient, Result

class SemishapeRagSearch(Tool):
    """Tool pro vyhledávání v build123d dokumentaci pomocí RAG.
    
    Tento tool umožňuje vyhledávat v lokální build123d dokumentaci
    pomocí vektorového vyhledávání (RAG) a volitelně také na webu.
    
    Použití:
        - Když uživatel potřebuje informace o build123d API
        - Pro nalezení příkladů použití funkcí
        - Pro řešení problémů s kódem
        - Pro zjištění správné syntaxe
    
    Parametry:
        query: Vyhledávací dotaz (povinné)
        top_k: Počet vrácených výsledků (volitelné, default 5, max 10)
        use_web: Použít také webové vyhledávání (volitelné, default True)
    
    Vrací:
        Response s nalezenou dokumentací, včetně zdrojů a relevance score.
    """
    
    async def execute(
        self,
        query: str,
        top_k: int = 5,
        use_web: bool = True,
    ) -> Response:
        """Vyhledá v build123d dokumentaci.
        
        Args:
            query: Vyhledávací dotaz (např. "Jak použít fillet?")
            top_k: Počet vrácených výsledků (1-10)
            use_web: True = použít také DuckDuckGo web search
        
        Returns:
            Response objekt s message obsahujícím nalezenou dokumentaci
        """
        try:
            # Validace vstupů
            if not query or not query.strip():
                return Response(
                    message="❌ Chyba: Vyhledávací dotaz nesmí být prázdný.",
                    break_loop=False,
                    additional={"error": "empty_query"}
                )
            
            # Omezení top_k
            top_k = max(1, min(top_k, 10))  # Clamp mezi 1 a 10
            
            # Inicializujeme klienta
            client = SemiShapeClient(
                language="cs",
                output_dir="/a0/usr/projects/semishape/vystupy",
                track_metrics=False,  # Pro RAG není potřeba
            )
            
            # Vyhledáme
            await self.set_progress(f"🔍 Vyhledávám v dokumentaci... (top_k={top_k})")
            
            result: Result = await client.search_rag(
                query=query,
                top_k=top_k,
                use_web_search=use_web,
            )
            
            # Sestavíme odpověď
            if result.success:
                message_parts = [
                    f"📚 **Nalezené dokumentace pro:** \"{query}\"",
                    "",
                ]
                
                # Přidáme hlavní obsah
                if result.explanation:
                    message_parts.append(result.explanation)
                else:
                    message_parts.append("Žádné výsledky nenalezeny.")
                
                # Přidáme metadata
                metadata = result.metadata or {}
                doc_count = metadata.get("document_count", 0)
                
                message_parts.extend([
                    "",
                    f"**Nalezeno dokumentů:** {doc_count}",
                ])
                
                # Přidáme webové výsledky pokud jsou
                if use_web and metadata.get("web_results"):
                    web_results = metadata["web_results"]
                    message_parts.extend([
                        "",
                        "**Webové zdroje:**",
                    ])
                    for i, wr in enumerate(web_results[:3], 1):
                        title = wr.get("title", "Neznámý")
                        url = wr.get("url", "")
                        message_parts.append(f"{i}. [{title}]({url})")
                
                # Přidáme RAG zdroje
                if result.rag_sources:
                    message_parts.extend([
                        "",
                        "**Lokální zdroje (RAG):**",
                    ])
                    for src in result.rag_sources[:5]:
                        message_parts.append(f"- `{src}`")
                
                return Response(
                    message="\n".join(message_parts),
                    break_loop=False,
                    additional={
                        "success": True,
                        "query": query,
                        "top_k": top_k,
                        "document_count": doc_count,
                        "rag_sources": result.rag_sources,
                        "web_results": metadata.get("web_results", []),
                    }
                )
            else:
                # Selhání
                error_msg = result.error or "Neznámá chyba při vyhledávání"
                
                return Response(
                    message=f"❌ **Vyhledávání selhalo**\n\n**Chyba:** {error_msg}",
                    break_loop=False,
                    additional={
                        "success": False,
                        "error": error_msg,
                        "query": query,
                    }
                )
                
        except Exception as e:
            return Response(
                message=f"❌ **Chyba v toolu:** {str(e)}",
                break_loop=False,
                additional={
                    "success": False,
                    "error": str(e),
                    "exception_type": type(e).__name__,
                }
            )
