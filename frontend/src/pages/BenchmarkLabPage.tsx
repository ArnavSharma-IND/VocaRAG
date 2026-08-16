import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  Play,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { api } from '../services/api';
import type { BenchmarkSummary } from '../types';

export const BenchmarkLabPage: React.FC = () => {
  const [summary, setSummary] = useState<BenchmarkSummary | null>(null);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadLatestBenchmark();
  }, []);

  const loadLatestBenchmark = async () => {
    try {
      const data = await api.getLatestBenchmark();
      setSummary(data);
    } catch (err: any) {
      console.error('Failed to load benchmark:', err);
    }
  };

  const handleRunBenchmark = async () => {
    setIsRunning(true);
    setError(null);
    try {
      const data = await api.runBenchmark();
      setSummary(data);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Benchmark execution failed.');
    } finally {
      setIsRunning(false);
    }
  };

  const chartData =
    summary?.runs.map((r, i) => ({
      name: `Q${i + 1}`,
      query: r.query,
      total: r.total_latency_ms,
      retrieval: r.retrieval_latency_ms,
      generation: r.generation_latency_ms,
      confidence: Math.round(r.confidence * 100),
      category: r.category,
    })) || [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 font-mono">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-[#111311] border border-[rgba(243,235,221,0.12)] text-[#C9C2B5] text-[10px] uppercase tracking-widest mb-2">
            <BarChart3 className="w-3 h-3 text-[#1C563E]" />
            <span>EMPIRICAL LATENCY BENCHMARKING</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#F3EBDD] tracking-tight">
            BENCHMARK LAB
          </h1>
          <p className="text-xs text-[#858983] mt-1 font-sans">
            Execute real automated query batches against the live vector index and calculate exact empirical P50, P70, and P100 latency percentiles.
          </p>
        </div>

        <button
          onClick={handleRunBenchmark}
          disabled={isRunning}
          className="flex items-center space-x-2 px-5 py-2.5 rounded-2xl bg-[#F3EBDD] hover:bg-[#FFFFFF] text-[#080908] font-bold text-xs shadow-md transition-all disabled:opacity-40 hover-lift"
        >
          {isRunning ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-[#080908] border-t-transparent rounded-full animate-spin" />
              <span>RUNNING BATCH...</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-[#123B2A] text-[#123B2A]" />
              <span>RUN BENCHMARK SUITE</span>
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-2xl bg-[#D58A8A]/10 border border-[#D58A8A]/30 text-[#D58A8A] text-xs">
          {error}
        </div>
      )}

      {/* Large Metric Display Typography */}
      {summary ? (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <div className="p-6 rounded-3xl bg-[#111311] border border-[rgba(243,235,221,0.14)] shadow-xl flex flex-col justify-between">
            <span className="text-[10px] font-bold uppercase tracking-widest text-[#858983]">
              P50 LATENCY (MEDIAN)
            </span>
            <div className="text-4xl sm:text-5xl font-bold text-[#F3EBDD] my-2">
              {summary.p50_total_ms}<span className="text-sm text-[#858983] font-normal ml-1">ms</span>
            </div>
            <span className="text-[10px] text-[#A8D5BA]">
              Retrieval P50: {summary.p50_retrieval_ms}ms
            </span>
          </div>

          <div className="p-6 rounded-3xl bg-[#111311] border border-[rgba(243,235,221,0.14)] shadow-xl flex flex-col justify-between">
            <span className="text-[10px] font-bold uppercase tracking-widest text-[#858983]">
              P70 LATENCY
            </span>
            <div className="text-4xl sm:text-5xl font-bold text-[#F3EBDD] my-2">
              {summary.p70_total_ms}<span className="text-sm text-[#858983] font-normal ml-1">ms</span>
            </div>
            <span className="text-[10px] text-[#858983]">
              70% requests under threshold
            </span>
          </div>

          <div className="p-6 rounded-3xl bg-[#111311] border border-[rgba(243,235,221,0.14)] shadow-xl flex flex-col justify-between">
            <span className="text-[10px] font-bold uppercase tracking-widest text-[#858983]">
              P100 MAX LATENCY
            </span>
            <div
              className={`text-4xl sm:text-5xl font-bold my-2 ${
                summary.p100_total_ms <= 200 ? 'text-[#F3EBDD]' : 'text-[#D9C48A]'
              }`}
            >
              {summary.p100_total_ms}<span className="text-sm text-[#858983] font-normal ml-1">ms</span>
            </div>
            <span className="text-[10px] text-[#858983]">
              TARGET: &lt;200ms ({summary.meets_target ? '✓ PASSED' : 'ABOVE TARGET'})
            </span>
          </div>
        </div>
      ) : (
        <div className="p-12 text-center text-[#858983] text-xs">
          NO BENCHMARKS YET. Run the benchmark suite.
        </div>
      )}

      {/* Latency Distribution Minimal Graph */}
      {summary && chartData.length > 0 && (
        <div className="bg-[#111311] rounded-3xl p-6 sm:p-7 border border-[rgba(243,235,221,0.14)] shadow-xl mb-8">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-6">
            <div>
              <h3 className="font-bold text-xs uppercase tracking-widest text-[#858983]">
                LATENCY DISTRIBUTION
              </h3>
              <p className="text-[11px] text-[#C9C2B5] mt-0.5">
                Target: &lt;200ms • Average: {summary.avg_total_ms}ms across {summary.total_queries} queries
              </p>
            </div>

            <div className="flex items-center space-x-3 text-[10px]">
              <span className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#1C563E]" />
                <span className="text-[#C9C2B5]">Total Pipeline</span>
              </span>
              <span className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#A8D5BA]" />
                <span className="text-[#C9C2B5]">FAISS Retrieval</span>
              </span>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorTotalDark" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#1C563E" stopOpacity={0.6} />
                    <stop offset="95%" stopColor="#1C563E" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="colorRetDark" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#A8D5BA" stopOpacity={0.5} />
                    <stop offset="95%" stopColor="#A8D5BA" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="2 2" stroke="rgba(243,235,221,0.06)" />
                <XAxis dataKey="name" stroke="#858983" fontSize={10} />
                <YAxis stroke="#858983" fontSize={10} unit="ms" />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="p-3 bg-[#080908] border border-[rgba(243,235,221,0.18)] rounded-xl shadow-2xl text-xs space-y-1 font-mono">
                          <p className="font-bold text-[#F3EBDD]">{data.query}</p>
                          <p className="text-[#858983]">Category: {data.category}</p>
                          <p className="text-[#A8D5BA]">Total: {data.total}ms</p>
                          <p className="text-[#C9C2B5]">Retrieval: {data.retrieval}ms</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <ReferenceLine
                  y={summary.p50_total_ms}
                  label={{ value: `P50: ${summary.p50_total_ms}ms`, fill: '#A8D5BA', fontSize: 10 }}
                  stroke="#1C563E"
                  strokeDasharray="3 3"
                />
                <Area
                  type="monotone"
                  dataKey="total"
                  stroke="#1C563E"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorTotalDark)"
                />
                <Area
                  type="monotone"
                  dataKey="retrieval"
                  stroke="#A8D5BA"
                  strokeWidth={1.5}
                  fillOpacity={1}
                  fill="url(#colorRetDark)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Query Execution Log Table */}
      {summary && (
        <div className="bg-[#111311] rounded-3xl p-6 border border-[rgba(243,235,221,0.14)] shadow-xl overflow-hidden mb-8">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-[rgba(243,235,221,0.08)]">
            <h3 className="font-bold text-xs uppercase tracking-widest text-[#858983]">
              EXECUTION LOG ({summary.runs.length} RUNS)
            </h3>
            <span className="text-[10px] text-[#858983]">ACTUAL MEASURED RUNS</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[10px] uppercase tracking-wider text-[#858983] border-b border-[rgba(243,235,221,0.08)] pb-2">
                <tr>
                  <th className="py-2 px-2">#</th>
                  <th className="py-2 px-3">EVALUATION QUERY</th>
                  <th className="py-2 px-3">CATEGORY</th>
                  <th className="py-2 px-3">RETRIEVAL</th>
                  <th className="py-2 px-3">TOTAL</th>
                  <th className="py-2 px-3">STATUS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[rgba(243,235,221,0.06)]">
                {summary.runs.map((r, i) => (
                  <tr key={r.id || i} className="hover:bg-[#171A17]/60 transition-colors">
                    <td className="py-2.5 px-2 font-bold text-[#858983]">
                      {String(i + 1).padStart(2, '0')}
                    </td>
                    <td className="py-2.5 px-3 text-[#F3EBDD] font-medium max-w-sm truncate">
                      {r.query}
                    </td>
                    <td className="py-2.5 px-3 text-[10px] text-[#858983]">
                      {r.category}
                    </td>
                    <td className="py-2.5 px-3 text-[#A8D5BA] font-bold">
                      {r.retrieval_latency_ms}ms
                    </td>
                    <td className="py-2.5 px-3 text-[#F3EBDD] font-bold">
                      {r.total_latency_ms}ms
                    </td>
                    <td className="py-2.5 px-3">
                      {r.abstained ? (
                        <span className="text-[10px] text-[#D9C48A] font-bold">ABSTAINED</span>
                      ) : (
                        <span className="text-[10px] text-[#A8D5BA] font-bold">GROUNDED</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
