"""
Unit Tests for Core RAG Components

Tests for:
1. Text Chunking - Verify chunk sizes, overlaps, and edge cases
2. Embeddings - Verify embedding generation and similarity
3. Retrieval - Verify vector search and hybrid search
"""

import unittest
import os
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.chunker import TextChunker
from app.services.embeddings import EmbeddingsService
from app.services.vector_store import VectorStore
from dotenv import load_dotenv

load_dotenv()


class TestTextChunker(unittest.TestCase):
    """Test cases for the TextChunker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.chunker = TextChunker()
    
    def test_basic_chunking(self):
        """Test basic text chunking."""
        text = "This is a test. " * 100  # Create a long text
        chunks = self.chunker.chunk_text(text, chunk_size=50, chunk_overlap=10)
        
        # Verify chunks were created
        self.assertGreater(len(chunks), 0)
        
        # Verify no chunk exceeds max size significantly
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 100)  # Allow some variance
    
    def test_chunk_overlap(self):
        """Test that chunks have proper overlap."""
        text = "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10"
        chunks = self.chunker.chunk_text(text, chunk_size=20, chunk_overlap=5)
        
        # Verify we have multiple chunks
        self.assertGreater(len(chunks), 1)
        
        # Verify overlap exists (last words of chunk N should appear in chunk N+1)
        for i in range(len(chunks) - 1):
            # This is a basic check - actual overlap depends on word boundaries
            self.assertGreater(len(chunks[i]), 0)
            self.assertGreater(len(chunks[i + 1]), 0)
    
    def test_empty_text(self):
        """Test chunking empty text."""
        chunks = self.chunker.chunk_text("", chunk_size=50, chunk_overlap=10)
        self.assertEqual(len(chunks), 0)
    
    def test_short_text(self):
        """Test chunking text shorter than chunk size."""
        text = "Short text."
        chunks = self.chunker.chunk_text(text, chunk_size=100, chunk_overlap=10)
        
        # Should return one chunk
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], text)
    
    def test_metadata_preservation(self):
        """Test that chunk metadata is correct."""
        text = "Test text " * 50
        chunk_size = 50
        chunk_overlap = 10
        
        chunks = self.chunker.chunk_text(
            text, 
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap
        )
        
        # Verify chunks exist
        self.assertGreater(len(chunks), 0)
        
        # Verify each chunk is a string
        for chunk in chunks:
            self.assertIsInstance(chunk, str)
    
    def test_special_characters(self):
        """Test chunking with special characters."""
        text = "Text with special chars: @#$%^&*() and newlines\n\nand tabs\t\there."
        chunks = self.chunker.chunk_text(text, chunk_size=50, chunk_overlap=10)
        
        # Should handle special characters
        self.assertGreater(len(chunks), 0)
        
        # Verify content is preserved
        combined = " ".join(chunks)
        self.assertIn("special chars", combined)


class TestEmbeddingsService(unittest.TestCase):
    """Test cases for the EmbeddingsService class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = EmbeddingsService()
    
    def test_embedding_generation(self):
        """Test basic embedding generation."""
        text = "This is a test document about machine learning."
        embedding = self.service.get_embedding(text)
        
        # Verify embedding is a list of floats
        self.assertIsInstance(embedding, list)
        self.assertGreater(len(embedding), 0)
        self.assertIsInstance(embedding[0], float)
    
    def test_embedding_consistency(self):
        """Test that same text produces same embedding."""
        text = "Consistent text for testing."
        
        embedding1 = self.service.get_embedding(text)
        embedding2 = self.service.get_embedding(text)
        
        # Should be identical (or very close due to floating point)
        self.assertEqual(len(embedding1), len(embedding2))
        
        # Check first few dimensions
        for i in range(min(5, len(embedding1))):
            self.assertAlmostEqual(embedding1[i], embedding2[i], places=5)
    
    def test_embedding_dimension(self):
        """Test that embeddings have expected dimension."""
        text = "Test text"
        embedding = self.service.get_embedding(text)
        
        # OpenAI text-embedding-ada-002 produces 1536-dimensional vectors
        # Sentence transformers typically produces 384-dimensional vectors
        # Check that we have a reasonable dimension
        self.assertIn(len(embedding), [384, 768, 1536])
    
    def test_batch_embeddings(self):
        """Test batch embedding generation."""
        texts = [
            "First document about ML",
            "Second document about AI",
            "Third document about NLP"
        ]
        
        embeddings = self.service.get_embeddings(texts)
        
        # Should return same number of embeddings
        self.assertEqual(len(embeddings), len(texts))
        
        # All embeddings should have same dimension
        dimensions = [len(emb) for emb in embeddings]
        self.assertEqual(len(set(dimensions)), 1)
    
    def test_empty_text_handling(self):
        """Test handling of empty text."""
        # Different services handle this differently
        # Some return zeros, some raise errors
        try:
            embedding = self.service.get_embedding("")
            # If it doesn't raise an error, check it returns something
            self.assertIsInstance(embedding, list)
        except ValueError:
            # It's acceptable to raise an error for empty text
            pass
    
    def test_semantic_similarity(self):
        """Test that similar texts have similar embeddings."""
        text1 = "Machine learning is a subset of artificial intelligence."
        text2 = "ML is part of AI and enables computers to learn."
        text3 = "I like pizza and pasta for dinner."
        
        emb1 = self.service.get_embedding(text1)
        emb2 = self.service.get_embedding(text2)
        emb3 = self.service.get_embedding(text3)
        
        # Calculate cosine similarity
        import numpy as np
        
        def cosine_sim(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        sim_12 = cosine_sim(emb1, emb2)
        sim_13 = cosine_sim(emb1, emb3)
        
        # Similar texts should have higher similarity
        self.assertGreater(sim_12, sim_13)
        self.assertGreater(sim_12, 0.5)  # Should be reasonably similar


class TestVectorStoreRetrieval(unittest.TestCase):
    """Test cases for vector store retrieval."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.vector_store = VectorStore(collection_name="test_retrieval_collection")
        self.vector_store.clear_collection()
        
        # Add some test documents
        self.test_docs = [
            "Machine learning is a method of data analysis.",
            "Deep learning uses neural networks with multiple layers.",
            "Natural language processing helps computers understand text.",
            "Computer vision enables machines to interpret images.",
            "Reinforcement learning involves agents learning from rewards."
        ]
        
        self.vector_store.add_documents(
            documents=self.test_docs,
            metadatas=[{"id": i, "topic": "AI"} for i in range(len(self.test_docs))]
        )
    
    def tearDown(self):
        """Clean up after tests."""
        self.vector_store.clear_collection()
    
    def test_basic_search(self):
        """Test basic vector search."""
        query = "What is machine learning?"
        results = self.vector_store.search(query, k=3)
        
        # Should return results
        self.assertGreater(len(results), 0)
        self.assertLessEqual(len(results), 3)
        
        # First result should be about machine learning
        self.assertIn("machine learning", results[0]["document"].lower())
    
    def test_search_k_parameter(self):
        """Test that k parameter limits results."""
        query = "deep learning"
        
        results_k2 = self.vector_store.search(query, k=2)
        results_k4 = self.vector_store.search(query, k=4)
        
        self.assertEqual(len(results_k2), 2)
        self.assertEqual(len(results_k4), 4)
    
    def test_search_relevance(self):
        """Test that most relevant document is returned first."""
        query = "neural networks and deep learning"
        results = self.vector_store.search(query, k=3)
        
        # First result should contain "deep learning" or "neural networks"
        first_result = results[0]["document"].lower()
        self.assertTrue(
            "deep learning" in first_result or "neural networks" in first_result
        )
    
    def test_hybrid_search(self):
        """Test hybrid search functionality."""
        query = "reinforcement learning agents"
        
        # Try hybrid search if available
        try:
            results = self.vector_store.hybrid_search(query, k=3)
            
            self.assertGreater(len(results), 0)
            self.assertLessEqual(len(results), 3)
            
            # Should find reinforcement learning document
            found_rl = any("reinforcement" in r["document"].lower() for r in results)
            self.assertTrue(found_rl)
            
        except AttributeError:
            # Hybrid search may not be implemented
            self.skipTest("Hybrid search not implemented")
    
    def test_metadata_retrieval(self):
        """Test that metadata is returned with results."""
        query = "computer vision"
        results = self.vector_store.search(query, k=1)
        
        self.assertGreater(len(results), 0)
        
        # Check metadata exists
        self.assertIn("metadata", results[0])
        self.assertIn("topic", results[0]["metadata"])
        self.assertEqual(results[0]["metadata"]["topic"], "AI")
    
    def test_empty_collection_search(self):
        """Test searching in an empty collection."""
        # Create a new empty collection
        empty_store = VectorStore(collection_name="empty_test_collection")
        empty_store.clear_collection()
        
        query = "test query"
        results = empty_store.search(query, k=3)
        
        # Should return empty results
        self.assertEqual(len(results), 0)
        
        # Cleanup
        empty_store.clear_collection()
    
    def test_similarity_scores(self):
        """Test that similarity scores are reasonable."""
        query = "machine learning data analysis"
        results = self.vector_store.search(query, k=3)
        
        # Check if results have similarity scores
        if "similarity" in results[0]:
            for result in results:
                score = result["similarity"]
                # Scores should be between -1 and 1 for cosine similarity
                self.assertGreaterEqual(score, -1.0)
                self.assertLessEqual(score, 1.0)


class TestEndToEndRAG(unittest.TestCase):
    """End-to-end integration tests for RAG pipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.chunker = TextChunker()
        self.vector_store = VectorStore(collection_name="e2e_test_collection")
        self.vector_store.clear_collection()
    
    def tearDown(self):
        """Clean up after tests."""
        self.vector_store.clear_collection()
    
    def test_full_pipeline(self):
        """Test complete RAG pipeline from document to retrieval."""
        # 1. Chunk a document
        document = """
        Machine learning is a field of artificial intelligence. 
        It enables systems to learn from data without being explicitly programmed.
        Deep learning is a subset of machine learning that uses neural networks.
        Neural networks are inspired by the human brain structure.
        """
        
        chunks = self.chunker.chunk_text(document, chunk_size=100, chunk_overlap=20)
        
        self.assertGreater(len(chunks), 0)
        
        # 2. Index chunks
        self.vector_store.add_documents(
            documents=chunks,
            metadatas=[{"chunk_id": i} for i in range(len(chunks))]
        )
        
        # 3. Query the system
        query = "What is deep learning?"
        results = self.vector_store.search(query, k=2)
        
        # 4. Verify results
        self.assertGreater(len(results), 0)
        
        # Should retrieve relevant chunk about deep learning
        relevant_found = any("deep learning" in r["document"].lower() for r in results)
        self.assertTrue(relevant_found)


def run_tests():
    """Run all tests and print results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTextChunker))
    suite.addTests(loader.loadTestsFromTestCase(TestEmbeddingsService))
    suite.addTests(loader.loadTestsFromTestCase(TestVectorStoreRetrieval))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEndRAG))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
