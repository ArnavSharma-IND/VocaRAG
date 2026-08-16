import time
import logging
from fastapi import APIRouter
from backend.models.schemas import RetrievalSearchRequest, RetrievalSearchResult
from backend.rag.embeddings import embedding_engine
from backend.rag.retriever import retriever_registry

router = APIRouter(prefix="/api/retrieval", tags=["Retrieval Lab"])
logger = logging.getLogger(__name__)

@router.post("/search", response_model=RetrievalSearchResult)
async def search_retrieval(req: RetrievalSearchRequest):
    t0 = time.perf_counter()
    qv = embedding_engine.embed_query(req.query.strip())
    collection = req.collection or "enterprise"
    retriever = retriever_registry.get_retriever(collection)
    sources = retriever.search(
        qv,
        top_k=req.top_k,
        threshold=req.threshold
    )
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    explanation = retriever.explain_retrieval(req.query, sources)

    return RetrievalSearchResult(
        query=req.query,
        total_matches=len(sources),
        results=sources,
        latency_ms=latency_ms,
        explanation=explanation
    )
