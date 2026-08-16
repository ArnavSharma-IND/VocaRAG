import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Body
from backend.models.schemas import BenchmarkSummary
from backend.rag.benchmark import benchmark_lab, BENCHMARK_TEST_SUITE

router = APIRouter(prefix="/api/benchmark", tags=["Benchmark Lab"])
logger = logging.getLogger(__name__)

@router.post("/run", response_model=BenchmarkSummary)
async def run_benchmark(custom_queries: Optional[List[str]] = Body(None, embed=True)):
    """
    Executes benchmark queries through the full RAG pipeline and returns
    accurate empirical P50, P70, and P100 latency percentiles.
    """
    try:
        summary = await benchmark_lab.run_benchmark(custom_queries)
        return summary
    except Exception as e:
        logger.error(f"Benchmark execution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Benchmark execution failed: {str(e)}")

@router.get("", response_model=Optional[BenchmarkSummary])
@router.get("/latest", response_model=Optional[BenchmarkSummary])
async def get_latest_benchmark():
    """Returns the most recent benchmark summary, or auto-runs if none exists."""
    if benchmark_lab.last_summary is None:
        return await benchmark_lab.run_benchmark()
    return benchmark_lab.last_summary

@router.get("/suite")
async def get_benchmark_suite():
    """Returns the predefined 16 benchmark test questions and categories."""
    return BENCHMARK_TEST_SUITE
