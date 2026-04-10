---
name: semishape-cad
version: 1.0.0
description: AI-powered 3D CAD model generation plugin for Agent Zero. Transforms text descriptions into parametric build123d Python code with automatic STL/STEP export.
triggers:
  - generate CAD model
  - create 3D model
  - build123d code
  - CAD generation
  - STL export
  - STEP export
  - 3D print model
allowed_tools:
  - semishape_generate
  - semishape_execute
  - semishape_rag_search
metadata:
  complexity: high
  category: cad
  language_support:
    - cs
    - en
  frameworks:
    - build123d
    - OpenCASCADE
  export_formats:
    - STL
    - STEP
  llm_provider: agent_zero_active_model
---

# SemiShape — build123d CAD Code Generation Skill

> **"Almost a shape. Mostly suggestion."**

## Overview

SemiShape is an Agent Zero plugin that provides AI-assisted parametric 3D CAD code generation
using the [build123d](https://github.com/gumyr/build123d) Python library.

**It uses whatever model is currently active in Agent Zero** — no separate model configuration
or API key is needed beyond what you already have.

Capabilities:
- Natural language to parametric build123d Python code (Czech or English)
- Safe code execution in an isolated subprocess sandbox
- Automatic STL / STEP export
- build123d documentation search (local keyword + optional DuckDuckGo web)

---

## Tools

### `semishape_generate` — Text → CAD code + STL

Generates build123d code from a natural language description and optionally runs it
to produce an STL file.

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `description` | ✅ | — | Text description of the model (Czech or English) |
| `language` | ❌ | `cs` | Language for code comments: `cs` \| `en` |
| `execute` | ❌ | `true` | Also execute code and export STL after generation |

**Example:**
```
@semishape_generate description="Create a 100×50×10 mm plate with four 3 mm mounting holes in the corners" language="en"
```

---

### `semishape_execute` — Execute code → STL / STEP

Runs existing build123d Python code in a sandbox and exports the model.

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `code` | ✅ | — | build123d Python code to execute |
| `output_name` | ❌ | `model` | Output filename stem (without extension) |
| `export_format` | ❌ | `stl` | Export format: `stl` \| `step` \| `both` |

**Example:**
```
@semishape_execute code="from build123d import *\nwith BuildPart() as part:\n    Box(50, 30, 10)" export_format="both" output_name="box"
```

---

### `semishape_rag_search` — Search build123d documentation

Searches the 600+ bundled build123d documentation files and optionally performs a
DuckDuckGo web search.

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `query` | ✅ | — | Search query or question |
| `top_k` | ❌ | `5` | Max results to return (1–10) |
| `use_web` | ❌ | `true` | Also search the web |

**Example:**
```
@semishape_rag_search query="How to use fillet on edges?"
```

---

## Typical Workflow

```
# 1. (Optional) Look up API docs first
@semishape_rag_search query="extrude with taper"

# 2. Generate code from description
@semishape_generate description="Create a mounting bracket 80×40×5 mm with four M3 holes" language="en"

# 3. Re-export in a different format if needed
@semishape_execute code="<paste code>" export_format="step" output_name="bracket"
```

---

## Notes

- The plugin uses the **currently active Agent Zero model** for code generation.
  To change the model, update the active model in Agent Zero settings.
- Generated STL/STEP files are saved to the `output/` directory inside the plugin folder.
- The build123d documentation bundled in `data/docs/` covers 600+ files including
  tutorials, API reference, and code examples.
- The vector store (`data/vectorstore/`) is optional. If it does not exist, RAG search
  falls back to keyword search over the raw documentation files.

---

## Best Practices

1. **Use specific dimensions** — "50 mm" is better than "small".
2. **Describe features clearly** — "four M3 mounting holes" not "some holes".
3. **Verify output** — AI-generated CAD code requires manual review before manufacturing.
4. **Start simple** — Test with simple primitives before complex assemblies.
5. **Use RAG for advanced features** — Search the docs when you need specific API details.

---

## Attribution

> Maitland, R. (2025). *build123d: A Python-based parametric CAD library* (v0.10.0).  
> DOI: [10.5281/zenodo.17537673](https://doi.org/10.5281/zenodo.17537673)

> ⚠️ SemiShape is an unofficial community tool — not affiliated with, sponsored by, or
> endorsed by the build123d core team. Always verify AI-generated geometry before
> manufacturing.
