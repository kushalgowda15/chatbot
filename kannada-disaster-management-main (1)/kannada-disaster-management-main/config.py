"""
config.py — Centralized Configuration & Environment Validation
Kannada Disaster Management AI System
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# Load .env
# ─────────────────────────────────────────────
# Try project-root .env first, then parent dir
_env_paths = [
    Path(__file__).parent / ".env",
    Path(__file__).parent.parent / ".env",
]
for _ep in _env_paths:
    if _ep.exists():
        load_dotenv(dotenv_path=_ep)
        break

# ─────────────────────────────────────────────
# Logging Setup
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("config")


# ─────────────────────────────────────────────
# API Keys
# ─────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")

# ─────────────────────────────────────────────
# Flask Settings
# ─────────────────────────────────────────────
FLASK_HOST: str = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5001"))
FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "false").lower() == "true"
SECRET_KEY: str = os.getenv("SECRET_KEY", "kannada-disaster-ai-secret-2026")

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
VECTORSTORE_DIR = BASE_DIR / "vectorstore"
DATASET_DIR = BASE_DIR / "dataset"
STATIC_DIR = BASE_DIR / "static"
AUDIO_DIR = STATIC_DIR / "audio"            # UUID-named audio files go here

FAISS_INDEX_PATH = str(VECTORSTORE_DIR / "disaster_index.faiss")
METADATA_PATH = str(VECTORSTORE_DIR / "disaster_metadata.json")

# ─────────────────────────────────────────────
# Model Settings
# ─────────────────────────────────────────────
EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "small")
TTS_VOICE: str = "kn-IN-SapnaNeural"

# ─────────────────────────────────────────────
# RAG Pipeline
# ─────────────────────────────────────────────
RAG_TOP_K: int = 5                          # retrieve top-K chunks
RAG_BM25_WEIGHT: float = 0.35              # BM25 score fusion weight
RAG_FAISS_WEIGHT: float = 0.65             # FAISS score fusion weight
RAG_SIMILARITY_THRESHOLD: float = 0.30     # reject chunks below this cosine sim
CONTEXT_MAX_TOKENS: int = 1500             # max chars of retrieved context

# ─────────────────────────────────────────────
# Conversation Memory
# ─────────────────────────────────────────────
MEMORY_MAX_TURNS: int = 5                  # keep last N turns per session
SESSION_TIMEOUT_MINS: int = 30

# ─────────────────────────────────────────────
# Rate Limiting
# ─────────────────────────────────────────────
RATE_LIMIT_CHAT: str = "60 per minute"
RATE_LIMIT_VOICE: str = "20 per minute"
RATE_LIMIT_ALERTS: str = "30 per minute"

# ─────────────────────────────────────────────
# Alerts Caching
# ─────────────────────────────────────────────
ALERTS_CACHE_TTL_SECONDS: int = 300        # 5-minute cache
WEATHER_DISTRICTS = [
    "Bengaluru", "Mysuru", "Hubballi", "Dharwad", "Belagavi",
    "Mangaluru", "Ballari", "Vijayapura", "Kalaburagi", "Shivamogga",
    "Tumakuru", "Raichur", "Bidar", "Hassan", "Chitradurga",
    "Davanagere", "Udupi", "Chikkamagaluru", "Kodagu", "Mandya",
]

# ─────────────────────────────────────────────
# Severity Thresholds
# ─────────────────────────────────────────────
class Severity:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    COLORS = {
        LOW: "#22c55e",
        MEDIUM: "#f59e0b",
        HIGH: "#f97316",
        CRITICAL: "#f43f5e",
    }

    # Severities that auto-trigger emergency UI mode
    EMERGENCY_TRIGGER = {HIGH, CRITICAL}


# ─────────────────────────────────────────────
# Validate Critical Env Vars
# ─────────────────────────────────────────────
def validate_env() -> None:
    """Warn on startup if critical keys are missing."""
    if not GROQ_API_KEY:
        logger.warning(
            "GROQ_API_KEY not set — LLM calls will fail. "
            "Offline mode will be used as fallback."
        )
    else:
        logger.info("GROQ_API_KEY loaded ✓")

    if not OPENWEATHER_API_KEY:
        logger.warning(
            "OPENWEATHER_API_KEY not set — live weather alerts will use IMD RSS fallback."
        )

    # Ensure required directories exist
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

    if not Path(FAISS_INDEX_PATH).exists():
        logger.warning(
            f"FAISS index not found at {FAISS_INDEX_PATH}. "
            "Run: python scripts/embeddings.py"
        )
