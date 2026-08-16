import React, { useState } from 'react';
import { ShieldAlert, ArrowUpRight, Info } from 'lucide-react';
import { motion } from 'framer-motion';
import type { AskResponse, SourceItem } from '../types';
import { SourceDrawer } from './SourceDrawer';

interface AnswerCardProps {
  response: AskResponse;
}

export const AnswerCard: React.FC<AnswerCardProps> = ({ response }) => {
  const [selectedSource, setSelectedSource] = useState<SourceItem | null>(null);

  const { query, answer, abstained, confidence, sources, mode, retrieval_explanation, latency } =
    response;

  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      className="w-full max-w-4xl mx-auto my-6 px-4 font-mono"
    >
      <div className="bg-[#111311] rounded-3xl p-6 sm:p-8 border border-[rgba(243,235,221,0.14)] shadow-2xl relative overflow-hidden">
        {/* Top Header Row */}
        <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-[rgba(243,235,221,0.12)]">
          <div className="flex items-center space-x-2.5">
            {abstained ? (
              <span className="w-2 h-2 rounded-full bg-[#D9C48A]" />
            ) : (
              <span className="w-2 h-2 rounded-full bg-[#1C563E] animate-pulse" />
            )}
            <div>
              <h2 className="text-xs font-bold tracking-widest text-[#858983] uppercase">
                {abstained ? 'SYSTEM ABSTENTION' : 'GROUNDED ANSWER'}
              </h2>
            </div>
          </div>

          {/* Right Badges: Grounding & Mode */}
          <div className="flex items-center space-x-2 text-[11px]">
            {abstained ? (
              <span className="px-2.5 py-0.5 rounded-full bg-[#D9C48A]/10 border border-[#D9C48A]/30 text-[#D9C48A]">
                ○ INSUFFICIENT EVIDENCE
              </span>
            ) : (
              <span className="px-2.5 py-0.5 rounded-full bg-[#123B2A] border border-[#1C563E] text-[#A8D5BA] flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#A8D5BA]" />
                <span>GROUNDED ({Math.round(confidence * 100)}%)</span>
              </span>
            )}
            <span className="px-2.5 py-0.5 rounded-full bg-[#171A17] border border-[rgba(243,235,221,0.14)] text-[#C9C2B5]">
              {mode.toUpperCase()}
            </span>
          </div>
        </div>

        {/* User Query Echo */}
        <div className="my-4 text-xs text-[#858983] bg-[#080908] px-3.5 py-2 rounded-xl border border-[rgba(243,235,221,0.08)] flex items-center space-x-2">
          <span className="text-[#C9C2B5] font-semibold">QUERY:</span>
          <span className="text-[#F3EBDD]">“{query}”</span>
        </div>

        {/* Answer Content in Large Editorial Typography */}
        <div className="my-6">
          {abstained ? (
            <div className="p-5 rounded-2xl bg-[#171A17] border border-[#D9C48A]/30 text-[#F3EBDD]">
              <div className="flex items-start space-x-3">
                <ShieldAlert className="w-5 h-5 text-[#D9C48A] flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-sm sm:text-base leading-relaxed text-[#F3EBDD] font-sans">
                    {answer}
                  </p>
                  <p className="mt-2 text-xs text-[#858983]">
                    Guardrails prevented hallucination because retrieved context similarity fell below the strict evidence threshold.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="relative">
              <p className="text-base sm:text-lg text-[#F3EBDD] leading-relaxed font-sans font-normal border-l-2 border-[#1C563E] pl-4 py-1">
                {answer}
              </p>
            </div>
          )}
        </div>

        {/* Retrieval Explanation Banner */}
        {retrieval_explanation && (
          <div className="mt-4 p-3 bg-[#080908] rounded-xl border border-[rgba(243,235,221,0.1)] text-xs text-[#858983] flex items-start space-x-2">
            <Info className="w-3.5 h-3.5 text-[#1C563E] flex-shrink-0 mt-0.5" />
            <div>
              <span className="text-[#C9C2B5] font-semibold">RATIONALE: </span>
              {retrieval_explanation}
            </div>
          </div>
        )}

        {/* Technical Latency Readout + Sources */}
        <div className="mt-8 pt-6 border-t border-[rgba(243,235,221,0.12)] grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Sources Column (2 cols) */}
          <div className="md:col-span-2">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-[10px] font-bold uppercase tracking-widest text-[#858983]">
                SOURCES / RETRIEVED CONTEXT ({sources.length})
              </h3>
              <span className="text-[10px] text-[#858983]">CLICK TO INSPECT</span>
            </div>

            {sources && sources.length > 0 ? (
              <div className="divide-y divide-[rgba(243,235,221,0.08)] border-y border-[rgba(243,235,221,0.08)]">
                {sources.map((src, idx) => {
                  const isGK =
                    src.source_type === 'general_knowledge' ||
                    src.category_label === 'GENERAL KNOWLEDGE' ||
                    src.doc_name.toLowerCase().startsWith('general_knowledge');
                  const label = src.category_label || (isGK ? 'GENERAL KNOWLEDGE' : 'POLICY');

                  return (
                    <button
                      key={src.id || idx}
                      onClick={() => setSelectedSource(src)}
                      className="w-full text-left py-3 px-2 flex items-center justify-between hover:bg-[#171A17]/60 transition-colors group focus:outline-none"
                    >
                      <div className="flex items-center space-x-3">
                        <span className="text-xs text-[#858983] font-bold">
                          {String(idx + 1).padStart(2, '0')}
                        </span>
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="text-xs font-medium text-[#F3EBDD] group-hover:text-[#A8D5BA] transition-colors">
                              {src.doc_name}
                            </span>
                            <span
                              className={`text-[9px] font-bold px-1.5 py-0.2 rounded ${
                                isGK
                                  ? 'bg-[#123B2A] text-[#A8D5BA] border border-[#1C563E]'
                                  : 'bg-[#171A17] text-[#C9C2B5] border border-[rgba(243,235,221,0.12)]'
                              }`}
                            >
                              {label}
                            </span>
                          </div>
                          <div className="text-[10px] text-[#858983]">
                            Chunk #{src.chunk_index}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3 text-right">
                        <span className="text-xs text-[#A8D5BA] font-semibold">
                          {Math.round(src.similarity * 100)}%
                        </span>
                        <ArrowUpRight className="w-3.5 h-3.5 text-[#858983] group-hover:text-[#F3EBDD] transition-colors" />
                      </div>
                    </button>
                  );
                })}
              </div>
            ) : (
              <p className="text-xs text-[#858983]">No sources retrieved.</p>
            )}
          </div>

          {/* Technical Readout Column (1 col) */}
          <div className="md:col-span-1 bg-[#080908] p-4 rounded-2xl border border-[rgba(243,235,221,0.1)] flex flex-col justify-between text-xs">
            <div>
              <span className="text-[9px] font-bold tracking-widest text-[#858983] uppercase block mb-3">
                PIPELINE LATENCY
              </span>

              <div className="space-y-1.5 text-[11px] text-[#C9C2B5]">
                <div className="flex justify-between">
                  <span className="text-[#858983]">STT</span>
                  <span>{latency.voice_stt_ms !== undefined && latency.voice_stt_ms !== null ? `${latency.voice_stt_ms}ms` : '—'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#858983]">GUARDRAIL</span>
                  <span>{latency.guardrail_ms}ms</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#858983]">EMBED</span>
                  <span>{latency.embedding_ms}ms</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#858983]">RETRIEVE</span>
                  <span>{latency.retrieval_ms}ms</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#858983]">GENERATE</span>
                  <span>{latency.generation_ms}ms</span>
                </div>
              </div>
            </div>

            <div className="pt-3 mt-3 border-t border-[rgba(243,235,221,0.12)] flex items-center justify-between font-bold">
              <span className="text-[#F3EBDD]">TOTAL</span>
              <span className="text-[#A8D5BA]">{latency.total_rag_ms}ms</span>
            </div>
          </div>
        </div>
      </div>

      {/* Slide-out Source Detail Drawer */}
      <SourceDrawer
        source={selectedSource}
        onClose={() => setSelectedSource(null)}
      />
    </motion.div>
  );
};
