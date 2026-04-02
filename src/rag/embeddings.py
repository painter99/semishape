"""Embedding wrapper using sentence-transformers for RAG pipeline."""

from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import torch


class EmbeddingModel:
    """Wrapper for sentence-transformers embedding model.
    
    Provides efficient embedding generation with automatic GPU detection
    and batch processing for large document collections.
    """
    
    # Default model optimized for semantic similarity
    DEFAULT_MODEL = 'all-MiniLM-L6-v2'
    
    # Alternative models for different use cases
    MODELS = {
        'fast': 'all-MiniLM-L6-v2',           # Fast, good quality (384 dims)
        'balanced': 'all-mpnet-base-v2',      # Better quality, slower (768 dims)
        'multilingual': 'paraphrase-multilingual-MiniLM-L12-v2',  # 50+ languages
        'code': 'codellama-7b-hf',             # Code-focused (if available)
    }
    
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: Optional[str] = None,
        cache_dir: Optional[str] = None
    ):
        """Initialize the embedding model.
        
        Args:
            model_name: Name of sentence-transformers model to use
            device: Device to use ('cuda', 'cpu', 'mps', or None for auto)
            cache_dir: Directory to cache downloaded models
        """
        self.model_name = model_name
        
        # Auto-detect best available device
        if device is None:
            device = self._get_device()
        
        # Initialize model
        self.model = SentenceTransformer(
            model_name,
            device=device,
            cache_folder=cache_dir
        )
        
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        self.device = device
        
        print(f"Loaded embedding model '{model_name}' on {device}")
        print(f"Embedding dimension: {self.embedding_dim}")
    
    def _get_device(self) -> str:
        """Determine the best available device."""
        if torch.cuda.is_available():
            return 'cuda'
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return 'mps'  # Apple Silicon
        return 'cpu'
    
    def embed(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False,
        normalize: bool = True
    ) -> np.ndarray:
        """Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            batch_size: Number of texts to process at once
            show_progress: Show progress bar for large datasets
            normalize: Whether to L2-normalize embeddings
        
        Returns:           numpy array of shape (len(texts), embedding_dim)
        """
        if not texts:
            return np.array([])
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=normalize,
            convert_to_numpy=True
        )
        
        return embeddings
    
    def embed_single(self, text: str, normalize: bool = True) -> np.ndarray:
        """Generate embedding for a single text.
        
        Args:
            text: Text string to embed
            normalize: Whether to L2-normalize embedding
        
        Returns:
            numpy array of shape (embedding_dim,)
        """
        embedding = self.model.encode(
            text,
            normalize_embeddings=normalize,
            convert_to_numpy=True
        )
        return embedding
    
    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a search query.
        
        This method returns a list format suitable for ChromaDB.
        
        Args:
            query: Query string to embed
        
        Returns:
            List of floats representing the embedding
        """
        embedding = self.embed_single(query, normalize=True)
        return embedding.tolist()
    
    def embed_documents(
        self,
        documents: List[str],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> List[List[float]]:
        """Generate embeddings for multiple documents.
        
        This method returns a list format suitable for ChromaDB.
        
        Args:
            documents: List of document texts
            batch_size: Batch size for processing
            show_progress: Show progress bar
        
        Returns:
            List of embedding vectors (each as list of floats)
        """
        embeddings = self.embed(
            documents,
            batch_size=batch_size,
            show_progress=show_progress,
            normalize=True
        )
        return embeddings.tolist()
    
    def similarity(
        self,
        query_embedding: np.ndarray,
        document_embeddings: np.ndarray
    ) -> np.ndarray:
        """Compute cosine similarity between query and documents.
        
        Args:
            query_embedding: Query embedding vector
            document_embeddings: Matrix of document embeddings
        
        Returns:
            Array of similarity scores
        """
        # Normalize if not already normalized
        if not np.allclose(np.linalg.norm(query_embedding), 1.0):
            query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        # Compute cosine similarity (embeddings should be normalized)
        similarities = np.dot(document_embeddings, query_embedding)
        return similarities
    
    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        return {
            'model_name': self.model_name,
            'embedding_dim': self.embedding_dim,
            'device': self.device,
            'max_seq_length': self.model.max_seq_length,
        }


# Convenience function for quick embedding
def create_embeddings(
    texts: List[str],
    model_name: str = EmbeddingModel.DEFAULT_MODEL
) -> np.ndarray:
    """Create embeddings for texts with default settings.
    
    Args:
        texts: List of texts to embed
        model_name: Name of sentence-transformers model
    
    Returns:
        numpy array of embeddings
    """
    model = EmbeddingModel(model_name)
    return model.embed(texts)


if __name__ == '__main__':
    # Test the embedding model
    model = EmbeddingModel()
    print(f"\nModel info: {model.get_model_info()}")
    
    # Test embedding
    test_texts = [
        "BuildSketch is used to create 2D profiles",
        "The with statement creates the BuildPart context manager",
        "from build123d import Box, BuildPart",
    ]
    
    print("\nGenerating embeddings...")
    embeddings = model.embed(test_texts, show_progress=False)
    print(f"Embeddings shape: {embeddings.shape}")
    
    # Test similarity
    query = "How do I create a 2D sketch?"
    query_embedding = model.embed_single(query)
    
    similarities = model.similarity(query_embedding, embeddings)
    print(f"\nQuery: '{query}'")
    for i, sim in enumerate(similarities):
        print(f"  Similarity to text {i+1}: {sim:.4f}")
