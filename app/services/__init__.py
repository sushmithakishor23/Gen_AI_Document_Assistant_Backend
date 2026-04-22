"""Services package for document processing."""

from .document_loader import (
    DocumentLoader,
    load_document,
    DocumentLoaderError,
    EmptyFileError,
    CorruptedFileError,
    UnsupportedFileTypeError,
    ScannedPDFError
)
from .chunker import TextChunker, chunk_text
from .embeddings import (
    EmbeddingsService,
    EmbeddingProvider,
    create_embeddings_service,
    embed_text,
    embed_texts
)
from .vector_store import VectorStore, create_vector_store

__all__ = [
    'DocumentLoader',
    'load_document',
    'DocumentLoaderError',
    'EmptyFileError',
    'CorruptedFileError',
    'UnsupportedFileTypeError',
    'ScannedPDFError',
    'TextChunker',
    'chunk_text',
    'EmbeddingsService',
    'EmbeddingProvider',
    'create_embeddings_service',
    'embed_text',
    'embed_texts',
    'VectorStore',
    'create_vector_store'
]
