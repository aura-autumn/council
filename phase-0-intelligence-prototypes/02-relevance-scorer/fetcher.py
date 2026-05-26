"""
fetcher.py — NewsAPI article ingestion with metadata enrichment.

Mirrors the interface from prototype 01 so the module can be shared
later when both prototypes are merged into the backend.
"""

from __future__ import annotations
import os
import time
import hashlib
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

NEWSAPI_KEY = os.getenv("NEWSAPIKEY", "")
NEWSAPI_BASE = "https://newsapi.org/v2/everything"

# ── Source metadata (bias + credibility) — same registry as prototype 01 ────
SOURCE_META: dict = {
    # Indian sources
    "the-hindu": {"bias": -0.2, "credibility": 0.85, "region": "india"},
    "the-times-of-india": {"bias": 0.1, "credibility": 0.70, "region": "india"},
    "ndtv": {"bias": -0.1, "credibility": 0.78, "region": "india"},
    "india-today": {"bias": 0.0, "credibility": 0.80, "region": "india"},
    "the-wire": {"bias": -0.4, "credibility": 0.75, "region": "india"},
    "mint": {"bias": 0.1, "credibility": 0.82, "region": "india"},
    "business-standard": {"bias": 0.1, "credibility": 0.83, "region": "india"},
    "scroll-in": {"bias": -0.3, "credibility": 0.74, "region": "india"},
    # Global sources
    "reuters": {"bias": 0.0, "credibility": 0.92, "region": "global"},
    "associated-press": {"bias": 0.0, "credibility": 0.93, "region": "global"},
    "bbc-news": {"bias": -0.1, "credibility": 0.88, "region": "global"},
    "the-guardian": {"bias": -0.35, "credibility": 0.82, "region": "global"},
    "bloomberg": {"bias": 0.1, "credibility": 0.87, "region": "global"},
    "financial-times": {"bias": 0.1, "credibility": 0.88, "region": "global"},
    "wired": {"bias": -0.1, "credibility": 0.80, "region": "global"},
    "techcrunch": {"bias": -0.05, "credibility": 0.76, "region": "global"},
    "the-wall-street-journal": {"bias": 0.25, "credibility": 0.86, "region": "global"},
    "fox-news": {"bias": 0.55, "credibility": 0.55, "region": "global"},
    "the-new-york-times": {"bias": -0.25, "credibility": 0.84, "region": "global"},
    "washington-post": {"bias": -0.25, "credibility": 0.83, "region": "global"},
}

DEFAULT_META = {"bias": 0.0, "credibility": 0.65, "region": "unknown"}


@dataclass
class Article:
    id: str
    title: str
    description: str
    content: str
    url: str
    source: str
    source_id: str
    published_at: str
    bias_score: float
    credibility: float
    region: str
    relevance_score: float = 0.0
    matched_topics: List[str] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        return f"{self.title}. {self.description or ''} {self.content or ''}".strip()

    @property
    def age_hours(self) -> float:
        try:
            pub = datetime.fromisoformat(self.published_at.replace("Z", "+00:00"))
            return (datetime.now(pub.tzinfo) - pub).total_seconds() / 3600
        except Exception:
            return 0.0


def fetch_articles(query: str, max_articles: int = 60, region_focus: str = "both") -> List[Article]:
    """Fetch articles from NewsAPI for the given query."""
    if not NEWSAPI_KEY:
        raise ValueError("NEWSAPI_KEY not set. Copy .env.example → .env and add your key.")

    sources_india = "the-hindu,ndtv,india-today,the-wire,mint,business-standard,scroll-in"
    sources_global = "reuters,bbc-news,the-guardian,bloomberg,wired,techcrunch,the-wall-street-journal"

    if region_focus == "india":
        sources = sources_india
    elif region_focus == "global":
        sources = sources_global
    else:
        sources = f"{sources_india},{sources_global}"

    params = {
        "q": query,
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": min(max_articles, 100),
        "apiKey": NEWSAPI_KEY,
        "sources": sources,
    }

    resp = requests.get(NEWSAPI_BASE, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    articles: List[Article] = []
    for raw in data.get("articles", []):
        src_id = (raw.get("source") or {}).get("id") or ""
        src_name = (raw.get("source") or {}).get("name") or "Unknown"
        meta = SOURCE_META.get(src_id, DEFAULT_META)

        uid = hashlib.md5((raw.get("url") or raw.get("title", "")).encode()).hexdigest()[:10]

        articles.append(Article(
            id=uid,
            title=raw.get("title") or "",
            description=raw.get("description") or "",
            content=(raw.get("content") or "")[:500],
            url=raw.get("url") or "",
            source=src_name,
            source_id=src_id,
            published_at=raw.get("publishedAt") or "",
            bias_score=meta["bias"],
            credibility=meta["credibility"],
            region=meta["region"],
        ))

    return articles
