"""
Flask backend for the SMI prototype.

The heavy Pandas analysis lives in analytics.py (Twitter) and
is written to JSON files
under Outputs/. This server simply loads those JSON files and exposes
them through stable GET endpoints, so the frontend never touches the
analysis code.

Endpoints (Twitter)
    GET /api/timeline       -> timeline.json
    GET /api/trends         -> trends.json
    GET /api/propagation    -> propagation.json
    GET /api/sentiment      -> sentiment.json
    GET /api/limitations   -> limitations.json

Endpoints (shared)
    GET /api/health        -> {"status": "ok"}
    GET /                   -> endpoint listing

Run:
    python analytics.py            # Twitter outputs
    python app.py
"""

from pathlib import Path

import json
from flask import Flask, jsonify, send_file, abort, request

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "Outputs"
FRONTEND_DIR = BASE_DIR.parent / "Frontend"

app = Flask(__name__)


FILES = {
    "timeline": "timeline.json",
    "trends": "trends.json",
    "propagation": "propagation.json",
    "sentiment": "sentiment.json",
    "limitations": "limitations.json",
}

# HELPER FUNCTION
def load_output(name):
    filename = FILES.get(name)

    if filename is None:
        abort(404, description="Unknown output")

    file_path = OUTPUT_DIR / filename

    if not file_path.exists():
        abort(
            404,
            description=f"{filename} not found in Outputs/"
        )

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError:
        abort(
            500,
            description=f"{filename} contains invalid JSON"
        )



# API ENDPOINTS
@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok"
    })


@app.get("/api/timeline")
def timeline():
    return jsonify(load_output("timeline"))


@app.get("/api/trends")
def trends():
    return jsonify(load_output("trends"))


@app.get("/api/propagation")
def propagation():
    return jsonify(load_output("propagation"))


@app.get("/api/sentiment")
def sentiment():
    return jsonify(load_output("sentiment"))


@app.get("/api/limitations")
def limitations():
    return jsonify(load_output("limitations"))

# FRONTEND
@app.get("/")
def home():
    index_file = FRONTEND_DIR / "index.html"

    if not index_file.exists():
        abort(404, description="index.html not found")

    return send_file(index_file)


@app.get("/<path:filename>")
def frontend(filename):
    file_path = FRONTEND_DIR / filename

    if not file_path.exists():
        abort(404, description="Frontend file not found")

    return send_file(file_path)


# RUN SERVER
if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )