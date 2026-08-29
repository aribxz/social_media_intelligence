"""
Social Media Intelligence (SMI) analytics engine for the Avengers / twitter_clean
dataset.

Separates all Pandas analysis from Flask. Running this script computes:
    - Timeline analysis
    - Trend analysis
    - Content propagation analysis
    - Model-predicted sentiment (inference only, no retraining)

and writes four frontend-friendly JSON files to Backend/Outputs/:
    timeline.json, trends.json, propagation.json, sentiment.json

Run order:
    python train_sentiment.py   # once, creates the saved model
    python analytics.py         # (re)generates the JSON outputs
"""

from pathlib import Path
import re

import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = Path(__file__).resolve().parent / "Outputs"
MODEL_PATH = Path(__file__).resolve().parent / "models" / "sentiment_model.joblib"

AVENGERS_CSV = BASE_DIR / "Data/Processed/Twitter_clean.csv"

# Sentiment label set (match the trained model's classes).
SENTIMENTS = ["Positive", "Neutral", "Negative"]

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

TIME_FMT = "%Y-%m-%d %H:%M"


def load_data():
    """Load the Avengers dataset and validate required columns."""
    df = pd.read_csv(AVENGERS_CSV)
    required = {
        "id", "text", "text_clean", "created", "user", "is_retweet",
        "retweet_count", "favorite_count", "time_bin", "tweet_type",
    }

    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Avengers dataset missing columns: {missing}")

    # Normalise the time bin to a pandas datetime for resampling.
    df["time_bin_dt"] = pd.to_datetime(df["time_bin"], errors="coerce")
    # 5-minute bin used throughout the dashboard.
    df["time_bin_5"] = df["time_bin_dt"].dt.floor("5min")
    return df


def five_min_label(ts):
    return ts.strftime(TIME_FMT)

# ---------------------------------------------------------------------------
# Text preprocessing (must match the training text_processed transformation)
# ---------------------------------------------------------------------------

_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_MENTION_RE = re.compile(r"@\w+")


def preprocess(text):
    """Replicate the training preprocessing:
    - remove URLs
    - replace @mentions with the USER_MENTION token
    """
    if not isinstance(text, str):
        text = "" if text is None or pd.isna(text) else str(text)
    text = _URL_RE.sub(" ", text)
    text = _MENTION_RE.sub("USER_MENTION", text)
    return text


# ===========================================================================
# PART 1 - Timeline Analysis
# ===========================================================================

def timeline_analysis(df):
    g = df.groupby("time_bin_5")

    volume = g.size().rename("total_tweets")
    original = df[~df["is_retweet"]].groupby("time_bin_5").size()
    retweet = df[df["is_retweet"]].groupby("time_bin_5").size()

    timeline = pd.DataFrame({
        "total_tweets": volume,
        "original": original,
        "retweet": retweet,
    }).fillna(0).astype(int).sort_index()

    timeline.index = [five_min_label(t) for t in timeline.index]
    timeline_records = [
        {
            "time_bin": idx,
            "total_tweets": int(row.total_tweets),
            "original": int(row.original),
            "retweet": int(row.retweet),
        }
        for idx, row in timeline.iterrows()
    ]
    timeline.index.name = "time_bin"

    peak_idx = timeline["total_tweets"].idxmax()
    peak_row = timeline.loc[peak_idx]

    top_bins = (
        timeline["total_tweets"]
        .sort_values(ascending=False)
        .head(5)
        .reset_index()
    )
    top_bins_records = [
        {"time_bin": r["time_bin"], "total_tweets": int(r["total_tweets"])}
        for _, r in top_bins.iterrows()
    ]

    total_tweets = int(timeline["total_tweets"].sum())
    total_originals = int(timeline["original"].sum())
    total_retweets = int(timeline["retweet"].sum())

    summary = {
        "total_tweets": total_tweets,
        "total_originals": total_originals,
        "total_retweets": total_retweets,
        "retweet_percentage": round(100 * total_retweets / total_tweets, 2),
        "original_percentage": round(100 * total_originals / total_tweets, 2),
        "start_time": five_min_label(df["time_bin_5"].min()),
        "end_time": five_min_label(df["time_bin_5"].max()),
        "peak_time": peak_idx,
        "peak_volume": int(peak_row["total_tweets"]),
    }

    return {
        "summary": summary,
        "timeline": timeline_records,
        "top_intervals": top_bins_records,
        "peak": {
            "peak_time_bin": peak_idx,
            "peak_tweet_count": int(peak_row["total_tweets"]),
        },
    }


# ===========================================================================
# PART 2 - Trend Analysis
# ===========================================================================

_HASHTAG_RE = re.compile(r"#\w+")
_MENTION_TREND_RE = re.compile(r"@\w+")
_STOPWORDS = set("""
a an and are as at be by for from has he in is it its of on that the to was
were what when where which who why will with i you your we they them his her
she this these those there but or not no if so do does did have had has me my
our their our us out up down off over under again about into can cant could
should would may might must im ive dont didnt isnt arent wasnt werent
rt http https co t s re ve ll m d
""".split())


def _tokenize(text):
    # Keep hashtags/mentions as tokens; split the rest on non-word chars.
    text = str(text).lower()
    tokens = re.findall(r"#\w+|@\w+|[a-z']+", text)
    return tokens


def trend_analysis(df):
    texts = df["text_clean"].fillna("").astype(str)

    # 1. Hashtag frequency (case-insensitive grouping).
    hashtags = _HASHTAG_RE.findall(" ".join(texts.tolist()))
    hashtag_counts = pd.Series(hashtags).str.lower().value_counts().head(20)
    hashtags_records = [
        {"hashtag": h, "count": int(c)} for h, c in hashtag_counts.items()
    ]

    # 2. Mention frequency.
    mentions = _MENTION_TREND_RE.findall(" ".join(texts.tolist()))
    mention_counts = pd.Series(mentions).str.lower().value_counts().head(20)
    mentions_records = [
        {"username": m, "count": int(c)} for m, c in mention_counts.items()
    ]

    # 3. Most common meaningful words (stopword + hashtag/mention filtered).
    all_tokens = []
    for t in texts:
        all_tokens.extend(_tokenize(t))
    words = [
        w for w in all_tokens
        if w not in _STOPWORDS and len(w) > 1
        and not w.startswith("#") and not w.startswith("@")
    ]
    word_counts = pd.Series(words).value_counts().head(20)
    words_records = [
        {"word": w, "count": int(c)} for w, c in word_counts.items()
    ]

    # 4. Phrase frequency (simple bigrams over cleaned tokens).
    bigrams = []
    for t in texts:
        toks = [w for w in _tokenize(t)
                if w not in _STOPWORDS and not w.startswith("#")
                and not w.startswith("@") and len(w) > 1]
        for a, b in zip(toks, toks[1:]):
            bigrams.append(f"{a} {b}")
    phrase_counts = pd.Series(bigrams).value_counts().head(20)
    phrases_records = [
        {"phrase": p, "count": int(c)} for p, c in phrase_counts.items()
    ]

    # 5. Trends over time for the strongest hashtags.
    top_hashtags = [h for h, _ in hashtag_counts.head(5).items()]
    trend_over_time = []
    for h in top_hashtags:
        pattern = re.compile(re.escape(h), re.IGNORECASE)
        sub = df[
            df["text_clean"].fillna("").astype(str).str.contains(pattern)
        ]
        counts = sub.groupby("time_bin_5").size()
        counts = counts.reindex(df["time_bin_5"].drop_duplicates().sort_values().unique(), fill_value=0)
        timeline = [
            {"time_bin": five_min_label(ts), "count": int(c)}
            for ts, c in counts.items()
        ]
        trend_over_time.append({"term": h, "timeline": timeline})

    return {
        "hashtags": hashtags_records,
        "mentions": mentions_records,
        "top_words": words_records,
        "phrases": phrases_records,
        "trends_over_time": trend_over_time,
    }


# ===========================================================================
# PART 3 - Content Propagation
# ===========================================================================

def propagation_analysis(df):
    # 1. Original vs retweet ratio.
    total_tweets = len(df)
    total_originals = int((~df["is_retweet"]).sum())
    total_retweets = int(df["is_retweet"].sum())

    ratio = {
        "total_originals": total_originals,
        "total_retweets": total_retweets,
        "original_percentage": round(100 * total_originals / total_tweets, 2),
        "retweet_percentage": round(100 * total_retweets / total_tweets, 2),
    }

    # 2. Top original tweets by retweet count.
    originals = df[~df["is_retweet"]].copy()
    top_originals = originals.sort_values(
        "retweet_count", ascending=False
    ).head(20)
    top_originals_records = [
        {
            "tweet_id": int(r["id"]),
            "user": r["user"],
            "text": r["text"],
            "retweet_count": int(r["retweet_count"]),
            "favorite_count": int(r["favorite_count"]),
            "created": r["created"],
        }
        for _, r in top_originals.iterrows()
    ]

    # 3. Top content by engagement (retweet + favorite).
    df["engagement"] = df["retweet_count"] + df["favorite_count"]
    top_engagement = df.sort_values(
        "engagement", ascending=False
    ).head(20)
    top_engagement_records = [
        {
            "tweet_id": int(r["id"]),
            "user": r["user"],
            "text": r["text"],
            "retweet_count": int(r["retweet_count"]),
            "favorite_count": int(r["favorite_count"]),
            "engagement": int(r["engagement"]),
        }
        for _, r in top_engagement.iterrows()
    ]

    # 4. Repeated content (by cleaned text).
    repeated = (
        df["text_clean"].fillna("").astype(str)
        .value_counts()
    )
    repeated = repeated[repeated > 1].head(20)
    repeated_records = [
        {"content": c, "occurrence_count": int(n)}
        for c, n in repeated.items()
    ]

    # 5. Propagation (retweet volume) over time.
    prop = df.groupby("time_bin_5")
    retweets_t = df[df["is_retweet"]].groupby("time_bin_5").size()
    originals_t = df[~df["is_retweet"]].groupby("time_bin_5").size()
    prop_df = pd.DataFrame({
        "retweets": retweets_t,
        "originals": originals_t,
    }).fillna(0).astype(int).sort_index()
    prop_df["total"] = prop_df["retweets"] + prop_df["originals"]
    prop_df.index = [five_min_label(t) for t in prop_df.index]
    propagation_timeline = [
        {
            "time_bin": idx,
            "retweets": int(row.retweets),
            "originals": int(row.originals),
            "total": int(row.total),
        }
        for idx, row in prop_df.iterrows()
    ]

    # 6. Propagation summary.
    top_repeated_content = repeated_records[0]["content"] if repeated_records else None
    # Most retweeted single content (by cleaned text with highest total retweets).
    agg = df.groupby(df["text_clean"].fillna("").astype(str)).agg(
        total_retweets=("retweet_count", "sum"),
        user=("user", "first"),
    )
    top_row = agg.sort_values("total_retweets", ascending=False).head(1)
    top_retweeted_content = top_row.index[0] if len(top_row) else None
    top_retweeted_user = top_row["user"].iloc[0] if len(top_row) else None

    summary = {
        "total_retweets": total_retweets,
        "total_originals": total_originals,
        "retweet_percentage": round(100 * total_retweets / total_tweets, 2),
        "top_retweeted_content": top_retweeted_content,
        "top_retweeted_user": top_retweeted_user,
        "most_repeated_content": top_repeated_content,
    }

    return {
        "ratio": ratio,
        "top_original_tweets": top_originals_records,
        "top_content_by_engagement": top_engagement_records,
        "repeated_content": repeated_records,
        "propagation_timeline": propagation_timeline,
        "summary": summary,
    }


# ===========================================================================
# PART 4 - Sentiment Analysis (inference only)
# ===========================================================================

def load_sentiment_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Sentiment model not found at {MODEL_PATH}. "
            "Run train_sentiment.py first."
        )
    return joblib.load(MODEL_PATH)


def sentiment_analysis(df, model_bundle):
    vectorizer = model_bundle["vectorizer"]
    model = model_bundle["model"]
    classes = model_bundle["classes"]

    texts = df["text"].fillna("").astype(str).apply(preprocess)
    X = vectorizer.transform(texts)
    preds = model.predict(X)
    proba = model.predict_proba(X)

    df = df.copy()
    df["pred_sentiment"] = preds

    # 1. Overall distribution.
    dist = pd.Series(preds).value_counts()
    counts = {s: int(dist.get(s, 0)) for s in SENTIMENTS}
    total = int(sum(counts.values()))
    distribution = {
        "counts": counts,
        "percentages": {
            s: round(100 * counts[s] / total, 2) for s in SENTIMENTS
        },
        "total": total,
    }

    # 2. Sentiment over time (per 5-min bin, counts + percentages).
    by_bin = df.groupby("time_bin_5")["pred_sentiment"]
    sentiment_time = []
    for ts, series in by_bin:
        vc = series.value_counts()
        rec = {
            "time_bin": five_min_label(ts),
        }
        for s in SENTIMENTS:
            rec[s] = int(vc.get(s, 0))
        n = int(series.size)
        for s in SENTIMENTS:
            rec[f"{s.lower()}_percentage"] = round(100 * rec[s] / n, 2) if n else 0.0
        sentiment_time.append(rec)
    sentiment_time.sort(key=lambda r: r["time_bin"])

    # 3. Sentiment trend (mean predicted probability per sentiment over time).
    proba_df = pd.DataFrame(proba, columns=classes)
    proba_df["time_bin_5"] = df["time_bin_5"].values
    trend = []
    for ts, sub in proba_df.groupby("time_bin_5"):
        rec = {"time_bin": five_min_label(ts)}
        for s in SENTIMENTS:
            if s in classes:
                rec[s] = round(float(sub[s].mean()), 4)
            else:
                rec[s] = 0.0
        trend.append(rec)
    trend.sort(key=lambda r: r["time_bin"])

    # 4. Sentiment + activity combined.
    combined = []
    # reuse timeline totals
    vol = df.groupby("time_bin_5").size()
    for ts, series in by_bin:
        vc = series.value_counts()
        n = int(series.size)
        rec = {"time_bin": five_min_label(ts), "total_tweets": n}
        for s in SENTIMENTS:
            rec[s] = int(vc.get(s, 0))
        for s in SENTIMENTS:
            rec[f"{s.lower()}_percentage"] = (
                round(100 * rec[s] / n, 2) if n else 0.0
            )
        combined.append(rec)
    combined.sort(key=lambda r: r["time_bin"])

    return {
        "distribution": distribution,
        "sentiment_over_time": sentiment_time,
        "sentiment_trend": trend,
        "sentiment_activity": combined,
        "note": (
            "Sentiment is model-predicted, not ground truth. The Avengers "
            "dataset has no sentiment labels; predictions come from a "
            "TF-IDF + Logistic Regression model trained on a separate "
            "labeled Twitter sentiment corpus."
        ),
    }


# ===========================================================================
# Orchestration
# ===========================================================================

def run_all():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_data()

    print("Timeline...")
    timeline = timeline_analysis(df)
    print("Trends...")
    trends = trend_analysis(df)
    print("Propagation...")
    propagation = propagation_analysis(df)

    print("Sentiment (loading model)...")
    model_bundle = load_sentiment_model()
    sentiment = sentiment_analysis(df, model_bundle)

    outputs = {
        "timeline.json": timeline,
        "trends.json": trends,
        "propagation.json": propagation,
        "sentiment.json": sentiment,
    }
    for name, data in outputs.items():
        path = OUTPUT_DIR / name
        with open(path, "w", encoding="utf-8") as f:
            import json
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("Wrote", path)

    # Limitations note reused by the frontend.
    limits = {
        "geo_analysis_not_meaningful": True,
        "retweets_dominate_dataset": True,
        "sentiment_is_model_predicted": True,
        "limited_time_window": True,
        "notes": [
            "Sentiment is model-predicted, not ground truth.",
            "The Twitter dataset represents a limited sample/time window (~81 minutes).",
            "Retweets heavily dominate the dataset (~90%).",
            "Propagation analysis measures observable signals, not a complete network.",
            "Geographic analysis is not meaningful due to insufficient coordinates.",
            "Trends reflect this dataset and time period, not Twitter as a whole.",
        ],
    }
    with open(OUTPUT_DIR / "limitations.json", "w", encoding="utf-8") as f:
        import json
        json.dump(limits, f, ensure_ascii=False, indent=2)
    print("Wrote", OUTPUT_DIR / "limitations.json")


if __name__ == "__main__":
    run_all()