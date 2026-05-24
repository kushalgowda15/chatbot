"""
app.py — Production Flask Application Entry Point
Kannada Disaster Management AI System
"""

import logging
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import (
    FLASK_HOST, FLASK_PORT, FLASK_DEBUG, SECRET_KEY,
    RATE_LIMIT_CHAT, RATE_LIMIT_VOICE, RATE_LIMIT_ALERTS,
    validate_env,
)

# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("app")

# ─────────────────────────────────────────────────────────────────────────────
# App Factory
# ─────────────────────────────────────────────────────────────────────────────
def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )
    app.secret_key = SECRET_KEY

    # CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Rate Limiting
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "60 per minute"],
        storage_uri="memory://",
    )

    # ── Register Blueprints ──────────────────────────────────────────────────
    from routes.chat_routes import chat_bp
    from routes.shelter_routes import shelter_bp
    from routes.alert_routes import alert_bp
    from routes.analytics_routes import analytics_bp
    from routes.health_routes import health_bp

    app.register_blueprint(chat_bp)
    app.register_blueprint(shelter_bp)
    app.register_blueprint(alert_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(health_bp)

    # ── Apply per-route rate limits ──────────────────────────────────────────
    from routes.chat_routes import chat_api, voice_api
    from routes.alert_routes import live_alerts
    limiter.limit(RATE_LIMIT_CHAT)(chat_api)
    limiter.limit(RATE_LIMIT_VOICE)(voice_api)
    limiter.limit(RATE_LIMIT_ALERTS)(live_alerts)

    # ── Home Route ───────────────────────────────────────────────────────────
    @app.route("/")
    def home():
        return render_template("index.html")

    # ── Structured Error Handlers ────────────────────────────────────────────
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad Request", "message": str(e)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not Found", "message": str(e)}), 404

    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify({
            "error": "Rate limit exceeded",
            "message": "ತುಂಬಾ ಅನೇಕ ವಿನಂತಿಗಳು. ದಯವಿಟ್ಟು ಸ್ವಲ್ಪ ಕಾಯಿರಿ.",
        }), 429

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Internal server error: {e}")
        return jsonify({
            "error": "Internal Server Error",
            "message": "ಸರ್ವರ್ ದೋಷ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
        }), 500

    # ── Request Logging ──────────────────────────────────────────────────────
    @app.before_request
    def log_request():
        from flask import request
        if request.path.startswith("/api/"):
            logger.info(f"→ {request.method} {request.path} [{request.remote_addr}]")

    @app.after_request
    def log_response(response):
        from flask import request
        if request.path.startswith("/api/"):
            logger.info(f"← {response.status_code} {request.path}")
        return response

    logger.info("✅ Flask app created with all blueprints registered")
    return app


# ─────────────────────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    validate_env()

    app = create_app()

    import sys
    # Force UTF-8 output on Windows terminals to avoid cp1252 UnicodeEncodeError
    if sys.stdout.encoding != "utf-8":
        sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

    print("\n" + "=" * 55)
    print("  [SHIELD] Karnataka Disaster Management AI System")
    print("  Kannada EOC Suite — Production Mode")
    print(f"  [URL]  http://127.0.0.1:{FLASK_PORT}")
    print(f"  [DBG]  Debug Mode: {FLASK_DEBUG}")
    print("=" * 55 + "\n")

    app.run(
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=FLASK_DEBUG,
    )