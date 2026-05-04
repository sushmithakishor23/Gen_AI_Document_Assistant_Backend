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
        try:
            Path(persist_directory).mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise RuntimeError(
                f"Permission denied: Cannot create ChromaDB directory '{persist_directory}'. "
                f"Please check directory permissions or choose a different location."
            )
        except OSError as e:
            raise RuntimeError(
                f"Failed to create ChromaDB directory '{persist_directory}': {str(e)}. "
                f"Please check disk space and file system permissions."
            )
        
        # Initialize embeddings service if not provided
        if embeddings_service is None:
            provider = EmbeddingProvider.OPENAI if use_openai_embeddings else EmbeddingProvider.SENTENCE_TRANSFORMERS
            self.embeddings_service = EmbeddingsService(provider=provider)
        else:
            self.embeddings_service = embeddings_service
        
        # Initialize ChromaDB client with proper error handling
        try:
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        except PermissionError:
            raise RuntimeError(
                f"Permission denied: Cannot access ChromaDB directory '{persist_directory}'. "
                f"Please check directory permissions."
            )
        except OSError as e:
            if "disk" in str(e).lower() or "space" in str(e).lower():
                raise RuntimeError(
                    f"Disk space error: Cannot initialize ChromaDB at '{persist_directory}'. "
                    f"Please free up disk space and try again. Error: {str(e)}"
                )
            else:
                raise RuntimeError(
                    f"Failed to initialize ChromaDB at '{persist_directory}': {str(e)}. "
                    f"Please ensure the directory is writable and has sufficient disk space."
                )
        except Exception as e:
            raise RuntimeError(
                f"Unexpected error initializing ChromaDB client: {str(e)}. "
                f"This may be due to a corrupted database or incompatible ChromaDB version. "
                f"Try deleting '{persist_directory}' and restarting."
            )
        
        # Get or create collection with error handling
        try:
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )
        except ValueError as e:
            raise RuntimeError(
                f"Invalid collection name '{collection_name}': {str(e)}. "
                f"Collection names must contain only alphanumeric characters, hyphens, and underscores."
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to create/access collection '{collection_name}': {str(e)}. "
                f"The database may be corrupted. Try deleting '{persist_directory}' and restarting."
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
        
        # Add to ChromaDB with error handling
        print(f"Adding {len(chunks)} documents to vector store...")
        try:
            self.collection.add(
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadata,
                ids=ids
            )
        except ValueError as e:
            raise RuntimeError(
                f"Invalid data format for ChromaDB: {str(e)}. "
                f"Please check that IDs are unique and metadata is properly formatted."
            )
        except OSError as e:
            raise RuntimeError(
                f"Disk error while adding documents to ChromaDB: {str(e)}. "
                f"Please check disk space at '{self.persist_directory}'."
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to add documents to ChromaDB: {str(e)}. "
                f"The database may be corrupted or out of disk space."
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
        
        # Search ChromaDB with error handling
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(k, self.collection.count()),
                where=filter_metadata,
                include=["documents", "metadatas", "distances"]
            )
        except ValueError as e:
            raise RuntimeError(
                f"Invalid search parameters: {str(e)}. "
                f"Please check your metadata filter or search parameters."
            )
        except OSError as e:
            raise RuntimeError(
                f"Disk error while searching ChromaDB: {str(e)}. "
                f"The database at '{self.persist_directory}' may be corrupted or inaccessible."
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to search ChromaDB: {str(e)}. "
                f"The database may be corrupted. Try restarting the service."
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
    
    def hybrid_search(
        self,
        query: str,
        k: int = 4,
        initial_k: int = 10,
        use_reranking: bool = True,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining vector search, BM25, and cross-encoder reranking.
        
        This method provides superior retrieval quality by:
        1. Fetching more candidates with vector search (initial_k)
        2. Combining vector scores with BM25 keyword scores
        3. Reranking with cross-encoder for final top-k results
        
        Args:
            query: Search query text
            k: Final number of results to return
            initial_k: Number of candidates to fetch initially (before reranking)
            use_reranking: Whether to apply cross-encoder reranking
            filter_metadata: Optional metadata filter
            
        Returns:
            List of reranked search results with enhanced scores
        """
        from .hybrid_retrieval import create_hybrid_retriever
        
        # Step 1: Get initial candidates with vector search
        initial_results = self.search(
            query=query,
            k=max(initial_k, k),  # Fetch more for reranking
            filter_metadata=filter_metadata
        )
        
        if not initial_results:
            return []
        
        # Step 2: Apply hybrid retrieval (vector + BM25 + reranking)
        retriever = create_hybrid_retriever(alpha=0.5)  # Balanced weighting
        
        final_results = retriever.retrieve(
            query=query,
            vector_results=initial_results,
            initial_k=initial_k,
            final_k=k,
            use_reranking=use_reranking
        )
        
        return final_results
    
    def delete_documents(self, ids: List[str]) -> Dict[str, Any]:
        """
        Delete documents by IDs.
        
        Args:
            ids: List of document IDs to delete
            
        Returns:
            Dictionary with operation results
        """
        try:
            self.collection.delete(ids=ids)
        except ValueError as e:
            raise RuntimeError(
                f"Invalid document IDs: {str(e)}. "
                f"Please check that the IDs exist in the collection."
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to delete documents from ChromaDB: {str(e)}. "
                f"The database may be corrupted or locked."
            )
        
        result = {
            "deleted_count": len(ids),
            "total_documents": self.collection.count()
        }
        
        print(f"✓ Deleted {len(ids)} documents (remaining: {result['total_documents']})")
        return result
    
    def delete_documents_by_prefix(self, prefix: str) -> Dict[str, Any]:
        """
        Delete all documents with IDs starting with the specified prefix.
        Useful for deleting all chunks from a specific document.
        
        Args:
            prefix: ID prefix to match
            
        Returns:
            Dictionary with operation results
        """
        # Get all documents and filter by prefix
        try:
            all_docs = self.collection.get(include=["metadatas"])
            matching_ids = [doc_id for doc_id in all_docs["ids"] if doc_id.startswith(prefix)]
            
            if not matching_ids:
                return {
                    "deleted_count": 0,
                    "total_documents": self.collection.count()
                }
            
            # Delete matching documents
            self.collection.delete(ids=matching_ids)
            
        except Exception as e:
            raise RuntimeError(
                f"Failed to delete documents with prefix '{prefix}': {str(e)}. "
                f"The database may be corrupted or locked."
            )
        
        result = {
            "deleted_count": len(matching_ids),
            "total_documents": self.collection.count()
        }
        
        print(f"✓ Deleted {len(matching_ids)} documents with prefix '{prefix}' (remaining: {result['total_documents']})")
        return result
    
    def clear_collection(self) -> Dict[str, Any]:
        """
        Clear all documents from the collection.
        
        Returns:
            Dictionary with operation results
        """
        try:
            count_before = self.collection.count()
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        except PermissionError:
            raise RuntimeError(
                f"Permission denied: Cannot modify collection '{self.collection_name}'. "
                f"The database may be locked by another process."
            )
        except OSError as e:
            raise RuntimeError(
                f"Disk error while clearing collection: {str(e)}. "
                f"Check disk space at '{self.persist_directory}'."
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to clear collection '{self.collection_name}': {str(e)}. "
                f"The database may be corrupted. Try restarting the service."
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
