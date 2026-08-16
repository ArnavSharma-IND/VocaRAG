import logging
from fastapi import APIRouter
from backend.models.schemas import GuardrailCheckRequest, GuardrailCheckResponse
from backend.rag.guardrails import guardrail_engine
from backend.config import settings

router = APIRouter(prefix="/api/guardrails", tags=["Guardrails"])
logger = logging.getLogger(__name__)

@router.post("/check", response_model=GuardrailCheckResponse)
async def check_guardrails(req: GuardrailCheckRequest):
    """Evaluates query security and detects prompt injections or toxic inputs."""
    info = guardrail_engine.check_query(req.query)
    
    if not info.passed:
        risk = "HIGH" if info.flagged_type == "PROMPT_INJECTION" else "MEDIUM"
        action = "BLOCK"
    else:
        risk = "LOW"
        action = "ALLOW"

    return GuardrailCheckResponse(
        query=req.query,
        passed=info.passed,
        flagged_type=info.flagged_type,
        reason=info.reason,
        risk_level=risk,
        recommended_action=action
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
