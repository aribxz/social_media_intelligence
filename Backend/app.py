"""
Flask backend for the SMI prototype.

The heavy Pandas analysis lives in analytics.py and is written to JSON files
under Outputs/. This server simply loads those JSON files and exposes them
through stable GET endpoints, so the frontend never touches the analysis code.

Endpoints
    GET /api/timeline       -> timeline.json
    GET /api/trends         -> trends.json
    GET /api/propagation    -> propagation.json
    GET /api/sentiment      -> sentiment.json
    GET /api/limitations   -> limitations.json
    GET /api/health        -> {"status": "ok"}
    GET /                   -> endpoint listing

Run:
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