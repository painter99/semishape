# SemiShape - AI CAD Model Generator for Agent Zero

🎨 **Transform text descriptions into 3D parametric CAD models**

SemiShape is a hobby project that adds AI-powered CAD generation to [Agent Zero](https://github.com/agent0ai/agent-zero). Describe what you want in plain Czech or English and get a build123d Python script and an STL file back.

> ⚙️ **Status:** Personal hobby project — actively used, actively improved. Bugs may exist.

---

## How It Works

SemiShape does not use a separate AI model. It uses whatever model you have configured as active in your Agent Zero conversation. The plugin provides:

- **Structured prompts** that guide the model to generate valid build123d code
- **A sandboxed executor** that runs the generated code safely
- **STL/STEP export** from the executed build123d model
- **Documentation search** across the bundled build123d docs

---

## Features

✅ **Natural Language to 3D**  
Describe geometry in Czech or English — the active Agent Zero model generates the build123d code.

✅ **Sandbox Execution**  
Generated code runs in an isolated subprocess with a 60-second timeout.

✅ **STL and STEP Export**  
Outputs ready-to-print STL or CAD-interchange STEP files.

✅ **build123d Documentation Search**  
Search 600+ bundled doc files or the web for API examples.

✅ **Auto-Correction**  
Applies known fixes for common build123d mistakes before execution.

---

## Installation

### Prerequisites

- Agent Zero (v1.0+)
- OpenRouter API key (used by your Agent Zero conversation model)
- Python 3.10+

### Quick Start

1. **Install the plugin in Agent Zero UI**  
   Settings → Plugins → Install Plugin → Git → `https://github.com/painter99/semishape`

2. **Enable the plugin**  
   Settings → Plugins → SemiShape → Enable

3. **Set your OpenRouter API key** (if not already set in Agent Zero)  
   The plugin reads `API_KEY_OPENROUTER` or `OPENROUTER_API_KEY` from your environment.

---

## Usage

### Generate a CAD model

```
@semishape_generate description="Vytvoř kvádr 50×30×10 mm s dírou uprostřed" language="cs"
```

```
@semishape_generate description="Create a 50×30×10 mm box with a centered hole" language="en"
```

### Execute existing build123d code

```
@semishape_execute code="from build123d import *; box = Box(50, 30, 10)" export_format="stl"
```

### Search build123d documentation

```
@semishape_rag_search query="how to use fillet"
```

---

## Tools Reference

### `@semishape_generate`

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `description` | ✅ | — | Text description of the model |
| `language` | ❌ | `cs` | Code comments language: `cs` or `en` |

> **Model:** Uses the currently active Agent Zero model. To change the model, switch it in your Agent Zero settings.

### `@semishape_execute`

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `code` | ✅ | — | build123d Python code to execute |
| `output_name` | ❌ | auto | Output filename (without extension) |
| `export_format` | ❌ | `stl` | `stl`, `step`, or `both` |

### `@semishape_rag_search`

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `query` | ✅ | — | Natural language search query |
| `top_k` | ❌ | `5` | Number of results (1–10) |
| `use_web` | ❌ | `true` | Also search the web |

---

## Examples

See the [`examples/`](./examples/) directory for real screenshots and parameter breakdowns.

### Plate with spherical feet

```
@semishape_generate description="Vytvoř kvádr 55×35×8 mm s válcovitým otvorem průměru 30mm uprostřed
a půlkulovými nožičkami r=5mm v rozích" language="cs"
```

Result: 3D model, 5 912 triangles, 1.5 MB STL — see [examples/](./examples/README.md).

---

## Configuration

Default settings are in `default_config.yaml`. You can override them per-project in  
`.a0proj/plugins/semishape/config.yaml`.

Key settings:

```yaml
cad:
  default_format: stl      # stl | step
  execution_timeout: 60    # seconds
  sandbox_enabled: true
```

> **Note:** There is no separate model configuration — SemiShape uses whatever model is active in your Agent Zero conversation.

---

## Project Structure

```
semishape/
├── plugin.yaml              # Agent Zero plugin manifest
├── default_config.yaml      # Default settings
├── hooks.py                 # Plugin lifecycle (install / uninstall)
├── initialize.py            # Dependency installer
├── README.md
│
├── tools/
│   ├── semishape_generate.py   # Text → CAD code
│   ├── semishape_execute.py    # Execute code → STL/STEP
│   └── semishape_rag_search.py # Search build123d docs
│
├── helpers/
│   ├── tool.py              # Base class for tools
│   └── semishape_client.py  # Client wrapping src/
│
├── src/
│   ├── generation/          # LLM prompting and code parsing
│   ├── execution/           # Sandbox + STL/STEP export
│   └── rag/                 # Documentation retrieval
│
├── data/docs/               # 600+ build123d documentation files
├── prompts/                 # Tool system prompts
├── skills/                  # Agent Zero skill definition
└── examples/                # Usage screenshots and walkthroughs
```

---

## Troubleshooting

**Plugin not visible in Agent Zero UI**  
Settings → Plugins → look under the Custom tab, not the Browse (hub) tab.

**OpenRouter API key not found**  
Set `API_KEY_OPENROUTER` in your environment or in Agent Zero secrets.

**build123d not installed**  
Run `python initialize.py` inside the plugin directory, or re-enable the plugin to trigger the installer.

**Generated code fails to execute**  
Try rephrasing the description with explicit dimensions. The model sometimes needs clearer geometry.

---

## Contributing

This is a personal hobby project — contributions and issue reports are welcome.

- Open an issue for bugs or ideas
- PRs welcome, especially for build123d compatibility fixes

---

## License

MIT — see [LICENSE](./LICENSE).

---

## Related

- [Agent Zero](https://github.com/agent0ai/agent-zero) — the framework this plugin runs on
- [build123d](https://github.com/gumyr/build123d) — the CAD library used for 3D modelling
- [OpenRouter](https://openrouter.ai) — API gateway for LLM models
