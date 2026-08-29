"""
Persist the sentiment model used for inference on the Avengers dataset.

All model logic (vectorizer, classifier, training, saving) lives in
ML/Source/Twitter/Sentiment_analysis.py so there is a single source of truth.
This file just imports that and writes the artifact the dashboard loads.

Output: Backend/models/sentiment_model.joblib
"""

import sys
from pathlib import Path

ML_DIR = Path(__file__).resolve().parents[1] / "ML" / "Source" / "Twitter"
sys.path.insert(0, str(ML_DIR))

from Sentiment_analysis import train_and_save_model  # noqa: E402

MODEL_PATH = Path(__file__).resolve().parent / "models" / "sentiment_model.joblib"


if __name__ == "__main__":
    path = train_and_save_model(MODEL_PATH)
    print("Saved model to", path)
