"""
Test script for vector store and embeddings service.
Tests document ingestion, vector storage, and semantic search.
"""

import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.document_loader import load_document
from app.services.chunker import chunk_text
from app.services.vector_store import VectorStore


def print_separator(title: str = ""):
    """Print a visual separator."""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)
    print()


def test_embeddings_service():
    """Test the embeddings service independently."""
    print_separator("Testing Embeddings Service")
    
    from app.services.embeddings import create_embeddings_service
    
    # Test with sentence-transformers (free)
    print("Creating embeddings service (sentence-transformers)...")
    embeddings_service = create_embeddings_service(use_openai=False)
    
    info = embeddings_service.get_info()
    print(f"✓ Embeddings service initialized")
    print(f"  Provider: {info['provider']}")
    print(f"  Model: {info['model_name']}")
    print(f"  Dimension: {info['dimension']}")
    print(f"  Free: {info['is_free']}")
    print()
    
    # Test single embedding
    print("Testing single text embedding...")
    text = "Natural language processing is fascinating"
    embedding = embeddings_service.embed_text(text)
    print(f"✓ Generated embedding for text: '{text}'")
    print(f"  Embedding dimension: {len(embedding)}")
    print(f"  First 5 values: {embedding[:5]}")
    print()
    
    # Test batch embeddings
    print("Testing batch embeddings...")
    texts = [
        "Machine learning is a subset of AI",
        "Deep learning uses neural networks",
        "NLP helps computers understand language"
    ]
    embeddings = embeddings_service.embed_texts(texts)
    print(f"✓ Generated {len(embeddings)} embeddings")
    print(f"  Each embedding has {len(embeddings[0])} dimensions")
    print()
    
    return embeddings_service


def test_vector_store_basic():
    """Test basic vector store operations."""
    print_separator("Testing Vector Store - Basic Operations")
    
    # Create vector store (using sentence-transformers by default)
    print("Creating vector store...")
    vector_store = VectorStore(
        collection_name="test_collection",
        persist_directory="./chroma_db_test",
        use_openai_embeddings=False
    )
    print()
    
    # Clear any existing data
    if vector_store.collection.count() > 0:
        print("Clearing existing data...")
        vector_store.clear_collection()
        print()
    
    # Add sample documents
    print("Adding sample documents...")
    sample_chunks = [
        "Machine learning is a method of data analysis that automates analytical model building.",
        "Deep learning is a subset of machine learning that uses neural networks with multiple layers.",
        "Natural language processing enables computers to understand and process human language.",
        "Computer vision allows machines to interpret and understand visual information from the world.",
        "Reinforcement learning is about taking suitable action to maximize reward in a particular situation."
    ]
    
    metadata = [
        {"topic": "machine_learning", "source": "sample", "index": 0},
        {"topic": "deep_learning", "source": "sample", "index": 1},
        {"topic": "nlp", "source": "sample", "index": 2},
        {"topic": "computer_vision", "source": "sample", "index": 3},
        {"topic": "reinforcement_learning", "source": "sample", "index": 4}
    ]
    
    result = vector_store.add_documents(sample_chunks, metadata=metadata)
    print()
    
    # Test search
    print_separator("Testing Semantic Search")
    
    queries = [
        "What is neural network learning?",
        "How do computers understand text?",
        "Tell me about AI and automated analysis"
    ]
    
    for query in queries:
        print(f"\nQuery: '{query}'")
        print("-" * 80)
        
        results = vector_store.search(query, k=3)
        
        for result in results:
            print(f"\n[Rank {result['rank']}] Similarity: {result['similarity_score']:.4f}")
            print(f"Topic: {result['metadata'].get('topic', 'N/A')}")
            print(f"Text: {result['document'][:150]}...")
    
    print()
    
    # Get stats
    print_separator("Vector Store Statistics")
    stats = vector_store.get_stats()
    print(f"Collection: {stats['collection_name']}")
    print(f"Total documents: {stats['document_count']}")
    print(f"Embeddings provider: {stats['embeddings_info']['provider']}")
    print(f"Embedding dimension: {stats['embeddings_info']['dimension']}")
    
    return vector_store


def test_pdf_ingestion_and_search():
    """Test end-to-end: ingest PDF and run search queries."""
    print_separator("End-to-End Test: PDF Ingestion and Search")
    
    # Use the sample PDF we created earlier
    pdf_path = "data/test_files/sample_document.pdf"
    
    if not Path(pdf_path).exists():
        print(f"ERROR: Sample PDF not found at {pdf_path}")
        print("Run create_sample_pdf.py first to create a test PDF")
        return
    
    # Step 1: Load PDF
    print("Step 1: Loading PDF document...")
    text = load_document(pdf_path)
    print(f"✓ Loaded PDF: {len(text)} characters")
    print(f"Preview: {text[:200]}...")
    print()
    
    # Step 2: Chunk the text
    print("Step 2: Chunking text...")
    chunks = chunk_text(text, chunk_size=500, chunk_overlap=50)
    print(f"✓ Created {len(chunks)} chunks")
    print(f"Average chunk size: {sum(len(c) for c in chunks) / len(chunks):.1f} chars")
    print()
    
    # Step 3: Create vector store and add documents
    print("Step 3: Creating vector store and adding documents...")
    vector_store = VectorStore(
        collection_name="pdf_documents",
        persist_directory="./chroma_db",
        use_openai_embeddings=False
    )
    
    # Clear previous data (for testing)
    if vector_store.collection.count() > 0:
        print("Clearing previous data...")
        vector_store.clear_collection()
    
    # Prepare metadata for chunks
    metadata = [
        {
            "source": pdf_path,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "file_type": "pdf"
        }
        for i in range(len(chunks))
    ]
    
    # Add documents
    add_result = vector_store.add_documents(chunks, metadata=metadata)
    print()
    
    # Step 4: Run search queries
    print_separator("Step 4: Running Search Queries")
    
    test_queries = [
        "What is natural language processing?",
        "Tell me about machine learning applications",
        "What are the challenges in NLP?",
        "How do transformers work?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: '{query}'")
        print('='*80)
        
        results = vector_store.search(query, k=4)
        
        if not results:
            print("No results found")
            continue
        
        for result in results:
            print(f"\n[Rank {result['rank']}] Similarity Score: {result['similarity_score']:.4f}")
            print(f"Chunk {result['metadata']['chunk_index'] + 1}/{result['metadata']['total_chunks']}")
            print("-" * 80)
            print(result['document'])
            print("-" * 80)
        
        print()
    
    # Step 5: Show final statistics
    print_separator("Final Statistics")
    stats = vector_store.get_stats()
    print(f"✓ Vector store ready for use")
    print(f"  Collection: {stats['collection_name']}")
    print(f"  Total documents: {stats['document_count']}")
    print(f"  Storage location: {stats['persist_directory']}")
    print(f"  Embeddings: {stats['embeddings_info']['provider']} ({stats['embeddings_info']['dimension']}d)")
    print()
    
    return vector_store


def main():
    """Run all tests."""
    print_separator("Vector Store & Embeddings Test Suite")
    print("This test suite will:")
    print("1. Test embeddings service")
    print("2. Test basic vector store operations")
    print("3. Test PDF ingestion and semantic search")
    print()
    
    try:
        # Test 1: Embeddings service
        embeddings_service = test_embeddings_service()
        
        # Test 2: Basic vector store operations
        vector_store = test_vector_store_basic()
        
        # Test 3: PDF ingestion and search (end-to-end)
        pdf_vector_store = test_pdf_ingestion_and_search()
        
        # Summary
        print_separator("All Tests Completed Successfully! ✓")
        print("The vector store is now ready for use in your application.")
        print()
        print("Quick usage example:")
        print("-" * 80)
        print("  from app.services.vector_store import VectorStore")
        print("  from app.services.document_loader import load_document")
        print("  from app.services.chunker import chunk_text")
        print()
        print("  # Load and process document")
        print("  text = load_document('your_file.pdf')")
        print("  chunks = chunk_text(text)")
        print()
        print("  # Store in vector database")
        print("  store = VectorStore()")
        print("  store.add_documents(chunks)")
        print()
        print("  # Search")
        print("  results = store.search('your query', k=4)")
        print("-" * 80)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
