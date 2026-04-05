# SemiShape Agent Zero Plugin

> **AI asistent pro generování 3D CAD modelů z textového popisu**  
> **AI assistant for generating 3D CAD models from text descriptions**

[![Version](https://img.shields.io/badge/Version-0.2.0-blue)](https://github.com/painter99/semishape)
[![License](https://img.shields.io/badge/License-Apache%202.0-green)](LICENSE)
[![Agent Zero](https://img.shields.io/badge/Agent-Zero-purple)]()

---

## 🇨🇿 Český popis / 🇬🇧 English Description

**Česky**: SemiShape Agent Zero plugin transformuje textový popis v češtině nebo angličtině na Python kód pro knihovnu **build123d** a vygeneruje **STL/STEP** soubor.

**English**: SemiShape Agent Zero plugin transforms text descriptions in Czech or English into Python code for the **build123d** library and generates **STL/STEP** files.

**Example / Příklad:**
```
"Vytvoř držák s 4 montážními dírami M3"
        ↓
    [SemiShape AI]
        ↓
    bracket.stl ✅
```

---

## Obsah / Table of Contents

- [Instalace / Installation](#instalace--installation)
- [Konfigurace / Configuration](#konfigurace--configuration)
- [Použití / Usage](#použití--usage)
- [Nástroje / Tools](#nástroje--tools)
- [Příklady / Examples](#příklady--examples)
- [Troubleshooting / Řešení problémů](#troubleshooting--řešení-problémů)

---

## Instalace / Installation

### 1. Předpoklady / Prerequisites

**Česky**: Ujistěte se, že máte nainstalovaný Agent Zero framework a přístup k projektu.

**English**: Ensure you have the Agent Zero framework installed and access to the project.

```bash
# Clone the repository / Naklonujte repozitář
cd /a0/usr/projects/semishape

# Create virtual environment / Vytvořte virtuální prostředí
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies / Nainstalujte závislosti
pip install -r requirements.txt
```

### 2. Plugin registrace / Plugin Registration

**Česky**: Plugin je automaticky registrován přes `plugin.yaml` soubor v rootu projektu.

**English**: The plugin is automatically registered via the `plugin.yaml` file in the project root.

```yaml
# plugin.yaml (existuje již v projektu / already exists in project)
name: semishape
version: 0.2.0
per_project_config: true
```

### 3. Nastavení API klíče / API Key Configuration

**Česky**: Nastavte OpenRouter API klíč přes Agent Zero secrets nebo `.env` soubor.

**English**: Set the OpenRouter API key via Agent Zero secrets or `.env` file.

**Option A - Agent Zero Secrets (doporučeno / recommended):**
```bash
# In Agent Zero configuration
secrets:
  openrouter_api_key: "sk-or-v1-..."
```

**Option B - Environment file / Soubor prostředí:**
```bash
# Vytvořte / Create: /a0/usr/projects/semishape/.env
OPENROUTER_API_KEY=sk-or-v1-...
```

---

## Konfigurace / Configuration

### Plugin.yaml struktura / Structure

```yaml
name: semishape
title: SemiShape CAD Generator
version: 0.2.0
per_project_config: true

settings_sections:
  api:
    title: API Configuration
    settings:
      - name: openrouter_api_key
        type: secret
        required: true
      - name: default_model
        type: string
        default: moonshotai/kimi-k2.5
        
  paths:
    title: Paths and Directories
    settings:
      - name: output_dir
        type: path
        default: ./output
      - name: cache_dir
        type: path
        default: ./data/cache
```

### Dostupné modely / Available Models

| Model | Role | Cena (vstup/výstup) / Price (input/output) |
|-------|------|-------------------------------------------|
| **moonshotai/kimi-k2.5** | Hlavní / Primary | $0.38 / $1.91 per 1M |
| **minimax/minimax-01** | Záloha / Backup | $0.10 / $0.27 per 1M |

---

## Použití / Usage

### V Agent Zero / In Agent Zero

**Česky**: Plugin poskytuje tři nástroje pro přímé použití v Agent Zero:

**English**: The plugin provides three tools for direct use in Agent Zero:

```
@semishape_generate query="..." language="..."
@semishape_execute code="..." output_format="..."
@semishape_rag_search query="..." limit="..."
```

---

## Nástroje / Tools

### 1. @semishape_generate

**Účel / Purpose**: Generování build123d kódu z textového popisu / Generating build123d code from text description.

**Parametry / Parameters:**

| Parametr | Typ | Vyžadováno | Popis / Description |
|----------|-----|------------|---------------------|
| `query` | string | ano / yes | Popis modelu / Model description |
| `language` | string | ne / no | Jazyk (`"cs"` nebo `"en"`, výchozí `"en"`) / Language |
| `use_rag` | boolean | ne / no | Použít RAG dokumentaci / Use RAG docs (výchozí / default: `true`) |

**Příklad / Example:**
```
@semishape_generate query="Vytvoř krychli 50mm s kulatým otvorem průměru 20mm" language="cs"
```

**Výstup / Output:**
```json
{
  "cad_code": "from build123d import...",
  "warnings": [],
  "model_used": "moonshotai/kimi-k2.5",
  "confidence": 0.95
}
```

---

### 2. @semishape_execute

**Účel / Purpose**: Spuštění build123d kódu a export do STL/STEP / Executing build123d code and exporting to STL/STEP.

**Parametry / Parameters:**

| Parametr | Typ | Vyžadováno | Popis / Description |
|----------|-----|------------|---------------------|
| `code` | string | ano / yes | Python build123d kód / Python build123d code |
| `output_format` | string | ne / no | Formát (`"stl"` nebo `"step"`, výchozí `"stl"`) / Format |
| `output_name` | string | ne / no | Název výstupního souboru / Output filename |
| `timeout` | integer | ne / no | Timeout v sekundách / Timeout seconds (výchozí / default: `60`) |

**Příklad / Example:**
```
@semishape_execute code="$semishape_generate.response.cad_code" output_format="stl" output_name="gear"
```

**Výstup / Output:**
```json
{
  "success": true,
  "output_file": "output/gear.stl",
  "execution_time": 3.5
}
```

---

### 3. @semishape_rag_search

**Účel / Purpose**: Vyhledávání v build123d dokumentaci pomocí RAG / Searching build123d documentation using RAG.

**Parametry / Parameters:**

| Parametr | Typ | Vyžadováno | Popis / Description |
|----------|-----|------------|---------------------|
| `query` | string | ano / yes | Vyhledávací dotaz / Search query |
| `limit` | integer | ne / no | Počet výsledků / Number of results (výchozí / default: `5`) |
| `threshold` | float | ne / no | Minimální skóre / Minimum score 0-1 (výchozí / default: `0.7`) |

**Příklad / Example:**
```
@semishape_rag_search query="How to create a fillet on edges?" limit=3
```

**Výstup / Output:**
```json
{
  "results": [
    {
      "text": "fillet(edges, radius=2.0)...",
      "source": "docs/building_blocks.rst",
      "score": 0.89
    }
  ]
}
```

---

## Příklady / Examples

### Kompletní workflow / Complete workflow

**Česky**: Vygenerování a export jedním dotazem:

**English**: Generate and export in one flow:

```
# 1. Generování kódu / Generate code
@semishape_generate query="Vytvoř montážní držák 80x60mm s 4 dírami M3 v rozích" language="cs"

# 2. Spuštění a export / Execute and export
@semishape_execute code="$semishape_generate.response.cad_code" output_format="stl" output_name="drzak_m3"

# Výsledek / Result: output/drzak_m3.stl
```

### Složitý model / Complex model

```
@semishape_generate query="Create a parametric gear:
- 20 teeth
- 50mm outer diameter
- 10mm thickness
- 6mm bore hole
- Pressure angle 20 degrees" language="en"
```

### S použitím RAG / With RAG context

```
# Nejprve vyhledat dokumentaci / First search docs
@semishape_rag_search query="How to extrude a polygon?" limit=2

# Pak generovat s vědomím kontextu / Then generate with context
@semishape_generate query="Create a pentagon prism with 30mm sides" language="en" use_rag=true
```

---

## Troubleshooting / Řešení problémů

### Časté chyby / Common errors

| Chyba / Error | Příčina / Cause | Řešení / Solution |
|---------------|----------------|-------------------|
| `ImportError: build123d` | Knihovna není nainstalována / Library not installed | `pip install build123d` |
| `API key error` | Chybí OpenRouter klíč / Missing OpenRouter key | Nastavit `OPENROUTER_API_KEY` / Set `OPENROUTER_API_KEY` |
| `Empty RAG results` | Vectorstore není vytvořen / Vectorstore not built | `python scripts/build_vectorstore.py` |
| `Execution timeout` | Kód je příliš složitý / Code too complex | Zvýšit timeout nebo zjednodušit model / Increase timeout or simplify |
| `No module named 'chromadb'` | Chybí RAG závislosti / RAG deps missing | `pip install chromadb sentence-transformers` |

### Kontrola instalace / Installation check

```bash
cd /a0/usr/projects/semishape
source .venv/bin/activate

# Test importů / Test imports
python -c "from build123d import Box; print('build123d OK')"
python -c "import chromadb; print('chromadb OK')"
python -c "from src.semishape import SemiShape; print('SemiShape OK')"
```

### Debug režim / Debug mode

**Česky**: Pro detailní logování nastavte proměnnou:

**English**: For detailed logging, set the variable:

```bash
export SEMISHAPE_DEBUG=1
# nebo / or in .env:
SEMISHAPE_DEBUG=1
```

---

## Podpora / Support

**GitHub**: [painter99/semishape](https://github.com/painter99/semishape)  
**Issues**: [Report bug / Nahlásit chybu](https://github.com/painter99/semishape/issues)

---

## Licence / License

**Apache 2.0** - viz [LICENSE](LICENSE)

---

## Autor / Author

**Pavel Mareš** ([painter99](https://github.com/painter99))

---

> ⚠️ **Upozornění / Disclaimer**: SemiShape je neoficiální komunitní nástroj. Není afiliován, sponzorován ani podporován týmem build123d. AI generovaný kód vyžaduje lidskou kontrolu před výrobou.
> 
> SemiShape is an unofficial community tool. It is not affiliated with, sponsored by, or endorsed by the build123d core team. AI-generated CAD code requires manual review before manufacturing.

## Attribution

> Maitland, R. (2025). _build123d: A Python-based parametric CAD library_ (v0.10.0).
> DOI: [10.5281/zenodo.17537673](https://doi.org/10.5281/zenodo.17537673)
