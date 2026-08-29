# Frontend Build Prompt — SMI Dashboard

> **How to use this file:** This is a self-contained prompt for an AI agent or
> frontend developer. It describes (A) the design brief and (B) the exact
> backend structure / API contract the frontend must consume. Append any extra
> instructions (the "clause") below this block, then hand it to the builder.

---

## A. WHAT TO BUILD

A single-page-style web dashboard for the **Social Media Intelligence (SMI)**
prototype. It visualizes analytics served by an existing Flask backend.

### Design language (mandatory — keep 100% consistent)

- **Theme:** dark, near-black background with a purple accent. Minimalist,
  classy, "startup" aesthetic. No clutter, generous whitespace, restrained
  motion (subtle fades/hover only).
- **Palette (use as CSS variables):**
  - `--bg`: `#0a0a0f` (page background, near-black)
  - `--surface`: `#121019` (cards / panels)
  - `--surface-2`: `#171324`
  - `--border`: `#2a2440` (subtle purple-tinted borders)
  - `--accent`: `#8b5cf6` (violet)
  - `--accent-2`: `#a855f7` (lighter violet for gradients)
  - `--accent-soft`: `rgba(139,92,246,0.12)` (hover / fills)
  - `--text`: `#e7e5f0` (primary text)
  - `--text-dim`: `#9a93b3` (secondary text)
  - `--positive`: `#34d399`, `--neutral`: `#a855f7`, `--negative`: `#f87171`
    (used only for sentiment coloring)
- **Typography:** Inter (or Geist / system-ui fallback). One display weight
  (600/700) for headings, 400 for body. Letter-spacing slightly tight on
  headings.
- **Components:** rounded-2xl cards (`border-radius: 16px`), 1px
  `--border`, soft shadow, subtle gradient on hover. Buttons are pill or
  rounded with violet outline/glow on hover. No heavy shadows, no skeuomorphism.
  - **Charts:** Chart.js (via CDN). Use violet gradients for fills, thin grid
    lines in `--border`, tooltips styled to match dark theme. Keep charts
    uncluttered. Charts should animate in on load (Chart.js default ease-out
    is fine) and re-animate on data fetch.
  - **Motion & animation (make the UI feel alive, but tasteful):**
    - **Hover:** cards lift (`translateY(-4px)` + stronger violet glow /
      border brighten) with a 150–200ms ease; buttons get a violet glow /
      fill sweep on hover; nav links underline-grow in violet.
    - **Entrance / scroll reveal:** use an `IntersectionObserver` to slide
      + fade elements up (`translateY(16px)` → `0`, `opacity 0` → `1`,
      250–400ms ease) as they enter the viewport. Stagger cards
      (`transition-delay` ~60ms per item) for a cascading reveal.
    - **Page transitions:** a soft fade + slight upward slide when navigating
      between hub and detail pages (e.g., a `.page-enter` class applied on
      load, or a lightweight view swap). Avoid hard cuts.
    - **Hero:** the SMI logo / radial glow can have a slow, subtle pulse or
      float; keep it gentle (long duration, low opacity shift).
    - **Number counters:** KPI summary numbers should count up from 0 to
      their value on first reveal (requestAnimationFrame, ~800ms).
    - **Chart hovers:** tooltips already animate; ensure axes/grid fade in
      with the chart.
    - **Reduced motion:** wrap all of the above in
      `@media (prefers-reduced-motion: reduce)` to disable transforms /
      large motion for accessibility (keep simple fades only).
    - Keep durations short (150–400ms for interactions, 400–800ms for
      entrances) and easing consistent (`cubic-bezier(0.22,1,0.36,1)` or
      ease-out). No bouncing, no neon-flicker — classy, not flashy.

### Pages / navigation flow

1. **Landing (`index.html`)**
   - Centered **SMI wordmark / logo** at top: "Social Media Intelligence"
     set in a refined way (e.g., letterspaced uppercase "SMI" + light
     subtitle "Social Media Intelligence"). Optionally a minimal SVG mark
     (concentric purple arcs).
   - A short elegant tagline, e.g. *"Understand the conversation."*
   - Scroll down → a section that asks **"Choose a platform"** with two
     large choice cards / buttons:
     - **Instagram** — present but **disabled** ("Coming soon" overlay /
       muted, not clickable).
     - **Twitter** — active; clicking navigates to `twitter.html`.
   - Smooth scrolling; hero uses a faint radial purple glow behind the logo.

2. **Twitter hub (`twitter.html`)**
   - Header with "Twitter Analytics" and a back link to home.
   - A responsive grid of **four** option cards, each beautifully illustrated
     with an icon + title + one-line description + gradient hover:
     - **Propagation**
     - **Sentiment analysis**
     - **Timeline analysis**
     - **Trend**
   - Each card links to its detail page.

3. **Detail pages** (one per section): `propagation.html`, `sentiment.html`,
   `timeline.html`, `trend.html`
   - Consistent header (section title + back to Twitter hub).
   - Summary cards (KPIs) at top.
   - Charts built from the relevant endpoint (see Section B).
   - A small **limitations/disclaimer banner** (from `/api/limitations`)
     stating sentiment is model-predicted, retweets dominate, limited window,
     no geo. Keep it subtle but visible.

### Technical constraints

- **Stack:** plain HTML + CSS + vanilla JS (no framework / no build step).
  Chart.js via CDN (`https://cdn.jsdelivr.net/npm/chart.js`). This keeps it
  prototype-simple and matches the "analytics separate from app" philosophy.
- **Data:** fetch from the Flask API (default `http://127.0.0.1:5000`). Use
  relative-ish absolute base `http://127.0.0.1:5000`. Handle non-200 / 404
  gracefully (show a friendly "data not generated — run analytics.py" message).
- **Files to create** (all under `Frontend/`):
  - `index.html`
  - `twitter.html`
  - `propagation.html`, `sentiment.html`, `timeline.html`, `trend.html`
  - `assets/styles.css` (shared theme)
  - `assets/app.js` (shared helpers: fetch + theme + chart defaults) and/or
    small per-page scripts. Keep JS minimal and readable.
- **Consistency:** every page imports the same `assets/styles.css` and uses
  the same CSS variables, header component, and card style. Do not introduce
  per-page color drift.
- **Responsive:** works on laptop + tablet; cards wrap to a single column on
  narrow widths.
- **Accessibility:** semantic HTML, `aria-label` on icon buttons, sufficient
  contrast (the palette above meets this).

---

## B. BACKEND STRUCTURE & API CONTRACT (what the frontend must consume)

The backend already exists. **Do not modify it.** You only build the frontend
that reads these endpoints.

### Backend files (context only)

```
Backend/
  app.py                 # Flask server, serves JSON on port 5000
  analytics.py           # generates the JSON (already run)
  train_sentiment.py     # trains+persists the model (already run)
  models/sentiment_model.joblib
  Outputs/
      timeline.json
      trends.json
      propagation.json
      sentiment.json
      limitations.json
  API_CONTRACT.md        # full reference (same info as below)
```

### Endpoints (GET, return JSON)

Base URL: `http://127.0.0.1:5000`

| Path               | Use for page        | Shape summary |
|--------------------|---------------------|---------------|
| `/api/timeline`    | `timeline.html`     | summary + timeline[] + top_intervals[] + peak |
| `/api/trends`      | `trend.html`        | hashtags[] + mentions[] + top_words[] + phrases[] + trends_over_time[] |
| `/api/propagation` | `propagation.html`  | ratio + top_original_tweets[] + top_content_by_engagement[] + repeated_content[] + propagation_timeline[] + summary |
| `/api/sentiment`   | `sentiment.html`    | distribution + sentiment_over_time[] + sentiment_trend[] + sentiment_activity[] + note |
| `/api/limitations` | disclaimer banner   | booleans + notes[] |
| `/api/health`      | optional liveness   | `{"status":"ok"}` |

### Exact JSON shapes (render these fields)

**`/api/timeline`**
```json
{
  "summary": {
    "total_tweets": 15000, "total_originals": 1499, "total_retweets": 13501,
    "retweet_percentage": 90.01, "original_percentage": 9.99,
    "start_time": "2019-04-23 09:20", "end_time": "2019-04-23 10:40",
    "peak_time": "2019-04-23 09:55", "peak_volume": 1038
  },
  "timeline": [ { "time_bin": "2019-04-23 09:20", "total_tweets": 558, "original": 62, "retweet": 496 } ],
  "top_intervals": [ { "time_bin": "2019-04-23 09:55", "total_tweets": 1038 } ],
  "peak": { "peak_time_bin": "2019-04-23 09:55", "peak_tweet_count": 1038 }
}
```
Render: KPI cards (total / originals / retweets / peak). A line or area chart
of `timeline[].total_tweets` over `time_bin`. A stacked bar of `original` vs
`retweet` over `time_bin`.

**`/api/trends`**
```json
{
  "hashtags": [ { "hashtag": "#avengersendgame", "count": 13478 } ],
  "mentions": [ { "username": "@marvel", "count": 2023 } ],
  "top_words": [ { "word": "man", "count": 2184 } ],
  "phrases": [ { "phrase": "avengers endgame", "count": 8123 } ],
  "trends_over_time": [ { "term": "#avengersendgame", "timeline": [ { "time_bin": "...", "count": 20 } ] } ]
}
```
Render: horizontal bar charts for hashtags, mentions, top_words. A phrase list.
A multi-line "trend over time" chart from `trends_over_time[].timeline`.

**`/api/propagation`**
```json
{
  "ratio": { "total_originals": 1499, "total_retweets": 13501,
             "original_percentage": 9.99, "retweet_percentage": 90.01 },
  "top_original_tweets": [ { "tweet_id": 123, "user": "hmvtweets", "text": "...",
      "retweet_count": 318, "favorite_count": 5, "created": "2019-04-23 09:.." } ],
  "top_content_by_engagement": [ { "tweet_id": 123, "user": "...", "text": "...",
      "retweet_count": 318, "favorite_count": 5, "engagement": 323 } ],
  "repeated_content": [ { "content": "RT @HelloBoon: ...", "occurrence_count": 1456 } ],
  "propagation_timeline": [ { "time_bin": "...", "retweets": 496, "originals": 62, "total": 558 } ],
  "summary": { "total_retweets": 13501, "total_originals": 1499,
               "top_retweeted_user": "SahapunB", "most_repeated_content": "RT @HelloBoon: ..." }
}
```
Render: a donut for `ratio` (original vs retweet). A stacked bar of
`propagation_timeline` (originals vs retweets over time). Two tables:
top original tweets (user, text, retweet_count) and repeated content
(content, occurrence_count).

**`/api/sentiment`**
```json
{
  "distribution": {
    "counts": { "Positive": 4650, "Neutral": 9122, "Negative": 1228 },
    "percentages": { "Positive": 31.0, "Neutral": 60.81, "Negative": 8.19 },
    "total": 15000
  },
  "sentiment_over_time": [ { "time_bin": "...", "Positive": 186, "Neutral": 332, "Negative": 40,
      "positive_percentage": 33.33, "neutral_percentage": 59.5, "negative_percentage": 7.17 } ],
  "sentiment_trend": [ { "time_bin": "...", "Positive": 0.71, "Neutral": 0.88, "Negative": 0.42 } ],
  "sentiment_activity": [ { "time_bin": "...", "total_tweets": 558, "Positive": 186, "Neutral": 332, "Negative": 40,
      "positive_percentage": 33.33, "neutral_percentage": 59.5, "negative_percentage": 7.17 } ],
  "note": "Sentiment is model-predicted, not ground truth. ..."
}
```
Render: a donut for `distribution` (use `--positive/--neutral/--negative`
colors). A stacked area/line of `sentiment_over_time` over `time_bin`. An
optional line of `sentiment_trend` (model confidence, label as "model
confidence", not human certainty). **Always show `note` / limitations.**

**`/api/limitations`**
```json
{ "geo_analysis_not_meaningful": true, "retweets_dominate_dataset": true,
  "sentiment_is_model_predicted": true, "limited_time_window": true,
  "notes": [ "Sentiment is model-predicted, not ground truth.", "..." ] }
```
Render: a subtle banner/footer on every detail page.

---

## C. ACCEPTANCE CRITERIA

- Landing page shows the SMI logo/title, scrolls to a platform chooser;
  Instagram is visibly disabled, Twitter navigates to the hub.
- Twitter hub shows four consistent, attractive cards; each opens its detail page.
- Each detail page fetches its endpoint, shows KPI cards + charts, and the
  limitations banner. Theme is identical across all pages.
- **Motion is present and polished:** hover lifts/glows on all interactive
  elements; cards/sections slide + fade in on scroll (staggered); KPI numbers
  count up; page transitions are soft; charts animate in. All motion respects
  `prefers-reduced-motion`.
- No console errors; 404s show a friendly message.
- Visual style is dark + purple, minimal, classy, startup-like throughout.

---

<!-- Append your additional clause/instructions below this line. -->
