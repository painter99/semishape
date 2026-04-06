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

**language** (string, optional, default: "cs")
- Language for code comments and variable names
- Options: `"cs"` (Czech) or `"en"` (English)

## Model Selection

> **Note:** SemiShape uses the AI model that is currently active in your Agent Zero conversation.
> There is no separate model selection — the plugin inherits the model you have configured in Agent Zero.
> To use a different model for CAD generation, change the active model in your Agent Zero settings.

## What This Tool Returns

The tool returns build123d Python code and (optionally) exports it to STL:

### Success Response:
```
✅ CAD code generated!

**Generated code:**
```python
# ... complete Python code using build123d ...
```

**STL file:** `/a0/usr/projects/semishape/output/model_name.stl`
```

### Error Response:
```
❌ Generation failed

**Error:** [Error description]
```

## Tool Behavior

1. **Generates build123d Python code** from the text description using the active Agent Zero model
2. **Syntax Validation**: Checks generated code for Python syntax errors before execution
3. **Auto-Fix**: Applies known fixes for common build123d API mistakes
4. **Sandbox Execution**: Runs code in isolated environment with 60-second timeout
5. **Auto-Export**: Exports to STL format upon successful execution

## Common Use Cases

### Basic Shapes:
```
description: "Create a 100mm cube"
```

### With Features:
```
description: "Vytvoř desku 100x50x5mm se 4 dírami průměru 3mm v rozích"
```

### Complex Geometry:
```
description: "Vytvoř kvádr 55x35x8 mm s válcovitým otvorem uprostřed a půlkulovými nožičkami r=5mm v rozích"
```

## Best Practices

1. **Be specific with dimensions**: "100mm cube" is better than "a cube"
2. **Use simple language**: Avoid overly complex technical jargon
3. **One object at a time**: For assemblies, describe the relationship clearly
4. **Verify output**: Always confirm the STL file was generated at `output_path`

## Related Tools

- `semishape_execute` - Run existing build123d code or re-export to different format
- `semishape_rag_search` - Look up build123d API documentation

## Technical Notes

- Uses build123d library for CAD operations
- Runs in isolated Python sandbox with limited imports
- Output directory: `/a0/usr/projects/semishape/output/`
- API keys loaded from Agent Zero secrets (`API_KEY_OPENROUTER` or `OPENROUTER_API_KEY`)
