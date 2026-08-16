import logging
from datetime import datetime
from fastapi import APIRouter
from backend.config import settings
from backend.models.schemas import SystemStatus, KnowledgeBaseStats
from backend.rag.embeddings import embedding_engine
from backend.rag.retriever import vector_retriever
from backend.rag.ingestion import ingestion_manager
from backend.rag.generator import llm_generator

router = APIRouter(prefix="/api", tags=["System Status & Health"])
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "VocaRAG API Core",
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/stats", response_model=KnowledgeBaseStats)
async def get_stats():
    return ingestion_manager.get_stats()

@router.get("/system", response_model=SystemStatus)
async def get_system_status():
    mode, provider_name = llm_generator.get_active_mode()
    stats = ingestion_manager.get_stats()

    optimizations = [
        "In-Memory MD5 Embedding Cache",
        "FAISS IndexFlatIP Normalized Cosine Search",
        "Multi-Tier Guardrail Abstention (Zero Unnecessary LLM Calls)",
        "Async Non-Blocking FastAPI Endpoints",
        "Exponential Backoff Retry on Upstream 429/500s",
        "Sub-20ms Deterministic Fallback Mode"
    ]

    return SystemStatus(
        voice_engine_status="Ready (Native Web Speech API + Audio Waveform Analyser)",
        embedding_model_status="Ready",
        embedding_model_name=settings.EMBEDDING_MODEL_NAME,
        vector_store_status="Ready (FAISS IndexFlatIP)" if vector_retriever.use_faiss else "Ready (NumPy Cosine Engine)",
        vector_count=vector_retriever.total_chunks,
        vector_dimension=vector_retriever.dimension,
        llm_provider=provider_name,
        llm_provider_mode=mode,
        llm_model=settings.GEMINI_MODEL if mode == "Live" and settings.GEMINI_API_KEY else (settings.OPENAI_MODEL if mode == "Live" else "Deterministic Synthesizer"),
        knowledge_base_status="Indexed & Ready" if stats.index_ready else "Empty",
        documents_count=stats.documents_count,
        chunks_count=stats.chunks_count,
        api_status="Healthy",
        optimizations=optimizations,
        environment="production-ready",
        server_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    )
