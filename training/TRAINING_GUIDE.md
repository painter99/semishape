# 🎯 SemiShape Fine-tuning Guide

Tento dokument obsahuje návody pro fine-tuning modelu **IBM Granite 4.0 H Micro** na datasetu **build123d**.

---

## 📁 Soubory v projektu

| Soubor | Formát | Použití |
|--------|--------|--------|
| `unsloth_combined_train.json` | ShareGPT | **Google Colab + Unsloth** |
| `autotrain_dataset.jsonl` | JSONL | **HuggingFace AutoTrain** |
| `*_eval.json` | - | ⛧ Nepoužívat pro trénink! |

---

## 🚀 Možnost A: Google Colab + Unsloth

### Výhody:
- ✅ Plně kontrola nad tréninkem
- ✅ Možnost ladit hyperparametry
- ✅ Větší flexibilita

### Postup:

1. **Otevřít Google Colab** s GPU (T4 zdarma, A100 ideální)
2. **Nahrát notebook**: `training/semishape_qlora_colab.ipynb`
3. **Nahrát dataset** na Google Drive:
   - Cesta: `/content/drive/MyDrive/semishape/unsloth_combined_train.json`
4. **Spustit buňky postupně**
5. **Výstup**: LoRA adaptery na Google Drive

### Odhad času:
- **T4 GPU**: 3-4 hodiny
- **A100 GPU**: 1-2 hodiny

---

## 🤗 Možnost B: HuggingFace AutoTrain

### Výhady:
- ✅ Jednoduché UI
- ✅ Automatická správa GPU
- ✅ Bez kódování

### Postup:

#### 1. Připravit dataset na HF Hub

```bash
# Vytvořit repo na huggingface.co/new
# Nahrát autotrain_dataset.jsonl jako train.jsonl
```

#### 2. Spustit AutoTrain

Na HuggingFace:
1. **AutoTrain → Create New Space**
2. **Vybrat model**: `ibm-granite/granite-4.0-h-micro`
3. **Task**: Chat / Instruction Tuning
4. **Upload dataset**: `autotrain_dataset.jsonl`
5. **Konfigurace**:
   - LoRA rank: 16
   - Learning rate: 2e-4
   - Epochs: 3
   - Batch size: 4
   
#### 3. Spustit trénink

AutoTrain automaticky:
- Načte model
- Aplikuje QLoRA
- Spustí trénink
- Uloží adapter na Hub

---

## ⚙️ Konfigurace QLoRA

### Doporučené nastavení:

| Parametr | Hodnota | Vysvětlení |
|----------|---------|------------|
| **LoRA rank** | 16-32 | Vyšší = více naučitelné, ale pomalejší |
| **LoRA alpha** | 32-64 | Obvykle 2x rank |
| **Dropout** | 0.05 | Regularizace |
| **Learning rate** | 2e-4 | Pro QLoRA |
| **Epochs** | 3-5 | Dle velikosti datasetu |
| **Batch size** | 4-8 | Dle VRAM |
| **Gradient accumulation** | 4-8 | Pro menší GPU |
| **Max seq length** | 2048 | Pro kód |

### Target modules pro Granite:
```
q_proj, k_proj, v_proj, o_proj,
gate_proj, up_proj, down_proj
```

---

## 📊 Monitoring tréninku

### Weights & Biases (wandb):
```python
import wandb
wandb.init(project="semishape-build123d")
```

Sledujte:
- **Loss klesá** = model se učí
- **Learning rate** = stabilní na začátku
- **GPU memory** = nesmí překročit VRAM

---

## 💾 Po tréninku

### Uložení LoRA adapterů:
```python
model.save_pretrained("semishape-granite-lora")
tokenizer.save_pretrained("semishape-granite-lora")
```

### Nahrání na HuggingFace Hub:
```python
from huggingface_hub import HfApi
api = HfApi()
api.upload_folder(
    folder_path="semishape-granite-lora",
    repo_id="your-username/semishape-granite-lora",
    repo_type="model"
)
```

### Inference s LoRA:
```python
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="your-username/semishape-granite-lora",
    max_seq_length=2048,
    load_in_4bit=True,
)

FastLanguageModel.for_inference(model)  # Rychlejší inference

inputs = tokenizer(
    "Jak vytvořím válec o průměru 50mm?",
    return_tensors="pt"
).to("cuda")

outputs = model.generate(**inputs, max_new_tokens=256)
print(tokenizer.decode(outputs[0]))
```

---

## ❓ Často kladené otázky

### Q: Kolik VRAM potřebuji?
**A:** QLoRA na Granite Micro vyžaduje ~8GB VRAM. Pro bezpečnost doporučuji 16GB.

### Q: Můžu použít bezplatný T4 v Colab?
**A:** Ano, ale trénink bude pomalejší (3-4 hodiny). Pro A100 s Colab Pro bude trvat 1-2 hodiny.

### Q: Co dělat když loss neklesá?
**A:** Zkuste:
1. Snížit learning rate (2e-5)
2. Zvýšit epochs
3. Přidat více data

### Q: Jak zjistím kvalitu modelu?
**A:** Použijte `*_eval.json` datasety pro testování na neviděných datech.

---

*Poslední aktualizace: 2026-04-02*
