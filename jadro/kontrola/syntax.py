#!/usr/bin/env python3
"""
Kontrola Python kódu před spuštěním
Zkontroluje syntaxi a běžné chyby v build123d kódu
"""

import ast
import re
from typing import Dict, List, Tuple, Optional


class KontrolaSyntaxe:
    """Kontroluje kód před spuštěním"""
    
    # Známé chyby v build123d kódu
    ZNAME_CHYBY = {
        r"Location\([^)]*axis\s*=": {
            "chyba": "Location nepodporuje parametr 'axis'",
            "oprava": "Použij Location((x, y, z)) bez axis"
        },
        r"\.export_step\(": {
            "chyba": "Export rušíme - dělá se automaticky",
            "oprava": "Odstraň řádek s export_step"
        },
        r"\.export_stl\(": {
            "chyba": "Export rušíme - dělá se automaticky", 
            "oprava": "Odstraň řádek s export_stl"
        },
        r"part\.part\.wrapped": {
            "chyba": "Špatný přístup k property",
            "oprava": "Použij přímo part.part (bez .wrapped)"
        },
        r"Mode\.SUBTRACT": {
            "chyba": "extrude s SUBTRACT může selhat",
            "oprava": "Pro výřezy použij Hole() nebo Subtract()"
        },
        r"\.val\(\)": {
            "chyba": "BuildPart nemá metodu .val()",
            "oprava": "Použij přímo .part nebo .sketch"
        }
    }
    
    def zkontroluj(self, kod: str) -> Dict:
        """
        Zkontroluje kód a vrátí výsledek
        
        Returns:
            {
                "ok": bool,
                "syntax_chyba": Optional[str],
                "semanticke_chyby": List[Dict],
                "opraveny_kod": Optional[str]
            }
        """
        vysledek = {
            "ok": False,
            "syntax_chyba": None,
            "semanticke_chyby": [],
            "opraveny_kod": None
        }
        
        # 1. Kontrola Python syntaxe
        try:
            ast.parse(kod)
        except SyntaxError as e:
            vysledek["syntax_chyba"] = f"Řádek {e.lineno}: {e.msg}"
            return vysledek
        
        # 2. Kontrola známých chyb v build123d
        chyby = self._najdi_zname_chyby(kod)
        vysledek["semanticke_chyby"] = chyby
        
        # 3. Pokud jsou chyby, zkusíme opravit
        if chyby:
            opraveny = self._oprav_kod(kod, chyby)
            vysledek["opraveny_kod"] = opraveny
            # Znovu zkontrolujeme syntax opraveného kódu
            try:
                ast.parse(opraveny)
                vysledek["ok"] = True
            except SyntaxError:
                vysledek["ok"] = False
        else:
            vysledek["ok"] = True
            vysledek["opraveny_kod"] = kod
        
        return vysledek
    
    def _najdi_zname_chyby(self, kod: str) -> List[Dict]:
        """Najde známé chyby v kódu"""
        chyby = []
        for pattern, info in self.ZNAME_CHYBY.items():
            if re.search(pattern, kod):
                # Najdeme řádek
                for i, radek in enumerate(kod.split('\n'), 1):
                    if re.search(pattern, radek):
                        chyby.append({
                            "radek": i,
                            "text": radek.strip(),
                            "chyba": info["chyba"],
                            "oprava": info["oprava"]
                        })
                        break
        return chyby
    
    def _oprav_kod(self, kod: str, chyby: List[Dict]) -> str:
        """Zkusí opravit známé chyby"""
        opraveny = kod
        
        # Opravy - jednoduché regex substituce
        opraveny = re.sub(r"Location\(([^)]*)axis\s*=\s*\([^)]*\)\)", 
                         r"Location(\1", opraveny)
        opraveny = re.sub(r"^\s*\w+\.export_step\([^)]*\)\s*\n", "", opraveny, flags=re.MULTILINE)
        opraveny = re.sub(r"^\s*\w+\.export_stl\([^)]*\)\s*\n", "", opraveny, flags=re.MULTILINE)
        opraveny = re.sub(r"\.wrapped", "", opraveny)
        opraveny = re.sub(r"\.val\(\)", "", opraveny)
        
        return opraveny


def zkontroluj_a_oprav(kod: str) -> Tuple[bool, str, Optional[str]]:
    """
    Jednoduchá funkce pro kontrolu
    
    Returns:
        (ok, zprava, opraveny_kod)
    """
    k = KontrolaSyntaxe()
    vysledek = k.zkontroluj(kod)
    
    if vysledek["ok"] and not vysledek["semanticke_chyby"]:
        return True, "✅ Kód je v pořádku", vysledek["opraveny_kod"]
    
    if vysledek["syntax_chyba"]:
        return False, f"❌ Chyba syntaxe: {vysledek['syntax_chyba']}", None
    
    zprava = "⚠️ Nalezeny problémy:\n"
    for ch in vysledek["semanticke_chyby"]:
        zprava += f"  Řádek {ch['radek']}: {ch['chyba']}\n"
        zprava += f"    → {ch['oprava']}\n"
    
    if vysledek["ok"]:
        zprava += "\n✅ Kód byl automaticky opraven"
        return True, zprava, vysledek["opraveny_kod"]
    else:
        zprava += "\n❌ Oprava selhala - syntax stále chybná"
        return False, zprava, None


if __name__ == "__main__":
    # Test
    test_kod = """
from build123d import *

with BuildPart() as model:
    Box(50, 30, 10)
    
model.part.export_step("test.step")
"""
    ok, zprava, opraveny = zkontroluj_a_oprav(test_kod)
    print(zprava)
    if opraveny:
        print("\nOpravený kód:")
        print(opraveny)
