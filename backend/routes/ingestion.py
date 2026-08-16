import logging
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from backend.models.schemas import DocumentInfo, KnowledgeBaseStats, ReindexRequest, ChunkInfo
from backend.rag.ingestion import ingestion_manager
from backend.rag.retriever import retriever_registry

router = APIRouter(prefix="/api", tags=["Ingestion & Documents"])
logger = logging.getLogger(__name__)

@router.post("/ingest", response_model=DocumentInfo)
async def ingest_document(
    file: UploadFile = File(...),
    collection: str = Form("enterprise")
):
    try:
        content_bytes = await file.read()
        doc_info = ingestion_manager.ingest_document(
            name=file.filename,
            content_bytes=content_bytes,
            is_sample=False,
            collection=collection,
            auto_reindex=True
        )
        return doc_info
    except Exception as e:
        logger.error(f"Error ingesting file {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process and index document: {str(e)}")

@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents(collection: Optional[str] = Query(None)):
    return ingestion_manager.get_all_documents(collection=collection)

@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, collection: str = Query("enterprise")):
    success = ingestion_manager.delete_document(doc_id, collection=collection)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"success": True, "message": f"Document {doc_id} deleted and index rebuilt."}

@router.post("/reindex", response_model=KnowledgeBaseStats)
async def reindex_corpus(req: ReindexRequest, collection: str = Query("enterprise")):
    stats = ingestion_manager.reindex_all(
        collection=collection,
        strategy=req.chunk_strategy,
        chunk_size=req.chunk_size,
        chunk_overlap=req.chunk_overlap
    )
    return stats

@router.get("/stats", response_model=KnowledgeBaseStats)
async def get_stats(collection: str = Query("enterprise")):
    return ingestion_manager.get_stats(collection=collection)

@router.get("/chunks", response_model=List[ChunkInfo])
async def list_chunks(
    doc_id: Optional[str] = Query(None),
    collection: str = Query("enterprise"),
    limit: int = Query(50, le=200)
):
    retriever = retriever_registry.get_retriever(collection)
    chunks = retriever.chunks
    if doc_id:
        chunks = [c for c in chunks if c.doc_id == doc_id]
    return chunks[:limit]
