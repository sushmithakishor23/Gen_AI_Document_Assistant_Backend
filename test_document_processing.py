"""
Test script for document loader and chunker services.
Tests document loading, text chunking, and edge case handling.
"""

import os
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.document_loader import (
    DocumentLoader,
    load_document,
    EmptyFileError,
    CorruptedFileError,
    UnsupportedFileTypeError,
    ScannedPDFError
)
from app.services.chunker import TextChunker, chunk_text


def print_separator(title: str = ""):
    """Print a visual separator."""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)
    print()


def test_document_loader(file_path: str):
    """Test document loading with a specific file."""
    print_separator(f"Testing Document Loader: {file_path}")
    
    try:
        loader = DocumentLoader()
        text = loader.load(file_path)
        
        print(f"✓ Successfully loaded document")
        print(f"  File: {file_path}")
        print(f"  Text length: {len(text)} characters")
        print(f"\nFirst 500 characters:")
        print("-" * 80)
        print(text[:500])
        print("-" * 80)
        
        return text
        
    except FileNotFoundError as e:
        print(f"✗ File not found: {e}")
        return None
    except EmptyFileError as e:
        print(f"✗ Empty file: {e}")
        return None
    except CorruptedFileError as e:
        print(f"✗ Corrupted file: {e}")
        return None
    except ScannedPDFError as e:
        print(f"✗ Scanned PDF (OCR not supported): {e}")
        return None
    except UnsupportedFileTypeError as e:
        print(f"✗ Unsupported file type: {e}")
        return None
    except Exception as e:
        print(f"✗ Unexpected error: {type(e).__name__}: {e}")
        return None


def test_chunker(text: str, chunk_size: int = 500, chunk_overlap: int = 50):
    """Test text chunking."""
    print_separator(f"Testing Text Chunker (size={chunk_size}, overlap={chunk_overlap})")
    
    try:
        chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = chunker.chunk_text(text)
        
        print(f"✓ Successfully chunked text")
        print(f"  Total chunks: {len(chunks)}")
        
        # Get statistics
        stats = chunker.get_chunk_stats(chunks)
        print(f"\nChunk Statistics:")
        print(f"  Total chunks: {stats['total_chunks']}")
        print(f"  Total characters: {stats['total_characters']}")
        print(f"  Average chunk size: {stats['average_chunk_size']:.1f} chars")
        print(f"  Min chunk size: {stats['min_chunk_size']} chars")
        print(f"  Max chunk size: {stats['max_chunk_size']} chars")
        
        # Display first 3 chunks
        print(f"\nFirst 3 chunks:")
        print("-" * 80)
        for i, chunk in enumerate(chunks[:3]):
            print(f"\nChunk #{i + 1} ({len(chunk)} chars):")
            print(chunk[:200] + ("..." if len(chunk) > 200 else ""))
        print("-" * 80)
        
        return chunks
        
    except ValueError as e:
        print(f"✗ Invalid input: {e}")
        return None
    except Exception as e:
        print(f"✗ Unexpected error: {type(e).__name__}: {e}")
        return None


def test_edge_cases():
    """Test various edge cases."""
    print_separator("Testing Edge Cases")
    
    test_dir = Path("data/test_files")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Test 1: Empty file
    print("Test 1: Empty TXT file")
    empty_file = test_dir / "empty.txt"
    empty_file.write_text("")
    test_document_loader(str(empty_file))
    
    # Test 2: Very small file
    print("\nTest 2: Very small TXT file")
    small_file = test_dir / "small.txt"
    small_file.write_text("Hi")
    text = test_document_loader(str(small_file))
    if text:
        test_chunker(text, chunk_size=500, chunk_overlap=50)
    
    # Test 3: Unsupported file type
    print("\nTest 3: Unsupported file type (.jpg)")
    unsupported_file = test_dir / "image.jpg"
    unsupported_file.write_bytes(b"\xFF\xD8\xFF\xE0")
    test_document_loader(str(unsupported_file))
    
    # Test 4: Non-existent file
    print("\nTest 4: Non-existent file")
    test_document_loader("data/test_files/nonexistent.pdf")
    
    print("\nEdge case testing complete!")


def create_sample_text_file():
    """Create a sample text file for testing."""
    print_separator("Creating Sample Text File")
    
    sample_text = """
Machine Learning and Artificial Intelligence

Introduction
Machine learning is a subset of artificial intelligence that provides systems the ability 
to automatically learn and improve from experience without being explicitly programmed. 
Machine learning focuses on the development of computer programs that can access data 
and use it to learn for themselves.

The process of learning begins with observations or data, such as examples, direct 
experience, or instruction, in order to look for patterns in data and make better 
decisions in the future based on the examples that we provide. The primary aim is to 
allow the computers to learn automatically without human intervention or assistance 
and adjust actions accordingly.

Types of Machine Learning
Machine learning algorithms are mainly divided into three categories:

1. Supervised Learning
Supervised learning is where you have input variables (x) and an output variable (Y) 
and you use an algorithm to learn the mapping function from the input to the output.
The goal is to approximate the mapping function so well that when you have new input 
data (x) that you can predict the output variables (Y) for that data.

2. Unsupervised Learning
Unsupervised learning is where you only have input data (X) and no corresponding output 
variables. The goal for unsupervised learning is to model the underlying structure or 
distribution in the data in order to learn more about the data.

3. Reinforcement Learning
Reinforcement learning is an area of machine learning concerned with how software agents 
ought to take actions in an environment in order to maximize the notion of cumulative reward.

Applications
Machine learning has numerous applications in various fields including:
- Healthcare: Disease prediction, drug discovery, personalized treatment
- Finance: Fraud detection, algorithmic trading, credit scoring
- E-commerce: Recommendation systems, price optimization
- Transportation: Autonomous vehicles, traffic prediction
- Manufacturing: Predictive maintenance, quality control

Conclusion
As technology continues to evolve, machine learning will play an increasingly important 
role in our daily lives, transforming industries and creating new opportunities for 
innovation and growth.
"""
    
    test_dir = Path("data/test_files")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    sample_file = test_dir / "sample_ml.txt"
    sample_file.write_text(sample_text.strip())
    
    print(f"✓ Created sample file: {sample_file}")
    print(f"  File size: {len(sample_text)} characters")
    
    return str(sample_file)


def main():
    """Main test function."""
    print_separator("Document Loader & Chunker Test Suite")
    
    # Create and test with sample text file
    sample_file = create_sample_text_file()
    
    # Test document loading
    text = test_document_loader(sample_file)
    
    if text:
        # Test text chunking
        test_chunker(text, chunk_size=500, chunk_overlap=50)
        
        # Test with different chunk sizes
        print("\n")
        test_chunker(text, chunk_size=300, chunk_overlap=30)
    
    # Test edge cases
    test_edge_cases()
    
    # Instructions for PDF testing
    print_separator("Testing with PDF Files")
    print("To test with a PDF file:")
    print("1. Place a PDF file in the 'data/test_files/' directory")
    print("2. Run the following code:")
    print()
    print("    from app.services.document_loader import load_document")
    print("    from app.services.chunker import chunk_text")
    print()
    print("    # Load PDF")
    print("    text = load_document('data/test_files/your_file.pdf')")
    print("    print(f'Loaded {len(text)} characters')")
    print()
    print("    # Chunk the text")
    print("    chunks = chunk_text(text, chunk_size=500, chunk_overlap=50)")
    print("    print(f'Created {len(chunks)} chunks')")
    print()
    print("    # Display chunks")
    print("    for i, chunk in enumerate(chunks[:3]):")
    print("        print(f'\\nChunk {i+1}:\\n{chunk}\\n')")
    print()
    
    print_separator("Tests Complete")


if __name__ == "__main__":
    main()
