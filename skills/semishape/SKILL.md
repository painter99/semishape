---
name: semishape-cad
version: 0.2.0
description: AI-powered CAD model generation using build123d library. Transforms text descriptions into 3D parametric CAD models with STL/STEP export support.
triggers:
  - generate CAD model
  - create 3D model
  - build123d code
  - semishape code
  - CAD generation
  - STL export
  - STEP export
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
  llm_provider: openrouter
  models:
    - moonshotai/kimi-k2.5
    - minimax/minimax-01
---

# SemiShape - build123d CAD Code Generation Skill

> **"Almost a shape. Mostly suggestion."**

## Overview

SemiShape is an Agent Zero skill that provides AI-assisted parametric CAD code generation using the build123d Python library. It combines:

- **RAG-powered documentation retrieval** - Semantic search through build123d documentation
- **LLM-based code generation** - Natural language to parametric CAD code
- **Code execution sandbox** - Safe execution of generated build123d code
- **STL/STEP export** - Export generated models to standard formats

This skill enables Agent Zero to generate, execute, and export build123d CAD models from natural language descriptions.

## Capabilities

### 1. Code Generation (`semishape_generate`)
Generate build123d Python code from natural language descriptions.

**Supports:**
- Czech and English languages
- Parametric designs with variable dimensions
- Conservative inference (no unexpected features)
- RAG-enhanced documentation context

**Usage:**
```
@semishape_generate query="Create a 100mm cube with a 10mm hole" language="en"
```

### 2. Code Execution (`semishape_execute`)
Execute build123d code in a safe sandbox environment.

**Features:**
- Isolated subprocess execution
- Timeout protection
- Automatic STL/STEP file detection
- Output capture and error handling

**Usage:**
```
@semishape_execute code="..." output_format="stl"
```

### 3. RAG Search (`semishape_rag_search`)
Search build123d documentation using semantic similarity.

**Returns:**
- Relevant documentation snippets
- Code examples
- Source file references

**Usage:**
```
@semishape_rag_search query="How to create a sketch?" limit=5
```

### 4. Complete Workflow
End-to-end workflow using multiple tools: generate code, then execute for export.

**Example:**
```
# Generate code first
@semishape_generate query="Vytvoř držák na kabely" language="cs"

# Then execute the generated code
@semishape_execute code="$semishape_generate.result.cad_code" output_format="stl"
```

## Installation

### Prerequisites

Ensure the SemiShape project is active and dependencies are installed:

```bash
cd /a0/usr/projects/semishape
source .venv/bin/activate  # or create one: python -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install build123d ocp-vscode sentence-transformers chromadb requests
```

### Vector Store Setup

```bash
# Build the RAG vector store (first time only)
python scripts/build_vectorstore.py
```

### API Keys

Set up environment variables:

```bash
# In /a0/usr/.env or via Agent Zero secrets
API_KEY_OPENROUTER=your_openrouter_key
# Or for local LLM
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
```

## Usage

### In Agent Zero with Plugin

When the SemiShape plugin is active, use `@` tool invocations:

```
# Generate build123d code
@semishape_generate query="Create a 100mm cube with a 10mm hole" language="en"

# Execute generated code
@semishape_execute code="..." output_format="stl"

# Search documentation
@semishape_rag_search query="How to create a sketch?"

# Complete workflow
@semishape_generate query="Vytvoř držák s 4 dírami" language="cs"
```

### As Agent Zero Skill (Legacy Mode)

If using as skill only (without plugin), the tools are available via skill loader:

```python
# Generate build123d code
semishape_generate(query="Create a 100mm cube with a 10mm hole", language="en")

# Execute generated code
semishape_execute(code="...")

# Search documentation
semishape_rag_search(query="How to create a sketch?")
```

### As Python Module

```python
from src.semishape import SemiShape

# Initialize
ss = SemiShape()

# Generate code
result = ss.generate_code("Create a bracket with 4 mounting holes")
print(result.code)
print(result.warnings)

# Execute and export
result = ss.generate_and_execute("Vytvoř kvádr 50x30x10mm", language="cs")
print(result.output_path)
```

### Command-Line Interface

```bash
# Generate code
python -m src.cli generate "Create a box with lid"

# Execute code
python -m src.cli execute model.py

# RAG search
python -m src.cli rag-search "How to use extrude?"

# Interactive mode
python -m src.cli interactive
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider (openrouter/ollama) | `openrouter` |
| `LLM_MODEL` | Model identifier | `openai/gpt-4o-mini` |
| `LLM_TEMPERATURE` | Generation temperature | `0.7` |
| `LLM_MAX_TOKENS` | Max tokens for response | `4096` |
| `API_KEY_OPENROUTER` | OpenRouter API key | (required for OpenRouter) |

### Project Structure

```
/a0/usr/projects/semishape/
├── plugin.yaml                  # Agent Zero plugin configuration
├── skills/semishape/SKILL.md    # This file
├── tools/                        # Agent Zero tool implementations
│   ├── semishape_generate.py
│   ├── semishape_execute.py
│   └── semishape_rag_search.py
├── helpers/semishape_client.py   # Shared client implementation
├── prompts/                      # Prompt templates
│   ├── agent.system.tool.semishape_generate.md
│   ├── agent.system.tool.semishape_execute.md
│   └── agent.system.tool.semishape_rag_search.md
├── src/
│   ├── semishape.py            # Main entry point
│   ├── cli.py                  # CLI interface
│   ├── generation/             # LLM + prompts
│   ├── rag/                    # Vector store + retrieval
│   └── execution/              # Sandbox + export
├── data/
│   ├── docs/                   # build123d documentation
│   └── vectorstore/             # ChromaDB storage
└── scripts/
    └── build_vectorstore.py    # Index documentation
```

## Examples

### English Query with Plugin

```
@semishape_generate query="Create a mounting bracket with:
 - 100mm x 50mm x 10mm base
 - Four 5mm mounting holes in corners
 - 2mm fillet on all edges" language="en"
```

### Czech Query with Plugin

```
@semishape_generate query="Vytvoř držák na kabely:
 - Průměr 20mm
 - Výška 30mm
 - Otvor pro přišroubování" language="cs"
```

### With RAG Context

```
# Search documentation first for specific patterns
@semishape_rag_search query="How to create a sketch on a face?"

# Generate with context - the generator uses RAG internally
@semishape_generate query="Create a sketch on the top face of a box and extrude a cylinder" language="en"
```

### Complete Workflow

```
# 1. Generate the code
@semishape_generate query="Create a parametric gear with 20 teeth and 50mm diameter" language="en"

# 2. Execute and export
@semishape_execute code="$semishape_generate.response.cad_code" output_format="stl" output_name="gear_20t"

# Result: STL file exported to output/ directory
```

## Tool Reference

### @semishape_generate

Generates build123d CAD code from natural language description.

**Parameters:**
- `query` (string, required): Description of the CAD model to create
- `language` (string, optional): Language of the query (`"en"` or `"cs"`, default: `"en"`)
- `use_rag` (boolean, optional): Whether to use RAG documentation context (default: `true`)

**Returns:**
```json
{
  "cad_code": "from build123d import...",
  "warnings": ["..."],
  "model_used": "moonshotai/kimi-k2.5",
  "confidence": 0.95
}
```

### @semishape_execute

Executes build123d code and exports to STL/STEP.

**Parameters:**
- `code` (string, required): Python build123d code to execute
- `output_format` (string, optional): Export format (`"stl"` or `"step"`, default: `"stl"`)
- `output_name` (string, optional): Base name for output file (default: auto-generated)
- `timeout` (integer, optional): Execution timeout in seconds (default: `60`)

**Returns:**
```json
{
  "success": true,
  "output_file": "output/model.stl",
  "execution_time": 3.5,
  "stdout": "..."
}
```

### @semishape_rag_search

Searches build123d documentation using semantic similarity.

**Parameters:**
- `query` (string, required): Search query
- `limit` (integer, optional): Number of results (default: `5`)
- `threshold` (float, optional): Similarity threshold 0-1 (default: `0.7`)

**Returns:**
```json
{
  "results": [
    {
      "text": "...",
      "source": "docs/building_blocks.rst",
      "score": 0.89
    }
  ],
  "total_found": 5
}
```

## Error Handling

Common errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| `ImportError: build123d` | Library not installed | Run `pip install build123d` |
| `No module named 'chromadb'` | RAG dependencies missing | Run `pip install chromadb sentence-transformers` |
| `API key error` | Missing OpenRouter key | Set `API_KEY_OPENROUTER` in .env |
| `Empty RAG results` | Vectorstore not built | Run `python scripts/build_vectorstore.py` |
| `Execution timeout` | Code too complex | Increase timeout or simplify model |

## Bilingual Support

SemiShape supports both Czech and English:

**Czech (`language="cs")`:**
- Optimized tokenization for Czech engineering terms
- Localized error messages in output
- Czech prompt templates from `prompts/cs/`

**English (`language="en")`:**
- Full documentation coverage
- GPT-4 optimized prompts
- Industry-standard terminology

## Best Practices

1. **Use specific dimensions**: "50mm" instead of "small"
2. **Describe features clearly**: "four mounting holes" instead of "some holes"
3. **Use RAG for complex features**: Enable `use_rag=true` for advanced operations
4. **Validate output**: Always check generated code before manufacturing
5. **Start simple**: Test with simple primitives before complex assemblies

## License

Apache 2.0 - See [LICENSE](../../LICENSE)

## Author

**Pavel Mareš** ([painter99](https://github.com/painter99))

---

> ⚠️ **Disclaimer**: SemiShape is an unofficial community tool. It is not affiliated with, sponsored by, or endorsed by the build123d core team. AI-generated CAD code requires manual review. Always verify geometry and engineering constraints before manufacturing.

## Attribution

> Maitland, R. (2025). _build123d: A Python-based parametric CAD library_ (v0.10.0).
> DOI: [10.5281/zenodo.17537673](https://doi.org/10.5281/zenodo.17537673)
