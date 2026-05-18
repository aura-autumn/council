# ⚡ Council · Prototype 01 — News Bias & Contradiction Detector

Part of the [Council](../README.md) open-source intelligence platform.

**This prototype proves:** Council's Analyzer Agent — the system's ability to ingest multi-source coverage of a topic, detect political lean, surface sentiment divergence, and score how diverse and credible the information landscape is.

---

## What It Does

Enter any topic. Council fetches live news from up to 60 articles across Indian and global sources, then delivers:

- **Bias Distribution** — how coverage skews politically across the Left–Center–Right spectrum
- **Sentiment vs Bias Scatter** — are left-leaning sources more negative? Right-leaning more positive? See the actual data.
- **Contradiction Detection** — pairs of articles covering the *same story* with *opposing sentiment*, ranked by severity
- **Source Credibility Heatmap** — which outlets are most reliable for this topic
- **Diversity Score (0–100)** — a composite score measuring source variety, bias spread, regional mix, and credibility

## Demo

![Dashboard screenshot](docs/screenshot.png)

---

## Quickstart

```bash
# 1. Clone
git clone https://github.com/aura-autumn/council.git
cd council/phase-0-intelligence-prototypes/01-bias-detector

# 2. Install
pip install -r requirements.txt

# 3. Set your NewsAPI key (free at newsapi.org)
cp .env.example .env
# Edit .env → NEWSAPI_KEY=your_key

# 4. Run
streamlit run app.py
```

The first run downloads the DistilBERT sentiment model (~250MB). Subsequent runs are instant.

---

## How It Works

```
User enters topic
    ↓
fetcher.py  →  NewsAPI /everything endpoint
               + source metadata enrichment (bias score, credibility)
    ↓
analyzer.py →  DistilBERT sentiment scoring (CPU, offline after first download)
               TF-IDF cosine similarity for topic grouping
               Contradiction detection: similar topic + opposing sentiment
               Diversity score computation
    ↓
charts.py   →  Plotly visualizations (cyberpunk dark theme)
    ↓
app.py      →  Streamlit dashboard
```

### Contradiction Detection Logic

Two articles are flagged as contradictory if:
1. **Content similarity ≥ 0.35** (TF-IDF cosine) — they cover the same story
2. **Sentiment divergence ≥ threshold** (default 0.25) — they frame it very differently
3. **Different sources** — same outlet can't contradict itself here

Severity is rated:
- 🔴 **High** — divergence > 0.6
- 🟡 **Medium** — divergence 0.35–0.6
- 🔵 **Low** — divergence 0.25–0.35

### Bias Scoring

Source bias scores are manually curated from established media bias research (AllSides, Ad Fontes Media). Scale: -1.0 (far left) to +1.0 (far right). Sources not in the curated list are labeled "Unknown".

---

## Connection to Full Council System

In the production Council system, this prototype's logic maps directly to:

| Prototype Component | Production Component |
|---------------------|----------------------|
| `fetcher.py` | `backend/services/ingestion.py` |
| `analyzer.py` (sentiment) | `backend/graphs/analyzer_agent.py` |
| Contradiction detection | `backend/graphs/analyzer_agent.py` → contradiction node |
| Diversity score | `backend/services/rag.py` → source diversity metric |
| Charts | Frontend holographic panel: "Deep Analysis View" |

---

## Limitations & Honest Notes

- Bias scores are static and manually assigned — a production system would use dynamic, model-driven scoring
- Sentiment model (DistilBERT SST-2) is general-purpose, not news-specific — a fine-tuned model would perform better
- NewsAPI free tier: 100 requests/day, articles from last 30 days only
- Contradiction detection uses lexical similarity (TF-IDF), not semantic similarity — embedding-based detection is more accurate and is used in production

---

## Stack

`Python` · `Streamlit` · `HuggingFace Transformers (DistilBERT)` · `scikit-learn` · `Plotly` · `NewsAPI`
