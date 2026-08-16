from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class SourceItem(BaseModel):
    id: str
    doc_id: str
    doc_name: str
    chunk_index: int
    content: str
    similarity: float
    relevance_tier: str = "Medium" # High | Medium | Low
    source_type: str = "document" # general_knowledge | sample_policy | user_upload
    category_label: str = "DOCUMENT" # GENERAL KNOWLEDGE | POLICY | DOCUMENT
    metadata: Dict[str, Any] = Field(default_factory=dict)

class LatencyBreakdown(BaseModel):
    voice_stt_ms: Optional[float] = None
    preprocessing_ms: float = 0.0
    guardrail_ms: float = 0.0
    embedding_ms: float = 0.0
    retrieval_ms: float = 0.0
    prompt_construction_ms: float = 0.0
    generation_ms: float = 0.0
    total_rag_ms: float = 0.0
    total_pipeline_ms: float = 0.0

class GuardrailInfo(BaseModel):
    passed: bool = True
    flagged_type: Optional[str] = None # PROMPT_INJECTION | OUT_OF_SCOPE | INSUFFICIENT_EVIDENCE | None
    reason: Optional[str] = None
    abstained: bool = False

class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = None
    threshold: Optional[float] = None
    chunk_strategy: Optional[str] = None
    voice_latency_ms: Optional[float] = None
    override_provider: Optional[str] = None

class AskResponse(BaseModel):
    query: str
    answer: str
    grounded: bool
    abstained: bool
    confidence: float
    sources: List[SourceItem] = Field(default_factory=list)
    latency: LatencyBreakdown
    guardrails: GuardrailInfo
    mode: str = "Live" # Live | Demo
    retrieval_explanation: Optional[str] = None

class DocumentInfo(BaseModel):
    id: str
    name: str
    size_bytes: int
    file_type: str
    chunks_count: int
    uploaded_at: str
    is_sample: bool = False
    source_type: str = "sample_policy" # general_knowledge | sample_policy | user_upload
    category_badge: str = "SAMPLE" # GENERAL | SAMPLE | UPLOAD

class ChunkInfo(BaseModel):
    id: str
    doc_id: str
    doc_name: str
    chunk_index: int
    content: str
    char_count: int
    metadata: Dict[str, Any] = Field(default_factory=dict)

class KnowledgeBaseStats(BaseModel):
    documents_count: int
    chunks_count: int
    embeddings_count: int
    chunking_strategy: str
    chunk_size: int
    chunk_overlap: int
    last_indexed_at: Optional[str]
    embedding_dimension: int
    index_ready: bool

class ReindexRequest(BaseModel):
    chunk_strategy: str = "recursive"
    chunk_size: int = 450
    chunk_overlap: int = 80

class RetrievalSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    threshold: float = 0.25

class RetrievalSearchResult(BaseModel):
    query: str
    total_matches: int
    results: List[SourceItem]
    latency_ms: float
    explanation: str

class BenchmarkQueryRun(BaseModel):
    id: str
    query: str
    category: str
    retrieval_latency_ms: float
    generation_latency_ms: float
    total_latency_ms: float
    success: bool
    confidence: float
    abstained: bool
    grounded: bool
    sources_count: int
    answer_preview: str
    timestamp: str

class BenchmarkSummary(BaseModel):
    total_queries: int
    successful_queries: int
    p50_total_ms: float
    p70_total_ms: float
    p100_total_ms: float
    avg_total_ms: float
    min_total_ms: float
    max_total_ms: float
    p50_retrieval_ms: float
    p70_retrieval_ms: float
    p100_retrieval_ms: float
    p50_generation_ms: float
    p70_generation_ms: float
    p100_generation_ms: float
    target_ms: float = 200.0
    meets_target: bool
    runs: List[BenchmarkQueryRun] = Field(default_factory=list)

class GuardrailCheckRequest(BaseModel):
    query: str

class GuardrailCheckResponse(BaseModel):
    query: str
    passed: bool
    flagged_type: Optional[str] = None
    reason: Optional[str] = None
    risk_level: str = "LOW" # LOW | MEDIUM | HIGH
    recommended_action: str = "ALLOW" # ALLOW | BLOCK | ABSTAIN

class SystemStatus(BaseModel):
    voice_engine_status: str
    embedding_model_status: str
    embedding_model_name: str
    vector_store_status: str
    vector_count: int
    vector_dimension: int
    llm_provider: str
    llm_provider_mode: str
    llm_model: str
    knowledge_base_status: str
    documents_count: int
    chunks_count: int
    api_status: str
    optimizations: List[str]
    environment: str = "production-ready"
    server_time: str
