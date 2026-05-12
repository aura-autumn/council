"""
council/phase-0/01-bias-detector
analyzer.py — Sentiment analysis, stance scoring, and contradiction detection.

Uses a lightweight HuggingFace model for sentiment so this runs fully offline
after first download — no OpenAI key required.
"""

from __future__ import annotations
import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer


# ──────────────────────────────────────────────
# Sentiment scoring (zero-shot, CPU-friendly)
# ──────────────────────────────────────────────

_pipeline = None  # lazy-load so Streamlit startup stays fast


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        from transformers import pipeline
        # distilbert is small (~250 MB) and fast on CPU
        _pipeline = pipeline(
            "text-classification",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            truncation=True,
            max_length=512,
        )
    return _pipeline


def score_sentiment(text: str) -> float:
    """
    Returns a sentiment score: -1.0 (very negative) to +1.0 (very positive).
    """
    if not text or not text.strip():
        return 0.0
    pipe = _get_pipeline()
    result = pipe(text[:512])[0]
    score = result["score"]
    return score if result["label"] == "POSITIVE" else -score


def analyze_articles(articles: list[dict]) -> list[dict]:
    """
    Enrich each article with:
    - sentiment_score: float [-1, 1]
    - sentiment_label: str
    - text_for_analysis: combined title + description
    """
    enriched = []
    for art in articles:
        text = f"{art['title']}. {art['description']}"
        sentiment = score_sentiment(text)
        enriched.append({
            **art,
            "sentiment_score": sentiment,
            "sentiment_label": (
                "Positive" if sentiment > 0.15
                else "Negative" if sentiment < -0.15
                else "Neutral"
            ),
            "text_for_analysis": text,
        })
    return enriched


# ──────────────────────────────────────────────
# Contradiction detection
# ──────────────────────────────────────────────

def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def detect_contradictions(articles: list[dict], threshold: float = 0.25) -> list[dict]:
    """
    Finds article pairs that:
    1. Cover similar content (high TF-IDF cosine similarity ≥ 0.35)
    2. Have opposing sentiment scores (difference ≥ threshold)

    Returns a list of contradiction dicts.
    """
    if len(articles) < 2:
        return []

    texts = [_clean(a["text_for_analysis"]) for a in articles]

    vectorizer = TfidfVectorizer(stop_words="english", max_features=500)
    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
    except ValueError:
        return []

    sim_matrix = cosine_similarity(tfidf_matrix)
    sentiments = np.array([a["sentiment_score"] for a in articles])

    contradictions = []
    seen = set()

    for i in range(len(articles)):
        for j in range(i + 1, len(articles)):
            pair_key = (i, j)
            if pair_key in seen:
                continue

            content_similar = sim_matrix[i, j] >= 0.35
            sentiment_diff = abs(sentiments[i] - sentiments[j])
            opposing_sentiment = sentiment_diff >= threshold

            # Skip same source
            same_source = articles[i]["source_name"] == articles[j]["source_name"]

            if content_similar and opposing_sentiment and not same_source:
                seen.add(pair_key)
                contradictions.append({
                    "article_a": {
                        "title": articles[i]["title"],
                        "source": articles[i]["source_name"],
                        "sentiment": articles[i]["sentiment_label"],
                        "sentiment_score": round(sentiments[i], 3),
                        "bias_label": articles[i]["bias_label"],
                        "url": articles[i]["url"],
                    },
                    "article_b": {
                        "title": articles[j]["title"],
                        "source": articles[j]["source_name"],
                        "sentiment": articles[j]["sentiment_label"],
                        "sentiment_score": round(sentiments[j], 3),
                        "bias_label": articles[j]["bias_label"],
                        "url": articles[j]["url"],
                    },
                    "content_similarity": round(float(sim_matrix[i, j]), 3),
                    "sentiment_divergence": round(float(sentiment_diff), 3),
                    "severity": (
                        "High" if sentiment_diff > 0.6
                        else "Medium" if sentiment_diff > 0.35
                        else "Low"
                    ),
                })

    # Sort by severity then divergence
    severity_order = {"High": 0, "Medium": 1, "Low": 2}
    contradictions.sort(
        key=lambda x: (severity_order[x["severity"]], -x["sentiment_divergence"])
    )

    return contradictions[:15]  # cap at 15 most significant


# ──────────────────────────────────────────────
# Diversity score
# ──────────────────────────────────────────────

def compute_diversity_score(articles: list[dict]) -> dict:
    """
    Computes a source diversity score (0–100) based on:
    - Number of unique sources
    - Spread of bias scores (std dev)
    - Mix of regions (India vs Global)
    - Credibility average
    """
    if not articles:
        return {"score": 0, "breakdown": {}}

    known = [a for a in articles if a["bias_score"] is not None]

    unique_sources = len(set(a["source_name"] for a in articles))
    source_score = min(unique_sources / 8, 1.0)  # normalise against 8 ideal sources

    bias_scores = [a["bias_score"] for a in known]
    bias_spread = float(np.std(bias_scores)) if bias_scores else 0.0
    bias_score = min(bias_spread / 0.3, 1.0)  # 0.3 std = good spread

    regions = set(a["region"] for a in articles)
    region_score = min(len(regions) / 2, 1.0)

    credibilities = [a["credibility"] for a in known if a["credibility"]]
    credibility_avg = float(np.mean(credibilities)) if credibilities else 0.5

    final_score = round(
        (source_score * 30 + bias_score * 35 + region_score * 15 + credibility_avg * 20), 1
    )

    return {
        "score": final_score,
        "breakdown": {
            "Source Variety": round(source_score * 30, 1),
            "Bias Spread": round(bias_score * 35, 1),
            "Regional Mix": round(region_score * 15, 1),
            "Credibility": round(credibility_avg * 20, 1),
        },
        "unique_sources": unique_sources,
        "bias_spread_std": round(bias_spread, 3),
        "credibility_avg": round(credibility_avg, 2),
    }
