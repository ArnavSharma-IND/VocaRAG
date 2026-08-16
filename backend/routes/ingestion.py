import logging
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from backend.models.schemas import (
    DocumentInfo,
    KnowledgeBaseStats,
    ReindexRequest,
    ChunkInfo
)
from backend.rag.ingestion import ingestion_manager
from backend.rag.retriever import vector_retriever

router = APIRouter(prefix="/api", tags=["Knowledge Base & Ingestion"])
logger = logging.getLogger(__name__)

@router.post("/ingest", response_model=DocumentInfo)
async def upload_document(file: UploadFile = File(...)):
    """Uploads and ingests a document (PDF, TXT, DOCX, MD)."""
    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        doc_info = ingestion_manager.ingest_document(
            name=file.filename,
            content_bytes=content,
            is_sample=False,
            auto_reindex=True
        )
        return doc_info
    except Exception as e:
        logger.error(f"Failed to ingest file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@router.post("/reindex", response_model=KnowledgeBaseStats)
async def reindex_knowledge_base(request: ReindexRequest):
    """Reindexes all documents using the selected chunking strategy and size parameters."""
    try:
        stats = ingestion_manager.reindex_all(
            strategy=request.chunk_strategy,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap
        )
        return stats
    except Exception as e:
        logger.error(f"Failed to reindex: {e}")
        raise HTTPException(status_code=500, detail=f"Reindexing failed: {str(e)}")

@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """Retrieves all indexed documents in the knowledge base."""
    return ingestion_manager.get_all_documents()

@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Deletes a document by ID and rebuilds vector index."""
    success = ingestion_manager.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"success": True, "message": f"Document '{doc_id}' deleted and knowledge base reindexed."}

@router.get("/chunks", response_model=List[ChunkInfo])
async def list_chunks(doc_id: Optional[str] = None, limit: int = 50):
    """Lists chunks for technical inspection."""
    all_chunks = vector_retriever.chunks
    if doc_id:
        all_chunks = [c for c in all_chunks if c.doc_id == doc_id]
    return all_chunks[:limit]
