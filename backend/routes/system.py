from datetime import datetime, timezone
from fastapi import APIRouter
from backend.models.schemas import SystemStatus
from backend.config import settings
from backend.rag.embeddings import embedding_engine
from backend.rag.ingestion import ingestion_manager
from backend.rag.retriever import retriever_registry
from backend.rag.generator import llm_generator
from backend.rag.stt import sarvam_stt

router = APIRouter(prefix="/api", tags=["System"])

@router.get("/system", response_model=SystemStatus)
async def get_system_status():
    mode, provider_info = llm_generator.get_active_mode()
    ent_stats = ingestion_manager.get_stats("enterprise")
    msm_stats = ingestion_manager.get_stats("msmarco")
    total_docs = ent_stats.documents_count + msm_stats.documents_count
    total_chunks = ent_stats.chunks_count + msm_stats.chunks_count
    total_vectors = ent_stats.embeddings_count + msm_stats.embeddings_count

    return SystemStatus(
        voice_engine_status="Ready" if sarvam_stt.is_configured else "Demo (Sarvam key required for live voice)",
        embedding_model_status="Online" if embedding_engine.is_ready else "Initializing",
        embedding_model_name=embedding_engine.model_name,
        vector_store_status="Indexed (Dual Collections)" if (ent_stats.index_ready or msm_stats.index_ready) else "Empty",
        vector_count=total_vectors,
        vector_dimension=embedding_engine.dimension,
        llm_provider=settings.LLM_PROVIDER.upper(),
        llm_provider_mode=mode,
        llm_model=provider_info,
        knowledge_base_status="Loaded" if total_docs > 0 else "Empty",
        documents_count=total_docs,
        chunks_count=total_chunks,
        api_status="Operational",
        optimizations=[
            "Sarvam AI Saaras v3 Multilingual STT (23 Indic Languages)",
            "Dual FAISS IndexFlatIP (Enterprise + MSMARCO-XI Collections)",
            "Paraphrase-Multilingual-MPNet-Base-v2 (768-dim Indic Dense Embeddings)",
            "Four Chunking Strategies (Fixed, Sentence, Recursive, Semantic)",
            "Groq LPU Fast-Path Inference (sub-250ms Grounded Generation)",
            "Two-Sided Guardrails: Injection Filter + Evidence Threshold + Post-Gen Groundedness"
        ],
        environment="production-ready",
        server_time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        stt_provider="sarvam",
        stt_configured=sarvam_stt.is_configured,
        active_collection=settings.DEFAULT_COLLECTION
    )

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "llm_mode": llm_generator.get_active_mode()[0],
        "stt_configured": sarvam_stt.is_configured
    }
