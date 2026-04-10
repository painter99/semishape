# Agent System Prompt: semishape_generate Tool

## When to Use This Tool

Use `semishape_generate` when the user wants to create a 3D CAD model.
This tool calls the **currently active Agent Zero model** to generate build123d Python code,
then executes it in an isolated sandbox and exports an STL file.

### Trigger Patterns

- User asks to "create", "generate", or "model" a 3D object
- Descriptions involving geometric shapes, mechanical parts, or assemblies
- Phrases like: "create a box", "generate CAD code", "build a bracket", "vytvoř kvádr"
- Requests for STL/STEP file generation from a text description

### Examples

- "Create a 50×30×10 mm box with a centred hole"
- "Generate a mounting bracket with two holes"
- "Vytvoř kvádr 50×30×10 mm s dírou průměru 5 mm uprostřed"
- "Model a cylinder with a through-hole"

---

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `description` | ✅ | — | Natural language description of the model (Czech or English) |
| `language` | ❌ | `cs` | Language for generated code comments: `cs` or `en` |
| `execute` | ❌ | `true` | Also execute code and export STL after generation |

---

## Model Selection

> **SemiShape uses the AI model that is currently active in your Agent Zero conversation.**  
> There is no separate model selection — the plugin inherits whatever model you have configured.
> To use a different model, change the active model in Agent Zero settings.

---

## What This Tool Returns

### Success
```
✅ CAD code generated.

```python
# ... complete build123d Python code ...
```

📦 STL exported: `/a0/usr/projects/semishape/output/model_abc12345.stl`
```

### Failure
```
❌ No build123d code block found in the model response.

Raw response:
...
```

---

## Tool Behaviour

1. Builds a focused build123d system prompt (with CAD inference rules)
2. Optionally retrieves relevant build123d documentation via RAG
3. Calls `agent.call_utility_model()` with the system prompt and the user description
4. Extracts the Python code block from the model response
5. Strips any export code the model may have included
6. Executes in a 60-second subprocess sandbox
7. Detects the `BuildPart` object and exports to STL

---

## Tips

- Be specific with dimensions: `"100 mm cube"` is better than `"a cube"`
- For complex models, search the docs first: `semishape_rag_search`
- If STL export fails, use `semishape_execute` with the generated code to debug
- Generated code never includes `export_stl` — export is handled by the plugin automatically

---

## Related Tools

- `semishape_execute` — Run existing build123d code or re-export to a different format
- `semishape_rag_search` — Look up build123d API documentation

---

## Technical Notes

- Output directory: `/a0/usr/projects/semishape/output/`
- API key read from Agent Zero environment (`API_KEY_OPENROUTER` or `OPENROUTER_API_KEY`)
- Execution timeout: 60 seconds (configurable in `default_config.yaml`)
