"""
services/offline_service.py
Offline Emergency Fallback — works without LLM API
Kannada Disaster Management AI System
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# OFFLINE FAQ DATASET
# Critical Kannada Q&A that works without internet / LLM
# ─────────────────────────────────────────────────────────────────────────────

OFFLINE_FAQ = [
    {
        "keywords": ["ಪ್ರವಾಹ", "flood", "ನೀರು ಹೆಚ್ಚಾ", "ಮನೆ ಮುಳುಗ"],
        "response": (
            "🌊 **ಪ್ರವಾಹ ಸಂದರ್ಭದಲ್ಲಿ ಮಾಡಬೇಕಾದ ಕ್ರಮಗಳು:**\n"
            "1. ತಕ್ಷಣ ಎತ್ತರದ ಸ್ಥಳಕ್ಕೆ ತೆರಳಿ\n"
            "2. ವಿದ್ಯುತ್ ಸ್ವಿಚ್ ಆಫ್ ಮಾಡಿ\n"
            "3. ಮಕ್ಕಳು ಮತ್ತು ಹಿರಿಯರಿಗೆ ಮೊದಲ ಆದ್ಯತೆ ನೀಡಿ\n"
            "4. ತುರ್ತು: SEOC 1070 | ಪೊಲೀಸ್ 112 | ಅಂಬ್ಯುಲೆನ್ಸ್ 108"
        ),
    },
    {
        "keywords": ["ಭೂಕಂಪ", "earthquake", "ನಡುಕ"],
        "response": (
            "🏚️ **ಭೂಕಂಪ ಸಂದರ್ಭದಲ್ಲಿ ಮಾಡಬೇಕಾದ ಕ್ರಮಗಳು:**\n"
            "1. ಟೇಬಲ್ ಅಡಿ ಅಥವಾ ಗೋಡೆಗೆ ಒತ್ತಿಕೊಳ್ಳಿ (Drop, Cover, Hold On)\n"
            "2. ಕಿಟಕಿ ಮತ್ತು ಬಾಗಿಲಿನಿಂದ ದೂರ ಇರಿ\n"
            "3. ನಡುಕ ನಿಂತ ಬಳಿಕ ತೆರೆದ ಸ್ಥಳಕ್ಕೆ ತೆರಳಿ\n"
            "4. ತುರ್ತು: NDRF 9711077372 | SEOC 1070"
        ),
    },
    {
        "keywords": ["ಭೂಕುಸಿತ", "landslide", "ಮಣ್ಣು ಜಾರ"],
        "response": (
            "⛰️ **ಭೂಕುಸಿತ ಸಂದರ್ಭದಲ್ಲಿ ಮಾಡಬೇಕಾದ ಕ್ರಮಗಳು:**\n"
            "1. ತಕ್ಷಣ ಗುಡ್ಡದಿಂದ ದೂರ ತೆರಳಿ\n"
            "2. ನದಿ ಮತ್ತು ಕಣಿವೆ ಪ್ರದೇಶದಿಂದ ಮಾರಿ ಇರಿ\n"
            "3. ಅಧಿಕಾರಿಗಳ ಸೂಚನೆ ಅನುಸರಿಸಿ\n"
            "4. ತುರ್ತು: SEOC 1070 | DEOC 1077"
        ),
    },
    {
        "keywords": ["ಬೆಂಕಿ", "fire", "ಅಗ್ನಿ", "ಸುಟ್ಟ"],
        "response": (
            "🔥 **ಬೆಂಕಿ ತುರ್ತು ಸಂದರ್ಭದಲ್ಲಿ ಮಾಡಬೇಕಾದ ಕ್ರಮಗಳು:**\n"
            "1. ತಕ್ಷಣ ಕಟ್ಟಡ ಖಾಲಿ ಮಾಡಿ — ಎಲಿವೇಟರ್ ಬಳಸಬೇಡಿ\n"
            "2. ಹೊಗೆ ತಪ್ಪಿಸಲು ಕೆಳಗೆ ಬಾಗಿ ತೆರಳಿ\n"
            "3. ಬಾಗಿಲು ಮುಚ್ಚಿ ಬೆಂಕಿ ಹರಡದಂತೆ ತಡೆಯಿರಿ\n"
            "4. ತುರ್ತು: ಅಗ್ನಿಶಾಮಕ 101 | ಅಂಬ್ಯುಲೆನ್ಸ್ 108"
        ),
    },
    {
        "keywords": ["ಚಂಡಮಾರುತ", "cyclone", "ಬಿರುಗಾಳಿ", "ತೂಫಾನ್"],
        "response": (
            "🌀 **ಚಂಡಮಾರುತ ಸಂದರ್ಭದಲ್ಲಿ ಮಾಡಬೇಕಾದ ಕ್ರಮಗಳು:**\n"
            "1. ಗಟ್ಟಿ ಕಟ್ಟಡದಲ್ಲಿ ಆಶ್ರಯ ಪಡೆಯಿರಿ\n"
            "2. ಕಿಟಕಿ ಮತ್ತು ಬಾಗಿಲು ಮುಚ್ಚಿ\n"
            "3. ವಿದ್ಯುತ್ ಸಾಧನ ಬಳಕೆ ನಿಲ್ಲಿಸಿ\n"
            "4. ತುರ್ತು: SEOC 1070 | ಕರಾವಳಿ ರಕ್ಷಣಾ 1554"
        ),
    },
    {
        "keywords": ["ಉಷ್ಣಗಾಳಿ", "heatwave", "ಸೆಕೆ", "ಬಿಸಿಲು"],
        "response": (
            "🌡️ **ತೀವ್ರ ಉಷ್ಣಗಾಳಿ ಸಂದರ್ಭದಲ್ಲಿ ಮಾಡಬೇಕಾದ ಕ್ರಮಗಳು:**\n"
            "1. ನೀರು ಹೆಚ್ಚು ಕುಡಿಯಿರಿ — ಬಿಸಿಲಿನಲ್ಲಿ ಹೊರಗೆ ಹೋಗಬೇಡಿ\n"
            "2. ತಿಳಿ ಬಣ್ಣದ ಬಟ್ಟೆ ಧರಿಸಿ\n"
            "3. ವೃದ್ಧರು ಮತ್ತು ಮಕ್ಕಳ ಮೇಲೆ ನಿಗಾ ಇಡಿ\n"
            "4. ತುರ್ತು: ಆರೋಗ್ಯ ಸಹಾಯ 104 | ಅಂಬ್ಯುಲೆನ್ಸ್ 108"
        ),
    },
    {
        "keywords": ["ರಕ್ಷಣಾ ಕೇಂದ್ರ", "shelter", "ಆಶ್ರಯ", "ಪರಿಹಾರ ಶಿಬಿರ"],
        "response": (
            "🏕️ **ಪರಿಹಾರ ಶಿಬಿರ ಮಾಹಿತಿ:**\n"
            "1. ಸ್ಥಳೀಯ ಶಾಲೆ ಅಥವಾ ಸರ್ಕಾರಿ ಕಟ್ಟಡಕ್ಕೆ ತೆರಳಿ\n"
            "2. ಗ್ರಾಮ ಪಂಚಾಯಿತಿ ಅಥವಾ ತಹಶೀಲ್ದಾರ್ ಅಧಿಕಾರಿ ಸಂಪರ್ಕಿಸಿ\n"
            "3. ತುರ್ತು ಸಂಪರ್ಕ:\n"
            "   - SEOC: 1070\n"
            "   - DEOC: 1077\n"
            "   - ಪೊಲೀಸ್: 112"
        ),
    },
    {
        "keywords": ["ಸಂಪರ್ಕ", "helpline", "ನಂಬರ್", "ಫೋನ್", "contact"],
        "response": (
            "📞 **ತುರ್ತು ಸಹಾಯವಾಣಿ ಸಂಖ್ಯೆಗಳು:**\n"
            "• SEOC (ರಾಜ್ಯ ನಿಯಂತ್ರಣ ಕೊಠಡಿ): **1070**\n"
            "• DEOC (ಜಿಲ್ಲಾ ನಿಯಂತ್ರಣ ಕೊಠಡಿ): **1077**\n"
            "• ಪೊಲೀಸ್ ತುರ್ತು: **112**\n"
            "• ಅಗ್ನಿಶಾಮಕ ದಳ: **101**\n"
            "• ಆಂಬ್ಯುಲೆನ್ಸ್ (TTS): **108**\n"
            "• NDRF: **9711077372**\n"
            "• ಆರೋಗ್ಯ ಸಹಾಯ: **104**"
        ),
    },
    {
        "keywords": ["ಮೊದಲ ಸಹಾಯ", "first aid", "ಗಾಯ", "ಔಷಧ"],
        "response": (
            "🩺 **ಪ್ರಾಥಮಿಕ ಚಿಕಿತ್ಸೆ ಮಾರ್ಗದರ್ಶನ:**\n"
            "1. ಗಾಯದ ಸ್ಥಳ ಸ್ವಚ್ಛ ಬಟ್ಟೆಯಿಂದ ಒತ್ತಿ ರಕ್ತ ನಿಲ್ಲಿಸಿ\n"
            "2. ಮೂಳೆ ಮುರಿದಿದ್ದರೆ ಸ್ಥಳ ಅಲ್ಲಾಡಿಸಬೇಡಿ\n"
            "3. ಅಂಬ್ಯುಲೆನ್ಸ್: **108**\n"
            "4. ಆರೋಗ್ಯ ಸಹಾಯ: **104**"
        ),
    },
]

# Generic fallback when no keyword matches
_GENERIC_FALLBACK = (
    "ℹ️ **ಸಾಮಾನ್ಯ ವಿಪತ್ತು ಸುರಕ್ಷತಾ ಮಾರ್ಗದರ್ಶನ (ಆಫ್‌ಲೈನ್ ಮೋಡ್):**\n"
    "1. ಶಾಂತವಾಗಿರಿ ಮತ್ತು ಸ್ಥಳೀಯ ಅಧಿಕಾರಿಗಳ ಸೂಚನೆ ಪಾಲಿಸಿ\n"
    "2. ತುರ್ತು ಸಂಪರ್ಕ: SEOC **1070** | ಪೊಲೀಸ್ **112**\n"
    "3. ಆಂಬ್ಯುಲೆನ್ಸ್: **108** | ಅಗ್ನಿಶಾಮಕ: **101**\n"
    "⚠️ ಸರ್ವರ್ ಸಂಪರ್ಕ ಸಮಸ್ಯೆ — ಆಫ್‌ಲೈನ್ ಮೋಡ್‌ನಲ್ಲಿ ಉತ್ತರ ನೀಡಲಾಗಿದೆ."
)


def _normalize(text: str) -> str:
    return re.sub(r"[^\w\s]", " ", text.lower())


def get_offline_response(query: str) -> str:
    """
    Match query against offline FAQ.
    Returns a safe Kannada response without internet/LLM.
    """
    normalized = _normalize(query)
    best_match: Optional[str] = None
    best_count = 0

    for faq in OFFLINE_FAQ:
        count = sum(
            1 for kw in faq["keywords"]
            if _normalize(kw) in normalized
        )
        if count > best_count:
            best_count = count
            best_match = faq["response"]

    if best_match:
        logger.info(f"Offline FAQ matched (score={best_count})")
        return best_match

    logger.info("Offline FAQ: no match — returning generic fallback")
    return _GENERIC_FALLBACK
