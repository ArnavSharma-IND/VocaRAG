import re
import logging
from typing import Tuple, Optional, List, Set
import numpy as np
from backend.models.schemas import GuardrailInfo, SourceItem
from backend.config import settings

logger = logging.getLogger(__name__)


def _extract_char_ngrams(text: str, n: int = 3) -> Set[str]:
    """
    Extracts normalized character n-grams.
    Script-agnostic: operates identically across Latin, Devanagari, Telugu, Bengali, etc.
    """
    # Normalize whitespaces and lowercase
    cleaned = re.sub(r'\s+', ' ', text.strip().lower())
    if len(cleaned) < n:
        return {cleaned} if cleaned else set()
    return {cleaned[i:i + n] for i in range(len(cleaned) - n + 1)}


class GuardrailEngine:
    """
    Multi-layer safety and hallucination prevention guardrail engine:
    1. Prompt Injection & Jailbreak Defense (Pre-retrieval)
    2. Out-of-Scope / Harmful query filter (Pre-retrieval)
    3. Retrieval Confidence & Evidence Thresholding (Post-retrieval Abstention)
    4. Multilingual & Script-Agnostic Post-Generation Groundedness Verification
    """

    # Comprehensive Prompt Injection patterns (English + transliterated Indic)
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
        # Transliterated Hindi injection attempts
        r"(?i)pichle\s+(sabhi\s+)?nirdesh(on)?\s+(ko\s+)?bhool\s+ja",
        r"(?i)system\s+prompt\s+dikha",
        r"(?i)sab\s+niyam\s+tod",
        # Devanagari Hindi injection attempts
        r"पिछले\s+(सभी\s+)?निर्देश(ों)?\s+(को\s+)?भूल\s+जाओ?",
        r"सिस्टम\s+प्रॉम्प्ट\s+दिखाओ?",
        # Telugu injection attempts
        r"మునుపటి\s+సూచనలను\s+విస్మరించండి",
        # Additional patterns
        r"(?i)pretend\s+you\s+are\s+(not\s+)?(an?\s+)?(ai|chatbot|assistant)",
        r"(?i)simulate\s+(being\s+)?(hacked|compromised|jailbroken)",
        r"(?i)enter\s+(sudo|admin|root|developer)\s+mode",
    ]

    # Expanded out-of-scope / harmful indicators
    OUT_OF_SCOPE_PATTERNS = [
        r"(?i)(how\s+to\s+)?(create|make|build|assemble)\s+(a\s+)?(bomb|weapon|explosive|malware|ransomware|exploit|virus)",
        r"(?i)sql\s+injection\s+payload|ddos\s+attack\s+script|xss\s+attack",
        # Self-harm and violence
        r"(?i)(how\s+to\s+)?(commit|attempt)\s+(suicide|self.harm)",
        r"(?i)(how\s+to\s+)?poison\s+(someone|a\s+person)",
        r"(?i)(how\s+to\s+)?(kidnap|abduct|stalk)\s+(someone|a\s+person)",
        # Drug synthesis
        r"(?i)(how\s+to\s+)?(synthesize|cook|manufacture)\s+(meth|cocaine|heroin|fentanyl|drugs)",
        # Social engineering / phishing
        r"(?i)(how\s+to\s+)?(phish|scam|social\s+engineer|catfish)",
        r"(?i)(write|create|generate)\s+(a\s+)?(phishing|scam)\s+(email|message|page)",
        # Personal data extraction
        r"(?i)(give|tell|reveal|show)\s+(me\s+)?(someone.s|their|his|her)\s+(address|phone|ssn|credit\s+card|password)",
        # Hate speech
        r"(?i)(write|generate)\s+(hateful|racist|sexist|discriminatory)\s+(content|speech|text)",
        # NSFW
        r"(?i)(write|generate|create)\s+(explicit|pornographic|nsfw|sexual)\s+(content|story|text|image)",
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
                    reason="Query falls outside safe knowledge boundaries.",
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

    @classmethod
    def check_groundedness(
        cls,
        answer_text: str,
        sources: List[SourceItem],
        threshold: float = settings.GROUNDEDNESS_THRESHOLD
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Multilingual, script-agnostic post-generation groundedness verification.
        Uses character 3-gram and 4-gram overlap + Unicode word token overlap.
        Works seamlessly across English, Hindi (Devanagari), Telugu, Bengali, and code-mixed text.
        
        Returns: (is_grounded, groundedness_score, reason)
        """
        if not answer_text or not sources:
            return False, 0.0, "No answer or sources to verify."

        # Strip citations like [Source 1], [Note: ...] from answer before computing overlap
        clean_answer = re.sub(r'\[Source\s*\d+\]', '', answer_text)
        clean_answer = re.sub(r'\[Note:.*?\]', '', clean_answer).strip()

        if not clean_answer:
            return True, 1.0, None

        # Concatenate all source content
        source_text = " ".join(s.content for s in sources)

        # 1. Character 3-gram overlap (script-agnostic)
        ans_3grams = _extract_char_ngrams(clean_answer, n=3)
        src_3grams = _extract_char_ngrams(source_text, n=3)
        
        # 2. Character 4-gram overlap (script-agnostic)
        ans_4grams = _extract_char_ngrams(clean_answer, n=4)
        src_4grams = _extract_char_ngrams(source_text, n=4)

        overlap_3g = len(ans_3grams & src_3grams) / len(ans_3grams) if ans_3grams else 0.0
        overlap_4g = len(ans_4grams & src_4grams) / len(ans_4grams) if ans_4grams else 0.0

        # 3. Unicode word token overlap (matches any language word characters)
        ans_tokens = set(re.findall(r'[\w\u0900-\u0D7F\u0C00-\u0C7F]{2,}', clean_answer.lower()))
        src_tokens = set(re.findall(r'[\w\u0900-\u0D7F\u0C00-\u0C7F]{2,}', source_text.lower()))

        token_overlap = len(ans_tokens & src_tokens) / len(ans_tokens) if ans_tokens else 0.0

        # Blended groundedness metric: 40% char 3-gram + 30% char 4-gram + 30% token overlap
        groundedness_score = (0.40 * overlap_3g) + (0.30 * overlap_4g) + (0.30 * token_overlap)

        if groundedness_score < threshold:
            return (
                False,
                round(groundedness_score, 4),
                f"Low groundedness ({round(groundedness_score * 100, 1)}%). "
                f"Answer may not be fully supported by retrieved evidence."
            )

        return True, round(groundedness_score, 4), None


guardrail_engine = GuardrailEngine()
