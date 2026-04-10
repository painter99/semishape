"""RAG pipeline for SemiShape build123d documentation search.

Provides retrieval-augmented generation components for searching
the bundled build123d documentation.

Components:
    RSTChunker: Parse and chunk reStructuredText documentation files
    EmbeddingModel: Generate embeddings using sentence-transformers
    VectorStore: Persistent ChromaDB vector storage
    Retriever: High-level retrieval interface with query augmentation

Usage:
    from src.rag import VectorStore, Retriever

    store = VectorStore(Path('data/vectorstore'))
    retriever = Retriever(store)
    results = retriever.retrieve('How to create a sketch?')
"""

from .chunker import (
    RSTChunker,
    DocumentChunk,
    CodeBlock,
    chunk_directory,
)

from .embeddings import (
    EmbeddingModel,
    create_embeddings,
)

from .vectorstore import (
    VectorStore,
    create_vectorstore,
)

from .retriever import (
    Retriever,
    RetrievalResult,
    ContextFormatter,
    create_retriever,
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
