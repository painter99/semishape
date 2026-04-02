#!/usr/bin/env python3
"""Build the ChromaDB vectorstore from build123d documentation.

This script:
1. Loads all RST files from the docs directory
2. Chunks them into semantic units preserving code examples
3. Stores them in ChromaDB with embeddings
4. Runs test queries to verify the setup

Usage:
    python scripts/build_vectorstore.py
    python scripts/build_vectorstore.py --rebuild
    python scripts/build_vectorstore.py --test-only
"""

import argparse
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.rag import RSTChunker, VectorStore, Retriever, chunk_directory


def build_vectorstore(
    docs_path: Path,
    vectorstore_path: Path,
    collection_name: str = "build123d_docs",
    embedding_model: str = "all-MiniLM-L6-v2",
    rebuild: bool = False,
    verbose: bool = True
) -> VectorStore:
    """Build the vectorstore from documentation.
    
    Args:
        docs_path: Path to documentation directory
        vectorstore_path: Path to store ChromaDB
        collection_name: Name of the collection
        embedding_model: Name of embedding model
        rebuild: If True, clear existing data first
        verbose: Print progress information
    
    Returns:
        VectorStore instance
    """
    start_time = time.time()
    
    # Initialize chunker
    if verbose:
        print(f"\n{'='*60}")
        print(f"Building VectorStore for build123d Documentation")
        print(f"{'='*60}")
        print(f"\nDocs path: {docs_path}")
        print(f"Vectorstore path: {vectorstore_path}")
        print(f"Embedding model: {embedding_model}")
    
    # Count RST files
    rst_files = list(docs_path.rglob("*.rst"))
    if verbose:
        print(f"\nFound {len(rst_files)} RST files to process")
    
    if not rst_files:
        print(f"ERROR: No RST files found in {docs_path}")
        sys.exit(1)
    
    # Initialize vectorstore
    if verbose:
        print(f"\nInitializing vectorstore...")
    
    vectorstore = VectorStore(
        persist_dir=vectorstore_path,
        collection_name=collection_name,
        embedding_model_name=embedding_model
    )
    
    if rebuild:
        if verbose:
            print("Clearing existing data...")
        vectorstore.clear()
    
    # Check if already populated
    existing_count = vectorstore.count()
    if existing_count > 0 and not rebuild:
        if verbose:
            print(f"\nVectorstore already contains {existing_count} documents")
            print("Use --rebuild to recreate from scratch")
        return vectorstore
    
    # Chunk all documents
    if verbose:
        print(f"\nChunking documents...")
    
    chunker = RSTChunker(
        chunk_size=1000,
        chunk_overlap=200,
        preserve_code_blocks=True
    )
    
    all_chunks = []
    for i, rst_file in enumerate(rst_files):
        try:
            chunks = chunker.parse_file(rst_file)
            all_chunks.extend(chunks)
            if verbose and (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(rst_files)} files, {len(all_chunks)} chunks")
        except Exception as e:
            print(f"Warning: Failed to process {rst_file}: {e}")
            continue
    
    if verbose:
        print(f"\nTotal chunks created: {len(all_chunks)}")
        code_chunks = sum(1 for c in all_chunks if c.chunk_type == 'code')
        text_chunks = sum(1 for c in all_chunks if c.chunk_type == 'text')
        print(f"  - Code chunks: {code_chunks}")
        print(f"  - Text chunks: {text_chunks}")
    
    # Convert chunks to dicts
    chunk_dicts = [c.to_dict() for c in all_chunks]
    
    # Add to vectorstore
    if verbose:
        print(f"\nAdding chunks to vectorstore...")
    
    added = vectorstore.add_chunks(chunk_dicts, batch_size=100)
    
    elapsed = time.time() - start_time
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"VectorStore Build Complete")
        print(f"{'='*60}")
        print(f"Documents indexed: {added}")
        print(f"Time elapsed: {elapsed:.2f} seconds")
        stats = vectorstore.get_stats()
        print(f"\nStatistics:")
        print(f"  Total documents: {stats['total_documents']}")
        print(f"  Unique sources: {stats['unique_sources']}")
        print(f"  Chunk types: {stats['chunk_types']}")
    
    return vectorstore


def run_tests(vectorstore: VectorStore, verbose: bool = True):
    """Run test queries against the vectorstore.
    
    Args:
        vectorstore: VectorStore instance to test
        verbose: Print detailed results
    """
    if verbose:
        print(f"\n{'='*60}")
        print("Running Test Queries")
        print(f"{'='*60}")
    
    retriever = Retriever(vectorstore)
    
    test_queries = [
        # Basic queries
        ("How do I create a sketch?", None),
        ("Extrude a sketch to 3D", None),
        ("Select edges by length", None),
        
        # Code-focused queries
        ("Create a circle with a hole", {"filter_code": True}),
        ("Fillet edges example", {"filter_code": True}),
        
        # Concept queries
        ("What is BuildPart?", None),
        ("How to use selectors", None),
        
        # Advanced queries
        ("Create a box with filleted corners", None),
        ("How to make assemblies", None),
        
        # Specific file queries
        ("BuildSketch context manager", {"filter_file": "build_sketch.rst"}),
    ]
    
    results_summary = []
    
    for query, options in test_queries:
        if verbose:
            print(f"\n--- Query: '{query}' ---")
        
        start = time.time()
        
        if options and options.get("filter_code"):
            results = retriever.retrieve(query, top_k=3, filter_code=True)
        elif options and options.get("filter_file"):
            results = retriever.retrieve(query, top_k=3, filter_file=options["filter_file"])
        else:
            results = retriever.retrieve(query, top_k=3)
        
        elapsed = (time.time() - start) * 1000
        
        if verbose:
            print(f"Found {len(results)} results ({elapsed:.2f}ms)")
            
            for i, result in enumerate(results):
                print(f"\n  [{i+1}] Score: {result.score:.3f}")
                print(f"      Source: {result.source_file} > {result.section_title}")
                print(f"      Type: {result.chunk_type}")
                
                # Show content preview
                content_preview = result.content[:200].replace('\n', ' ')
                print(f"      Preview: {content_preview}...")
                
                # Show code if available
                if result.chunk_type == 'code' and '```' in result.content:
                    code_start = result.content.find('```')
                    code_preview = result.content[code_start:code_start+150]
                    print(f"      Code: {code_preview}...")
        
        results_summary.append({
            'query': query,
            'results_count': len(results),
            'top_score': results[0].score if results else 0,
            'time_ms': elapsed
        })
    
    # Summary
    if verbose:
        print(f"\n{'='*60}")
        print("Test Summary")
        print(f"{'='*60}")
        print(f"Queries run: {len(test_queries)}")
        avg_time = sum(r['time_ms'] for r in results_summary) / len(results_summary)
        print(f"Average query time: {avg_time:.2f}ms")
        avg_score = sum(r['top_score'] for r in results_summary) / len(results_summary)
        print(f"Average top result score: {avg_score:.3f}")
        
        # Check for low-score results
        low_scores = [r for r in results_summary if r['top_score'] < 0.5]
        if low_scores:
            print(f"\n⚠️  {len(low_scores)} queries had low relevance scores:")
            for r in low_scores:
                print(f"  - '{r['query']}' ({r['top_score']:.3f})")
        else:
            print(f"\n✅ All queries returned highly relevant results")


def main():
    parser = argparse.ArgumentParser(
        description="Build vectorstore from build123d documentation"
    )
    parser.add_argument(
        "--docs-path",
        type=Path,
        default=Path("/a0/usr/projects/semishape/data/docs"),
        help="Path to documentation directory"
    )
    parser.add_argument(
        "--vectorstore-path",
        type=Path,
        default=Path("/a0/usr/projects/semishape/data/vectorstore"),
        help="Path to store ChromaDB"
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="build123d_docs",
        help="Collection name"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="all-MiniLM-L6-v2",
        help="Embedding model name"
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild vectorstore from scratch"
    )
    parser.add_argument(
        "--test-only",
        action="store_true",
        help="Only run tests, don't rebuild"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress detailed output"
    )
    
    args = parser.parse_args()
    
    # Validate paths
    if not args.docs_path.exists():
        print(f"ERROR: Documentation path does not exist: {args.docs_path}")
        sys.exit(1)
    
    # Build or load vectorstore
    if args.test_only:
        if verbose := not args.quiet:
            print(f"Loading existing vectorstore...")
        vectorstore = VectorStore(
            persist_dir=args.vectorstore_path,
            collection_name=args.collection
        )
    else:
        vectorstore = build_vectorstore(
            docs_path=args.docs_path,
            vectorstore_path=args.vectorstore_path,
            collection_name=args.collection,
            embedding_model=args.model,
            rebuild=args.rebuild,
            verbose=not args.quiet
        )
    
    # Run tests
    run_tests(vectorstore, verbose=not args.quiet)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())