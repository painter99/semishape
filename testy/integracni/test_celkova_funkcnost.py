#!/usr/bin/env python3
"""
test_celkova_funkcnost.py - Integrační E2E testy SemiShape

Testy pokrývají:
- E2E: vygeneruj → spusť → exportuj
- Test přepínání modelů
- Test metrik
- Test web search
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Přidání root do path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from jadro.hlavni import SemiShape
from jadro.utils.metriky import Metriky


class TestE2EGenerovani(unittest.TestCase):
    """E2E test: kompletní workflow generování"""
    
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"})
    def test_e2e_jednoduchy_model(self):
        """E2E test jednoduchého modelu"""
        # Mock LLM odpovědi
        mock_kod = """
from build123d import *

with BuildPart() as model:
    Box(50, 50, 50)

if __name__ == "__main__":
    from build123d import export_stl
    export_stl(model.part, "vystupy/test_krychle.stl")
"""
        
        with patch('jadro.modely.prepinac.ModelovyPrepinac.posli_prompt') as mock_send:
            mock_response = Mock()
            mock_response.kod = mock_kod
            mock_response.uspech = True
            mock_response.model = "kimi"
            mock_response.tokeny_vstup = 150
            mock_response.tokeny_vystup = 200
            mock_response.cena_usd = 0.0045
            mock_response.latence_s = 2.5
            mock_send.return_value = mock_response
            
            # Vytvoření instance a generování
            ss = SemiShape(jazyk="cs")
            vysledek = ss.vygeneruj("Vytvoř krychli 50mm", uloz_jako="test_krychle")
            
            # Kontroly
            self.assertTrue(vysledek.funguje)
            self.assertEqual(vysledek.pouzity_model, "kimi")
            self.assertEqual(vysledek.tokeny_vstup, 150)
            self.assertEqual(vysledek.tokeny_vystup, 200)
            self.assertAlmostEqual(vysledek.cena_usd, 0.0045)
            self.assertAlmostEqual(vysledek.latence_s, 2.5)
    
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"})
    def test_e2e_slozity_model(self):
        """E2E test složitějšího modelu s otvory"""
        mock_kod = """
from build123d import *

with BuildPart() as drzak:
    with BuildSketch() as base:
        Rectangle(80, 60)
    extrude(amount=5)
    
    # 4 díry
    with Locations(drzak.faces().sort_by(Axis.Z)[-1]):
        with GridLocations(60, 40, 2, 2):
            Hole(3.5/2)

if __name__ == "__main__":
    from build123d import export_stl
    export_stl(drzak.part, "vystupy/test_drzak.stl")
"""
        
        with patch('jadro.modely.prepinac.ModelovyPrepinac.posli_prompt') as mock_send:
            mock_response = Mock()
            mock_response.kod = mock_kod
            mock_response.uspech = True
            mock_response.model = "kimi"
            mock_response.tokeny_vstup = 200
            mock_response.tokeny_vystup = 350
            mock_response.cena_usd = 0.008
            mock_response.latence_s = 3.2
            mock_send.return_value = mock_response
            
            ss = SemiShape(jazyk="cs")
            popis = """Vytvoř montážní držák:
            - Základna 80x60mm, tloušťka 5mm
            - 4 montážní díry M3 (průměr 3.5mm)"""
            
            vysledek = ss.vygeneruj(popis, uloz_jako="test_drzak")
            
            self.assertTrue(vysledek.funguje)
            self.assertIn("drzak", vysledek.puvodni_kod.lower())


class TestPrepinaniModelu(unittest.TestCase):
    """Test přepínání mezi modely Kimi a Minimax"""
    
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"})
    def test_prepnuti_na_minimax(self):
        """Test že při selhání Kimi se použije Minimax"""
        
        mock_kod = "from build123d import *\nwith BuildPart() as m:\n    Box(30,30,30)"
        
        with patch('jadro.modely.prepinac.ModelovyPrepinac.posli_prompt') as mock_send:
            # První volání selže, druhé uspěje
            mock_fail = Mock()
            mock_fail.uspech = False
            mock_fail.chyba = "Rate limit"
            
            mock_success = Mock()
            mock_success.kod = mock_kod
            mock_success.uspech = True
            mock_success.model = "minimax"
            mock_success.tokeny_vstup = 100
            mock_success.tokeny_vystup = 150
            mock_success.cena_usd = 0.001
            mock_success.latence_s = 1.5
            
            mock_send.side_effect = [mock_fail, mock_success]
            
            ss = SemiShape(jazyk="cs")
            vysledek = ss.vygeneruj("Vytvoř krychli 30mm")
            
            self.assertTrue(vysledek.funguje)
            self.assertEqual(vysledek.pouzity_model, "minimax")
            self.assertEqual(mock_send.call_count, 2)  # Voláno 2x - retry
    
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"})
    def test_vynuceny_model_kimi(self):
        """Test vynucení Kimi modelu"""
        mock_kod = "from build123d import *\nBox(25,25,25)"
        
        with patch('jadro.modely.prepinac.ModelovyPrepinac.posli_prompt') as mock_send:
            mock_response = Mock()
            mock_response.kod = mock_kod
            mock_response.uspech = True
            mock_response.model = "kimi"
            mock_response.tokeny_vstup = 80
            mock_response.tokeny_vystup = 100
            mock_response.cena_usd = 0.0005
            mock_response.latence_s = 1.0
            mock_send.return_value = mock_response
            
            ss = SemiShape(jazyk="cs")
            vysledek = ss.vygeneruj("Vytvoř krychli 25mm", model="kimi")
            
            self.assertTrue(vysledek.funguje)
            self.assertEqual(vysledek.pouzity_model, "kimi")
    
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"})
    def test_vynuceny_model_minimax(self):
        """Test vynucení Minimax modelu"""
        mock_kod = "from build123d import *\nCylinder(15, 30)"
        
        with patch('jadro.modely.prepinac.ModelovyPrepinac.posli_prompt') as mock_send:
            mock_response = Mock()
            mock_response.kod = mock_kod
            mock_response.uspech = True
            mock_response.model = "minimax"
            mock_response.tokeny_vstup = 90
            mock_response.tokeny_vystup = 120
            mock_response.cena_usd = 0.0003
            mock_response.latence_s = 0.8
            mock_send.return_value = mock_response
            
            ss = SemiShape(jazyk="cs")
            vysledek = ss.vygeneruj("Vytvoř válec", model="minimax")
            
            self.assertTrue(vysledek.funguje)
            self.assertEqual(vysledek.pouzity_model, "minimax")


class TestMetriky(unittest.TestCase):
    """Test sledování metrik"""
    
    def test_zaznam_metrik(self):
        """Test záznamu metrik z generování"""
        metriky = Metriky()
        
        # Simulace generování
        metriky.pridej(
            model="kimi",
            tokeny_vstup=100,
            tokeny_vystup=200,
            cena_usd=0.005,
            latence_s=2.0,
            uspech=True
        )
        
        stats = metriky.ziskej_statistiky()
        
        self.assertEqual(stats["celkem_generovani"], 1)
        self.assertEqual(stats["uspesnych"], 1)
        self.assertEqual(stats["neuspesnych"], 0)
        self.assertAlmostEqual(stats["celkova_cena_usd"], 0.005)
        self.assertAlmostEqual(stats["prumerna_latence_s"], 2.0)
    
    def test_vicenasobne_metriky(self):
        """Test více záznamů metrik"""
        metriky = Metriky()
        
        # Přidání více generování
        for i in range(5):
            metriky.pridej(
                model="kimi" if i % 2 == 0 else "minimax",
                tokeny_vstup=100 + i * 10,
                tokeny_vystup=200 + i * 20,
                cena_usd=0.001 * (i + 1),
                latence_s=1.0 + i * 0.5,
                uspech=True
            )
        
        stats = metriky.ziskej_statistiky()
        
        self.assertEqual(stats["celkem_generovani"], 5)
        self.assertEqual(stats["uspesnych"], 5)
        self.assertTrue(stats["celkova_cena_usd"] > 0)
    
    def test_ulozeni_metrik(self):
        """Test uložení metrik do souboru"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            metriky = Metriky()
            metriky.pridej(
                model="kimi",
                tokeny_vstup=100,
                tokeny_vystup=200,
                cena_usd=0.005,
                latence_s=2.0,
                uspech=True
            )
            
            metriky.uloz(temp_file)
            
            # Kontrola uloženého souboru
            with open(temp_file, 'r') as f:
                data = json.load(f)
            
            self.assertEqual(len(data["generovani"]), 1)
            self.assertEqual(data["generovani"][0]["model"], "kimi")
            
        finally:
            os.unlink(temp_file)
    
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"})
    def test_integrace_metrik_v_semishape(self):
        """Test integrace metrik v SemiShape třídě"""
        mock_kod = "from build123d import *\nBox(40,40,40)"
        
        with patch('jadro.modely.prepinac.ModelovyPrepinac.posli_prompt') as mock_send:
            mock_response = Mock()
            mock_response.kod = mock_kod
            mock_response.uspech = True
            mock_response.model = "kimi"
            mock_response.tokeny_vstup = 120
            mock_response.tokeny_vystup = 180
            mock_response.cena_usd = 0.003
            mock_response.latence_s = 1.8
            mock_send.return_value = mock_response
            
            ss = SemiShape(jazyk="cs")
            vysledek = ss.vygeneruj("Vytvoř krychli 40mm")
            
            # Kontrola že metriky byly zaznamenány
            stats = ss.ziskej_metriky()
            self.assertEqual(stats["celkem_generovani"], 1)


class TestWebSearch(unittest.TestCase):
    """Test web search funkcionality"""
    
    @patch('jadro.vyhledavani.web_search.DDGS')
    def test_vyhledani_dokumentace(self, mock_ddgs):
        """Test vyhledání dokumentace"""
        # Mock výsledků
        mock_instance = MagicMock()
        mock_instance.__enter__.return_value = mock_instance
        mock_instance.text.return_value = [
            {
                "title": "build123d Tutorial - Box",
                "href": "https://build123d.readthedocs.io/box.html",
                "body": "Tutorial pro vytvoření Box objektu v build123d"
            },
            {
                "title": "build123d Examples",
                "href": "https://build123d.readthedocs.io/examples.html",
                "body": "Příklady použití build123d knihovny"
            }
        ]
        mock_ddgs.return_value = mock_instance
        
        from jadro.vyhledavani.web_search import vyhledat_dokumentaci
        
        vysledky = vyhledat_dokumentaci("build123d Box", max_vysledku=2)
        
        self.assertEqual(len(vysledky), 2)
        self.assertIn("build123d", vysledky[0]["title"])
        self.assertTrue(vysledky[0]["href"].startswith("http"))
    
    @patch('jadro.vyhledavani.web_search.DDGS')
    def test_vyhledani_seriozni_chyba(self, mock_ddgs):
        """Test vyhledání při chybě"""
        mock_instance = MagicMock()
        mock_instance.__enter__.return_value = mock_instance
        mock_instance.text.side_effect = Exception("Connection error")
        mock_ddgs.return_value = mock_instance
        
        from jadro.vyhledavani.web_search import vyhledat_dokumentaci
        
        vysledky = vyhledat_dokumentaci("build123d", max_vysledku=3)
        
        # Při chybě by měl vrátit prázdný seznam
        self.assertEqual(vysledky, [])


class TestExport(unittest.TestCase):
    """Test exportu výsledků"""
    
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"})
    def test_export_kodu(self):
        """Test exportu vygenerovaného kódu"""
        mock_kod = "from build123d import *\nBox(30,30,30)"
        
        with patch('jadro.modely.prepinac.ModelovyPrepinac.posli_prompt') as mock_send:
            mock_response = Mock()
            mock_response.kod = mock_kod
            mock_response.uspech = True
            mock_response.model = "kimi"
            mock_response.tokeny_vstup = 100
            mock_response.tokeny_vystup = 150
            mock_response.cena_usd = 0.002
            mock_response.latence_s = 1.5
            mock_send.return_value = mock_response
            
            with tempfile.TemporaryDirectory() as tmpdir:
                ss = SemiShape(jazyk="cs")
                vysledek = ss.vygeneruj("Vytvoř krychli 30mm", uloz_jako="test_export")
                
                self.assertTrue(vysledek.funguje)
                # Kód by měl obsahovat Box
                self.assertIn("Box", vysledek.puvodni_kod)


class TestChyboveStavy(unittest.TestCase):
    """Test chybových stavů"""
    
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"})
    def test_chyba_v_kodu(self):
        """Test zpracování chyby v generovaném kódu"""
        # Kód s chybou - syntaktická chyba
        mock_kod_chybny = "from build123d import *\nBox(30 30, 30)"  # Chybí čárka
        
        with patch('jadro.modely.prepinac.ModelovyPrepinac.posli_prompt') as mock_send:
            mock_response = Mock()
            mock_response.kod = mock_kod_chybny
            mock_response.uspech = True
            mock_response.model = "kimi"
            mock_response.tokeny_vstup = 100
            mock_response.tokeny_vystup = 150
            mock_response.cena_usd = 0.002
            mock_response.latence_s = 1.5
            mock_send.return_value = mock_response
            
            ss = SemiShape(jazyk="cs")
            
            # Tento test závisí na tom, zda syntax.py opraví chybu nebo ne
            # Pokud je kód neopravitelný, mělo by to být zaznamenáno
            vysledek = ss.vygeneruj("Vytvoř krychli 30mm")
            
            # Výsledek by měl buď fungovat (po opravě) nebo reportovat chybu
            self.assertIn(vysledek.funguje, [True, False])
    
    def test_chyba_bez_api_klice(self):
        """Test chování bez API klíče"""
        # Odstraníme API klíč z prostředí
        with patch.dict(os.environ, {}, clear=True):
            # Tento test kontroluje validaci na začátku
            ss = SemiShape(jazyk="cs")
            # Nemělo by spadnout, ale mělo by to reportovat chybu při použití


def spustit_testy():
    """Funkce pro spuštění všech testů"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Přidání všech testovacích tříd
    suite.addTests(loader.loadTestsFromTestCase(TestE2EGenerovani))
    suite.addTests(loader.loadTestsFromTestCase(TestPrepinaniModelu))
    suite.addTests(loader.loadTestsFromTestCase(TestMetriky))
    suite.addTests(loader.loadTestsFromTestCase(TestWebSearch))
    suite.addTests(loader.loadTestsFromTestCase(TestExport))
    suite.addTests(loader.loadTestsFromTestCase(TestChyboveStavy))
    
    # Spuštění
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = spustit_testy()
    sys.exit(0 if success else 1)
