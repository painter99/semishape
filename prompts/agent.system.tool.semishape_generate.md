# Agent System Prompt: semishape_generate Tool

## When to Use This Tool

Use the `semishape_generate` tool when the user wants to create a 3D CAD model using the build123d Python library. This tool converts natural language descriptions into executable Python CAD code.

### Trigger Patterns:
- User asks to "create", "generate", or "model" a 3D object
- Descriptions involving geometric shapes, mechanical parts, or assemblies
- Phrases like: "vytvoř model", "vytvoř kvádr", "create a box", "generate CAD code", "build a bracket"
- Requests for STL/STEP file generation from text descriptions

### Examples:
- "Vytvoř kvádr 50x30x10mm" (Create a 50x30x10mm box)
- "Generate a mounting bracket with two holes"
- "Model a gear with 20 teeth"
- "Create a cylinder with a hole through the center"

## Parameters

### Required Parameters

**description** (string, required)
- Natural language description of the desired 3D model
- Can be in Czech or English
- Should include dimensions, shapes, and relationships
- Example: "Vytvoř kvádr 50x30x10mm s dírou průměru 5mm uprostřed"

### Optional Parameters

**model** (string, optional, default: "auto")
- AI model selection strategy
- Options:
  - `"auto"` - Automatic selection (Kimi K2.5 → Minimax fallback)
  - `"kimi"` - Force use of Kimi K2.5 (higher quality, higher cost)
  - `"minimax"` - Force use of Minimax 2.7 (lower cost, faster)

**language** (string, optional, default: "cs")
- Language for code comments and variable names
- Options: `"cs"` (Czech) or `"en"` (English)

## What This Tool Returns

The tool returns a structured Response containing:

### Success Response:
```
✅ CAD kód úspěšně vygenerován!

**Model:** moonshotai/kimi-k2.5
**Cena:** $0.0042
🔧 Automatické opravy: Ano (if applicable)

**STL soubor:** `/a0/usr/projects/semishape/vystupy/model_abc123.stl`

**Vygenerovaný kód:**
```python
# ... complete Python code using build123d ...
```
```

### Error Response:
```
❌ Generování selhalo

**Chyba:** [Error description]
**Použitý model:** minimax/minimax-m2.7

**Vygenerovaný kód (před selháním):**
```python
# ... code that failed ...
```
```

### Response Fields (additional dict):
- `success` (bool) - Whether generation and execution succeeded
- `code` (str) - The generated Python code
- `output_path` (str) - Path to the exported STL file (if successful)
- `files` (list) - List of all generated files
- `model` (str) - Which AI model was actually used
- `cost_usd` (float) - API cost in USD
- `was_fixed` (bool) - Whether automatic syntax fixes were applied
- `error` (str) - Error message (if failed)

## Tool Behavior

1. **Dual-Model Strategy**: Automatically tries Kimi K2.5 first, falls back to Minimax 2.7 if needed
2. **Syntax Validation**: Checks generated code for Python syntax errors before execution
3. **Auto-Fix**: Applies known fixes for common build123d API mistakes
4. **Sandbox Execution**: Runs code in isolated environment with 60-second timeout
5. **Auto-Export**: Automatically exports to STL format upon successful execution
6. **Cost Tracking**: Returns estimated API cost in USD

## Common Use Cases

### Basic Shapes:
```
description: "Create a 100mm cube"
```

### With Features:
```
description: "Vytvoř desku 100x50x5mm se 4 dírami průměru 3mm v rozích"
```

### Assemblies:
```
description: "Generate a box with a lid, both 50x30x20mm, with matching screw holes"
```

## Error Handling

The tool handles these error types internally:
- **API errors** - Model unavailable, rate limits
- **Syntax errors** - Invalid Python code (with auto-fix attempts)
- **Runtime errors** - Import errors, execution failures in sandbox
- **Export errors** - STL generation failures

Always check `response.additional["success"]` before using the generated code or output files.

## Best Practices

1. **Be specific with dimensions**: "100mm cube" is better than "a cube"
2. **Use simple language**: Avoid overly complex technical jargon
3. **One object at a time**: For assemblies, describe the relationship clearly
4. **Check for fixes**: If `was_fixed` is true, review the auto-corrected code
5. **Verify output**: Always confirm the STL file was generated at `output_path`

## Related Tools

- `semishape_execute` - Run existing code or re-export to different format
- `semishape_rag_search` - Look up build123d API documentation

## Technical Notes

- Uses build123d library for CAD operations
- Runs in isolated Python sandbox with limited imports
- Output directory: `/a0/usr/projects/semishape/vystupy/`
- API keys loaded from Agent Zero secrets (OPENROUTER_API_KEY)
- Config loaded from `nastaveni/modely.yaml`
