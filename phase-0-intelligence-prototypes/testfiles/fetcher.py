"""
council/phase-0/01-bias-detector
fetcher.py — Fetches articles from NewsAPI and enriches with source metadata.
"""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Source bias metadata — manually curated, transparent to user
# Scale: -1.0 (far left) to +1.0 (far right), 0 = center
# Credibility: 0.0 to 1.0
SOURCE_METADATA = {
    # Indian sources
    "the-hindu": {"label": "The Hindu", "bias": -0.2, "credibility": 0.88, "region": "India"},
    "the-times-of-india": {"label": "Times of India", "bias": 0.1, "credibility": 0.75, "region": "India"},
    "ndtv": {"label": "NDTV", "bias": -0.1, "credibility": 0.80, "region": "India"},
    "india-today": {"label": "India Today", "bias": 0.0, "credibility": 0.78, "region": "India"},
    "the-indian-express": {"label": "Indian Express", "bias": -0.15, "credibility": 0.85, "region": "India"},
    "hindustan-times": {"label": "Hindustan Times", "bias": 0.05, "credibility": 0.76, "region": "India"},
    "wion": {"label": "WION", "bias": 0.15, "credibility": 0.70, "region": "India"},
    # Global sources
    "bbc-news": {"label": "BBC News", "bias": -0.1, "credibility": 0.90, "region": "Global"},
    "reuters": {"label": "Reuters", "bias": 0.0, "credibility": 0.95, "region": "Global"},
    "al-jazeera-english": {"label": "Al Jazeera", "bias": -0.2, "credibility": 0.82, "region": "Global"},
    "the-guardian": {"label": "The Guardian", "bias": -0.35, "credibility": 0.85, "region": "Global"},
    "fox-news": {"label": "Fox News", "bias": 0.55, "credibility": 0.60, "region": "Global"},
    "cnn": {"label": "CNN", "bias": -0.25, "credibility": 0.72, "region": "Global"},
    "associated-press": {"label": "AP News", "bias": 0.0, "credibility": 0.94, "region": "Global"},
    "bloomberg": {"label": "Bloomberg", "bias": 0.1, "credibility": 0.88, "region": "Global"},
    "the-washington-post": {"label": "Washington Post", "bias": -0.3, "credibility": 0.83, "region": "Global"},
    "the-wall-street-journal": {"label": "Wall Street Journal", "bias": 0.2, "credibility": 0.87, "region": "Global"},
}

BIAS_LABEL_MAP = {
    (-1.0, -0.4): "Far Left",
    (-0.4, -0.15): "Left-Leaning",
    (-0.15, 0.15): "Center",
    (0.15, 0.4): "Right-Leaning",
    (0.4, 1.0): "Far Right",
}


def get_bias_label(score: float) -> str:
    for (lo, hi), label in BIAS_LABEL_MAP.items():
        if lo <= score < hi:
            return label
    return "Far Right" if score >= 0.4 else "Far Left"


def fetch_articles(topic: str, days_back: int = 3, max_articles: int = 40) -> list[dict]:
    """
    Fetch articles for a topic from NewsAPI.
    Returns a list of enriched article dicts.
    """
    api_key = os.getenv("NEWSAPI_KEY")
    if not api_key:
        raise ValueError("NEWSAPI_KEY not set in .env")

    from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": topic,
        "from": from_date,
        "sortBy": "relevancy",
        "language": "en",
        "pageSize": max_articles,
        "apiKey": api_key,
    }

    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    articles = []
    for art in data.get("articles", []):
        source_id = art.get("source", {}).get("id") or ""
        source_name = art.get("source", {}).get("name", "Unknown")

        meta = SOURCE_METADATA.get(source_id, {
            "label": source_name,
            "bias": None,
            "credibility": None,
            "region": "Unknown",
        })

        articles.append({
            "title": art.get("title", ""),
            "description": art.get("description", "") or "",
            "content": art.get("content", "") or "",
            "url": art.get("url", ""),
            "published_at": art.get("publishedAt", ""),
            "source_id": source_id,
            "source_name": meta["label"],
            "bias_score": meta["bias"],
            "bias_label": get_bias_label(meta["bias"]) if meta["bias"] is not None else "Unknown",
            "credibility": meta["credibility"],
            "region": meta["region"],
        })

    return articles
