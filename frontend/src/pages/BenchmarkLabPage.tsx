import React, { useState, useEffect } from 'react';
import { Play, Gauge, Zap } from 'lucide-react';
import { api } from '../services/api';
import type { BenchmarkSummary } from '../types';

export const BenchmarkLabPage: React.FC = () => {
  const [summary, setSummary] = useState<BenchmarkSummary | null>(null);
  const [isRunning, setIsRunning] = useState<boolean>(false);

  useEffect(() => {
    loadLatest();
  }, []);

  const loadLatest = async () => {
    try {
      const data = await api.getLatestBenchmark();
      setSummary(data);
    } catch (err) {
      console.error('Failed to load benchmark:', err);
    }
  };

  const handleRun = async () => {
    setIsRunning(true);
    try {
      const data = await api.runBenchmark();
      setSummary(data);
    } catch (err) {
      console.error('Benchmark execution failed:', err);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[rgba(243,235,221,0.12)] pb-6">
        <div>
          <h1 className="text-2xl font-bold font-editorial text-[#F3EBDD]">Latency & Accuracy Benchmark Lab</h1>
          <p className="text-xs text-[#858983] mt-1 font-mono">
            Empirical P50 / P70 / P100 percentile telemetry over 16 evaluation queries.
          </p>
        </div>

        <button
          onClick={handleRun}
          disabled={isRunning}
          className="flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-semibold bg-[#F3EBDD] text-[#080908] hover:bg-[#FFFFFF] transition-all disabled:opacity-50"
        >
          <Play className={`w-3.5 h-3.5 fill-current ${isRunning ? 'animate-spin' : ''}`} />
          <span>{isRunning ? 'RUNNING TEST SUITE (16 QUERIES)...' : 'RUN BENCHMARK SUITE'}</span>
        </button>
      </div>

      {summary && (
        <div className="space-y-6 font-mono">
          {/* Headline Metric Cards: Retrieval vs E2E */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 1. Retrieval Pipeline (<200ms Target) */}
            <div className="p-6 rounded-3xl bg-[#0C241B]/40 border border-[#1C563E]/60 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Zap className="w-5 h-5 text-[#A8D5BA]" />
                  <span className="text-sm font-bold text-[#F3EBDD] uppercase tracking-wider">
                    Retrieval Pipeline (Embed + FAISS)
                  </span>
                </div>
                <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                  summary.meets_retrieval_target ? 'bg-[#1C563E] text-[#A8D5BA]' : 'bg-[#D58A8A]/20 text-[#D58A8A]'
                }`}>
                  {summary.meets_retrieval_target ? 'TARGET MET (<200ms)' : 'TARGET EXCEEDED'}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="p-3 bg-[#111311] rounded-2xl border border-[rgba(243,235,221,0.08)]">
                  <span className="text-[10px] text-[#858983]">P50 RETRIEVAL</span>
                  <p className="text-lg font-bold text-[#A8D5BA] mt-0.5">{summary.p50_retrieval_ms}ms</p>
                </div>
                <div className="p-3 bg-[#111311] rounded-2xl border border-[rgba(243,235,221,0.08)]">
                  <span className="text-[10px] text-[#858983]">P70 RETRIEVAL</span>
                  <p className="text-lg font-bold text-[#A8D5BA] mt-0.5">{summary.p70_retrieval_ms}ms</p>
                </div>
                <div className="p-3 bg-[#111311] rounded-2xl border border-[rgba(243,235,221,0.08)]">
                  <span className="text-[10px] text-[#858983]">P100 RETRIEVAL</span>
                  <p className="text-lg font-bold text-[#A8D5BA] mt-0.5">{summary.p100_retrieval_ms}ms</p>
                </div>
              </div>
            </div>

            {/* 2. End-to-End with LLM Generation */}
            <div className="p-6 rounded-3xl bg-[#111311] border border-[rgba(243,235,221,0.12)] space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Gauge className="w-5 h-5 text-[#D9C48A]" />
                  <span className="text-sm font-bold text-[#F3EBDD] uppercase tracking-wider">
                    End-to-End Pipeline (with LLM Generation)
                  </span>
                </div>
                <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-[#171A17] text-[#D9C48A]">
                  GROQ LPU / DEMO
                </span>
              </div>

              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="p-3 bg-[#171A17] rounded-2xl border border-[rgba(243,235,221,0.08)]">
                  <span className="text-[10px] text-[#858983]">P50 E2E</span>
                  <p className="text-lg font-bold text-[#F3EBDD] mt-0.5">{summary.p50_total_ms}ms</p>
                </div>
                <div className="p-3 bg-[#171A17] rounded-2xl border border-[rgba(243,235,221,0.08)]">
                  <span className="text-[10px] text-[#858983]">P70 E2E</span>
                  <p className="text-lg font-bold text-[#F3EBDD] mt-0.5">{summary.p70_total_ms}ms</p>
                </div>
                <div className="p-3 bg-[#171A17] rounded-2xl border border-[rgba(243,235,221,0.08)]">
                  <span className="text-[10px] text-[#858983]">P100 E2E</span>
                  <p className="text-lg font-bold text-[#F3EBDD] mt-0.5">{summary.p100_total_ms}ms</p>
                </div>
              </div>
            </div>
          </div>

          {/* Individual Query Execution Runs Table */}
          <div className="p-6 rounded-3xl bg-[#111311] border border-[rgba(243,235,221,0.12)]">
            <h2 className="text-sm font-semibold text-[#F3EBDD] uppercase tracking-wider mb-4">
              Query Test Execution Log ({summary.runs.length} runs)
            </h2>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[rgba(243,235,221,0.1)] text-[#858983]">
                    <th className="py-2 px-3">QUERY</th>
                    <th className="py-2 px-3">CATEGORY</th>
                    <th className="py-2 px-3">RETRIEVAL</th>
                    <th className="py-2 px-3">GENERATION</th>
                    <th className="py-2 px-3">TOTAL</th>
                    <th className="py-2 px-3">CONFIDENCE</th>
                    <th className="py-2 px-3">STATUS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[rgba(243,235,221,0.06)]">
                  {summary.runs.map((run) => (
                    <tr key={run.id} className="hover:bg-[#171A17]/50">
                      <td className="py-2.5 px-3 text-[#F3EBDD] font-sans max-w-xs truncate">{run.query}</td>
                      <td className="py-2.5 px-3 text-[#858983]">{run.category}</td>
                      <td className="py-2.5 px-3 text-[#A8D5BA]">{run.retrieval_latency_ms}ms</td>
                      <td className="py-2.5 px-3 text-[#D9C48A]">{run.generation_latency_ms}ms</td>
                      <td className="py-2.5 px-3 text-[#F3EBDD] font-bold">{run.total_latency_ms}ms</td>
                      <td className="py-2.5 px-3 text-[#A8D5BA]">{Math.round(run.confidence * 100)}%</td>
                      <td className="py-2.5 px-3">
                        {run.abstained ? (
                          <span className="text-[#D9C48A]">Abstained</span>
                        ) : run.grounded ? (
                          <span className="text-[#A8D5BA]">Grounded</span>
                        ) : (
                          <span className="text-[#D58A8A]">Blocked</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
