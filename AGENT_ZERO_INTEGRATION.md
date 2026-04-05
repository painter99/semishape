# Agent Zero Integration Guide for SemiShape

## Overview

This guide explains how to integrate the SemiShape CAD generator plugin with Agent Zero framework. SemiShape provides AI-powered 3D CAD model generation using the build123d Python library.

---

## Integration Options

There are **two ways** to use SemiShape with Agent Zero:

### Option 1: Full Plugin (Recommended)
Complete integration with dedicated tools (`@semishape_generate`, `@semishape_execute`, `@semishape_rag_search`).

**Advantages:**
- Native `@tool` syntax in conversations
- Dedicated tool classes with isolated execution
- Per-project configuration support
- Best for production use

### Option 2: Skill-Only Mode
Use SemiShape as a skill without dedicated tools.

**Advantages:**
- Simpler setup
- Direct Python function calls
- Good for development/testing

---

## Option 1: Full Plugin Installation

### Step 1: Prerequisites

Ensure your environment meets these requirements:

```bash
# Python 3.10+
python --version  # Should be 3.10 or higher

# Agent Zero framework installed
# (Standard in Kali Linux container at /a0)
```

### Step 2: Project Setup

The SemiShape project should be located at:
```
/a0/usr/projects/semishape/
```

Verify structure:
```bash
cd /a0/usr/projects/semishape
ls -la
```

Expected files:
- `plugin.yaml` - Plugin configuration
- `tools/` - Tool implementations
- `helpers/` - Shared utilities
- `skills/semishape/SKILL.md` - Skill definition

### Step 3: Configure API Keys

SemiShape requires an OpenRouter API key for LLM access.

#### Method A: Agent Zero Secrets (Recommended)

Set the secret in your Agent Zero configuration:

```bash
# Edit secrets file (path varies by setup)
# Standard location: /a0/usr/.env or project-specific
```

Add to `/a0/usr/.env`:
```
API_KEY_OPENROUTER=sk-or-v1-your-key-here
```

Or use the Agent Zero secret alias format in `plugin.yaml`:
```yaml
settings_sections:
  api:
    settings:
      - name: openrouter_api_key
        type: secret
        description: OpenRouter API key for LLM access
        required: true
        # Value comes from Agent Zero secrets
```

#### Method B: Environment Variable

```bash
export OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### Step 4: Install Dependencies

```bash
cd /a0/usr/projects/semishape
source .venv/bin/activate  # If using venv
pip install -r requirements.txt
```

Key dependencies:
- `build123d>=0.10.0` - CAD library
- `chromadb>=0.5.0` - Vector database for RAG
- `sentence-transformers>=2.0.0` - Embeddings for RAG
- `openai>=1.0.0` - LLM client

### Step 5: Build RAG Vector Store (Optional but Recommended)

For RAG search functionality, build the documentation index:

```bash
cd /a0/usr/projects/semishape
python scripts/build_vectorstore.py
```

This creates a vector store from build123d documentation (605 files) in:
```
data/vectorstore/
```

### Step 6: Plugin Registration

Agent Zero automatically detects plugins from `plugin.yaml` files in project directories.

Verify plugin.yaml structure:
```yaml
name: semishape
title: SemiShape CAD Generator
version: 0.2.0
per_project_config: true

tools:
  semishape_generate:
    title: Generate CAD Code
    file: tools/semishape_generate.py
    class: SemishapeGenerate
    settings_section: api
    
  semishape_execute:
    title: Execute CAD Code
    file: tools/semishape_execute.py
    class: SemishapeExecute
    settings_section: paths
    
  semishape_rag_search:
    title: Search Documentation
    file: tools/semishape_rag_search.py
    class: SemishapeRagSearch
    settings_section: api
```

### Step 7: Verify Installation

Test the installation:

```python
# From Python
from helpers.semishape_client import SemiShapeClient
client = SemiShapeClient()
result = client.generate("Create a cube 50mm", language="en")
print(result)
```

Or via Agent Zero:
```
@semishape_generate query="Create a cube 50mm" language="en"
```

---

## Option 2: Skill-Only Mode

### Setup

1. Ensure the skill is in the correct location:
   ```
   /a0/usr/projects/semishape/skills/semishape/SKILL.md
   ```

2. Load the skill in Agent Zero (automatic when project is active)

### Usage

In Agent Zero conversation, reference the skill directly:

```
Use the semishape skill to generate a mounting bracket with 4 holes
```

Or call functions directly:

```python
# Agent Zero loads skills automatically
result = semishape_generate(query="Create a bracket", language="en")
```

---

## Tool Reference

### @semishape_generate

Generates build123d Python code from natural language.

**When to use:**
- Creating new CAD models from descriptions
- Converting engineering requirements to code
- Exploring parametric designs

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| query | string | Yes | - | Model description |
| language | string | No | "en" | Query language ("en" or "cs") |
| use_rag | boolean | No | true | Use RAG documentation |

**Example:**
```
@semishape_generate query="Create a gear with 20 teeth, 50mm diameter, 10mm thickness" language="en"
```

### @semishape_execute

Executes build123d code and exports to STL/STEP.

**When to use:**
- Running generated code
- Exporting to 3D printable formats
- Testing CAD code

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| code | string | Yes | - | Python build123d code |
| output_format | string | No | "stl" | Export format ("stl" or "step") |
| output_name | string | No | auto | Output filename |
| timeout | integer | No | 60 | Execution timeout (seconds) |

**Example:**
```
@semishape_execute code="from build123d import *\nwith BuildPart() as p:\n  Box(50,50,50)" output_format="stl"
```

### @semishape_rag_search

Searches build123d documentation using semantic similarity.

**When to use:**
- Finding documentation for specific features
- Learning build123d syntax
- Debugging code issues

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| query | string | Yes | - | Search query |
| limit | integer | No | 5 | Number of results |
| threshold | float | No | 0.7 | Similarity threshold (0-1) |

**Example:**
```
@semishape_rag_search query="How to create a fillet?" limit=3
```

---

## Usage Patterns

### Pattern 1: Simple Generation

Generate a model in one step:

```
@semishape_generate query="Create a mounting bracket 80x60mm with 4 holes" language="en"
@semishape_execute code="$semishape_generate.response.cad_code" output_format="stl"
```

### Pattern 2: RAG-Assisted Generation

Use documentation search for complex features:

```
@semishape_rag_search query="How to create a revolve feature?" limit=3
@semishape_generate query="Create a revolved vase with 100mm height" language="en" use_rag=true
@semishape_execute code="$semishape_generate.response.cad_code" output_name="vase"
```

### Pattern 3: Iterative Design

Refine models through multiple iterations:

```
# First attempt
@semishape_generate query="Create a box 50x30x10mm" language="en"

# Review and refine
@semishape_generate query="Create a box 50x30x10mm with rounded corners (radius 5mm)" language="en"

# Execute final version
@semishape_execute code="$semishape_generate.response.cad_code" output_name="box_rounded"
```

### Pattern 4: Czech Language Support

Use Czech for natural interaction:

```
@semishape_generate query="Vytvoř držák na kabely s průměrem 20mm" language="cs"
@semishape_execute code="$semishape_generate.response.cad_code" output_format="stl"
```

---

## Configuration Options

### Per-Project Settings

When `per_project_config: true` in plugin.yaml, settings can be customized per project:

```yaml
settings_sections:
  api:
    settings:
      - name: default_model
        type: string
        default: moonshotai/kimi-k2.5
        options:
          - moonshotai/kimi-k2.5
          - minimax/minimax-01
          - deepseek/deepseek-chat
```

### Available Models

| Model | Use Case | Cost (input/output per 1M) |
|-------|----------|---------------------------|
| moonshotai/kimi-k2.5 | Best for complex CAD | $0.38 / $1.91 |
| minimax/minimax-01 | Backup/faster | $0.10 / $0.27 |
| deepseek/deepseek-chat | Alternative | Varies |

---

## Troubleshooting

### Common Issues

#### Issue: "ImportError: build123d"

**Cause:** build123d library not installed

**Solution:**
```bash
pip install build123d>=0.10.0
```

#### Issue: "API key error"

**Cause:** Missing OpenRouter API key

**Solution:**
```bash
# Set in environment
export OPENROUTER_API_KEY=sk-or-v1-...

# Or in .env file
echo "OPENROUTER_API_KEY=sk-or-v1-..." > .env
```

#### Issue: "Empty RAG results"

**Cause:** Vectorstore not built

**Solution:**
```bash
python scripts/build_vectorstore.py
```

#### Issue: "Tool not found"

**Cause:** Plugin not loaded

**Solution:**
1. Verify plugin.yaml syntax: `cat plugin.yaml`
2. Check tools directory exists: `ls tools/`
3. Restart Agent Zero context

#### Issue: "Execution timeout"

**Cause:** CAD code too complex

**Solution:**
```
@semishape_execute code="..." timeout=120  # Increase timeout
```

Or simplify the model description.

### Debug Mode

Enable debug logging:

```bash
export SEMISHAPE_DEBUG=1
```

Check logs:
```bash
tail -f /a0/usr/projects/semishape/data/logs/semishape.log
```

---

## Best Practices

### 1. Use Specific Dimensions

✅ Good: `"Create a cube 50mm with a 10mm hole"`

❌ Avoid: `"Create a small cube with a hole"`

### 2. Describe Features Clearly

✅ Good: `"Four mounting holes in corners, 5mm diameter"`

❌ Avoid: `"Some holes for mounting"`

### 3. Start Simple

Begin with basic shapes before complex assemblies:
1. Test with primitives (cube, cylinder, sphere)
2. Add features incrementally
3. Build assemblies from validated parts

### 4. Use RAG for Complex Features

Enable RAG when using advanced build123d features:
```
@semishape_generate query="..." use_rag=true
```

### 5. Validate Before Manufacturing

⚠️ Always review generated code before 3D printing:
```
# Check the generated code
print($semishape_generate.response.cad_code)

# Visualize before export
@semishape_execute code="..." output_format="stl"
```

---

## Comparison: Full Plugin vs Skill-Only

| Feature | Full Plugin | Skill-Only |
|---------|-------------|------------|
| Tool syntax | `@semishape_generate` | Function calls |
| Per-project config | ✅ Yes | ❌ No |
| Tool isolation | ✅ Yes | ❌ No |
| Setup complexity | Medium | Low |
| Best for | Production | Development |
| Response format | Structured JSON | Python objects |

---

## Advanced Topics

### Custom Prompts

Modify prompts in `prompts/` directory:
- `agent.system.tool.semishape_generate.md`
- `agent.system.tool.semishape_execute.md`
- `agent.system.tool.semishape_rag_search.md`

### Extending Tools

Create new tools by extending the Tool class:

```python
# tools/my_custom_tool.py
from helpers.tool import Tool, Response

class MyCustomTool(Tool):
    async def execute(self, **kwargs) -> Response:
        # Custom logic
        return Response(message="Done", break_loop=False)
```

### Integration with Other Plugins

SemiShape can work alongside other Agent Zero plugins:

```
@docker_terminal command="ls -la"  # Check files
@semishape_generate query="Create a bracket for these dimensions"  # Generate CAD
@docker_terminal command="cp output/bracket.stl /shared/"  # Copy result
```

---

## Support

- **GitHub**: https://github.com/painter99/semishape
- **Issues**: https://github.com/painter99/semishape/issues
- **Documentation**: See README_PLUGIN.md for detailed tool reference

---

## Attribution

This plugin is powered by [build123d](https://github.com/gumyr/build123d) by Roger Maitland.

> Maitland, R. (2025). _build123d: A Python-based parametric CAD library_ (v0.10.0).  
> DOI: [10.5281/zenodo.17537673](https://doi.org/10.5281/zenodo.17537673)

---

> ⚠️ **Disclaimer**: SemiShape is an unofficial community tool. It is not affiliated with, sponsored by, or endorsed by the build123d core team. AI-generated CAD code requires manual review. Always verify geometry and engineering constraints before manufacturing.
