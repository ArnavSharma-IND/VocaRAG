import logging
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional
from backend.rag.stt import sarvam_stt

router = APIRouter(prefix="/api", tags=["Speech-to-Text"])
logger = logging.getLogger(__name__)


@router.post("/stt/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language_code: Optional[str] = Form(None),
    mode: str = Form("transcribe"),
):
    """
    Transcribes uploaded audio using Sarvam AI Saaras v3.
    Accepts WAV, WebM, OGG, MP3, FLAC audio files.
    """
    if not sarvam_stt.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Sarvam STT not configured. Set SARVAM_API_KEY in .env."
        )

    try:
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio file.")

        result = await sarvam_stt.transcribe(
            audio_bytes=audio_bytes,
            language_code=language_code,
            mode=mode,
            filename=file.filename or "audio.wav",
        )

        if result.error:
            logger.warning(f"STT returned error: {result.error}")

        return {
            "transcript": result.transcript,
            "language": result.language_code,
            "latency_ms": result.latency_ms,
            "error": result.error,
            "provider": "sarvam",
            "model": sarvam_stt.model,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"STT endpoint error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"code": "STT_ERROR", "message": str(e)}
        )


@router.get("/stt/status")
async def stt_status():
    """Returns Sarvam STT configuration status."""
    return {
        "configured": sarvam_stt.is_configured,
        "provider": "sarvam",
        "model": sarvam_stt.model,
        "default_language": sarvam_stt.default_language,
        "supported_languages": [
            {"code": "hi-IN", "name": "Hindi"},
            {"code": "te-IN", "name": "Telugu"},
            {"code": "en-IN", "name": "English"},
            {"code": "bn-IN", "name": "Bengali"},
            {"code": "ta-IN", "name": "Tamil"},
            {"code": "kn-IN", "name": "Kannada"},
            {"code": "ml-IN", "name": "Malayalam"},
            {"code": "mr-IN", "name": "Marathi"},
            {"code": "gu-IN", "name": "Gujarati"},
            {"code": "pa-IN", "name": "Punjabi"},
            {"code": "or-IN", "name": "Odia"},
            {"code": "ur-IN", "name": "Urdu"},
        ],
    }
