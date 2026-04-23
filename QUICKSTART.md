# Quick Start Guide - RAG API Testing

## Prerequisites

1. **Set OpenAI API Key**
   ```powershell
   $env:OPENAI_API_KEY='sk-your-api-key-here'
   ```

2. **Ensure dependencies are installed**
   ```powershell
   pip install -r requirements.txt
   ```

## Step 1: Start the Server

```powershell
py start_server.py
```

The server will start at http://localhost:8000

You should see output like:
```
✓ OPENAI_API_KEY is set (ends with ...xxxx)
✓ Vector database found at chroma_db
✓ Test files found in data\test_files

Server will start at: http://localhost:8000

Quick Links:
  • API Documentation: http://localhost:8000/docs
  • Health Check:      http://localhost:8000/health
```

## Step 2: Test with Python (Recommended)

Open a **new terminal** and run:

```powershell
# Run the complete test suite
py test_api.py
```

This will:
1. Check server health
2. Upload a sample PDF
3. Get collection statistics
4. Run multiple test queries
5. Display answers with sources

### Individual Tests

```powershell
# Upload a specific document
py test_api.py upload data/test_files/sample_document.pdf

# Query with a specific question
py test_api.py query "What is natural language processing?"

# Get collection stats
py test_api.py stats

# See curl examples
py test_api.py curl
```

## Step 3: Test with cURL

### Upload a Document
```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@data/test_files/sample_document.pdf" \
  -F "collection_name=documents"
```

### Query Documents
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"What is natural language processing?\", \"k\": 4}"
```

### Get Stats
```bash
curl -X GET "http://localhost:8000/api/v1/collections/documents/stats"
```

## Step 4: Test with Postman

### Upload Document
1. **Method:** POST
2. **URL:** `http://localhost:8000/api/v1/upload`
3. **Body:** form-data
   - Key: `file`, Type: File, Value: [Select your PDF]
   - Key: `collection_name`, Type: Text, Value: `documents`

### Query
1. **Method:** POST
2. **URL:** `http://localhost:8000/api/v1/query`
3. **Headers:** `Content-Type: application/json`
4. **Body:** raw JSON
   ```json
   {
     "question": "What is natural language processing?",
     "k": 4
   }
   ```

## Step 5: Use Interactive API Docs

Open in browser: http://localhost:8000/docs

This provides a Swagger UI where you can:
- See all endpoints
- Try them interactively
- View request/response schemas

## Expected Output

### Upload Response
```json
{
  "filename": "sample_document.pdf",
  "chunks_created": 5,
  "chunks_stored": 5,
  "collection_name": "documents",
  "message": "Successfully ingested sample_document.pdf into documents collection"
}
```

### Query Response
```json
{
  "answer": "Natural Language Processing (NLP) is a branch of artificial intelligence that helps computers understand, interpret, and manipulate human language. NLP draws from many disciplines, including computer science and computational linguistics, in its pursuit to fill the gap between human communication and computer understanding.",
  "sources": [
    {
      "text": "Natural Language Processing (NLP) is a branch of artificial intelligence...",
      "similarity_score": 0.8934,
      "metadata": {
        "source": "sample_document.pdf",
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

## Troubleshooting

### Server won't start
- Check if OPENAI_API_KEY is set
- Ensure port 8000 is not in use
- Check for import errors: `py -c "from app.routes import documents_router"`

### Upload fails
- Verify file exists and is PDF/DOCX/TXT
- Check file size (very large files may timeout)
- Look at server logs for detailed error

### Query returns "No documents found"
- Make sure you uploaded documents first
- Check collection name matches (default: "documents")
- Run: `curl http://localhost:8000/api/v1/collections/documents/stats`

### OpenAI API errors
- Verify API key is correct and active
- Check if you have API credits
- Look for rate limit errors in server logs

## What's Happening Behind the Scenes

1. **Upload:**
   - File is saved temporarily
   - Text is extracted (PDF/DOCX/TXT)
   - Text is chunked into ~500 char pieces with 50 char overlap
   - Each chunk is converted to embeddings using OpenAI
   - Embeddings + text + metadata stored in ChromaDB

2. **Query:**
   - Question is converted to embedding
   - ChromaDB finds most similar chunks (vector search)
   - Top-k chunks sent to GPT-3.5-turbo with special RAG prompt
   - LLM generates answer based on context
   - Answer + sources returned

## Next Steps

1. Upload your own documents
2. Try different questions
3. Experiment with `k` parameter (2-8 works well)
4. Build a frontend that calls these APIs
5. Explore the interactive docs at `/docs`

## Full Documentation

See `API_DOCUMENTATION.md` for complete API reference with all endpoints, parameters, and examples.
