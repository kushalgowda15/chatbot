"""
services/severity_service.py
Emergency Severity Classification — Keyword + Groq LLM
Kannada Disaster Management AI System
"""

import re
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# KEYWORD TAXONOMY  (Kannada + English)
# Priority: CRITICAL > HIGH > MEDIUM > LOW
# ─────────────────────────────────────────────────────────────────────────────

CRITICAL_KEYWORDS = [
    # Kannada
    "ಸಿಕ್ಕಿಹಾಕಿಕೊಂಡಿದ್ದೇನೆ", "ಸಿಕ್ಕಿಹಾಕಿಕೊಂಡಿದ್ದಾರೆ", "ಮುಳುಗುತ್ತಿದ್ದೇನೆ",
    "ಮುಳುಗುತ್ತಿದ್ದಾರೆ", "ತುರ್ತು ಸಹಾಯ", "ಜೀವ ಅಪಾಯ", "ಉಸಿರಾಡಲು ಸಾಧ್ಯವಿಲ್ಲ",
    "ಮರಣ", "ಶವ", "ದೊಡ್ಡ ಅಪಘಾತ", "ಕಟ್ಟಡ ಕುಸಿತ", "ಮನೆ ಕೊಚ್ಚಿಹೋಯಿತು",
    "ನಾವು ಕೊಚ್ಚಿಹೋಗುತ್ತಿದ್ದೇವೆ", "ರಕ್ಷಿಸಿ", "ಜೀವ ಉಳಿಸಿ", "ಸಾಯುತ್ತಿದ್ದೇನೆ",
    "ತೀವ್ರ ಗಾಯ", "ರಕ್ತ ಬರುತ್ತಿದೆ", "ಪ್ರಜ್ಞೆ ಕಳೆದಿದ್ದಾರೆ",
    # English
    "trapped", "drowning", "dying", "help me", "save me", "life risk",
    "building collapsed", "swept away", "unconscious", "bleeding heavily",
    "critical", "mayday", "sos", "people trapped", "no way out",
]

HIGH_KEYWORDS = [
    # Kannada
    "ನೀರು ಮನೆಗೆ ಬಂದಿದೆ", "ಪ್ರವಾಹ ಬಂದಿದೆ", "ಭೂಕುಸಿತ ಆಗಿದೆ",
    "ಭೂಕಂಪ ಆಗಿದೆ", "ಬೆಂಕಿ ಹೊತ್ತಿಕೊಂಡಿದೆ", "ಚಂಡಮಾರುತ ಬರುತ್ತಿದೆ",
    "ರಸ್ತೆ ಮುಳುಗಿದೆ", "ಸೇತುವೆ ಕೊಚ್ಚಿಹೋಯಿತು", "ವಿದ್ಯುತ್ ಕಂಬ ಬಿದ್ದಿದೆ",
    "ಮನೆ ಮುಳುಗಿದೆ", "ಗಾಯಗೊಂಡಿದ್ದಾರೆ", "ತೀವ್ರ ಮಳೆ", "ಪ್ರವಾಹ ಎಚ್ಚರಿಕೆ",
    # English
    "flood water entered", "house flooded", "landslide occurred",
    "earthquake happened", "fire broke out", "cyclone approaching",
    "road blocked", "bridge washed", "injured", "severe rain",
    "flood warning", "evacuation needed", "danger zone",
]

MEDIUM_KEYWORDS = [
    # Kannada
    "ಎಚ್ಚರಿಕೆ", "ಮಳೆ ಬರುತ್ತಿದೆ", "ನೀರು ಹೆಚ್ಚಾಗುತ್ತಿದೆ", "ಸಿದ್ಧರಾಗಿ",
    "ತೆರಳಿ", "ಸ್ಥಳಾಂತರ", "ಸಹಾಯ ಬೇಕು", "ಮನೆ ಖಾಲಿ ಮಾಡಬೇಕು",
    "ಆಹಾರ ಇಲ್ಲ", "ಶುದ್ಧ ನೀರು ಇಲ್ಲ", "ವಿದ್ಯುತ್ ಇಲ್ಲ",
    # English
    "warning", "heavy rain", "water rising", "evacuate", "prepare",
    "shelter needed", "no food", "no clean water", "power outage",
    "road damaged", "alert issued",
]

LOW_KEYWORDS = [
    # Kannada
    "ಮುನ್ನೆಚ್ಚರಿಕೆ", "ಸಲಹೆ", "ಮಾಹಿತಿ", "ಏನು ಮಾಡಬೇಕು", "ಹೇಗೆ",
    "ತಿಳಿಸಿ", "ಸಂಪರ್ಕ ಸಂಖ್ಯೆ", "ಫೋನ್ ನಂಬರ್", "ಯೋಜನೆ",
    # English
    "precaution", "advice", "information", "what to do", "how to",
    "contact number", "helpline", "general", "tips", "awareness",
]

# ─────────────────────────────────────────────────────────────────────────────
# Severity Score Mapping
# ─────────────────────────────────────────────────────────────────────────────

_TIER_WEIGHTS = {
    "CRITICAL": 100,
    "HIGH": 60,
    "MEDIUM": 30,
    "LOW": 10,
}

_KEYWORD_TIERS = [
    ("CRITICAL", CRITICAL_KEYWORDS),
    ("HIGH", HIGH_KEYWORDS),
    ("MEDIUM", MEDIUM_KEYWORDS),
    ("LOW", LOW_KEYWORDS),
]


def _normalize(text: str) -> str:
    """Lowercase and remove punctuation for robust matching."""
    return re.sub(r"[^\w\s]", " ", text.lower())


def classify_severity(query: str) -> Dict:
    """
    Classify a user query into LOW / MEDIUM / HIGH / CRITICAL.

    Returns:
        {
            "severity": "HIGH",
            "score": 60,
            "confidence": 0.85,
            "matched_keywords": ["flood water entered"],
            "color": "#f97316",
            "is_emergency": True
        }
    """
    from config import Severity

    normalized = _normalize(query)
    scores: Dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    matched: list[str] = []

    for tier, keywords in _KEYWORD_TIERS:
        for kw in keywords:
            if _normalize(kw) in normalized:
                scores[tier] += _TIER_WEIGHTS[tier]
                matched.append(kw)

    # Pick highest-scoring tier
    best_tier = max(scores, key=scores.get)
    best_score = scores[best_tier]

    # Default to LOW if nothing matched
    if best_score == 0:
        best_tier = Severity.LOW
        best_score = _TIER_WEIGHTS[Severity.LOW]

    # Confidence: ratio of best tier score to total scored weight
    total_weight = sum(scores.values()) or 1
    confidence = round(min(1.0, best_score / total_weight), 2)

    result = {
        "severity": best_tier,
        "score": best_score,
        "confidence": confidence,
        "matched_keywords": matched[:5],  # top 5
        "color": Severity.COLORS[best_tier],
        "is_emergency": best_tier in Severity.EMERGENCY_TRIGGER,
    }

    logger.info(
        f"Severity classified: {best_tier} (score={best_score}, "
        f"confidence={confidence}, matches={len(matched)})"
    )
    return result


def get_severity_label_kn(severity: str) -> str:
    """Return Kannada label for severity level."""
    labels = {
        "LOW": "ಕಡಿಮೆ",
        "MEDIUM": "ಮಧ್ಯಮ",
        "HIGH": "ಹೆಚ್ಚು",
        "CRITICAL": "ತುರ್ತು",
    }
    return labels.get(severity, "ಕಡಿಮೆ")
