import React from 'react';
import { Mic, ShieldAlert, Cpu, Database, CheckCircle2, AlertTriangle, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import type { LatencyBreakdown, GuardrailInfo } from '../types';

interface PipelineVisualizerProps {
  isLoading: boolean;
  hasResult: boolean;
  latency?: LatencyBreakdown;
  guardrails?: GuardrailInfo;
  abstained?: boolean;
}

export const PipelineVisualizer: React.FC<PipelineVisualizerProps> = ({
  isLoading,
  hasResult,
  latency,
  guardrails,
  abstained,
}) => {
  const isFailedGuardrail = guardrails && !guardrails.passed;

  const stages = [
    {
      id: 'voice',
      label: 'VOICE',
      sub: latency?.voice_stt_ms !== undefined && latency?.voice_stt_ms !== null ? `${latency.voice_stt_ms}ms` : 'STT',
      icon: <Mic className="w-3.5 h-3.5" />,
      status: isLoading ? 'active' : hasResult ? 'done' : 'idle',
    },
    {
      id: 'guardrail',
      label: 'GUARDRAIL',
      sub: latency ? `${latency.guardrail_ms}ms` : 'SAFETY',
      icon: <ShieldAlert className="w-3.5 h-3.5" />,
      status: isLoading
        ? 'active'
        : hasResult
        ? isFailedGuardrail
          ? 'error'
          : 'done'
        : 'idle',
    },
    {
      id: 'embed',
      label: 'EMBED',
      sub: latency ? `${latency.embedding_ms}ms` : 'MINILM',
      icon: <Cpu className="w-3.5 h-3.5" />,
      status: isLoading ? 'active' : hasResult && !isFailedGuardrail ? 'done' : 'idle',
    },
    {
      id: 'faiss',
      label: 'FAISS',
      sub: latency ? `${latency.retrieval_ms}ms` : 'COSINE',
      icon: <Database className="w-3.5 h-3.5" />,
      status: isLoading ? 'active' : hasResult && !isFailedGuardrail ? 'done' : 'idle',
    },
    {
      id: 'generate',
      label: 'GENERATE',
      sub: latency
        ? abstained
          ? 'ABSTAINED'
          : `${latency.generation_ms}ms`
        : 'GROUNDED',
      icon: <Sparkles className="w-3.5 h-3.5" />,
      status: isLoading
        ? 'active'
        : hasResult
        ? abstained
          ? 'warning'
          : 'done'
        : 'idle',
    },
  ];

  return (
    <div className="w-full max-w-4xl mx-auto my-6 px-4 font-mono">
      <div className="bg-[#111311] rounded-2xl p-4 sm:p-5 border border-[rgba(243,235,221,0.14)] shadow-xl">
        <div className="flex items-center justify-between mb-3 px-1 border-b border-[rgba(243,235,221,0.08)] pb-2.5">
          <div className="flex items-center space-x-2">
            <span className="w-1.5 h-1.5 rounded-full bg-[#1C563E] animate-pulse" />
            <h3 className="text-[10px] font-mono font-bold uppercase tracking-widest text-[#858983]">
              PIPELINE EXECUTION TELEMETRY
            </h3>
          </div>
          {latency && (
            <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-[#171A17] border border-[rgba(243,235,221,0.14)] text-[#A8D5BA]">
              TOTAL: {latency.total_rag_ms}ms
            </span>
          )}
        </div>

        {/* Horizontal on Desktop, Vertical on Mobile */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 sm:gap-2.5">
          {stages.map((stage, idx) => {
            let statusColor = 'bg-[#171A17]/60 border-[rgba(243,235,221,0.1)] text-[#858983]';
            let badgeBg = 'bg-[#111311] text-[#858983]';

            if (stage.status === 'active') {
              statusColor = 'bg-[#123B2A] border-[#1C563E] text-[#F3EBDD] ring-1 ring-[#1C563E]';
              badgeBg = 'bg-[#171A17] text-[#A8D5BA] animate-pulse';
            } else if (stage.status === 'done') {
              statusColor = 'bg-[#111311] border-[#1C563E]/60 text-[#F3EBDD]';
              badgeBg = 'bg-[#123B2A] text-[#A8D5BA] font-mono';
            } else if (stage.status === 'warning') {
              statusColor = 'bg-[#111311] border-[#D9C48A]/40 text-[#D9C48A]';
              badgeBg = 'bg-[#D9C48A]/10 text-[#D9C48A]';
            } else if (stage.status === 'error') {
              statusColor = 'bg-[#111311] border-[#D58A8A]/40 text-[#D58A8A]';
              badgeBg = 'bg-[#D58A8A]/10 text-[#D58A8A]';
            }

            return (
              <motion.div
                key={stage.id}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: idx * 0.05 }}
                className={`flex flex-col justify-between p-2.5 sm:p-3 rounded-xl border transition-all ${statusColor}`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="p-1 rounded bg-[#080908] border border-[rgba(243,235,221,0.08)]">
                    {stage.icon}
                  </div>
                  {stage.status === 'done' && (
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#A8D5BA]" />
                  )}
                  {stage.status === 'warning' && (
                    <AlertTriangle className="w-3.5 h-3.5 text-[#D9C48A]" />
                  )}
                  {stage.status === 'active' && (
                    <div className="w-3 h-3 border-2 border-[#F3EBDD] border-t-transparent rounded-full animate-spin" />
                  )}
                </div>

                <div>
                  <div className="text-[10px] font-mono font-bold tracking-wider">{stage.label}</div>
                  <div className={`mt-1 inline-block px-1.5 py-0.5 rounded text-[9px] font-mono ${badgeBg}`}>
                    {stage.sub}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
