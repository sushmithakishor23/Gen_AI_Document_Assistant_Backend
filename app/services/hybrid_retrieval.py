"""
Hybrid Retrieval Service
Combines vector search with BM25 keyword search and cross-encoder reranking
for superior retrieval quality.
"""

from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder
import numpy as np


class HybridRetriever:
    """
    Hybrid retrieval system combining:
    1. Dense vector search (semantic similarity)
    2. BM25 sparse keyword search (lexical matching)
    3. Cross-encoder reranking (fine-grained relevance scoring)
    """
    
    def __init__(
        self,
        reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        alpha: float = 0.5
    ):
        """
        Initialize the hybrid retriever.
        
        Args:
            reranker_model: Cross-encoder model for reranking
            alpha: Weight for combining vector and BM25 scores (0-1)
                   0 = pure BM25, 1 = pure vector, 0.5 = balanced
        """
        self.alpha = alpha
        self.reranker_model_name = reranker_model
        
        # Lazy load the cross-encoder (expensive to initialize)
        self._reranker = None
        self._bm25_index = None
        self._documents = []
        
        print(f"✓ Hybrid retriever initialized (alpha={alpha})")
    
    @property
    def reranker(self):
        """Lazy load cross-encoder model."""
        if self._reranker is None:
            print(f"Loading cross-encoder: {self.reranker_model_name}")
            self._reranker = CrossEncoder(self.reranker_model_name)
            print(f"✓ Cross-encoder loaded")
        return self._reranker
    
    def build_bm25_index(self, documents: List[str]):
        """
        Build BM25 index from documents.
        
        Args:
            documents: List of document texts to index
        """
        if not documents:
            return
        
        # Tokenize documents (simple whitespace tokenization)
        tokenized_docs = [doc.lower().split() for doc in documents]
        
        # Build BM25 index
        self._bm25_index = BM25Okapi(tokenized_docs)
        self._documents = documents
        
        print(f"✓ BM25 index built with {len(documents)} documents")
    
    def bm25_search(
        self,
        query: str,
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform BM25 keyword search.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of results with scores and document indices
        """
        if self._bm25_index is None:
            return []
        
        # Tokenize query
        tokenized_query = query.lower().split()
        
        # Get BM25 scores
        scores = self._bm25_index.get_scores(tokenized_query)
        
        # Get top k indices
        top_k_indices = np.argsort(scores)[::-1][:k]
        
        # Format results
        results = []
        for idx in top_k_indices:
            if scores[idx] > 0:  # Only include non-zero scores
                results.append({
                    "index": int(idx),
                    "bm25_score": float(scores[idx]),
                    "document": self._documents[idx]
                })
        
        return results
    
    def hybrid_search(
        self,
        query: str,
        vector_results: List[Dict[str, Any]],
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Combine vector search with BM25 search using weighted fusion.
        
        Args:
            query: Search query
            vector_results: Results from vector search with similarity scores
            k: Number of results to return
            
        Returns:
            Combined and reranked results
        """
        # Build BM25 index from vector results if needed
        documents = [r.get('document', r.get('text', '')) for r in vector_results]
        self.build_bm25_index(documents)
        
        # Get BM25 results
        bm25_results = self.bm25_search(query, k=len(vector_results))
        
        # Normalize scores to 0-1 range
        vector_scores = {}
        if vector_results:
            max_vector_score = max(r.get('similarity_score', 0) for r in vector_results)
            min_vector_score = min(r.get('similarity_score', 0) for r in vector_results)
            score_range = max_vector_score - min_vector_score
            
            for i, r in enumerate(vector_results):
                if score_range > 0:
                    normalized = (r.get('similarity_score', 0) - min_vector_score) / score_range
                else:
                    normalized = 1.0
                vector_scores[i] = normalized
        
        bm25_scores = {}
        if bm25_results:
            max_bm25 = max(r['bm25_score'] for r in bm25_results)
            if max_bm25 > 0:
                for r in bm25_results:
                    bm25_scores[r['index']] = r['bm25_score'] / max_bm25
        
        # Combine scores using weighted fusion
        combined_results = []
        for i, vector_result in enumerate(vector_results):
            vector_score = vector_scores.get(i, 0)
            bm25_score = bm25_scores.get(i, 0)
            
            # Hybrid score: weighted combination
            hybrid_score = (
                self.alpha * vector_score +
                (1 - self.alpha) * bm25_score
            )
            
            combined_results.append({
                **vector_result,
                'vector_score': float(vector_score),
                'bm25_score': float(bm25_score),
                'hybrid_score': float(hybrid_score),
                'index': i
            })
        
        # Sort by hybrid score
        combined_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
        
        return combined_results[:k]
    
    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Rerank results using cross-encoder for fine-grained relevance.
        
        Args:
            query: Search query
            results: Results to rerank
            top_k: Number of top results to return after reranking
            
        Returns:
            Reranked results with cross-encoder scores
        """
        if not results:
            return []
        
        # Prepare query-document pairs for cross-encoder
        pairs = [
            [query, r.get('document', r.get('text', ''))]
            for r in results
        ]
        
        # Get cross-encoder scores
        print(f"Reranking {len(pairs)} results with cross-encoder...")
        ce_scores = self.reranker.predict(pairs)
        
        # Add scores to results
        reranked_results = []
        for i, (result, ce_score) in enumerate(zip(results, ce_scores)):
            reranked_results.append({
                **result,
                'cross_encoder_score': float(ce_score),
                'final_rank': i + 1
            })
        
        # Sort by cross-encoder score
        reranked_results.sort(key=lambda x: x['cross_encoder_score'], reverse=True)
        
        # Update final ranks
        for i, result in enumerate(reranked_results[:top_k]):
            result['final_rank'] = i + 1
        
        print(f"✓ Reranked to top {top_k} results")
        return reranked_results[:top_k]
    
    def retrieve(
        self,
        query: str,
        vector_results: List[Dict[str, Any]],
        initial_k: int = 10,
        final_k: int = 4,
        use_reranking: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Full hybrid retrieval pipeline:
        1. Combine vector + BM25 search
        2. Rerank with cross-encoder
        
        Args:
            query: Search query
            vector_results: Results from vector search
            initial_k: Number of results after hybrid fusion
            final_k: Final number of results after reranking
            use_reranking: Whether to apply cross-encoder reranking
            
        Returns:
            Final reranked results
        """
        # Step 1: Hybrid search (vector + BM25)
        hybrid_results = self.hybrid_search(query, vector_results, k=initial_k)
        
        print(f"Hybrid search: {len(hybrid_results)} results")
        
        # Step 2: Rerank with cross-encoder
        if use_reranking and hybrid_results:
            final_results = self.rerank(query, hybrid_results, top_k=final_k)
        else:
            final_results = hybrid_results[:final_k]
        
        return final_results
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about the hybrid retriever configuration."""
        return {
            "reranker_model": self.reranker_model_name,
            "alpha": self.alpha,
            "bm25_indexed": self._bm25_index is not None,
            "document_count": len(self._documents),
            "reranker_loaded": self._reranker is not None
        }


# Convenience function
def create_hybrid_retriever(alpha: float = 0.5) -> HybridRetriever:
    """
    Create a hybrid retriever with default settings.
    
    Args:
        alpha: Weight for combining vector and BM25 scores
        
    Returns:
        Configured HybridRetriever instance
    """
    return HybridRetriever(alpha=alpha)
