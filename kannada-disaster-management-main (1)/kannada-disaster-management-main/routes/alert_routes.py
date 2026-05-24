"""
routes/alert_routes.py
Live Disaster Alerts API
Kannada Disaster Management AI System
"""

import logging
from flask import Blueprint, jsonify, request
from services.alerts_service import get_live_alerts, get_district_weather

logger = logging.getLogger(__name__)
alert_bp = Blueprint("alerts", __name__)


@alert_bp.route("/api/alerts", methods=["GET"])
def live_alerts():
    """
    Return current disaster alerts for Karnataka.

    Query params:
        district (optional): Filter by district name
    """
    try:
        district = request.args.get("district", "").strip()
        alerts = get_live_alerts(district=district)
        return jsonify({
            "alerts": alerts,
            "count": len(alerts),
            "district_filter": district or "All Karnataka",
        })
    except Exception as e:
        logger.exception(f"Alerts API error: {e}")
        return jsonify({"error": str(e), "alerts": []}), 500


@alert_bp.route("/api/weather", methods=["GET"])
def district_weather():
    """
    Return current weather for a Karnataka district.

    Query params:
        district (required): District name (e.g. Bengaluru, Mysuru)
    """
    try:
        district = request.args.get("district", "Bengaluru").strip()
        weather = get_district_weather(district)
        return jsonify(weather)
    except Exception as e:
        logger.exception(f"Weather API error: {e}")
        return jsonify({"error": str(e)}), 500
