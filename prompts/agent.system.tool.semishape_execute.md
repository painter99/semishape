# Agent System Prompt: semishape_execute Tool

## When to Use This Tool

Use `semishape_execute` when the user wants to run existing build123d Python code,
re-export a model to a different format, or test code that has already been generated.

### Trigger Patterns

- User asks to "run", "execute", or "test" existing CAD code
- Requests to re-export a model (e.g., STL → STEP)
- Phrases like: "execute this code", "export to STEP", "run in sandbox"

### Examples

- "Execute the generated code and export as STEP"
- "Run this build123d script"
- "Re-export the previous model to both STL and STEP"

---

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `code` | ✅ | — | build123d Python code to execute |
| `output_name` | ❌ | `model` | Output filename stem (without extension) |
| `export_format` | ❌ | `stl` | Export format: `stl` \| `step` \| `both` |

---

## What This Tool Returns

### Success
```
✅ CAD model exported successfully.

📦 STL: `/a0/usr/projects/semishape/output/model.stl`
📦 STEP: `/a0/usr/projects/semishape/output/model.step`
```

### Failure
```
❌ Execution succeeded but no output file was produced.

Make sure your code uses `with BuildPart() as part:` syntax...
```

---

## Tool Behaviour

1. Strips any export code the user may have included in the code block
2. Appends auto-generated export code for each requested format
3. Runs the combined script in an isolated subprocess (60-second timeout)
4. Detects the `BuildPart` object and calls `export_stl` / `export_step`
5. Returns paths of files that were actually created

---

## Tips

- Use `export_format="both"` to get both STL (for 3D printing) and STEP (for CAD software)
- Use `output_name` to give the file a meaningful name
- If execution fails, check that the code uses `with BuildPart() as part:` syntax
- Do NOT include `export_stl()` calls in the code — the tool adds them automatically

---

## Related Tools

- `semishape_generate` — Generate build123d code from a text description
- `semishape_rag_search` — Look up build123d API documentation

---

## Technical Notes

- Output directory: `/a0/usr/projects/semishape/output/`
- Execution timeout: 60 seconds (configurable in `default_config.yaml`)
- Supported formats: `stl`, `step`, `both`
