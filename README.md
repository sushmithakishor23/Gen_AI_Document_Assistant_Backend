# Gen AI Document Assistant Backend

AI-powered document assistant backend with document processing, vector embeddings, and semantic search capabilities.

## Features

- ✅ **Document Loading**: Extract text from PDF, DOCX, and TXT files
- ✅ **Text Chunking**: Intelligent text splitting with LangChain
- ✅ **Vector Embeddings**: OpenAI or sentence-transformers support
- ✅ **Vector Search**: ChromaDB-based semantic search
- 🚧 **FastAPI Endpoints**: (Coming soon)

## Project Structure

```
.
├── app/
│   ├── routes/          # API route handlers
│   ├── services/        # Business logic and AI services
│   │   ├── document_loader.py    # PDF/DOCX/TXT extraction
│   │   ├── chunker.py            # Text chunking
│   │   ├── embeddings.py         # Embedding generation
│   │   └── vector_store.py       # ChromaDB vector search
│   └── utils/           # Utility functions
├── tests/               # Test files
├── data/                # Document storage
│   └── test_files/      # Sample documents
├── chroma_db/           # Vector database (persisted)
├── main.py              # FastAPI application entry point
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (not in git)
└── *.py                 # Test scripts
```

## Setup Instructions

### 1. Create Virtual Environment

```powershell
# Using venv
py -m venv venv

# Activate on Windows PowerShell
.\venv\Scripts\Activate.ps1

# Activate on Windows CMD
.\venv\Scripts\activate.bat
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure Environment

1. Copy `.env.example` to `.env`
2. Add your API keys:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```

### 4. Test the Services

```powershell
# Test document processing (PDF, DOCX, TXT)
py test_document_processing.py

# Test PDF processing specifically
py test_pdf.py

# Test vector store with OpenAI embeddings (recommended)
$env:OPENAI_API_KEY='your-key-here'
py test_vector_store_openai.py
```

**Note**: If you encounter PyTorch DLL errors on Windows, see `WINDOWS_PYTORCH_FIX.md`

### 5. Run the Server

```powershell
# Development mode (with auto-reload)
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at `http://localhost:8000`

## Quick Start - Document Processing

```python
from app.services import load_document, chunk_text, VectorStore

# 1. Load a document
text = load_document('data/your_document.pdf')

# 2. Chunk into smaller pieces
chunks = chunk_text(text, chunk_size=500, chunk_overlap=50)

# 3. Create vector store
vector_store = VectorStore(
    collection_name="my_docs",
    use_openai_embeddings=True  # requires OPENAI_API_KEY
)

# 4. Add to vector store
vector_store.add_documents(chunks, metadata=[{"source": "your_document.pdf"}] * len(chunks))

# 5. Search semantically
results = vector_store.search("What is this document about?", k=3)

for result in results:
    print(f"Similarity: {result['similarity_score']:.4f}")
    print(f"Text: {result['document'][:200]}...\n")
```

See `VECTOR_STORE_GUIDE.md` for complete documentation.

## API Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

## Dependencies

- **FastAPI** - Modern web framework for building APIs
- **Uvicorn** - ASGI server
- **LangChain** - AI/LLM framework and text splitting
- **OpenAI** - OpenAI API client (embeddings and LLMs)
- **ChromaDB** - Vector database for semantic search
- **Sentence-Transformers** - Local embedding generation (free alternative)
- **PyPDF & python-docx** - Document text extraction

## Services

### Document Loader (`app/services/document_loader.py`)
- Extracts text from PDF, DOCX, TXT
- Handles edge cases: empty files, corrupted files, scanned PDFs
- Multi-encoding support for text files

### Text Chunker (`app/services/chunker.py`)
- Uses LangChain's RecursiveCharacterTextSplitter
- Smart splitting on natural boundaries
- Configurable chunk size (default: 500) and overlap (default: 50)

### Embeddings (`app/services/embeddings.py`)
- **OpenAI**: `text-embedding-3-small` (1536d, requires API key)
- **Sentence-Transformers**: `all-MiniLM-L6-v2` (384d, free, local)
- Flexible provider system

### Vector Store (`app/services/vector_store.py`)
- ChromaDB-based persistent storage
- Semantic search with similarity scores
- Metadata filtering and management
- Automatic persistence to `./chroma_db`

## Test Scripts

| Script | Description | Requirement |
|--------|-------------|-------------|
| `test_document_processing.py` | Tests document loader and chunker | None |
| `test_pdf.py` | Focused PDF processing test | None |
| `test_vector_store_openai.py` | Vector store with OpenAI | OPENAI_API_KEY |
| `test_vector_store.py` | Vector store with sentence-transformers | Working PyTorch |
| `test_validation.py` | Quick validation of code structure | None |

## Documentation

- **`VECTOR_STORE_GUIDE.md`** - Complete vector store usage guide
- **`WINDOWS_PYTORCH_FIX.md`** - Troubleshooting PyTorch on Windows
- **`IMPLEMENTATION_SUMMARY.md`** - Document processing implementation details

## Development

### Testing the API

```powershell
# Test health endpoint
Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing
```

### Running Tests

```powershell
# Test document loading and chunking
py test_document_processing.py

# Test vector store (requires OpenAI API key)
$env:OPENAI_API_KEY='sk-your-key-here'
py test_vector_store_openai.py
```

### Creating Sample Files

```powershell
# Create a sample PDF for testing
py create_sample_pdf.py
```

## Troubleshooting

**PyTorch DLL Error on Windows**
- Use OpenAI embeddings instead: `use_openai_embeddings=True`
- Or see `WINDOWS_PYTORCH_FIX.md` for solutions

**Import Errors**
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Activate virtual environment before running

**ChromaDB Errors**
- Delete `./chroma_db` directory and recreate
- Check write permissions on project directory

## Next Steps

1. Add document upload endpoints in `app/routes/`
2. Implement document processing in `app/services/`
3. Set up ChromaDB for vector storage
4. Add AI query endpoints using LangChain
5. Write tests in `tests/`

## License

MIT