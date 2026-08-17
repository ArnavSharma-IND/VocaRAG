import React, { useState, useEffect } from 'react';
import { Play, Gauge, Zap, Globe, Layers, Award, BarChart2 } from 'lucide-react';
import { api } from '../services/api';
import type { BenchmarkSummary, IREvalResult } from '../types';

export const BenchmarkLabPage: React.FC = () => {
  const [collection, setCollection] = useState<string>('msmarco');
  const [summary, setSummary] = useState<BenchmarkSummary | null>(null);
  const [irEval, setIrEval] = useState<IREvalResult | null>(null);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [isRunningIR, setIsRunningIR] = useState<boolean>(false);

  useEffect(() => {
    loadData(collection);
  }, [collection]);

  const loadData = async (col: string) => {
    try {
      const data = await api.getLatestBenchmark(col);
      setSummary(data);
      if (col === 'msmarco') {
        if (data?.ir_eval) {
          setIrEval(data.ir_eval);
        } else {
          const irData = await api.getIREval();
          setIrEval(irData);
        }
      }
    } catch (err) {
      console.error('Failed to load benchmark data:', err);
    }
  };

  const handleRun = async () => {
    setIsRunning(true);
    try {
      const data = await api.runBenchmark(undefined, collection);
      setSummary(data);
      if (data.ir_eval) setIrEval(data.ir_eval);
    } catch (err) {
      console.error('Benchmark execution failed:', err);
    } finally {
      setIsRunning(false);
    }
  };

  const handleRunIREval = async () => {
    setIsRunningIR(true);
    try {
      const data = await api.runIREval(10);
      setIrEval(data);
    } catch (err) {
      console.error('IR Eval execution failed:', err);
    } finally {
      setIsRunningIR(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Header & Collection Selector */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[rgba(243,235,221,0.12)] pb-6">
        <div>
          <h1 className="text-2xl font-bold font-editorial text-[#F3EBDD]">Latency & Accuracy Benchmark Lab</h1>
          <p className="text-xs text-[#858983] mt-1 font-mono">
            Empirical P50 / P70 / P100 percentile telemetry & formal IR evaluation metrics.
          </p>
        </div>

        {/* Collection Selector */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="inline-flex p-1 bg-[#111311] rounded-xl border border-[rgba(243,235,221,0.12)]">
            <button
              onClick={() => setCollection('msmarco')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                collection === 'msmarco' ? 'bg-[#1C563E] text-[#F3EBDD]' : 'text-[#858983] hover:text-[#F3EBDD]'
              }`}
            >
              <Globe className="w-3.5 h-3.5" />
              <span>Indic MSMARCO-XI (Task #2 Graded)</span>
            </button>
            <button
              onClick={() => setCollection('enterprise')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                collection === 'enterprise' ? 'bg-[#1C563E] text-[#F3EBDD]' : 'text-[#858983] hover:text-[#F3EBDD]'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Enterprise Policies (Demo)</span>
            </button>
          </div>

          <button
            onClick={handleRun}
            disabled={isRunning}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold bg-[#F3EBDD] text-[#080908] hover:bg-[#FFFFFF] transition-all disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 fill-current ${isRunning ? 'animate-spin' : ''}`} />
            <span>{isRunning ? 'RUNNING BENCHMARK...' : 'RUN BENCHMARK'}</span>
          </button>
        </div>
      </div>

      {/* Formal Information Retrieval Evaluation Card (MSMARCO-XI) */}
      {collection === 'msmarco' && (
        <div className="p-6 rounded-3xl bg-[#0C241B]/30 border border-[#1C563E]/60 space-y-5 font-mono">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[rgba(243,235,221,0.08)] pb-4">
            <div className="flex items-center space-x-2.5">
              <Award className="w-5 h-5 text-[#A8D5BA]" />
              <div>
                <h2 className="text-sm font-bold text-[#F3EBDD] uppercase tracking-wider">
                  Formal IR Evaluation (ai4bharat/MSMARCO-XI Gold Set)
                </h2>
                <p className="text-[11px] text-[#858983] font-sans">
                  Measured against {irEval?.total_queries || 0} gold relevance query-passage pairs across Hindi, Telugu & English.
                </p>
              </div>
            </div>

            <button
              onClick={handleRunIREval}
              disabled={isRunningIR}
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-[#171A17] hover:bg-[#1E231E] text-[#A8D5BA] border border-[#1C563E]/40 rounded-xl text-xs font-semibold transition-all disabled:opacity-50"
            >
              <BarChart2 className={`w-3.5 h-3.5 ${isRunningIR ? 'animate-spin' : ''}`} />
              <span>{isRunningIR ? 'EVALUATING IR METRICS...' : 'RE-EVALUATE IR GOLD SET'}</span>
            </button>
          </div>

          {irEval && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-4 bg-[#111311] rounded-2xl border border-[rgba(243,235,221,0.08)]">
                <span className="text-[10px] text-[#858983] uppercase tracking-wider block">RECALL@1</span>
                <p className="text-2xl font-bold text-[#A8D5BA] mt-1">{(irEval.recall_at_1 * 100).toFixed(1)}%</p>
                <span className="text-[10px] text-[#858983]">Top-1 exact passage match</span>
              </div>
              <div className="p-4 bg-[#111311] rounded-2xl border border-[rgba(243,235,221,0.08)]">
                <span className="text-[10px] text-[#858983] uppercase tracking-wider block">RECALL@5</span>
                <p className="text-2xl font-bold text-[#A8D5BA] mt-1">{(irEval.recall_at_5 * 100).toFixed(1)}%</p>
                <span className="text-[10px] text-[#858983]">Top-5 gold passage retrieval</span>
              </div>
              <div className="p-4 bg-[#111311] rounded-2xl border border-[rgba(243,235,221,0.08)]">
                <span className="text-[10px] text-[#858983] uppercase tracking-wider block">RECALL@10</span>
                <p className="text-2xl font-bold text-[#A8D5BA] mt-1">{(irEval.recall_at_10 * 100).toFixed(1)}%</p>
                <span className="text-[10px] text-[#858983]">Top-10 candidate coverage</span>
              </div>
              <div className="p-4 bg-[#111311] rounded-2xl border border-[rgba(243,235,221,0.08)]">
                <span className="text-[10px] text-[#858983] uppercase tracking-wider block">MEAN RECIPROCAL RANK (MRR)</span>
                <p className="text-2xl font-bold text-[#D9C48A] mt-1">{irEval.mrr.toFixed(3)}</p>
                <span className="text-[10px] text-[#858983]">Average 1/Rank score</span>
              </div>
            </div>
          )}

          {/* Per-Language Breakdown Table */}
          {irEval && Object.keys(irEval.per_language).length > 0 && (
            <div className="mt-4 pt-3 border-t border-[rgba(243,235,221,0.06)]">
              <span className="text-[10px] text-[#858983] uppercase tracking-widest block mb-2">
                PER-LANGUAGE IR ACCURACY BREAKDOWN:
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                {Object.entries(irEval.per_language).map(([lang, data]) => (
                  <div key={lang} className="p-3 bg-[#111311]/80 rounded-xl border border-[rgba(243,235,221,0.06)] flex items-center justify-between">
                    <div>
                      <span className="font-bold text-[#F3EBDD] uppercase">
                        {lang === 'hi' ? 'Hindi (hi)' : lang === 'te' ? 'Telugu (te)' : 'English (en)'}
                      </span>
                      <span className="text-[10px] text-[#858983] block">({data.total_queries} queries)</span>
                    </div>
                    <div className="text-right">
                      <span className="text-[#A8D5BA] font-bold block">R@5: {(data.recall_at_5 * 100).toFixed(1)}%</span>
                      <span className="text-[#D9C48A] text-[10px]">MRR: {data.mrr.toFixed(3)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Latency Percentile Telemetry */}
      {summary && (
        <div className="space-y-6 font-mono">
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
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-[#F3EBDD] uppercase tracking-wider">
                Benchmark Query Execution Log ({summary.runs.length} runs on [{collection.toUpperCase()}])
              </h2>
            </div>

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
