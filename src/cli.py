#!/usr/bin/env python3
"""SemiShape Command-Line Interface.

Provides CLI commands for testing and using SemiShape:
- generate: Generate build123d code from natural language
- execute: Execute build123d code and export
- rag-search: Search build123d documentation
- interactive: Interactive REPL mode
"""

import argparse
import json
import logging
import sys
import os
from pathlib import Path
from typing import Optional

# CRITICAL: Set environment variables BEFORE any imports
# This must happen before any module that might use them
_a0_env = Path("/a0/usr/.env")
if _a0_env.exists():
    with open(_a0_env) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

# Set API key explicitly if not already set
if 'API_KEY_OPENROUTER' not in os.environ or not os.environ['API_KEY_OPENROUTER']:
    # Try to read from .env file directly
    if _a0_env.exists():
        with open(_a0_env) as f:
            for line in f:
                if line.startswith('API_KEY_OPENROUTER='):
                    os.environ['API_KEY_OPENROUTER'] = line.split('=', 1)[1].strip()
                    break

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.semishape import SemiShape, SemiShapeResult, Language
from src.generation import GeneratedCode

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cmd_generate(args):
    """Generate build123d code from natural language."""
    ss = SemiShape(
        model=args.model or 'openai/gpt-4o-mini',
        provider=args.provider,
        language=args.language,
        use_rag=not args.no_rag,
    )
    
    print(f"\nGenerating code for: {args.query}")
    print(f"   Language: {args.language.upper()}")
    print(f"   Use RAG: {not args.no_rag}")
    print()
    
    result = ss.generate_code(
        query=args.query,
        language=args.language,
        use_rag=not args.no_rag,
    )
    
    if not result.has_errors():
        print("=" * 60)
        print("GENERATED CODE:")
        print("=" * 60)
        print(result.code)
        print("=" * 60)
        if result.rag_sources:
            print(f"\nUsed {len(result.rag_sources)} RAG contexts")
    else:
        print(f"ERROR: {result.error}")
    
    return 0 if not result.has_errors() else 1


def cmd_execute(args):
    """Execute build123d code."""
    # Read code from file or argument
    if args.file:
        code = Path(args.file).read_text()
    elif args.code:
        code = args.code
    else:
        print("ERROR: Either --file or --code required")
        return 1
    
    ss = SemiShape()
    result = ss.execute_code(
        code=code,
        timeout=args.timeout,
        export_format=args.export,
    )
    
    if not result.has_errors():
        print("=" * 60)
        print("EXECUTION SUCCESS")
        print("=" * 60)
        if result.output_file:
            print(f"Output file: {result.output_file}")
        if result.output:
            print(f"Output: {result.output}")
    else:
        print(f"EXECUTION FAILED: {result.error}")
    
    return 0 if not result.has_errors() else 1


def cmd_rag_search(args):
    """Search build123d documentation."""
    ss = SemiShape(language=args.language)
    results = ss.rag_search(query=args.query, top_k=args.top_k)
    
    print(f"Searching for: {args.query}")
    print(f"   Top {args.top_k} results\n")
    
    for i, doc in enumerate(results, 1):
        score = doc.metadata.get('distance', 0)
        source = doc.metadata.get('source', 'unknown')
        section = doc.metadata.get('section', '')
        
        print(f"{'=' * 60}")
        print(f"Result {i} (score: {score:.3f})")
        print(f"Source: {source}")
        print(f"Section: {section}")
        print("-" * 60)
        print(doc.page_content[:500])
        print()
    
    return 0


def cmd_interactive(args):
    """Interactive REPL mode."""
    print("SemiShape Interactive Mode")
    print("Type 'help' for commands, 'quit' to exit\n")
    
    ss = SemiShape(
        model=args.model or 'openai/gpt-4o-mini',
        provider=args.provider,
        language=args.language,
        use_rag=not args.no_rag,
    )
    
    while True:
        try:
            query = input("semishape> ").strip()
            if not query:
                continue
            
            if query.lower() in ('quit', 'exit', 'q'):
                print("Goodbye!")
                break
            
            if query.lower() == 'help':
                print("""Commands:
  <query>      - Generate build123d code
  rag <query>  - Search documentation
  lang <cs/en>  - Switch language
  help          - Show this message
  quit          - Exit
""")
                continue
            
            if query.lower().startswith('rag '):
                search_query = query[4:]
                results = ss.rag_search(search_query)
                for doc in results:
                    print(f"\n{doc.page_content[:300]}...\n")
                continue
            
            if query.lower().startswith('lang '):
                lang = query[5:].strip().lower()
                if lang in ('cs', 'en'):
                    ss = SemiShape(language=lang)
                    print(f"Language: {lang}")
                else:
                    print("Use 'cs' or 'en'")
                continue
            
            # Generate code
            result = ss.generate_code(query)
            if not result.has_errors():
                print(f"\n{result.code}\n")
            else:
                print(f"\nERROR: {result.error}\n")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"ERROR: {e}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="SemiShape - AI CAD Assistant for build123d"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate build123d code")
    gen_parser.add_argument("query", help="Natural language description")
    gen_parser.add_argument("--language", "-l", default="cs", choices=["cs", "en"],
                           help="Language (cs/en)")
    gen_parser.add_argument("--model", "-m", default=None, help="Model name")
    gen_parser.add_argument("--provider", "-p", default="openrouter", help="LLM provider")
    gen_parser.add_argument("--no-rag", action="store_true", help="Disable RAG")
    gen_parser.set_defaults(func=cmd_generate)
    
    # Execute command
    exec_parser = subparsers.add_parser("execute", help="Execute build123d code")
    exec_parser.add_argument("--file", "-f", help="Code file")
    exec_parser.add_argument("--code", "-c", help="Code string")
    exec_parser.add_argument("--timeout", "-t", type=int, default=60, help="Timeout")
    exec_parser.add_argument("--export", "-e", default="stl", help="Export format")
    exec_parser.set_defaults(func=cmd_execute)
    
    # RAG search command
    rag_parser = subparsers.add_parser("rag-search", help="Search documentation")
    rag_parser.add_argument("query", help="Search query")
    rag_parser.add_argument("--top-k", "-k", type=int, default=3, help="Results")
    rag_parser.add_argument("--language", "-l", default="cs", help="Language")
    rag_parser.set_defaults(func=cmd_rag_search)
    
    # Interactive mode
    int_parser = subparsers.add_parser("interactive", help="Interactive mode")
    int_parser.add_argument("--language", "-l", default="cs", help="Language")
    int_parser.add_argument("--model", "-m", default=None, help="Model")
    int_parser.add_argument("--provider", "-p", default="openrouter", help="Provider")
    int_parser.add_argument("--no-rag", action="store_true", help="Disable RAG")
    int_parser.set_defaults(func=cmd_interactive)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
