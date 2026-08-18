import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from backend.config import settings
from backend.rag.embeddings import embedding_engine
from backend.rag.ingestion import ingestion_manager
from backend.rag.retriever import retriever_registry
from backend.models.schemas import QueryRequest
from backend.routes import ask, ingestion, retrieval, benchmark, guardrails, system, stt, tts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("vocarag.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("==================================================")
    logger.info("Initializing VocaRAG Core Backend v2.1...")
    logger.info("==================================================")
    
    # 1. Warm up embedding engine
    embedding_engine.initialize()

    # 2. Seed / load enterprise sample knowledge base
    ingestion_manager.load_sample_knowledge_base()

    # 3. Seed / load MSMARCO-XI Indic multilingual dataset
    if settings.MSMARCO_ENABLED:
        try:
            ingestion_manager.load_msmarco_knowledge_base()
        except Exception as e:
            logger.error(f"Error loading MSMARCO-XI dataset: {e}. Enterprise collection remains operational.")

    ent_stats = ingestion_manager.get_stats("enterprise")
    msm_stats = ingestion_manager.get_stats("msmarco")
    
    print(f"[KB] Enterprise Docs: {ent_stats.documents_count}, Chunks: {ent_stats.chunks_count}, Vectors: {ent_stats.embeddings_count}")
    print(f"[KB] MSMARCO-XI Docs: {msm_stats.documents_count}, Chunks: {msm_stats.chunks_count}, Vectors: {msm_stats.embeddings_count}")
    print(f"[KB] Embedding model: {embedding_engine.model_name} (dim: {embedding_engine.dimension})")
    
    logger.info("VocaRAG Dual Vector Engine is online and fully populated.")
    
    yield
    
    logger.info("Shutting down VocaRAG backend.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Voice-Enabled Multilingual Retrieval Augmented Generation API — Hackathon Task #2",
    version=settings.VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(ask.router)
app.include_router(stt.router)
app.include_router(tts.router)
app.include_router(ingestion.router)
app.include_router(retrieval.router)
app.include_router(benchmark.router)
app.include_router(guardrails.router)
app.include_router(system.router)

@app.get("/api/debug/rag")
async def debug_rag(collection: str = "msmarco"):
    stats = ingestion_manager.get_stats(collection)
    retriever = retriever_registry.get_retriever(collection)
    return {
        "collection": collection,
        "documents": stats.documents_count,
        "chunks": stats.chunks_count,
        "vectors": retriever.total_chunks,
        "embedding_dimension": stats.embedding_dimension,
        "embedding_model": embedding_engine.model_name,
        "index_ready": retriever.is_indexed
    }


# Mount Pre-built Frontend SPA (Single-Container Fullstack Deployment)
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="static_assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Exclude /api routes and docs
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            return None
        target_file = FRONTEND_DIST / full_path
        if target_file.is_file():
            return FileResponse(target_file)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
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
