import time
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.models.schemas import BenchmarkQueryRun, BenchmarkSummary, QueryRequest
from backend.rag.pipeline import rag_pipeline

BENCHMARK_TEST_SUITE = [
    {"query": "What is the annual leave allowance for employees?", "category": "HR Policy"},
    {"query": "What are the core collaboration hours for remote employees?", "category": "HR Policy"},
    {"query": "How much is the monthly employee wellness stipend?", "category": "Benefits"},
    {"query": "What is the standard refund period for hardware purchases?", "category": "Customer Support"},
    {"query": "What is the restocking fee for returned products?", "category": "Customer Support"},
    {"query": "What is the maximum daily meal reimbursement for business travel?", "category": "Finance"},
    {"query": "When can employees book business class flights?", "category": "Finance"},
    {"query": "What is the standard maximum hotel rate per night for travel?", "category": "Finance"},
    {"query": "What is the mileage reimbursement rate for personal vehicles?", "category": "Finance"},
    {"query": "How many days do employees have to submit travel expenses?", "category": "Finance"},
    {"query": "What are the connectivity options for the VP-900 Voice Hub?", "category": "Hardware"},
    {"query": "How do I perform a hard factory reset on the VP-900 microphone?", "category": "Hardware"},
    {"query": "What should I do immediately if I lose my company laptop?", "category": "Security"},
    {"query": "Is SMS-based two factor authentication permitted?", "category": "Security"},
    {"query": "What is the anonymous ethics whistleblower phone number?", "category": "Compliance"},
    {"query": "What is the company policy on offshore cryptocurrency trading?", "category": "Abstention Test"},
]

class BenchmarkLab:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BenchmarkLab, cls).__new__(cls)
            cls._instance._last_summary = None
        return cls._instance

    @property
    def last_summary(self) -> Optional[BenchmarkSummary]:
        return self._last_summary

    async def run_benchmark(self, custom_queries: Optional[List[str]] = None) -> BenchmarkSummary:
        """
        Executes real test queries against the active knowledge base and computes exact empirical percentiles.
        """
        test_items = []
        if custom_queries:
            test_items = [{"query": q, "category": "Custom"} for q in custom_queries]
        else:
            test_items = BENCHMARK_TEST_SUITE

        runs: List[BenchmarkQueryRun] = []
        
        for idx, item in enumerate(test_items):
            q_text = item["query"]
            cat = item.get("category", "General")

            req = QueryRequest(query=q_text)
            resp = await rag_pipeline.process_query(req)

            answer_prev = resp.answer[:120] + "..." if len(resp.answer) > 120 else resp.answer

            run_record = BenchmarkQueryRun(
                id=f"run_{idx + 1}_{int(time.time())}",
                query=q_text,
                category=cat,
                retrieval_latency_ms=resp.latency.retrieval_ms,
                generation_latency_ms=resp.latency.generation_ms,
                total_latency_ms=resp.latency.total_rag_ms,
                success=True,
                confidence=resp.confidence,
                abstained=resp.abstained,
                grounded=resp.grounded,
                sources_count=len(resp.sources),
                answer_preview=answer_prev,
                timestamp=datetime.utcnow().strftime("%H:%M:%S.%f")[:-3]
            )
            runs.append(run_record)

        if not runs:
            return BenchmarkSummary(
                total_queries=0,
                successful_queries=0,
                p50_total_ms=0.0,
                p70_total_ms=0.0,
                p100_total_ms=0.0,
                avg_total_ms=0.0,
                min_total_ms=0.0,
                max_total_ms=0.0,
                p50_retrieval_ms=0.0,
                p70_retrieval_ms=0.0,
                p100_retrieval_ms=0.0,
                p50_generation_ms=0.0,
                p70_generation_ms=0.0,
                p100_generation_ms=0.0,
                target_ms=200.0,
                meets_target=True,
                runs=[]
            )

        total_latencies = [r.total_latency_ms for r in runs]
        ret_latencies = [r.retrieval_latency_ms for r in runs]
        gen_latencies = [r.generation_latency_ms for r in runs]

        # Calculate exact empirical percentiles
        p50 = float(np.percentile(total_latencies, 50))
        p70 = float(np.percentile(total_latencies, 70))
        p100 = float(np.percentile(total_latencies, 100))

        p50_ret = float(np.percentile(ret_latencies, 50))
        p70_ret = float(np.percentile(ret_latencies, 70))
        p100_ret = float(np.percentile(ret_latencies, 100))

        p50_gen = float(np.percentile(gen_latencies, 50))
        p70_gen = float(np.percentile(gen_latencies, 70))
        p100_gen = float(np.percentile(gen_latencies, 100))

        avg_lat = float(np.mean(total_latencies))
        min_lat = float(np.min(total_latencies))
        max_lat = float(np.max(total_latencies))

        summary = BenchmarkSummary(
            total_queries=len(runs),
            successful_queries=sum(1 for r in runs if r.success),
            p50_total_ms=round(p50, 2),
            p70_total_ms=round(p70, 2),
            p100_total_ms=round(p100, 2),
            avg_total_ms=round(avg_lat, 2),
            min_total_ms=round(min_lat, 2),
            max_total_ms=round(max_lat, 2),
            p50_retrieval_ms=round(p50_ret, 2),
            p70_retrieval_ms=round(p70_ret, 2),
            p100_retrieval_ms=round(p100_ret, 2),
            p50_generation_ms=round(p50_gen, 2),
            p70_generation_ms=round(p70_gen, 2),
            p100_generation_ms=round(p100_gen, 2),
            target_ms=200.0,
            meets_target=(p100 <= 200.0),
            runs=runs
        )

        self._last_summary = summary
        return summary

benchmark_lab = BenchmarkLab()
