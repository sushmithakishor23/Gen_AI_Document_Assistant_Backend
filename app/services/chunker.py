"""
Text Chunking Service
Splits text into manageable chunks using LangChain's RecursiveCharacterTextSplitter.
"""

from typing import List, Optional

# Try to import langchain text splitter, fall back to simple implementation
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter as LangChainSplitter
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


class SimpleTextChunker:
    """Simple fallback chunker when LangChain is not available."""
    
    def __init__(self, chunk_size: int, chunk_overlap: int, separators: List[str], **kwargs):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators
    
    def split_text(self, text: str) -> List[str]:
        """Simple text splitting."""
        if not text:
            return []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # If this is not the last chunk, try to break at a separator
            if end < len(text):
                # Look for the best separator within the chunk
                best_break = end
                for sep in self.separators:
                    if not sep:
                        continue
                    # Find the last occurrence of this separator before the end
                    pos = text.rfind(sep, start, end)
                    if pos > start:
                        best_break = pos + len(sep)
                        break
                end = best_break
            
            chunks.append(text[start:end])
            start = end - self.chunk_overlap
        
        return chunks


class TextChunker:
    """
    Service for chunking text into smaller, overlapping segments.
    
    Uses LangChain's RecursiveCharacterTextSplitter which attempts to split
    text on natural boundaries (paragraphs, sentences, words) while maintaining
    the specified chunk size.
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None,
        length_function: callable = len
    ):
        """
        Initialize the TextChunker.
        
        Args:
            chunk_size: Maximum size of each chunk in characters (default: 500)
            chunk_overlap: Number of characters to overlap between chunks (default: 50)
            separators: List of separators to use for splitting. If None, uses default.
            length_function: Function to measure chunk length (default: len)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Use default separators if none provided
        # These are ordered by preference: paragraph -> line -> sentence -> word -> character
        if separators is None:
            separators = [
                "\n\n",  # Paragraph breaks
                "\n",    # Line breaks
                ". ",    # Sentence endings
                "! ",    # Exclamation sentences
                "? ",    # Question sentences
                "; ",    # Semicolons
                ", ",    # Commas
                " ",     # Words
                ""       # Characters (fallback)
            ]
        
        # Initialize the text splitter (LangChain or fallback)
        if LANGCHAIN_AVAILABLE:
            self.splitter = LangChainSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=separators,
                length_function=length_function,
                is_separator_regex=False
            )
        else:
            self.splitter = SimpleTextChunker(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=separators
            )
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks.
        
        Args:
            text: The text to split into chunks
            
        Returns:
            List of text chunks
            
        Raises:
            ValueError: If text is empty or invalid
        """
        if not text or not isinstance(text, str):
            raise ValueError("Text must be a non-empty string")
        
        # Use the LangChain splitter
        chunks = self.splitter.split_text(text)
        
        return chunks
    
    def chunk_text_with_metadata(self, text: str, metadata: Optional[dict] = None) -> List[dict]:
        """
        Split text into chunks with metadata.
        
        Args:
            text: The text to split into chunks
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of dictionaries containing chunk text and metadata
            
        Raises:
            ValueError: If text is empty or invalid
        """
        if not text or not isinstance(text, str):
            raise ValueError("Text must be a non-empty string")
        
        chunks = self.chunk_text(text)
        
        # Create chunk objects with metadata
        chunk_objects = []
        for i, chunk in enumerate(chunks):
            chunk_obj = {
                "chunk_id": i,
                "text": chunk,
                "chunk_size": len(chunk),
                "total_chunks": len(chunks)
            }
            
            # Add custom metadata if provided
            if metadata:
                chunk_obj["metadata"] = metadata
            
            chunk_objects.append(chunk_obj)
        
        return chunk_objects
    
    def get_chunk_stats(self, chunks: List[str]) -> dict:
        """
        Get statistics about the chunks.
        
        Args:
            chunks: List of text chunks
            
        Returns:
            Dictionary containing chunk statistics
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "total_characters": 0,
                "average_chunk_size": 0,
                "min_chunk_size": 0,
                "max_chunk_size": 0
            }
        
        chunk_sizes = [len(chunk) for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "total_characters": sum(chunk_sizes),
            "average_chunk_size": sum(chunk_sizes) / len(chunks),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes)
        }


# Convenience function for quick usage
def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[str]:
    """
    Convenience function to chunk text with default settings.
    
    Args:
        text: The text to split into chunks
        chunk_size: Maximum size of each chunk (default: 500)
        chunk_overlap: Overlap between chunks (default: 50)
        
    Returns:
        List of text chunks
    """
    chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return chunker.chunk_text(text)
