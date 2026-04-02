# SemiShape - Projektová Roadmapa

## 🎯 Finální vize

**SemiShape** = AI agent, který transformuje český textový popis do 3D CAD modelu pomocí build123d knihovny.

### Workflow (Cílový stav)
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Telegram   │────▶│    RAG +     │────▶│   build123d  │────▶│    3D Model  │
│  (čeština)   │     │  Fine-tuned  │     │   Python     │     │    .STL      │
│              │     │     LLM      │     │   script     │     │    .STEP     │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

---

## 📋 Fáze projektu

### Fáze 1: Příprava dat a infrastruktura
- [ ] Shromáždit build123d dokumentaci a příklady
- [ ] Vytvořit dataset pro fine-tuning (cs/en)
- [ ] Nastavit QLoRA training pipeline
- [ ] Vybrat/verifikovat Granite 4.0 H micro

### Fáze 2: RAG systém
- [ ] Analýza vhodného RAG přístupu (agentic vs. standard)
- [ ] Vectorizace build123d dokumentace
- [ ] Implementace retrieval mechanismu
- [ ] Testování precision/recall

### Fáze 3: Fine-tuning
- [ ] Příprava training data ve formátu pro QLoRA
- [ ] Definice LoRA adapterů (target modules)
- [ ] Training na GPU/Cloud
- [ ] Evaluace modelu

### Fáze 4: Backend & Integrace
- [ ] Python backend pro spouštění build123d
- [ ] Bezpečný sandbox (Docker? E2B?)
- [ ] API endpointy

### Fáze 5: Telegram Bot
- [ ] Vytvořit Telegram bot interface
- [ ] Integrace s LLM + RAG
- [ ] Odesílání výsledků (obrázky, soubory)

---

## 🤔 Otevřené otázky k rozhodnutí

### 1. Model hosting
| Možnost | Výhody | Nevýhody |
|---------|--------|----------|
| **Lokální (Ollama)** | Soukromí, žádné API náklady | Vyžaduje GPU hardware |
| **API (OpenRouter)** | Snadné, škálovatelné | Náklady, závislost na službě |
| **Hybrid** | Flexibilita | Komplexita |

### 2. RAG architektura
| Typ | Vhodné pro |
|-----|-----------|
| **Standard RAG** | Jednoduché dotazy, rychlá implementace |
| **Agentic RAG** | Komplexní úkoly, multi-step reasoning |
| **Graph RAG** | Vztahy mezi entitami, komplexní dokumenty |

### 3. Fine-tuning přístup
- **QLoRA** (doporučeno): Efektivní, nízké nároky na VRAM
- **Full fine-tuning**: Lepší výsledky, ale náročné
- **Adapter layers**: Modulární, lze kombinovat

---

## 📊 Odhad zdrojů

### Fine-tuning (QLoRA)
- GPU: 16-24GB VRAM minimum (RTX 3090/4090 nebo A10G)
- Čas: 2-8 hodin dle datasetu
- Cloud možnosti: RunPod, Lambda Labs, Google Colab Pro

### RAG Vector DB
- **ChromaDB** - jednoduché, lokální
- **Pinecone** - managed, škálovatelné
- **FAISS** - rychlé, lokální

---

## 📅 Next Steps (Okamžité akce)

1. ✅ Git repozitář nastaven
2. 🔄 Shromáždit build123d dokumentaci
3. 🔄 Definovat dataset strukturu
4. 🔄 Otestovat Granite 4.0 H micro baseline

---

*Poslední aktualizace: 2026-04-02*
