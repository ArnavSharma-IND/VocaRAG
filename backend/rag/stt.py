import time
import asyncio
import logging
from typing import Optional
from dataclasses import dataclass
import httpx
from backend.config import settings

logger = logging.getLogger(__name__)

@dataclass
class SarvamSTTResponse:
    transcript: str
    language_code: str
    mode: str
    latency_ms: float
    error: Optional[str] = None

class SarvamSTT:
    def __init__(self):
        self.api_key = settings.SARVAM_API_KEY
        self.model = settings.SARVAM_MODEL
        self.api_url = settings.SARVAM_API_URL
        self.default_language = settings.SARVAM_DEFAULT_LANGUAGE

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def transcribe(
        self,
        audio_bytes: bytes,
        language_code: Optional[str] = None,
        mode: str = "transcribe",  # transcribe | translate | codemix
        filename: str = "audio.wav",
        max_retries: int = 2
    ) -> SarvamSTTResponse:
        if not self.is_configured:
            return SarvamSTTResponse(
                transcript="",
                language_code=language_code or self.default_language,
                mode=mode,
                latency_ms=0.0,
                error="Sarvam API key not configured. Set SARVAM_API_KEY in .env."
            )

        lang = language_code or self.default_language
        t_start = time.perf_counter()

        files = {"file": (filename, audio_bytes)}
        data = {
            "model": self.model,
            "language_code": lang,
            "mode": mode,
        }
        headers = {
            "api-subscription-key": self.api_key,
        }

        delay = 1.0
        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt in range(max_retries + 1):
                try:
                    resp = await client.post(
                        self.api_url,
                        files=files,
                        data=data,
                        headers=headers,
                    )
                    latency_ms = round((time.perf_counter() - t_start) * 1000, 2)

                    if resp.status_code == 200:
                        result = resp.json()
                        transcript = result.get("transcript", "").strip()
                        detected_lang = result.get("language_code", lang)
                        return SarvamSTTResponse(
                            transcript=transcript,
                            language_code=detected_lang,
                            mode=mode,
                            latency_ms=latency_ms,
                        )
                    elif resp.status_code in [429, 500, 503] and attempt < max_retries:
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue
                    else:
                        error_text = resp.text[:200]
                        return SarvamSTTResponse(
                            transcript="",
                            language_code=lang,
                            mode=mode,
                            latency_ms=latency_ms,
                            error=f"Sarvam API error {resp.status_code}: {error_text}"
                        )
                except Exception as e:
                    if attempt < max_retries:
                        await asyncio.sleep(delay)
                        delay *= 2
                    else:
                        latency_ms = round((time.perf_counter() - t_start) * 1000, 2)
                        return SarvamSTTResponse(
                            transcript="",
                            language_code=lang,
                            mode=mode,
                            latency_ms=latency_ms,
                            error=f"Connection error: {str(e)}"
                        )

        latency_ms = round((time.perf_counter() - t_start) * 1000, 2)
        return SarvamSTTResponse(
            transcript="",
            language_code=lang,
            mode=mode,
            latency_ms=latency_ms,
            error="Max retries exceeded."
        )

sarvam_stt = SarvamSTT()
