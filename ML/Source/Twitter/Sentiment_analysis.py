from pathlib import Path

import joblib
import pandas as pd

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

BASE_DIR = Path(__file__).resolve().parents[3]

TRAIN_CSV = BASE_DIR / "Data/Processed/Twitter Training Dataset Cleaned.csv"
TEST_CSV = BASE_DIR / "Data/Processed/Twitter Testing Dataset Cleaned.csv"


# ---------------------------------------------------------------------------
# Single source of truth for the deployed model configuration
# ---------------------------------------------------------------------------

def build_vectorizer():
    return TfidfVectorizer(
        lowercase=False,
        ngram_range=(1, 2),
        min_df=1,
        sublinear_tf=True,
    )


def build_model():
    return LogisticRegression(max_iter=1000, C=10, random_state=42)


def load_training(csv_path=TRAIN_CSV):
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=["text"])
    df = df[df["text"].str.strip() != ""]
    df = df[df["text_processed"].fillna("").str.strip() != ""].copy()
    return df


def load_eval_test(train_df, csv_path=TEST_CSV):
    test_df = pd.read_csv(csv_path)
    train_texts = set(train_df["text"])
    test_eval = test_df[~test_df["text"].isin(train_texts)].copy()
    test_eval = test_eval.reset_index(drop=True)
    return test_eval


def train_pipeline(train_df=None):
    if train_df is None:
        train_df = load_training()

    X = train_df["text_processed"]
    y = train_df["sentiment"]

    vectorizer = build_vectorizer()
    X_tf = vectorizer.fit_transform(X)
    model = build_model()
    model.fit(X_tf, y)
    return {
        "vectorizer": vectorizer,
        "model": model,
        "classes": list(model.classes_),
    }


def save_model(bundle, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, path)
    return path


def load_model(path):
    return joblib.load(path)


def predict_texts(texts, bundle):
    vectorizer = bundle["vectorizer"]
    model = bundle["model"]
    X = vectorizer.transform([str(t) for t in texts])
    return model.predict(X), model.predict_proba(X)


def train_and_save_model(model_path):
    """Fit on the training corpus and persist the pipeline for inference."""
    train_df = load_training()
    bundle = train_pipeline(train_df)
    print(
        "Training accuracy:",
        bundle["model"].score(
            bundle["vectorizer"].transform(train_df["text_processed"]),
            train_df["sentiment"],
        ),
    )
    print("Classes:", bundle["classes"])
    return save_model(bundle, model_path)


# ---------------------------------------------------------------------------
# Optional hyper-parameter tuning (not used by the deployed model)
# ---------------------------------------------------------------------------

def hyperparameter_tunning(X_train, y_train):
    pipeline = Pipeline([
        ("tfidf", build_vectorizer()),
        ("lr", build_model()),
    ])

    param_grid = {
        "tfidf__ngram_range": [(1, 1), (1, 2)],
        "tfidf__min_df": [1, 2, 5],
        "tfidf__sublinear_tf": [False, True],
        "lr__C": [0.1, 1, 10],
    }

    grid_search = GridSearchCV(
        pipeline,
        param_grid,
        cv=3,
        scoring="f1_macro",
        n_jobs=-1,
        verbose=1,
    )

    grid_search.fit(X_train, y_train)

    print("\n" + "=" * 60)
    print("BEST PARAMETERS")
    print("=" * 60)

    print(grid_search.best_params_)

    print(
        f"\nBest CV Macro F1: "
        f"{grid_search.best_score_:.4f}"
    )

    best_model = grid_search.best_estimator_
    return best_model


def metrics(y_pred, y_test):
    accuracy = accuracy_score(y_test, y_pred)

    print("\n" + "=" * 60)
    print("MODEL RESULTS")
    print("=" * 60)

    print(f"\nAccuracy: {accuracy:.4f}")

    print("\nClassification Report:")
    print(
        classification_report(
            y_test,
            y_pred,
            digits=4
        )
    )

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))


# ---------------------------------------------------------------------------
# Direct execution: evaluate on a held-out test set
# ---------------------------------------------------------------------------

def main():
    train_df = load_training()
    test_eval = load_eval_test(train_df)

    X_train = train_df["text_processed"]
    y_train = train_df["sentiment"]
    X_test = test_eval["text_processed"]
    y_test = test_eval["sentiment"]

    bundle = train_pipeline(train_df)
    y_pred, _ = predict_texts(X_test, bundle)
    # metrics(y_pred, y_test)  # uncomment for the full classification report

    results = test_eval[["text", "sentiment"]].copy()
    results["predicted"] = y_pred

    errors = results[
        results["sentiment"] != results["predicted"]
    ]

    print("Total errors:", len(errors))
    try:
        print(errors.to_string(index=False))
    except UnicodeEncodeError:
        print(errors.to_string(index=False).encode("ascii", "replace").decode("ascii"))


if __name__ == "__main__":
    main()