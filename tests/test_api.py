"""
API Test Examples
Demonstrates how to test the RAG API endpoints using curl and Python requests.
"""

import requests
import json
from pathlib import Path


# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"


def print_separator(title: str = ""):
    """Print a visual separator."""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)
    print()


def test_health_check():
    """Test the health check endpoint."""
    print_separator("Testing Health Check")
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200


def test_upload_document(file_path: str, collection_name: str = "documents"):
    """Test document upload endpoint."""
    print_separator(f"Testing Document Upload: {file_path}")
    
    if not Path(file_path).exists():
        print(f"ERROR: File not found: {file_path}")
        return None
    
    # Prepare the file upload
    with open(file_path, 'rb') as f:
        files = {'file': (Path(file_path).name, f, 'application/octet-stream')}
        data = {
            'collection_name': collection_name,
            'chunk_size': 500,
            'chunk_overlap': 50
        }
        
        response = requests.post(f"{API_BASE}/upload", files=files, data=data)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Response:")
        print(f"  Filename: {result['filename']}")
        print(f"  Chunks Created: {result['chunks_created']}")
        print(f"  Chunks Stored: {result['chunks_stored']}")
        print(f"  Collection: {result['collection_name']}")
        print(f"  Message: {result['message']}")
        return result
    else:
        print(f"Error: {response.text}")
        return None


def test_query(question: str, k: int = 4, collection_name: str = "documents"):
    """Test query endpoint."""
    print_separator(f"Testing Query: '{question}'")
    
    payload = {
        "question": question,
        "k": k,
        "collection_name": collection_name
    }
    
    response = requests.post(
        f"{API_BASE}/query",
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"\nAnswer:")
        print("-" * 80)
        print(result['answer'])
        print("-" * 80)
        
        print(f"\nMetadata:")
        print(f"  Model: {result['model']}")
        print(f"  Context Chunks Used: {result['context_used']}")
        
        if 'usage' in result and result['usage']:
            print(f"  Tokens: {result['usage']['total_tokens']} "
                  f"(prompt: {result['usage']['prompt_tokens']}, "
                  f"completion: {result['usage']['completion_tokens']})")
        
        print(f"\nSources ({len(result['sources'])}):")
        for i, source in enumerate(result['sources'], 1):
            print(f"\n  Source {i}:")
            print(f"    Similarity: {source['similarity_score']:.4f}")
            print(f"    Metadata: {source['metadata']}")
            print(f"    Text: {source['text'][:150]}...")
        
        return result
    else:
        print(f"Error: {response.text}")
        return None


def test_get_stats(collection_name: str = "documents"):
    """Test collection stats endpoint."""
    print_separator(f"Testing Collection Stats: {collection_name}")
    
    response = requests.get(f"{API_BASE}/collections/{collection_name}/stats")
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        stats = response.json()
        print(f"Collection Stats:")
        print(f"  Collection Name: {stats['collection_name']}")
        print(f"  Document Count: {stats['document_count']}")
        print(f"  Embeddings Provider: {stats['embeddings_info']['provider']}")
        print(f"  Embedding Dimension: {stats['embeddings_info']['dimension']}")
        return stats
    else:
        print(f"Error: {response.text}")
        return None


def run_full_test():
    """Run a complete end-to-end test."""
    print_separator("RAG API - Complete End-to-End Test")
    
    # Test 1: Health check
    if not test_health_check():
        print("ERROR: Health check failed. Is the server running?")
        return
    
    # Test 2: Upload document
    pdf_path = "data/test_files/sample_document.pdf"
    upload_result = test_upload_document(pdf_path)
    
    if not upload_result:
        print("ERROR: Document upload failed. Check the logs.")
        return
    
    # Test 3: Get collection stats
    test_get_stats()
    
    # Test 4: Query documents
    test_questions = [
        "What is natural language processing?",
        "What are the main applications of NLP?",
        "What challenges exist in NLP?",
        "Tell me about machine translation"
    ]
    
    for question in test_questions:
        test_query(question, k=3)
    
    print_separator("All Tests Completed!")


def generate_curl_examples():
    """Generate curl command examples."""
    print_separator("cURL Command Examples")
    
    print("1. Upload a document:")
    print("-" * 80)
    print("""curl -X POST "http://localhost:8000/api/v1/upload" \\
  -F "file=@data/test_files/sample_document.pdf" \\
  -F "collection_name=documents" \\
  -F "chunk_size=500" \\
  -F "chunk_overlap=50"
""")
    
    print("\n2. Query documents:")
    print("-" * 80)
    print("""curl -X POST "http://localhost:8000/api/v1/query" \\
  -H "Content-Type: application/json" \\
  -d '{
    "question": "What is natural language processing?",
    "k": 4,
    "collection_name": "documents"
  }'
""")
    
    print("\n3. Get collection statistics:")
    print("-" * 80)
    print("""curl -X GET "http://localhost:8000/api/v1/collections/documents/stats"
""")
    
    print("\n4. Clear collection:")
    print("-" * 80)
    print("""curl -X DELETE "http://localhost:8000/api/v1/collections/documents"
""")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "curl":
            generate_curl_examples()
        elif sys.argv[1] == "upload":
            file_path = sys.argv[2] if len(sys.argv) > 2 else "data/test_files/sample_document.pdf"
            test_upload_document(file_path)
        elif sys.argv[1] == "query":
            question = sys.argv[2] if len(sys.argv) > 2 else "What is natural language processing?"
            test_query(question)
        elif sys.argv[1] == "stats":
            test_get_stats()
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Usage: py test_api.py [curl|upload|query|stats]")
    else:
        # Run full test suite
        run_full_test()
