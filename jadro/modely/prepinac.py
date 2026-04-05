#!/usr/bin/env python3
"""
Přepínač mezi modely Kimi K2.5 a Minimax M2.7
Když Kimi selže, automaticky zpří se Minimax
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any


class PrepincacModelu:
    """
    Hlavní rozhraní pro generování kódu.
    Automaticky zvolí nejlepší dostupný model.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        # Načteme nastavení
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "nastaveni" / "modely.yaml"
        
        with open(config_path, "r", encoding="utf-8") as f:
            self.nastaveni = yaml.safe_load(f)
        
        self.hlavni = self.nastaveni["hlavni_model"]
        self.zaloha = self.nastaveni["zalozni_model"]
        
    def generuj(self, prompt: str, jazyk: str = "cs", with_rag: bool = True) -> Dict[str, Any]:
        """
        Vygeneruje kód pro zadaný popis
        
        Args:
            prompt: Popis modelu v češtině nebo angličtině
            jazyk: "cs" (přednastaveno) nebo "en" 
            with_rag: Použít dokumentaci build123d (ANO)
            
        Returns:
            {
                "kod": str,              # Vygenerovaný Python kód
                "uspesne": bool,          # True = kód vygenerován
                "pouzity_model": str,     # Který model byl použit
                "cena": float,            # Orientační cena v USD
                "chyba": Optional[str]    # Chybová zpráva pokud selhalo
            }
        """
        # Nejprve zkusíme Kimi
        vysledek = self._zkus_kimi(prompt, jazyk, with_rag)
        
        if vysledek["uspesne"]:
            return vysledek
            
        # Kimi selhal → zkusíme Minimax
        print(f"⚠️ Kimi selhal: {vysledek['chyba']}")
        print("🔄 Zkouším Minimax M2.7...")
        
        vysledek = self._zkus_minimax(prompt, jazyk, with_rag)
        
        if vysledek["uspesne"]:
            return vysledek
            
        # Oba modely selhaly
        return {
            "kod": "",
            "uspesne": False,
            "pouzity_model": "none",
            "cena": 0.0,
            "chyba": f"Kimi: {vysledek.get('chyba', 'Neznámá chyba')}, Minimax: {vysledek.get('chyba', 'Neznámá chyba')}"
        }
    
    def _zkus_kimi(self, prompt: str, jazyk: str, with_rag: bool) -> Dict[str, Any]:
        """Zkusí vygenerovat s Kimi K2.5"""
        try:
            # Importujeme stávající SemiShape
            from src.semishape import SemiShape
            
            ss = SemiShape(
                model="moonshotai/kimi-k2.5",
                provider="openrouter",
                language=jazyk
            )
            
            # Vygenerujeme kód
            result = ss.generate_code(prompt)
            
            if result.has_errors():
                return {
                    "kod": "",
                    "uspesne": False,
                    "pouzity_model": "kimi-k2.5",
                    "cena": 0.0,
                    "chyba": str(result.stderr) if result.stderr else "Chyba při generování"
                }
            
            # Výpočet ceny (orientační)
            tokeny_vstup = len(prompt) // 4  # Přibližně
            tokeny_vystup = len(result.code) // 4
            cena = (tokeny_vstup * self.hlavni["cena_vstup"] + 
                   tokeny_vystup * self.hlavni["cena_vystup"]) / 1000000
            
            return {
                "kod": result.code,
                "uspesne": True,
                "pouzity_model": "kimi-k2.5",
                "cena": cena,
                "chyba": None
            }
            
        except Exception as e:
            return {
                "kod": "",
                "uspesne": False,
                "pouzity_model": "kimi-k2.5",
                "cena": 0.0,
                "chyba": str(e)
            }
    
    def _zkus_minimax(self, prompt: str, jazyk: str, with_rag: bool) -> Dict[str, Any]:
        """Zkusí vygenerovat s Minimax M2.7"""
        try:
            from src.semishape import SemiShape
            
            ss = SemiShape(
                model="minimax/minimax-m2.7",
                provider="openrouter",
                language=jazyk
            )
            
            result = ss.generate_code(prompt)
            
            if result.has_errors():
                return {
                    "kod": "",
                    "uspesne": False,
                    "pouzity_model": "minimax-m2.7",
                    "cena": 0.0,
                    "chyba": str(result.stderr) if result.stderr else "Chyba při generování"
                }
            
            tokeny_vstup = len(prompt) // 4
            tokeny_vystup = len(result.code) // 4
            cena = (tokeny_vstup * self.zaloha["cena_vstup"] + 
                   tokeny_vystup * self.zaloha["cena_vystup"]) / 1000000
            
            return {
                "kod": result.code,
                "uspesne": True,
                "pouzity_model": "minimax-m2.7",
                "cena": cena,
                "chyba": None
            }
            
        except Exception as e:
            return {
                "kod": "",
                "uspesne": False,
                "pouzity_model": "minimax-m2.7",
                "cena": 0.0,
                "chyba": str(e)
            }


if __name__ == "__main__":
    # Test
    p = PrepincacModelu()
    vysledek = p.generuj("Vytvoř kvádr 50x30x10mm")
    print(f"Výsledek: {vysledek}")
