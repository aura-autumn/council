"""
scorer.py — Relevance Engine core.

Scores articles against the user profile using a two-stage pipeline:

  Stage 1 — Topic matching (fast, keyword-level)
    Each article is scored against ALL_INTERESTS using keyword heuristics.
    This produces a sparse "article interest vector."

  Stage 2 — Cosine similarity
    Dot product between the normalised user-profile vector and the
    normalised article interest vector.  This is the base relevance score.

  Stage 3 — Signal boosting
    Freshness, credibility, and query alignment nudge the final score.

The design intentionally mirrors what production will do with sentence
embeddings — the vector shape is identical, only the encoding differs.
"""

from __future__ import annotations
import re
import math
import numpy as np
from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from user_profile import UserProfile, ALL_INTERESTS
from fetcher import Article

# ── Interest → keyword mapping ───────────────────────────────────────────────
INTEREST_KEYWORDS: Dict[str, List[str]] = {
    "Artificial Intelligence": ["ai", "machine learning", "deep learning", "llm", "neural", "gpt", "chatgpt", "openai", "anthropic", "automation", "generative"],
    "Cybersecurity": ["cyber", "hack", "breach", "ransomware", "malware", "vulnerability", "security", "phishing", "data leak", "zero-day"],
    "Startups & VC": ["startup", "venture capital", "funding", "series a", "series b", "ipo", "unicorn", "founder", "pitch", "accelerator"],
    "Web3 & Crypto": ["bitcoin", "crypto", "blockchain", "ethereum", "nft", "defi", "web3", "token", "wallet", "solana"],
    "Space & Deep Tech": ["space", "nasa", "isro", "rocket", "satellite", "quantum", "fusion", "semiconductor", "chip"],
    "Open Source": ["open source", "github", "linux", "contributor", "apache", "mit license", "community", "fork"],
    "Indian Markets": ["nifty", "sensex", "bse", "nse", "sebi", "dalal street", "indian stock", "mutual fund india", "smallcap"],
    "Global Macro": ["federal reserve", "interest rate", "inflation", "gdp", "recession", "imf", "world bank", "monetary policy"],
    "Personal Finance": ["personal finance", "savings", "investment", "portfolio", "sip", "retirement", "tax planning", "insurance"],
    "Policy & RBI": ["rbi", "reserve bank", "repo rate", "monetary", "rbi policy", "governor", "inflation target"],
    "Startups & Funding": ["funding", "raised", "seed round", "angel investor", "valuation", "startup india", "incubator"],
    "India-China Relations": ["india china", "border", "ladakh", "line of actual control", "doklam", "galwan", "bri", "dragon"],
    "US Politics": ["biden", "trump", "congress", "senate", "white house", "democrat", "republican", "election"],
    "Middle East": ["israel", "palestine", "iran", "saudi", "hamas", "gaza", "middle east", "oil price"],
    "South Asia": ["pakistan", "bangladesh", "sri lanka", "nepal", "saarc", "south asia"],
    "International Trade": ["trade war", "tariff", "export", "wto", "supply chain", "sanctions", "trade deal"],
    "Climate & Environment": ["climate", "carbon", "emission", "renewable", "solar", "wind energy", "net zero", "cop", "biodiversity"],
    "Biotech & Health": ["vaccine", "clinical trial", "biotech", "pharma", "drug approval", "genome", "cancer", "pandemic"],
    "Physics": ["particle physics", "cern", "quantum", "gravitational wave", "physics experiment"],
    "Astronomy": ["telescope", "planet", "galaxy", "black hole", "nasa", "isro", "chandrayaan", "mars", "asteroid"],
    "Research & Academia": ["research", "study", "journal", "university", "iit", "iim", "phd", "academic paper"],
    "Education": ["education", "school", "college", "neet", "jee", "exam", "student", "teacher", "curriculum"],
    "Urban India": ["smart city", "metro", "urban", "housing", "real estate india", "bengaluru", "mumbai", "delhi"],
    "Sports": ["cricket", "ipl", "football", "olympic", "athlete", "world cup", "sports", "chess", "badminton"],
    "Entertainment": ["bollywood", "ott", "netflix", "amazon prime", "film", "movie", "music", "streaming"],
    "Philosophy & Ideas": ["philosophy", "ethics", "values", "existential", "consciousness", "meaning", "ideology"],
    "Indian Government": ["modi", "parliament", "budget", "cabinet", "ministry", "lok sabha", "rajya sabha", "bjp", "congress party"],
    "Defence": ["army", "air force", "navy", "defence", "missile", "military", "rafale", "drdo", "border security"],
    "Infrastructure": ["highway", "railway", "bullet train", "airport", "port", "infrastructure india", "project"],
    "Healthcare Policy": ["health ministry", "ayushman", "nhs", "hospital", "healthcare reform", "who", "public health"],
    "Legal & Courts": ["supreme court", "high court", "judgement", "petition", "constitution", "law", "legal"],
}


def _article_interest_vector(article: Article) -> np.ndarray:
    """Compute a sparse interest vector for an article via keyword matching."""
    text = article.full_text.lower()
    vec = np.zeros(len(ALL_INTERESTS))
    matched = []
    for i, interest in enumerate(ALL_INTERESTS):
        keywords = INTEREST_KEYWORDS.get(interest, [interest.lower()])
        hits = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', text))
        if hits > 0:
            vec[i] = min(hits / 3.0, 1.0)   # cap at 1.0
            matched.append(interest)
    return vec, matched


def score_articles(
    articles: List[Article],
    profile: UserProfile,
    query: str = "",
    freshness_weight: float = 0.10,
    credibility_weight: float = 0.10,
) -> List[Article]:
    """
    Score and sort articles by relevance to the user profile.
    Returns articles with .relevance_score and .matched_topics set.
    """
    profile_vec = profile.to_vector()   # (n_interests,)

    # Build TF-IDF matrix over article texts for query similarity boost
    texts = [a.full_text for a in articles]
    try:
        tfidf = TfidfVectorizer(max_features=5000, stop_words="english")
        tfidf_matrix = tfidf.fit_transform(texts)
        if query:
            query_vec = tfidf.transform([query])
            query_sims = cosine_similarity(query_vec, tfidf_matrix).flatten()
        else:
            query_sims = np.zeros(len(articles))
    except Exception:
        query_sims = np.zeros(len(articles))

    max_age = 72.0   # normalise freshness over 3 days

    for i, article in enumerate(articles):
        art_vec, matched = _article_interest_vector(article)

        # Cosine similarity between user profile and article interest vectors
        norm_p = np.linalg.norm(profile_vec)
        norm_a = np.linalg.norm(art_vec)
        if norm_p > 0 and norm_a > 0:
            base_score = float(np.dot(profile_vec, art_vec) / (norm_p * norm_a))
        else:
            base_score = 0.0

        # Freshness boost: newer articles score higher
        freshness = max(0.0, 1.0 - article.age_hours / max_age)

        # Credibility boost
        credibility = article.credibility

        # Query alignment boost
        query_boost = float(query_sims[i]) if query else 0.0

        # Combined score
        relevance = (
            (1.0 - freshness_weight - credibility_weight) * base_score
            + freshness_weight * freshness
            + credibility_weight * credibility
        )
        # Query boost is additive (only active when query given)
        relevance = min(1.0, relevance + 0.15 * query_boost)

        article.relevance_score = round(relevance, 4)
        article.matched_topics = matched

    return sorted(articles, key=lambda a: a.relevance_score, reverse=True)


def compute_feed_stats(articles: List[Article]) -> dict:
    """Aggregate stats for the scored feed — used by charts."""
    if not articles:
        return {}

    scores = [a.relevance_score for a in articles]
    topic_freq: Dict[str, int] = {}
    for a in articles:
        for t in a.matched_topics:
            topic_freq[t] = topic_freq.get(t, 0) + 1

    return {
        "mean_relevance": float(np.mean(scores)),
        "median_relevance": float(np.median(scores)),
        "high_relevance_pct": sum(1 for s in scores if s >= 0.5) / len(scores),
        "top_topics": sorted(topic_freq.items(), key=lambda x: x[1], reverse=True)[:10],
        "score_distribution": scores,
    }
