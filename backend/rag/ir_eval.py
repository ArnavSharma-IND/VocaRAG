import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import numpy as np
from backend.models.schemas import IREvalResult
from backend.rag.embeddings import embedding_engine
from backend.rag.retriever import retriever_registry
from backend.rag.msmarco_loader import msmarco_loader

logger = logging.getLogger(__name__)


class IREvaluationEngine:
    """
    Computes formal Information Retrieval metrics over the MSMARCO-XI gold evaluation set:
    - Recall@1, Recall@3, Recall@5, Recall@10
    - Mean Reciprocal Rank (MRR)
    - Per-language breakdown (Hindi, Telugu, English)
    """

    _last_result: Optional[IREvalResult] = None

    @classmethod
    def evaluate(cls, top_k: int = 10, sample_limit: Optional[int] = None) -> IREvalResult:
        """
        Executes IR retrieval evaluation against the MSMARCO-XI FAISS vector index.
        """
        gold_pairs = msmarco_loader.gold_pairs
        if not gold_pairs:
            logger.warning("No gold pairs found in MSMARCO loader. Running corpus load...")
            msmarco_loader.load_msmarco_corpus()
            gold_pairs = msmarco_loader.gold_pairs

        if not gold_pairs:
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            return IREvalResult(
                total_queries=0,
                recall_at_1=0.0,
                recall_at_3=0.0,
                recall_at_5=0.0,
                recall_at_10=0.0,
                mrr=0.0,
                avg_retrieval_latency_ms=0.0,
                per_language={},
                evaluated_at=now_str
            )

        pairs_to_eval = gold_pairs[:sample_limit] if sample_limit else gold_pairs
        retriever = retriever_registry.get_retriever("msmarco")

        r1_hits = 0
        r3_hits = 0
        r5_hits = 0
        r10_hits = 0
        reciprocal_ranks = []
        latencies = []

        by_lang: Dict[str, Dict[str, Any]] = {}

        t_start_total = time.perf_counter()

        for item in pairs_to_eval:
            query = item["query"]
            gold_pid = item["passage_id"]
            lang = item["language"]

            if lang not in by_lang:
                by_lang[lang] = {
                    "total": 0, "r1": 0, "r5": 0, "r10": 0, "rr_sum": 0.0
                }
            by_lang[lang]["total"] += 1

            t0 = time.perf_counter()
            query_vec = embedding_engine.embed_query(query)
            results = retriever.search(query_vec, top_k=top_k, threshold=0.0)
            lat_ms = (time.perf_counter() - t0) * 1000
            latencies.append(lat_ms)

            # Find 1-indexed rank of the gold passage
            found_rank = None
            for rank_idx, res in enumerate(results, start=1):
                retrieved_pid = res.metadata.get("passage_id")
                # Also match if same query_id and language
                if retrieved_pid == gold_pid or (
                    res.metadata.get("query_id") == item.get("query_id") and
                    res.metadata.get("language") == lang and
                    res.metadata.get("is_selected")
                ):
                    found_rank = rank_idx
                    break

            if found_rank is not None:
                rr = 1.0 / found_rank
                reciprocal_ranks.append(rr)
                by_lang[lang]["rr_sum"] += rr

                if found_rank <= 1:
                    r1_hits += 1
                    by_lang[lang]["r1"] += 1
                if found_rank <= 3:
                    r3_hits += 1
                if found_rank <= 5:
                    r5_hits += 1
                    by_lang[lang]["r5"] += 1
                if found_rank <= 10:
                    r10_hits += 1
                    by_lang[lang]["r10"] += 1
            else:
                reciprocal_ranks.append(0.0)

        n = len(pairs_to_eval)
        r1 = round(r1_hits / n, 4) if n else 0.0
        r3 = round(r3_hits / n, 4) if n else 0.0
        r5 = round(r5_hits / n, 4) if n else 0.0
        r10 = round(r10_hits / n, 4) if n else 0.0
        mrr = round(float(np.mean(reciprocal_ranks)), 4) if reciprocal_ranks else 0.0
        avg_lat = round(float(np.mean(latencies)), 2) if latencies else 0.0

        # Language breakdown
        lang_summary = {}
        for l_code, l_data in by_lang.items():
            l_total = l_data["total"]
            lang_summary[l_code] = {
                "total_queries": l_total,
                "recall_at_1": round(l_data["r1"] / l_total, 4) if l_total else 0.0,
                "recall_at_5": round(l_data["r5"] / l_total, 4) if l_total else 0.0,
                "recall_at_10": round(l_data["r10"] / l_total, 4) if l_total else 0.0,
                "mrr": round(l_data["rr_sum"] / l_total, 4) if l_total else 0.0,
            }

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        eval_result = IREvalResult(
            total_queries=n,
            recall_at_1=r1,
            recall_at_3=r3,
            recall_at_5=r5,
            recall_at_10=r10,
            mrr=mrr,
            avg_retrieval_latency_ms=avg_lat,
            per_language=lang_summary,
            evaluated_at=now_str
        )

        cls._last_result = eval_result
        logger.info(
            f"MSMARCO-XI IR Evaluation ({n} queries): "
            f"Recall@1={r1*100}%, Recall@5={r5*100}%, MRR={mrr}, Avg Latency={avg_lat}ms"
        )
        return eval_result

    @classmethod
    def get_last_result(cls) -> Optional[IREvalResult]:
        return cls._last_result


ir_eval_engine = IREvaluationEngine()
