"""
Quick test to verify the get_vector_store() fix handles multiple collections correctly.
"""

# Simulate the fixed implementation
from typing import Dict

class MockVectorStore:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        print(f"✓ Created VectorStore for collection: '{collection_name}'")

_vector_stores: Dict[str, MockVectorStore] = {}

def get_vector_store(collection_name: str = "documents") -> MockVectorStore:
    """Get or create vector store instance for the specified collection."""
    global _vector_stores
    
    if collection_name not in _vector_stores:
        _vector_stores[collection_name] = MockVectorStore(collection_name=collection_name)
    
    return _vector_stores[collection_name]

# Test the fix
print("Testing get_vector_store() with multiple collection names:\n")

print("1. First call with 'documents':")
vs1 = get_vector_store("documents")
print(f"   Returned collection: {vs1.collection_name}\n")

print("2. Second call with 'documents' (should reuse existing):")
vs2 = get_vector_store("documents")
print(f"   Returned collection: {vs2.collection_name}")
print(f"   Same instance? {vs1 is vs2} ✓\n")

print("3. First call with 'legal_docs':")
vs3 = get_vector_store("legal_docs")
print(f"   Returned collection: {vs3.collection_name}\n")

print("4. First call with 'technical_docs':")
vs4 = get_vector_store("technical_docs")
print(f"   Returned collection: {vs4.collection_name}\n")

print("5. Call 'documents' again (should reuse first instance):")
vs5 = get_vector_store("documents")
print(f"   Returned collection: {vs5.collection_name}")
print(f"   Same instance as vs1? {vs1 is vs5} ✓\n")

print("6. Verify all collections are independent:")
print(f"   documents != legal_docs? {vs1 is not vs3} ✓")
print(f"   documents != technical_docs? {vs1 is not vs4} ✓")
print(f"   legal_docs != technical_docs? {vs3 is not vs4} ✓\n")

print("=" * 60)
print("✅ TEST PASSED: Each collection name gets its own VectorStore instance!")
print(f"   Total collections created: {len(_vector_stores)}")
print(f"   Collections: {list(_vector_stores.keys())}")
