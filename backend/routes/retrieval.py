import time
import logging
from fastapi import APIRouter, HTTPException
from backend.models.schemas import RetrievalSearchRequest, RetrievalSearchResult
from backend.rag.embeddings import embedding_engine
from backend.rag.retriever import vector_retriever

router = APIRouter(prefix="/api/retrieval", tags=["Retrieval Engine"])
logger = logging.getLogger(__name__)

@router.post("/search", response_model=RetrievalSearchResult)
async def search_retrieval(req: RetrievalSearchRequest):
    """
    Direct retrieval sandbox endpoint.
    Performs vector similarity search against the FAISS index without running LLM generation.
    """
    t0 = time.perf_counter()
    try:
        query_vec = embedding_engine.embed_query(req.query)
        sources = vector_retriever.search(query_vec, top_k=req.top_k, threshold=req.threshold)
        explanation = vector_retriever.explain_retrieval(req.query, sources)
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)

        return RetrievalSearchResult(
            query=req.query,
            total_matches=len(sources),
            results=sources,
            latency_ms=latency_ms,
            explanation=explanation
        )
    except Exception as e:
        logger.error(f"Retrieval search error: {e}")
        raise HTTPException(status_code=500, detail=f"Retrieval search failed: {str(e)}")

@router.get("")
async def get_retrieval_status():
    """Retrieves current vector store statistics and indexing status."""
    return {
        "engine": "FAISS IndexFlatIP (Cosine Similarity)" if vector_retriever.use_faiss else "Optimized Vector Dot Product",
        "total_vectors": vector_retriever.total_chunks,
        "dimension": vector_retriever.dimension,
        "is_ready": vector_retriever.is_indexed
    }
