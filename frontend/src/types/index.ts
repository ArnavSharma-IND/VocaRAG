export interface SourceItem {
  id: string;
  doc_id: string;
  doc_name: string;
  chunk_index: number;
  content: string;
  similarity: number;
  relevance_tier: 'High' | 'Medium' | 'Low';
  source_type: 'general_knowledge' | 'sample_policy' | 'user_upload' | 'msmarco_xi' | string;
  category_label: string;
  metadata: Record<string, any>;
}

export interface LatencyBreakdown {
  voice_stt_ms?: number | null;
  preprocessing_ms: number;
  guardrail_ms: number;
  embedding_ms: number;
  retrieval_ms: number;
  prompt_construction_ms: number;
  generation_ms: number;
  groundedness_check_ms?: number;
  total_rag_ms: number;
  total_pipeline_ms: number;
}

export interface GuardrailInfo {
  passed: boolean;
  flagged_type?: string | null;
  reason?: string | null;
  abstained: boolean;
}

export interface AskResponse {
  query: string;
  answer: string;
  grounded: boolean;
  abstained: boolean;
  confidence: number;
  groundedness_score?: number | null;
  sources: SourceItem[];
  latency: LatencyBreakdown;
  guardrails: GuardrailInfo;
  mode: string;
  retrieval_explanation?: string | null;
}

export interface DocumentInfo {
  id: string;
  name: string;
  size_bytes: number;
  file_type: string;
  chunks_count: number;
  uploaded_at: string;
  is_sample: boolean;
  source_type: string;
  category_badge: string;
  language?: string | null;
  collection: string;
}

export interface ChunkInfo {
  id: string;
  doc_id: string;
  doc_name: string;
  chunk_index: number;
  content: string;
  char_count: number;
  metadata: Record<string, any>;
}

export interface KnowledgeBaseStats {
  documents_count: number;
  chunks_count: number;
  embeddings_count: number;
  chunking_strategy: string;
  chunk_size: number;
  chunk_overlap: number;
  last_indexed_at?: string | null;
  embedding_dimension: number;
  index_ready: boolean;
  collection: string;
}

export interface ReindexRequest {
  chunk_strategy: 'fixed' | 'sentence' | 'recursive' | 'semantic' | string;
  chunk_size: number;
  chunk_overlap: number;
}

export interface RetrievalSearchResult {
  query: string;
  total_matches: number;
  results: SourceItem[];
  latency_ms: number;
  explanation: string;
}

export interface BenchmarkQueryRun {
  id: string;
  query: string;
  category: string;
  retrieval_latency_ms: number;
  generation_latency_ms: number;
  total_latency_ms: number;
  success: boolean;
  confidence: number;
  abstained: boolean;
  grounded: boolean;
  sources_count: number;
  answer_preview: string;
  timestamp: string;
}

export interface IREvalResult {
  total_queries: number;
  recall_at_1: number;
  recall_at_3: number;
  recall_at_5: number;
  recall_at_10: number;
  mrr: number;
  avg_retrieval_latency_ms: number;
  per_language: Record<string, {
    total_queries: number;
    recall_at_1: number;
    recall_at_5: number;
    recall_at_10: number;
    mrr: number;
  }>;
  evaluated_at: string;
}

export interface BenchmarkSummary {
  collection: string;
  total_queries: number;
  successful_queries: number;
  p50_total_ms: number;
  p70_total_ms: number;
  p100_total_ms: number;
  avg_total_ms: number;
  min_total_ms: number;
  max_total_ms: number;
  p50_retrieval_ms: number;
  p70_retrieval_ms: number;
  p100_retrieval_ms: number;
  p50_generation_ms: number;
  p70_generation_ms: number;
  p100_generation_ms: number;
  target_ms: number;
  meets_retrieval_target: boolean;
  meets_e2e_target: boolean;
  meets_target: boolean;
  ir_eval?: IREvalResult | null;
  runs: BenchmarkQueryRun[];
}

export interface GuardrailCheckResponse {
  query: string;
  passed: boolean;
  flagged_type?: string | null;
  reason?: string | null;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  recommended_action: 'ALLOW' | 'BLOCK' | 'ABSTAIN';
  latency_ms?: number;
}

export interface TTSResponse {
  audio_base64?: string | null;
  content_type: string;
  language_code: string;
  speaker: string;
  latency_ms: number;
  error?: string | null;
}

export interface SystemStatus {
  voice_engine_status: string;
  embedding_model_status: string;
  embedding_model_name: string;
  vector_store_status: string;
  vector_count: number;
  vector_dimension: number;
  llm_provider: string;
  llm_provider_mode: string;
  llm_model: string;
  knowledge_base_status: string;
  documents_count: number;
  chunks_count: number;
  api_status: string;
  optimizations: string[];
  environment: string;
  server_time: string;
  stt_provider?: string;
  stt_configured?: boolean;
  active_collection?: string;
}
