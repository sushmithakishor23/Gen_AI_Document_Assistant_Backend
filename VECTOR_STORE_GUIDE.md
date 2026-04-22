# Vector Store and Embeddings System - Implementation Guide

## Overview
Built a complete vector storage and semantic search system using ChromaDB and embeddings (OpenAI or sentence-transformers).

## Components Created

### 1. **Embeddings Service** (`app/services/embeddings.py`)
Flexible embeddings service supporting multiple providers:

- **OpenAI** (`text-embedding-3-small`): Cloud-based, 1536 dimensions
- **Sentence-Transformers** (`all-MiniLM-L6-v2`): Local/free, 384 dimensions

```python
from app.services.embeddings import EmbeddingsService, EmbeddingProvider

# Option 1: OpenAI embeddings (requires API key)
embeddings = EmbeddingsService(
    provider=EmbeddingProvider.OPENAI,
    model_name="text-embedding-3-small"
)

# Option 2: Sentence-transformers (free, local)
embeddings = EmbeddingsService(
    provider=EmbeddingProvider.SENTENCE_TRANSFORMERS
)

# Generate embeddings
embedding = embeddings.embed_text("Your text here")
embeddings_batch = embeddings.embed_texts(["Text 1", "Text 2"])
```

### 2. **Vector Store Service** (`app/services/vector_store.py`)
ChromaDB-based persistent vector database with semantic search:

```python
from app.services.vector_store import VectorStore

# Create vector store
vector_store = VectorStore(
    collection_name="documents",
    persist_directory="./chroma_db",
    use_openai_embeddings=True  # or False for sentence-transformers
)

# Add documents
chunks = ["Document 1 text", "Document 2 text"]
metadata = [{"source": "file1.pdf"}, {"source": "file2.pdf"}]
vector_store.add_documents(chunks, metadata=metadata)

# Search
results = vector_store.search("your query", k=4)
for result in results:
    print(f"Score: {result['similarity_score']:.4f}")
    print(f"Text: {result['document']}")
    print(f"Metadata: {result['metadata']}")
```

**Features:**
- Persistent storage in `./chroma_db`
- Cosine similarity search
- Metadata filtering
- Automatic timestamp tracking
- Statistics and document management

### 3. **Updated Requirements**
Added to `requirements.txt`:
```
sentencesentence-transformers>=2.2.0
```

Existing dependencies:
- `chromadb>=0.4.22`
- `openai>=1.10.0`

## Complete Usage Example

### End-to-End: PDF to Searchable Vector Store

```python
from app.services.document_loader import load_document
from app.services.chunker import chunk_text
from app.services.vector_store import VectorStore

# 1. Load document
text = load_document("data/your_document.pdf")

# 2. Chunk into smaller pieces
chunks = chunk_text(text, chunk_size=500, chunk_overlap=50)

# 3. Create vector store (using OpenAI)
vector_store = VectorStore(
    collection_name="my_documents",
    persist_directory="./chroma_db",
    use_openai_embeddings=True
)

# 4. Add chunks with metadata
metadata = [
    {
        "source": "your_document.pdf",
        "chunk_index": i,
        "page": i // 2  # example
    }
    for i in range(len(chunks))
]
vector_store.add_documents(chunks, metadata=metadata)

# 5. Search with semantic similarity
results = vector_store.search(
    query="What are the key findings?",
    k=4
)

# 6. Process results
for result in results:
    print(f"\n[Rank {result['rank']}] Similarity: {result['similarity_score']:.4f}")
    print(f"Source: {result['metadata']['source']}")
    print(f"Text: {result['document']}")
```

## Test Scripts

### ⚠ Important: PyTorch/Windows Issue
Due to a PyTorch DLL issue on Windows with Python 3.14, use the OpenAI-based test:

### Recommended: OpenAI Test (Works on Windows)
```bash
# Set API key
$env:OPENAI_API_KEY='your-key-here'

# Run test
py test_vector_store_openai.py
```

### Alternative: Sentence-Transformers Test (Requires PyTorch Fix)
```bash
py test_vector_store.py
```

If you get a PyTorch DLL error, see `WINDOWS_PYTORCH_FIX.md` for solutions.

## Files Created

| File | Description |
|------|-------------|
| `app/services/embeddings.py` | Embeddings service (OpenAI + sentence-transformers) |
| `app/services/vector_store.py` | ChromaDB vector store with search |
| `test_vector_store.py` | Full test with sentence-transformers |
| `test_vector_store_openai.py` | Full test with OpenAI embeddings |
| `test_validation.py` | Quick validation of code structure |
| `WINDOWS_PYTORCH_FIX.md` | Troubleshooting guide for PyTorch issues |

## Vector Store API Reference

### VectorStore Class

#### `__init__(collection_name, persist_directory, embeddings_service, use_openai_embeddings)`
Initialize vector store.

#### `add_documents(chunks, metadata=None, ids=None)`
Add documents to the store.
- **Returns**: `{"added_count": int, "ids": list, "total_documents": int}`

#### `search(query, k=4, filter_metadata=None)`
Semantic search for similar documents.
- **Returns**: List of results with `document`, `metadata`, `similarity_score`, `distance`, `rank`

#### `delete_documents(ids)`
Delete documents by ID.

#### `clear_collection()`
Remove all documents.

#### `get_stats()`
Get collection statistics.

#### `get_all_documents(limit=None)`
Retrieve all stored documents.

## Embeddings API Reference

### EmbeddingsService Class

#### `__init__(provider, model_name=None, api_key=None)`
Initialize embeddings service.
- `provider`: `EmbeddingProvider.OPENAI` or `EmbeddingProvider.SENTENCE_TRANSFORMERS`
- `model_name`: Optional model override
- `api_key`: Optional API key for OpenAI

#### `embed_text(text)`
Generate embedding for single text.
- **Returns**: List[float] (embedding vector)

#### `embed_texts(texts)`
Generate embeddings for multiple texts.
- **Returns**: List[List[float]]

#### `dimension`
Get embedding dimension (property).

#### `get_info()`
Get service information.

## Storage Structure

```
./chroma_db/               # Default vector store location
  ├── chroma.sqlite3       # ChromaDB database
  └── [collection_id]/     # Collection data
```

## Performance Notes

### OpenAI Embeddings
- **Pros**: Excellent quality, easy setup, no local dependencies
- **Cons**: Requires API key, costs money (very cheap: ~$0.13 per 1M tokens)
- **Speed**: ~1000 texts per minute (rate limited)
- **Dimension**: 1536

### Sentence-Transformers
- **Pros**: Free, fast, private (local), no API needed
- **Cons**: Requires PyTorch (large install), GPU recommended for speed
- **Speed**: Very fast locally (thousands per second with GPU)
- **Dimension**: 384 (default model)

## Example: Building a Document Q&A System

```python
from app.services import load_document, chunk_text, VectorStore

# Initialize vector store once
vector_store = VectorStore(
    collection_name="qa_documents",
    use_openai_embeddings=True
)

# Ingest documents
for pdf_file in ["doc1.pdf", "doc2.pdf", "doc3.pdf"]:
    text = load_document(pdf_file)
    chunks = chunk_text(text, chunk_size=500, chunk_overlap=50)
    
    metadata = [{"source": pdf_file, "chunk": i} for i in range(len(chunks))]
    vector_store.add_documents(chunks, metadata=metadata)

print(f"Indexed {vector_store.collection.count()} chunks")

# Answer questions
while True:
    question = input("\nAsk a question (or 'quit'): ")
    if question.lower() == 'quit':
        break
    
    results = vector_store.search(question, k=3)
    
    print("\nRelevant passages:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. [{result['metadata']['source']}] "
              f"(similarity: {result['similarity_score']:.2f})")
        print(result['document'][:200] + "...")
```

## Next Steps

The vector store is ready! You can now:

1. **Ingest your documents**: Use the document loader + chunker + vector store
2. **Build search**: Implement semantic search over your documents
3. **Add to API**: Integrate into FastAPI endpoints
4. **Implement RAG**: Use with LLM for retrieval-augmented generation

Example API endpoint:
```python
from fastapi import FastAPI
from app.services import VectorStore

app = FastAPI()
vector_store = VectorStore()

@app.post("/search")
async def search_documents(query: str, k: int = 4):
    results = vector_store.search(query, k=k)
    return {"results": results}
```

## Troubleshooting

**Issue**: PyTorch DLL error on Windows  
**Solution**: Use OpenAI embeddings or see `WINDOWS_PYTORCH_FIX.md`

**Issue**: Out of memory  
**Solution**: Reduce chunk size or batch size when adding documents

**Issue**: ChromaDB collection already exists  
**Solution**: Use `vector_store.clear_collection()` or choose different collection name

**Issue**: Slow search  
**Solution**: Reduce `k` parameter or use fewer documents for testing
