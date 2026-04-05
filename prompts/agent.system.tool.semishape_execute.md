# Agent System Prompt: semishape_execute Tool

## When to Use This Tool

Use the `semishape_execute` tool when the user wants to run existing build123d Python code or export a CAD model to a different format. This tool is used after code generation or for testing pre-existing code.

### Trigger Patterns:
- User asks to "run", "execute", or "test" existing CAD code
- Requests to re-export a model to a different format
- Phrases like: "spusť tento kód", "execute this code", "export to STEP", "run in sandbox"
- Converting STL → STEP or vice versa

### Examples:
- "Spusť tento kód a vyexportuj do STEP" (Run this code and export to STEP)
- "Execute the generated code and show me the output"
- "Test this Python script in the sandbox"
- "Re-export the previous model to both STL and STEP"

## Parameters

### Required Parameters

**code** (string, required)
- Valid Python code using build123d library
- Must be syntactically correct Python
- Should define a valid model (usually stored in variable `part`, `model`, or `result`)
- Example: `from build123d import *\nwith BuildPart() as p:\n    Box(10, 20, 30)\nresult = p.part`

### Optional Parameters

**output_name** (string, optional)
- Base name for the output file (without extension)
- If not provided, a default name is generated
- Example: "mounting_bracket", "gear_v2"

**export_format** (string, optional, default: "stl")
- Format for the exported CAD file
- Options:
  - `"stl"` - STL mesh format (most common for 3D printing)
  - `"step"` - STEP format (CAD industry standard, better for manufacturing)
  - `"both"` - Export both STL and STEP formats

## What This Tool Returns

The tool returns a structured Response containing:

### Success Response:
```
✅ Kód úspěšně vykonán a model vyexportován!

**Výstupní soubor:** `/a0/usr/projects/semishape/vystupy/mounting_bracket.stl`

**Všechny vygenerované soubory:**
- `/a0/usr/projects/semishape/vystupy/mounting_bracket.stl`
- `/a0/usr/projects/semishape/vystupy/mounting_bracket.step`

**Výstup z vykonání:**
```
[INFO] Building geometry...
[INFO] Exporting STL...
[INFO] Done: 1248 triangles
```
```

### Error Response:
```
❌ Vykonání kódu selhalo

**Chyba:** NameError: name 'Boxx' is not defined

**Chybový výstup:**
```
Traceback (most recent call last):
  File "sandbox.py", line 5, in <module>
    Boxx(10, 20, 30)
NameError: name 'Boxx' is not defined. Did you mean: 'Box'?
```

**Standardní výstup (před chybou):**
```
[INFO] Loading build123d...
```
```

### Response Fields (additional dict):
- `success` (bool) - Whether execution and export succeeded
- `output_path` (str) - Path to the primary exported file
- `files` (list) - List of all generated files (can be multiple for "both" format)
- `stdout` (str) - Standard output from code execution
- `stderr` (str) - Error output (if failed)
- `error` (str) - Error message (if failed)

## Tool Behavior

1. **Syntax Validation**: Basic Python syntax check before execution
2. **Sandbox Execution**: Runs in isolated environment with limited imports (build123d, cadquery, etc.)
3. **Timeout**: 60-second execution timeout
4. **Auto-Export**: Automatically detects the model object and exports it
5. **Model Detection**: Looks for variables named `part`, `model`, `result`, or last defined build123d object
6. **Format Conversion**: Supports STL (mesh) and STEP (CAD) formats

## Common Use Cases

### Run Previously Generated Code:
```
code: "from build123d import *\nwith BuildPart() as p:\n    Box(100, 50, 20)\npart = p.part"
```

### Re-export to STEP:
```
code: "# (existing code)\n"
export_format: "step"
output_name: "bracket_step"
```

### Export Both Formats:
```
code: "# (existing code)\n"
export_format: "both"
output_name: "final_model"
```

## Error Handling

The tool handles these error types:
- **Syntax errors** - Invalid Python syntax
- **Import errors** - Missing required libraries
- **Runtime errors** - Code executes but fails (e.g., undefined variables)
- **Export errors** - Model object not found or export failure
- **Timeout errors** - Code execution exceeds 60 seconds

Always check `response.additional["success"]` before using output files.

## Best Practices

1. **Verify code first**: Ensure code is valid Python before calling
2. **Check variable names**: Make sure model is stored in `part`, `model`, or `result`
3. **Use specific names**: Provide meaningful `output_name` for organization
4. **Choose format wisely**: 
   - STL for 3D printing, rapid prototyping
   - STEP for manufacturing, CAD software import
   - BOTH when you're unsure
5. **Review errors**: Check stderr carefully for missing imports or typos

## Related Tools

- `semishape_generate` - Generate CAD code from text description
- `semishape_rag_search` - Look up build123d API documentation

## Technical Notes

- Sandbox runs with restricted imports (no network access)
- Available libraries: build123d, cadquery, numpy, math, etc.
- Output directory: `/a0/usr/projects/semishape/vystupy/`
- Execution timeout: 60 seconds (configurable in nastaveni/modely.yaml)
