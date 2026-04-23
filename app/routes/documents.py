"""
Document Routes
API endpoints for document upload, ingestion, and querying.
"""

import os
import tempfile
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel, Field

from app.services.document_loader import load_document, DocumentLoaderError
from app.services.chunker import chunk_text
from app.services.vector_store import VectorStore
from app.services.llm_service import LLMService


# Request/Response models
class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    question: str = Field(..., description="Question to answer", min_length=1)
    k: int = Field(4, description="Number of context chunks to retrieve", ge=1, le=10)
    collection_name: str = Field("documents", description="Vector store collection to search")


class Source(BaseModel):
    """Source document information."""
    text: str
    similarity_score: float
    metadata: dict


class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    answer: str
    sources: List[Source]
    model: str
    context_used: int
    usage: Optional[dict] = None


class UploadResponse(BaseModel):
    """Response model for upload endpoint."""
    filename: str
    chunks_created: int
    chunks_stored: int
    collection_name: str
    message: str


# Initialize router
router = APIRouter(prefix="/api/v1", tags=["documents"])

# Global vector store (initialized on first use)
_vector_store: Optional[VectorStore] = None
_llm_service: Optional[LLMService] = None


def get_vector_store(collection_name: str = "documents") -> VectorStore:
    """Get or create vector store instance."""
    global _vector_store
    # For simplicity, we're using a single global instance
    # In production, you might want to manage multiple collections
    if _vector_store is None:
        _vector_store = VectorStore(
            collection_name=collection_name,
            persist_directory="./chroma_db",
            use_openai_embeddings=True  # Using OpenAI for production
        )
    return _vector_store


def get_llm_service() -> LLMService:
    """Get or create LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService(
            model="gpt-3.5-turbo",
            temperature=0.7
        )
    return _llm_service


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="Document file (PDF, DOCX, or TXT)"),
    collection_name: str = Form("documents", description="Collection name for storage"),
    chunk_size: int = Form(500, description="Size of text chunks"),
    chunk_overlap: int = Form(50, description="Overlap between chunks")
):
    """
    Upload and ingest a document into the vector store.
    
    This endpoint:
    1. Accepts a file upload (PDF, DOCX, or TXT)
    2. Extracts text from the document
    3. Splits text into chunks
    4. Generates embeddings and stores in vector database
    5. Returns ingestion statistics
    
    Args:
        file: Document file to upload
        collection_name: Name of the vector store collection
        chunk_size: Size of each text chunk in characters
        chunk_overlap: Number of characters to overlap between chunks
        
    Returns:
        UploadResponse with ingestion details
    """
    # Validate file type
    allowed_extensions = {'.pdf', '.docx', '.txt'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Create a temporary file to save the upload
    temp_file = None
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Step 1: Extract text from document
        try:
            text = load_document(temp_file_path)
        except DocumentLoaderError as e:
            raise HTTPException(status_code=400, detail=f"Failed to load document: {str(e)}")
        
        # Step 2: Chunk the text
        try:
            chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to chunk text: {str(e)}")
        
        # Step 3: Prepare metadata for each chunk
        metadata = []
        for i, chunk in enumerate(chunks):
            # Calculate approximate page number (rough estimate)
            chars_per_page = 3000  # Rough estimate
            approx_page = (i * chunk_size) // chars_per_page + 1
            
            metadata.append({
                "source": file.filename,
                "filename": file.filename,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "page_number": approx_page,
                "chunk_size": len(chunk),
                "file_type": file_ext
            })
        
        # Step 4: Store in vector database
        try:
            vector_store = get_vector_store(collection_name)
            result = vector_store.add_documents(chunks, metadata=metadata)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to store in vector database: {str(e)}")
        
        return UploadResponse(
            filename=file.filename,
            chunks_created=len(chunks),
            chunks_stored=result['added_count'],
            collection_name=collection_name,
            message=f"Successfully ingested {file.filename} into {collection_name} collection"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except:
                pass


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Query documents using RAG (Retrieval-Augmented Generation).
    
    This endpoint:
    1. Takes a user question
    2. Retrieves relevant chunks from vector store
    3. Uses LLM with retrieved context to generate answer
    4. Returns answer with source citations
    
    Args:
        request: QueryRequest with question and parameters
        
    Returns:
        QueryResponse with answer and sources
    """
    try:
        # Step 1: Retrieve relevant chunks from vector store
        vector_store = get_vector_store(request.collection_name)
        
        # Check if collection has any documents
        if vector_store.collection.count() == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No documents found in collection '{request.collection_name}'. Please upload documents first."
            )
        
        search_results = vector_store.search(
            query=request.question,
            k=request.k
        )
        
        if not search_results:
            return QueryResponse(
                answer="I couldn't find any relevant information to answer your question.",
                sources=[],
                model="gpt-3.5-turbo",
                context_used=0
            )
        
        # Step 2: Use LLM to generate answer with RAG
        llm_service = get_llm_service()
        result = llm_service.answer_question(
            question=request.question,
            context_chunks=search_results
        )
        
        # Step 3: Format response
        sources = [
            Source(
                text=source['text'],
                similarity_score=source['similarity_score'],
                metadata=source.get('metadata', {})
            )
            for source in result['sources']
        ]
        
        return QueryResponse(
            answer=result['answer'],
            sources=sources,
            model=result['model'],
            context_used=result['context_used'],
            usage=result.get('usage')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/collections/{collection_name}/stats")
async def get_collection_stats(collection_name: str = "documents"):
    """
    Get statistics about a vector store collection.
    
    Args:
        collection_name: Name of the collection
        
    Returns:
        Collection statistics
    """
    try:
        vector_store = get_vector_store(collection_name)
        stats = vector_store.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.delete("/collections/{collection_name}")
async def clear_collection(collection_name: str = "documents"):
    """
    Clear all documents from a collection.
    
    Args:
        collection_name: Name of the collection to clear
        
    Returns:
        Confirmation message
    """
    try:
        vector_store = get_vector_store(collection_name)
        result = vector_store.clear_collection()
        return {
            "message": f"Cleared {result['deleted_count']} documents from {collection_name}",
            "deleted_count": result['deleted_count']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear collection: {str(e)}")
