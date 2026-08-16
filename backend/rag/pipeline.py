import time
import logging
from typing import Optional
from backend.config import settings
from backend.models.schemas import QueryRequest, AskResponse, LatencyBreakdown, GuardrailInfo
from backend.rag.guardrails import guardrail_engine
from backend.rag.embeddings import embedding_engine
from backend.rag.retriever import retriever_registry
from backend.rag.generator import llm_generator

logger = logging.getLogger(__name__)

class RAGPipeline:
    async def process_query(self, req: QueryRequest) -> AskResponse:
        """
        Executes the full Voice-to-Answer RAG Pipeline with real microsecond latency tracking.
        Two-sided Guardrailing:
        1. Pre-retrieval: Prompt injection & safety patterns.
        2. Pre-generation: Retrieval confidence & threshold check.
        3. Post-generation: Token-overlap groundedness check & LLM abstention detection.
        """
        t_pipeline_start = time.perf_counter()
        
        # 1. Query Preprocessing & Normalization
        t0 = time.perf_counter()
        cleaned_query = req.query.strip()
        top_k = req.top_k or settings.DEFAULT_TOP_K
        threshold = req.threshold if req.threshold is not None else settings.DEFAULT_SIMILARITY_THRESHOLD
        collection = req.collection or settings.DEFAULT_COLLECTION
        preprocessing_ms = round((time.perf_counter() - t0) * 1000, 2)

        # 2. Pre-retrieval Security & Injection Guardrail
        t0 = time.perf_counter()
        pre_guard = guardrail_engine.check_query(cleaned_query)
        guardrail_ms = round((time.perf_counter() - t0) * 1000, 2)

        if not pre_guard.passed:
            total_rag_ms = round((time.perf_counter() - t_pipeline_start) * 1000, 2)
            voice_ms = req.voice_latency_ms
            total_pipe_ms = round(total_rag_ms + (voice_ms or 0.0), 2)
            
            return AskResponse(
                query=cleaned_query,
                answer=f"Request blocked by safety guardrails: {pre_guard.reason}",
                grounded=False,
                abstained=True,
                confidence=0.0,
                sources=[],
                latency=LatencyBreakdown(
                    voice_stt_ms=voice_ms,
                    preprocessing_ms=preprocessing_ms,
                    guardrail_ms=guardrail_ms,
                    embedding_ms=0.0,
                    retrieval_ms=0.0,
                    prompt_construction_ms=0.0,
                    generation_ms=0.0,
                    groundedness_check_ms=0.0,
                    total_rag_ms=total_rag_ms,
                    total_pipeline_ms=total_pipe_ms
                ),
                guardrails=pre_guard,
                mode="Guardrail-Enforced",
                retrieval_explanation="Query blocked before vector retrieval."
            )

        # 3. Vector Embedding Generation
        t0 = time.perf_counter()
        query_vector = embedding_engine.embed_query(cleaned_query)
        embedding_ms = round((time.perf_counter() - t0) * 1000, 2)

        # 4. FAISS Vector Retrieval (collection-aware)
        t0 = time.perf_counter()
        vector_retriever = retriever_registry.get_retriever(collection)
        sources = vector_retriever.search(query_vector, top_k=top_k, threshold=threshold)
        retrieval_explanation = vector_retriever.explain_retrieval(cleaned_query, sources)
        retrieval_ms = round((time.perf_counter() - t0) * 1000, 2)

        # 5. Post-retrieval Evidence & Confidence Guardrail
        t_evidence_start = time.perf_counter()
        has_evidence, evidence_reason, top_confidence = guardrail_engine.check_evidence(sources, threshold=settings.CONFIDENCE_ABSTAIN_THRESHOLD)
        guardrail_ms += round((time.perf_counter() - t_evidence_start) * 1000, 2)

        if not has_evidence:
            total_rag_ms = round((time.perf_counter() - t_pipeline_start) * 1000, 2)
            voice_ms = req.voice_latency_ms
            total_pipe_ms = round(total_rag_ms + (voice_ms or 0.0), 2)

            return AskResponse(
                query=cleaned_query,
                answer="I couldn't find enough evidence in the knowledge base to answer this question reliably.",
                grounded=False,
                abstained=True,
                confidence=round(top_confidence, 4),
                sources=sources,
                latency=LatencyBreakdown(
                    voice_stt_ms=voice_ms,
                    preprocessing_ms=preprocessing_ms,
                    guardrail_ms=guardrail_ms,
                    embedding_ms=embedding_ms,
                    retrieval_ms=retrieval_ms,
                    prompt_construction_ms=0.0,
                    generation_ms=0.0,
                    groundedness_check_ms=0.0,
                    total_rag_ms=total_rag_ms,
                    total_pipeline_ms=total_pipe_ms
                ),
                guardrails=GuardrailInfo(
                    passed=True,
                    flagged_type="INSUFFICIENT_EVIDENCE",
                    reason=evidence_reason,
                    abstained=True
                ),
                mode="Abstained",
                retrieval_explanation=f"Abstained: {evidence_reason}"
            )

        # 6. Prompt Construction
        t0 = time.perf_counter()
        prompt_construction_ms = round((time.perf_counter() - t0) * 1000, 2)

        # 7. Grounded LLM Generation
        t0 = time.perf_counter()
        answer_text, active_mode = await llm_generator.generate_answer(cleaned_query, sources)
        generation_ms = round((time.perf_counter() - t0) * 1000, 2)

        # 8. Post-Generation Groundedness & Abstention Verification
        t0 = time.perf_counter()
        is_grounded_check, groundedness_score, ground_reason = guardrail_engine.check_groundedness(answer_text, sources)
        groundedness_check_ms = round((time.perf_counter() - t0) * 1000, 2)

        # Detect if LLM generated an explicit abstention response
        abstain_phrases = [
            "no information", "not mentioned", "not provide", "does not contain",
            "cannot find", "couldn't find", "not possible to determine",
            "not in the provided", "no mention"
        ]
        is_llm_abstaining = any(p in answer_text.lower() for p in abstain_phrases)

        # Determine overall grounded/abstained state
        if is_llm_abstaining or (not is_grounded_check and groundedness_score < 0.20):
            is_abstained = True
            is_grounded = False
            flagged = "INSUFFICIENT_EVIDENCE" if is_llm_abstaining else "LOW_GROUNDEDNESS"
            guard_reason = "Answer indicates insufficient evidence in retrieved context." if is_llm_abstaining else ground_reason
        else:
            is_abstained = False
            is_grounded = True
            flagged = None
            guard_reason = None

        # Total Latency Calculations
        total_rag_ms = round((time.perf_counter() - t_pipeline_start) * 1000, 2)
        voice_ms = req.voice_latency_ms
        total_pipe_ms = round(total_rag_ms + (voice_ms or 0.0), 2)

        return AskResponse(
            query=cleaned_query,
            answer=answer_text,
            grounded=is_grounded,
            abstained=is_abstained,
            confidence=round(top_confidence, 4),
            groundedness_score=groundedness_score,
            sources=sources,
            latency=LatencyBreakdown(
                voice_stt_ms=voice_ms,
                preprocessing_ms=preprocessing_ms,
                guardrail_ms=guardrail_ms,
                embedding_ms=embedding_ms,
                retrieval_ms=retrieval_ms,
                prompt_construction_ms=prompt_construction_ms,
                generation_ms=generation_ms,
                groundedness_check_ms=groundedness_check_ms,
                total_rag_ms=total_rag_ms,
                total_pipeline_ms=total_pipe_ms
            ),
            guardrails=GuardrailInfo(passed=True, flagged_type=flagged, reason=guard_reason, abstained=is_abstained),
            mode=active_mode,
            retrieval_explanation=retrieval_explanation
        )

rag_pipeline = RAGPipeline()
