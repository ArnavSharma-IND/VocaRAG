import time
import logging
from typing import Optional
from backend.config import settings
from backend.models.schemas import QueryRequest, AskResponse, LatencyBreakdown, GuardrailInfo
from backend.rag.guardrails import guardrail_engine
from backend.rag.embeddings import embedding_engine
from backend.rag.retriever import vector_retriever
from backend.rag.generator import llm_generator

logger = logging.getLogger(__name__)

class RAGPipeline:
    async def process_query(self, req: QueryRequest) -> AskResponse:
        """
        Executes the full Voice-to-Answer RAG Pipeline with real microsecond latency tracking.
        """
        t_pipeline_start = time.perf_counter()
        
        # 1. Query Preprocessing & Normalization
        t0 = time.perf_counter()
        cleaned_query = req.query.strip()
        top_k = req.top_k or settings.DEFAULT_TOP_K
        threshold = req.threshold if req.threshold is not None else settings.DEFAULT_SIMILARITY_THRESHOLD
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

        # 4. FAISS Vector Retrieval & Similarity Search
        t0 = time.perf_counter()
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

        # Total Latency Calculations
        total_rag_ms = round((time.perf_counter() - t_pipeline_start) * 1000, 2)
        voice_ms = req.voice_latency_ms
        total_pipe_ms = round(total_rag_ms + (voice_ms or 0.0), 2)

        return AskResponse(
            query=cleaned_query,
            answer=answer_text,
            grounded=True,
            abstained=False,
            confidence=round(top_confidence, 4),
            sources=sources,
            latency=LatencyBreakdown(
                voice_stt_ms=voice_ms,
                preprocessing_ms=preprocessing_ms,
                guardrail_ms=guardrail_ms,
                embedding_ms=embedding_ms,
                retrieval_ms=retrieval_ms,
                prompt_construction_ms=prompt_construction_ms,
                generation_ms=generation_ms,
                total_rag_ms=total_rag_ms,
                total_pipeline_ms=total_pipe_ms
            ),
            guardrails=GuardrailInfo(passed=True, flagged_type=None, reason=None, abstained=False),
            mode=active_mode,
            retrieval_explanation=retrieval_explanation
        )

rag_pipeline = RAGPipeline()
