# SemiShape MVP - Implementační Plán

## 🎯 Cíl
Vytvořit funkční MVP SemiShape jako agent-zero skill/integrace pro generování build123d kódu z českého textu.

---

## 📋 Fáze implementace

### Fáze 1: Základní infrastruktura ✅
- [x] Git repozitář nastaven
- [x] Datasety připraveny
- [x] Trénovací notebook vytvořen

### Fáze 2: RAG Systém (Priorita)
- [ ] Stáhnout build123d dokumentaci z GitHub
- [ ] Zpracovat a chunkovat dokumenty
- [ ] Vytvořit ChromaDB vector store
- [ ] Implementovat retrieval mechanismus
- [ ] Otestovat precision/recall

### Fáze 3: Backend Execution
- [ ] Vytvořit Python sandbox pro build123d
- [ ] Implementovat bezpečné spouštění kódu
- [ ] Export do STL/STEP
- [ ] Generování náhledů

### Fáze 4: Agent-Zero Integrace
- [ ] Vytvořit skill pro build123d
- [ ] Integrovat RAG do skill
- [ ] Vytvořit workflow pro uživatele

### Fáze 5: Testing & Dokumentace
- [ ] Unit testy
- [ ] Integrační testy
- [ ] Uživatelská dokumentace

---

## 🏗️ Architektura

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AGENT ZERO                                  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    SemiShape Skill                            │  │
│  │                                                               │  │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐   │  │
│  │  │   User      │───▶│    RAG      │───▶│  Code           │   │  │
│  │  │   Query     │    │  Retrieval  │    │  Generation     │   │  │
│  │  │   (cs/en)   │    │  (ChromaDB) │    │  (LLM + rules)  │   │  │
│  │  └─────────────┘    └─────────────┘    └─────────────────┘   │  │
│  │                                                │              │  │
│  │                                                ▼              │  │
│  │  ┌─────────────────────────────────────────────────────────┐│  │
│  │  │                  Execution Layer                         ││  │
│  │  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  ││  │
│  │  │  │ build123d   │───▶│ STL/STEP    │───▶│ Preview     │  ││  │
│  │  │  │ Execution   │    │ Export      │    │ Generation  │  ││  │
│  │  │  └─────────────┘    └─────────────┘    └─────────────┘  ││  │
│  │  └─────────────────────────────────────────────────────────┘│  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Struktura projektu

```
semishape/
├── src/
│   ├── __init__.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── embeddings.py      # Embedding funkce
│   │   ├── vectorstore.py     # ChromaDB wrapper
│   │   ├── retriever.py       # Retrieval logic
│   │   └── chunker.py         # Document chunking
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── sandbox.py         # Bezpečné spouštění
│   │   ├── exporter.py        # STL/STEP export
│   │   └── preview.py         # Náhled generace
│   ├── generation/
│   │   ├── __init__.py
│   │   ├── prompts.py         # System prompts
│   │   └── inference.py       # LLM interface
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── data/
│   ├── docs/                  # build123d dokumentace
│   ├── vectorstore/           # ChromaDB data
│   └── templates/             # Code templates
├── tests/
│   ├── test_rag.py
│   ├── test_execution.py
│   └── test_generation.py
├── skills/
│   └── semishape/
│       └── SKILL.md           # Agent-zero skill
├── docs/                      # Dokumentace
├── datasets/                  # Trénovací data
└── training/                  # Trénovací skripty
```

---

## 🔧 Technologie

| Komponenta | Technologie | Důvod |
|------------|-------------|-------|
| Vector DB | ChromaDB | Jednoduchá, lokální, zdarma |
| Embeddings | sentence-transformers | Kvalitní, zdarma |
| LLM | OpenRouter API / Ollama | Flexibilita |
| Execution | Docker / venv | Izolace |
| Export | build123d + OCP | Nativní |

---

## 📅 Timeline

| Fáze | Čas | Stav |
|------|-----|------|
| Fáze 1: Infrastruktura | ✅ Hotovo | Done |
| Fáze 2: RAG | 4-6h | 🔄 In Progress |
| Fáze 3: Backend | 4-6h | ⏳ Pending |
| Fáze 4: Integrace | 2-4h | ⏳ Pending |
| Fáze 5: Testing | 2-4h | ⏳ Pending |

---

*Vytvořeno: 2026-04-02*
*Aktualizováno: 2026-04-02*
