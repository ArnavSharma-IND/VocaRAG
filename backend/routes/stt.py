import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.rag.stt import sarvam_stt

router = APIRouter(prefix="/api/stt", tags=["Speech-to-Text"])
logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {
    "hi-IN": "Hindi",
    "te-IN": "Telugu",
    "en-IN": "English (Indian)",
    "bn-IN": "Bengali",
    "ta-IN": "Tamil",
    "kn-IN": "Kannada",
    "ml-IN": "Malayalam",
    "mr-IN": "Marathi",
    "gu-IN": "Gujarati",
    "pa-IN": "Punjabi",
    "od-IN": "Odia"
}

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language_code: Optional[str] = Form("hi-IN"),
    mode: Optional[str] = Form("transcribe")  # transcribe | translate
):
    """
    Receives raw audio recorded in browser and transcribes / translates via Sarvam AI Saaras v3.
    """
    try:
        content_bytes = await file.read()
        if len(content_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty audio payload received.")

        result = await sarvam_stt.transcribe(
            audio_bytes=content_bytes,
            language_code=language_code,
            mode=mode,
            filename=file.filename or "audio.webm"
        )
        return {
            "transcript": result.transcript,
            "language": result.language_code,
            "mode": result.mode,
            "latency_ms": result.latency_ms,
            "error": result.error,
        }
    except Exception as e:
        logger.error(f"Error in STT transcribe endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"STT transcription failed: {str(e)}")

@router.get("/status")
async def get_stt_status():
    return {
        "provider": "sarvam",
        "model": sarvam_stt.model,
        "configured": sarvam_stt.is_configured,
        "supported_languages": SUPPORTED_LANGUAGES,
        "supported_modes": ["transcribe", "translate", "codemix"]
    }
