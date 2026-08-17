import re
import time
import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
import httpx
from backend.config import settings

logger = logging.getLogger(__name__)

# Supported Sarvam Bulbul voices and languages
SARVAM_TTS_LANGUAGES = {
    "hi-IN": "Hindi",
    "te-IN": "Telugu",
    "bn-IN": "Bengali",
    "en-IN": "English (Indian)",
    "ta-IN": "Tamil",
    "kn-IN": "Kannada",
    "ml-IN": "Malayalam",
    "mr-IN": "Marathi",
    "gu-IN": "Gujarati",
    "pa-IN": "Punjabi",
    "od-IN": "Odia"
}

SARVAM_TTS_SPEAKERS = ["meera", "pavithra", "arvind", "amartya"]


def _clean_text_for_speech(text: str) -> str:
    """Removes citations like [Source 1], URLs, markdown formatting, and brackets."""
    # Remove citations
    cleaned = re.sub(r'\[Source\s*\d+.*?\]', '', text)
    cleaned = re.sub(r'\[Note:.*?\]', '', cleaned)
    # Remove markdown headers and bullets
    cleaned = re.sub(r'^[#\*\-]+\s*', '', cleaned, flags=re.MULTILINE)
    # Remove markdown bold/italic
    cleaned = re.sub(r'[\*_]{1,3}', '', cleaned)
    # Normalize whitespaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


@dataclass
class SarvamTTSResponse:
    audio_base64: Optional[str]
    content_type: str
    language_code: str
    speaker: str
    latency_ms: float
    error: Optional[str] = None


class SarvamTTS:
    """
    Text-to-Speech client using Sarvam AI Bulbul models (bulbul:v2 / bulbul:v1).
    Synthesizes spoken grounded answers in Indic languages and English.
    """

    def __init__(self):
        self.api_key = settings.SARVAM_API_KEY
        self.api_url = "https://api.sarvam.ai/text-to-speech"
        self.default_model = "bulbul:v2"
        self.default_speaker = "meera"
        self.default_language = settings.SARVAM_DEFAULT_LANGUAGE

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def synthesize(
        self,
        text: str,
        language_code: Optional[str] = None,
        speaker: Optional[str] = None,
        max_retries: int = 2
    ) -> SarvamTTSResponse:
        """Synthesizes input text to spoken audio via Sarvam Bulbul API."""
        cleaned_text = _clean_text_for_speech(text)
        lang = language_code or self.default_language
        spk = speaker or self.default_speaker

        if not cleaned_text:
            return SarvamTTSResponse(
                audio_base64=None,
                content_type="audio/wav",
                language_code=lang,
                speaker=spk,
                latency_ms=0.0,
                error="Text is empty after stripping formatting."
            )

        if not self.is_configured:
            return SarvamTTSResponse(
                audio_base64=None,
                content_type="audio/wav",
                language_code=lang,
                speaker=spk,
                latency_ms=0.0,
                error="Sarvam API key not configured. Set SARVAM_API_KEY in .env."
            )

        # Cap text length to 500 characters for snappy voice response
        if len(cleaned_text) > 500:
            cleaned_text = cleaned_text[:500].rsplit(' ', 1)[0] + "."

        t_start = time.perf_counter()
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": [cleaned_text],
            "target_language_code": lang,
            "speaker": spk,
            "pitch": 0,
            "pace": 1.0,
            "loudness": 1.5,
            "speech_sample_rate": 22050,
            "enable_preprocessing": True,
            "model": self.default_model
        }

        delay = 1.0
        async with httpx.AsyncClient(timeout=20.0) as client:
            for attempt in range(max_retries + 1):
                try:
                    resp = await client.post(self.api_url, headers=headers, json=payload)
                    latency_ms = round((time.perf_counter() - t_start) * 1000, 2)

                    if resp.status_code == 200:
                        data = resp.json()
                        audios = data.get("audios", [])
                        if audios and isinstance(audios, list):
                            return SarvamTTSResponse(
                                audio_base64=audios[0],
                                content_type="audio/wav",
                                language_code=lang,
                                speaker=spk,
                                latency_ms=latency_ms
                            )
                        elif "audio" in data:
                            return SarvamTTSResponse(
                                audio_base64=data["audio"],
                                content_type="audio/wav",
                                language_code=lang,
                                speaker=spk,
                                latency_ms=latency_ms
                            )
                    elif resp.status_code in [429, 500, 503] and attempt < max_retries:
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue
                    else:
                        logger.warning(f"Sarvam TTS returned {resp.status_code}: {resp.text[:200]}")
                        break
                except Exception as e:
                    logger.error(f"Sarvam TTS exception: {e}")
                    if attempt < max_retries:
                        await asyncio.sleep(delay)
                        delay *= 2
                    else:
                        break

        latency_ms = round((time.perf_counter() - t_start) * 1000, 2)
        return SarvamTTSResponse(
            audio_base64=None,
            content_type="audio/wav",
            language_code=lang,
            speaker=spk,
            latency_ms=latency_ms,
            error="Sarvam TTS synthesis failed."
        )


sarvam_tts = SarvamTTS()
