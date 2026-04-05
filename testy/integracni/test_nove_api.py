#!/usr/bin/env python3
"""
Integrační test pro nové API v0.2.0
Ověří že hlavní komponenty fungují
"""

import sys
from pathlib import Path

# Přidáme cesty
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from jadro.hlavni import SemiShape, Vysledek
from jadro.kontrola.syntax import zkontroluj_a_oprav


def test_kontrola_syntaxe():
    """Test: Kontrola syntaxe opraví známé chyby"""
    print("\n🧪 Test: Kontrola syntaxe")
    
    # Kód s chybou
    chybny_kod = """
from build123d import *
with BuildPart() as model:
    Box(50, 30, 10)
model.part.export_step("test.step")
"""
    
    ok, zprava, opraveny = zkontroluj_a_oprav(chybny_kod)
    
    assert ok, f"Kontrola měla projít: {zprava}"
    assert "export_step" not in opraveny, "Export kód měl být odstraněn"
    assert "Opraven" in zprava or "v pořádku" in zprava, "Měla být detekce chyby"
    
    print(f"  ✅ OK: {zprava[:50]}...")
    return True


def test_struktura_projektu():
    """Test: Všechny složky existují"""
    print("\n🧪 Test: Struktura projektu")
    
    koren = Path(__file__).parent.parent.parent
    
    pozadovane = [
        "jadro/hlavni.py",
        "jadro/modely/prepinac.py",
        "jadro/kontrola/syntax.py",
        "nastaveni/modely.yaml",
        "spusteni/sandbox.py",
        "spusteni/exporter.py",
    ]
    
    for soubor in pozadovane:
        cesta = koren / soubor
        assert cesta.exists(), f"Chybí: {soubor}"
        print(f"  ✅ {soubor}")
    
    return True


def test_nacteni_konfigurace():
    """Test: Konfigurace modelů se načte správně"""
    print("\n🧪 Test: Konfigurace")
    
    import yaml
    
    config_path = Path(__file__).parent.parent.parent / "nastaveni" / "modely.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    assert "hlavni_model" in config, "Chybí hlavni_model"
    assert "zalozni_model" in config, "Chybí zalozni_model"
    assert config["hlavni_model"]["nazev"] == "moonshotai/kimi-k2.5"
    assert config["zalozni_model"]["nazev"] == "minimax/minimax-m2.7"
    
    print(f"  ✅ Hlavní: {config['hlavni_model']['nazev']}")
    print(f"  ✅ Záloha: {config['zalozni_model']['nazev']}")
    
    return True


def test_vysledek_dataclass():
    """Test: Vysledek dataclass funguje"""
    print("\n🧪 Test: Vysledek struktura")
    
    v = Vysledek(
        funguje=True,
        kod="test",
        soubor_stl="/test.stl",
        pouzity_model="kimi-k2.5",
        cena_usd=0.01,
        chyba=None,
        opraveno=False
    )
    
    assert v.funguje is True
    assert v.pouzity_model == "kimi-k2.5"
    
    print(f"  ✅ Vysledek dataclass OK")
    return True


def run_all_tests():
    """Spustí všechny testy"""
    print("=" * 50)
    print("SemiShape v0.2.0 - Integrační testy")
    print("=" * 50)
    
    testy = [
        test_struktura_projektu,
        test_nacteni_konfigurace,
        test_kontrola_syntaxe,
        test_vysledek_dataclass,
    ]
    
    uspech = 0
    selhani = 0
    
    for test in testy:
        try:
            test()
            uspech += 1
        except Exception as e:
            print(f"  ❌ Selhalo: {e}")
            selhani += 1
    
    print("\n" + "=" * 50)
    print(f"Výsledek: {uspech} OK, {selhani} selhalo")
    print("=" * 50)
    
    return selhani == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
