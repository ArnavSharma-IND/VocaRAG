import logging
from fastapi import APIRouter
from backend.models.schemas import GuardrailCheckRequest, GuardrailCheckResponse
from backend.rag.guardrails import guardrail_engine
from backend.config import settings

router = APIRouter(prefix="/api/guardrails", tags=["Guardrails"])
logger = logging.getLogger(__name__)

from backend.rag.retriever import retriever_registry
from backend.rag.embeddings import embedding_engine
import time

@router.post("/check", response_model=GuardrailCheckResponse)
async def check_guardrails(req: GuardrailCheckRequest):
    """Evaluates query security against adversarial prompt injections and checks target collection grounding evidence."""
    t0 = time.perf_counter()
    target_collection = req.collection if req.collection in ["msmarco", "enterprise"] else "msmarco"
    info = guardrail_engine.check_query(req.query)
    
    flagged_type = info.flagged_type
    reason = info.reason
    evidence_confidence = None

    if not info.passed:
        risk = "HIGH" if info.flagged_type == "PROMPT_INJECTION" else "MEDIUM"
        action = "BLOCK"
        passed = False
    else:
        # Pre-retrieval passed; evaluate evidence confidence in target collection
        try:
            retriever = retriever_registry.get_retriever(target_collection)
            if retriever and retriever.is_indexed and retriever.total_chunks > 0:
                query_vec = embedding_engine.embed_text(req.query)
                matches = retriever.search(query_vec, top_k=3, min_similarity=0.0)
                if matches:
                    evidence_confidence = float(matches[0].similarity)
                    if evidence_confidence < settings.CONFIDENCE_ABSTAIN_THRESHOLD:
                        passed = True  # Query is benign, but will trigger explicit abstention
                        risk = "MEDIUM"
                        action = "ABSTAIN"
                        flagged_type = "LOW_EVIDENCE_CONFIDENCE"
                        reason = f"Top retrieval similarity ({evidence_confidence:.2f}) in '{target_collection}' is below abstention threshold ({settings.CONFIDENCE_ABSTAIN_THRESHOLD}). RAG pipeline will safely abstain."
                    else:
                        passed = True
                        risk = "LOW"
                        action = "ALLOW"
                        reason = f"Query passed all injection shields and grounded in '{target_collection}' with {evidence_confidence*100:.1f}% confidence."
                else:
                    passed = True
                    risk = "MEDIUM"
                    action = "ABSTAIN"
                    flagged_type = "EMPTY_RETRIEVAL"
                    reason = f"No context matches found in target collection '{target_collection}'. RAG pipeline will safely abstain."
            else:
                passed = True
                risk = "LOW"
                action = "ALLOW"
        except Exception as e:
            logger.warning(f"Guardrail collection search check error: {e}")
            passed = True
            risk = "LOW"
            action = "ALLOW"

    latency_ms = round((time.perf_counter() - t0) * 1000, 2)

    return GuardrailCheckResponse(
        query=req.query,
        passed=passed,
        flagged_type=flagged_type,
        reason=reason,
        risk_level=risk,
        recommended_action=action,
        collection=target_collection,
        evidence_confidence=evidence_confidence,
        latency_ms=latency_ms
    )

@router.get("/rules")
async def get_guardrail_rules():
    """Returns active guardrail configuration and pattern rules."""
    return {
        "confidence_abstain_threshold": settings.CONFIDENCE_ABSTAIN_THRESHOLD,
        "prompt_injection_filter": "Active (10 heuristic regex patterns)",
        "out_of_scope_filter": "Active",
        "empty_retrieval_guard": "Active (Zero LLM invocation on empty results)",
        "injection_patterns_count": len(guardrail_engine.INJECTION_PATTERNS)
    }
