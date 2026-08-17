import logging
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from backend.rag.tts import sarvam_tts, SARVAM_TTS_LANGUAGES, SARVAM_TTS_SPEAKERS

router = APIRouter(prefix="/api/tts", tags=["Text-to-Speech"])
logger = logging.getLogger(__name__)

class TTSRequest(BaseModel):
    text: str
    language_code: Optional[str] = "hi-IN"
    speaker: Optional[str] = "meera"

class TTSResponse(BaseModel):
    audio_base64: Optional[str] = None
    content_type: str = "audio/wav"
    language_code: str
    speaker: str
    latency_ms: float
    error: Optional[str] = None

@router.post("/synthesize", response_model=TTSResponse)
async def synthesize_speech(req: TTSRequest):
    """
    Synthesizes grounded text answers to natural spoken voice using Sarvam AI Bulbul TTS.
    Supports Hindi, Telugu, Bengali, Tamil, Kannada, Marathi, and Indian English.
    """
    try:
        res = await sarvam_tts.synthesize(
            text=req.text,
            language_code=req.language_code,
            speaker=req.speaker
        )
        return TTSResponse(
            audio_base64=res.audio_base64,
            content_type=res.content_type,
            language_code=res.language_code,
            speaker=res.speaker,
            latency_ms=res.latency_ms,
            error=res.error
        )
    except Exception as e:
        logger.error(f"TTS synthesis endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")

@router.get("/status")
async def get_tts_status():
    return {
        "provider": "sarvam",
        "model": "bulbul:v2",
        "configured": sarvam_tts.is_configured,
        "supported_languages": SARVAM_TTS_LANGUAGES,
        "speakers": SARVAM_TTS_SPEAKERS
    }
