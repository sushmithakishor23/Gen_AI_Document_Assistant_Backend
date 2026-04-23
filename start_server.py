"""
Quick Start Script
Starts the FastAPI server and provides helpful information.
"""

import os
import sys
from pathlib import Path


def check_environment():
    """Check if environment is properly configured."""
    print("Checking environment...")
    
    # Check for .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠ WARNING: .env file not found")
        print("  Create a .env file with your OPENAI_API_KEY")
        print("  Example: OPENAI_API_KEY=sk-your-key-here")
        print()
    
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠ WARNING: OPENAI_API_KEY not set")
        print("  Set it in .env file or environment variable")
        print()
        print("  PowerShell: $env:OPENAI_API_KEY='your-key-here'")
        print("  CMD:        set OPENAI_API_KEY=your-key-here")
        print()
        response = input("Do you want to continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    else:
        print(f"✓ OPENAI_API_KEY is set (ends with ...{api_key[-4:]})")
    
    # Check if ChromaDB directory exists
    chroma_dir = Path("./chroma_db")
    if chroma_dir.exists():
        print(f"✓ Vector database found at {chroma_dir}")
    else:
        print(f"ℹ Vector database will be created at {chroma_dir}")
    
    # Check if test files exist
    test_dir = Path("data/test_files")
    if test_dir.exists() and any(test_dir.iterdir()):
        print(f"✓ Test files found in {test_dir}")
    else:
        print(f"ℹ No test files found. You can create sample files with:")
        print(f"  py create_sample_pdf.py")
    
    print()


def print_instructions():
    """Print helpful instructions."""
    print("=" * 80)
    print("  Gen AI Document Assistant - RAG API Server")
    print("=" * 80)
    print()
    print("Server will start at: http://localhost:8000")
    print()
    print("Quick Links:")
    print("  • API Documentation: http://localhost:8000/docs")
    print("  • Health Check:      http://localhost:8000/health")
    print("  • Root:              http://localhost:8000")
    print()
    print("API Endpoints:")
    print("  • POST /api/v1/upload - Upload and ingest documents")
    print("  • POST /api/v1/query  - Ask questions (RAG)")
    print("  • GET  /api/v1/collections/{name}/stats - Get statistics")
    print()
    print("Test the API:")
    print("  • From another terminal, run: py test_api.py")
    print("  • Or use curl/Postman (see API_DOCUMENTATION.md)")
    print()
    print("Example cURL commands:")
    print("  # Upload a document")
    print("  curl -X POST http://localhost:8000/api/v1/upload \\")
    print('    -F "file=@data/test_files/sample_document.pdf"')
    print()
    print("  # Query documents")
    print("  curl -X POST http://localhost:8000/api/v1/query \\")
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"question": "What is NLP?", "k": 4}\'')
    print()
    print("=" * 80)
    print()
    print("Starting server...")
    print()


def main():
    """Main function to start the server."""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check environment
    check_environment()
    
    # Print instructions
    print_instructions()
    
    # Start the server
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug
    )


if __name__ == "__main__":
    main()
