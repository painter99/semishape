# Průvodce datasety pro build123d (QLoRA Fine-tuning)

Tento dokument slouží jako mapa k 12 JSON souborům v tomto repozitáři. Jsou rozděleny do 3 hlavních kategorií podle toho, k čemu slouží.

## 1. Soubory připravené pro trénink (Unsloth / ShareGPT formát)
**Tyto soubory jako jediné vkládáš přímo do trénovacího nástroje (Unsloth GUI, Google Colab, Axolotl apod.).** Jsou ve formátu `ShareGPT` (human/gpt), kterému trenéři rozumí bez nastavování.

* **`unsloth_combined_train.json`** - **TVŮJ HLAVNÍ SOUBOR PRO QLoRA**
  * **Obsah:** Sloučený klasický chat (otázka/odpověď) i doplňování kódu (FIM).
  * **Použití:** Toto je ten jediný soubor, který teď potřebuješ nahrát k tréninku.

*(Pokud bys chtěl experimentovat s odděleným tréninkem, máš k dispozici dílčí soubory:)*
* `unsloth_chat_train.json` - Pouze klasické instrukce (vygeneruj, oprav).
* `unsloth_fim_train.json` - Pouze Fill-In-the-Middle (doplňování kódu v editoru).

---

## 2. Zdroje pro Evaluaci a Validaci (Mimo trénink)
Tyto soubory se **nesmí** použít k trénování, aby se model neučil testovací otázky "zpaměti". Slouží k otestování modelu po tréninku.

* **`build123d_universal_chat_eval.json`** - Pár testovacích konverzací (otázka/odpověď), které model nikdy neviděl.
* **`build123d_universal_fim_eval.json`** - Pár testovacích FIM doplňovaček pro editor.

---

## 3. "Master/Raw" zdroje a Architektura (Pro vývojáře a AI)
S těmito soubory pracuje Cascade, když vytváří tréninková data. Jsou to zdrojové kódy a plány. Do tréninku nejdou.

**Zlatý důl (čisté konverzace, ze kterých generujeme tréninková data):**
* `cs_build123d.json` - Český základ (76 konverzací).
* `en_build123d.json` - Anglický překlad (76 konverzací).

**Strukturované tasky (s metadaty o jazyku a typu úkolu):**
* `build123d_universal_chat_train.json` - Vygenerované úlohy z čistého seedu (GENERATE, REVIEW, REPAIR). Z tohoto souboru se konvertuje ShareGPT verze.
* `build123d_universal_fim_train.json` - Vygenerované FIM úlohy.

**Řízení a Audit:**
* `build123d_dataset_audit.json` - Automaticky generovaná zpráva o stavu (např. zjistili jsme z ní, kolik procent "zlatého dolu" už bylo využito).
* `build123d_dataset_manifest.json` - Konfigurace a definice celého projektu.
* `build123d_granite_training_pack.json` - Strojový "blueprint" pro loadery dat.
