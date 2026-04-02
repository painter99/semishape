# SemiShape - build123d CAD Code Generation Skill

> **"Almost a shape. Mostly suggestion."**

## Overview

SemiShape is an Agent-Zero skill that provides AI-assisted parametric CAD code generation using the build123d Python library. It combines:

- **RAG-powered documentation retrieval** - Semantic search through build123d documentation
- **LLM-based code generation** - Natural language to parametric CAD code
- **Code execution sandbox** - Safe execution of generated build123d code
- **STL/STEP export** - Export generated models to standard formats

This skill enables Agent-Zero to generate, execute, and export build123d CAD models from natural language descriptions.

## Capabilities

### 1. Code Generation (`semishape_generate`)
Generate build123d Python code from natural language descriptions.

**Supports:**
- Czech and English languages
- Parametric designs with variable dimensions
- Conservative inference (no unexpected features)
- RAG-enhanced documentation context

### 2. Code Execution (`semishape_execute`)
Execute build123d code in a safe sandbox environment.

**Features:**
- Isolated subprocess execution
- Timeout protection
- Automatic STL/STEP file detection
- Output capture and error handling

### 3. RAG Search (`semishape_rag_search`)
Search build123d documentation using semantic similarity.

**Returns:**
- Relevant documentation snippets
- Code examples
- Source file references

### 4. Complete Workflow (`semishape_generate_and_execute`)
End-to-end workflow: generate code, execute it, and export the result.

## Installation

### Prerequisites

```bash
# Activate the SemiShape project
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
# In /a0/usr/.env
API_KEY_OPENROUTER=your_openrouter_key
# Or for local LLM
# LLM_PROVIDER=ollama
# LLM_MODEL=llama3.2
```

## Usage

### As Agent-Zero Skill

The skill is automatically available when the project is active. Use the skill tools:

```
# Generate build123d code
semishape_generate(query="Create a 100mm cube with a 10mm hole", language="en")

# Execute generated code
semishape_execute(code="...")

# Search documentation
semishape_rag_search(query="How to create a sketch?")

# Complete workflow
semishape_generate_and_execute(query="Vytvoř držák na kabely", language="cs")
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
├── skills/semishape/SKILL.md    # This file
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

### English Query

```python
result = ss.generate_and_execute(
    "Create a mounting bracket with:
     - 100mm x 50mm x 10mm base
     - Four 5mm mounting holes in corners
     - 2mm fillet on all edges"
)
```

### Czech Query

```python
result = ss.generate_and_execute(
    "Vytvoř držák na kabely:
     - Průměr 20mm
     - Výška 30mm
     - Otvor pro přišroubování",
    language="cs"
)
```

### With RAG Context

```python
# Search documentation first
docs = ss.rag_search("How to create a sketch on a face?")

# Generate with context
result = ss.generate_code(
    "Create a sketch on the top face of a box and extrude a cylinder",
    use_rag=True
)
```

## Output Formats

### Generated Code Result

```python
@dataclass
class GeneratedCode:
    code: str              # build123d Python code
    explanation: str       # Natural language explanation
    raw_response: str      # Full LLM response
    model: str             # Model used
    usage: dict            # Token usage
    warnings: list         # Validation warnings
    rag_sources: list      # RAG documentation sources
```

### Execution Result

```python
@dataclass
class ExecutionResult:
    success: bool          # Execution status
    stdout: str            # Standard output
    stderr: str            # Error output
    output_path: str       # Path to generated STL/STEP
    files: list           # List of generated files
    execution_time: float  # Time in seconds
```

## Error Handling

The skill provides helpful error messages:

```python
result = ss.generate_code("Create something impossible")
if result.has_errors():
    print("Warnings:", result.warnings)
    # Warnings: ['Missing build123d import', 'Consider defining dimensions as variables']
```

```python
result = ss.execute(code)
if not result.success:
    print("Error:", result.stderr)
    # Error: NameError: name 'Box' is not defined
```

## Best Practices

### Parametric Design
Always define dimensions as variables:

```python
# Good
WIDTH = 100.0
HEIGHT = 50.0
with BuildPart() as part:
    Box(WIDTH, HEIGHT, 10)

# Avoid
with BuildPart() as part:
    Box(100, 50, 10)  # Magic numbers!
```

### Robust Selectors
Use geometric selectors instead of fragile index-based selections:

```python
# Good
top_face = part.faces().sort_by(Axis.Z).last

# Avoid
top_face = part.faces()[0]  # Fragile!
```

### Builder Mode
Use modern Builder Mode context managers:

```python
# Good
with BuildPart() as part:
    Box(100, 50, 10)

# Avoid
part = Box(100, 50, 10)
```

## License

Apache License 2.0 - See project LICENSE file.

## Attribution

SemiShape is powered by:
- [build123d](https://github.com/gumyr/build123d) - Python parametric CAD library
- [Agent Zero](https://github.com/agent0ai/agent-zero) - AI agent framework

## Support

- GitHub Issues: [painter99/semishape](https://github.com/painter99/semishape)
- Agent Zero Discord: [discord.gg/B8KZKNsPpj](https://discord.gg/B8KZKNsPpj)
