import re
import asyncio
import logging
from typing import List, Tuple
import httpx
from backend.config import settings
from backend.models.schemas import SourceItem

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are VocaRAG, a precise, grounded, low-latency multilingual answering engine.
Your ONLY job is to answer the user's question using ONLY the provided context passages.
Rules:
1. Use ONLY information from the context passages below.
2. Cite sources using [Source N] notation matching the passage numbers.
3. Keep answers strictly concise and direct (2 to 3 sentences maximum, strictly under 80 words). Never generate conversational filler, preamble, or repetition.
4. If the context does not contain enough information to answer the question, state clearly: "I cannot find enough information in the provided context to answer this question."
5. Never invent or hallucinate information beyond what the passages explicitly state."""


class LLMGenerator:
    def __init__(self):
        self.gemini_key = settings.GEMINI_API_KEY
        self.openai_key = settings.OPENAI_API_KEY
        self.groq_key = settings.GROQ_API_KEY
        self.provider = settings.LLM_PROVIDER

    def construct_prompt(self, query: str, sources: List[SourceItem]) -> str:
        context_parts = []
        for idx, src in enumerate(sources):
            context_parts.append(
                f"--- [Source {idx + 1}:{src.doc_name}] ---\n{src.content}"
            )
        context_str = "\n\n".join(context_parts)
        return f"CONTEXT PASSAGES:\n{context_str}\n\nUSER QUESTION: {query}\n\nGROUNDED ANSWER:"

    def get_active_mode(self) -> Tuple[str, str]:
        if self.groq_key:
            return "Live", f"Groq ({settings.GROQ_MODEL})"
        if self.gemini_key:
            return "Live", f"Gemini ({settings.GEMINI_MODEL})"
        if self.openai_key:
            return "Live", f"OpenAI ({settings.OPENAI_MODEL})"
        return "Demo", "Local Deterministic Extractor"

    async def _call_groq(self, prompt: str, max_retries: int = 2) -> str:
        """Calls Groq LPU endpoint with exponential backoff."""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.GROQ_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 200
        }

        delay = 1.0
        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt in range(max_retries + 1):
                try:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        choices = data.get("choices", [])
                        if choices and "message" in choices[0]:
                            return choices[0]["message"].get("content", "").strip()
                    elif resp.status_code in [429, 500, 503] and attempt < max_retries:
                        logger.warning(f"Groq API error {resp.status_code}. Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue
                    else:
                        logger.error(f"Groq API error {resp.status_code}: {resp.text[:200]}")
                        break
                except Exception as e:
                    logger.error(f"Groq request exception: {e}")
                    if attempt < max_retries:
                        await asyncio.sleep(delay)
                        delay *= 2
                    else:
                        break
        return self._local_grounded_synthesis(prompt)

    async def _call_gemini(self, prompt: str, max_retries: int = 2) -> str:
        """Calls Gemini REST API with exponential backoff."""
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.GEMINI_MODEL}:generateContent?key={self.gemini_key}"
        )
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{SYSTEM_PROMPT}\n\n{prompt}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 200,
                "topP": 0.95
            }
        }

        delay = 1.0
        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt in range(max_retries + 1):
                try:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            parts = candidates[0]["content"].get("parts", [])
                            if parts and "text" in parts[0]:
                                return parts[0]["text"].strip()
                    elif resp.status_code in [429, 500, 503] and attempt < max_retries:
                        logger.warning(f"Gemini API rate/server error {resp.status_code}. Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue
                    else:
                        logger.error(f"Gemini API returned error: {resp.status_code} - {resp.text}")
                        break
                except Exception as e:
                    logger.error(f"Exception calling Gemini: {e}")
                    if attempt < max_retries:
                        await asyncio.sleep(delay)
                        delay *= 2
                    else:
                        break

        return self._local_grounded_synthesis(prompt)

    async def _call_openai(self, prompt: str, max_retries: int = 2) -> str:
        """Calls OpenAI-compatible endpoint with exponential backoff."""
        url = f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 200
        }

        delay = 1.0
        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt in range(max_retries + 1):
                try:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        choices = data.get("choices", [])
                        if choices and "message" in choices[0]:
                            return choices[0]["message"].get("content", "").strip()
                    elif resp.status_code in [429, 500, 503] and attempt < max_retries:
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue
                    else:
                        logger.error(f"OpenAI API error {resp.status_code}: {resp.text}")
                        break
                except Exception as e:
                    logger.error(f"OpenAI request exception: {e}")
                    if attempt < max_retries:
                        await asyncio.sleep(delay)
                        delay *= 2
                    else:
                        break

        return self._local_grounded_synthesis(prompt)

    def _local_grounded_synthesis(self, prompt: str) -> str:
        """
        High-precision deterministic grounded synthesis for Demo Mode.
        Extracts clean, informative factual sentences directly from matching context passages.
        If token coverage is insufficient, cleanly abstains without hallucinating.
        """
        context_match = re.search(r"CONTEXT PASSAGES:\s*(.*?)\s*USER QUESTION:\s*(.*?)\s*GROUNDED ANSWER", prompt, re.DOTALL)
        if not context_match:
            return "I cannot find enough information in the provided context to answer this question."

        context_str = context_match.group(1)
        query_str = context_match.group(2).strip().lower()

        stop_words = {"what", "is", "the", "how", "many", "to", "a", "an", "for", "of", "in", "and", "or", "can", "do", "should", "i", "my", "tell", "me", "about", "who", "why", "does", "it", "called"}
        query_tokens = [w for w in re.findall(r'\b[a-z0-9\u0900-\u0DFF\u0C00-\u0C7F]+\b', query_str) if w not in stop_words and len(w) > 2]
        
        if not query_tokens:
            query_tokens = [w for w in re.findall(r'\b\w+\b', query_str) if len(w) > 2]

        sources_raw = re.split(r'---\s*\[Source\s*(\d+):([^\]]+)\]\s*---', context_str)
        extracted_facts = []
        
        for i in range(1, len(sources_raw), 3):
            src_num = sources_raw[i]
            src_body = sources_raw[i+2].strip() if i+2 < len(sources_raw) else ""

            cleaned_lines = []
            for line in src_body.splitlines():
                l = line.strip()
                if not l or set(l).issubset({'=', '-', '*', '#', '_', '~', ' '}):
                    continue
                if l.startswith("VOCARAG GENERAL KNOWLEDGE") or l.startswith("VocaPulse Technologies") or "Policy (" in l or "Handbook (" in l:
                    continue
                l_clean = re.sub(r'\[.*?\]', '', l).strip()
                l_clean = re.sub(r'^\(.*?\)\s*', '', l_clean).strip()
                if l_clean:
                    cleaned_lines.append(l_clean)

            clean_text = " ".join(cleaned_lines)
            sentences = re.split(r'(?<=[.!?])\s+', clean_text)
            
            for s in sentences:
                s_clean = s.strip()
                s_clean = re.sub(r'^[-\*\u2022\d\.\s]+', '', s_clean).strip()
                if len(s_clean) < 25 or not re.search(r'[A-Za-z\u0900-\u0DFF\u0C00-\u0C7F]', s_clean):
                    continue
                
                s_lower = s_clean.lower()
                matching_tokens = [token for token in query_tokens if token in s_lower]
                distinct_matches = len(set(matching_tokens))
                coverage = distinct_matches / len(query_tokens) if query_tokens else 0.0
                
                # Check for sufficient keyword coverage
                if query_tokens:
                    if len(query_tokens) == 1 and distinct_matches < 1:
                        continue
                    elif len(query_tokens) == 2 and distinct_matches < 1:
                        continue
                    elif len(query_tokens) >= 3 and (distinct_matches < 2 or coverage < 0.40):
                        continue

                score = len(matching_tokens) + (distinct_matches * 3)
                if any(c.isdigit() or c in "$%#" for c in s_clean):
                    score += 1
                extracted_facts.append((score, coverage, f"{s_clean} [Source {src_num}]"))

        # Sort facts by score descending
        extracted_facts.sort(key=lambda x: (x[0], x[1]), reverse=True)

        if not extracted_facts:
            return "I cannot find enough information in the provided context to answer this question."

        # Pick top 2 most relevant sentences
        selected = [f[2] for f in extracted_facts[:2]]
        unique_selected = []
        for item in selected:
            if item not in unique_selected:
                unique_selected.append(item)

        return " ".join(unique_selected)

    async def generate_answer(self, query: str, sources: List[SourceItem]) -> Tuple[str, str]:
        prompt = self.construct_prompt(query, sources)
        mode, provider_info = self.get_active_mode()

        if mode == "Live":
            if self.groq_key:
                answer = await self._call_groq(prompt)
                return answer, "Live (Groq)"
            elif self.gemini_key:
                answer = await self._call_gemini(prompt)
                return answer, "Live (Gemini)"
            elif self.openai_key:
                answer = await self._call_openai(prompt)
                return answer, "Live (OpenAI)"

        answer = self._local_grounded_synthesis(prompt)
        return answer, "Demo"

llm_generator = LLMGenerator()
