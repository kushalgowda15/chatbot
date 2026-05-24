"""
routes/chat_routes.py
Chat & Voice API Endpoints
Kannada Disaster Management AI System
"""

import os
import uuid
import logging
import time
from flask import Blueprint, request, jsonify

from services.chatbot_service import ask_chatbot
from services.voice_service import speech_to_text, synthesize_speech
from services import analytics_service

logger = logging.getLogger(__name__)

chat_bp = Blueprint("chat", __name__)

# ─────────────────────────────────────────────────────────────────────────────
# Helper — extract session ID from request
# ─────────────────────────────────────────────────────────────────────────────

def _get_session_id() -> str:
    """Extract or generate a session ID from request headers or JSON body."""
    # Try header first, then JSON body, then generate new one
    sid = (
        request.headers.get("X-Session-ID")
        or (request.json or {}).get("session_id")
        or request.form.get("session_id")
        or str(uuid.uuid4())
    )
    return sid.strip()


def _get_district() -> str:
    return (
        (request.json or {}).get("district", "")
        or request.form.get("district", "")
        or request.args.get("district", "")
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/chat — Text Chat
# ─────────────────────────────────────────────────────────────────────────────

@chat_bp.route("/api/chat", methods=["POST"])
def chat_api():
    """
    Process a text query and return AI response with severity classification.

    Request JSON:
        { "question": "...", "session_id": "...", "district": "..." }

    Response JSON:
        {
            "response": "...",
            "severity": "HIGH",
            "severity_color": "#f97316",
            "is_emergency": true,
            "audio_url": "/static/audio/abc.mp3",
            "citations": [...],
            "retrieval_confidence": 0.72,
            "is_offline": false,
            "mode": "emergency",
            "latency_ms": 1234
        }
    """
    try:
        data = request.get_json(silent=True) or {}
        question = data.get("question", "").strip()

        if not question:
            return jsonify({"error": "ಪ್ರಶ್ನೆ ಕಾಣೆಯಾಗಿದೆ (Question missing)"}), 400

        if len(question) > 2000:
            return jsonify({"error": "ಪ್ರಶ್ನೆ ತುಂಬಾ ಉದ್ದ (Question too long, max 2000 chars)"}), 400

        session_id = _get_session_id()
        district = _get_district()

        # Get chatbot response
        result = ask_chatbot(question, session_id=session_id)

        # Generate TTS audio
        audio_url = synthesize_speech(result["response"])

        # Record analytics
        analytics_service.record_query(
            query_type="text",
            severity=result["severity"],
            category=result["citations"][0].split("—")[0].strip() if result["citations"] else "General",
            latency_ms=result["latency_ms"],
            district=district,
            is_offline=result["is_offline"],
        )

        return jsonify({
            "response": result["response"],
            "severity": result["severity"],
            "severity_color": result["severity_color"],
            "is_emergency": result["is_emergency"],
            "audio_url": audio_url,
            "citations": result["citations"],
            "retrieval_confidence": result["retrieval_confidence"],
            "is_offline": result["is_offline"],
            "mode": "emergency" if result["is_emergency"] else "normal",
            "latency_ms": result["latency_ms"],
            "session_id": session_id,
        })

    except Exception as e:
        logger.exception(f"Chat API error: {e}")
        analytics_service.record_query(
            query_type="text", severity="LOW", category="Error",
            latency_ms=0, is_error=True, error_type="ChatError"
        )
        return jsonify({
            "error": "ಸರ್ವರ್ ದೋಷ ಸಂಭವಿಸಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
            "error_detail": str(e)
        }), 500


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/voice — Voice Chat
# ─────────────────────────────────────────────────────────────────────────────

@chat_bp.route("/api/voice", methods=["POST"])
def voice_api():
    """
    Process an uploaded audio file: STT → RAG → TTS.

    Request: multipart/form-data with 'file' field (audio/webm)
    Response JSON: same structure as /api/chat plus 'transcript' field
    """
    try:
        from config import AUDIO_DIR

        audio_file = request.files.get("file")
        if not audio_file:
            return jsonify({"error": "ಆಡಿಯೋ ಫೈಲ್ ಕಾಣೆಯಾಗಿದೆ (No audio file uploaded)"}), 400

        # Validate content type
        content_type = audio_file.content_type or ""
        allowed_types = {"audio/webm", "audio/wav", "audio/mp4", "audio/ogg", "audio/mpeg", ""}
        if content_type not in allowed_types and not content_type.startswith("audio/"):
            return jsonify({"error": f"Unsupported audio format: {content_type}"}), 415

        # Save with UUID filename (prevents collision)
        ext = "webm"
        if "wav" in content_type:
            ext = "wav"
        elif "mp4" in content_type or "m4a" in content_type:
            ext = "mp4"

        upload_filename = f"upload_{uuid.uuid4().hex}.{ext}"
        upload_path = str(AUDIO_DIR / upload_filename)
        audio_file.save(upload_path)

        session_id = _get_session_id()
        district = _get_district()

        try:
            # STT
            transcript, confidence = speech_to_text(upload_path)

            if not transcript:
                return jsonify({
                    "transcript": "",
                    "response": "ಕ್ಷಮಿಸಿ, ನಿಮ್ಮ ಧ್ವನಿ ಸ್ಪಷ್ಟವಾಗಿ ಕೇಳಿಸಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಮಾತನಾಡಿ.",
                    "severity": "LOW",
                    "is_emergency": False,
                    "mode": "normal",
                    "stt_confidence": confidence,
                })

            # RAG + LLM
            result = ask_chatbot(transcript, session_id=session_id)

            # TTS
            audio_url = synthesize_speech(result["response"])

            # Analytics
            analytics_service.record_query(
                query_type="voice",
                severity=result["severity"],
                category=result["citations"][0].split("—")[0].strip() if result["citations"] else "General",
                latency_ms=result["latency_ms"],
                district=district,
                is_offline=result["is_offline"],
            )

            return jsonify({
                "transcript": transcript,
                "stt_confidence": confidence,
                "response": result["response"],
                "severity": result["severity"],
                "severity_color": result["severity_color"],
                "is_emergency": result["is_emergency"],
                "audio_url": audio_url,
                "citations": result["citations"],
                "retrieval_confidence": result["retrieval_confidence"],
                "is_offline": result["is_offline"],
                "mode": "emergency" if result["is_emergency"] else "normal",
                "latency_ms": result["latency_ms"],
                "session_id": session_id,
            })

        finally:
            # Clean up uploaded temp file
            if os.path.exists(upload_path):
                try:
                    os.remove(upload_path)
                except Exception:
                    pass

    except Exception as e:
        logger.exception(f"Voice API error: {e}")
        analytics_service.record_query(
            query_type="voice", severity="LOW", category="Error",
            latency_ms=0, is_error=True, error_type="VoiceError"
        )
        return jsonify({
            "error": "ಧ್ವನಿ ಸಂಸ್ಕರಣೆಯಲ್ಲಿ ದೋಷ ಸಂಭವಿಸಿದೆ.",
            "error_detail": str(e)
        }), 500
