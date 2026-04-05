# Agent System Prompt: semishape_rag_search Tool

## When to Use This Tool

Use the `semishape_rag_search` tool when the user needs information about build123d API, wants to look up function documentation, or needs to solve problems with CAD code syntax.

### Trigger Patterns:
- User asks about build123d API, functions, or classes
- Questions about how to use specific features
- Phrases like: "jak funguje fillet", "how to use extrude", "build123d dokumentace"
- Debugging questions: "proč nefunguje Box", "why is my code failing"
- API reference lookups: "dokumentace pro Circle", "Select.LAST documentation"

### Examples:
- "Jak funguje fillet v build123d?" (How does fillet work in build123d?)
- "How do I use Select.LAST?"
- "Dokumentace pro extrude s Mode.SUBTRACT"
- "What's the difference between Box and Cylinder?"
- "How to select faces using Axis?"

## Parameters

### Required Parameters

**query** (string, required)
- Natural language search query about build123d
- Can describe what you want to learn about
- Example: "jak použít fillet na hrany kvádru"

### Optional Parameters

**top_k** (integer, optional, default: 5)
- Number of results to return (1-10)
- Higher values give more context but longer responses
- Recommended: 3-5 for quick lookups, 7-10 for comprehensive research

**use_web** (boolean, optional, default: True)
- Whether to include DuckDuckGo web search results
- Web search finds official build123d docs and examples
- Recommended: True for better coverage, False when offline

## What This Tool Returns

The tool returns a structured Response containing:

### Success Response:
```
📚 Nalezené dokumentace pro: "jak použít fillet"

[1] fillet.py (relevance: 0.94):
Creates a fillet (rounded edge) on specified edges...
Example: fillet(model.edges(), radius=2.0)
...

[2] selectors.rst (relevance: 0.87):
Selectors in build123d allow you to reference geometry...
Use Select.LAST for the most recently created geometry...

**Nalezeno dokumentů:** 5

**Webové zdroje:**
1. [build123d fillet documentation](https://build123d.readthedocs.io/...)
2. [GitHub fillet example](https://github.com/...)

**Lokální zdroje (RAG):**
- `fillet.py`
- `selectors.rst`
- `edges.py`
```

### No Results Response:
```
📚 Nalezené dokumentace pro: "xyz nonexistent function"

Žádné výsledky nenalezeny.

**Nalezeno dokumentů:** 0

**Lokální zdroje (RAG):**
(none)
```

### Error Response:
```
❌ Vyhledávání selhalo

**Chyba:** ChromaDB connection failed

**Query:** "fillet documentation"
```

### Response Fields (additional dict):
- `success` (bool) - Whether search succeeded
- `query` (str) - The search query that was used
- `top_k` (int) - Number of results requested
- `document_count` (int) - Number of documents actually found
- `rag_sources` (list) - List of local document paths found
- `web_results` (list) - List of web search results (if use_web=True)

## Tool Behavior

1. **Vector Search**: Uses ChromaDB with 605+ indexed build123d documentation files
2. **Semantic Matching**: Finds relevant docs even if wording differs from indexed content
3. **Hybrid Search**: Combines RAG (local) + DuckDuckGo (web) for comprehensive results
4. **Relevance Scoring**: Each result includes a similarity score (0.0-1.0)
5. **Snippet Truncation**: Long content is truncated to ~500 chars with "..."
6. **Query Cache**: Recent queries may be cached for faster response

## Common Use Cases

### Look Up Function:
```
query: "Circle function parameters"
```

### Learn About Selectors:
```
query: "Select.LAST usage examples"
```

### Debug Code:
```
query: "Mode.SUBTRACT not working"
```

### Learn Pattern:
```
query: "2D sketch first then extrude workflow"
use_web: true
```

### Offline Search:
```
query: "Box class methods"
use_web: false  # Only local docs
```

## Error Handling

The tool handles these error types:
- **Database errors** - ChromaDB not initialized or corrupted
- **Embedding errors** - Failed to create query embeddings
- **Network errors** - Web search failed (falls back to local only)
- **Timeout errors** - Search took too long (returns partial results)

If you see database errors, the RAG index may need to be rebuilt using `rag-index` command.

## Best Practices

1. **Be specific**: "fillet with radius parameter" > "fillet"
2. **Use function names**: "Select.LAST" is better than "last selector"
3. **Include context**: "extrude with Mode" helps disambiguate
4. **Check relevance**: Higher score = more relevant (0.9+ = very relevant)
5. **Combine results**: RAG gives snippets, web gives links - use both
6. **Iterate**: If no results, try rephrasing with different keywords

## RAG vs Web Search

| Aspect | RAG (Local) | Web Search |
|--------|-------------|------------|
| Sources | 605 documentation files | Official docs + GitHub |
| Latency | ~8ms | ~1-3 seconds |
| Offline | ✓ Yes | ✗ No |
| Freshness | Index date only | Latest official docs |
| Content | Full code examples | Links + summaries |

Use `use_web: true` for most queries unless you need offline operation.

## Related Tools

- `semishape_generate` - Create CAD code (can auto-use RAG internally)
- `semishape_execute` - Run and export generated code

## Technical Notes

- Vector store: ChromaDB at `/a0/usr/projects/semishape/data/vectorstore/`
- Embedding model: Sentence-transformers (local)
- 605 documents indexed (build123d docs + examples)
- Default similarity threshold: 0.7
- Max results: 10 (enforced per query)
- Query latency: ~8-15ms for local RAG only

## Index Rebuilding

If you see "no results" for common queries, the index may be stale or missing:

```bash
# Rebuild the RAG index from build123d source
python scripts/build_vectorstore.py
```

This requires download of build123d documentation (can be slow first time).
