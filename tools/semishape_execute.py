"""SemiShape Execute Tool - Tool pro spuštění kódu a export CAD modelu.

Tento tool vykoná existující build123d Python kód a exportuje výsledný
3D model do STL nebo STEP formátu.

Použití v Agent Zero:
    Agent použije tento tool když uživatel chce spustit vygenerovaný kód
    nebo exportovat model v jiném formátu.
    Např.: "Spusť tento kód a vyexportuj do STEP"
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


class SemishapeExecute(Tool):
    """Tool pro vykonání build123d kódu a export modelu.
    
    Tento tool spustí existující Python kód s build123d modelováním
    a vyexportuje výsledný 3D model do požadovaného formátu.
    
    Použití:
        - Když uživatel chce spustit již vygenerovaný kód
        - Pro export modelu do jiného formátu (STL → STEP)
        - Pro testování kódu bez generování
    
    Parametry:
        code: Python kód s build123d modelováním (povinné)
        output_name: Název výstupního souboru bez přípony (volitelné)
        export_format: Formát exportu - "stl", "step", nebo "both" (volitelné, default "stl")
    
    Vrací:
        Response s cestou k vyexportovanému souboru, stdout/stderr z vykonání,
        a seznamem všech vygenerovaných souborů.
    """
    
    async def execute(
        self,
        code: str,
        output_name: str = None,
        export_format: str = "stl",
    ) -> Response:
        """Vykoná build123d kód a exportuje model.
        
        Args:
            code: Python kód s build123d modelováním
            output_name: Název výstupního souboru (bez přípony)
            export_format: "stl" = STL formát, "step" = STEP formát, "both" = obojí
        
        Returns:
            Response objekt s message obsahujícím výsledek
        """
        try:
            # Validace vstupů
            if not code or not code.strip():
                return Response(
                    message="❌ Chyba: Kód nesmí být prázdný.",
                    break_loop=False,
                    additional={"error": "empty_code"}
                )
            
            # Validace export formátu
            valid_formats = ["stl", "step", "both"]
            if export_format not in valid_formats:
                return Response(
                    message=f"❌ Chyba: Neplatný formát '{export_format}'. Povolené: {', '.join(valid_formats)}",
                    break_loop=False,
                    additional={"error": "invalid_format", "valid_formats": valid_formats}
                )
            
            # Inicializujeme klienta
            client = SemiShapeClient(
                language="cs",
                output_dir="/a0/usr/projects/semishape/vystupy",
                track_metrics=True,
            )
            
            # Spustíme kód
            await self.set_progress("⚙️ Spouštím kód v sandboxu...")
            
            result: Result = await client.execute_code(
                code=code,
                output_name=output_name,
                export_format=export_format,
            )
            
            # Sestavíme odpověď
            if result.success:
                message_parts = [
                    "✅ **Kód úspěšně vykonán a model vyexportován!**",
                ]
                
                if result.output_path:
                    message_parts.extend([
                        "",
                        f"**Výstupní soubor:** `{result.output_path}`",
                    ])
                
                if result.files and len(result.files) > 1:
                    message_parts.extend([
                        "",
                        "**Všechny vygenerované soubory:**",
                    ])
                    for f in result.files:
                        message_parts.append(f"- `{f}`")
                
                if result.stdout:
                    message_parts.extend([
                        "",
                        "**Výstup z vykonání:**",
                        "```",
                        result.stdout[:2000],  # Omezení délky
                        "```",
                    ])
                
                return Response(
                    message="\n".join(message_parts),
                    break_loop=False,
                    additional={
                        "success": True,
                        "output_path": result.output_path,
                        "files": result.files,
                        "stdout": result.stdout,
                    }
                )
            else:
                # Selhání
                error_msg = result.error or "Neznámá chyba při vykonání"
                
                message_parts = [
                    "❌ **Vykonání kódu selhalo**",
                    "",
                    f"**Chyba:** {error_msg}",
                ]
                
                if result.stderr:
                    message_parts.extend([
                        "",
                        "**Chybový výstup:**",
                        "```",
                        result.stderr[:2000],
                        "```",
                    ])
                
                if result.stdout:
                    message_parts.extend([
                        "",
                        "**Standardní výstup (před chybou):**",
                        "```",
                        result.stdout[:1000],
                        "```",
                    ])
                
                return Response(
                    message="\n".join(message_parts),
                    break_loop=False,
                    additional={
                        "success": False,
                        "error": error_msg,
                        "stderr": result.stderr,
                        "stdout": result.stdout,
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
