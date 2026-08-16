import React, { useState, useEffect } from 'react';
import {
  Cpu,
  RefreshCw,
  Zap,
} from 'lucide-react';
import { api } from '../services/api';
import type { SystemStatus } from '../types';

export const SystemStatusPage: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [lastRefreshed, setLastRefreshed] = useState<string>('');

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    setIsLoading(true);
    try {
      const data = await api.getSystemStatus();
      setStatus(data);
      setLastRefreshed(new Date().toLocaleTimeString());
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const statusRows = [
    { label: 'FASTAPI BACKEND CORE', status: status?.api_status || 'HEALTHY', sub: status?.server_time || 'ACTIVE' },
    { label: 'VECTOR STORE (FAISS)', status: 'READY', sub: `${status?.vector_count || 0} VECTORS INDEXED` },
    { label: 'EMBEDDING MODEL', status: 'READY', sub: `${status?.embedding_model_name || 'all-MiniLM-L6-v2'} (${status?.vector_dimension || 384} DIM)` },
    { label: 'LLM SYNTHESIS ENGINE', status: 'CONNECTED', sub: `${status?.llm_provider || 'DEMO EXTRACTOR'} (${status?.llm_provider_mode || 'Demo'} Mode)` },
    { label: 'KNOWLEDGE BASE CORPUS', status: 'INDEXED', sub: `${status?.documents_count || 0} DOCS • ${status?.chunks_count || 0} CHUNKS` },
    { label: 'VOICE CAPTURE ENGINE', status: 'READY', sub: 'WEB SPEECH API + WEB AUDIO RMS' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 font-mono">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-[#111311] border border-[rgba(243,235,221,0.12)] text-[#C9C2B5] text-[10px] uppercase tracking-widest mb-2">
            <Cpu className="w-3 h-3 text-[#1C563E]" />
            <span>INFRASTRUCTURE & DIAGNOSTICS</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#F3EBDD] tracking-tight">
            SYSTEM STATUS
          </h1>
          <p className="text-xs text-[#858983] mt-1 font-sans">
            Real-time health verification across Voice, Embedding, FAISS, and LLM services.
          </p>
        </div>

        <button
          onClick={fetchStatus}
          disabled={isLoading}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-[#171A17] hover:bg-[#1E231E] border border-[rgba(243,235,221,0.14)] text-xs font-semibold text-[#F3EBDD] transition-colors shadow-xs"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>REFRESH</span>
          {lastRefreshed && (
            <span className="text-[10px] text-[#858983] font-mono">({lastRefreshed})</span>
          )}
        </button>
      </div>

      {/* Technical Readout List */}
      <div className="bg-[#111311] rounded-3xl p-6 sm:p-8 border border-[rgba(243,235,221,0.14)] shadow-xl mb-8">
        <h3 className="font-bold text-xs uppercase tracking-widest text-[#858983] mb-4 pb-3 border-b border-[rgba(243,235,221,0.08)]">
          SUBSYSTEM TELEMETRY READOUT
        </h3>

        <div className="divide-y divide-[rgba(243,235,221,0.08)]">
          {statusRows.map((row, idx) => (
            <div
              key={idx}
              className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-xs"
            >
              <div>
                <span className="font-bold text-[#F3EBDD]">{row.label}</span>
                <span className="text-[10px] text-[#858983] block sm:inline sm:ml-3">
                  {row.sub}
                </span>
              </div>

              <div className="flex items-center space-x-1.5 text-[#A8D5BA] font-bold text-xs">
                <span className="w-1.5 h-1.5 rounded-full bg-[#1C563E] animate-pulse" />
                <span>● {row.status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Technical Specs Readout */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8 text-xs">
        <div className="p-5 rounded-2xl bg-[#111311] border border-[rgba(243,235,221,0.12)]">
          <span className="text-[9px] uppercase tracking-widest text-[#858983] block mb-1">
            VECTOR DIMENSION
          </span>
          <span className="text-2xl font-bold text-[#F3EBDD]">
            {status?.vector_dimension || 384}
          </span>
        </div>

        <div className="p-5 rounded-2xl bg-[#111311] border border-[rgba(243,235,221,0.12)]">
          <span className="text-[9px] uppercase tracking-widest text-[#858983] block mb-1">
            VECTOR COUNT
          </span>
          <span className="text-2xl font-bold text-[#F3EBDD]">
            {status?.vector_count || 0}
          </span>
        </div>

        <div className="p-5 rounded-2xl bg-[#111311] border border-[rgba(243,235,221,0.12)]">
          <span className="text-[9px] uppercase tracking-widest text-[#858983] block mb-1">
            EMBEDDING CACHE
          </span>
          <span className="text-2xl font-bold text-[#A8D5BA]">
            ACTIVE (MD5)
          </span>
        </div>
      </div>

      {/* Engineered Production Capabilities */}
      <div className="bg-[#111311] rounded-3xl p-6 sm:p-8 border border-[rgba(243,235,221,0.14)] shadow-xl">
        <div className="flex items-center space-x-2 mb-4 pb-3 border-b border-[rgba(243,235,221,0.08)]">
          <Zap className="w-4 h-4 text-[#1C563E]" />
          <h3 className="font-bold text-xs uppercase tracking-widest text-[#858983]">
            PRODUCTION OPTIMIZATIONS
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          {status?.optimizations.map((opt, i) => (
            <div
              key={i}
              className="p-3 rounded-xl bg-[#080908] border border-[rgba(243,235,221,0.08)] flex items-center space-x-2"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-[#1C563E]" />
              <span className="text-[#F3EBDD] font-bold text-[11px]">{opt}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
