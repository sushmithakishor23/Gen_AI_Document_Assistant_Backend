"""
Document Routes
API endpoints for document upload, ingestion, and querying.
"""

import os
import tempfile
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.services.document_loader import load_document, DocumentLoaderError
from app.services.chunker import chunk_text
from app.services.vector_store import VectorStore
from app.services.llm_service import LLMService
from app.database import get_db
from app.models import Document, Collection


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


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message text content")


class ChatRequest(BaseModel):
    """Chat request model with conversation history."""
    question: str = Field(..., description="User question", min_length=1)
    chat_history: List[ChatMessage] = Field(default=[], description="Previous conversation messages")
    collection_id: Optional[str] = Field(None, description="Optional collection ID for context")


class UploadResponse(BaseModel):
    """Response model for upload endpoint."""
    filename: str
    chunks_created: int
    chunks_stored: int
    collection_name: str
    message: str
    document_id: int


class DocumentInfo(BaseModel):
    """Document information model."""
    id: int
    filename: str
    file_type: str
    file_size: int
    collection_id: int
    collection_name: str
    chunks_count: int
    chunk_size: int
    chunk_overlap: int
    created_at: datetime


class CollectionInfo(BaseModel):
    """Collection information model."""
    id: int
    name: str
    description: Optional[str]
    document_count: int
    created_at: datetime
    updated_at: datetime


# Initialize router
router = APIRouter(prefix="/api/v1", tags=["documents"])

# Global vector stores (initialized on first use per collection)
_vector_stores: Dict[str, VectorStore] = {}
_llm_service: Optional[LLMService] = None


def get_vector_store(collection_name: str = "documents") -> VectorStore:
    """Get or create vector store instance for the specified collection."""
    global _vector_stores
    
    # Create a new VectorStore for each unique collection name
    if collection_name not in _vector_stores:
        _vector_stores[collection_name] = VectorStore(
            collection_name=collection_name,
            persist_directory="./chroma_db",
            use_openai_embeddings=True  # Using OpenAI for production
        )
    
    return _vector_stores[collection_name]


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
    chunk_size: int = Form(500, ge=100, le=5000, description="Size of text chunks (100-5000 characters)"),
    chunk_overlap: int = Form(50, ge=0, le=500, description="Overlap between chunks (0-500 characters)"),
    db: Session = Depends(get_db)
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
        chunk_size: Size of each text chunk in characters (100-5000)
        chunk_overlap: Number of characters to overlap between chunks (0-500, must be < chunk_size)
        
    Returns:
        UploadResponse with ingestion details
    """
    # Validate chunk parameters
    if chunk_overlap >= chunk_size:
        raise HTTPException(
            status_code=400,
            detail=f"chunk_overlap ({chunk_overlap}) must be less than chunk_size ({chunk_size})"
        )
    
    # Validate file type
    allowed_extensions = {'.pdf', '.docx', '.txt'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Create a temporary file to save the upload
    # Initialize to None so cleanup in finally block works even if error occurs early
    temp_file_path = None
    
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file_path = temp_file.name
            
            # Read file in chunks to validate size without loading all into memory at once
            MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
            content = bytearray()
            buffer_size = 8192  # 8KB read buffer (renamed to avoid shadowing chunk_size param)
            total_size = 0
            
            while True:
                chunk = await file.read(buffer_size)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size is {MAX_FILE_SIZE // 1024 // 1024}MB. Your file is approximately {total_size // 1024 // 1024}MB."
                    )
                content.extend(chunk)
            
            # Write the validated content to temp file
            temp_file.write(bytes(content))
        
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
        # Generate unique prefix for this document's chunks
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        doc_prefix = f"doc_{timestamp}"
        
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
                "file_type": file_ext,
                "doc_prefix": doc_prefix
            })
        
        # Step 4: Ensure collection exists in database
        db_collection = db.query(Collection).filter(Collection.name == collection_name).first()
        if not db_collection:
            db_collection = Collection(
                name=collection_name,
                description=f"Auto-created collection: {collection_name}"
            )
            db.add(db_collection)
            db.commit()
            db.refresh(db_collection)
        
        # Step 5: Store in vector database
        try:
            vector_store = get_vector_store(collection_name)
            # Generate IDs with the document prefix
            chunk_ids = [f"{doc_prefix}_{i}" for i in range(len(chunks))]
            result = vector_store.add_documents(chunks, metadata=metadata, ids=chunk_ids)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to store in vector database: {str(e)}")
        
        # Step 6: Save document metadata to database
        db_document = Document(
            filename=file.filename,
            file_type=file_ext,
            file_size=total_size,
            collection_id=db_collection.id,
            chunks_count=len(chunks),
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            vector_ids_prefix=doc_prefix
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        return UploadResponse(
            filename=file.filename,
            chunks_created=len(chunks),
            chunks_stored=result['added_count'],
            collection_name=collection_name,
            message=f"Successfully ingested {file.filename} into {collection_name} collection",
            document_id=db_document.id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        # Always clean up temporary file, even if an error occurred
        # This ensures we don't leave orphaned temp files on the server
        if temp_file_path:
            if os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    # Log but don't raise - cleanup failure shouldn't break the response
                    print(f"Warning: Failed to delete temporary file {temp_file_path}: {e}")
            else:
                # File was already cleaned up or never created
                pass


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: ChatRequest):
    """
    Query documents using RAG (Retrieval-Augmented Generation) with chat history support.
    
    This endpoint:
    1. Takes a user question and optional chat history
    2. Retrieves top 4 chunks from vector store
    3. Passes last 5 messages from chat_history to LLM
    4. Returns answer with source citations
    
    Args:
        request: ChatRequest with question, chat_history, and optional collection_id
        
    Returns:
        QueryResponse with answer and sources
    """
    try:
        # Use collection_id or default to "documents"
        collection_name = request.collection_id or "documents"
        
        # Step 1: Retrieve top 4 chunks from vector store
        vector_store = get_vector_store(collection_name)
        
        # Check if collection has any documents
        if vector_store.collection.count() == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No documents found in collection '{collection_name}'. Please upload documents first."
            )
        
        search_results = vector_store.search(
            query=request.question,
            k=4  # Retrieve top 4 chunks
        )
        
        if not search_results:
            return QueryResponse(
                answer="I don't know based on the provided documents.",
                sources=[],
                model="gpt-3.5-turbo",
                context_used=0
            )
        
        # Step 2: Convert ChatMessage objects to dict format and get last 5 messages
        chat_history_dict = None
        if request.chat_history:
            # Take only last 5 messages from chat history
            last_5_messages = request.chat_history[-5:]
            chat_history_dict = [
                {"role": msg.role, "content": msg.content}
                for msg in last_5_messages
            ]
        
        # Step 3: Use LLM to generate answer with RAG and chat history
        llm_service = get_llm_service()
        result = llm_service.answer_question(
            question=request.question,
            context_chunks=search_results,
            chat_history=chat_history_dict
        )
        
        # Step 4: Format response with source chunks
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


@router.post("/chat", response_model=QueryResponse)
async def chat_with_documents(request: ChatRequest):
    """
    Chat with documents using RAG with conversation history support.
    
    This endpoint:
    1. Takes a user question and chat history
    2. Retrieves relevant chunks from vector store
    3. Uses LLM with retrieved context and chat history to generate answer
    4. Returns answer with source citations
    
    Args:
        request: ChatRequest with question, chat history, and optional collection ID
        
    Returns:
        QueryResponse with answer and sources
    """
    try:
        # Use collection_id or default to "documents"
        collection_name = request.collection_id or "documents"
        
        # Step 1: Retrieve relevant chunks from vector store
        vector_store = get_vector_store(collection_name)
        
        # Check if collection has any documents
        if vector_store.collection.count() == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No documents found in collection '{collection_name}'. Please upload documents first."
            )
        
        search_results = vector_store.search(
            query=request.question,
            k=4  # Default to 4 chunks for chat
        )
        
        if not search_results:
            return QueryResponse(
                answer="I don't know based on the provided documents.",
                sources=[],
                model="gpt-3.5-turbo",
                context_used=0
            )
        
        # Step 2: Convert ChatMessage objects to dict format and get last 5 messages
        chat_history_dict = None
        if request.chat_history:
            # Take only last 5 messages from chat history
            last_5_messages = request.chat_history[-5:]
            chat_history_dict = [
                {"role": msg.role, "content": msg.content}
                for msg in last_5_messages
            ]
        
        # Step 3: Use LLM to generate answer with RAG and chat history
        llm_service = get_llm_service()
        result = llm_service.answer_question(
            question=request.question,
            context_chunks=search_results,
            chat_history=chat_history_dict
        )
        
        # Step 4: Format response
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
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


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


@router.get("/documents", response_model=List[DocumentInfo])
async def get_documents(
    collection_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all documents, optionally filtered by collection.
    
    Args:
        collection_name: Optional collection name to filter by
        db: Database session
        
    Returns:
        List of documents with metadata
    """
    try:
        query = db.query(Document)
        
        # Filter by collection if specified
        if collection_name:
            collection = db.query(Collection).filter(Collection.name == collection_name).first()
            if not collection:
                raise HTTPException(status_code=404, detail=f"Collection '{collection_name}' not found")
            query = query.filter(Document.collection_id == collection.id)
        
        documents = query.order_by(Document.created_at.desc()).all()
        
        # Convert to response models
        return [
            DocumentInfo(
                id=doc.id,
                filename=doc.filename,
                file_type=doc.file_type,
                file_size=doc.file_size,
                collection_id=doc.collection_id,
                collection_name=doc.collection.name,
                chunks_count=doc.chunks_count,
                chunk_size=doc.chunk_size,
                chunk_overlap=doc.chunk_overlap,
                created_at=doc.created_at
            )
            for doc in documents
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a document and all its chunks from both database and vector store.
    
    Args:
        document_id: ID of the document to delete
        db: Database session
        
    Returns:
        Confirmation message
    """
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found")
        
        # Delete chunks from vector store
        collection_name = document.collection.name
        vector_store = get_vector_store(collection_name)
        
        try:
            # Delete all chunks with this document's prefix
            result = vector_store.delete_documents_by_prefix(document.vector_ids_prefix)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete document chunks from vector store: {str(e)}"
            )
        
        # Delete from database
        db.delete(document)
        db.commit()
        
        return {
            "message": f"Successfully deleted document '{document.filename}'",
            "document_id": document_id,
            "filename": document.filename,
            "chunks_deleted": result['deleted_count']
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@router.get("/collections", response_model=List[CollectionInfo])
async def get_collections(db: Session = Depends(get_db)):
    """
    Get all collections with their document counts.
    
    Args:
        db: Database session
        
    Returns:
        List of collections
    """
    try:
        collections = db.query(Collection).order_by(Collection.created_at.desc()).all()
        
        return [
            CollectionInfo(
                id=col.id,
                name=col.name,
                description=col.description,
                document_count=len(col.documents),
                created_at=col.created_at,
                updated_at=col.updated_at
            )
            for col in collections
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve collections: {str(e)}")


@router.post("/collections", response_model=CollectionInfo)
async def create_collection(
    name: str = Form(..., description="Collection name"),
    description: Optional[str] = Form(None, description="Optional description"),
    db: Session = Depends(get_db)
):
    """
    Create a new collection/session.
    
    Args:
        name: Collection name
        description: Optional description
        db: Database session
        
    Returns:
        Created collection information
    """
    try:
        # Check if collection already exists
        existing = db.query(Collection).filter(Collection.name == name).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Collection '{name}' already exists")
        
        # Create new collection
        collection = Collection(
            name=name,
            description=description
        )
        db.add(collection)
        db.commit()
        db.refresh(collection)
        
        return CollectionInfo(
            id=collection.id,
            name=collection.name,
            description=collection.description,
            document_count=0,
            created_at=collection.created_at,
            updated_at=collection.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create collection: {str(e)}")

