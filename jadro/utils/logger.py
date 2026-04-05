#!/usr/bin/env python3
"""
Strukturované JSON logování pro SemiShape

Vlastnosti:
- JSON formát pro každé generování
- Uložení promptu, kódu, výsledku
- Rotace logů (max 10MB, 5 souborů)
- Thread-safe
"""

import json
import gzip
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from threading import Lock


class SemiShapeLogger:
    """
    Strukturovaný JSON logger s rotací.
    
    Každý záznam je JSON objekt na samostatném řádku (JSONL formát).
    Rotuje soubory: log → log.1 → log.2 → ... → log.5 (archivováno)
    """
    
    MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    MAX_BACKUPS = 5
    
    def __init__(self, log_dir: Optional[str] = None):
        """
        Args:
            log_dir: Adresář pro log soubory
                     (default: /a0/usr/projects/semishape/data/logs)
        """
        if log_dir is None:
            self.log_dir = Path("/a0/usr/projects/semishape/data/logs")
        else:
            self.log_dir = Path(log_dir)
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_file = self.log_dir / "semishape.log"
        self._lock = Lock()
        
        # Vytvoříme log soubor pokud neexistuje
        if not self.log_file.exists():
            self.log_file.touch()
    
    def _rotuj(self):
        """Rotuje log soubory pokud je potřeba"""
        if not self.log_file.exists():
            return
        
        # Kontrola velikosti
        if self.log_file.stat().st_size < self.MAX_BYTES:
            return
        
        # Rotace: log.4 → log.5 (gzip), log.3 → log.4, ..., log → log.1
        for i in range(self.MAX_BACKUPS - 1, 0, -1):
            zdroj = self.log_dir / f"semishape.log.{i}"
            cil = self.log_dir / f"semishape.log.{i + 1}"
            
            if zdroj.exists():
                if i == self.MAX_BACKUPS - 1:
                    # Poslední soubor zkomprimujeme
                    with open(zdroj, "rb") as f_in:
                        with gzip.open(str(cil) + ".gz", "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    zdroj.unlink()
                else:
                    if cil.exists():
                        cil.unlink()
                    shutil.move(str(zdroj), str(cil))
        
        # Přesuň hlavní log
        cil = self.log_dir / "semishape.log.1"
        if cil.exists():
            cil.unlink()
        shutil.move(str(self.log_file), str(cil))
        
        # Vytvoří nový prázdný log
        self.log_file.touch()
    
    def loguj(
        self,
        uroven: str,  # "INFO", "WARNING", "ERROR"
        popis: str,
        prompt: Optional[str] = None,
        kod: Optional[str] = None,
        vysledek: Optional[Dict] = None,
        chyba: Optional[str] = None,
        extra: Optional[Dict] = None
    ):
        """
        Zaloguje strukturovaná data o generování.
        
        Args:
            uroven: Úroveň záznamu (INFO, WARNING, ERROR)
            popis: Krátký popis události
            prompt: Vstupní prompt uživatele
            kod: Vygenerovaný Python kód
            vysledek: Slovník s výsledkem generování
            chyba: Chybová zpráva pokud selhalo
            extra: Další metadata
        """
        with self._lock:
            # Rotace pokud je potřeba
            self._rotuj()
            
            # Sestavíme záznam
            zaznam = {
                "timestamp": datetime.now().isoformat(),
                "uroven": uroven,
                "popis": popis,
            }
            
            # Volitelné pole
            if prompt is not None:
                zaznam["prompt"] = prompt[:5000] if len(prompt) > 5000 else prompt  # Limit 5k znaků
            
            if kod is not None:
                zaznam["kod"] = kod[:10000] if len(kod) > 10000 else kod  # Limit 10k znaků
            
            if vysledek is not None:
                zaznam["vysledek"] = vysledek
            
            if chyba is not None:
                zaznam["chyba"] = chyba[:1000] if len(chyba) > 1000 else chyba
            
            if extra is not None:
                zaznam["extra"] = extra
            
            # Zapisujeme jako JSONL (JSON na řádku)
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(zaznam, ensure_ascii=False) + "\n")
    
    def loguj_generovani(
        self,
        prompt: str,
        kod: str,
        funguje: bool,
        pouzity_model: str,
        cena_usd: float,
        doba_s: float,
        chyba: Optional[str] = None,
        soubor_stl: Optional[str] = None,
        opraveno: bool = False
    ):
        """
        Specializované logování pro výsledek generování.
        
        Args:
            prompt: Vstupní popis
            kod: Vygenerovaný Python kód
            funguje: True pokud kód fungoval
            pouzity_model: Jaký model byl použit
            cena_usd: Orientační cena
            doba_s: Doba generování v sekundách
            chyba: Chyba pokud selhalo
            soubor_stl: Cesta k výstupnímu STL
            opraveno: Zda byl kód opraven
        """
        vysledek = {
            "funguje": funguje,
            "pouzity_model": pouzity_model,
            "cena_usd": round(cena_usd, 6),
            "doba_s": round(doba_s, 2),
            "soubor_stl": soubor_stl,
            "opraveno": opraveno
        }
        
        uroven = "INFO" if funguje else "ERROR"
        popis = "Generování úspěšné" if funguje else "Generování selhalo"
        
        self.loguj(
            uroven=uroven,
            popis=popis,
            prompt=prompt,
            kod=kod,
            vysledek=vysledek,
            chyba=chyba,
            extra={"event_type": "generation"}
        )
    
    def loguj_info(self, zprava: str, extra: Optional[Dict] = None):
        """Jednoduché info logování"""
        self.loguj("INFO", zprava, extra=extra)
    
    def loguj_varovani(self, zprava: str, extra: Optional[Dict] = None):
        """Logování varování"""
        self.loguj("WARNING", zprava, extra=extra)
    
    def loguj_chybu(self, zprava: str, chyba: Optional[Exception] = None, extra: Optional[Dict] = None):
        """Logování chyby"""
        extra_data = extra or {}
        if chyba:
            extra_data["exception"] = str(chyba)
        self.loguj("ERROR", zprava, chyba=str(chyba) if chyba else None, extra=extra_data)
    
    def ziskej_posledni(self, n: int = 10) -> list:
        """Vrátí posledních N záznamů z logu"""
        with self._lock:
            zaznamy = []
            
            # Hlavní log soubor
            if self.log_file.exists():
                zaznamy.extend(self._cti_log_soubor(self.log_file))
            
            # Starší rotované soubory (od nejnovějšího)
            for i in range(1, self.MAX_BACKUPS + 1):
                soubor = self.log_dir / f"semishape.log.{i}"
                if soubor.exists():
                    zaznamy.extend(self._cti_log_soubor(soubor))
                
                # Zkontrolujeme i gzipnuté
                soubor_gz = self.log_dir / f"semishape.log.{i}.gz"
                if soubor_gz.exists():
                    zaznamy.extend(self._cti_log_soubor(soubor_gz, compressed=True))
            
            # Seřadíme podle timestamp a vrátíme poslední N
            zaznamy.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return zaznamy[:n]
    
    def _cti_log_soubor(self, soubor: Path, compressed: bool = False) -> list:
        """Přečte záznamy z log souboru"""
        zaznamy = []
        
        try:
            if compressed:
                with gzip.open(soubor, "rt", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                zaznamy.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
            else:
                with open(soubor, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                zaznamy.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
        except Exception:
            pass
        
        return zaznamy
    
    def vymaz_logy(self):
        """Smaže všechny logy (pouze pro testování)"""
        with self._lock:
            # Hlavní log
            if self.log_file.exists():
                self.log_file.unlink()
                self.log_file.touch()
            
            # Rotované soubory
            for i in range(1, self.MAX_BACKUPS + 1):
                soubor = self.log_dir / f"semishape.log.{i}"
                if soubor.exists():
                    soubor.unlink()
                soubor_gz = self.log_dir / f"semishape.log.{i}.gz"
                if soubor_gz.exists():
                    soubor_gz.unlink()


# Singleton instance
_logger_instance: Optional[SemiShapeLogger] = None


def get_logger(log_dir: Optional[str] = None) -> SemiShapeLogger:
    """Vrátí singleton instanci Loggeru"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = SemiShapeLogger(log_dir)
    return _logger_instance


if __name__ == "__main__":
    # Test
    logger = SemiShapeLogger()
    logger.vymaz_logy()
    
    # Test logování
    logger.loguj_generovani(
        prompt="Vytvoř kvádr 50x30x10",
        kod="from build123d import *\nbox = Box(50, 30, 10)",
        funguje=True,
        pouzity_model="kimi-k2.5",
        cena_usd=0.015,
        doba_s=12.5,
        soubor_stl="/vystupy/test.stl",
        opraveno=False
    )
    
    logger.loguj_generovani(
        prompt="Složitý model",
        kod="# Nevalidní kód",
        funguje=False,
        pouzity_model="kimi-k2.5",
        cena_usd=0.012,
        doba_s=8.5,
        chyba="SyntaxError: invalid syntax"
    )
    
    logger.loguj_info("Systém spuštěn", extra={"verze": "0.2.0"})
    logger.loguj_varovani("Model nezná některé parametry")
    
    print("Poslední záznamy:")
    for z in logger.ziskej_posledni(3):
        print(f"  {z['timestamp']}: {z['popis']}")
