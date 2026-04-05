# Changelog

Všechny významné změny v projektu SemiShape budou dokumentovány v tomto souboru.

Formát je založen na [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.2.0] - 2026-04-05

### Přidáno

#### Monitoring a Metriky
- **Sledování nákladů**: Automatický výpočet ceny za každé generování ($/token)
- **Metriky výkonu**: Měření latence, tokenů vstup/výstup
- **Statistiky**: Celkový přehled generování, úspěšnost, průměrné ceny
- **Export metrik**: Ukládání do JSON pro analýzu nákladů

#### Web Search
- **DuckDuckGo integrace**: Vyhledávání aktuální build123d dokumentace
- **GitHub monitoring**: Sledování nových commitů v build123d repozitáři
- **Automatické hledání**: Vyhledání dokumentace pro neznámé koncepty

#### Dva AI Modely
- **Kimi K2.5** (hlavní model): $0.38/$1.91 per 1M tokenů, nejlepší pro kód
- **Minimax 2.7** (záložní model): $0.10/$0.27 per 1M tokenů, ekonomická varianta
- **Automatické přepínání**: Fallback na Minimax při selhání Kimi
- **Manuální výběr**: Možnost vynutit konkrétní model

#### Kontrola a Opravy Kódu
- **Syntax validator**: Kontrola Python kódu před spuštěním
- **Automatické opravy**: Detekce a oprava běžných chyb v build123d
- **Odstranění nebezpečného kódu**: Odstranění importů jako os, sys, subprocess
- **Kontrola exportů**: Zajištění správného STL exportu

#### Nová Architektura
- **Přepracovaná struktura**:
  - `jadro/` - Hlavní logika
  - `spusteni/` - Spuštění a export
  - `vyhledavani/` - Web search a monitoring
  - `kontrola/` - Validace a opravy kódu
  - `utils/` - Metriky a pomocné funkce
- **Modulární design**: Snadná rozšiřitelnost a testování

#### Dovednosti (Skills)
- **Agent Zero integrace**: SemiShape jako skill pro AI agenty
- **Loader dovedností**: Dynamické načítání skill modulů

#### Dokumentace a Příklady
- **Rozšířená dokumentace**: Sekce Monitoring, Web Search, Skills
- **7 praktických příkladů**: Od jednoduché krychle po komplexní držák
- **Integrační testy**: E2E testy pro všechny komponenty
- **Testovací sada**: Mock testy pro všechny funkce

### Změněno
- Vylepšený prompt pro lepší generování build123d kódu
- Optimalizované parametry pro český jazyk
- Rychlejší sandbox spuštění

### Opraveno
- Oprava exportu STL - správný přístup k `.part` atributu
- Oprava chyby 'property object has no attribute wrapped'
- Stabilnější detekce vygenerovaného modelu

### Bezpečnost
- Sandbox spuštění s omezeným prostředím
- Validace všech vstupů před spuštěním
- Bezpečné odstranění neautorizovaných operací

---

## [0.1.0] - 2025-03-20

### Přidáno
- Základní generování build123d kódu z textového popisu
- Telegram bot integrace
- Jednoduchý RAG systém pro dokumentaci
- Export do STL formátu
- Podpora češtiny a angličtiny

---

## Roadmap

### [0.3.0] - Plánováno
- [ ] Granite 4.0 H micro fine-tuned model
- [ ] QLoRA trénink na vlastním datasetu
- [ ] Vylepšený RAG s hybridním retrieverem
- [ ] Podpora STEP exportu
- [ ] Parametrické modely s proměnnými

### [1.0.0] - Plánováno
- [ ] Plná podpora českého jazyka (B1 úroveň)
- [ ] Kompletní dokumentace v češtině
- [ ] GUI webové rozhraní
- [ ] Knihovna předvytvořených komponent
- [ ] Validace modelů pro 3D tisk

---

## Autoři

- **Pavel Mareš** ([painter99](https://github.com/painter99)) - Vývoj a návrh

## Poděkování

- [build123d](https://github.com/gumyr/build123d) tým za vynikající CAD knihovnu
- Komunita Open Source za inspiraci a podporu
