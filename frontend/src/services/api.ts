import type {
  AskResponse,
  DocumentInfo,
  KnowledgeBaseStats,
  ReindexRequest,
  ChunkInfo,
  RetrievalSearchResult,
  BenchmarkSummary,
  GuardrailCheckResponse,
  SystemStatus,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail?.message || errJson.detail || JSON.stringify(errJson);
    } catch {
      errorDetail = `HTTP ${response.status} - ${response.statusText}`;
    }
    throw new Error(errorDetail);
  }
  return response.json();
}

export const api = {
  async askQuestion(
    query: string,
    voiceLatencyMs?: number,
    topK?: number,
    threshold?: number
  ): Promise<AskResponse> {
    const res = await fetch(`${API_BASE_URL}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        voice_latency_ms: voiceLatencyMs,
        top_k: topK,
        threshold: threshold,
      }),
    });
    return handleResponse<AskResponse>(res);
  },

  async uploadDocument(file: File): Promise<DocumentInfo> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE_URL}/ingest`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<DocumentInfo>(res);
  },

  async getDocuments(): Promise<DocumentInfo[]> {
    const res = await fetch(`${API_BASE_URL}/documents`);
    return handleResponse<DocumentInfo[]>(res);
  },

  async deleteDocument(docId: string): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${API_BASE_URL}/documents/${docId}`, {
      method: 'DELETE',
    });
    return handleResponse<{ success: boolean; message: string }>(res);
  },

  async reindexKnowledgeBase(req: ReindexRequest): Promise<KnowledgeBaseStats> {
    const res = await fetch(`${API_BASE_URL}/reindex`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    return handleResponse<KnowledgeBaseStats>(res);
  },

  async getKnowledgeBaseStats(): Promise<KnowledgeBaseStats> {
    const res = await fetch(`${API_BASE_URL}/stats`);
    return handleResponse<KnowledgeBaseStats>(res);
  },

  async getChunks(docId?: string, limit: number = 50): Promise<ChunkInfo[]> {
    const params = new URLSearchParams();
    if (docId) params.append('doc_id', docId);
    params.append('limit', limit.toString());
    const res = await fetch(`${API_BASE_URL}/chunks?${params.toString()}`);
    return handleResponse<ChunkInfo[]>(res);
  },

  async searchRetrieval(
    query: string,
    topK: number = 5,
    threshold: number = 0.35
  ): Promise<RetrievalSearchResult> {
    const res = await fetch(`${API_BASE_URL}/retrieval/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k: topK, threshold }),
    });
    return handleResponse<RetrievalSearchResult>(res);
  },

  async runBenchmark(customQueries?: string[]): Promise<BenchmarkSummary> {
    const res = await fetch(`${API_BASE_URL}/benchmark/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(customQueries ? { custom_queries: customQueries } : {}),
    });
    return handleResponse<BenchmarkSummary>(res);
  },

  async getLatestBenchmark(): Promise<BenchmarkSummary> {
    const res = await fetch(`${API_BASE_URL}/benchmark/latest`);
    return handleResponse<BenchmarkSummary>(res);
  },

  async checkGuardrails(query: string): Promise<GuardrailCheckResponse> {
    const res = await fetch(`${API_BASE_URL}/guardrails/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });
    return handleResponse<GuardrailCheckResponse>(res);
  },

  async getGuardrailRules(): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/guardrails/rules`);
    return handleResponse<any>(res);
  },

  async getSystemStatus(): Promise<SystemStatus> {
    const res = await fetch(`${API_BASE_URL}/system`);
    return handleResponse<SystemStatus>(res);
  },
};
