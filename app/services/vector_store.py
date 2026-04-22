"""
Vector Store Service
Manages document storage and retrieval using ChromaDB vector database.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import chromadb
from chromadb.config import Settings

from .embeddings import EmbeddingsService, EmbeddingProvider


class VectorStore:
    """
    Vector store using ChromaDB for persistent document storage and semantic search.
    """
    
    def __init__(
        self,
        collection_name: str = "documents",
        persist_directory: str = "./chroma_db",
        embeddings_service: Optional[EmbeddingsService] = None,
        use_openai_embeddings: bool = False
    ):
        """
        Initialize the vector store.
        
        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist the database
            embeddings_service: Optional custom embeddings service
            use_openai_embeddings: If True and no service provided, use OpenAI embeddings
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # Create persist directory if it doesn't exist
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize embeddings service if not provided
        if embeddings_service is None:
            provider = EmbeddingProvider.OPENAI if use_openai_embeddings else EmbeddingProvider.SENTENCE_TRANSFORMERS
            self.embeddings_service = EmbeddingsService(provider=provider)
        else:
            self.embeddings_service = embeddings_service
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        
        print(f"✓ Vector store initialized")
        print(f"  Collection: {collection_name}")
        print(f"  Persist directory: {persist_directory}")
        print(f"  Embeddings: {self.embeddings_service.get_info()['provider']} ({self.embeddings_service.dimension}d)")
        print(f"  Document count: {self.collection.count()}")
    
    def add_documents(
        self,
        chunks: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Add documents (text chunks) to the vector store.
        
        Args:
            chunks: List of text chunks to add
            metadata: Optional list of metadata dicts (one per chunk)
            ids: Optional list of IDs (auto-generated if not provided)
            
        Returns:
            Dictionary with operation results
        """
        if not chunks:
            raise ValueError("Chunks list cannot be empty")
        
        # Generate IDs if not provided
        if ids is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ids = [f"doc_{timestamp}_{i}" for i in range(len(chunks))]
        
        # Ensure metadata exists for all chunks
        if metadata is None:
            metadata = [{"chunk_index": i} for i in range(len(chunks))]
        elif len(metadata) != len(chunks):
            raise ValueError("Metadata list must match chunks list length")
        
        # Add timestamps to metadata
        for meta in metadata:
            if "added_at" not in meta:
                meta["added_at"] = datetime.now().isoformat()
        
        # Generate embeddings
        print(f"Generating embeddings for {len(chunks)} chunks...")
        embeddings = self.embeddings_service.embed_texts(chunks)
        
        # Add to ChromaDB
        print(f"Adding {len(chunks)} documents to vector store...")
        self.collection.add(
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadata,
            ids=ids
        )
        
        result = {
            "added_count": len(chunks),
            "ids": ids,
            "total_documents": self.collection.count()
        }
        
        print(f"✓ Added {len(chunks)} documents (total: {result['total_documents']})")
        return result
    
    def search(
        self,
        query: str,
        k: int = 4,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using semantic search.
        
        Args:
            query: Search query text
            k: Number of results to return
            filter_metadata: Optional metadata filter
            
        Returns:
            List of search results with documents, metadata, and scores
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        # Generate query embedding
        print(f"Searching for: '{query[:100]}{'...' if len(query) > 100 else ''}'")
        query_embedding = self.embeddings_service.embed_text(query)
        
        # Search ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, self.collection.count()),
            where=filter_metadata,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = []
        if results["documents"] and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                # Convert distance to similarity score (cosine similarity)
                # ChromaDB returns squared L2 distance for cosine space
                distance = results["distances"][0][i]
                similarity_score = 1 - (distance / 2)  # Convert to 0-1 range
                
                formatted_results.append({
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity_score": similarity_score,
                    "distance": distance,
                    "rank": i + 1
                })
        
        print(f"✓ Found {len(formatted_results)} results")
        return formatted_results
    
    def delete_documents(self, ids: List[str]) -> Dict[str, Any]:
        """
        Delete documents by IDs.
        
        Args:
            ids: List of document IDs to delete
            
        Returns:
            Dictionary with operation results
        """
        self.collection.delete(ids=ids)
        
        result = {
            "deleted_count": len(ids),
            "total_documents": self.collection.count()
        }
        
        print(f"✓ Deleted {len(ids)} documents (remaining: {result['total_documents']})")
        return result
    
    def clear_collection(self) -> Dict[str, Any]:
        """
        Clear all documents from the collection.
        
        Returns:
            Dictionary with operation results
        """
        count_before = self.collection.count()
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        result = {
            "deleted_count": count_before,
            "total_documents": 0
        }
        
        print(f"✓ Cleared collection (deleted {count_before} documents)")
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory,
            "document_count": self.collection.count(),
            "embeddings_info": self.embeddings_service.get_info()
        }
    
    def get_all_documents(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all documents from the collection.
        
        Args:
            limit: Optional limit on number of documents to retrieve
            
        Returns:
            List of documents with metadata
        """
        count = self.collection.count()
        if count == 0:
            return []
        
        n_results = min(limit, count) if limit else count
        
        results = self.collection.get(
            limit=n_results,
            include=["documents", "metadatas"]
        )
        
        documents = []
        for i in range(len(results["documents"])):
            documents.append({
                "id": results["ids"][i],
                "document": results["documents"][i],
                "metadata": results["metadatas"][i]
            })
        
        return documents


# Convenience functions
def create_vector_store(
    collection_name: str = "documents",
    persist_directory: str = "./chroma_db",
    use_openai: bool = False
) -> VectorStore:
    """
    Create a vector store with default settings.
    
    Args:
        collection_name: Name of the collection
        persist_directory: Directory to persist data
        use_openai: If True, use OpenAI embeddings
        
    Returns:
        Configured VectorStore instance
    """
    return VectorStore(
        collection_name=collection_name,
        persist_directory=persist_directory,
        use_openai_embeddings=use_openai
    )
