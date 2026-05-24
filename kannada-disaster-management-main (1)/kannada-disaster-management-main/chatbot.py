"""
chatbot.py — Legacy compatibility wrapper
New code should import from services.chatbot_service directly.
Kannada Disaster Management AI System
"""

from services.chatbot_service import ask_chatbot as _ask_chatbot


def ask_chatbot(user_query: str) -> str:
    """
    Backward-compatible wrapper around the improved chatbot service.
    Returns plain response string (same contract as original chatbot.py).
    """
    result = _ask_chatbot(user_query, session_id="legacy")
    return result["response"]