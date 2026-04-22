"""
Embeddings Service
Provides text embedding capabilities using OpenAI or sentence-transformers.
"""

import os
from typing import List, Literal, Optional
from enum import Enum


class EmbeddingProvider(str, Enum):
    """Available embedding providers."""
    OPENAI = "openai"
    SENTENCE_TRANSFORMERS = "sentence-transformers"


class EmbeddingsService:
    """
    Service for generating text embeddings.
    
    Supports multiple embedding providers:
    - OpenAI: text-embedding-3-small (requires API key)
    - Sentence Transformers: all-MiniLM-L6-v2 (free, runs locally)
    """
    
    def __init__(
        self,
        provider: EmbeddingProvider = EmbeddingProvider.SENTENCE_TRANSFORMERS,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize the embeddings service.
        
        Args:
            provider: Embedding provider to use (openai or sentence-transformers)
            model_name: Optional model name override
            api_key: Optional API key (for OpenAI)
        """
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._client = None
        self._dimension = None
        
        # Initialize the appropriate provider
        if provider == EmbeddingProvider.OPENAI:
            self._init_openai(model_name or "text-embedding-3-small")
        else:
            self._init_sentence_transformers(model_name or "all-MiniLM-L6-v2")
    
    def _init_openai(self, model_name: str):
        """Initialize OpenAI embeddings."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "OpenAI is not installed. Install it with: pip install openai"
            )
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self._client = OpenAI(api_key=self.api_key)
        self.model_name = model_name
        
        # Set dimension based on model
        if "text-embedding-3-small" in model_name:
            self._dimension = 1536
        elif "text-embedding-3-large" in model_name:
            self._dimension = 3072
        elif "text-embedding-ada-002" in model_name:
            self._dimension = 1536
        else:
            self._dimension = 1536  # Default
    
    def _init_sentence_transformers(self, model_name: str):
        """Initialize sentence-transformers embeddings."""
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Install it with: pip install sentence-transformers"
            )
        
        print(f"Loading sentence-transformers model: {model_name}...")
        self._client = SentenceTransformer(model_name)
        self.model_name = model_name
        self._dimension = self._client.get_sentence_embedding_dimension()
        print(f"✓ Model loaded successfully (dimension: {self._dimension})")
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        if self.provider == EmbeddingProvider.OPENAI:
            return self._embed_openai([text])[0]
        else:
            return self._embed_sentence_transformers([text])[0]
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        # Filter out empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            raise ValueError("All texts are empty")
        
        if self.provider == EmbeddingProvider.OPENAI:
            return self._embed_openai(valid_texts)
        else:
            return self._embed_sentence_transformers(valid_texts)
    
    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI."""
        try:
            response = self._client.embeddings.create(
                model=self.model_name,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            raise RuntimeError(f"OpenAI embedding failed: {str(e)}")
    
    def _embed_sentence_transformers(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using sentence-transformers."""
        try:
            embeddings = self._client.encode(
                texts,
                show_progress_bar=len(texts) > 10,
                convert_to_numpy=True
            )
            return embeddings.tolist()
        except Exception as e:
            raise RuntimeError(f"Sentence-transformers embedding failed: {str(e)}")
    
    @property
    def dimension(self) -> int:
        """Get the embedding dimension."""
        return self._dimension
    
    def get_info(self) -> dict:
        """Get information about the embeddings service."""
        return {
            "provider": self.provider.value,
            "model_name": self.model_name,
            "dimension": self._dimension,
            "is_free": self.provider == EmbeddingProvider.SENTENCE_TRANSFORMERS
        }


# Convenience functions for quick usage
def create_embeddings_service(
    use_openai: bool = False,
    api_key: Optional[str] = None
) -> EmbeddingsService:
    """
    Create an embeddings service with smart defaults.
    
    Args:
        use_openai: If True, use OpenAI embeddings. Otherwise use sentence-transformers (free)
        api_key: Optional OpenAI API key
        
    Returns:
        Configured EmbeddingsService instance
    """
    if use_openai:
        return EmbeddingsService(
            provider=EmbeddingProvider.OPENAI,
            api_key=api_key
        )
    else:
        return EmbeddingsService(
            provider=EmbeddingProvider.SENTENCE_TRANSFORMERS
        )


def embed_text(text: str, use_openai: bool = False) -> List[float]:
    """
    Quick function to embed a single text.
    
    Args:
        text: Text to embed
        use_openai: If True, use OpenAI. Otherwise use sentence-transformers
        
    Returns:
        Embedding vector
    """
    service = create_embeddings_service(use_openai=use_openai)
    return service.embed_text(text)


def embed_texts(texts: List[str], use_openai: bool = False) -> List[List[float]]:
    """
    Quick function to embed multiple texts.
    
    Args:
        texts: List of texts to embed
        use_openai: If True, use OpenAI. Otherwise use sentence-transformers
        
    Returns:
        List of embedding vectors
    """
    service = create_embeddings_service(use_openai=use_openai)
    return service.embed_texts(texts)
