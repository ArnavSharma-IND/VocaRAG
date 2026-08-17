import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Body
from backend.models.schemas import BenchmarkSummary, IREvalResult
from backend.rag.benchmark import benchmark_lab, MSMARCO_BENCHMARK_SUITE, ENTERPRISE_BENCHMARK_SUITE
from backend.rag.ir_eval import ir_eval_engine

router = APIRouter(prefix="/api/benchmark", tags=["Benchmark Lab"])
logger = logging.getLogger(__name__)

@router.post("/run", response_model=BenchmarkSummary)
async def run_benchmark(
    collection: str = Query("msmarco"),
    custom_queries: Optional[List[str]] = Body(None, embed=True)
):
    """
    Executes benchmark queries through the full RAG pipeline on the specified collection
    (default: 'msmarco' for Task #2 Graded evaluation, or 'enterprise' for Demo).
    """
    try:
        summary = await benchmark_lab.run_benchmark(collection=collection, custom_queries=custom_queries)
        return summary
    except Exception as e:
        logger.error(f"Benchmark execution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Benchmark execution failed: {str(e)}")

@router.get("/latest", response_model=Optional[BenchmarkSummary])
async def get_latest_benchmark(collection: str = Query("msmarco")):
    """Returns the most recent benchmark summary for the collection, or auto-runs if none exists."""
    last = benchmark_lab.get_last_summary(collection)
    if last is None:
        return await benchmark_lab.run_benchmark(collection=collection)
    return last

@router.post("/ir-eval", response_model=IREvalResult)
async def run_ir_eval(top_k: int = Query(10), sample_limit: Optional[int] = Query(None)):
    """
    Executes formal Information Retrieval evaluation over the MSMARCO-XI dataset:
    Computes Recall@1, Recall@3, Recall@5, Recall@10, and MRR.
    """
    try:
        result = ir_eval_engine.evaluate(top_k=top_k, sample_limit=sample_limit)
        return result
    except Exception as e:
        logger.error(f"IR evaluation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"IR evaluation failed: {str(e)}")

@router.get("/ir-eval", response_model=Optional[IREvalResult])
async def get_ir_eval():
    """Returns cached IR evaluation metrics or runs on-demand."""
    cached = ir_eval_engine.get_last_result()
    if cached is None:
        return ir_eval_engine.evaluate(top_k=10)
    return cached

@router.get("/suite")
async def get_benchmark_suite(collection: str = Query("msmarco")):
    """Returns the predefined benchmark test questions for the requested collection."""
    if collection == "enterprise":
        return ENTERPRISE_BENCHMARK_SUITE
    return MSMARCO_BENCHMARK_SUITE
