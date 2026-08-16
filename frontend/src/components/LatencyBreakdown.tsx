import React from 'react';
import type { LatencyBreakdown as LatencyType } from '../types';

interface LatencyBreakdownProps {
  latency: LatencyType;
}

export const LatencyBreakdown: React.FC<LatencyBreakdownProps> = ({ latency }) => {
  const targetMs = 200;
  const isUnderTarget = latency.total_rag_ms <= targetMs;

  const items = [
    {
      label: 'VOICE STT',
      value: latency.voice_stt_ms !== undefined && latency.voice_stt_ms !== null ? `${latency.voice_stt_ms}ms` : '—',
    },
    {
      label: 'GUARDRAILS',
      value: `${latency.guardrail_ms}ms`,
    },
    {
      label: 'EMBEDDING',
      value: `${latency.embedding_ms}ms`,
    },
    {
      label: 'RETRIEVAL',
      value: `${latency.retrieval_ms}ms`,
    },
    {
      label: 'GENERATION',
      value: `${latency.generation_ms}ms`,
    },
  ];

  return (
    <div className="w-full max-w-4xl mx-auto my-4 px-4 font-mono">
      <div className="bg-[#111311] rounded-2xl p-4 border border-[rgba(243,235,221,0.12)]">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3 pb-2 border-b border-[rgba(243,235,221,0.08)] text-[10px]">
          <span className="font-bold uppercase tracking-widest text-[#858983]">
            LATENCY TELEMETRY READOUT
          </span>
          <div className="flex items-center space-x-2">
            <span className="text-[#858983]">TARGET: &lt;200ms</span>
            <span
              className={`px-2 py-0.5 rounded ${
                isUnderTarget
                  ? 'bg-[#123B2A] text-[#A8D5BA] border border-[#1C563E]'
                  : 'bg-[#D9C48A]/10 text-[#D9C48A] border border-[#D9C48A]/30'
              }`}
            >
              TOTAL: {latency.total_rag_ms}ms
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs">
          {items.map((it, idx) => (
            <div key={idx} className="p-2 rounded-xl bg-[#080908] border border-[rgba(243,235,221,0.06)]">
              <span className="text-[9px] text-[#858983] block">{it.label}</span>
              <span className="font-bold text-[#F3EBDD] text-xs mt-0.5 block">{it.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
