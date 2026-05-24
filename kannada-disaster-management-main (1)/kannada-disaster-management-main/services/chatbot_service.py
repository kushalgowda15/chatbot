"""
services/chatbot_service.py
Hybrid RAG Chatbot — FAISS + BM25 + Groq LLM + Conversation Memory
Kannada Disaster Management AI System
"""

import os
import json
import time
import logging
import numpy as np
import faiss
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import defaultdict, deque
from threading import Lock

from groq import Groq
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from config import (
    GROQ_API_KEY, GROQ_MODEL, EMBEDDING_MODEL,
    FAISS_INDEX_PATH, METADATA_PATH,
    RAG_TOP_K, RAG_BM25_WEIGHT, RAG_FAISS_WEIGHT,
    RAG_SIMILARITY_THRESHOLD, CONTEXT_MAX_TOKENS,
    MEMORY_MAX_TURNS, SESSION_TIMEOUT_MINS,
)
from services.severity_service import classify_severity
from services.offline_service import get_offline_response

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Singleton Initialization (load once at startup)
# ─────────────────────────────────────────────────────────────────────────────

logger.info("Loading embedding model...")
_embedding_model = SentenceTransformer(EMBEDDING_MODEL)

logger.info("Loading FAISS vector index...")
try:
    _faiss_index = faiss.read_index(FAISS_INDEX_PATH)
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        _metadata: List[Dict] = json.load(f)
    logger.info(f"FAISS index loaded: {_faiss_index.ntotal} vectors")
    _index_available = True
except Exception as e:
    logger.error(f"FAISS index not found: {e} — RAG will be disabled")
    _faiss_index = None
    _metadata = []
    _index_available = False

# BM25 index over document texts
logger.info("Building BM25 index...")
try:
    _bm25_corpus = [
        f"{item['category']} {item['question']} {item['answer']}".lower().split()
        for item in _metadata
    ]
    _bm25 = BM25Okapi(_bm25_corpus) if _bm25_corpus else None
    logger.info(f"BM25 index built: {len(_bm25_corpus)} docs")
except Exception as e:
    logger.error(f"BM25 index failed: {e}")
    _bm25 = None

# Groq client
_groq_client: Optional[Groq] = None
if GROQ_API_KEY:
    try:
        _groq_client = Groq(api_key=GROQ_API_KEY)
        logger.info("Groq client initialized ✓")
    except Exception as e:
        logger.error(f"Groq init failed: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# Conversation Memory Store (session_id → deque of turns)
# ─────────────────────────────────────────────────────────────────────────────

_memory_lock = Lock()
_sessions: Dict[str, Dict] = {}   # { session_id: { "turns": deque, "last_active": float } }


def _get_session(session_id: str) -> Dict:
    with _memory_lock:
        now = time.time()
        if session_id not in _sessions:
            _sessions[session_id] = {
                "turns": deque(maxlen=MEMORY_MAX_TURNS),
                "last_active": now,
                "severity_state": "LOW",
            }
        else:
            _sessions[session_id]["last_active"] = now
        return _sessions[session_id]


def _add_turn(session_id: str, role: str, content: str) -> None:
    session = _get_session(session_id)
    with _memory_lock:
        session["turns"].append({"role": role, "content": content})


def _build_history_prompt(session_id: str) -> str:
    """Format last N turns as conversation context."""
    session = _get_session(session_id)
    turns = list(session["turns"])
    if not turns:
        return ""
    lines = []
    for turn in turns:
        prefix = "ಬಳಕೆದಾರ" if turn["role"] == "user" else "ಸಹಾಯಕ"
        lines.append(f"{prefix}: {turn['content']}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Hybrid Retrieval: FAISS + BM25 Score Fusion
# ─────────────────────────────────────────────────────────────────────────────

def _faiss_retrieve(query: str, top_k: int) -> List[Tuple[int, float]]:
    """Return (index, cosine_similarity) pairs from FAISS."""
    if not _index_available:
        return []
    q_emb = _embedding_model.encode([query], convert_to_numpy=True).astype("float32")
    distances, indices = _faiss_index.search(q_emb, top_k)
    results = []
    for idx, dist in zip(indices[0], distances[0]):
        if idx < 0:
            continue
        # Convert L2 distance to similarity score (0-1)
        similarity = 1.0 / (1.0 + float(dist))
        results.append((idx, similarity))
    return results


def _bm25_retrieve(query: str, top_k: int) -> List[Tuple[int, float]]:
    """Return (index, normalized_bm25_score) pairs."""
    if _bm25 is None:
        return []
    tokens = query.lower().split()
    scores = _bm25.get_scores(tokens)
    top_indices = np.argsort(scores)[::-1][:top_k]
    max_score = scores[top_indices[0]] if len(top_indices) > 0 else 1.0
    results = []
    for idx in top_indices:
        norm_score = float(scores[idx]) / max(max_score, 1e-6)
        results.append((int(idx), norm_score))
    return results


def retrieve_context(query: str, top_k: int = RAG_TOP_K) -> Tuple[str, float, List[str]]:
    """
    Hybrid retrieval: FAISS + BM25 score fusion.

    Returns:
        (context_text, retrieval_confidence, source_citations)
    """
    faiss_results = _faiss_retrieve(query, top_k)
    bm25_results = _bm25_retrieve(query, top_k)

    # Fuse scores
    fused: Dict[int, float] = defaultdict(float)
    for idx, score in faiss_results:
        fused[idx] += score * RAG_FAISS_WEIGHT
    for idx, score in bm25_results:
        fused[idx] += score * RAG_BM25_WEIGHT

    # Sort by fused score, apply threshold
    ranked = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:top_k]

    contexts: List[str] = []
    citations: List[str] = []
    best_score = 0.0

    char_count = 0
    for idx, score in ranked:
        if score < RAG_SIMILARITY_THRESHOLD:
            logger.debug(f"Chunk {idx} rejected: score {score:.3f} < threshold {RAG_SIMILARITY_THRESHOLD}")
            continue
        if idx >= len(_metadata):
            continue

        item = _metadata[idx]
        chunk = (
            f"[Category: {item['category']}]\n"
            f"Q: {item['question']}\n"
            f"A: {item['answer']}"
        )

        # Respect context token budget
        if char_count + len(chunk) > CONTEXT_MAX_TOKENS:
            break

        contexts.append(chunk)
        citations.append(f"{item['category']} — {item['question'][:60]}...")
        char_count += len(chunk)

        if score > best_score:
            best_score = score

    retrieval_confidence = round(best_score, 3)

    if not contexts:
        logger.warning("No relevant context retrieved above threshold")
        return "", 0.0, []

    return "\n\n---\n\n".join(contexts), retrieval_confidence, citations


# ─────────────────────────────────────────────────────────────────────────────
# Prompt Templates
# ─────────────────────────────────────────────────────────────────────────────

def _build_prompt(
    query: str,
    context: str,
    history: str,
    severity: str,
    citations: List[str],
) -> str:
    """Build a structured, grounded prompt based on severity level."""

    citation_block = ""
    if citations:
        citation_block = "\n\nSource Documents:\n" + "\n".join(
            f"• {c}" for c in citations[:3]
        )

    history_block = f"\nConversation History:\n{history}\n" if history else ""

    if severity in ("HIGH", "CRITICAL"):
        instruction = (
            "EMERGENCY RESPONSE MODE ACTIVE.\n"
            "Provide IMMEDIATE, life-safety-focused guidance.\n"
            "Format: numbered steps. Start with the most critical action.\n"
            "Include emergency helpline numbers at the end.\n"
            "Be direct. No unnecessary introductions."
        )
    else:
        instruction = (
            "Provide clear, practical disaster safety guidance.\n"
            "Format: situation summary + 3-4 actionable steps.\n"
            "Include relevant helpline numbers if appropriate."
        )

    return f"""You are a Kannada Disaster Management AI Assistant for the State Emergency Operations Center (SEOC), Karnataka.

CRITICAL RULES:
- Answer ONLY in Kannada (ಕನ್ನಡ)
- Base your answer on the provided context. Do NOT hallucinate facts or numbers.
- If context is insufficient, say "ನನ್ನ ಬಳಿ ಈ ವಿಷಯದ ಸ್ಪಷ್ಟ ಮಾಹಿತಿ ಇಲ್ಲ" and give general safety guidance
- Never fabricate helpline numbers — only use: 1070 (SEOC), 1077 (DEOC), 112 (Police), 101 (Fire), 108 (Ambulance), 104 (Health)
- Keep response under 150 words
- Emergency level: {severity}

{instruction}

Retrieved Context:
{context if context else "ಸಂದರ್ಭ ಸಿಗಲಿಲ್ಲ — ಸಾಮಾನ್ಯ ಸುರಕ್ಷತಾ ಮಾರ್ಗದರ್ಶನ ನೀಡಿ"}
{citation_block}
{history_block}
Current User Query: {query}

Response in Kannada:"""


# ─────────────────────────────────────────────────────────────────────────────
# Main Chat Function
# ─────────────────────────────────────────────────────────────────────────────

def ask_chatbot(
    query: str,
    session_id: str = "default",
) -> Dict:
    """
    Main chatbot entry point.

    Args:
        query: User query (Kannada or English)
        session_id: Session ID for conversation memory

    Returns:
        {
            "response": str,
            "severity": str,
            "severity_color": str,
            "is_emergency": bool,
            "citations": List[str],
            "retrieval_confidence": float,
            "is_offline": bool,
            "latency_ms": float,
        }
    """
    start_time = time.time()
    is_offline = False

    # 1. Classify severity
    severity_result = classify_severity(query)
    severity = severity_result["severity"]

    # 2. Retrieve context (hybrid FAISS + BM25)
    context, retrieval_confidence, citations = retrieve_context(query)

    # 3. Build conversation history
    history = _build_history_prompt(session_id)

    # 4. Call LLM (with offline fallback)
    response_text = ""
    if _groq_client is None:
        logger.warning("No Groq client — using offline fallback")
        response_text = get_offline_response(query)
        is_offline = True
    else:
        prompt = _build_prompt(query, context, history, severity, citations)
        try:
            completion = _groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.25,
                max_tokens=300,
            )
            response_text = completion.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq API error: {e} — switching to offline fallback")
            response_text = get_offline_response(query)
            is_offline = True

    # 5. Update conversation memory
    _add_turn(session_id, "user", query)
    _add_turn(session_id, "assistant", response_text[:200])  # store trimmed

    # 6. Update session severity state
    session = _get_session(session_id)
    with _memory_lock:
        session["severity_state"] = severity

    latency_ms = round((time.time() - start_time) * 1000, 1)
    logger.info(
        f"Chat complete | severity={severity} | confidence={retrieval_confidence} "
        f"| offline={is_offline} | latency={latency_ms}ms"
    )

    return {
        "response": response_text,
        "severity": severity,
        "severity_color": severity_result["color"],
        "is_emergency": severity_result["is_emergency"],
        "citations": citations[:3],
        "retrieval_confidence": retrieval_confidence,
        "is_offline": is_offline,
        "latency_ms": latency_ms,
        "matched_keywords": severity_result.get("matched_keywords", []),
    }
