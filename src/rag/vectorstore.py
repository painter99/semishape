"""ChromaDB vectorstore wrapper for RAG pipeline.

Provides persistent storage and retrieval of document embeddings
with metadata filtering capabilities.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions


class VectorStore:
    """ChromaDB-based vector store for document retrieval.
    
    Features:
    - Persistent storage on disk
    - Metadata filtering (source file, section, chunk type)
    - Similarity search with relevance scores
    - Collection management
    """
    
    DEFAULT_COLLECTION = "build123d_docs"
    
    def __init__(
        self,
        persist_dir: Path,
        collection_name: str = DEFAULT_COLLECTION,
        embedding_model_name: str = "all-MiniLM-L6-v2"   ):
        """Initialize the vector store.
        
        Args:
            persist_dir: Directory to store ChromaDB data
            collection_name: Name of the collection to use
            embedding_model_name: Name of sentence-transformers model
        """
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model_name
        
        # Initialize ChromaDB client with persistent storage
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Create or get collection
        self.collection = self._get_or_create_collection()
        
        print(f"VectorStore initialized at {self.persist_dir}")
        print(f"Collection: {collection_name}, Documents: {self.count()}")
    
    def _get_or_create_collection(self):
        """Get existing collection or create new one."""
        embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.embedding_model_name
        )
        
        return self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=embedding_func,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> int:
        """Add documents to the vector store.
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dictionaries
            ids: List of unique document IDs
        
        Returns:
            Number of documents added
        """
        if not documents:
            return 0
        
        # Generate IDs if not provided
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in documents]
        
        # Create default metadata if not provided
        if metadatas is None:
            metadatas = [{} for _ in documents]
        
        # Ensure all metadata values are strings or numbers (ChromaDB requirement)
        clean_metadatas = []
        for meta in metadatas:
            clean_meta = {}
            for k, v in meta.items():
                if v is None:
                    clean_meta[k] = ""
                elif isinstance(v, (list, tuple)):
                    clean_meta[k] = ", ".join(str(x) for x in v)
                elif isinstance(v, dict):
                    clean_meta[k] = str(v)
                else:
                    clean_meta[k] = v
            clean_metadatas.append(clean_meta)
        
        self.collection.add(
            documents=documents,
            metadatas=clean_metadatas,
            ids=ids
        )
        
        return len(documents)
    
    def add_chunks(self, chunks: List[dict], batch_size: int = 100) -> int:
        """Add DocumentChunk objects to the store.
        
        Args:
            chunks: List of chunk dictionaries from RSTChunker
            batch_size: Number of chunks to add at once
        
        Returns:
            Number of chunks added
        """
        total_added = 0
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            documents = [c['content'] for c in batch]
            ids = [f"{c['source_file']}_{c['start_line']}_{i}" for i, c in enumerate(batch)]
            
            metadatas = [{
                'source_file': c['source_file'],
                'section_title': c['section_title'],
                'section_path': ", ".join(c['section_path']),
                'chunk_type': c['chunk_type'],
                'start_line': c['start_line'],
                'end_line': c['end_line'],
                'has_code': str(c.get('has_code', False)),
                'language': c.get('language', ''),
            } for c in batch]
            
            added = self.add_documents(documents, metadatas, ids)
            total_added += added
        
        return total_added
    
    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query the vector store for similar documents.
        
        Args:
            query_text: Query string
            n_results: Number of results to return
            where: Metadata filter (e.g., {"source_file": "build_sketch.rst"})
            where_document: Document content filter
        
        Returns:
            Dictionary with documents, metadatas, distances
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=["documents", "metadatas", "distances"]
        )
        
        return results
    
    def search_by_code(
        self,
        query: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search specifically for code examples.
        
        Args:
            query: Query string
            n_results: Number of results
        
        Returns:
            List of results with documents and metadata
        """
        return self.query(
            query,
            n_results=n_results,
            where={"chunk_type": "code"}
        )
    
    def search_by_file(
        self,
        query: str,
        source_file: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search within a specific source file.
        
        Args:
            query: Query string
            source_file: Source file name to filter by
            n_results: Number of results
        
        Returns:
            List of results
        """
        return self.query(
            query,
            n_results=n_results,
            where={"source_file": source_file}
        )
    
    def search_by_section(
        self,
        query: str,
        section_title: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search within a specific section.
        
        Args:
            query: Query string
            section_title: Section title to filter by
            n_results: Number of results
        
        Returns:
            List of results
        """
        return self.query(
            query,
            n_results=n_results,
            where={"section_title": section_title}
        )
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific document by ID.
        
        Args:
            doc_id: Document ID
        
        Returns:
            Document dict or None if not found
        """
        results = self.collection.get(
            ids=[doc_id],
            include=["documents", "metadatas"]
        )
        
        if results['documents']:
            return {
                'id': doc_id,
                'document': results['documents'][0],
                'metadata': results['metadatas'][0]
            }
        return None
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document by ID.
        
        Args:
            doc_id: Document ID to delete
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            self.collection.delete(ids=[doc_id])
            return True
        except Exception:
            return False
    
    def clear(self) -> None:
        """Clear all documents from the collection."""
        # Get all IDs
        all_items = self.collection.get(include=[])
        if all_items['ids']:
            self.collection.delete(ids=all_items['ids'])
        print(f"Cleared collection: {self.collection_name}")
    
    def count(self) -> int:
        """Get the number of documents in the collection."""
        return self.collection.count()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        count = self.count()
        
        # Get sample of metadata to show available sources
        sample = self.collection.get(
            limit=min(count, 100),
            include=["metadatas"]
        )
        
        sources = set()
        sections = set()
        chunk_types = {'code': 0, 'text': 0}
        
        for meta in (sample.get('metadatas') or []):
            if meta.get('source_file'):
                sources.add(meta['source_file'])
            if meta.get('section_title'):
                sections.add(meta['section_title'])
            if meta.get('chunk_type'):
                chunk_types[meta['chunk_type']] = chunk_types.get(meta['chunk_type'], 0) + 1
        
        return {
            'total_documents': count,
            'unique_sources': len(sources),
            'sources': sorted(list(sources))[:10],  # First 10
            'unique_sections': len(sections),
            'chunk_types': chunk_types,
            'persist_directory': str(self.persist_dir),
            'collection_name': self.collection_name,
            'embedding_model': self.embedding_model_name
        }
    
    def peek(self, n: int = 5) -> List[Dict[str, Any]]:
        """Preview a few documents from the store.
        
        Args:
            n: Number of documents to preview
        
        Returns:
            List of document dicts
        """
        results = self.collection.peek(limit=n)
        
        documents = []
        for i, doc in enumerate(results['documents']):
            documents.append({
                'id': results['ids'][i],
                'document': doc[:200] + '...' if len(doc) > 200 else doc,
                'metadata': results['metadatas'][i]
            })
        
        return documents


def create_vectorstore(
    persist_dir: Path,
    collection_name: str = VectorStore.DEFAULT_COLLECTION,
    embedding_model: str = "all-MiniLM-L6-v2"
) -> VectorStore:
    """Factory function to create a VectorStore."""
    return VectorStore(
        persist_dir=persist_dir,
        collection_name=collection_name,
        embedding_model_name=embedding_model
    )


if __name__ == '__main__':
    # Test vectorstore
    import tempfile
    
    # Create temporary test store
    with tempfile.TemporaryDirectory() as tmpdir:
        store = VectorStore(Path(tmpdir), "test_collection")
        
        # Test adding documents
        test_docs = [
            "BuildSketch creates 2D profiles for extrusion",
            "BuildPart is used to create 3D objects",
            "The with statement creates a context manager",
        ]
        test_metadatas = [
            {'source_file': 'test.rst', 'section_title': 'Introduction'},
            {'source_file': 'test.rst', 'section_title': 'BuildPart'},
            {'source_file': 'test.rst', 'section_title': 'Context Managers'},
        ]
        
        print("\nAdding test documents...")
        store.add_documents(test_docs, test_metadatas)
        print(f"Documents in store: {store.count()}")
        
        # Test query
        print("\nTesting query...")
        results = store.query("How do I create a sketch?", n_results=2)
        for i, doc in enumerate(results['documents'][0]):
            print(f"Result {i+1}: {doc[:100]}...")
            print(f"  Distance: {results['distances'][0][i]:.4f}")
        
        print("\nStats:", store.get_stats())
