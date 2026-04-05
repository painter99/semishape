"""SemiShape Generate Tool - Tool pro generování CAD kódu.

Tento tool generuje build123d Python kód z textového popisu modelu.
Používá dual-model přístup (Kimi K2.5 → Minimax 2.7 fallback)
s automatickou kontrolou a opravou syntaxe.

Použití v Agent Zero:
    Agent použije tento tool když uživatel chce vygenerovat 3D CAD model.
    Např.: "Vytvoř kvádr 50x30x10mm s dírou uprostřed"
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

class SemishapeGenerate(Tool):
    """Tool pro generování build123d CAD kódu z textového popisu.
    
    Tento tool vygeneruje Python kód používající build123d knihovnu
    pro tvorbu parametrických 3D modelů.
    
    Použití:
        - Když uživatel chce vytvořit 3D model
        - Pro generování CAD kódu z přirozeného popisu
        - Pro návrh geometrie v češtině nebo angličtině
    
    Parametry:
        description: Textový popis požadovaného modelu (povinné)
        model: Použitý model - "auto", "kimi", nebo "minimax" (volitelné, default "auto")
        language: Jazyk komunikace - "cs" nebo "en" (volitelné, default "cs")
    
    Vrací:
        Response s vygenerovaným kódem, cestou k STL souboru (pokud se spustí),
        informacemi o použitém modelu a ceně.
    """
    
    async def execute(
        self,
        description: str,
        model: str = "auto",
        language: str = "cs",
    ) -> Response:
        """Vygeneruje CAD kód z textového popisu.
        
        Args:
            description: Textový popis modelu (např. "Vytvoř kvádr 50x30x10mm")
            model: "auto" = automatický výběr, "kimi" = Kimi K2.5, "minimax" = Minimax 2.7
            language: "cs" = čeština, "en" = angličtina
        
        Returns:
            Response objekt s message obsahujícím výsledek
        """
        try:
            # Validace vstupů
            if not description or not description.strip():
                return Response(
                    message="❌ Chyba: Popis modelu nesmí být prázdný.",
                    break_loop=False,
                    additional={"error": "empty_description"}
                )
            
            # Inicializujeme klienta
            # Note: model parametr je pro budoucí použití, aktuálně se používá auto-switching
            client = SemiShapeClient(
                language=language,
                output_dir="/a0/usr/projects/semishape/vystupy",
                track_metrics=True,
            )
            
            # Generujeme kód
            await self.set_progress("🎨 Generuji CAD kód...")
            
            result: Result = await client.generate_code(
                description=description,
                output_name=None,  # Auto-generované jméno
                auto_execute=True,  # Automaticky spustíme a vyexportujeme
            )
            
            # Sestavíme odpověď
            if result.success:
                message_parts = [
                    "✅ **CAD kód úspěšně vygenerován!**",
                    "",
                    f"**Model:** {result.model}",
                    f"**Cena:** ${result.cost_usd:.4f}",
                ]
                
                if result.was_fixed:
                    message_parts.append("🔧 **Automatické opravy:** Ano")
                
                if result.output_path:
                    message_parts.extend([
                        "",
                        f"**STL soubor:** `{result.output_path}`",
                    ])
                
                message_parts.extend([
                    "",
                    "**Vygenerovaný kód:**",
                    "```python",
                    result.code,
                    "```",
                ])
                
                return Response(
                    message="\n".join(message_parts),
                    break_loop=False,
                    additional={
                        "success": True,
                        "code": result.code,
                        "output_path": result.output_path,
                        "files": result.files,
                        "model": result.model,
                        "cost_usd": result.cost_usd,
                        "was_fixed": result.was_fixed,
                    }
                )
            else:
                # Selhání
                error_msg = result.error or "Neznámá chyba"
                
                message_parts = [
                    "❌ **Generování selhalo**",
                    "",
                    f"**Chyba:** {error_msg}",
                ]
                
                if result.code:
                    message_parts.extend([
                        "",
                        "**Vygenerovaný kód (před selháním):**",
                        "```python",
                        result.code,
                        "```",
                    ])
                
                if result.model:
                    message_parts.append(f"\n**Použitý model:** {result.model}")
                
                return Response(
                    message="\n".join(message_parts),
                    break_loop=False,
                    additional={
                        "success": False,
                        "error": error_msg,
                        "code": result.code,
                        "model": result.model,
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
