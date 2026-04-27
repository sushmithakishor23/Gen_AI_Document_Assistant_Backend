"""
Quick Start Script for Chat UI Demo
Helps you test the complete MVP quickly
"""

import os
import sys
from pathlib import Path


def print_banner():
    """Print welcome banner"""
    print("=" * 60)
    print("🤖 Gen AI Document Assistant - Chat UI Demo")
    print("=" * 60)
    print()


def check_environment():
    """Check if environment is set up correctly"""
    print("📋 Checking environment...")
    
    issues = []
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        issues.append("❌ Virtual environment not activated")
        print("   Run: .\\venv\\Scripts\\Activate.ps1")
    else:
        print("   ✅ Virtual environment: Active")
    
    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        issues.append("❌ OPENAI_API_KEY not set")
        print("   Run: $env:OPENAI_API_KEY='your-key-here'")
    else:
        api_key = os.getenv('OPENAI_API_KEY')
        masked_key = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else "***"
        print(f"   ✅ OpenAI API Key: {masked_key}")
    
    # Check if static folder exists
    static_dir = Path(__file__).parent / "static"
    if not static_dir.exists():
        issues.append("❌ Static folder not found")
    else:
        print(f"   ✅ Static folder: {static_dir}")
    
    # Check if index.html exists
    index_path = static_dir / "index.html"
    if not index_path.exists():
        issues.append("❌ index.html not found")
    else:
        print(f"   ✅ Chat UI: {index_path}")
    
    # Check if sample files exist
    test_files_dir = Path(__file__).parent / "data" / "test_files"
    if test_files_dir.exists():
        test_files = list(test_files_dir.glob("*.*"))
        if test_files:
            print(f"   ✅ Sample files: {len(test_files)} files available")
        else:
            print("   ⚠️  No sample files found (optional)")
    
    print()
    
    return issues


def print_instructions():
    """Print usage instructions"""
    print("🚀 Quick Start Instructions:")
    print("-" * 60)
    print()
    print("1. The server will start at: http://localhost:8000")
    print("2. Your browser will automatically open the chat UI")
    print("3. Upload a document using the upload section")
    print("4. Ask questions in the chat!")
    print()
    print("📁 Sample files to try:")
    
    test_files_dir = Path(__file__).parent / "data" / "test_files"
    if test_files_dir.exists():
        for f in test_files_dir.glob("*.txt"):
            print(f"   • {f.name}")
    
    print()
    print("💡 Example questions:")
    print("   • What is this document about?")
    print("   • Summarize the main points")
    print("   • Explain the key concepts")
    print()
    print("-" * 60)
    print()


def start_server():
    """Start the FastAPI server"""
    import uvicorn
    
    print("🔄 Starting server...")
    print()
    print("=" * 60)
    print("Server running at: http://localhost:8000")
    print("Press CTRL+C to stop")
    print("=" * 60)
    print()
    
    # Try to open browser
    try:
        import webbrowser
        import time
        import threading
        
        def open_browser():
            time.sleep(2)  # Wait for server to start
            webbrowser.open('http://localhost:8000')
        
        threading.Thread(target=open_browser, daemon=True).start()
    except:
        pass
    
    # Start server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


def main():
    """Main function"""
    print_banner()
    
    # Check environment
    issues = check_environment()
    
    if issues:
        print("⚠️  Issues found:")
        for issue in issues:
            print(f"   {issue}")
        print()
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("❌ Startup cancelled")
            return
        print()
    
    # Print instructions
    print_instructions()
    
    # Start server
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("\nTry running manually:")
        print("   python main.py")


if __name__ == "__main__":
    main()
