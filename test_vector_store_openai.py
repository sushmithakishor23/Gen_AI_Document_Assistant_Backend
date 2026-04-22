"""
Alternative vector store test using OpenAI embeddings.
Use this if sentence-transformers/torch has DLL issues on Windows.
"""

import sys
import os
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.document_loader import load_document
from app.services.chunker import chunk_text
from app.services.embeddings import EmbeddingsService, EmbeddingProvider
from app.services.vector_store import VectorStore


def print_separator(title: str = ""):
    """Print a visual separator."""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)
    print()


def check_openai_key():
    """Check if OpenAI API key is available."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set")
        print("\nTo set it:")
        print("  Windows (PowerShell):  $env:OPENAI_API_KEY='your-key-here'")
        print("  Windows (CMD):         set OPENAI_API_KEY=your-key-here")
        print("  Linux/Mac:             export OPENAI_API_KEY='your-key-here'")
        print("\nOr create a .env file with:")
        print("  OPENAI_API_KEY=your-key-here")
        return False
    return True


def test_openai_embeddings():
    """Test OpenAI embeddings."""
    print_separator("Testing OpenAI Embeddings")
    
    if not check_openai_key():
        return None
    
    print("Creating OpenAI embeddings service...")
    embeddings_service = EmbeddingsService(
        provider=EmbeddingProvider.OPENAI,
        model_name="text-embedding-3-small"
    )
    
    info = embeddings_service.get_info()
    print(f"✓ Embeddings service initialized")
    print(f"  Provider: {info['provider']}")
    print(f"  Model: {info['model_name']}")
    print(f"  Dimension: {info['dimension']}")
    print()
    
    # Test single embedding
    print("Testing single text embedding...")
    text = "Natural language processing is fascinating"
    embedding = embeddings_service.embed_text(text)
    print(f"✓ Generated embedding for text: '{text}'")
    print(f"  Embedding dimension: {len(embedding)}")
    print(f"  First 5 values: {[round(v, 4) for v in embedding[:5]]}")
    print()
    
    return embeddings_service


def test_pdf_with_openai():
    """Test end-to-end with OpenAI embeddings."""
    print_separator("PDF Ingestion and Search with OpenAI Embeddings")
    
    if not check_openai_key():
        return
    
    pdf_path = "data/test_files/sample_document.pdf"
    
    if not Path(pdf_path).exists():
        print(f"ERROR: Sample PDF not found at {pdf_path}")
        print("Run create_sample_pdf.py first")
        return
    
    # Step 1: Load PDF
    print("Step 1: Loading PDF...")
    text = load_document(pdf_path)
    print(f"✓ Loaded PDF: {len(text)} characters")
    print()
    
    # Step 2: Chunk text
    print("Step 2: Chunking text...")
    chunks = chunk_text(text, chunk_size=500, chunk_overlap=50)
    print(f"✓ Created {len(chunks)} chunks")
    print()
    
    # Step 3: Create embeddings service
    print("Step 3: Creating OpenAI embeddings service...")
    embeddings_service = EmbeddingsService(
        provider=EmbeddingProvider.OPENAI,
        model_name="text-embedding-3-small"
    )
    print(f"✓ Embeddings service ready")
    print()
    
    # Step 4: Create vector store
    print("Step 4: Creating vector store...")
    vector_store = VectorStore(
        collection_name="pdf_openai",
        persist_directory="./chroma_db_openai",
        embeddings_service=embeddings_service
    )
    
    # Clear previous data
    if vector_store.collection.count() > 0:
        print("Clearing previous data...")
        vector_store.clear_collection()
    
    # Prepare metadata
    metadata = [
        {
            "source": pdf_path,
            "chunk_index": i,
            "total_chunks": len(chunks)
        }
        for i in range(len(chunks))
    ]
    
    # Add documents
    print(f"\nAdding {len(chunks)} chunks to vector store...")
    vector_store.add_documents(chunks, metadata=metadata)
    print()
    
    # Step 5: Search
    print_separator("Running Search Queries")
    
    test_queries = [
        "What is natural language processing?",
        "Tell me about machine translation",
        "What challenges exist in NLP?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: '{query}'")
        print('='*80)
        
        results = vector_store.search(query, k=3)
        
        for result in results:
            print(f"\n[Rank {result['rank']}] Similarity: {result['similarity_score']:.4f}")
            print(f"Chunk {result['metadata']['chunk_index'] + 1}/{result['metadata']['total_chunks']}")
            print("-" * 80)
            print(result['document'][:300] + "..." if len(result['document']) > 300 else result['document'])
            print("-" * 80)
    
    # Stats
    print_separator("Final Statistics")
    stats = vector_store.get_stats()
    print(f"✓ Vector store operational")
    print(f"  Collection: {stats['collection_name']}")
    print(f"  Documents: {stats['document_count']}")
    print(f"  Embeddings: {stats['embeddings_info']['provider']}")
    print(f"  Dimension: {stats['embeddings_info']['dimension']}")
    print()


def main():
    """Run tests with OpenAI embeddings."""
    print_separator("Vector Store Test - OpenAI Embeddings")
    print("This test uses OpenAI's text-embedding-3-small model")
    print("Make sure your OPENAI_API_KEY is set")
    print()
    
    try:
        # Test embeddings
        embeddings_service = test_openai_embeddings()
        
        if embeddings_service:
            # Test PDF ingestion
            test_pdf_with_openai()
            
            print_separator("Test Completed Successfully! ✓")
        
    except Exception as e:
        print(f"\n✗ Test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
