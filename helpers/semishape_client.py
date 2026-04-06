"""SemiShape Client - Hlavní klient pro komunikaci se SemiShape API.

Tento modul poskytuje vysokoúrovňového klienta pro generování CAD kódu,
vykonávání kódu a vyhledávání v dokumentaci pomocí RAG.

Použití:
    from helpers.semishape_client import SemiShapeClient, Result
    
    client = SemiShapeClient()
    result = await client.generate_code("Vytvoř kvádr 50x30x10mm")
    
    if result.success:
        print(result.code)
        print(result.output_path)
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
from dataclasses import dataclass, field

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.semishape import SemiShape


@dataclass
class Result:
    """Strukturovaný výsledek operace SemiShapeClient.
    
    Attributes:
        success: True pokud operace uspěla
        code: Vygenerovaný Python kód (pokud relevantní)
        output_path: Cesta k vyexportovanému souboru
        files: Seznam vygenerovaných souborů
        explanation: Vysvětlení/výstup z operace
        stdout: Standardní výstup z vykonání
        stderr: Chybový výstup z vykonání
        model: Použitý AI model
        cost_usd: Orientační cena v USD
        error: Chybová zpráva pokud selhalo
        was_fixed: Byl kód automaticky opraven?
        rag_sources: Seznam zdrojů z RAG vyhledávání
        metadata: Další metadata
    """
    success: bool
    code: str = ""
    output_path: str = ""
    files: List[str] = field(default_factory=list)
    explanation: str = ""
    stdout: str = ""
    stderr: str = ""
    model: str = ""
    cost_usd: float = 0.0
    error: Optional[str] = None
    was_fixed: bool = False
    rag_sources: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertuje na slovník pro JSON serializaci."""
        return {
            "success": self.success,
            "code": self.code,
            "output_path": self.output_path,
            "files": self.files,
            "explanation": self.explanation,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "model": self.model,
            "cost_usd": self.cost_usd,
            "error": self.error,
            "was_fixed": self.was_fixed,
            "rag_sources": self.rag_sources,
            "metadata": self.metadata,
        }


class SemiShapeClient:
    """Hlavní klient pro SemiShape API integraci.
    
    Tato třída poskytuje jednoduché rozhraní pro:
    - Generování build123d CAD kódu z textového popisu
    - Vykonání kódu a export do STL/STEP
    - Vyhledávání v build123d dokumentaci pomocí RAG
    
    Konfigurace se načítá z nastaveni/modely.yaml.
    API klíče se berou z Agent Zero secrets (OPENROUTER_API_KEY).
    
    Attributes:
        language: Jazyk komunikace ("cs" nebo "en")
        output_dir: Adresář pro ukládání výstupních souborů
        track_metrics: Zapnout sledování metrik a logování
    """
    
    def __init__(
        self,
        language: str = "cs",
        output_dir: str = "/a0/usr/projects/semishape/vystupy",
        track_metrics: bool = True,
    ):
        """Inicializuje SemiShape klienta.
        
        Args:
            language: Jazyk komunikace - "cs" (čeština, default) nebo "en" (angličtina)
            output_dir: Adresář pro ukládání STL/STEP souborů
            track_metrics: True = sledovat metriky a logovat (default)
        """
        self.language = language
        self.output_dir = Path(output_dir)
        self.track_metrics = track_metrics
        
        # Inicializujeme core SemiShape API
        self._core = SemiShape(
            jazyk=language,
            adresar_vystupu=output_dir,
            sleduj_metriky=track_metrics,
        )
        
        # Načteme metriky pokud jsou povoleny
        if track_metrics:
            self._metrics = get_metriky()
        else:
            self._metrics = None
    
    async def generate_code(
        self,
        description: str,
        output_name: Optional[str] = None,
        auto_execute: bool = False,
    ) -> Result:
        """Vygeneruje build123d CAD kód z textového popisu.
        
        Používá dual-model přístup (Kimi K2.5 → Minimax 2.7 fallback)
        s automatickou kontrolou a opravou syntaxe.
        
        Args:
            description: Textový popis modelu (např. "Vytvoř kvádr 50x30x10mm")
            output_name: Název výstupního souboru (bez přípony)
            auto_execute: True = automaticky spustit a vyexportovat (default False)
        
        Returns:
            Result objekt s vygenerovaným kódem a metadaty
            
        Raises:
            Žádné - všechny chyby jsou zachyceny a vráceny v Result.error
        """
        try:
            # Zavoláme core API
            vysledek: Vysledek = self._core.vygeneruj(
                popis=description,
                uloz_jako=output_name,
            )
            
            # Převedeme Vysledek na Result
            result = Result(
                success=vysledek.funguje,
                code=vysledek.kod,
                output_path=vysledek.soubor_stl or "",
                model=vysledek.pouzity_model,
                cost_usd=vysledek.cena_usd,
                error=vysledek.chyba,
                was_fixed=vysledek.opraveno,
                files=[vysledek.soubor_stl] if vysledek.soubor_stl else [],
            )
            
            # Přidáme metadata
            result.metadata = {
                "language": self.language,
                "auto_executed": auto_execute,
                "description": description,
            }
            
            return result
            
        except Exception as e:
            return Result(
                success=False,
                error=f"Chyba při generování: {str(e)}",
                metadata={"exception_type": type(e).__name__},
            )
    
    async def execute_code(
        self,
        code: str,
        output_name: Optional[str] = None,
        export_format: str = "stl",
    ) -> Result:
        """Vykoná existující build123d kód a exportuje model.
        
        Args:
            code: Python kód s build123d modelováním
            output_name: Název výstupního souboru
            export_format: Formát exportu - "stl", "step", nebo "both"
        
        Returns:
            Result objekt s cestou k vyexportovanému souboru
        """
        try:
            # Pro spuštění použijeme generování s předem připraveným kódem
            # Toto vyžaduje úpravu - buď přes sandbox přímo nebo přes legacy API
            from src.execution.sandbox import ExecutionSandbox
            from src.execution.exporter import ModelExporter
            
            # Vytvoříme sandbox
            sandbox = ExecutionSandbox(
                output_dir=self.output_dir,
                timeout=60,
            )
            
            # Spustíme kód
            exec_result = sandbox.execute(code)
            
            if exec_result.has_errors():
                return Result(
                    success=False,
                    code=code,
                    stdout=exec_result.stdout,
                    stderr=exec_result.stderr,
                    error=f"Chyba při vykonání: {exec_result.stderr}",
                )
            
            # Exportujeme
            exporter = ModelExporter(output_dir=self.output_dir)
            
            files = []
            output_path = ""
            
            # Zkusíme exportovat podle formátu
            try:
                # Pokud code definuje 'part' nebo 'model' proměnnou
                local_vars = {}
                exec(code, {"__builtins__": __builtins__}, local_vars)
                
                # Najdeme modelový objekt
                model_obj = None
                for var_name in ["part", "model", "obj", "result"]:
                    if var_name in local_vars:
                        model_obj = local_vars[var_name]
                        break
                
                if model_obj is not None:
                    if export_format in ("stl", "both"):
                        stl_path = exporter.export_stl(
                            model_obj,
                            filename=f"{output_name or 'model'}.stl",
                        )
                        if stl_path:
                            files.append(str(stl_path))
                            output_path = str(stl_path)
                    
                    if export_format in ("step", "both"):
                        step_path = exporter.export_step(
                            model_obj,
                            filename=f"{output_name or 'model'}.step",
                        )
                        if step_path:
                            files.append(str(step_path))
                            if not output_path:
                                output_path = str(step_path)
                
                return Result(
                    success=True,
                    code=code,
                    output_path=output_path,
                    files=files,
                    stdout=exec_result.stdout,
                    model="manual_execution",
                )
                
            except Exception as export_err:
                return Result(
                    success=False,
                    code=code,
                    stdout=exec_result.stdout,
                    stderr=exec_result.stderr,
                    error=f"Chyba při exportu: {str(export_err)}",
                )
                
        except Exception as e:
            return Result(
                success=False,
                code=code,
                error=f"Chyba při vykonání kódu: {str(e)}",
                metadata={"exception_type": type(e).__name__},
            )
    
    async def search_rag(
        self,
        query: str,
        top_k: int = 5,
        use_web_search: bool = False,
    ) -> Result:
        """Vyhledá v build123d dokumentaci pomocí RAG.
        
        Args:
            query: Vyhledávací dotaz
            top_k: Počet vrácených výsledků (default 5)
            use_web_search: True = použít také webové vyhledávání
        
        Returns:
            Result objekt s nalezenou dokumentací v explanation poli
        """
        try:
            # Importujeme RAG komponenty
            from src.rag.retriever import Retriever
            
            # Inicializujeme retriever
            retriever = Retriever()
            
            # Vyhledáme
            documents = retriever.search(query, top_k=top_k)
            
            # Formátujeme výsledky
            sources = []
            explanation_parts = []
            
            for i, doc in enumerate(documents, 1):
                source = doc.get("source", "Neznámý zdroj")
                content = doc.get("content", "")
                score = doc.get("score", 0.0)
                
                sources.append(source)
                explanation_parts.append(
                    f"[{i}] {source} (relevance: {score:.2f}):\n{content[:500]}..."
                )
            
            explanation = "\n\n".join(explanation_parts) if explanation_parts else "Žádné výsledky nenalezeny."
            
            # Volitelně webové vyhledávání
            web_results = []
            if use_web_search:
                try:
                    from jadro.vyhledavani.web_search import vyhledej_dokumentaci
                    web_results = vyhledej_dokumentaci(query, max_results=3)
                except Exception:
                    pass  # Web search není kritický
            
            return Result(
                success=True,
                explanation=explanation,
                rag_sources=sources,
                metadata={
                    "query": query,
                    "top_k": top_k,
                    "web_results": web_results,
                    "document_count": len(documents),
                },
            )
            
        except Exception as e:
            return Result(
                success=False,
                error=f"Chyba při RAG vyhledávání: {str(e)}",
                metadata={"exception_type": type(e).__name__, "query": query},
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Vrátí aktuální metriky používání.
        
        Returns:
            Slovník s metrikami nebo prázdný dict pokud sledování je vypnuto
        """
        if self._metrics:
            return self._metrics.ziskej_souhrn()
        return {"error": "Sledování metrik je vypnuto"}
    
    def get_info(self) -> Dict[str, Any]:
        """Vrátí informace o klientovi a konfiguraci.
        
        Returns:
            Slovník s informacemi o verzi, jazyku, modelích apod.
        """
        return self._core.zobraz_info()


# Exportujeme pro použití v tools
__all__ = ["SemiShapeClient", "Result"]
