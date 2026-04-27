# System Architecture

## Overview Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         USER BROWSER                         │
│                     (http://localhost:8000)                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (Chat UI)                      │
│                     static/index.html                        │
│                                                              │
│  ┌────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │   Upload   │  │  Chat Area   │  │  Message Input    │  │
│  │  Section   │  │  (Messages)  │  │   (Send Box)      │  │
│  └─────┬──────┘  └──────┬───────┘  └────────┬──────────┘  │
│        │                │                    │              │
│        │ POST          │ Display            │ POST         │
│        │ /upload       │ Messages           │ /query       │
└────────┼────────────────┼────────────────────┼──────────────┘
         │                │                    │
         │                │                    │
         ▼                │                    ▼
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                           │
│                        main.py                               │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Static File Server                                   │  │
│  │  - Serves index.html at "/"                          │  │
│  │  - Mounts /static/ directory                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API Routes (app/routes/documents.py)                │  │
│  │                                                       │  │
│  │  POST /api/v1/upload                                 │  │
│  │  ├─ Accept file (PDF/DOCX/TXT)                      │  │
│  │  ├─ Extract text                                     │  │
│  │  ├─ Chunk text                                       │  │
│  │  └─ Store in vector DB                               │  │
│  │                                                       │  │
│  │  POST /api/v1/query                                  │  │
│  │  ├─ Receive question                                 │  │
│  │  ├─ Search vector DB                                 │  │
│  │  ├─ Call LLM with context                            │  │
│  │  └─ Return answer + sources                          │  │
│  └────────┬─────────────────────────┬────────────────────┘  │
│           │                         │                        │
└───────────┼─────────────────────────┼────────────────────────┘
            │                         │
            ▼                         ▼
┌─────────────────────┐   ┌──────────────────────────┐
│   VECTOR STORE      │   │    LLM SERVICE           │
│   vector_store.py   │   │    llm_service.py        │
│                     │   │                          │
│  ┌──────────────┐  │   │  ┌────────────────────┐  │
│  │   ChromaDB   │  │   │  │   OpenAI GPT       │  │
│  │   (Local)    │  │   │  │   gpt-3.5-turbo    │  │
│  │              │  │   │  │                    │  │
│  │  Collection: │  │   │  │  - Generate answer │  │
│  │  "documents" │  │   │  │  - Use context     │  │
│  │              │  │   │  │  - Return sources  │  │
│  └──────────────┘  │   │  └────────────────────┘  │
│                     │   │                          │
│  • Store chunks     │   │  • RAG pipeline          │
│  • Generate embeds  │   │  • Prompt engineering    │
│  • Similarity search│   │  • Token management      │
└─────────────────────┘   └──────────────────────────┘
            ▲                         ▲
            │                         │
            │                         │
┌───────────┴─────────────────────────┴────────────────┐
│              SUPPORTING SERVICES                      │
│                                                       │
│  ┌───────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │ Document      │  │   Chunker    │  │Embeddings│  │
│  │ Loader        │  │   Service    │  │ Service  │  │
│  │               │  │              │  │          │  │
│  │ • PDF         │  │ • LangChain  │  │ • OpenAI │  │
│  │ • DOCX        │  │ • Smart      │  │ • Sentence│  │
│  │ • TXT         │  │   splitting  │  │   Trans. │  │
│  └───────────────┘  └──────────────┘  └──────────┘  │
└───────────────────────────────────────────────────────┘
```

## Request Flow Diagrams

### Upload Flow

```
User Browser                  FastAPI                   Services
     │                           │                         │
     │  1. Select file          │                         │
     ├──────────────────────────►│                         │
     │  POST /api/v1/upload      │                         │
     │  (multipart/form-data)    │                         │
     │                           │                         │
     │                           │  2. Extract text        │
     │                           ├────────────────────────►│
     │                           │  load_document()        │
     │                           │                         │
     │                           │  3. Chunk text          │
     │                           ├────────────────────────►│
     │                           │  chunk_text()           │
     │                           │                         │
     │                           │  4. Store chunks        │
     │                           ├────────────────────────►│
     │                           │  vector_store.add()     │
     │                           │                         │
     │                           │◄────────────────────────┤
     │                           │  chunks stored          │
     │                           │                         │
     │  5. Upload response       │                         │
     │◄──────────────────────────┤                         │
     │  {filename, chunks_count} │                         │
     │                           │                         │
     │  6. Display success       │                         │
     │                           │                         │
```

### Query Flow

```
User Browser              FastAPI              Vector Store      LLM Service
     │                       │                      │                │
     │  1. Type question    │                      │                │
     ├─────────────────────►│                      │                │
     │  POST /api/v1/query  │                      │                │
     │  {question, k}       │                      │                │
     │                       │                      │                │
     │                       │  2. Search vectors   │                │
     │                       ├─────────────────────►│                │
     │                       │  vector_store.search │                │
     │                       │                      │                │
     │                       │◄─────────────────────┤                │
     │                       │  [context_chunks]    │                │
     │                       │                      │                │
     │                       │  3. Generate answer                   │
     │                       ├──────────────────────────────────────►│
     │                       │  llm_service.answer()                 │
     │                       │                                       │
     │                       │◄──────────────────────────────────────┤
     │                       │  {answer, sources}                    │
     │                       │                                       │
     │  4. Query response    │                                       │
     │◄─────────────────────┤                                        │
     │  {answer, sources[]}  │                                        │
     │                       │                                        │
     │  5. Display chat      │                                        │
     │  + sources            │                                        │
     │                       │                                        │
```

## Data Flow

### Upload Data Transformation

```
Input File (PDF/DOCX/TXT)
         │
         ▼
    [Document Loader]
         │
         ▼
    Full Text String
    "Machine learning is..."
         │
         ▼
    [Text Chunker]
         │
         ▼
    Text Chunks (Array)
    [
      "Machine learning is a method...",
      "Applications include...",
      "The main types are..."
    ]
         │
         ▼
    [Embedding Generator]
         │
         ▼
    Vector Embeddings
    [
      [0.234, -0.567, 0.891, ...],  // 1536 dimensions
      [0.123, -0.456, 0.789, ...],
      [0.345, -0.678, 0.912, ...]
    ]
         │
         ▼
    [ChromaDB Storage]
         │
         ▼
    Stored in Collection
    "documents"
    {
      id: "uuid-1",
      embedding: [...],
      text: "Machine learning is...",
      metadata: {
        filename: "ml.txt",
        page_number: 1,
        chunk_index: 0
      }
    }
```

### Query Data Transformation

```
User Question
"What is machine learning?"
         │
         ▼
    [Embedding Generator]
         │
         ▼
    Query Vector
    [0.456, -0.789, 0.123, ...]  // 1536 dimensions
         │
         ▼
    [Vector Similarity Search]
         │
         ▼
    Top K Similar Chunks
    [
      {
        text: "Machine learning is a method...",
        similarity: 0.93,
        metadata: {filename: "ml.txt", page: 1}
      },
      {
        text: "Applications include...",
        similarity: 0.87,
        metadata: {filename: "ml.txt", page: 2}
      }
    ]
         │
         ▼
    [LLM Prompt Construction]
         │
         ▼
    Prompt to GPT
    "Answer based on context:
     [chunk 1]
     [chunk 2]
     Question: What is machine learning?"
         │
         ▼
    [OpenAI GPT-3.5]
         │
         ▼
    Generated Answer
    "Machine learning is a branch of
     artificial intelligence that..."
         │
         ▼
    [Response Formatting]
         │
         ▼
    JSON Response
    {
      answer: "Machine learning is...",
      sources: [...],
      model: "gpt-3.5-turbo",
      context_used: 2
    }
         │
         ▼
    Displayed in Chat UI
```

## Component Interaction

```
┌─────────────────────────────────────────────────────┐
│                  FRONTEND LAYER                      │
│                                                      │
│  • index.html (UI)                                  │
│  • JavaScript (API calls)                           │
│  • CSS (Styling)                                    │
└────────────────┬────────────────────────────────────┘
                 │
                 │ HTTP/JSON
                 │
┌────────────────▼────────────────────────────────────┐
│                  API LAYER                           │
│                                                      │
│  • FastAPI (main.py)                                │
│  • Routes (documents.py)                            │
│  • CORS middleware                                  │
│  • Static file serving                              │
└────────────────┬────────────────────────────────────┘
                 │
                 │ Function calls
                 │
┌────────────────▼────────────────────────────────────┐
│               SERVICE LAYER                          │
│                                                      │
│  • Vector Store (storage + search)                  │
│  • LLM Service (answer generation)                  │
│  • Document Loader (text extraction)                │
│  • Chunker (text splitting)                         │
│  • Embeddings (vector generation)                   │
└────────────────┬────────────────────────────────────┘
                 │
                 │ API calls
                 │
┌────────────────▼────────────────────────────────────┐
│              EXTERNAL SERVICES                       │
│                                                      │
│  • OpenAI API (embeddings + chat)                   │
│  • ChromaDB (local vector database)                 │
└─────────────────────────────────────────────────────┘
```

## Technology Stack

```
Frontend
├── HTML5
├── CSS3 (embedded)
└── JavaScript ES6+ (embedded)

Backend
├── Python 3.x
├── FastAPI
├── Uvicorn
└── Pydantic

AI/ML
├── LangChain
├── OpenAI GPT-3.5
└── OpenAI Embeddings

Vector Database
└── ChromaDB

Document Processing
├── PyPDF
└── python-docx

Utilities
├── python-dotenv
└── aiofiles
```

## File Organization

```
Gen_AI_Document_Assistant_Backend/
│
├── Frontend
│   └── static/
│       └── index.html              # Chat UI
│
├── Backend
│   ├── main.py                     # FastAPI app
│   └── app/
│       ├── routes/
│       │   └── documents.py        # API endpoints
│       └── services/
│           ├── vector_store.py     # Vector operations
│           ├── llm_service.py      # LLM integration
│           ├── document_loader.py  # File parsing
│           ├── chunker.py          # Text splitting
│           └── embeddings.py       # Vector generation
│
├── Data Storage
│   ├── data/                       # Uploaded files
│   └── chroma_db/                  # Vector database
│
├── Configuration
│   ├── .env                        # API keys
│   └── requirements.txt            # Dependencies
│
├── Scripts
│   ├── start_chat_ui.py           # Quick launcher
│   └── test_*.py                   # Test scripts
│
└── Documentation
    ├── README.md
    ├── API_DOCUMENTATION.md
    ├── CHAT_UI_GUIDE.md
    ├── TESTING_CHECKLIST.md
    ├── DEMO_GUIDE.md
    └── IMPLEMENTATION_SUMMARY.md
```

---

## Deployment Architecture (Production)

```
                    Internet
                       │
                       ▼
                ┌──────────────┐
                │   Load       │
                │   Balancer   │
                └──────┬───────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌───────────────┐            ┌───────────────┐
│  FastAPI      │            │  FastAPI      │
│  Instance 1   │            │  Instance 2   │
└───────┬───────┘            └───────┬───────┘
        │                             │
        └──────────────┬──────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  Shared Vector │
              │  Database      │
              │  (ChromaDB)    │
              └────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  Object        │
              │  Storage       │
              │  (Documents)   │
              └────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  OpenAI API    │
              │  (External)    │
              └────────────────┘
```

---

*Architecture designed for scalability, maintainability, and performance*
