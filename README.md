# SemiShape v0.2.0

> **AI asistent pro generování 3D CAD modelů z textového popisu**

[![Version](https://img.shields.io/badge/Version-0.2.0-blue)](https://github.com/painter99/semishape)
[![License](https://img.shields.io/badge/License-Apache%202.0-green)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://python.org)

---

SemiShape je nástroj, který transformuje popis v češtině (nebo angličtině) na Python kód pro knihovnu **build123d** a vygeneruje **STL** soubor připravený pro 3D tisk.

**Příklad:**
```
"Vytvoř krychli 50mm s kulatým otvorem průměru 20mm ve středu"
        ↓
    [SemiShape AI]
        ↓
    model.stl ✅
```

---

## Co je nového ve v0.2.0

| Funkce | Popis |
|--------|-------|
| **🎭 Dva modely** | Kimi K2.5 (hlavní) + Minimax 2.7 (záloha) |
| **🔧 Automatické opravy** | Detekuje a opraví běžné chyby v kódu před spuštěním |
| **💰 Sledování nákladů** | Odhad ceny za každé generování |
| **🛡️ Kontrola kódu** | Ověří syntaxi před spuštěním |
| **🔄 Retry mechanismus** | Když Kimi selže, automaticky Minimax |

---

## Rychlý start

### Instalace

```bash
# Naklonuj repozitář
git clone git@github.com:painter99/semishape.git
cd semishape

# Vytvoř virtuální prostředí
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

# Nainstaluj závislosti
pip install -r requirements.txt
```

### Nastavení API klíče

```bash
# Vytvoř .env soubor v rootu projektu
echo "OPENROUTER_API_KEY=sk-or-v1-..." > .env
```

### Použití

#### Přímo z Pythonu:

```python
from jadro.hlavni import SemiShape

# Vytvoříme instanci
ss = SemiShape(jazyk="cs")

# Vygenerujeme model
vysledek = ss.vygeneruj("Vytvoř kvádr 50x30x10mm")

if vysledek.funguje:
    print(f"✅ Hotovo: {vysledek.soubor_stl}")
    print(f"💰 Cena: ${vysledek.cena_usd:.4f}")
    print(f"🤖 Použitý model: {vysledek.pouzity_model}")
else:
    print(f"❌ Chyba: {vysledek.chyba}")
```

#### Z příkazové řádky:

```bash
# Jednoduchý kvádr
python -m jadro.hlavni "Vytvoř kvádr 50x30x10mm"

# Složitější model s vlastním názvem
python -m jadro.hlavni "Vytvoř držák s 4 dírami" --jmeno drzak

# Anglicky
python -m jadro.hlavni "Create a box 50x30x10mm" --jazyk en
```

---

## Struktura projektu

```
semishape/
├── jadro/                  # Hlavní logika
│   ├── hlavni.py          # Hlavní API
│   ├── modely/
│   │   └── prepinac.py    # Přepínání Kimi/Minimax
│   ├── kontrola/
│   │   └── syntax.py      # Kontrola a oprava kódu
│   └── ...
│
├── nastaveni/
│   └── modely.yaml        # Nastavení AI modelů
│
├── spusteni/              # Spuštění kódu a export
│   ├── sandbox.py         # Bezpečné spuštění
│   └── exporter.py        # STL export
│
├── src/                   # Původní kód (zpětná kompatibilita)
│   ├── generation/        # LLM, RAG
│   ├── execution/
│   └── rag/
│
├── data/                  # Dokumentace build123d (605 souborů)
├── vystupy/               # Vygenerované STL soubory
├── priklady/              # Ukázkové použití
└── testy/                 # Testy
```

---

## Jak to funguje

### 1. Přijetí popisu
Převezme text v češtině popisující 3D model.

### 2. Výběr modelu
1. Nejprve zkusí **Kimi K2.5** (nejlépe pro kód)
2. Když selže → automaticky **Minimax 2.7**

### 3. Kontrola a oprava
- Ověří Python syntaxi
- Opraví známé chyby v build123d
- Odstraní neautorizovaný export kód

### 4. Spuštění
Spustí kód v sandboxu a vyexportuje STL.

### 5. Výstup
Vrátí cestu k STL souboru nebo chybovou zprávu.

---

## Modely

| Model | Role | Cena (vstup/výstup) | Kdy použít |
|-------|------|---------------------|------------|
| **Kimi K2.5** | Hlavní | $0.38 / $1.91 per 1M | Standardní použití |
| **Minimax 2.7** | Záloha | $0.10 / $0.27 per 1M | Když Kimi selže, jednoduché modely |

---

## Příklady použití

### Jednoduché modely

```python
# Krychle
ss.vygeneruj("Vytvoř krychli 50mm")

# Válec
ss.vygeneruj("Vytvoř válec průměru 30mm a výšky 50mm")

# Koule
ss.vygeneruj("Vytvoř kouli průměru 40mm")
```

### Složitější modely

```python
# Držák s otvory
drzak = """Vytvoř montážní držák:
- Základna 80x60mm, tloušťka 5mm
- 4 montážní díry M3 (průměr 3.5mm) v rozích
- Vzdálenost děr od okraje 10mm"""

ss.vygeneruj(drzak, uloz_jako="drzak_m3")
```

---

## Integrace s Agent Zero / Agent Zero Integration

SemiShape je dostupný jako **plugin pro Agent Zero** framework:

### Rychlý start / Quick Start

```
# 1. Generování kódu / Generate code
@semishape_generate query="Vytvoř držák s 4 dírami M3" language="cs"

# 2. Export do STL / Export to STL
@semishape_execute code="$semishape_generate.response.cad_code" output_format="stl"
```

### Dokumentace pluginu / Plugin Documentation

- **[README_PLUGIN.md](README_PLUGIN.md)** - Kompletní dokumentace nástrojů / Complete tool documentation
- **[AGENT_ZERO_INTEGRATION.md](AGENT_ZERO_INTEGRATION.md)** - Podrobný návod integrace / Detailed integration guide

### Dostupné nástroje / Available Tools

| Nástroj / Tool | Popis / Description |
|----------------|---------------------|
| `@semishape_generate` | Generování build123d kódu / Generate build123d code |
| `@semishape_execute` | Spuštění a export / Execute and export |
| `@semishape_rag_search` | Vyhledávání v dokumentaci / Search documentation |

### Rozdíly mezi režimy / Mode Differences

| Režim / Mode | Použití / Usage | Pro koho / For |
|--------------|-----------------|----------------|
| **Standalone** | `python -m jadro.hlavni` | Lokální vývoj / Local development |
| **Agent Zero Plugin** | `@semishape_generate` | AI asistenti / AI agents |
| **Skill-only** | `skills.semishape` | Jednoduché úlohy / Simple tasks |

---

## Monitoring

---

## Web Search

SemiShape podporuje vyhledávání aktuální dokumentace build123d přímo z webu:

```python
from jadro.vyhledavani.web_search import vyhledat_dokumentaci

# Vyhledání nejnovější dokumentace
vysledky = vyhledat_dokumentaci("Box build123d examples")
for vysledek in vysledky:
    print(f"{vysledek['title']}: {vysledek['href']}")
```

Nebo pomocí GitHub monitoringu pro sledování nových commitů:

```python
from jadro.vyhledavani.github_monitor import GithubMonitor

monitor = GithubMonitor()
novinky = monitor.ziskej_nove_commity(limit=5)
```

---

## Skills (Dovednosti)

SemiShape může fungovat jako skill v rámci Agent Zero:

```python
# Načtení dovednosti
from jadro.dovednosti.loader import nacti_dovednosti
dovednosti = nacti_dovednosti()

# Použití dovednosti
from skills.semishape.SKILL import vygeneruj_model
vygeneruj_model("Vytvoř válec 30mm")
```

---

## Poznámky k vývoji
## Licence

Apache 2.0 - viz [LICENSE](LICENSE)

---

## Autor

**Pavel Mareš** ([painter99](https://github.com/painter99))

---

## Poděkování

Projekt stojí na knihovně [build123d](https://github.com/gumyr/build123d) od Rogera Maitlanda.

```
Maitland, R. (2025). build123d: A Python-based parametric CAD library (v0.10.0).
DOI: 10.5281/zenodo.17537673
```

---

> ⚠️ **Upozornění**: AI generovaný kód vyžaduje lidskou kontrolu před výrobou.
