"""
routes/analytics_routes.py
Analytics Dashboard API
Kannada Disaster Management AI System
"""

import logging
from flask import Blueprint, jsonify
from services import analytics_service

logger = logging.getLogger(__name__)
analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/api/analytics/stats", methods=["GET"])
def analytics_stats():
    """Return system analytics metrics for the dashboard."""
    try:
        stats = analytics_service.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.exception(f"Analytics API error: {e}")
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/api/analytics/reset", methods=["POST"])
def reset_analytics():
    """Reset analytics counters (admin use)."""
    # Simple protection — only from localhost
    from flask import request
    if request.remote_addr not in ("127.0.0.1", "::1", "localhost"):
        return jsonify({"error": "Unauthorized"}), 403
    return jsonify({"message": "Analytics reset not supported in in-memory mode"}), 200
