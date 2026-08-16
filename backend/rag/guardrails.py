import re
from typing import Tuple, Optional, List
from backend.models.schemas import GuardrailInfo, SourceItem
from backend.config import settings

class GuardrailEngine:
    """
    Multi-layer safety and hallucination prevention guardrail engine:
    1. Prompt Injection & Jailbreak Defense (Pre-retrieval)
    2. Out-of-Scope / Toxic query filter (Pre-retrieval)
    3. Retrieval Confidence & Evidence Thresholding (Post-retrieval Abstention)
    """

    # Comprehensive Prompt Injection patterns
    INJECTION_PATTERNS = [
        r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules|commands)",
        r"(?i)disregard\s+(all\s+)?(previous|prior)\s+(instructions|prompts)",
        r"(?i)reveal\s+(the\s+)?(system\s+prompt|hidden\s+instructions|system\s+message)",
        r"(?i)you\s+are\s+now\s+(in\s+)?(DAN|developer|jailbreak|unrestricted)\s+mode",
        r"(?i)forget\s+(everything|all)\s+you\s+were\s+told",
        r"(?i)act\s+as\s+an\s+unrestricted\s+ai",
        r"(?i)print\s+(the\s+)?(initial|system)\s+(prompt|instructions)",
        r"(?i)bypass\s+(all\s+)?(safety|content|ethical)\s+filters",
        r"(?i)override\s+(system|guardrail|security)\s+protocols",
        r"(?i)secret\s+key\s+is|password\s+is",
    ]

    # Out of scope / harmful indicators
    OUT_OF_SCOPE_PATTERNS = [
        r"(?i)(how\s+to\s+)?(create|make|build)\s+(a\s+)?(bomb|weapon|malware|ransomware|exploit)",
        r"(?i)sql\s+injection\s+payload|ddos\s+attack\s+script",
    ]

    @classmethod
    def check_query(cls, query: str) -> GuardrailInfo:
        """Evaluates incoming query for security and injection hazards before retrieval."""
        cleaned = query.strip()
        if not cleaned:
            return GuardrailInfo(
                passed=False,
                flagged_type="EMPTY_QUERY",
                reason="Query is empty.",
                abstained=True
            )

        # 1. Check for prompt injection
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, cleaned):
                return GuardrailInfo(
                    passed=False,
                    flagged_type="PROMPT_INJECTION",
                    reason="Potential prompt injection or instruction override attempt detected.",
                    abstained=True
                )

        # 2. Check for out-of-scope / harmful queries
        for pattern in cls.OUT_OF_SCOPE_PATTERNS:
            if re.search(pattern, cleaned):
                return GuardrailInfo(
                    passed=False,
                    flagged_type="OUT_OF_SCOPE",
                    reason="Query falls outside safe enterprise knowledge boundaries.",
                    abstained=True
                )

        return GuardrailInfo(passed=True, flagged_type=None, reason=None, abstained=False)

    @classmethod
    def check_evidence(
        cls,
        results: List[SourceItem],
        threshold: float = settings.CONFIDENCE_ABSTAIN_THRESHOLD
    ) -> Tuple[bool, Optional[str], float]:
        """
        Evaluates whether retrieved sources contain sufficient evidence to warrant generation.
        Returns: (has_sufficient_evidence, reason, top_confidence)
        """
        if not results:
            return (
                False,
                "No relevant documents found in knowledge base.",
                0.0
            )

        top_confidence = results[0].similarity

        if top_confidence < threshold:
            return (
                False,
                f"Top similarity ({round(top_confidence, 2)}) is below the required confidence threshold ({threshold}).",
                top_confidence
            )

        return True, None, top_confidence

guardrail_engine = GuardrailEngine()
