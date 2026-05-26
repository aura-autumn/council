# ⚡ Council · Prototype 02 — Relevance Engine

Part of the [Council](../README.md) open-source intelligence platform.

**This prototype proves:** Council's Feed Ranking system — the ability to build a personalised user interest profile, encode it as a weighted vector, and score a live article feed via cosine similarity. The result: a ranked intelligence feed that improves with every interaction.

---

## What It Does

1. **Onboarding Quiz** — Set interest weights across 6 categories (Technology, Finance, Geopolitics, Science, Society, Policy). Each topic gets a weight from 0→1.

2. **Live Topic Search** — Enter any query (or tap a quick-scan button). Council fetches up to 60 live articles from Indian and global sources.

3. **Relevance Scoring** — Each article is encoded as a sparse interest vector (via keyword heuristics) and compared to your profile vector using cosine similarity. Freshness and credibility signals boost the final score.

4. **Ranked Feed** — Articles sorted by relevance, badged HIGH / MED / LOW / NOISE, with matched topics shown.

5. **Feedback Loop** — Read / Save / Skip / Dislike buttons nudge your interest weights, improving future scores.

6. **Analytics** — Score distribution, topic frequency, relevance×credibility scatter, interest heatmap, decay curve.

---

## Quickstart

```bash
# 1. Clone
git clone https://github.com/aura-autumn/council.git
cd council/phase-0-intelligence-prototypes/02-relevance-engine

# 2. Install
pip install -r requirements.txt

# 3. Set your NewsAPI key (free at newsapi.org)
cp .env.example .env
# Edit .env → NEWSAPI_KEY=your_key

# 4. Run
streamlit run app.py
```

Profile weights are persisted in `user_profile.json` (auto-created on first save).

---

## How It Works

```
Onboarding quiz
    ↓
user_profile.py  →  UserProfile (interests dict → normalised weight vector)
    ↓
fetcher.py       →  NewsAPI /everything + source metadata enrichment
    ↓
scorer.py        →  Stage 1: keyword → article interest vector (sparse)
                    Stage 2: cosine_similarity(profile_vec, article_vec)
                    Stage 3: freshness + credibility boost
                    → sorted ranked feed
    ↓
charts.py        →  Plotly cyberpunk visualisations
    ↓
app.py           →  Streamlit dashboard (onboarding + feed + analytics)
```

### Scoring Pipeline

```
relevance = (0.80 × cosine_sim) + (0.10 × freshness) + (0.10 × credibility)
          + (0.15 × query_alignment)   ← additive, only when query given
```

All values are clipped to [0, 1].

### Interest Vector

- **Profile vector** — dense `(n_interests,)` array of user weights, L2-normalised.
- **Article vector** — sparse `(n_interests,)` array where each dimension counts keyword hits for that interest (capped at 1.0).
- **Cosine similarity** — dot product of normalised vectors. Range: 0 (no overlap) → 1 (perfect match).

This is a direct structural analogue of the production system, which replaces keyword heuristics with sentence-transformer embeddings. The vector shape and scoring formula are identical.

---

## Connection to Full Council System

| Prototype Component | Production Component |
|---------------------|----------------------|
| `user_profile.py` | `backend/models/user.py` + `backend/services/profiles.py` |
| `fetcher.py` | `backend/services/ingestion.py` |
| `scorer.py` (cosine stage) | `backend/graphs/ranker_agent.py` |
| `scorer.py` (keyword vectors) | Replaced by `text-embedding-3-small` in prod |
| Feedback loop | `backend/services/feedback.py` → profile update queue |
| Charts | Frontend holographic panel: "Feed View" |

---

## Limitations & Honest Notes

- **Keyword-based article vectors** — production replaces these with `text-embedding-3-small`. Keyword matching misses semantic similarity (e.g. "LLM" won't match the "machine learning" interest unless the keyword list includes it).
- **Static source bias/credibility registry** — same limitation as prototype 01. Production uses dynamic scoring.
- **NewsAPI free tier** — 100 req/day, 30-day history. Upgrade to Developer plan for production volume.
- **Profile persistence is local** — `user_profile.json` lives on disk. Production stores profiles in PostgreSQL.

---

## Stack

`Python` · `Streamlit` · `scikit-learn (TF-IDF + cosine_similarity)` · `NumPy` · `Plotly` · `NewsAPI`
