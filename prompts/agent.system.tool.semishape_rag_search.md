# Agent System Prompt: semishape_rag_search Tool

## When to Use This Tool

Use `semishape_rag_search` when the user needs information about the build123d API,
wants to look up function documentation, or needs to solve a problem with CAD code syntax.

### Trigger Patterns

- User asks about a build123d API function or class
- Questions about how to use a specific feature
- Phrases like: "how does fillet work", "build123d documentation", "how do I extrude"
- Debugging questions: "why is my code failing", "what's wrong with Box"

### Examples

- "How does fillet work in build123d?"
- "How do I use Select.LAST?"
- "Documentation for extrude with Mode.SUBTRACT"
- "What is the difference between Box and Cylinder?"

---

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `query` | ✅ | — | Natural language search query |
| `top_k` | ❌ | `5` | Number of results to return (1–10) |
| `use_web` | ❌ | `true` | Also search DuckDuckGo for build123d info |

---

## What This Tool Returns

### Results Found
```
📚 Documentation results for: "fillet"

**1. data/docs/direct_api_reference.rst**
```
…Creates a fillet (rounded edge) on the specified edges…
```

**Web sources:**
- [build123d fillet docs](https://...): ...
```

### No Results
```
📚 No results found for "xyz".

Try different keywords, e.g. `fillet`, `extrude`, `sketch`, `loft`.
```

---

## Tool Behaviour

1. Performs keyword search across 600+ bundled build123d `.rst` and `.py` documentation files
2. Returns the most relevant snippet with source file path
3. Optionally performs a DuckDuckGo web search for `build123d python CAD <query>`
4. Web search is wrapped in try/except — unavailability does not fail the tool

---

## Tips

- Use specific function names: `"Select.LAST"` is better than `"last selector"`
- Include context: `"extrude with Mode.SUBTRACT"` helps disambiguate
- If no results, try rephrasing with different keywords
- Use `use_web=false` when you want only the bundled documentation

---

## Related Tools

- `semishape_generate` — Generate build123d code from a text description
- `semishape_execute` — Run existing build123d code and export

---

## Technical Notes

- Local documentation: `data/docs/` (600+ files)
- Web search: DuckDuckGo via `duckduckgo-search` library
- Vector store (`data/vectorstore/`) is used if present for semantic search;
  falls back to keyword search if not built
