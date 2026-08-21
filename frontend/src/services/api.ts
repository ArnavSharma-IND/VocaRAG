import type {
  AskResponse,
  DocumentInfo,
  KnowledgeBaseStats,
  ReindexRequest,
  ChunkInfo,
  RetrievalSearchResult,
  BenchmarkSummary,
  IREvalResult,
  GuardrailCheckResponse,
  TTSResponse,
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
    threshold?: number,
    collection: string = 'msmarco'
  ): Promise<AskResponse> {
    const res = await fetch(`${API_BASE_URL}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        voice_latency_ms: voiceLatencyMs,
        top_k: topK,
        threshold: threshold,
        collection: collection,
      }),
    });
    return handleResponse<AskResponse>(res);
  },

  async transcribeAudio(
    audioBlob: Blob,
    languageCode: string = 'hi-IN',
    mode: string = 'transcribe'
  ): Promise<{ transcript: string; language: string; mode: string; latency_ms: number; error?: string }> {
    const formData = new FormData();
    formData.append('file', audioBlob, 'mic_recording.webm');
    formData.append('language_code', languageCode);
    formData.append('mode', mode);

    const res = await fetch(`${API_BASE_URL}/stt/transcribe`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<{ transcript: string; language: string; mode: string; latency_ms: number; error?: string }>(res);
  },

  async synthesizeSpeech(
    text: string,
    languageCode: string = 'hi-IN',
    speaker: string = 'meera'
  ): Promise<TTSResponse> {
    const res = await fetch(`${API_BASE_URL}/tts/synthesize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, language_code: languageCode, speaker }),
    });
    return handleResponse<TTSResponse>(res);
  },

  async uploadDocument(file: File, collection: string = 'enterprise'): Promise<DocumentInfo> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('collection', collection);
    const res = await fetch(`${API_BASE_URL}/ingest`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<DocumentInfo>(res);
  },

  async getDocuments(collection?: string): Promise<DocumentInfo[]> {
    const params = collection ? `?collection=${collection}` : '';
    const res = await fetch(`${API_BASE_URL}/documents${params}`);
    return handleResponse<DocumentInfo[]>(res);
  },

  async deleteDocument(docId: string, collection: string = 'enterprise'): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${API_BASE_URL}/documents/${docId}?collection=${collection}`, {
      method: 'DELETE',
    });
    return handleResponse<{ success: boolean; message: string }>(res);
  },

  async reindexKnowledgeBase(req: ReindexRequest, collection: string = 'enterprise'): Promise<KnowledgeBaseStats> {
    const res = await fetch(`${API_BASE_URL}/reindex?collection=${collection}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    return handleResponse<KnowledgeBaseStats>(res);
  },

  async getKnowledgeBaseStats(collection: string = 'enterprise'): Promise<KnowledgeBaseStats> {
    const res = await fetch(`${API_BASE_URL}/stats?collection=${collection}`);
    return handleResponse<KnowledgeBaseStats>(res);
  },

  async getChunks(docId?: string, collection: string = 'enterprise', limit: number = 50): Promise<ChunkInfo[]> {
    const params = new URLSearchParams();
    if (docId) params.append('doc_id', docId);
    params.append('collection', collection);
    params.append('limit', limit.toString());
    const res = await fetch(`${API_BASE_URL}/chunks?${params.toString()}`);
    return handleResponse<ChunkInfo[]>(res);
  },

  async searchRetrieval(
    query: string,
    topK: number = 5,
    threshold: number = 0.30,
    collection: string = 'msmarco'
  ): Promise<RetrievalSearchResult> {
    const res = await fetch(`${API_BASE_URL}/retrieval/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k: topK, threshold, collection }),
    });
    return handleResponse<RetrievalSearchResult>(res);
  },

  async runBenchmark(customQueries?: string[], collection: string = 'msmarco'): Promise<BenchmarkSummary> {
    const res = await fetch(`${API_BASE_URL}/benchmark/run?collection=${collection}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(customQueries ? { custom_queries: customQueries } : {}),
    });
    return handleResponse<BenchmarkSummary>(res);
  },

  async getLatestBenchmark(collection: string = 'msmarco'): Promise<BenchmarkSummary> {
    const res = await fetch(`${API_BASE_URL}/benchmark/latest?collection=${collection}`);
    return handleResponse<BenchmarkSummary>(res);
  },

  async runIREval(topK: number = 10): Promise<IREvalResult> {
    const res = await fetch(`${API_BASE_URL}/benchmark/ir-eval?top_k=${topK}`, {
      method: 'POST',
    });
    return handleResponse<IREvalResult>(res);
  },

  async getIREval(): Promise<IREvalResult> {
    const res = await fetch(`${API_BASE_URL}/benchmark/ir-eval`);
    return handleResponse<IREvalResult>(res);
  },

  async checkGuardrails(query: string, collection: string = 'msmarco'): Promise<GuardrailCheckResponse> {
    const t0 = performance.now();
    const res = await fetch(`${API_BASE_URL}/guardrails/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, collection }),
    });
    const data = await handleResponse<GuardrailCheckResponse>(res);
    if (!data.latency_ms) {
      data.latency_ms = Math.round(performance.now() - t0);
    }
    return data;
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
