#!/usr/bin/env python3
"""
pouziti.py - Praktické příklady použití SemiShape

Tento soubor obsahuje 7 praktických příkladů použití SemiShape pro různé
typy 3D modelů a funkcí.

Spuštění:
    python priklady/pouziti.py
"""

import os
import sys

# Přidání root do path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jadro.hlavni import SemiShape


def priklad_01_jednoducha_krychle():
    """Příklad 1: Jednoduchá krychle"""
    print("=" * 50)
    print("Příklad 1: Jednoduchá krychle 50mm")
    print("=" * 50)
    
    ss = SemiShape(jazyk="cs")
    vysledek = ss.vygeneruj("Vytvoř krychli 50mm")
    
    if vysledek.funguje:
        print(f"✅ Hotovo: {vysledek.soubor_stl}")
        print(f"💰 Cena: ${vysledek.cena_usd:.4f}")
    else:
        print(f"❌ Chyba: {vysledek.chyba}")
    
    return vysledek


def priklad_02_valec_s_otvorem():
    """Příklad 2: Válec s otvorem"""
    print("\n" + "=" * 50)
    print("Příklad 2: Válec s otvorem")
    print("=" * 50)
    
    ss = SemiShape(jazyk="cs")
    popis = """Vytvoř válec:
    - Průměr 40mm, výška 30mm
    - Skrz střed kulatý otvor průměru 10mm"""
    
    vysledek = ss.vygeneruj(popis, uloz_jako="valec_s_otvorem")
    
    if vysledek.funguje:
        print(f"✅ Hotovo: {vysledek.soubor_stl}")
        print(f"🤖 Použitý model: {vysledek.pouzity_model}")
    else:
        print(f"❌ Chyba: {vysledek.chyba}")
    
    return vysledek


def priklad_03_montazni_drzak():
    """Příklad 3: Složitější držák s dírami"""
    print("\n" + "=" * 50)
    print("Příklad 3: Montážní držák M3")
    print("=" * 50)
    
    ss = SemiShape(jazyk="cs")
    popis = """Vytvoř montážní držák:
    - Základna 80x60mm, tloušťka 5mm
    - 4 montážní díry M3 (průměr 3.5mm) v rozích
    - Vzdálenost děr od okraje 10mm
    - Všechny hrany zaobli 2mm"""
    
    vysledek = ss.vygeneruj(popis, uloz_jako="drzak_m3")
    
    if vysledek.funguje:
        print(f"✅ Hotovo: {vysledek.soubor_stl}")
        print(f"💰 Cena: ${vysledek.cena_usd:.4f}")
        print(f"⏱️  Latence: {vysledek.latence_s:.2f}s")
    else:
        print(f"❌ Chyba: {vysledek.chyba}")
    
    return vysledek


def priklad_04_sledovani_metrik():
    """Příklad 4: Použití s metrikami"""
    print("\n" + "=" * 50)
    print("Příklad 4: Sledování metrik generování")
    print("=" * 50)
    
    ss = SemiShape(jazyk="cs")
    
    # Vygenerujeme několik modelů
    modely = [
        "Vytvoř krychli 30mm",
        "Vytvoř válec průměru 20mm a výšky 40mm",
        "Vytvoř kouli průměru 25mm"
    ]
    
    for i, popis in enumerate(modely, 1):
        print(f"\n--- Model {i}/3 ---")
        vysledek = ss.vygeneruj(popis, uloz_jako=f"metriky_test_{i}")
        
        if vysledek.funguje:
            print(f"✅ {popis[:30]}...")
            print(f"   Tokeny vstup: {vysledek.tokeny_vstup}")
            print(f"   Tokeny výstup: {vysledek.tokeny_vystup}")
            print(f"   Cena: ${vysledek.cena_usd:.4f}")
            print(f"   Latence: {vysledek.latence_s:.2f}s")
        else:
            print(f"❌ Chyba: {vysledek.chyba}")
    
    # Uložení všech metrik
    metriky_file = "priklady_metriky.json"
    ss.uloz_metriky(metriky_file)
    print(f"\n📊 Metriky uloženy do: {metriky_file}")
    
    return ss.ziskej_metriky()


def priklad_05_prepinani_modelu():
    """Příklad 5: Přepínání mezi modely"""
    print("\n" + "=" * 50)
    print("Příklad 5: Test přepínání modelů Kimi/Minimax")
    print("=" * 50)
    
    ss = SemiShape(jazyk="cs")
    
    # Vynutíme Kimi
    print("\n--- Test s Kimi K2.5 ---")
    vysledek1 = ss.vygeneruj(
        "Vytvoř krychli 25mm",
        model="kimi",
        uloz_jako="kimi_test"
    )
    print(f"Model: {vysledek1.pouzity_model}")
    print(f"Cena: ${vysledek1.cena_usd:.4f}")
    
    # Vynutíme Minimax
    print("\n--- Test s Minimax 2.7 ---")
    vysledek2 = ss.vygeneruj(
        "Vytvoř válec průměru 15mm, výška 30mm",
        model="minimax",
        uloz_jako="minimax_test"
    )
    print(f"Model: {vysledek2.pouzity_model}")
    print(f"Cena: ${vysledek2.cena_usd:.4f}")
    
    # Automatické přepínání (retry)
    print("\n--- Automatické přepínání ---")
    vysledek3 = ss.vygeneruj("Vytvoř kouli 20mm")
    print(f"Použitý model: {vysledek3.pouzity_model}")
    
    return vysledek1, vysledek2, vysledek3


def priklad_06_web_search():
    """Příklad 6: Vyhledávání dokumentace"""
    print("\n" + "=" * 50)
    print("Příklad 6: Vyhledávání dokumentace build123d")
    print("=" * 50)
    
    try:
        from jadro.vyhledavani.web_search import vyhledat_dokumentaci
        
        print("\n--- Vyhledání dokumentace ---")
        vysledky = vyhledat_dokumentaci("build123d Box tutorial", max_vysledku=3)
        
        for i, vysledek in enumerate(vysledky, 1):
            print(f"\n{i}. {vysledek['title']}")
            print(f"   URL: {vysledek['href']}")
            print(f"   Popis: {vysledek['body'][:100]}...")
        
    except ImportError as e:
        print(f"⚠️  Modul web_search není dostupný: {e}")
        return None
    
    return vysledky


def priklad_07_komplexni_model():
    """Příklad 7: Komplexní model s více operacemi"""
    print("\n" + "=" * 50)
    print("Příklad 7: Komplexní držák s vlastnostmi")
    print("=" * 50)
    
    ss = SemiShape(jazyk="cs")
    popis = """Vytvoř držák pro montáž na zeď:
    - Základní deska 100x80mm, tloušťka 8mm
    - 4 kulaté díry průměru 4.5mm pro šrouby M4
    - Díry v rozích, 12mm od okraje
    - Výstupek uprostřed 40x40mm, výška 20mm
    - Skrz výstupek díra průměru 8mm
    - Všechny hrany zaobli 1.5mm fillet
    - Základna má 4 nožičky 10x10mm, výška 3mm"""
    
    print("\nGenerování komplexního modelu...")
    print("Tento příklad může trvat déle...")
    
    vysledek = ss.vygeneruj(popis, uloz_jako="komplexni_drzak")
    
    if vysledek.funguje:
        print(f"\n✅ Hotovo!")
        print(f"   Soubor: {vysledek.soubor_stl}")
        print(f"   Použitý model: {vysledek.pouzity_model}")
        print(f"   Tokeny: {vysledek.tokeny_vstup} → {vysledek.tokeny_vystup}")
        print(f"   Cena: ${vysledek.cena_usd:.4f}")
    else:
        print(f"\n❌ Chyba: {vysledek.chyba}")
    
    return vysledek


def main():
    """Hlavní funkce spouštějící všechny příklady"""
    print("""
    ╔═══════════════════════════════════════════════════╗
    ║     SemiShape v0.2.0 - Praktické příklady        ║
    ╚═══════════════════════════════════════════════════╝
    """)
    
    # Kontrola API klíče
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv("OPENROUTER_API_KEY"):
        print("⚠️  VAROVÁNÍ: OPENROUTER_API_KEY nenalezen v .env")
        print("   Nastavte API klíč před spuštěním příkladů.")
        return
    
    try:
        # Spuštění všech příkladů
        priklad_01_jednoducha_krychle()
        priklad_02_valec_s_otvorem()
        priklad_03_montazni_drzak()
        priklad_04_sledovani_metrik()
        priklad_05_prepinani_modelu()
        priklad_06_web_search()
        priklad_07_komplexni_model()
        
        print("\n" + "=" * 50)
        print("✅ Všechny příklady dokončeny!")
        print("=" * 50)
        print("\nVygenerované soubory naleznete v adresáři: vystupy/")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Uživatel přerušil běh příkladů")
    except Exception as e:
        print(f"\n\n❌ Chyba při běhu příkladů: {e}")
        raise


if __name__ == "__main__":
    main()
