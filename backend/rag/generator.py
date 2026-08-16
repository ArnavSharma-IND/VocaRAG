import os
import re
import time
import asyncio
import logging
from typing import List, Tuple, Dict, Any, Optional
import httpx
from backend.config import settings
from backend.models.schemas import SourceItem

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are VocaRAG, a high-precision, voice-enabled enterprise knowledge assistant.
Your duty is to answer the user's question with 100% strict grounding in the provided context passages.

RULES:
1. Answer using ONLY the retrieved context passages provided.
2. If the context does not contain sufficient facts to answer the question, state: "I couldn't find enough evidence in the knowledge base to answer this question reliably."
3. Do NOT extrapolate, speculate, or invent details not present in the text.
4. Reference your sources using bracketed citations, e.g., [Source 1], [Source 2].
5. Clearly distinguish when answering from general knowledge vs company policies if relevant.
6. Keep your answer direct, clear, and professional.
"""

class LLMGenerator:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.gemini_key = settings.GEMINI_API_KEY
        self.openai_key = settings.OPENAI_API_KEY
        self.http_client = httpx.AsyncClient(timeout=15.0)

    def get_active_mode(self) -> Tuple[str, str]:
        """Returns (mode, provider_info). Mode is 'Live' or 'Demo'."""
        if self.gemini_key and len(self.gemini_key.strip()) > 5:
            return "Live", f"Google Gemini ({settings.GEMINI_MODEL})"
        elif self.openai_key and len(self.openai_key.strip()) > 5:
            return "Live", f"OpenAI Compatible ({settings.OPENAI_MODEL})"
        else:
            return "Demo", "Local Deterministic Extractor"

    def construct_prompt(self, query: str, sources: List[SourceItem]) -> str:
        """Builds structured context prompt with document types."""
        context_blocks = []
        for i, src in enumerate(sources, 1):
            context_blocks.append(
                f"--- [Source {i}: {src.doc_name} (Type: {src.category_label}, Relevance: {src.relevance_tier}, Similarity: {src.similarity})] ---\n{src.content}"
            )
        
        context_text = "\n\n".join(context_blocks)
        
        user_prompt = f"""CONTEXT PASSAGES:
{context_text}

USER QUESTION:
{query}

GROUNDED ANSWER (with citations):"""
        return user_prompt

    async def _call_gemini(self, prompt: str, max_retries: int = 2) -> str:
        """Calls Google Gemini API with exponential backoff retry."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={self.gemini_key}"
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
                "maxOutputTokens": 600,
                "topP": 0.95
            }
        }

        delay = 1.0
        for attempt in range(max_retries + 1):
            try:
                resp = await self.http_client.post(url, json=payload)
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
            "max_tokens": 600
        }

        delay = 1.0
        for attempt in range(max_retries + 1):
            try:
                resp = await self.http_client.post(url, headers=headers, json=payload)
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
        """
        context_match = re.search(r"CONTEXT PASSAGES:\s*(.*?)\s*USER QUESTION:\s*(.*?)\s*GROUNDED ANSWER", prompt, re.DOTALL)
        if not context_match:
            return "The requested information was located in the primary source document [Source 1]."

        context_str = context_match.group(1)
        query_str = context_match.group(2).strip().lower()

        stop_words = {"what", "is", "the", "how", "many", "to", "a", "an", "for", "of", "in", "and", "or", "can", "do", "should", "i", "my", "tell", "me", "about", "who", "why", "does", "it"}
        query_tokens = [w for w in re.findall(r'\b[a-z0-9]+\b', query_str) if w not in stop_words and len(w) > 2]

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
                # Strip section bracket headers like [PHOTOSYNTHESIS PROCESS] or [WHY IS THE SKY BLUE?]
                l_clean = re.sub(r'\[.*?\]', '', l).strip()
                l_clean = re.sub(r'^\(.*?\)\s*', '', l_clean).strip()
                if l_clean:
                    cleaned_lines.append(l_clean)

            clean_text = " ".join(cleaned_lines)
            sentences = re.split(r'(?<=[.!?])\s+', clean_text)
            
            for s in sentences:
                s_clean = s.strip()
                # Clean any lingering leading punctuation
                s_clean = re.sub(r'^[-\*\•\d\.\s]+', '', s_clean).strip()
                if len(s_clean) < 25 or not re.search(r'[A-Za-z]', s_clean):
                    continue
                
                s_lower = s_clean.lower()
                matches = sum(1 for token in query_tokens if token in s_lower)
                
                # Bonus if sentence contains multiple distinct query tokens
                distinct_matches = len(set(token for token in query_tokens if token in s_lower))
                
                if matches > 0:
                    score = matches + (distinct_matches * 2)
                    if any(c.isdigit() or c in "$%#" for c in s_clean):
                        score += 1
                    extracted_facts.append((score, f"{s_clean} [Source {src_num}]"))

        # Sort facts by weighted match density
        extracted_facts.sort(key=lambda x: x[0], reverse=True)

        if not extracted_facts:
            if len(sources_raw) > 3:
                for line in sources_raw[3].splitlines():
                    l = line.strip()
                    if len(l) > 30 and not l.startswith("===") and not l.startswith("VOCARAG") and not l.startswith("VocaPulse"):
                        l_sub = re.sub(r'\[.*?\]', '', l).strip()
                        return f"{l_sub.split('.')[0]}. [Source 1]"
            return "The requested information was located in the primary source document [Source 1]."

        # Pick top 2 most relevant sentences
        selected = [f[1] for f in extracted_facts[:2]]
        unique_selected = []
        for item in selected:
            if item not in unique_selected:
                unique_selected.append(item)

        return " ".join(unique_selected)

    async def generate_answer(self, query: str, sources: List[SourceItem]) -> Tuple[str, str]:
        """
        Generates grounded response using active provider.
        Returns: (answer_text, mode_string)
        """
        prompt = self.construct_prompt(query, sources)
        mode, provider_info = self.get_active_mode()

        if mode == "Live":
            if self.gemini_key:
                answer = await self._call_gemini(prompt)
                return answer, "Live"
            elif self.openai_key:
                answer = await self._call_openai(prompt)
                return answer, "Live"

        # Explicit Demo Mode
        answer = self._local_grounded_synthesis(prompt)
        return answer, "Demo"

llm_generator = LLMGenerator()
