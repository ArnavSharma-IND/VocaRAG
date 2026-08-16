import logging
from fastapi import APIRouter, HTTPException
from backend.models.schemas import QueryRequest, AskResponse
from backend.rag.pipeline import rag_pipeline

router = APIRouter(prefix="/api", tags=["Ask"])
logger = logging.getLogger(__name__)

@router.post("/ask", response_model=AskResponse)
async def ask_question(request: QueryRequest):
    """
    Core Voice-to-Answer RAG endpoint.
    Accepts text or voice transcript, executes guardrails, FAISS retrieval, and grounded answer generation.
    Supports collection-based routing ('enterprise' or 'msmarco').
    """
    try:
        response = await rag_pipeline.process_query(request)
        return response
    except Exception as e:
        logger.error(f"Unhandled error during /api/ask pipeline: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "RAG_PIPELINE_ERROR",
                "message": f"Pipeline processing encountered an issue: {str(e)}"
            }
        )
