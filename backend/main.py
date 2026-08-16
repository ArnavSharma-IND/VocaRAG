import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.rag.embeddings import embedding_engine
from backend.rag.ingestion import ingestion_manager
from backend.rag.retriever import vector_retriever
from backend.models.schemas import QueryRequest
from backend.routes import ask, ingestion, retrieval, benchmark, guardrails, system

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("vocarag.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("==================================================")
    logger.info("Initializing VocaRAG Core Backend...")
    logger.info("==================================================")
    
    # 1. Warm up embedding engine
    embedding_engine.initialize()

    # 2. Seed / load knowledge base documents
    ingestion_manager.load_sample_knowledge_base()

    stats = ingestion_manager.get_stats()
    faiss_vectors = vector_retriever.total_chunks
    
    # Print the exact requested diagnostic logs
    print(f"[KB] Documents loaded: {stats.documents_count}")
    print(f"[KB] Chunks created: {stats.chunks_count}")
    print(f"[KB] Embeddings generated: {stats.embeddings_count}")
    print(f"[KB] FAISS vectors: {faiss_vectors}")
    print(f"[KB] Embedding dimension: {stats.embedding_dimension}")
    
    logger.info(f"[KB] Documents loaded: {stats.documents_count}")
    logger.info(f"[KB] Chunks created: {stats.chunks_count}")
    logger.info(f"[KB] Embeddings generated: {stats.embeddings_count}")
    logger.info(f"[KB] FAISS vectors: {faiss_vectors}")
    logger.info(f"[KB] Embedding dimension: {stats.embedding_dimension}")
    
    if stats.documents_count == 0 or stats.chunks_count == 0 or faiss_vectors == 0:
        logger.error("CRITICAL: Vector store is empty after initialization!")
    else:
        logger.info("VocaRAG RAG Vector Engine is online and fully populated.")
    
    yield
    
    logger.info("Shutting down VocaRAG backend.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Voice-Enabled Retrieval Augmented Generation API — Hackathon Task #2",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(ask.router)
app.include_router(ingestion.router)
app.include_router(retrieval.router)
app.include_router(benchmark.router)
app.include_router(guardrails.router)
app.include_router(system.router)

# Debug endpoints
@app.get("/api/debug/rag")
async def debug_rag():
    stats = ingestion_manager.get_stats()
    return {
        "documents": stats.documents_count,
        "chunks": stats.chunks_count,
        "vectors": vector_retriever.total_chunks,
        "embedding_dimension": stats.embedding_dimension,
        "index_ready": vector_retriever.is_indexed
    }

@app.post("/api/debug/retrieval")
async def debug_retrieval(req: QueryRequest):
    qv = embedding_engine.embed_query(req.query.strip())
    raw_results = vector_retriever.search(
        qv,
        top_k=req.top_k or settings.DEFAULT_TOP_K,
        threshold=req.threshold if req.threshold is not None else 0.0
    )
    return {
        "query": req.query,
        "raw_results_count": len(raw_results),
        "results": [r.model_dump() for r in raw_results]
    }

@app.get("/")
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "tagline": settings.TAGLINE,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "health_url": "/api/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
