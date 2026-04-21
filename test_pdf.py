"""
Quick test to verify PDF loading and chunking with the sample PDF.
"""

import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.document_loader import load_document
from app.services.chunker import chunk_text


def main():
    pdf_path = 'data/test_files/sample_document.pdf'
    
    print("=" * 80)
    print("PDF Document Processing Test")
    print("=" * 80)
    print()
    
    # Load PDF
    print(f"Loading PDF: {pdf_path}")
    text = load_document(pdf_path)
    print(f"✓ Successfully loaded PDF")
    print(f"  Extracted text length: {len(text)} characters")
    print()
    
    # Show first 400 characters
    print("First 400 characters of extracted text:")
    print("-" * 80)
    print(text[:400])
    print("-" * 80)
    print()
    
    # Chunk the text
    print("Chunking text (chunk_size=500, overlap=50)...")
    chunks = chunk_text(text, chunk_size=500, chunk_overlap=50)
    print(f"✓ Successfully created {len(chunks)} chunks")
    print()
    
    # Show chunk details
    print("Chunk size distribution:")
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i+1}: {len(chunk)} characters")
    print()
    
    # Display first 3 chunks
    print("First 3 chunks:")
    print("=" * 80)
    for i, chunk in enumerate(chunks[:3]):
        print(f"\nChunk #{i+1}:")
        print("-" * 80)
        print(chunk)
        print("-" * 80)
    
    print("\n✓ PDF processing test completed successfully!")


if __name__ == "__main__":
    main()
