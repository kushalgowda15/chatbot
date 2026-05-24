"""
services/alerts_service.py
Live Disaster Alerts — OpenWeatherMap + IMD RSS + Mock Fallback
Kannada Disaster Management AI System
"""

import time
import logging
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from cachetools import TTLCache
from config import OPENWEATHER_API_KEY, ALERTS_CACHE_TTL_SECONDS, WEATHER_DISTRICTS

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# TTL Caches
# ─────────────────────────────────────────────────────────────────────────────

_weather_cache = TTLCache(maxsize=50, ttl=ALERTS_CACHE_TTL_SECONDS)
_alerts_cache = TTLCache(maxsize=10, ttl=ALERTS_CACHE_TTL_SECONDS)

# ─────────────────────────────────────────────────────────────────────────────
# Karnataka District Coordinates (lat, lon)
# ─────────────────────────────────────────────────────────────────────────────

DISTRICT_COORDS = {
    "Bengaluru":     (12.9716, 77.5946),
    "Mysuru":        (12.2958, 76.6394),
    "Hubballi":      (15.3647, 75.1240),
    "Dharwad":       (15.4589, 75.0078),
    "Belagavi":      (15.8497, 74.4977),
    "Mangaluru":     (12.9141, 74.8560),
    "Ballari":       (15.1394, 76.9214),
    "Vijayapura":    (16.8302, 75.7100),
    "Kalaburagi":    (17.3297, 76.8343),
    "Shivamogga":    (13.9299, 75.5681),
    "Tumakuru":      (13.3409, 77.1010),
    "Raichur":       (16.2120, 77.3439),
    "Hassan":        (13.0068, 76.1003),
    "Chitradurga":   (14.2251, 76.3980),
    "Davanagere":    (14.4644, 75.9218),
    "Udupi":         (13.3409, 74.7421),
    "Chikkamagaluru":(13.3161, 75.7720),
    "Kodagu":        (12.4244, 75.7382),
    "Mandya":        (12.5218, 76.8951),
    "Bidar":         (17.9104, 77.5199),
}

# Severity from OWM condition codes
def _owm_code_to_severity(code: int) -> str:
    if code in range(200, 300):   return "HIGH"      # Thunderstorm
    if code in range(300, 400):   return "MEDIUM"    # Drizzle
    if code in range(500, 600):
        if code >= 502:           return "HIGH"      # Heavy rain
        return "MEDIUM"
    if code in range(600, 700):   return "MEDIUM"    # Snow
    if code in range(700, 800):   return "LOW"       # Atmosphere
    if code == 800:               return "LOW"        # Clear
    if code in range(800, 810):   return "LOW"
    return "LOW"

def _severity_label_kn(severity: str) -> str:
    return {"LOW": "ಕಡಿಮೆ", "MEDIUM": "ಮಧ್ಯಮ", "HIGH": "ಹೆಚ್ಚು", "CRITICAL": "ತುರ್ತು"}.get(severity, "ಕಡಿಮೆ")


# ─────────────────────────────────────────────────────────────────────────────
# OpenWeatherMap Integration
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_owm_weather(district: str) -> Optional[Dict]:
    """Fetch current weather for a district via OpenWeatherMap API."""
    if not OPENWEATHER_API_KEY:
        return None

    cache_key = f"owm_{district}"
    if cache_key in _weather_cache:
        return _weather_cache[cache_key]

    lat, lon = DISTRICT_COORDS.get(district, (12.9716, 77.5946))
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=en"
    )

    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()

        code = data["weather"][0]["id"]
        desc = data["weather"][0]["description"].title()
        temp = data["main"]["temp"]
        rain = data.get("rain", {}).get("1h", 0)
        severity = _owm_code_to_severity(code)

        result = {
            "district": district,
            "description": desc,
            "temp_c": temp,
            "rain_mm": rain,
            "severity": severity,
            "severity_kn": _severity_label_kn(severity),
            "source": "OpenWeatherMap",
            "timestamp": int(time.time()),
        }
        _weather_cache[cache_key] = result
        return result

    except Exception as e:
        logger.warning(f"OWM fetch failed for {district}: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# IMD RSS Feed (Free, No API key)
# ─────────────────────────────────────────────────────────────────────────────

IMD_RSS_URL = "https://rss.weatherusa.net/rss/india/karnataka.xml"

def _fetch_imd_alerts() -> List[Dict]:
    """Parse IMD RSS feed for Karnataka alerts."""
    cache_key = "imd_rss"
    if cache_key in _alerts_cache:
        return _alerts_cache[cache_key]

    try:
        resp = requests.get(IMD_RSS_URL, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")[:5]
        alerts = []
        for item in items:
            title = item.findtext("title", "").strip()
            desc = item.findtext("description", "").strip()
            link = item.findtext("link", "")
            alerts.append({
                "title": title,
                "description": desc[:200],
                "link": link,
                "severity": "MEDIUM",
                "source": "IMD RSS",
                "timestamp": int(time.time()),
            })
        _alerts_cache[cache_key] = alerts
        logger.info(f"IMD RSS: loaded {len(alerts)} alerts")
        return alerts
    except Exception as e:
        logger.warning(f"IMD RSS fetch failed: {e}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Mock / Static Alerts (guaranteed fallback — no API needed)
# ─────────────────────────────────────────────────────────────────────────────

_MOCK_ALERTS = [
    {
        "title": "Karnataka Flood Watch — Kodagu, Hassan Districts",
        "description": (
            "IMD has issued heavy rainfall warning for Western Ghats districts. "
            "River Cauvery water level rising. Residents in low-lying areas advised to evacuate."
        ),
        "severity": "HIGH",
        "severity_kn": "ಹೆಚ್ಚು",
        "district": "Kodagu",
        "source": "IMD Mock",
        "alert_type": "flood",
        "timestamp": int(time.time()),
    },
    {
        "title": "Heatwave Alert — Raichur, Kalaburagi",
        "description": (
            "Maximum temperature expected to cross 44°C. "
            "KSNDMC advises staying indoors between 12:00–16:00. Drink water frequently."
        ),
        "severity": "MEDIUM",
        "severity_kn": "ಮಧ್ಯಮ",
        "district": "Raichur",
        "source": "KSNDMC Mock",
        "alert_type": "heatwave",
        "timestamp": int(time.time()),
    },
    {
        "title": "Landslide Risk — Chikkamagaluru, Shivamogga",
        "description": (
            "Continuous heavy rain has saturated hill slopes. "
            "NDRF teams on standby. Avoid travel in ghat sections."
        ),
        "severity": "HIGH",
        "severity_kn": "ಹೆಚ್ಚು",
        "district": "Chikkamagaluru",
        "source": "KSNDMC Mock",
        "alert_type": "landslide",
        "timestamp": int(time.time()),
    },
    {
        "title": "Thunderstorm Warning — Bengaluru, Tumakuru",
        "description": (
            "IMD warns of isolated thunderstorms with lightning. "
            "Strong winds up to 50 kmph expected. Avoid open areas."
        ),
        "severity": "MEDIUM",
        "severity_kn": "ಮಧ್ಯಮ",
        "district": "Bengaluru",
        "source": "IMD Mock",
        "alert_type": "storm",
        "timestamp": int(time.time()),
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Public API Functions
# ─────────────────────────────────────────────────────────────────────────────

def get_live_alerts(district: str = "") -> List[Dict]:
    """
    Return current disaster alerts for Karnataka (or specific district).
    Tries IMD RSS → falls back to mock data.
    """
    alerts = _fetch_imd_alerts()

    # Add OWM weather alert for requested district
    if district and district in DISTRICT_COORDS:
        weather = _fetch_owm_weather(district)
        if weather and weather["severity"] in ("HIGH", "CRITICAL"):
            alerts.insert(0, {
                "title": f"Weather Alert — {district}",
                "description": (
                    f"{weather['description']}. Temperature: {weather['temp_c']}°C. "
                    f"Rainfall: {weather['rain_mm']} mm/hr"
                ),
                "severity": weather["severity"],
                "severity_kn": weather["severity_kn"],
                "district": district,
                "source": "OpenWeatherMap",
                "alert_type": "weather",
                "timestamp": weather["timestamp"],
            })

    # Always guarantee at least mock alerts
    if not alerts:
        alerts = list(_MOCK_ALERTS)

    # Filter by district if specified
    if district:
        filtered = [a for a in alerts if district.lower() in a.get("district", "").lower()]
        return filtered if filtered else alerts[:2]

    return alerts[:8]


def get_district_weather(district: str) -> Dict:
    """Return weather data for a specific Karnataka district."""
    weather = _fetch_owm_weather(district)
    if weather:
        return weather

    # Generic mock weather if OWM unavailable
    return {
        "district": district,
        "description": "Partly Cloudy",
        "temp_c": 28.0,
        "rain_mm": 0,
        "severity": "LOW",
        "severity_kn": "ಕಡಿಮೆ",
        "source": "Mock",
        "timestamp": int(time.time()),
    }
