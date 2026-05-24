"""
services/analytics_service.py
In-Memory Analytics Tracker — Query Metrics & Usage Statistics
Kannada Disaster Management AI System
"""

import time
import logging
from collections import defaultdict, deque
from threading import Lock
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Thread-safe in-memory analytics store
# ─────────────────────────────────────────────────────────────────────────────

_lock = Lock()

_store: Dict[str, Any] = {
    "total_queries": 0,
    "voice_queries": 0,
    "text_queries": 0,
    "offline_responses": 0,
    "severity_counts": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
    "category_counts": defaultdict(int),
    "district_counts": defaultdict(int),
    "latency_samples": deque(maxlen=100),     # last 100 response latency (ms)
    "hourly_trend": defaultdict(int),          # hour -> count
    "error_counts": defaultdict(int),          # error_type -> count
    "session_count": 0,
    "start_time": time.time(),
}


def record_query(
    query_type: str,         # "text" | "voice"
    severity: str,           # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    category: str,           # RAG document category
    latency_ms: float,       # response time in milliseconds
    district: str = "",      # optional district from user context
    is_offline: bool = False,
    is_error: bool = False,
    error_type: str = "",
) -> None:
    """Record a single query event into analytics store."""
    with _lock:
        _store["total_queries"] += 1

        if query_type == "voice":
            _store["voice_queries"] += 1
        else:
            _store["text_queries"] += 1

        if is_offline:
            _store["offline_responses"] += 1

        if severity in _store["severity_counts"]:
            _store["severity_counts"][severity] += 1

        if category:
            _store["category_counts"][category] += 1

        if district:
            _store["district_counts"][district] += 1

        _store["latency_samples"].append(latency_ms)

        # Hourly trend (0-23)
        hour = time.strftime("%H")
        _store["hourly_trend"][hour] += 1

        if is_error and error_type:
            _store["error_counts"][error_type] += 1


def record_session() -> None:
    """Increment session count."""
    with _lock:
        _store["session_count"] += 1


def get_stats() -> Dict:
    """Return a JSON-serializable analytics snapshot."""
    with _lock:
        samples = list(_store["latency_samples"])
        avg_latency = round(sum(samples) / len(samples), 1) if samples else 0
        max_latency = round(max(samples), 1) if samples else 0

        uptime_seconds = int(time.time() - _store["start_time"])
        uptime_str = _seconds_to_human(uptime_seconds)

        # Top 5 categories
        top_categories = sorted(
            _store["category_counts"].items(),
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        # Top 5 districts
        top_districts = sorted(
            _store["district_counts"].items(),
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        # Hourly trend: last 12 hours
        current_hour = int(time.strftime("%H"))
        trend_hours = [(current_hour - i) % 24 for i in range(11, -1, -1)]
        hourly_data = [
            {
                "hour": f"{h:02d}:00",
                "count": _store["hourly_trend"].get(f"{h:02d}", 0),
            }
            for h in trend_hours
        ]

        return {
            "total_queries": _store["total_queries"],
            "voice_queries": _store["voice_queries"],
            "text_queries": _store["text_queries"],
            "offline_responses": _store["offline_responses"],
            "session_count": _store["session_count"],
            "severity_distribution": dict(_store["severity_counts"]),
            "top_categories": [{"name": k, "count": v} for k, v in top_categories],
            "top_districts": [{"name": k, "count": v} for k, v in top_districts],
            "avg_latency_ms": avg_latency,
            "max_latency_ms": max_latency,
            "error_counts": dict(_store["error_counts"]),
            "hourly_trend": hourly_data,
            "uptime": uptime_str,
        }


def _seconds_to_human(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}h {m}m {s}s"
