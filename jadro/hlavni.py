#!/usr/bin/env python3
"""
SemiShape v0.2.0 - Hlavní API
Generování build123d CAD kódu z textového popisu

Jednoduché použití:
    from jadro.hlavni import SemiShape
    
    ss = SemiShape()
    vysledek = ss.vygeneruj("Vytvoř kvádr 50x30x10mm")
    
    if vysledek.funguje:
        print(f"Hotovo: {vysledek.soubor_stl}")
"""

import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, List

# Přidáme src/ do path pro zpětnou kompatibilitu
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jadro.modely.prepinac import PrepincacModelu
from jadro.kontrola.syntax import zkontroluj_a_oprav

# Importy ze stávajícího src/
from semishape import SemiShape as LegacySemiShape, SemiShapeResult


@dataclass
class Vysledek:
    """Výsledek generování modelu"""
    funguje: bool           # True = kód se spustil a vyexportoval STL
    kod: str                # Vygenerovaný Python kód
    soubor_stl: Optional[str]   # Cesta k STL souboru
    pouzity_model: str      # "kimi-k2.5" nebo "minimax-m2.7"
    cena_usd: float         # Orientační cena
    chyba: Optional[str]    # Chybová zpráva pokud nefunguje
    opraveno: bool          # Byly opraveny známé chyby?


class SemiShape:
    """
    Hlavní třída pro generování CAD modelů
    
    Automaticky:
    - Zvolí nejlepší model (Kimi K2.5 → Minimax 2.7)
    - Opraví známé chyby v kódu
    - Spustí kód a vyexportuje STL
    """
    
    def __init__(
        self,
        jazyk: str = "cs",
        adresar_vystupu: str = "/a0/usr/projects/semishape/vystupy",
        timeout: int = 60
    ):
        """
        Args:
            jazyk: "cs" nebo "en"
            adresar_vystupu: Kam se ukládají STL soubory
            timeout: Kolik sekund čekat na generování
        """
        self.jazyk = jazyk
        self.adresar_vystupu = Path(adresar_vystupu)
        self.adresar_vystupu.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        
        # Inicializujeme přepínač modelů
        self.prepinac = PrepincacModelu()
        
    def vygeneruj(self, popis: str, uloz_jako: Optional[str] = None) -> Vysledek:
        """
        Vygeneruje 3D model z textového popisu
        
        Args:
            popis: Např. "Vytvoř kvádr 50x30x10mm"
            uloz_jako: Název souboru (bez přípony)
            
        Returns:
            Vysledek objekt se všemi informacemi
        """
        print(f"🎨 Generuji: {popis[:50]}...")
        
        # Krok 1: Vygenerujeme kód s přepínáním modelů
        vysledek_gen = self.prepinac.generuj(popis, self.jazyk)
        
        if not vysledek_gen["uspesne"]:
            return Vysledek(
                funguje=False,
                kod="",
                soubor_stl=None,
                pouzity_model=vysledek_gen["pouzity_model"],
                cena_usd=0.0,
                chyba=f"Generování selhalo: {vysledek_gen['chyba']}",
                opraveno=False
            )
        
        kod = vysledek_gen["kod"]
        pouzity_model = vysledek_gen["pouzity_model"]
        cena = vysledek_gen["cena"]
        
        # Krok 2: Kontrola a oprava kódu
        ok, zprava, opraveny_kod = zkontroluj_a_oprav(kod)
        opraveno = kod != opraveny_kod
        
        if opraveno:
            print(f"🔧 {zprava}")
            kod = opraveny_kod
        
        if not ok:
            return Vysledek(
                funguje=False,
                kod=kod,
                soubor_stl=None,
                pouzity_model=pouzity_model,
                cena_usd=cena,
                chyba=f"Kontrola kódu selhala: {zprava}",
                opraveno=opraveno
            )
        
        # Krok 3: Spuštění a export
        try:
            # Použijeme legacy SemiShape pro spuštění
            legacy = LegacySemiShape(
                model="moonshotai/kimi-k2.5" if pouzity_model == "kimi-k2.5" else "minimax/minimax-m2.7",
                provider="openrouter",
                language=self.jazyk
            )
            
            # Generujeme a spouštíme
            result = legacy.generate_and_execute(popis, output_name=uloz_jako)
            
            if result.has_errors():
                # Selhalo - zkusíme znovu s Minimax (pokud jsme začali s Kimi)
                if pouzity_model == "kimi-k2.5":
                    print("⚠️ Kimi selhal při spuštění, zkouším Minimax...")
                    legacy = LegacySemiShape(
                        model="minimax/minimax-m2.7",
                        provider="openrouter",
                        language=self.jazyk
                    )
                    result = legacy.generate_and_execute(popis, output_name=uloz_jako)
                    pouzity_model = "minimax-m2.7"
                
                if result.has_errors():
                    return Vysledek(
                        funguje=False,
                        kod=kod,
                        soubor_stl=None,
                        pouzity_model=pouzity_model,
                        cena_usd=cena,
                        chyba=f"Spuštění selhalo: {result.stderr}",
                        opraveno=opraveno
                    )
            
            # Úspěch!
            return Vysledek(
                funguje=True,
                kod=kod,
                soubor_stl=result.output_path,
                pouzity_model=pouzity_model,
                cena_usd=cena,
                chyba=None,
                opraveno=opraveno
            )
            
        except Exception as e:
            return Vysledek(
                funguje=False,
                kod=kod,
                soubor_stl=None,
                pouzity_model=pouzity_model,
                cena_usd=cena,
                chyba=f"Chyba při spuštění: {str(e)}",
                opraveno=opraveno
            )
    
    def zobraz_info(self) -> Dict:
        """Vrátí informace o nastavení"""
        return {
            "verze": "0.2.0",
            "jazyk": self.jazyk,
            "adresar_vystupu": str(self.adresar_vystupu),
            "modely": {
                "hlavni": "moonshotai/kimi-k2.5",
                "zaloha": "minimax/minimax-m2.7"
            }
        }


# Jednoduché CLI pro testování
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SemiShape - CAD generátor")
    parser.add_argument("popis", help="Popis modelu k vygenerování")
    parser.add_argument("--jazyk", default="cs", help="cs nebo en")
    parser.add_argument("--jmeno", help="Název výstupního souboru")
    
    args = parser.parse_args()
    
    print(f"=== SemiShape v0.2.0 ===\n")
    
    ss = SemiShape(jazyk=args.jazyk)
    info = ss.zobraz_info()
    print(f"Hlavní model: {info['modely']['hlavni']}")
    print(f"Záloha: {info['modely']['zaloha']}")
    print(f"Jazyk: {info['jazyk']}\n")
    
    vysledek = ss.vygeneruj(args.popis, uloz_jako=args.jmeno)
    
    if vysledek.funguje:
        print(f"\n✅ Úspěch!")
        print(f"   Model: {vysledek.pouzity_model}")
        print(f"   Cena: ${vysledek.cena_usd:.4f}")
        print(f"   STL: {vysledek.soubor_stl}")
        if vysledek.opraveno:
            print(f"   ℹ️ Kód byl automaticky opraven")
    else:
        print(f"\n❌ Selhalo: {vysledek.chyba}")
        print(f"   Použitý model: {vysledek.pouzity_model}")
