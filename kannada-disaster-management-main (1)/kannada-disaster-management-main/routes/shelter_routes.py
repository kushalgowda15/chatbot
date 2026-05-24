"""
routes/shelter_routes.py
GIS Shelter Data API — Karnataka Relief Camps
Kannada Disaster Management AI System
"""

import logging
from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)
shelter_bp = Blueprint("shelters", __name__)

# ─────────────────────────────────────────────────────────────────────────────
# Static shelter data (Karnataka districts — real-world inspired coordinates)
# In production: replace with live database query
# ─────────────────────────────────────────────────────────────────────────────

_SHELTERS = [
    {"id": 1,  "name_kn": "ಕೊಡಗು ಪ್ರಾಥಮಿಕ ಪರಿಹಾರ ಶಿಬಿರ",    "name": "Kodagu Primary Relief Camp",      "district": "Kodagu",         "district_kn": "ಕೊಡಗು",       "lat": 12.3375, "lng": 75.8069, "capacity_max": 500,  "capacity_used": 320, "status": "OPEN",  "contact": "08272-228510"},
    {"id": 2,  "name_kn": "ಹಾಸನ ಜಿಲ್ಲಾ ಪರಿಹಾರ ಶಿಬಿರ",         "name": "Hassan District Relief Camp",    "district": "Hassan",         "district_kn": "ಹಾಸನ",        "lat": 13.0068, "lng": 76.1003, "capacity_max": 800,  "capacity_used": 800, "status": "FULL",  "contact": "08172-268100"},
    {"id": 3,  "name_kn": "ಶಿವಮೊಗ್ಗ ತುರ್ತು ಆಶ್ರಯ ಕೇಂದ್ರ",     "name": "Shivamogga Emergency Shelter",   "district": "Shivamogga",     "district_kn": "ಶಿವಮೊಗ್ಗ",   "lat": 13.9299, "lng": 75.5681, "capacity_max": 600,  "capacity_used": 210, "status": "OPEN",  "contact": "08182-277100"},
    {"id": 4,  "name_kn": "ಚಿಕ್ಕಮಗಳೂರು ಪರಿಹಾರ ಶಿಬಿರ",         "name": "Chikkamagaluru Relief Camp",     "district": "Chikkamagaluru", "district_kn": "ಚಿಕ್ಕಮಗಳೂರು","lat": 13.3161, "lng": 75.7720, "capacity_max": 300,  "capacity_used": 145, "status": "OPEN",  "contact": "08262-234567"},
    {"id": 5,  "name_kn": "ರಾಯಚೂರು ಜಿಲ್ಲಾ ಪರಿಹಾರ ಕೇಂದ್ರ",    "name": "Raichur District Relief Center", "district": "Raichur",        "district_kn": "ರಾಯಚೂರು",    "lat": 16.2120, "lng": 77.3439, "capacity_max": 1000, "capacity_used": 430, "status": "OPEN",  "contact": "08532-220100"},
    {"id": 6,  "name_kn": "ಕಲಬುರಗಿ ಪ್ರಾಥಮಿಕ ಶಿಬಿರ",            "name": "Kalaburagi Primary Camp",        "district": "Kalaburagi",     "district_kn": "ಕಲಬುರಗಿ",    "lat": 17.3297, "lng": 76.8343, "capacity_max": 700,  "capacity_used": 700, "status": "FULL",  "contact": "08472-277000"},
    {"id": 7,  "name_kn": "ಬೆಳಗಾವಿ ತುರ್ತು ಪರಿಹಾರ ಶಿಬಿರ",      "name": "Belagavi Emergency Relief Camp", "district": "Belagavi",       "district_kn": "ಬೆಳಗಾವಿ",    "lat": 15.8497, "lng": 74.4977, "capacity_max": 1200, "capacity_used": 560, "status": "OPEN",  "contact": "0831-2420100"},
    {"id": 8,  "name_kn": "ಉತ್ತರ ಕನ್ನಡ ಪರಿಹಾರ ಕೇಂದ್ರ",        "name": "Uttara Kannada Relief Center",   "district": "Uttara Kannada", "district_kn": "ಉತ್ತರ ಕನ್ನಡ","lat": 14.7932, "lng": 74.6782, "capacity_max": 400,  "capacity_used": 180, "status": "OPEN",  "contact": "08382-226100"},
    {"id": 9,  "name_kn": "ಮಂಗಳೂರು ಕರಾವಳಿ ಪರಿಹಾರ ಶಿಬಿರ",     "name": "Mangaluru Coastal Relief Camp",  "district": "Dakshina Kannada","district_kn": "ದಕ್ಷಿಣ ಕನ್ನಡ","lat": 12.8747, "lng": 74.8422, "capacity_max": 900,  "capacity_used": 350, "status": "OPEN",  "contact": "0824-2220100"},
    {"id": 10, "name_kn": "ಬೆಂಗಳೂರು ವಿಪತ್ತು ನಿರ್ವಹಣಾ ಕೇಂದ್ರ", "name": "Bengaluru Disaster Mgmt Center", "district": "Bengaluru Urban","district_kn": "ಬೆಂಗಳೂರು",   "lat": 12.9716, "lng": 77.5946, "capacity_max": 2000, "capacity_used": 120, "status": "OPEN",  "contact": "080-22230021"},
]


@shelter_bp.route("/api/shelters", methods=["GET"])
def get_shelters():
    """
    Return list of active Karnataka relief shelters.

    Query params:
        district (optional): Filter by district name
        status (optional): Filter by "OPEN" or "FULL"
    """
    district_filter = request.args.get("district", "").strip().lower()
    status_filter = request.args.get("status", "").strip().upper()

    shelters = list(_SHELTERS)

    if district_filter:
        shelters = [s for s in shelters if district_filter in s["district"].lower()]

    if status_filter in ("OPEN", "FULL"):
        shelters = [s for s in shelters if s["status"] == status_filter]

    return jsonify(shelters)
