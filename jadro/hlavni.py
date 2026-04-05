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
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, List

# Přidáme src/ do path pro zpětnou kompatibilitu
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jadro.modely.prepinac import PrepincacModelu
from jadro.kontrola.syntax import zkontroluj_a_oprav
from jadro.utils.metriky import get_metriky
from jadro.utils.logger import get_logger

# Importy ze stávajícího src/
from semishape import SemiShape as LegacySemiShape


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
        timeout: int = 60,
        sleduj_metriky: bool = True
    ):
        """
        Args:
            jazyk: "cs" nebo "en"
            adresar_vystupu: Kam se ukládají STL soubory
            timeout: Kolik sekund čekat na generování
            sleduj_metriky: True = zapnout sledování výkonu
        """
        self.jazyk = jazyk
        self.adresar_vystupu = Path(adresar_vystupu)
        self.adresar_vystupu.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.sleduj_metriky = sleduj_metriky
        
        # Inicializujeme přepínač modelů
        self.prepinac = PrepincacModelu()
        
        # Inicializujeme metriky a logger pokud jsou zapnuty
        if self.sleduj_metriky:
            self.metriky = get_metriky()
            self.logger = get_logger()
            self.logger.loguj_info("SemiShape inicializován", extra={"verze": "0.2.0", "jazyk": jazyk})
        else:
            self.metriky = None
            self.logger = None

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
        
        cas_zacatku = time.time() if self.sleduj_metriky else None
        
        # Krok 1: Vygenerujeme kód s přepínáním modelů
        vysledek_gen = self.prepinac.generuj(popis, self.jazyk)
        
        if not vysledek_gen["uspesne"]:
            vysledek_obj = Vysledek(
                funguje=False,
                kod="",
                soubor_stl=None,
                pouzity_model=vysledek_gen["pouzity_model"],
                cena_usd=0.0,
                chyba=f"Generování selhalo: {vysledek_gen['chyba']}",
                opraveno=False
            )
            self._zaznamenaj_metriky(popis, vysledek_obj, cas_zacatku, "")
            return vysledek_obj
        
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
            vysledek_obj = Vysledek(
                funguje=False,
                kod=kod,
                soubor_stl=None,
                pouzity_model=pouzity_model,
                cena_usd=cena,
                chyba=f"Kontrola kódu selhala: {zprava}",
                opraveno=opraveno
            )
            self._zaznamenaj_metriky(popis, vysledek_obj, cas_zacatku, kod)
            return vysledek_obj
        
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
                    vysledek_obj = Vysledek(
                        funguje=False,
                        kod=kod,
                        soubor_stl=None,
                        pouzity_model=pouzity_model,
                        cena_usd=cena,
                        chyba=f"Spuštění selhalo: {result.stderr}",
                        opraveno=opraveno
                    )
                    self._zaznamenaj_metriky(popis, vysledek_obj, cas_zacatku, kod)
                    return vysledek_obj
            
            # Úspěch!
            vysledek_obj = Vysledek(
                funguje=True,
                kod=kod,
                soubor_stl=result.output_path,
                pouzity_model=pouzity_model,
                cena_usd=cena,
                chyba=None,
                opraveno=opraveno
            )
            
            self._zaznamenaj_metriky(popis, vysledek_obj, cas_zacatku, kod)
            return vysledek_obj
            
        except Exception as e:
            vysledek_obj = Vysledek(
                funguje=False,
                kod=kod,
                soubor_stl=None,
                pouzity_model=pouzity_model,
                cena_usd=cena,
                chyba=f"Chyba při spuštění: {str(e)}",
                opraveno=opraveno
            )
            
            self._zaznamenaj_metriky(popis, vysledek_obj, cas_zacatku, kod)
            return vysledek_obj

    def _zaznamenaj_metriky(self, popis: str, vysledek: Vysledek, cas_zacatku: Optional[float], kod: str):
        """Zapíše metriky a log pro dané generování"""
        if not self.sleduj_metriky or cas_zacatku is None:
            return
        
        doba = time.time() - cas_zacatku
        
        # Zaznamenáme metriky
        self.metriky.zaznamenaj(
            popis=popis,
            uspesne=vysledek.funguje,
            pouzity_model=vysledek.pouzity_model,
            cena_usd=vysledek.cena_usd,
            doba_s=doba,
            chyba=vysledek.chyba,
            opraveno=vysledek.opraveno
        )
        
        # Zalogujeme strukturovaná data
        self.logger.loguj_generovani(
            prompt=popis,
            kod=kod,
            funguje=vysledek.funguje,
            pouzity_model=vysledek.pouzity_model,
            cena_usd=vysledek.cena_usd,
            doba_s=doba,
            chyba=vysledek.chyba,
            soubor_stl=vysledek.soubor_stl,
            opraveno=vysledek.opraveno
        )

    def ziskej_metriky(self) -> Dict:
        """Vrátí aktuální souhrn metrik"""
        if not self.sleduj_metriky or self.metriky is None:
            return {"chyba": "Sledování metrik je vypnuto"}
        return self.metriky.ziskej_souhrn()

    def ziskej_historii(self, limit: int = 100) -> List[Dict]:
        """Vrátí historii generování"""
        if not self.sleduj_metriky or self.metriky is None:
            return []
        return self.metriky.ziskej_historii(limit)

    def zobraz_info(self) -> Dict:
        """Vrátí informace o nastavení včetně metrik"""
        info = {
            "verze": "0.2.0",
            "jazyk": self.jazyk,
            "adresar_vystupu": str(self.adresar_vystupu),
            "modely": {
                "hlavni": "moonshotai/kimi-k2.5",
                "zaloha": "minimax/minimax-m2.7"
            },
            "sledovani_metrik": self.sleduj_metriky
        }
        
        if self.sleduj_metriky:
            info["metriky"] = self.metriky.ziskej_souhrn()
        
        return info


# Jednoduché CLI pro testování
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SemiShape - CAD generátor")
    parser.add_argument("popis", help="Popis modelu k vygenerování")
    parser.add_argument("--jazyk", default="cs", help="cs nebo en")
    parser.add_argument("--vystup", default="/a0/usr/projects/semishape/vystupy", help="Adresář pro výstupy")
    args = parser.parse_args()
    
    print(f"=== SemiShape v0.2.0 ===\n")
    
    ss = SemiShape(jazyk=args.jazyk, adresar_vystupu=args.vystup)
    vysledek = ss.vygeneruj(args.popis)
    
    if vysledek.funguje:
        print(f"\n✅ Úspěch!")
        print(f"📁 STL: {vysledek.soubor_stl}")
        print(f"🤖 Model: {vysledek.pouzity_model}")
        print(f"💰 Cena: ${vysledek.cena_usd:.4f}")
    else:
        print(f"\n❌ Selhalo: {vysledek.chyba}")
    
    # Zobrazíme metriky
    print(f"\n📊 Aktuální metriky:")
    metriky = ss.ziskej_metriky()
    if "chyba" not in metriky:
        print(f"   Celkem: {metriky['celkem_generovani']} | "
              f"Úspěšnost: {metriky['uspesnost_procent']:.1f}% | "
              f"Cena celkem: ${metriky['celkova_cena_usd']:.4f}")
