from pathlib import Path

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

train_df = pd.read_csv(BASE_DIR / "Data/Processed/Twitter Training Dataset Cleaned.csv")
test_df = pd.read_csv(BASE_DIR / "Data/Processed/Twitter Testing Dataset Cleaned.csv")

train_df = train_df.dropna(subset=["text"]) #  Drops rows where the text column is NULL.
train_df = train_df[train_df["text"].str.strip() != ""] # Keeps only rows whoose text after taking out whitespace is not empty.

# Removing empty processed training tweet
train_df = train_df[
    train_df["text_processed"].fillna("").str.strip() != ""
].copy() # Replace NaN with ""

# Creating unseen test set
train_texts = set(train_df["text"]) # Makes a set of all text rows (fast look-up)

test_eval = test_df[
    ~test_df["text"].isin(train_texts)
].copy() # Keeps only test rows whose text is not (~) in the training set (prevents leakage).

test_eval = test_eval.reset_index(drop=True) # Cleanly resets indexes from 0.

# Train and Validation split
# X = train_df["text_processed"]
# y = train_df["sentiment"]

# X_train, X_val, y_train, y_val = train_test_split(
#     X,
#     y,
#     test_size=0.20,
#     random_state=42,
#     stratify=y
# )

X_train = train_df["text_processed"]
y_train = train_df["sentiment"]

X_test = test_eval["text_processed"]
y_test = test_eval["sentiment"]

def hyperparameter_tunning(X_train, y_train):
    pipeline = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                lowercase=False
            )
        ),
        (
            "lr",
            LogisticRegression(
                max_iter=1000,
                random_state=42
            )
        )
    ])

    param_grid = {
        "tfidf__ngram_range": [
            (1, 1),
            (1, 2)
        ],

        "tfidf__min_df": [
            1,
            2,
            5
        ],

        "tfidf__sublinear_tf": [
            False,
            True
        ],

        "lr__C": [
            0.1,
            1,
            10
        ]
    }

    grid_search = GridSearchCV(
        pipeline,
        param_grid,
        cv=3,
        scoring="f1_macro",
        n_jobs=-1,
        verbose=1
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

# Term Frequency-Inverse Document
def tf(X_train, X_test): # A technique that converts strings into numbers a model can use.
    vectorizer = TfidfVectorizer( # Buulds a vocab and makes a column of all unique words
        lowercase=False,
        ngram_range=(1,2),
        min_df=1,
        sublinear_tf=True
    )

    X_train_tf = vectorizer.fit_transform(X_train) # Learn vocab and IDF weights (How rare is the word)
    X_test_tf = vectorizer.transform(X_test) # Doesnt relearn so it leakage prevented.

    return X_train_tf, X_test_tf

def logistic_regression(X_train_tf, y_train, X_test_tf):
    model = LogisticRegression(max_iter=1000, C=10, random_state=42)
    model.fit(X_train_tf, y_train)

    y_pred = model.predict(X_test_tf)

    return y_pred

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

X_train_tf, X_test_tf = tf(X_train, X_test)
y_pred = logistic_regression(X_train_tf, y_train, X_test_tf)
# metrics(y_pred, y_test)

results = test_eval[["text", "sentiment"]].copy()
results["predicted"] = y_pred

errors = results[
    results["sentiment"] != results["predicted"]
]

print("Total errors:", len(errors))
print(errors.to_string(index=False))