# SemiShape - AI CAD Model Generator for Agent Zero

🎨 **Transform text descriptions into 3D parametric CAD models**

SemiShape is a production-ready Agent Zero plugin that generates build123d Python code from natural language descriptions (Czech or English) and exports 3D models as STL or STEP files.

---

## Features

✅ **Dual-Model Intelligence**
- Primary: moonshotai/kimi-k2.5 (quality-focused)
- Backup: minimax/minimax-01 (cost-efficient)
- Auto-fallback on failure

✅ **Automatic Code Generation**
- Syntax validation and correction
- Multi-language support (Czech, English)
- Parameter extraction from descriptions

✅ **Export Formats**
- STL (stereolithography)
- STEP (CAD exchange format)
- Batch export support

✅ **Integrated Documentation Search**
- Search bundled build123d docs
- Web search for examples
- API reference lookups

✅ **Sandbox Execution**
- Isolated code execution environment
- Resource limits (timeout, memory)
- Security validation

---

## Installation

### Prerequisites

- Python 3.10+
- Agent Zero framework (v1.0+)
- OpenRouter API key (for LLM access)

### Quick Start

1. **Enable the plugin in Agent Zero**
   ```bash
   # In Agent Zero UI or CLI, enable the semishape plugin
   # The plugin auto-installs dependencies on first use
   ```

2. **Configure API key**
   
   Set your OpenRouter API key in one of these ways:
   
   **Option A: Environment Variable**
   ```bash
   export API_KEY_OPENROUTER="sk-or-v1-..."
   ```
   
   **Option B: Agent Zero Secrets**
   
   In your `.a0proj/secrets.env`:
   ```
   API_KEY_OPENROUTER=sk-or-v1-...
   ```
   
   **Option C: Plugin Settings**
   
   Configure in Agent Zero UI → Plugins → SemiShape → Settings

3. **Test the installation**
   ```bash
   # In Agent Zero conversation:
   @semishape_generate description="Create a 50×30×10 mm box with a centered hole"
   ```

---

## Usage

### Tool 1: Generate CAD Code

```bash
@semishape_generate \
  description="Create a mounting bracket with 4 M3 holes" \
  model="auto" \
  language="cs" \
  execute="true"
```

**Arguments:**
- `description` (required) — text description of the desired 3D model
- `model` (optional) — `"auto"` | `"kimi"` | `"minimax"` (default: `"auto"`)
- `language` (optional) — `"cs"` | `"en"` (default: `"cs"`)
- `execute` (optional) — `"true"` to also generate and export STL (default: `"false"`)

**Output:**
- Generated build123d Python code
- STL export path (if `execute=true`)
- Estimated API cost

---

### Tool 2: Execute CAD Code

```bash
@semishape_execute \
  code="from build123d import *; box = Box(10, 20, 30)" \
  output_name="my_model" \
  export_format="stl"
```

**Arguments:**
- `code` (required) — build123d Python code to execute
- `output_name` (optional) — filename stem for export (default: `"model"`)
- `export_format` (optional) — `"stl"` | `"step"` | `"both"` (default: `"stl"`)

**Output:**
- File paths for generated STL/STEP models
- Execution status and any errors

---

### Tool 3: Search Documentation

```bash
@semishape_rag_search \
  query="How to use fillet in build123d?" \
  top_k="5" \
  use_web="true"
```

**Arguments:**
- `query` (required) — search term or question
- `top_k` (optional) — max results (1-10, default: 5)
- `use_web` (optional) — include web search (default: `true`)

**Output:**
- Relevant documentation snippets
- Web search results with links
- Code examples

---

## Configuration

### Default Settings (`default_config.yaml`)

```yaml
openrouter_api_key: ""              # Set via environment or secrets
default_model: "moonshotai/kimi-k2.5"
backup_model: "minimax/minimax-01"
temperature: 0.2                    # Lower = more consistent
max_tokens: 4096
output_dir: "/a0/usr/projects/semishape/output"
execution_timeout: 60               # Seconds
sandbox_enabled: true
default_export_format: "stl"
default_language: "cs"
```

### Per-Project Override

Create `.a0proj/semishape/config.yaml` to override defaults for a specific project:

```yaml
# Override just the fields you need
default_model: "minimax/minimax-01"  # Use cheaper model for this project
output_dir: "./cad_models"           # Project-specific output
```

---

## Supported CAD Types

SemiShape recognizes these common patterns and optimizes generation:

- **Bracket** — holding/mounting parts
- **Gear** — toothed mechanical parts
- **Housing** — enclosures and boxes
- **Plate** — flat structural parts
- **Shaft** — rotating cylindrical parts
- **Bearing** — rolling element supports
- **Flange** — connector parts with extended rim
- **Coupling** — connection between shafts
- **Enclosure** — sealed boxes and cabinets

---

## Examples

### Example 1: Simple Box with Hole

```bash
@semishape_generate \
  description="Vytvoř kvádr 50×30×10 mm s dírou uprostřed" \
  execute="true"
```

Output:
```python
from build123d import *

box = Box(50, 30, 10)
hole = Hole(8)  # 8 mm diameter
result = box - hole.moved(z=5)

ExportSTL(result, "model.stl")
```

---

### Example 2: Search Documentation

```bash
@semishape_rag_search query="extrude with taper"
```

Returns: Documentation snippets showing taper examples + web links

---

## Troubleshooting

### API Key Not Found

```
❌ No OpenRouter API key found.
Set `API_KEY_OPENROUTER` in your environment or configure it in the plugin settings.
```

**Solution:**
```bash
export API_KEY_OPENROUTER="sk-or-v1-your-key-here"
```

### Generation Timeout

```
⚠ Generation timed out (>60s)
```

**Solution:**
Increase `execution_timeout` in settings or try a simpler description.

### Syntax Errors in Generated Code

SemiShape automatically corrects most syntax errors. If you still see errors:

1. Review the generated code
2. Use `@semishape_execute` with corrected code
3. Report via GitHub issues

---

## Plugin Lifecycle

### Install
Called when plugin is first enabled:
- Creates output directories
- Symlinks agent initialization extension
- Installs Python dependencies

### Uninstall
Called when plugin is disabled:
- Removes temporary cache
- Preserves user data (output/, models/)
- Removes extensions symlink

### Update
Called during version updates:
- Preserves user configuration
- Regenerates extension symlinks
- Runs new dependency installers

---

## Architecture

```
semishape/
├── plugin.yaml               # Manifest
├── default_config.yaml       # Default settings
├── initialize.py             # Dependency installer
├── hooks.py                  # Lifecycle management
├── helpers/
│   ├── tool.py              # Base Tool class
│   ├── semishape_client.py  # Generation/execution logic
│   └── __init__.py
├── tools/
│   ├── semishape_generate.py    # CAD code generator
│   ├── semishape_execute.py     # CAD code executor
│   ├── semishape_rag_search.py  # Documentation search
│   └── __init__.py
├── extensions/
│   └── python/
│       └── agent_init/
│           └── _10_semishape.py  # Agent initialization
├── data/
│   ├── docs/                # build123d documentation (605 files)
│   ├── cache/               # Temporary cache
│   └── vectorstore/         # Cached embeddings
└── output/                  # Generated STL/STEP files
```

---

## Performance

- **Generation time:** 5-15s per model (depends on LLM model)
- **Execution time:** 2-5s per STL export
- **Documentation search:** <1s for local, 2-3s with web search
- **Memory usage:** ~500MB base + 100MB per concurrent request

---

## Security

✅ **Sandbox Execution**
- Code runs in isolated subprocess
- Resource limits (timeout, memory)
- No access to host environment

✅ **API Key Protection**
- Never logged or exposed in error messages
- Loaded from secure environment only
- Alternative: use Agent Zero Secrets management

✅ **Input Validation**
- Description length limits
- Code syntax validation
- AST analysis for dangerous imports

---

## Roadmap

- [ ] Real-time visualization in web UI
- [ ] Multi-part assembly support
- [ ] Constraint-based parametric generation
- [ ] Import CAD files for modification
- [ ] Batch generation API
- [ ] Custom training per use-case

---

## Contributing

SemiShape is open-source. To contribute:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request with description

---

## Support

- **GitHub Issues:** Report bugs and request features
- **Documentation:** See `AGENT_ZERO_INTEGRATION.md`
- **Community:** Join Agent Zero Discord

---

## License

SemiShape is licensed under the MIT License. See `LICENSE` file for details.

---

## Acknowledgments

Built with:
- [build123d](https://github.com/gumyr/build123d) — parametric CAD library
- [OpenRouter](https://openrouter.ai/) — multi-model LLM API
- [Agent Zero](https://github.com/agent0ai/agent0) — autonomous agent framework

---

**Made with ❤️ for the Agent Zero community**
