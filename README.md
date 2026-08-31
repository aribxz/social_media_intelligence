# SMI — Social Media Intelligence

> **AI-Based Social Media Analytics & Threat Risk Assessment** · SIH 2026 Prototype — IMSEC

Understand the conversation. Turn raw social noise into clear, measurable signal.

[![SIH 2026](https://img.shields.io/badge/SIH-2026-purple)](Documentation/SIH_Social_Media_Analytics_Consolidated_Meetings.pdf)
[![Prototype](https://img.shields.io/badge/status-prototype%20complete-8b5cf6)](#)
[![Python](https://img.shields.io/badge/python-3.14-3776AB)](#)
[![Flask](https://img.shields.io/badge/flask-%23000.svg-000?logo=flask&logoColor=white)](#)
[![Chart.js](https://img.shields.io/badge/chart.js-FF6384?logo=chartdotjs&logoColor=white)](#)

---

## Overview

SMI is a **lean SIH prototype** that proves an AI-driven social-media analytics engine can be built, evaluated, and communicated in one internal round — without prematurely scaling to a full streaming platform.

It runs two distinct analytical streams:

| Stream | Corpus | What it proves |
| :--- | :--- | :--- |
| **Twitter** | 15,000 tweets · 81-min window (Avengers: Endgame) | Timeline + Trends + Propagation + **supervised sentiment** |
| **Instagram** | 29,999 posts · 23 signals · 366-day window | Timing + Category + Media + Reach + Engagement (+ VADER sentiment on synthetic captions) |

Both streams converge on a **dark + purple dashboard** (Chart.js, vanilla JS) served locally by **Flask**. A thin **risk-prioritization heuristic** combines sentiment + propagation + reach + engagement into a 0–100 triage score — explicitly **not** a threat verdict; every high score routes to human review.

📄 **Full documentation:** [`DOCUMENTATION.md`](DOCUMENTATION.md) — 22 sections covering architecture, datasets, ML, API, meetings, and limitations.

---

## Quick Demo

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  —  source .venv/bin/activate on macOS/Linux
pip install flask pandas scikit-learn joblib vaderSentiment

python Backend/train_sentiment.py        # one-off: TF-IDF + LR → Backend/models/sentiment_model.joblib
python Backend/analytics.py              # → timeline/trends/propagation/sentiment.json
python Backend/instagram_analytics.py    # → instagram_*.json

python Backend/app.py                    # http://127.0.0.1:5000
```

Open **http://127.0.0.1:5000** — landing → choose a platform → hub → detail (charts) → about. Or double-click `Frontend/index.html` (still needs the Flask backend running).

For all setup, verification, and regeneration details see [`DOCUMENTATION.md` §16](DOCUMENTATION.md#16-getting-started).

---

## Features

### Four (+one) Analytical Pillars

| Pillar | Twitter | Instagram | Dashboard |
| :--- | :--- | :--- | :--- |
| **Timeline** | 5-min bins, peak volume, retweet vs original | Daily bins by media_type, peak date | Volume lines + stacked bars |
| **Trends** | Hashtags, mentions, words, bigrams, sparkline per term | Same + categories, media, traffic sources, DOW×hour heatmap | Horizontal bars, phrase list, multi-line |
| **Propagation** | Retweet ratio, top amplified tweets, repeated-content table | Reach funnel, top posts/accounts, media breakdown | Ratio donuts, stacked timeline, ranked tables |
| **Sentiment** | VADER baseline **and** TF-IDF + Logistic Regression (inference → distribution + trend) | VADER on captions (distribution + sentiment↔engagement cross) | Donuts, stacked area, confidence trend |
| **Engagement** | *(within propagation)* | Performance buckets, hourly/DOW, CTA lift | Heatmap, distribution bars |

### At a Glance

- **90% retweets** surfaced in the Twitter window — conversation is amplification-driven.
- **98.74% sentiment accuracy** on 398 genuinely unseen tweets (52% train-test overlap explicitly removed).
- **Triage risk score:** `Risk = (0.30·Negative + 0.25·Share + 0.25·Reach + 0.20·Eng) × 100` → Low 0–39 / Med 40–69 / **High 70–100**.

---

## Architecture

```
CSV datasets (Twitter / Instagram)
        │
        ├── Pandas cleaning & feature engineering (time_bin, tweet_type, text_clean, engagement_rate)
        │
        ├─── Twitter stream ────────────────────────────────────┐
        │      Timeline │ Trends │ Propagation │ Sentiment (VADER + ML)
        │
        ├─── Instagram stream ──────────────────────────────────┤
        │      Timeline │ Trends │ Propagation │ Sentiment (VADER) │ Engagement
        │
        └── Risk heuristic ──→ triage bands ──→ Human-in-the-Loop
                 │
        JSON outputs (Backend/Outputs/*.json)
                 │
        Flask API (port 5000)  +  static Frontend/
                 │
        Vanilla JS dashboard (Chart.js · Inter/Geist · prefers-reduced-motion)
```

*Deeper diagram + stage table:* [`DOCUMENTATION.md` §4](DOCUMENTATION.md#4-system-architecture).

---

## Project Structure

```
Social Media Intelligence (SMI)/
├── Backend/
│   ├── app.py                   # Flask — JSON API + static Frontend
│   ├── analytics.py             # Twitter: 4 pillars → JSON
│   ├── instagram_analytics.py   # Instagram: 5 engines → JSON
│   ├── train_sentiment.py       # Calls ML/Source/Twitter/Sentiment_analysis.py
│   └── Outputs/                 # timeline/trends/propagation/sentiment + instagram_*
├── Frontend/
│   ├── index.html               # Landing
│   ├── twitter.html / instagram.html   # Hubs
│   ├── *.html                   # 9 detail pages (4 Twitter + 5 Instagram) + about.html
│   └── assets/                  # styles.css · app.js
├── ML/Source/                   # Sentiment_analysis.py (single source of truth)
├── Data/
│   ├── Processed/               # Twitter_clean.csv (15K) · Instagram.csv (29,999) + ML corpora
│   └── Raw/
├── Documentation/               # 3 source PDFs
├── DOCUMENTATION.md             # Full docs (this repo's spec)
└── README.md                    # This file
```

---

## Tech Stack

| Layer | Stack |
| :--- | :--- |
| **Data / ML** | Python 3.14 · Pandas · scikit-learn (TfidfVectorizer, LogisticRegression C=10) · joblib · vaderSentiment |
| **Backend** | Flask 3 · CORS on `/api/*` |
| **Frontend** | Vanilla HTML/CSS/JS · Chart.js (CDN) · dark+purple tokens (`--bg #0a0a0f`, `--accent #8b5cf6`) |
| **Authorship** | 6-member IMSEC team — see [Team](#team) |

---

## API

Base: `http://127.0.0.1:5000`

| Path | Source | Page |
| :--- | :--- | :--- |
| `GET /api/timeline` | `timeline.json` | `timeline.html` |
| `GET /api/trends` | `trends.json` | `trend.html` |
| `GET /api/propagation` | `propagation.json` | `propagation.html` |
| `GET /api/sentiment` | `sentiment.json` | `sentiment.html` |
| `GET /api/limitations` | `limitations.json` | banner on every detail page |
| `GET /api/instagram/timeline` | `instagram_timeline.json` | `instagram_timeline.html` |
| `GET /api/instagram/trends` | `instagram_trends.json` | `instagram_trend.html` |
| `GET /api/instagram/propagation` | `instagram_propagation.json` | `instagram_propagation.html` |
| `GET /api/instagram/sentiment` | `instagram_sentiment.json` | `instagram_sentiment.html` |
| `GET /api/instagram/engagement` | `instagram_engagement.json` | `instagram_engagement.html` |
| `GET /api/health` | — | `{"status":"ok"}` |
| `GET /api` | — | full endpoint index |

Contract shapes + sample payloads: [`DOCUMENTATION.md` §11](DOCUMENTATION.md#11-backend--flask-api) and [`Backend/API_CONTRACT.md`](Backend/API_CONTRACT.md).

Regeneration: `python Backend/train_sentiment.py && python Backend/analytics.py && python Backend/instagram_analytics.py`

---

## Results Snapshot

| Corpus | Top Finding |
| :--- | :--- |
| **Twitter (VADER)** | All tweets 52.94% Pos / 38.42% Neu / 8.64% Neg · **originals** 14.48% Neg (higher neg concentration in originals) |
| **Twitter (ML inference)** | Neutral 60.81% · Positive 31.0% · Negative 8.19% on 15K — peak window 09:55 with 1,038 tweets |
| **Twitter propagation** | 90.01% retweets — most repeated `RT @HelloBoon: Man these #AvengersEndgame ads are everywhere` (1,456×) |
| **Twitter ML** | **98.74%** on 398 unseen tweets (5 contextual errors); initial 92.96% before tuning |
| **Instagram sentiment (VADER)** | Positive 46.01% · Negative 28.49% · Neutral 25.49% across 29,999 |
| **Instagram timing** | Best hours 03:00/08:00/02:00/17:00/20:00 & categories Music>Fitness>Fashion — all **small gaps** (combine, don't chase one factor) |
| **Risk signal** | Week-4 negative surge 35% vs ~28% baseline; share-gated queue at `quantile(0.90)` → example triaged post `shares 516 · reach 46,738 · eng 0.2398 · −0.8655` → **risk 76 = HIGH** |

Full tables & meeting-by-meeting records: [`DOCUMENTATION.md` §13–14](DOCUMENTATION.md#13-key-findings--results).

---

## Team

| Member | Role | Links |
| :--- | :--- | :--- |
| **Arib** | ML Engineer & Frontend Lead | [GitHub](https://github.com/aribxz) · [LinkedIn](https://linkedin.com/in/mohammad-arib-salim-14a055371) |
| **Kunal** | Team Lead & ML Engineer | [GitHub](https://github.com/kunal-1505) · [LinkedIn](https://www.linkedin.com/in/kunal-sharma-ba04b6432) |
| **Mansi** | Backend Engineer | [GitHub](https://github.com/Mansi155) · [LinkedIn](https://www.linkedin.com/in/mansi-chaudhary-1089243a9) |
| **Nikhil** | Creative Assistance & Frontend | [GitHub](https://github.com/Nik-code-alt) · [LinkedIn](https://www.linkedin.com/in/nikhil-gupta-8abb37431) |
| **Neeraj** | Documentation Lead | [GitHub](https://github.com/neerajbalodhi13-collab) · [LinkedIn](https://www.linkedin.com/in/neeraj-balodhi-52bb16431) |
| **Digvijay** | Documentation Lead | [GitHub](https://github.com/digvijaysinghrajputt) · [LinkedIn](https://www.linkedin.com/in/digvijay-singh-8b3544380) |

`Frontend/about.html` renders this team as an interactive graph — click a node to focus its card.

---

## Limitations

> This is a prototype. The broad caveats surface on every detail page via `/api/limitations`.

- Historical CSVs, not a live streaming pipeline.
- `Instagram.csv` has no raw caption text (VADER runs on synthetic captions — a polarity proxy).
- No complete account graph → network analysis is skeleton only.
- `performance_bucket_label` may leak if `engagement_rate` is used to predict it; likes/comments/shares/saves are post-outcome.
- The risk score is **heuristic (30/25/25/20 weights, hand-set)** — not a threat probability — and requires analyst review.

All caveats in [`DOCUMENTATION.md` §18](DOCUMENTATION.md#18-limitations--data-gaps).

---

## Roadmap

`Correlation Analysis → Feature Engineering → Validated ML → NLP on real captions → Full propagation & network → Unified explainable dashboard → Supervised threat model (expert labels + BERT/RoBERTa + RF/XGBoost + graph features).`

See [`DOCUMENTATION.md` §19](DOCUMENTATION.md#19-future-roadmap).

---

## Docs

- **Full spec:** [`DOCUMENTATION.md`](DOCUMENTATION.md) — 22 sections, includes the 27–30 Aug meeting log and the risk-prototype formula.
- **Source PDFs:** [`Documentation/`](Documentation/) — 3 files (8 + 3 + 19 pages).
- **API contract:** [`Backend/API_CONTRACT.md`](Backend/API_CONTRACT.md)
- **Frontend build prompt:** [`Frontend/BUILD_PROMPT.md`](Frontend/BUILD_PROMPT.md)

---

## License

Prototype for SIH internal evaluation — not licensed for reuse beyond the hackathon context. Ask the team before redistribution.

---

*SMI prototype — analytics served locally from Flask. Made by IMSEC Students.*
