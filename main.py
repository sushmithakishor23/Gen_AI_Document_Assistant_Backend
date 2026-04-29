from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os
from datetime import datetime
from pathlib import Path

from app.routes import documents_router

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title=os.getenv("APP_NAME", "Gen AI Document Assistant"),
    version=os.getenv("APP_VERSION", "1.0.0"),
    description="AI-powered document assistant backend API with RAG capabilities"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents_router)

# Mount static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    """Serve the chat UI"""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {
        "message": "Welcome to Gen AI Document Assistant API",
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "note": "Chat UI not found. Please check /docs for API documentation."
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": os.getenv("APP_NAME", "Gen AI Document Assistant"),
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    
    # Parse PORT with error handling for non-numeric values
    try:
        port = int(os.getenv("PORT", "8000"))
    except (ValueError, TypeError):
        print(f"Warning: Invalid PORT value '{os.getenv('PORT')}', using default 8000")
        port = 8000
    
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug
    )
