#!/usr/bin/env python3
"""
Jednotkové testy pro metriky
"""

import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pytest

from jadro.utils.metriky import Metriky, ZaznamGenerovani, get_metriky


class TestMetriky:
    """Testy pro metriky systém"""
    
    @pytest.fixture
    def temp_dir(self):
        """Vytvoří dočasný adresář pro testy"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
    @pytest.fixture
    def metriky(self, temp_dir):
        """Vytvoří instanci metrik s dočasným souborem"""
        soubor = Path(temp_dir) / "test_metriky.json"
        m = Metriky(str(soubor))
        m.reset()
        return m
    
    def test_zaznamenaj_uspesne(self, metriky):
        """Test záznamu úspěšného generování"""
        vysledek = metriky.zaznamenaj(
            popis="Test kvádr",
            uspesne=True,
            pouzity_model="kimi-k2.5",
            cena_usd=0.015,
            doba_s=12.5,
            chyba=None,
            opraveno=False
        )
        
        assert vysledek["celkem_generovani"] == 1
        assert vysledek["uspesnych"] == 1
        assert vysledek["selhalo"] == 0
        assert vysledek["uspesnost_procent"] == 100.0
        assert vysledek["kimi_pouziti"] == 1
    
    def test_zaznamenaj_s_chybou(self, metriky):
        """Test záznamu neúspěšného generování"""
        vysledek = metriky.zaznamenaj(
            popis="Složitý model",
            uspesne=False,
            pouzity_model="kimi-k2.5",
            cena_usd=0.012,
            doba_s=8.5,
            chyba="SyntaxError: invalid syntax",
            opraveno=False
        )
        
        assert vysledek["celkem_generovani"] == 1
        assert vysledek["uspesnych"] == 0
        assert vysledek["selhalo"] == 1
        assert vysledek["uspesnost_procent"] == 0.0
        assert "nejcastejsi_chyby" in vysledek
    
    def test_pocitani_cen(self, metriky):
        """Test výpočtu cen"""
        metriky.zaznamenaj("Test 1", True, "kimi-k2.5", 0.010, 10.0)
        metriky.zaznamenaj("Test 2", True, "kimi-k2.5", 0.020, 15.0)
        metriky.zaznamenaj("Test 3", True, "minimax-m2.7", 0.030, 20.0)
        
        vysledek = metriky.ziskej_souhrn()
        
        assert vysledek["celkova_cena_usd"] == 0.060
        assert vysledek["prumerna_cena_usd"] == 0.020
        assert vysledek["kimi_pouziti"] == 2
        assert vysledek["minimax_pouziti"] == 1
    
    def test_pocitani_doby(self, metriky):
        """Test výpočtu průměrné doby"""
        metriky.zaznamenaj("Test 1", True, "kimi-k2.5", 0.010, 10.0)
        metriky.zaznamenaj("Test 2", True, "kimi-k2.5", 0.020, 20.0)
        
        vysledek = metriky.ziskej_souhrn()
        
        assert vysledek["prumerna_doba_s"] == 15.0
    
    def test_klasifikace_chyb(self, metriky):
        """Test klasifikace různých typů chyb"""
        # Syntax error
        metriky.zaznamenaj("Test 1", False, "kimi-k2.5", 0.010, 5.0, "IndentationError: unexpected indent")
        # API error
        metriky.zaznamenaj("Test 2", False, "kimi-k2.5", 0.010, 5.0, "AttributeError: 'NoneType' object has no attribute 'extrude'")
        # Import error
        metriky.zaznamenaj("Test 3", False, "kimi-k2.5", 0.010, 5.0, "ModuleNotFoundError: No module named 'build123d'")
        
        vysledek = metriky.ziskej_souhrn()
        chyby = vysledek["nejcastejsi_chyby"]
        
        assert "syntax_error" in chyby
        assert "api_error" in chyby
        assert "import_error" in chyby
    
    def test_pocitani_oprav(self, metriky):
        """Test počítání automatických oprav"""
        metriky.zaznamenaj("Test 1", True, "kimi-k2.5", 0.010, 10.0, None, True)
        metriky.zaznamenaj("Test 2", True, "kimi-k2.5", 0.010, 10.0, None, True)
        metriky.zaznamenaj("Test 3", True, "kimi-k2.5", 0.010, 10.0, None, False)
        
        vysledek = metriky.ziskej_souhrn()
        
        assert vysledek["opraveno_pocet"] == 2
    
    def test_persistece(self, temp_dir):
        """Test uložení a načtení metrik"""
        soubor = Path(temp_dir) / "test_metriky.json"
        
        # První instance
        m1 = Metriky(str(soubor))
        m1.reset()
        m1.zaznamenaj("Test", True, "kimi-k2.5", 0.010, 10.0)
        
        # Druhá instance - načte stejný soubor
        m2 = Metriky(str(soubor))
        vysledek = m2.ziskej_souhrn()
        
        assert vysledek["celkem_generovani"] == 1
    
    def test_historie(self, metriky):
        """Test ukládání historie"""
        for i in range(5):
            metriky.zaznamenaj(f"Test {i}", True, "kimi-k2.5", 0.010, 10.0)
        
        historie = metriky.ziskej_historii(limit=3)
        
        assert len(historie) == 3
        # Nejnovější první
        assert "Test 4" in historie[0]["popis"] or "Test 3" in historie[0]["popis"]
    
    def test_limit_historie(self, metriky):
        """Test limitu historie (max 1000 záznamů)"""
        # Simulujeme více záznamů než limit
        for i in range(1005):
            metriky.zaznamenaj(f"Test {i}", True, "kimi-k2.5", 0.001, 1.0)
        
        historie = metriky.ziskej_historii(limit=1001)
        
        # Mělo by být uloženo jen posledních 1000
        assert len(historie) <= 1000
    
    def test_zkraceni_popisu(self, metriky):
        """Test zkrácení dlouhého popisu"""
        dlouhy_popis = "A" * 150
        metriky.zaznamenaj(dlouhy_popis, True, "kimi-k2.5", 0.010, 10.0)
        
        historie = metriky.ziskej_historii(limit=1)
        
        assert len(historie[0]["popis"]) <= 103  # 100 + "..."
    
    def test_zkraceni_chyby(self, metriky):
        """Test zkrácení dlouhé chyby"""
        dlouha_chyba = "Error: " + "X" * 500
        metriky.zaznamenaj("Test", False, "kimi-k2.5", 0.010, 5.0, dlouha_chyba)
        
        historie = metriky.ziskej_historii(limit=1)
        
        assert len(historie[0]["chyba"]) <= 200
    
    def test_reset(self, metriky):
        """Test resetování metrik"""
        metriky.zaznamenaj("Test", True, "kimi-k2.5", 0.010, 10.0)
        metriky.reset()
        
        vysledek = metriky.ziskej_souhrn()
        
        assert vysledek["celkem_generovani"] == 0
        assert vysledek["uspesnych"] == 0
        assert vysledek["celkova_cena_usd"] == 0.0


class TestZaznamGenerovani:
    """Testy pro dataclass ZaznamGenerovani"""
    
    def test_vytvoreni(self):
        """Test vytvoření záznamu"""
        zaznam = ZaznamGenerovani(
            timestamp=datetime.now().isoformat(),
            popis="Test",
            uspesne=True,
            pouzity_model="kimi-k2.5",
            cena_usd=0.015,
            doba_s=12.5,
            chyba=None,
            opraveno=False
        )
        
        assert zaznam.popis == "Test"
        assert zaznam.uspesne is True


class TestGetMetriky:
    """Testy pro singleton funkci get_metriky"""
    
    def test_singleton(self, temp_dir):
        """Test že get_metriky vrací stejnou instanci"""
        soubor = Path(temp_dir) / "singleton.json"
        
        # Resetujeme globální instanci
        import jadro.utils.metriky as m
        m._metriky_instance = None
        
        m1 = get_metriky(str(soubor))
        m2 = get_metriky(str(soubor))
        
        assert m1 is m2
    
    def test_singleton_zachovava_stav(self, temp_dir):
        """Test že singleton zachovává stav"""
        soubor = Path(temp_dir) / "singleton2.json"
        
        # Reset
        import jadro.utils.metriky as m
        m._metriky_instance = None
        
        m1 = get_metriky(str(soubor))
        m1.zaznamenaj("Test", True, "kimi-k2.5", 0.010, 10.0)
        
        # Stejná instance
        m2 = get_metriky(str(soubor))
        vysledek = m2.ziskej_souhrn()
        
        assert vysledek["celkem_generovani"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
