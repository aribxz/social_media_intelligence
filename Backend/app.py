"""
Flask backend for the SMI prototype.
"""

import os
from pathlib import Path

import json
from flask import Flask, jsonify, abort, send_from_directory

# PATH CONFIGURATION

# Backend
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "Outputs"
PROJECT_DIR = BASE_DIR.parent
FRONTEND_DIR = PROJECT_DIR / "Frontend"

# FLASK APPLICATION

app = Flask(__name__)

@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    return response


@app.route("/api/<path:path>", methods=["OPTIONS"])
@app.route("/api/instagram/<path:path>", methods=["OPTIONS"])
def handle_options(path=None):
    return ("", 204)

FILES = {
    # Twitter
    "timeline": "timeline.json",
    "trends": "trends.json",
    "propagation": "propagation.json",
    "sentiment": "sentiment.json",
    "limitations": "limitations.json",

    # Instagram
    "instagram_timeline": "instagram_timeline.json",
    "instagram_trends": "instagram_trends.json",
    "instagram_propagation": "instagram_propagation.json",
    "instagram_sentiment": "instagram_sentiment.json",
    "instagram_engagement": "instagram_engagement.json",
    "instagram_limitations": "instagram_limitations.json",
}

# HELPER FUNCTIONS

def load_output(name):
    filename = FILES.get(name)

    if filename is None:
        abort(
            404,
            description="Unknown output requested."
        )

    file_path = OUTPUT_DIR / filename

    if not file_path.is_file():
        abort(
            404,
            description=(
                f"Output file '{filename}' was not found. "
                f"Run the corresponding analysis script first."
            )
        )

    try:
        with file_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError:
        abort(
            500,
            description=f"Output file '{filename}' contains invalid JSON."
        )

    except OSError:
        abort(
            500,
            description=f"Unable to read output file '{filename}'."
        )


def api_response(name):
    return jsonify(load_output(name))

# HEALTH CHECK

@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok"
    })

# TWITTER ENDPOINTS

@app.get("/api/timeline")
def timeline():
    return api_response("timeline")


@app.get("/api/trends")
def trends():
    return api_response("trends")


@app.get("/api/propagation")
def propagation():
    return api_response("propagation")


@app.get("/api/sentiment")
def sentiment():
    return api_response("sentiment")


@app.get("/api/limitations")
def limitations():
    return api_response("limitations")

# INSTAGRAM ENDPOINTS

@app.get("/api/instagram/timeline")
def instagram_timeline():
    return api_response("instagram_timeline")


@app.get("/api/instagram/trends")
def instagram_trends():
    return api_response("instagram_trends")


@app.get("/api/instagram/propagation")
def instagram_propagation():
    return api_response("instagram_propagation")


@app.get("/api/instagram/sentiment")
def instagram_sentiment():
    return api_response("instagram_sentiment")


@app.get("/api/instagram/engagement")
def instagram_engagement():
    return api_response("instagram_engagement")


@app.get("/api/instagram/limitations")
def instagram_limitations():
    return api_response("instagram_limitations")

# API INFORMATION

@app.get("/api")
def api_info():
    return jsonify({
        "name": "SMI Prototype API",
        "status": "running",

        "twitter": {
            "timeline": "/api/timeline",
            "trends": "/api/trends",
            "propagation": "/api/propagation",
            "sentiment": "/api/sentiment",
            "limitations": "/api/limitations",
        },

        "instagram": {
            "timeline": "/api/instagram/timeline",
            "trends": "/api/instagram/trends",
            "propagation": "/api/instagram/propagation",
            "sentiment": "/api/instagram/sentiment",
            "engagement": "/api/instagram/engagement",
            "limitations": "/api/instagram/limitations",
        },

        "shared": {
            "health": "/api/health",
            "api_info": "/api",
            "home": "/",
        }
    })

# FRONTEND

@app.get("/")
def home():
    index_file = FRONTEND_DIR / "index.html"

    if not index_file.is_file():
        abort(
            404,
            description="Frontend index.html not found."
        )

    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )

@app.get("/<path:filename>")
def frontend(filename):
    # Prevent shadowing unknown API routes — return JSON 404 for /api/*
    if filename.startswith("api/"):
        return jsonify({
            "error": "Not Found",
            "message": f"Unknown API endpoint '/{filename}'"
        }), 404

    requested_file = FRONTEND_DIR / filename

    if not requested_file.is_file():
        abort(
            404,
            description=f"Frontend file '{filename}' not found."
        )

    return send_from_directory(
        FRONTEND_DIR,
        filename
    )

# ERROR HANDLERS

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Not Found",
        "message": error.description
    }), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "error": "Internal Server Error",
        "message": getattr(
            error,
            "description",
            "An unexpected server error occurred."
        )
    }), 500

# RUN SERVER — Render-ready: binds 0.0.0.0:$PORT, debug off in production

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")
    host = "0.0.0.0"

    print("=" * 60)
    print("SMI Flask Backend")
    print("=" * 60)

    print(f"Backend directory : {BASE_DIR}")
    print(f"Output directory  : {OUTPUT_DIR}")
    print(f"Frontend directory: {FRONTEND_DIR}")
    print(f"Environment       : {'development' if debug else 'production'}")

    print("\nAPI running at:")
    print(f"http://{host}:{port}")

    print("\nHealth check:")
    print(f"http://{host}:{port}/api/health")

    print("\nAPI documentation:")
    print(f"http://{host}:{port}/api")

    print("=" * 60)

    app.run(
        host=host,
        port=port,
        debug=debug
    )
