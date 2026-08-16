import React, { useState } from 'react';
import { Search, Info, ArrowUpRight } from 'lucide-react';
import { api } from '../services/api';
import type { RetrievalSearchResult, SourceItem } from '../types';
import { SourceDrawer } from '../components/SourceDrawer';

export const RetrievalLabPage: React.FC = () => {
  const [query, setQuery] = useState<string>('What is the travel meal reimbursement rate?');
  const [topK, setTopK] = useState<number>(5);
  const [threshold, setThreshold] = useState<number>(0.35);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [result, setResult] = useState<RetrievalSearchResult | null>(null);
  const [selectedSource, setSelectedSource] = useState<SourceItem | null>(null);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    try {
      const data = await api.searchRetrieval(query.trim(), topK, threshold);
      setResult(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const sampleQueries = [
    'What is the travel meal reimbursement rate?',
    'What is the standard refund period for hardware purchases?',
    'How do I report a lost laptop or hardware security key?',
    'What are the specifications of the VP-900 Voice Hub microphone?',
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 font-mono">
      {/* Header */}
      <div className="mb-8">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-[#111311] border border-[rgba(243,235,221,0.12)] text-[#C9C2B5] text-[10px] uppercase tracking-widest mb-2">
          <Search className="w-3 h-3 text-[#1C563E]" />
          <span>VECTOR RETRIEVAL LABORATORY</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-[#F3EBDD] tracking-tight">
          RETRIEVAL LAB
        </h1>
        <p className="text-xs text-[#858983] mt-1 font-sans">
          Inspect what the model sees before it answers. Query the FAISS vector index directly with granular Top-K and threshold filters.
        </p>
      </div>

      {/* Query Bar & Controls */}
      <div className="bg-[#111311] rounded-3xl p-6 sm:p-7 border border-[rgba(243,235,221,0.14)] shadow-xl mb-8">
        <form onSubmit={handleSearch}>
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter query to test vector retrieval..."
                className="w-full px-4 py-3 rounded-2xl bg-[#171A17] border border-[rgba(243,235,221,0.14)] text-xs sm:text-sm text-[#F3EBDD] focus:outline-none focus:border-[#1C563E] font-sans"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="px-5 py-3 rounded-2xl bg-[#F3EBDD] hover:bg-[#FFFFFF] text-[#080908] font-bold text-xs shadow-md flex items-center justify-center space-x-2 transition-all disabled:opacity-40 hover-lift"
            >
              {isLoading ? (
                <div className="w-3.5 h-3.5 border-2 border-[#080908] border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <Search className="w-3.5 h-3.5 text-[#123B2A]" />
                  <span>RETRIEVE CHUNKS</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Sliders: Top-K and Threshold */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mt-6 pt-5 border-t border-[rgba(243,235,221,0.08)]">
          <div>
            <div className="flex items-center justify-between text-xs text-[#C9C2B5] mb-2">
              <span className="text-[10px] text-[#858983] uppercase tracking-widest">TOP K MATCHES</span>
              <span className="text-[#A8D5BA]">{topK}</span>
            </div>
            <input
              type="range"
              min="1"
              max="12"
              step="1"
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="w-full accent-[#1C563E]"
            />
          </div>

          <div>
            <div className="flex items-center justify-between text-xs text-[#C9C2B5] mb-2">
              <span className="text-[10px] text-[#858983] uppercase tracking-widest">SIMILARITY THRESHOLD</span>
              <span className="text-[#A8D5BA]">{Math.round(threshold * 100)}%</span>
            </div>
            <input
              type="range"
              min="0.10"
              max="0.80"
              step="0.05"
              value={threshold}
              onChange={(e) => setThreshold(Number(e.target.value))}
              className="w-full accent-[#1C563E]"
            />
          </div>
        </div>

        {/* Quick Sample Queries */}
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="text-[10px] text-[#858983] mr-1">PRESETS:</span>
          {sampleQueries.map((sq, i) => (
            <button
              key={i}
              type="button"
              onClick={() => {
                setQuery(sq);
              }}
              className="text-[10px] bg-[#171A17] hover:bg-[#1E231E] text-[#C9C2B5] px-2.5 py-1 rounded-lg border border-[rgba(243,235,221,0.08)] transition-all"
            >
              {sq}
            </button>
          ))}
        </div>
      </div>

      {/* Why Retrieved & Rationale Card */}
      {result && (
        <div className="bg-[#111311] rounded-3xl p-6 border border-[rgba(243,235,221,0.14)] shadow-xl mb-8">
          <div className="flex items-center justify-between pb-3 border-b border-[rgba(243,235,221,0.08)] mb-3">
            <div className="flex items-center space-x-2">
              <Info className="w-4 h-4 text-[#1C563E]" />
              <h3 className="font-bold text-xs uppercase tracking-widest text-[#858983]">
                WHY THIS RESULT WAS RETRIEVED
              </h3>
            </div>
            <span className="text-[11px] text-[#A8D5BA] font-bold">
              SEARCH TIME: {result.latency_ms}ms
            </span>
          </div>

          <p className="text-xs sm:text-sm text-[#F3EBDD] leading-relaxed font-sans">
            {result.explanation}
          </p>
        </div>
      )}

      {/* Retrieved Results Table / Rows */}
      {result ? (
        <div className="bg-[#111311] rounded-3xl p-6 border border-[rgba(243,235,221,0.14)] shadow-xl">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-[rgba(243,235,221,0.08)]">
            <h3 className="font-bold text-xs uppercase tracking-widest text-[#858983]">
              RETRIEVED EVIDENCE CHUNKS ({result.results.length})
            </h3>
            <span className="text-[10px] text-[#858983]">CLICK ROW TO INSPECT CHUNK</span>
          </div>

          {result.results.length === 0 ? (
            <div className="p-8 text-center text-[#858983] text-xs">
              NO CHUNKS MET SIMILARITY THRESHOLD ({Math.round(threshold * 100)}%). Lower threshold to broaden search.
            </div>
          ) : (
            <div className="divide-y divide-[rgba(243,235,221,0.08)]">
              {result.results.map((item: SourceItem, idx: number) => {
                const scorePct = Math.round(item.similarity * 100);
                return (
                  <button
                    key={item.id || idx}
                    onClick={() => setSelectedSource(item)}
                    className="w-full text-left py-4 px-2 hover:bg-[#171A17]/60 transition-colors group focus:outline-none flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                  >
                    <div className="flex items-start space-x-3">
                      <span className="text-xs font-bold text-[#858983] font-mono mt-0.5">
                        {String(idx + 1).padStart(2, '0')}
                      </span>
                      <div>
                        <div className="text-xs font-bold text-[#F3EBDD] group-hover:text-[#A8D5BA] transition-colors">
                          {item.doc_name} <span className="text-[#858983] font-normal font-mono">(Chunk #{item.chunk_index})</span>
                        </div>
                        <p className="text-[11px] text-[#858983] line-clamp-1 mt-0.5 font-sans">
                          {item.content}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-3 sm:ml-auto flex-shrink-0">
                      <span className="text-xs font-bold font-mono text-[#A8D5BA]">
                        {scorePct}% SCORE
                      </span>
                      <ArrowUpRight className="w-3.5 h-3.5 text-[#858983] group-hover:text-[#F3EBDD] transition-colors" />
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      ) : (
        <div className="p-12 text-center text-[#858983] text-xs">
          RUN A QUERY TO INSPECT RETRIEVAL.
        </div>
      )}

      {/* Slide-out Source Detail Drawer */}
      <SourceDrawer
        source={selectedSource}
        onClose={() => setSelectedSource(null)}
      />
    </div>
  );
};
