"""RAG Pipeline for SemiShape build123d documentation.

This package provides a complete Retrieval-Augmented Generation pipeline:
- RSTChunker: Parse and chunk reStructuredText documentation
- EmbeddingModel: Generate embeddings using sentence-transformers
- VectorStore: Persistent storage with ChromaDB
- Retriever: High-level retrieval interface with query augmentation

Usage:
    from src.rag import RSTChunker, VectorStore, Retriever
    
    # Chunk documents
    chunker = RSTChunker()
    chunks = chunker.parse_file('docs/build_sketch.rst')
    
    # Create vectorstore
    store = VectorStore(Path('data/vectorstore'))
    store.add_chunks([c.to_dict() for c in chunks])
    
    # Query
    retriever = Retriever(store)
    results = retriever.retrieve('How to create a sketch?')
"""

from .chunker import (
    RSTChunker,
    DocumentChunk,
    CodeBlock,
    chunk_directory
)

from .embeddings import (
    EmbeddingModel,
    create_embeddings
)

from .vectorstore import (
    VectorStore,
    create_vectorstore
)

from .retriever import (
    Retriever,
    RetrievalResult,
    ContextFormatter,
    create_retriever
)

__all__ = [
    # Chunker
    'RSTChunker',
    'DocumentChunk',
    'CodeBlock',
    'chunk_directory',
    
    # Embeddings
    'EmbeddingModel',
    'create_embeddings',
    
    # VectorStore
    'VectorStore',
    'create_vectorstore',
    
    # Retriever
    'Retriever',
    'RetrievalResult',
    'ContextFormatter',
    'create_retriever',
]

__version__ = '0.1.0'