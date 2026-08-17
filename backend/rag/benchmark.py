import time
import numpy as np
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.models.schemas import BenchmarkQueryRun, BenchmarkSummary, QueryRequest
from backend.rag.pipeline import rag_pipeline
from backend.rag.ir_eval import ir_eval_engine

# MSMARCO-XI Multilingual Benchmark Suite (Hindi, Telugu, English)
MSMARCO_BENCHMARK_SUITE = [
    # Hindi (Devanagari)
    {"query": "भारत की राजधानी क्या है?", "category": "Hindi General Knowledge", "collection": "msmarco"},
    {"query": "प्रकाश संश्लेषण क्या है?", "category": "Hindi Science", "collection": "msmarco"},
    {"query": "सौर मंडल में कितने ग्रह हैं?", "category": "Hindi Astronomy", "collection": "msmarco"},
    {"query": "पानी का रासायनिक सूत्र क्या है?", "category": "Hindi Science", "collection": "msmarco"},
    {"query": "कंप्यूटर नेटवर्क क्या है?", "category": "Hindi Technology", "collection": "msmarco"},
    # Telugu
    {"query": "భారతదేశ రాజధాని ఏది?", "category": "Telugu General Knowledge", "collection": "msmarco"},
    {"query": "సౌర వ్యవస్థలో ఎన్ని గ్రహాలు ఉన్నాయి?", "category": "Telugu Astronomy", "collection": "msmarco"},
    {"query": "నీటి రసాయన సూత్రం ఏమిటి?", "category": "Telugu Science", "collection": "msmarco"},
    {"query": "కిరణజన్య సంయోగక్రియ అంటే ఏమిటి?", "category": "Telugu Science", "collection": "msmarco"},
    # English MS MARCO
    {"query": "What is photosynthesis and how does it work?", "category": "English Science", "collection": "msmarco"},
    {"query": "What is the capital of India?", "category": "English Geography", "collection": "msmarco"},
    {"query": "How many planets are in the solar system?", "category": "English Astronomy", "collection": "msmarco"},
    {"query": "What is an API in software engineering?", "category": "English Technology", "collection": "msmarco"},
    {"query": "What causes the aurora borealis?", "category": "English Science", "collection": "msmarco"},
    # Abstention Tests (Multilingual)
    {"query": "What is the population of a fictional planet called Xylon-9?", "category": "Abstention (English)", "collection": "msmarco"},
    {"query": "काल्पनिक ग्रह ज़ाइलॉन-9 की जनसंख्या कितनी है?", "category": "Abstention (Hindi)", "collection": "msmarco"},
]

# Enterprise Policy Benchmark Suite
ENTERPRISE_BENCHMARK_SUITE = [
    {"query": "What is the annual leave allowance for employees?", "category": "HR Policy", "collection": "enterprise"},
    {"query": "What are the core collaboration hours for remote employees?", "category": "HR Policy", "collection": "enterprise"},
    {"query": "How much is the monthly employee wellness stipend?", "category": "Benefits", "collection": "enterprise"},
    {"query": "What is the standard refund period for hardware purchases?", "category": "Customer Support", "collection": "enterprise"},
    {"query": "What is the restocking fee for returned products?", "category": "Customer Support", "collection": "enterprise"},
    {"query": "What is the maximum daily meal reimbursement for business travel?", "category": "Finance", "collection": "enterprise"},
    {"query": "When can employees book business class flights?", "category": "Finance", "collection": "enterprise"},
    {"query": "What is the standard maximum hotel rate per night for travel?", "category": "Finance", "collection": "enterprise"},
    {"query": "What is the mileage reimbursement rate for personal vehicles?", "category": "Finance", "collection": "enterprise"},
    {"query": "How many days do employees have to submit travel expenses?", "category": "Finance", "collection": "enterprise"},
    {"query": "What are the connectivity options for the VP-900 Voice Hub?", "category": "Hardware", "collection": "enterprise"},
    {"query": "How do I perform a hard factory reset on the VP-900 microphone?", "category": "Hardware", "collection": "enterprise"},
    {"query": "What should I do immediately if I lose my company laptop?", "category": "Security", "collection": "enterprise"},
    {"query": "Is SMS-based two factor authentication permitted?", "category": "Security", "collection": "enterprise"},
    {"query": "What is the anonymous ethics whistleblower phone number?", "category": "Compliance", "collection": "enterprise"},
    {"query": "What is the company policy on offshore cryptocurrency trading?", "category": "Abstention Test", "collection": "enterprise"},
]


class BenchmarkLab:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BenchmarkLab, cls).__new__(cls)
            cls._instance._last_summary = {}
        return cls._instance

    def get_last_summary(self, collection: str = "msmarco") -> Optional[BenchmarkSummary]:
        return self._last_summary.get(collection)

    async def run_benchmark(
        self,
        collection: str = "msmarco",
        custom_queries: Optional[List[str]] = None
    ) -> BenchmarkSummary:
        """
        Executes benchmark queries through the RAG pipeline on the specified collection.
        Computes P50/P70/P100 latency percentiles and attaches formal IR evaluation metrics.
        """
        test_items = []
        if custom_queries:
            test_items = [{"query": q, "category": "Custom", "collection": collection} for q in custom_queries]
        elif collection == "enterprise":
            test_items = ENTERPRISE_BENCHMARK_SUITE
        else:
            test_items = MSMARCO_BENCHMARK_SUITE

        runs: List[BenchmarkQueryRun] = []
        
        for idx, item in enumerate(test_items):
            q_text = item["query"]
            cat = item.get("category", "General")
            target_coll = item.get("collection", collection)

            req = QueryRequest(query=q_text, collection=target_coll)
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
                timestamp=datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3]
            )
            runs.append(run_record)

        # Run IR Eval for MSMARCO collection
        ir_eval_result = None
        if collection == "msmarco":
            try:
                ir_eval_result = ir_eval_engine.evaluate(top_k=10)
            except Exception as e:
                logger.error(f"Error during IR evaluation: {e}")

        if not runs:
            return BenchmarkSummary(
                collection=collection,
                total_queries=0, successful_queries=0,
                p50_total_ms=0.0, p70_total_ms=0.0, p100_total_ms=0.0,
                avg_total_ms=0.0, min_total_ms=0.0, max_total_ms=0.0,
                p50_retrieval_ms=0.0, p70_retrieval_ms=0.0, p100_retrieval_ms=0.0,
                p50_generation_ms=0.0, p70_generation_ms=0.0, p100_generation_ms=0.0,
                target_ms=200.0, meets_retrieval_target=True, meets_e2e_target=True,
                meets_target=True, ir_eval=ir_eval_result, runs=[]
            )

        total_latencies = [r.total_latency_ms for r in runs]
        ret_latencies = [r.retrieval_latency_ms for r in runs]
        gen_latencies = [r.generation_latency_ms for r in runs]

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

        meets_ret = (p100_ret <= 200.0)
        meets_e2e = (p100 <= 200.0)

        summary = BenchmarkSummary(
            collection=collection,
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
            meets_retrieval_target=meets_ret,
            meets_e2e_target=meets_e2e,
            meets_target=meets_ret,
            ir_eval=ir_eval_result,
            runs=runs
        )

        self._last_summary[collection] = summary
        return summary

benchmark_lab = BenchmarkLab()
