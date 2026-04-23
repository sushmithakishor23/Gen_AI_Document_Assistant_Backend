# RAG API Documentation

## Overview
Complete RAG (Retrieval-Augmented Generation) API with document ingestion, vector search, and LLM-powered question answering.

## Base URL
```
http://localhost:8000
```

## API Endpoints

### 1. Upload Document
**Endpoint:** `POST /api/v1/upload`

Upload and ingest a document into the vector database.

**Request:**
- **Content-Type:** `multipart/form-data`
- **Parameters:**
  - `file` (required): Document file (PDF, DOCX, or TXT)
  - `collection_name` (optional): Collection name (default: "documents")
  - `chunk_size` (optional): Chunk size in characters (default: 500)
  - `chunk_overlap` (optional): Chunk overlap in characters (default: 50)

**Response:**
```json
{
  "filename": "sample_document.pdf",
  "chunks_created": 5,
  "chunks_stored": 5,
  "collection_name": "documents",
  "message": "Successfully ingested sample_document.pdf into documents collection"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@data/test_files/sample_document.pdf" \
  -F "collection_name=documents" \
  -F "chunk_size=500" \
  -F "chunk_overlap=50"
```

**Python Example:**
```python
import requests

with open('document.pdf', 'rb') as f:
    files = {'file': f}
    data = {'collection_name': 'documents'}
    response = requests.post('http://localhost:8000/api/v1/upload', files=files, data=data)
    print(response.json())
```

---

### 2. Query Documents
**Endpoint:** `POST /api/v1/query`

Ask questions about uploaded documents using RAG.

**Request:**
- **Content-Type:** `application/json`
- **Body:**
```json
{
  "question": "What is natural language processing?",
  "k": 4,
  "collection_name": "documents"
}
```

**Parameters:**
- `question` (required): The question to answer
- `k` (optional): Number of context chunks to retrieve (1-10, default: 4)
- `collection_name` (optional): Collection to search (default: "documents")

**Response:**
```json
{
  "answer": "Natural Language Processing (NLP) is a branch of artificial intelligence that helps computers understand, interpret, and manipulate human language...",
  "sources": [
    {
      "text": "Natural Language Processing (NLP) is a branch of artificial intelligence...",
      "similarity_score": 0.8934,
      "metadata": {
        "source": "sample_document.pdf",
        "filename": "sample_document.pdf",
        "chunk_index": 0,
        "page_number": 1
      }
    }
  ],
  "model": "gpt-3.5-turbo",
  "context_used": 3,
  "usage": {
    "prompt_tokens": 523,
    "completion_tokens": 89,
    "total_tokens": 612
  }
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is natural language processing?",
    "k": 4,
    "collection_name": "documents"
  }'
```

**Python Example:**
```python
import requests

payload = {
    "question": "What is natural language processing?",
    "k": 4,
    "collection_name": "documents"
}

response = requests.post(
    'http://localhost:8000/api/v1/query',
    json=payload
)

result = response.json()
print(f"Answer: {result['answer']}")
print(f"\nSources:")
for source in result['sources']:
    print(f"  - {source['metadata']['filename']} (score: {source['similarity_score']:.4f})")
```

---

### 3. Get Collection Statistics
**Endpoint:** `GET /api/v1/collections/{collection_name}/stats`

Get statistics about a vector store collection.

**Response:**
```json
{
  "collection_name": "documents",
  "persist_directory": "./chroma_db",
  "document_count": 15,
  "embeddings_info": {
    "provider": "openai",
    "model_name": "text-embedding-3-small",
    "dimension": 1536,
    "is_free": false
  }
}
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/collections/documents/stats"
```

---

### 4. Clear Collection
**Endpoint:** `DELETE /api/v1/collections/{collection_name}`

Delete all documents from a collection.

**Response:**
```json
{
  "message": "Cleared 15 documents from documents",
  "deleted_count": 15
}
```

**cURL Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/collections/documents"
```

---

### 5. Health Check
**Endpoint:** `GET /health`

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "Gen AI Document Assistant",
  "version": "1.0.0",
  "timestamp": "2026-04-23T10:30:00"
}
```

---

## Complete Workflow Example

### Step 1: Start the Server
```bash
# Set your OpenAI API key
$env:OPENAI_API_KEY='your-api-key-here'

# Start the server
py main.py
```

The server will start at `http://localhost:8000`

### Step 2: Upload Documents
```bash
# Upload a PDF
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@document.pdf"

# Upload a DOCX
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@report.docx"
```

### Step 3: Query Documents
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main findings?",
    "k": 5
  }'
```

### Step 4: View API Documentation
Open in browser: `http://localhost:8000/docs`

---

## Python Client Example

```python
import requests
from pathlib import Path

class DocumentAssistantClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
    
    def upload_document(self, file_path, collection="documents"):
        """Upload a document to the vector store."""
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f)}
            data = {'collection_name': collection}
            response = requests.post(f"{self.api_base}/upload", files=files, data=data)
            response.raise_for_status()
            return response.json()
    
    def query(self, question, k=4, collection="documents"):
        """Ask a question about the documents."""
        payload = {
            "question": question,
            "k": k,
            "collection_name": collection
        }
        response = requests.post(f"{self.api_base}/query", json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_stats(self, collection="documents"):
        """Get collection statistics."""
        response = requests.get(f"{self.api_base}/collections/{collection}/stats")
        response.raise_for_status()
        return response.json()

# Usage
client = DocumentAssistantClient()

# Upload documents
result = client.upload_document("report.pdf")
print(f"Uploaded: {result['filename']}, created {result['chunks_created']} chunks")

# Ask questions
answer = client.query("What are the key findings?")
print(f"\nAnswer: {answer['answer']}")

print(f"\nSources:")
for source in answer['sources']:
    print(f"  - {source['metadata']['filename']} (similarity: {source['similarity_score']:.2f})")
```

---

## Testing with Postman

### 1. Upload Document
- **Method:** POST
- **URL:** `http://localhost:8000/api/v1/upload`
- **Body:** form-data
  - Key: `file`, Type: File, Value: [Select your PDF/DOCX file]
  - Key: `collection_name`, Type: Text, Value: `documents`

### 2. Query
- **Method:** POST
- **URL:** `http://localhost:8000/api/v1/query`
- **Headers:** `Content-Type: application/json`
- **Body:** raw JSON
```json
{
  "question": "What is this document about?",
  "k": 4
}
```

---

## Error Handling

### 400 Bad Request
```json
{
  "detail": "Unsupported file type: .jpg. Allowed types: .pdf, .docx, .txt"
}
```

### 404 Not Found
```json
{
  "detail": "No documents found in collection 'documents'. Please upload documents first."
}
```

### 500 Internal Server Error
```json
{
  "detail": "LLM API call failed: ..."
}
```

---

## Environment Variables

Create a `.env` file:
```env
# OpenAI API Key (required)
OPENAI_API_KEY=sk-your-api-key-here

# Server Configuration (optional)
HOST=0.0.0.0
PORT=8000
DEBUG=True

# App Information (optional)
APP_NAME=Gen AI Document Assistant
APP_VERSION=1.0.0
```

---

## Performance Tips

1. **Chunk Size**: Smaller chunks (300-500) for precise answers, larger chunks (700-1000) for context
2. **K Parameter**: Start with k=3-5 for most queries
3. **Collection Management**: Use separate collections for different document sets
4. **Batch Uploads**: Upload multiple documents to build a comprehensive knowledge base

---

## Limitations

- **Supported File Types:** PDF, DOCX, TXT only
- **Max File Size:** Depends on server configuration (default: unlimited)
- **Scanned PDFs:** Not supported (OCR not implemented)
- **API Rate Limits:** Subject to OpenAI rate limits
- **Concurrent Requests:** Shared vector store instance (consider scaling for production)

---

## Next Steps

1. **Test the API:** Use `test_api.py` or Postman
2. **Build a Frontend:** Connect to these endpoints
3. **Add Authentication:** Implement API keys or OAuth
4. **Scale:** Deploy with Docker, add load balancing
5. **Monitor:** Add logging and metrics

## Support

For issues or questions, check:
- API Documentation: `http://localhost:8000/docs`
- Test Examples: `test_api.py`
- Vector Store Guide: `VECTOR_STORE_GUIDE.md`
