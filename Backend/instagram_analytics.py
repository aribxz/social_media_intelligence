"""
Social Media Intelligence (SMI) — Instagram analytics engine.

Reads Data/Processed/Instagram_with_balanced_captions.csv and runs the four
analytical pillars (Timeline, Trends, Propagation, Sentiment) over the
Instagram dataset, mirroring the Twitter analytics in analytics.py.

Sentiment is computed with VADER (lexicon-based), exactly as used in the
notebooks under ML/Source/Instagram. Captions are pre-bundled in
Instagram_with_balanced_captions.csv (synthetic captions generated for
engagement simulation). Sentiment outputs are therefore model-predicted,
not ground truth — matching the Twitter sentiment workflow.

Outputs (written to Backend/Outputs/):
    instagram_timeline.json
    instagram_trends.json
    instagram_propagation.json
    instagram_sentiment.json
    instagram_engagement.json  (extra: like-comment-share funnel,
                                risk scoring, top posts by metric)

Run:
    pip install vaderSentiment
    python instagram_analytics.py
"""

from pathlib import Path
import re
import json

import pandas as pd

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except ImportError:
    raise SystemExit(
        "vaderSentiment is required. Install with:  pip install vaderSentiment"
    )

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = Path(__file__).resolve().parent / "Outputs"

INSTAGRAM_CSV = BASE_DIR / "Data/Processed/Instagram_with_balanced_captions.csv"

# Sentiment label set (VADER-driven).
SENTIMENTS = ["Positive", "Neutral", "Negative"]

TIME_FMT_DATE = "%Y-%m-%d"
TIME_FMT_DT = "%Y-%m-%d %H:%M"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def load_data():
    """Load the Instagram dataset and validate required columns."""
    df = pd.read_csv(INSTAGRAM_CSV)

    required = {
        "post_id", "caption", "account_id", "account_type", "follower_count",
        "media_type", "content_category", "traffic_source", "post_datetime",
        "post_date", "post_hour", "day_of_week",
        "likes", "comments", "shares", "saves", "reach", "impressions",
        "engagement_rate", "followers_gained", "caption_length",
        "hashtags_count", "performance_bucket_label",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Instagram dataset missing columns: {missing}")

    df["post_date"] = pd.to_datetime(df["post_date"], errors="coerce")
    df["post_datetime"] = pd.to_datetime(df["post_datetime"], errors="coerce")

    # 1-day bin used for the dashboard (Instagram data is sampled daily).
    df["time_bin"] = df["post_date"].dt.floor("1D")
    return df


# ===========================================================================
# PART 1 — Timeline Analysis
# ===========================================================================

def timeline_analysis(df):
    g = df.groupby("time_bin")

    volume = g.size().rename("total_posts")
    reel = df[df["media_type"].str.lower() == "reel"].groupby("time_bin").size()
    image = df[df["media_type"].str.lower() == "image"].groupby("time_bin").size()
    carousel = df[df["media_type"].str.lower() == "carousel"].groupby("time_bin").size()

    timeline = pd.DataFrame({
        "total_posts": volume,
        "reel": reel,
        "image": image,
        "carousel": carousel,
    }).fillna(0).astype(int).sort_index()

    timeline_records = [
        {
            "time_bin": ts.strftime(TIME_FMT_DATE),
            "total_posts": int(row.total_posts),
            "reel": int(row.reel),
            "image": int(row.image),
            "carousel": int(row.carousel),
        }
        for ts, row in timeline.iterrows()
    ]

    peak_idx = timeline["total_posts"].idxmax()
    peak_row = timeline.loc[peak_idx]

    top_bins = (
        timeline["total_posts"]
        .sort_values(ascending=False)
        .head(5)
        .reset_index()
    )
    top_bins_records = [
        {
            "time_bin": r["time_bin"].strftime(TIME_FMT_DATE),
            "total_posts": int(r["total_posts"]),
        }
        for _, r in top_bins.iterrows()
    ]

    total_posts = int(timeline["total_posts"].sum())
    total_reels = int(timeline["reel"].sum())
    total_images = int(timeline["image"].sum())
    total_carousels = int(timeline["carousel"].sum())

    summary = {
        "total_posts": total_posts,
        "total_reels": total_reels,
        "total_images": total_images,
        "total_carousels": total_carousels,
        "reel_percentage": round(100 * total_reels / total_posts, 2),
        "image_percentage": round(100 * total_images / total_posts, 2),
        "carousel_percentage": round(100 * total_carousels / total_posts, 2),
        "start_date": df["time_bin"].min().strftime(TIME_FMT_DATE),
        "end_date": df["time_bin"].max().strftime(TIME_FMT_DATE),
        "peak_date": peak_idx.strftime(TIME_FMT_DATE),
        "peak_volume": int(peak_row["total_posts"]),
    }

    return {
        "summary": summary,
        "timeline": timeline_records,
        "top_intervals": top_bins_records,
        "peak": {
            "peak_date": peak_idx.strftime(TIME_FMT_DATE),
            "peak_post_count": int(peak_row["total_posts"]),
        },
    }


# ===========================================================================
# PART 2 — Trend Analysis
# ===========================================================================

_HASHTAG_RE = re.compile(r"#\w+")
_MENTION_RE = re.compile(r"@\w+")
_STOPWORDS = set("""
a an and are as at be by for from has he in is it its of on that the to was
were what when where which who why will with i you your we they them his her
she this these those there but or not no if so do does did have had has me my
our their our us out up down off over under again about into can cant could
should would may might must im ive dont didnt isnt arent wasnt werent
rt http https co t s re ve ll m d
""".split())


def _tokenize(text):
    text = str(text).lower()
    return re.findall(r"#\w+|@\w+|[a-z']+", text)


def trend_analysis(df):
    captions = df["caption"].fillna("").astype(str)
    cat = df["content_category"].fillna("Unknown").astype(str)
    media = df["media_type"].fillna("unknown").astype(str)
    traffic = df["traffic_source"].fillna("Unknown").astype(str)

    # 1. Top hashtags
    hashtags = _HASHTAG_RE.findall(" ".join(captions.tolist()))
    hashtag_counts = pd.Series(hashtags).str.lower().value_counts().head(20)
    hashtags_records = [
        {"hashtag": h, "count": int(c)} for h, c in hashtag_counts.items()
    ]

    # 2. Top mentions
    mentions = _MENTION_RE.findall(" ".join(captions.tolist()))
    mention_counts = pd.Series(mentions).str.lower().value_counts().head(20)
    mentions_records = [
        {"username": m, "count": int(c)} for m, c in mention_counts.items()
    ]

    # 3. Top words (filtered)
    all_tokens = []
    for c in captions:
        all_tokens.extend(_tokenize(c))
    words = [
        w for w in all_tokens
        if w not in _STOPWORDS and len(w) > 1
        and not w.startswith("#") and not w.startswith("@")
    ]
    word_counts = pd.Series(words).value_counts().head(20)
    words_records = [
        {"word": w, "count": int(c)} for w, c in word_counts.items()
    ]

    # 4. Top phrases (bigrams over cleaned tokens)
    bigrams = []
    for c in captions:
        toks = [
            w for w in _tokenize(c)
            if w not in _STOPWORDS and not w.startswith("#")
            and not w.startswith("@") and len(w) > 1
        ]
        for a, b in zip(toks, toks[1:]):
            bigrams.append(f"{a} {b}")
    phrase_counts = pd.Series(bigrams).value_counts().head(20)
    phrases_records = [
        {"phrase": p, "count": int(c)} for p, c in phrase_counts.items()
    ]

    # 5. Content category distribution
    cat_counts = cat.value_counts().head(15)
    cat_records = [
        {"category": c, "count": int(n)} for c, n in cat_counts.items()
    ]

    # 6. Media type distribution
    media_counts = media.str.lower().value_counts()
    media_records = [
        {"media_type": m, "count": int(n)} for m, n in media_counts.items()
    ]

    # 7. Traffic source distribution
    traffic_counts = traffic.value_counts().head(15)
    traffic_records = [
        {"source": s, "count": int(n)} for s, n in traffic_counts.items()
    ]

    # 8. Posting heatmap — posts by day-of-week × hour
    heat = df.groupby(["day_of_week", "post_hour"]).size().unstack(fill_value=0)
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday",
                  "Friday", "Saturday", "Sunday"]
    heat = heat.reindex([d for d in days_order if d in heat.index], fill_value=0)
    heat_records = [
        {
            "day_of_week": d,
            "hours": {int(h): int(heat.loc[d, h]) for h in heat.columns},
        }
        for d in heat.index
    ]

    # 9. Top hashtags over time (timeline per top hashtag)
    top_hashtags = [h for h, _ in hashtag_counts.head(5).items()]
    trends_over_time = []
    for h in top_hashtags:
        pattern = re.compile(re.escape(h), re.IGNORECASE)
        sub = df[captions.str.contains(pattern)]
        counts = sub.groupby("time_bin").size()
        all_bins = df["time_bin"].drop_duplicates().sort_values().unique()
        counts = counts.reindex(all_bins, fill_value=0)
        series = [
            {"time_bin": ts.strftime(TIME_FMT_DATE), "count": int(c)}
            for ts, c in counts.items()
        ]
        trends_over_time.append({"term": h, "timeline": series})

    return {
        "hashtags": hashtags_records,
        "mentions": mentions_records,
        "top_words": words_records,
        "phrases": phrases_records,
        "categories": cat_records,
        "media_types": media_records,
        "traffic_sources": traffic_records,
        "heatmap": heat_records,
        "trends_over_time": trends_over_time,
    }


# ===========================================================================
# PART 3 — Propagation (engagement & reach)
# ===========================================================================

def propagation_analysis(df):
    total_posts = len(df)
    total_reach = int(df["reach"].sum())
    total_impressions = int(df["impressions"].sum())
    total_likes = int(df["likes"].sum())
    total_comments = int(df["comments"].sum())
    total_shares = int(df["shares"].sum())
    total_saves = int(df["saves"].sum())
    total_followers_gained = int(df["followers_gained"].sum())

    # 1. Top posts by reach
    top_reach = df.sort_values("reach", ascending=False).head(20)
    top_reach_records = [
        {
            "post_id": str(r["post_id"]),
            "account_id": int(r["account_id"]),
            "account_type": r["account_type"],
            "media_type": r["media_type"],
            "content_category": r["content_category"],
            "caption": r["caption"],
            "reach": int(r["reach"]),
            "impressions": int(r["impressions"]),
            "likes": int(r["likes"]),
            "comments": int(r["comments"]),
            "shares": int(r["shares"]),
            "saves": int(r["saves"]),
            "engagement_rate": float(r["engagement_rate"]),
            "post_date": r["post_date"].strftime(TIME_FMT_DATE),
        }
        for _, r in top_reach.iterrows()
    ]

    # 2. Top posts by engagement (likes + comments + shares + saves)
    df["engagement"] = (
        df["likes"] + df["comments"] + df["shares"] + df["saves"]
    )
    top_eng = df.sort_values("engagement", ascending=False).head(20)
    top_eng_records = [
        {
            "post_id": str(r["post_id"]),
            "account_id": int(r["account_id"]),
            "account_type": r["account_type"],
            "media_type": r["media_type"],
            "content_category": r["content_category"],
            "caption": r["caption"],
            "engagement": int(r["engagement"]),
            "likes": int(r["likes"]),
            "comments": int(r["comments"]),
            "shares": int(r["shares"]),
            "saves": int(r["saves"]),
            "engagement_rate": float(r["engagement_rate"]),
            "post_date": r["post_date"].strftime(TIME_FMT_DATE),
        }
        for _, r in top_eng.iterrows()
    ]

    # 3. Top accounts by total engagement
    by_account = df.groupby(["account_id", "account_type"]).agg(
        total_posts=("post_id", "count"),
        total_reach=("reach", "sum"),
        total_likes=("likes", "sum"),
        total_comments=("comments", "sum"),
        total_shares=("shares", "sum"),
        total_saves=("saves", "sum"),
        avg_engagement_rate=("engagement_rate", "mean"),
        followers=("follower_count", "max"),
    ).sort_values("total_reach", ascending=False).head(20).reset_index()
    by_account_records = [
        {
            "account_id": int(r["account_id"]),
            "account_type": r["account_type"],
            "total_posts": int(r["total_posts"]),
            "total_reach": int(r["total_reach"]),
            "total_likes": int(r["total_likes"]),
            "total_comments": int(r["total_comments"]),
            "total_shares": int(r["total_shares"]),
            "total_saves": int(r["total_saves"]),
            "avg_engagement_rate": round(float(r["avg_engagement_rate"]), 4),
            "followers": int(r["followers"]),
        }
        for _, r in by_account.iterrows()
    ]

    # 4. Engagement timeline (totals per day)
    daily = df.groupby("time_bin").agg(
        posts=("post_id", "count"),
        reach=("reach", "sum"),
        impressions=("impressions", "sum"),
        likes=("likes", "sum"),
        comments=("comments", "sum"),
        shares=("shares", "sum"),
        saves=("saves", "sum"),
    ).fillna(0).astype(int).sort_index()

    timeline_records = [
        {
            "time_bin": ts.strftime(TIME_FMT_DATE),
            "posts": int(row.posts),
            "reach": int(row.reach),
            "impressions": int(row.impressions),
            "likes": int(row.likes),
            "comments": int(row.comments),
            "shares": int(row.shares),
            "saves": int(row.saves),
        }
        for ts, row in daily.iterrows()
    ]

    # 5. Media-type propagation breakdown
    media_breakdown = df.groupby("media_type").agg(
        posts=("post_id", "count"),
        avg_reach=("reach", "mean"),
        avg_engagement_rate=("engagement_rate", "mean"),
        total_shares=("shares", "sum"),
    ).reset_index()
    media_records = [
        {
            "media_type": r["media_type"],
            "posts": int(r["posts"]),
            "avg_reach": round(float(r["avg_reach"]), 1),
            "avg_engagement_rate": round(float(r["avg_engagement_rate"]), 4),
            "total_shares": int(r["total_shares"]),
        }
        for _, r in media_breakdown.iterrows()
    ]

    # 6. Risk scoring (mirrors notebook: 0.30*neg + 0.25*share + 0.25*reach
    #    + 0.20*engagement, normalized 0-100)
    df = df.copy()
    df["negative_score"] = 0.0  # placeholder; filled in sentiment_analysis
    df["share_score"] = df["shares"] / max(df["shares"].max(), 1)
    df["reach_score"] = df["reach"] / max(df["reach"].max(), 1)
    df["engagement_score"] = df["engagement_rate"] / max(df["engagement_rate"].max(), 1)
    df["risk_score"] = (
        0.30 * df["negative_score"]
        + 0.25 * df["share_score"]
        + 0.25 * df["reach_score"]
        + 0.20 * df["engagement_score"]
    ) * 100

    def _risk_level(score):
        if score >= 70:
            return "High"
        if score >= 40:
            return "Medium"
        return "Low"

    df["risk_level"] = df["risk_score"].apply(_risk_level)
    risk_dist = df["risk_level"].value_counts()
    risk_distribution = [
        {"risk_level": str(k), "count": int(v)} for k, v in risk_dist.items()
    ]

    summary = {
        "total_posts": total_posts,
        "total_reach": total_reach,
        "total_impressions": total_impressions,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "total_shares": total_shares,
        "total_saves": total_saves,
        "total_followers_gained": total_followers_gained,
        "avg_engagement_rate": round(float(df["engagement_rate"].mean()), 4),
        "top_media_type_by_reach": (
            str(media_breakdown.sort_values("avg_reach", ascending=False).iloc[0]["media_type"])
            if len(media_breakdown) else None
        ),
    }

    return {
        "summary": summary,
        "top_posts_by_reach": top_reach_records,
        "top_posts_by_engagement": top_eng_records,
        "top_accounts_by_reach": by_account_records,
        "propagation_timeline": timeline_records,
        "media_type_breakdown": media_records,
        "risk_distribution": risk_distribution,
    }


# ===========================================================================
# PART 4 — Sentiment Analysis (VADER, same as the notebooks)
# ===========================================================================

def _score_vader(analyzer, text):
    if not isinstance(text, str):
        text = "" if text is None or pd.isna(text) else str(text)
    return analyzer.polarity_scores(text)["compound"]


def sentiment_analysis(df):
    analyzer = SentimentIntensityAnalyzer()

    captions = df["caption"].fillna("").astype(str)
    scores = captions.apply(lambda t: _score_vader(analyzer, t))

    def _label(s):
        if s >= 0.05:
            return "Positive"
        if s <= -0.05:
            return "Negative"
        return "Neutral"

    df = df.copy()
    df["sentiment_score"] = scores
    df["pred_sentiment"] = scores.apply(_label)

    # 1. Distribution
    dist = df["pred_sentiment"].value_counts()
    counts = {s: int(dist.get(s, 0)) for s in SENTIMENTS}
    total = int(sum(counts.values()))
    distribution = {
        "counts": counts,
        "percentages": {
            s: round(100 * counts[s] / total, 2) for s in SENTIMENTS
        },
        "total": total,
    }

    # 2. Sentiment over time
    by_bin = df.groupby("time_bin")["pred_sentiment"]
    sentiment_time = []
    for ts, series in by_bin:
        vc = series.value_counts()
        rec = {"time_bin": ts.strftime(TIME_FMT_DATE)}
        for s in SENTIMENTS:
            rec[s] = int(vc.get(s, 0))
        n = int(series.size)
        for s in SENTIMENTS:
            rec[f"{s.lower()}_percentage"] = round(100 * rec[s] / n, 2) if n else 0.0
        sentiment_time.append(rec)
    sentiment_time.sort(key=lambda r: r["time_bin"])

    # 3. Sentiment trend (mean compound score per bin, mapped per class)
    trend = []
    for ts, sub in df.groupby("time_bin"):
        mean_score = float(sub["sentiment_score"].mean())
        rec = {
            "time_bin": ts.strftime(TIME_FMT_DATE),
            "mean_compound": round(mean_score, 4),
            "Positive": round(max(mean_score, 0), 4),
            "Negative": round(max(-mean_score, 0), 4),
            "Neutral": round(1 - abs(mean_score), 4),
        }
        trend.append(rec)
    trend.sort(key=lambda r: r["time_bin"])

    # 4. Combined: activity + sentiment per day
    combined = []
    for ts, series in by_bin:
        vc = series.value_counts()
        n = int(series.size)
        rec = {
            "time_bin": ts.strftime(TIME_FMT_DATE),
            "total_posts": n,
        }
        for s in SENTIMENTS:
            rec[s] = int(vc.get(s, 0))
            rec[f"{s.lower()}_percentage"] = (
                round(100 * rec[s] / n, 2) if n else 0.0
            )
        combined.append(rec)
    combined.sort(key=lambda r: r["time_bin"])

    # 5. Sentiment ↔ engagement (mean engagement rate per sentiment bucket)
    sent_engage = df.groupby("pred_sentiment").agg(
        posts=("post_id", "count"),
        avg_likes=("likes", "mean"),
        avg_comments=("comments", "mean"),
        avg_shares=("shares", "mean"),
        avg_reach=("reach", "mean"),
        avg_engagement_rate=("engagement_rate", "mean"),
    ).reindex(SENTIMENTS, fill_value=0).reset_index()
    sent_engage_records = [
        {
            "sentiment": r["pred_sentiment"],
            "posts": int(r["posts"]),
            "avg_likes": round(float(r["avg_likes"]), 2),
            "avg_comments": round(float(r["avg_comments"]), 2),
            "avg_shares": round(float(r["avg_shares"]), 2),
            "avg_reach": round(float(r["avg_reach"]), 2),
            "avg_engagement_rate": round(float(r["avg_engagement_rate"]), 4),
        }
        for _, r in sent_engage.iterrows()
    ]

    return {
        "distribution": distribution,
        "sentiment_over_time": sentiment_time,
        "sentiment_trend": trend,
        "sentiment_activity": combined,
        "sentiment_engagement": sent_engage_records,
        "note": (
            "Instagram sentiment is VADER-predicted from caption text. The "
            "captions are synthetic (Instagram_with_balanced_captions.csv); "
            "the score is a polarity proxy, not ground truth."
        ),
    }


# ===========================================================================
# PART 5 — Engagement deep-dive (mirrors the risk/funnel work in the notebooks)
# ===========================================================================

def engagement_analysis(df):
    # Performance bucket distribution
    bucket = df["performance_bucket_label"].fillna("unknown").value_counts()
    bucket_records = [
        {"bucket": str(b), "count": int(n)} for b, n in bucket.items()
    ]

    # Hour-of-day distribution
    hourly = df.groupby("post_hour").size()
    hour_records = [
        {"hour": int(h), "posts": int(n)} for h, n in hourly.sort_index().items()
    ]

    # Day-of-week distribution
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday",
                  "Friday", "Saturday", "Sunday"]
    dow = df["day_of_week"].value_counts().reindex(days_order, fill_value=0)
    dow_records = [
        {"day": d, "posts": int(n)} for d, n in dow.items()
    ]

    # Account type distribution
    acct = df["account_type"].fillna("unknown").value_counts()
    acct_records = [
        {"account_type": a, "count": int(n)} for a, n in acct.items()
    ]

    # Has CTA conversion (avg engagement_rate with vs without CTA)
    cta = df.groupby("has_call_to_action").agg(
        posts=("post_id", "count"),
        avg_engagement_rate=("engagement_rate", "mean"),
        avg_reach=("reach", "mean"),
    ).reset_index()
    cta_records = [
        {
            "has_call_to_action": int(r["has_call_to_action"]),
            "posts": int(r["posts"]),
            "avg_engagement_rate": round(float(r["avg_engagement_rate"]), 4),
            "avg_reach": round(float(r["avg_reach"]), 1),
        }
        for _, r in cta.iterrows()
    ]

    return {
        "performance_buckets": bucket_records,
        "hourly_distribution": hour_records,
        "day_of_week_distribution": dow_records,
        "account_type_distribution": acct_records,
        "cta_performance": cta_records,
    }


# ===========================================================================
# Orchestration
# ===========================================================================

def run_all():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_data()

    print("Instagram Timeline...")
    timeline = timeline_analysis(df)
    print("Instagram Trends...")
    trends = trend_analysis(df)
    print("Instagram Propagation...")
    propagation = propagation_analysis(df)
    print("Instagram Sentiment (VADER)...")
    sentiment = sentiment_analysis(df)
    print("Instagram Engagement deep-dive...")
    engagement = engagement_analysis(df)

    outputs = {
        "instagram_timeline.json": timeline,
        "instagram_trends.json": trends,
        "instagram_propagation.json": propagation,
        "instagram_sentiment.json": sentiment,
        "instagram_engagement.json": engagement,
    }
    for name, data in outputs.items():
        path = OUTPUT_DIR / name
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        print("Wrote", path)

    # Instagram-specific limitations note
    limits = {
        "captions_are_synthetic": True,
        "sentiment_is_vader_predicted": True,
        "limited_time_window": True,
        "geo_data_not_available": True,
        "notes": [
            "Instagram captions are synthetic (generated for engagement "
            "simulation); sentiment is VADER-predicted and is a polarity "
            "proxy, not ground truth.",
            "The dataset spans a sampled time window, not all of Instagram.",
            "Reach, impressions and engagement_rate are taken from the "
            "dataset as-is and reflect the synthetic captions.",
            "Propagation metrics describe observable engagement (likes, "
            "comments, shares, saves, reach) — not a true follower graph.",
            "Hashtag/mention trends are derived from the synthetic caption text.",
            "Trends reflect this dataset and time period, not Instagram as a whole.",
        ],
    }
    with open(OUTPUT_DIR / "instagram_limitations.json", "w", encoding="utf-8") as f:
        json.dump(limits, f, ensure_ascii=False, indent=2)
    print("Wrote", OUTPUT_DIR / "instagram_limitations.json")


if __name__ == "__main__":
    run_all()