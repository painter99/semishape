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
from pathlib import Path
from typing import Optional

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
        model=args.model,
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
    
    if args.verbose:
        print("=" * 60)
        print("RAW RESPONSE:")
        print("-" * 60)
        print(result.raw_response[:500] + "..." if len(result.raw_response) > 500 else result.raw_response)
        print()
    
    print("=" * 60)
    print("GENERATED CODE:")
    print("-" * 60)
    print(result.code)
    print("-" * 60)
    
    if result.explanation:
        print(f"\nEXPLANATION:\n{result.explanation}")
    
    if result.warnings:
        print("\nWARNINGS:")
        for w in result.warnings:
            print(f"  - {w}")
    
    if result.rag_sources:
        print("\nRAG SOURCES:")
        for s in result.rag_sources:
            print(f"  - {s}")
    
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(result.code, encoding='utf-8')
        print(f"\nCode saved to: {output_path}")
    
    print(f"\nModel: {result.model}")
    print(f"Tokens: {result.usage.get('total_tokens', 'N/A')}")
    
    return 0 if result.code else 1


def cmd_execute(args):
    """Execute build123d code and export."""
    ss = SemiShape()
    
    if args.file:
        code = Path(args.file).read_text(encoding='utf-8')
        print(f"Executing: {args.file}")
    else:
        print("Reading code from stdin (Ctrl+D to finish)...")
        code = sys.stdin.read()
    
    print(f"   Export format: {args.format}")
    print()
    
    result = ss.execute(
        code=code,
        export_format=args.format,
        timeout=args.timeout,
    )
    
    print("=" * 60)
    print("EXECUTION RESULT:")
    print("-" * 60)
    print(f"Status: {'SUCCESS' if result.success else 'FAILED'}")
    
    if result.stdout:
        print(f"\nSTDOUT:\n{result.stdout}")
    
    if result.stderr:
        print(f"\nSTDERR:\n{result.stderr}")
    
    if result.output_path:
        print(f"\nOutput file: {result.output_path}")
    
    if result.files:
        print("\nGenerated files:")
        for f in result.files:
            print(f"  - {f}")
    
    return 0 if result.success else 1


def cmd_rag_search(args):
    """Search build123d documentation."""
    ss = SemiShape(use_rag=True)
    
    print(f"Searching for: {args.query}")
    print(f"   Top {args.top_k} results")
    print()
    
    results = ss.rag_search(
        query=args.query,
        top_k=args.top_k,
        filter_code=args.code_only,
    )
    
    if not results:
        print("No results found.")
        return 1
    
    for i, r in enumerate(results, 1):
        if "error" in r:
            print(f"Error: {r['error']}")
            return 1
        
        print("=" * 60)
        print(f"Result {i} (score: {r['score']:.3f})")
        print(f"Source: {r['source']}")
        if r['section']:
            print(f"Section: {r['section']}")
        print("-" * 60)
        
        content = r['content']
        if args.max_length and len(content) > args.max_length:
            content = content[:args.max_length] + "..."
        
        print(content)
        print()
    
    return 0


def cmd_interactive(args):
    """Interactive REPL mode."""
    ss = SemiShape(
        model=args.model,
        provider=args.provider,
        language=args.language,
    )
    
    print("\n" + "=" * 60)
    print("SemiShape Interactive Mode")
    print("=" * 60)
    print("\nCommands:")
    print("  <query>        - Generate build123d code")
    print("  /execute       - Execute last generated code")
    print("  /search <q>    - Search documentation")
    print("  /language <en|cs> - Set language")
    print("  /help          - Show help")
    print("  /quit          - Exit")
    print()
    
    last_code = None
    language = args.language
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if not user_input:
                continue
            
            if user_input.startswith('/'):
                parts = user_input.split(maxsplit=1)
                cmd = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else None
                
                if cmd in ('/quit', '/exit'):
                    print("Goodbye!")
                    break
                
                elif cmd == '/help':
                    print("\nCommands:")
                    print("  <query>        - Generate build123d code")
                    print("  /execute       - Execute last generated code")
                    print("  /search <q>    - Search documentation")
                    print("  /language <en|cs> - Set language")
                    print("  /help          - Show this help")
                    print("  /quit          - Exit")
                
                elif cmd == '/execute':
                    if not last_code:
                        print("No code to execute. Generate some code first.")
                        continue
                    
                    print("\nExecuting...")
                    result = ss.execute(last_code, export_format=args.format)
                    
                    if result.success:
                        print(f"Execution successful!")
                        if result.output_path:
                            print(f"Output: {result.output_path}")
                    else:
                        print(f"Execution failed:")
                        print(result.stderr)
                
                elif cmd == '/search':
                    if not arg:
                        print("Please provide a search query.")
                        continue
                    
                    results = ss.rag_search(arg, top_k=3)
                    for i, r in enumerate(results, 1):
                        if "error" in r:
                            print(f"Error: {r['error']}")
                            continue
                        print(f"\n[{i}] {r['source']} (score: {r['score']:.3f})")
                        print(r['content'][:200] + "...")
                
                elif cmd == '/language':
                    if arg in ('en', 'cs'):
                        language = arg
                        print(f"Language set to: {language.upper()}")
                    else:
                        print("Use 'en' or 'cs'")
                
                else:
                    print(f"Unknown command: {cmd}")
                
                continue
            
            # Generate code
            print("\nGenerating...")
            result = ss.generate_code(user_input, language=language)
            
            if result.code:
                last_code = result.code
                print("\n" + "=" * 60)
                print(result.code)
                print("=" * 60)
                
                if result.warnings:
                    print("Warnings:", ", ".join(result.warnings))
            else:
                print("No code generated.")
                if result.explanation:
                    print(result.explanation)
        
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
    
    return 0


def cmd_run(args):
    """Generate and execute in one step."""
    ss = SemiShape(
        model=args.model,
        provider=args.provider,
        language=args.language,
    )
    
    print(f"\nGenerating and executing: {args.query}")
    print(f"   Language: {args.language.upper()}")
    print(f"   Export: {args.format}")
    print()
    
    result = ss.generate_and_execute(
        query=args.query,
        language=args.language,
        export_format=args.format,
        timeout=args.timeout,
    )
    
    print("=" * 60)
    print("RESULT:")
    print("-" * 60)
    print(f"Status: {'SUCCESS' if result.success else 'FAILED'}")
    
    if result.code:
        print("\nCODE:")
        print("-" * 60)
        print(result.code[:500] + "..." if len(result.code) > 500 else result.code)
    
    if result.output_path:
        print(f"\nOutput: {result.output_path}")
    
    if result.warnings:
        print("\nWARNINGS:")
        for w in result.warnings:
            print(f"  - {w}")
    
    print(f"\nGeneration: {result.generation_time:.2f}s")
    print(f"Execution: {result.execution_time:.2f}s")
    
    return 0 if result.success else 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='semishape',
        description='SemiShape - build123d CAD Code Generation',
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate build123d code')
    gen_parser.add_argument('query', help='Natural language description')
    gen_parser.add_argument('--language', '-l', default='en', choices=['en', 'cs'])
    gen_parser.add_argument('--model', '-m', default='openai/gpt-4o-mini')
    gen_parser.add_argument('--provider', '-p', default='openrouter')
    gen_parser.add_argument('--output', '-o', help='Output file path')
    gen_parser.add_argument('--no-rag', action='store_true')
    gen_parser.add_argument('--verbose', '-v', action='store_true')
    gen_parser.set_defaults(func=cmd_generate)
    
    # Execute command
    exec_parser = subparsers.add_parser('execute', help='Execute build123d code')
    exec_parser.add_argument('file', nargs='?', help='Python file to execute')
    exec_parser.add_argument('--format', '-f', default='stl', choices=['stl', 'step'])
    exec_parser.add_argument('--timeout', '-t', type=int, default=60)
    exec_parser.set_defaults(func=cmd_execute)
    
    # RAG search command
    rag_parser = subparsers.add_parser('rag-search', help='Search documentation')
    rag_parser.add_argument('query', help='Search query')
    rag_parser.add_argument('--top-k', '-k', type=int, default=5)
    rag_parser.add_argument('--code-only', '-c', action='store_true')
    rag_parser.add_argument('--max-length', type=int, default=500)
    rag_parser.set_defaults(func=cmd_rag_search)
    
    # Run command (generate and execute)
    run_parser = subparsers.add_parser('run', help='Generate and execute')
    run_parser.add_argument('query', help='Natural language description')
    run_parser.add_argument('--language', '-l', default='en', choices=['en', 'cs'])
    run_parser.add_argument('--format', '-f', default='stl', choices=['stl', 'step'])
    run_parser.add_argument('--model', '-m', default='openai/gpt-4o-mini')
    run_parser.add_argument('--provider', '-p', default='openrouter')
    run_parser.add_argument('--timeout', '-t', type=int, default=60)
    run_parser.set_defaults(func=cmd_run)
    
    # Interactive command
    int_parser = subparsers.add_parser('interactive', help='Interactive REPL')
    int_parser.add_argument('--language', '-l', default='en', choices=['en', 'cs'])
    int_parser.add_argument('--model', '-m', default='openai/gpt-4o-mini')
    int_parser.add_argument('--provider', '-p', default='openrouter')
    int_parser.add_argument('--format', '-f', default='stl')
    int_parser.set_defaults(func=cmd_interactive)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
