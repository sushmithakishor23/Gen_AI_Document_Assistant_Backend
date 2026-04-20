# Gen AI Document Assistance Backend

AI-powered document assistant backend API built with FastAPI, LangChain, and ChromaDB.

## Project Structure

```
.
├── app/
│   ├── routes/          # API route handlers
│   ├── services/        # Business logic and AI services
│   └── utils/           # Utility functions
├── tests/               # Test files
├── data/                # Document storage
├── main.py              # FastAPI application entry point
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (not in git)
├── .env.example         # Environment template
└── .gitignore          # Git ignore rules
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

### 4. Run the Server

```powershell
# Development mode (with auto-reload)
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at `http://localhost:8000`

## API Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

## Dependencies

- **FastAPI** - Modern web framework for building APIs
- **Uvicorn** - ASGI server
- **LangChain** - AI/LLM framework
- **OpenAI** - OpenAI API client
- **ChromaDB** - Vector database for embeddings
- **PyPDF & python-docx** - Document processing

## Development

### Testing the API

```powershell
# Test health endpoint
Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing
```

### Next Steps

1. Add document upload endpoints in `app/routes/`
2. Implement document processing in `app/services/`
3. Set up ChromaDB for vector storage
4. Add AI query endpoints using LangChain
5. Write tests in `tests/`

## License

MIT