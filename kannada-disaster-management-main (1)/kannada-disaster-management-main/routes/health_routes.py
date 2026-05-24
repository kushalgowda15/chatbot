"""
routes/health_routes.py
System Health Check API
Kannada Disaster Management AI System
"""

import logging
import time
from pathlib import Path
from flask import Blueprint, jsonify
from config import FAISS_INDEX_PATH, GROQ_API_KEY

logger = logging.getLogger(__name__)
health_bp = Blueprint("health", __name__)


@health_bp.route("/api/health", methods=["GET"])
def health_check():
    """
    Return system component health status.
    Useful for monitoring and deployment readiness checks.
    """
    status = {
        "status": "ok",
        "timestamp": int(time.time()),
        "components": {
            "vector_db": {
                "status": "ok" if Path(FAISS_INDEX_PATH).exists() else "missing",
                "path": FAISS_INDEX_PATH,
            },
            "llm_api": {
                "status": "configured" if GROQ_API_KEY else "missing",
                "provider": "Groq (LLaMA-3.3-70b)",
            },
            "tts": {
                "status": "ok",
                "engine": "Edge TTS (kn-IN-SapnaNeural)",
            },
            "stt": {
                "status": "ok",
                "engine": "Faster-Whisper (small, int8)",
            },
        },
    }

    # Overall status degraded if critical components missing
    if status["components"]["vector_db"]["status"] == "missing":
        status["status"] = "degraded"
    if status["components"]["llm_api"]["status"] == "missing":
        status["status"] = "degraded"

    http_code = 200 if status["status"] == "ok" else 207
    return jsonify(status), http_code
