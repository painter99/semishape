#!/usr/bin/env python3
"""
Metriky pro sledování výkonu SemiShape

Jednoduché, robustní sledování:
- Úspěšnost generování
- Použité modely
- Ceny za generování
- Doba generování
- Nejčastější chyby
"""

import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from collections import defaultdict
from datetime import datetime
from threading import Lock


@dataclass
class ZaznamGenerovani:
    """Jeden záznam generování"""
    timestamp: str
    popis: str
    uspesne: bool
    pouzity_model: str
    cena_usd: float
    doba_s: float
    chyba: Optional[str]
    opraveno: bool


class Metriky:
    """
    Sledování metrik pro SemiShape generování.
    
    Ukládá do JSON souboru pro perzistentní sledování.
    Thread-safe pomocí Lock.
    """
    
    def __init__(self, soubor_metrik: Optional[str] = None):
        """
        Args:
            soubor_metrik: Cesta k JSON souboru s metrikami
                          (default: /a0/usr/projects/semishape/data/metriky.json)
        """
        if soubor_metrik is None:
            self.soubor = Path("/a0/usr/projects/semishape/data/metriky.json")
        else:
            self.soubor = Path(soubor_metrik)
        
        # Vytvoříme adresář pokud neexistuje
        self.soubor.parent.mkdir(parents=True, exist_ok=True)
        
        self._lock = Lock()
        self._data: Dict[str, Any] = self._nacti_nebo_vytvor()
    
    def _nacti_nebo_vytvor(self) -> Dict[str, Any]:
        """Načte existující data nebo vytvoří nová"""
        if self.soubor.exists():
            try:
                with open(self.soubor, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        return {
            "celkem_generovani": 0,
            "uspesnych": 0,
            "selhalo": 0,
            "uspesnost_procent": 0.0,
            "kimi_pouziti": 0,
            "minimax_pouziti": 0,
            "celkova_cena_usd": 0.0,
            "prumerna_cena_usd": 0.0,
            "celkova_doba_s": 0.0,
            "prumerna_doba_s": 0.0,
            "opraveno_pocet": 0,
            "chyby_frekvence": {},
            "historie": []
        }
    
    def _uloz(self):
        """Uloží aktuální data do souboru"""
        with open(self.soubor, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
    
    def zaznamenaj(
        self,
        popis: str,
        uspesne: bool,
        pouzity_model: str,
        cena_usd: float,
        doba_s: float,
        chyba: Optional[str] = None,
        opraveno: bool = False
    ) -> Dict[str, Any]:
        """
        Zaznamená jedno generování a aktualizuje statistiky.
        
        Args:
            popis: Popis modelu (prvních 100 znaků)
            uspesne: True pokud generování úspěšné
            pouzity_model: "kimi-k2.5" nebo "minimax-m2.7"
            cena_usd: Orientační cena v USD
            doba_s: Doba generování v sekundách
            chyba: Chybová zpráva pokud selhalo
            opraveno: True pokud byl kód automaticky opraven
            
        Returns:
            Aktualizované souhrnné metriky
        """
        with self._lock:
            # Zkrátíme popis pro přehlednost
            popis_zkraceny = popis[:100] + "..." if len(popis) > 100 else popis
            
            # Vytvoříme záznam
            zaznam = ZaznamGenerovani(
                timestamp=datetime.now().isoformat(),
                popis=popis_zkraceny,
                uspesne=uspesne,
                pouzity_model=pouzity_model,
                cena_usd=cena_usd,
                doba_s=doba_s,
                chyba=chyba[:200] if chyba else None,  # Zkrátíme chybu
                opraveno=opraveno
            )
            
            # Přidáme do historie (max 1000 záznamů)
            historie = self._data.get("historie", [])
            historie.append(asdict(zaznam))
            if len(historie) > 1000:
                historie = historie[-1000:]
            self._data["historie"] = historie
            
            # Aktualizujeme počty
            self._data["celkem_generovani"] += 1
            if uspesne:
                self._data["uspesnych"] += 1
            else:
                self._data["selhalo"] += 1
            
            # Model usage
            if pouzity_model == "kimi-k2.5":
                self._data["kimi_pouziti"] += 1
            elif pouzity_model == "minimax-m2.7":
                self._data["minimax_pouziti"] += 1
            
            # Ceny
            self._data["celkova_cena_usd"] += cena_usd
            celkem = self._data["celkem_generovani"]
            self._data["prumerna_cena_usd"] = (
                self._data["celkova_cena_usd"] / celkem if celkem > 0 else 0.0
            )
            
            # Doba
            self._data["celkova_doba_s"] += doba_s
            self._data["prumerna_doba_s"] = (
                self._data["celkova_doba_s"] / celkem if celkem > 0 else 0.0
            )
            
            # Opravy
            if opraveno:
                self._data["opraveno_pocet"] = self._data.get("opraveno_pocet", 0) + 1
            
            # Chyby - klasifikace podle typu
            if chyba and not uspesne:
                typ_chyby = self._klasifikuj_chybu(chyba)
                chyby_frekvence = self._data.get("chyby_frekvence", {})
                chyby_frekvence[typ_chyby] = chyby_frekvence.get(typ_chyby, 0) + 1
                self._data["chyby_frekvence"] = chyby_frekvence
            
            # Vypočítáme úspěšnost
            total = self._data["uspesnych"] + self._data["selhalo"]
            self._data["uspesnost_procent"] = (
                (self._data["uspesnych"] / total * 100) if total > 0 else 0.0
            )
            
            # Uložíme
            self._uloz()
            
            return self.ziskej_souhrn()
    
    def _klasifikuj_chybu(self, chyba: str) -> str:
        """Klasifikuje chybu podle obsahu"""
        chyba_lower = chyba.lower()
        
        if "syntax" in chyba_lower or "parse" in chyba_lower or "indent" in chyba_lower:
            return "syntax_error"
        elif "api" in chyba_lower or "build123d" in chyba_lower or "attribute" in chyba_lower:
            return "api_error"
        elif "import" in chyba_lower or "module" in chyba_lower:
            return "import_error"
        elif "timeout" in chyba_lower or "čas" in chyba_lower:
            return "timeout"
        elif "síť" in chyba_lower or "network" in chyba_lower or "connection" in chyba_lower:
            return "network_error"
        elif "stl" in chyba_lower or "export" in chyba_lower:
            return "export_error"
        else:
            return "ostatni"
    
    def ziskej_souhrn(self) -> Dict[str, Any]:
        """Vrátí souhrnné metriky"""
        with self._lock:
            return {
                "celkem_generovani": self._data["celkem_generovani"],
                "uspesnych": self._data["uspesnych"],
                "selhalo": self._data["selhalo"],
                "uspesnost_procent": round(self._data["uspesnost_procent"], 1),
                "kimi_pouziti": self._data["kimi_pouziti"],
                "minimax_pouziti": self._data["minimax_pouziti"],
                "celkova_cena_usd": round(self._data["celkova_cena_usd"], 4),
                "prumerna_cena_usd": round(self._data["prumerna_cena_usd"], 6),
                "prumerna_doba_s": round(self._data["prumerna_doba_s"], 1),
                "opraveno_pocet": self._data.get("opraveno_pocet", 0),
                "nejcastejsi_chyby": self._ziskej_top_chyby(5)
            }
    
    def _ziskej_top_chyby(self, n: int = 5) -> Dict[str, int]:
        """Vrátí N nejčastějších chyb"""
        chyby = self._data.get("chyby_frekvence", {})
        serazene = sorted(chyby.items(), key=lambda x: x[1], reverse=True)
        return dict(serazene[:n])
    
    def ziskej_historii(self, limit: int = 100) -> List[Dict]:
        """Vrátí posledních N záznamů z historie"""
        with self._lock:
            historie = self._data.get("historie", [])
            return historie[-limit:]
    
    def reset(self):
        """Resetuje všechny metriky (pouze pro testování)"""
        with self._lock:
            self._data = self._nacti_nebo_vytvor()
            self._data["celkem_generovani"] = 0
            self._data["uspesnych"] = 0
            self._data["selhalo"] = 0
            self._data["kimi_pouziti"] = 0
            self._data["minimax_pouziti"] = 0
            self._data["celkova_cena_usd"] = 0.0
            self._data["celkova_doba_s"] = 0.0
            self._data["opraveno_pocet"] = 0
            self._data["chyby_frekvence"] = {}
            self._data["historie"] = []
            self._uloz()


# Singleton instance pro celou aplikaci
_metriky_instance: Optional[Metriky] = None


def get_metriky(soubor_metrik: Optional[str] = None) -> Metriky:
    """Vrátí singleton instanci Metriky"""
    global _metriky_instance
    if _metriky_instance is None:
        _metriky_instance = Metriky(soubor_metrik)
    return _metriky_instance


if __name__ == "__main__":
    # Test
    m = Metriky()
    m.reset()
    
    # Simulace několika generování
    m.zaznamenaj("Kvádr 50x30x10", True, "kimi-k2.5", 0.015, 12.5)
    m.zaznamenaj("Válka průměr 20", True, "kimi-k2.5", 0.018, 15.2)
    m.zaznamenaj("Složitý model", False, "kimi-k2.5", 0.012, 8.5, "Chyba syntaxe", False)
    m.zaznamenaj("Složitý model retry", True, "minimax-m2.7", 0.022, 22.1, None, True)
    
    print("Souhrn metrik:")
    print(json.dumps(m.ziskej_souhrn(), indent=2, ensure_ascii=False))
