"""
services/voice_service.py
Improved STT / TTS Pipeline — Whisper + Edge TTS
Kannada Disaster Management AI System
"""

import asyncio
import logging
import os
import uuid
from pathlib import Path
from typing import Optional, Tuple

import edge_tts
from faster_whisper import WhisperModel

from config import WHISPER_MODEL_SIZE, TTS_VOICE, AUDIO_DIR

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Whisper Model (loaded once)
# ─────────────────────────────────────────────────────────────────────────────

logger.info(f"Loading Whisper model ({WHISPER_MODEL_SIZE})...")
try:
    _whisper = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    logger.info("Whisper model loaded ✓")
    _whisper_available = True
except Exception as e:
    logger.error(f"Whisper load failed: {e}")
    _whisper = None
    _whisper_available = False

# Minimum confidence threshold for Whisper segments
MIN_SEGMENT_CONFIDENCE = -1.0   # Whisper log-prob (higher is better; -1.0 is lenient)
MIN_TRANSCRIPT_CHARS = 3


# ─────────────────────────────────────────────────────────────────────────────
# Audio Format Conversion (webm → wav via pydub)
# ─────────────────────────────────────────────────────────────────────────────

def _convert_to_wav(input_path: str, output_path: str) -> bool:
    """Convert any audio format to 16kHz mono WAV for Whisper."""
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(input_path)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(output_path, format="wav")
        return True
    except Exception as e:
        logger.warning(f"Audio conversion failed: {e} — using original file")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# STT: Speech → Text
# ─────────────────────────────────────────────────────────────────────────────

def speech_to_text(audio_file: str) -> Tuple[str, float]:
    """
    Transcribe audio to Kannada text using Whisper.

    Args:
        audio_file: Path to uploaded audio file

    Returns:
        (transcript_text, confidence_score 0-1)
    """
    if not _whisper_available:
        logger.error("Whisper model unavailable")
        return "", 0.0

    # Try converting to WAV for better compatibility
    wav_path = str(AUDIO_DIR / f"tmp_{uuid.uuid4().hex}.wav")
    converted = _convert_to_wav(audio_file, wav_path)
    process_path = wav_path if converted else audio_file

    try:
        segments, info = _whisper.transcribe(
            process_path,
            language="kn",
            task="transcribe",
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 300},
        )

        # Filter segments by confidence threshold
        valid_segments = []
        confidence_sum = 0.0
        seg_count = 0

        for seg in segments:
            avg_logprob = getattr(seg, "avg_logprob", -0.5)
            if avg_logprob >= MIN_SEGMENT_CONFIDENCE:
                valid_segments.append(seg.text)
                confidence_sum += avg_logprob
                seg_count += 1
            else:
                logger.debug(f"Low-confidence segment skipped: logprob={avg_logprob:.2f}")

        transcript = " ".join(valid_segments).strip()

        # Confidence: normalize avg log-prob to 0-1 range roughly
        avg_conf = (confidence_sum / seg_count) if seg_count > 0 else -1.0
        confidence = max(0.0, min(1.0, (avg_conf + 1.0)))  # rough normalization

        if len(transcript) < MIN_TRANSCRIPT_CHARS:
            logger.warning(f"Transcript too short: '{transcript}'")
            return "", 0.0

        logger.info(f"STT result: '{transcript[:80]}...' (conf={confidence:.2f})")
        return transcript, round(confidence, 2)

    except Exception as e:
        logger.error(f"Whisper transcription error: {e}")
        return "", 0.0
    finally:
        # Clean up temp WAV file
        if converted and os.path.exists(wav_path):
            try:
                os.remove(wav_path)
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────────────────
# TTS: Text → Speech (UUID filename, non-blocking)
# ─────────────────────────────────────────────────────────────────────────────

async def _synthesize_async(text: str, output_path: str) -> None:
    """Async TTS using Edge TTS."""
    communicate = edge_tts.Communicate(text, voice=TTS_VOICE)
    await communicate.save(output_path)


def synthesize_speech(text: str) -> Optional[str]:
    """
    Generate TTS audio for given Kannada text.

    Returns:
        URL path to audio file (e.g. "/static/audio/abc123.mp3")
        or None on failure.
    """
    if not text or not text.strip():
        return None

    filename = f"{uuid.uuid4().hex}.mp3"
    output_path = str(AUDIO_DIR / filename)

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_synthesize_async(text, output_path))
        loop.close()

        audio_url = f"/static/audio/{filename}"
        logger.info(f"TTS generated: {audio_url}")
        return audio_url

    except Exception as e:
        logger.error(f"TTS synthesis error: {e}")
        return None
