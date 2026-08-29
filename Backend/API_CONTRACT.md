# SMI Analytics API Contract

Backend for the Social Media Intelligence prototype. The analytics engine
(`analytics.py`) writes JSON into `Outputs/`; this Flask server (`app.py`)
exposes those files through stable GET endpoints. The frontend never runs
Pandas — it only consumes JSON.

Base URL (local dev): `http://127.0.0.1:5000`

## Endpoints

| Method | Path               | Source file        | Purpose                          |
|--------|--------------------|--------------------|----------------------------------|
| GET    | `/api/timeline`    | `timeline.json`    | Volume + original/retweet over time |
| GET    | `/api/trends`      | `trends.json`      | Hashtags, mentions, words, phrases, trends over time |
| GET    | `/api/propagation` | `propagation.json` | Original/retweet ratio, top content, repeated content |
| GET    | `/api/sentiment`   | `sentiment.json`   | Model-predicted sentiment (NOT ground truth) |
| GET    | `/api/limitations` | `limitations.json` | Known limitations / disclaimers |
| GET    | `/api/health`      | —                  | `{"status": "ok"}` |
| GET    | `/`                | —                  | Endpoint listing |

All responses are `application/json`. If an output file is missing the
endpoint returns `404`.

## How to regenerate the data

```bash
cd Backend
python train_sentiment.py   # one-off: creates models/sentiment_model.joblib
python analytics.py         # writes the 5 JSON files into Outputs/
python app.py               # starts the server on port 5000
```

---

## `/api/timeline`

```json
{
  "summary": {
    "total_tweets": 15000,
    "total_originals": 1499,
    "total_retweets": 13501,
    "retweet_percentage": 90.01,
    "original_percentage": 9.99,
    "start_time": "2019-04-23 09:20",
    "end_time": "2019-04-23 10:40",
    "peak_time": "2019-04-23 09:55",
    "peak_volume": 1038
  },
  "timeline": [
    { "time_bin": "2019-04-23 09:20", "total_tweets": 558, "original": 62, "retweet": 496 }
  ],
  "top_intervals": [ { "time_bin": "...", "total_tweets": 1038 } ],
  "peak": { "peak_time_bin": "2019-04-23 09:55", "peak_tweet_count": 1038 }
}
```

## `/api/trends`

```json
{
  "hashtags": [ { "hashtag": "#avengersendgame", "count": 13478 } ],
  "mentions": [ { "username": "@marvel", "count": 2023 } ],
  "top_words": [ { "word": "man", "count": 2184 } ],
  "phrases": [ { "phrase": "avengers endgame", "count": 8123 } ],
  "trends_over_time": [
    { "term": "#avengersendgame", "timeline": [ { "time_bin": "...", "count": 20 } ] }
  ]
}
```

## `/api/propagation`

```json
{
  "ratio": { "total_originals": 1499, "total_retweets": 13501,
             "original_percentage": 9.99, "retweet_percentage": 90.01 },
  "top_original_tweets": [
    { "tweet_id": 123, "user": "hmvtweets", "text": "...",
      "retweet_count": 318, "favorite_count": 5, "created": "2019-04-23 09:.." }
  ],
  "top_content_by_engagement": [
    { "tweet_id": 123, "user": "...", "text": "...",
      "retweet_count": 318, "favorite_count": 5, "engagement": 323 }
  ],
  "repeated_content": [ { "content": "RT @HelloBoon: ...", "occurrence_count": 1456 } ],
  "propagation_timeline": [
    { "time_bin": "...", "retweets": 496, "originals": 62, "total": 558 }
  ],
  "summary": {
    "total_retweets": 13501, "total_originals": 1499,
    "retweet_percentage": 90.01,
    "top_retweeted_content": "...", "top_retweeted_user": "SahapunB",
    "most_repeated_content": "RT @HelloBoon: ..."
  }
}
```

## `/api/sentiment`

```json
{
  "distribution": {
    "counts": { "Positive": 4650, "Neutral": 9122, "Negative": 1228 },
    "percentages": { "Positive": 31.0, "Neutral": 60.81, "Negative": 8.19 },
    "total": 15000
  },
  "sentiment_over_time": [
    { "time_bin": "2019-04-23 09:20", "Positive": 186, "Neutral": 332, "Negative": 40,
      "positive_percentage": 33.33, "neutral_percentage": 59.5, "negative_percentage": 7.17 }
  ],
  "sentiment_trend": [
    { "time_bin": "...", "Positive": 0.71, "Neutral": 0.88, "Negative": 0.42 }
  ],
  "sentiment_activity": [
    { "time_bin": "...", "total_tweets": 558, "Positive": 186, "Neutral": 332, "Negative": 40,
      "positive_percentage": 33.33, "neutral_percentage": 59.5, "negative_percentage": 7.17 }
  ],
  "note": "Sentiment is model-predicted, not ground truth. ..."
}
```

> `sentiment_trend` probabilities are model confidence (0–1), NOT a measure of
> human certainty. Always label predicted sentiment as model-generated.

## `/api/limitations`

```json
{
  "geo_analysis_not_meaningful": true,
  "retweets_dominate_dataset": true,
  "sentiment_is_model_predicted": true,
  "limited_time_window": true,
  "notes": [ "Sentiment is model-predicted, not ground truth.", "..." ]
}
```

---

## Dashboard sections → endpoints

| Section       | Endpoint(s)                                  |
|---------------|----------------------------------------------|
| Sentiment     | `/api/sentiment`                             |
| Timeline      | `/api/timeline`                              |
| Trends        | `/api/trends`                                |
| Propagation   | `/api/propagation`                           |
| Disclaimers   | `/api/limitations`                           |
