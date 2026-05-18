import os
import requests
import json, pathlib

from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def load_sources() -> dict:
    "Load the source metadata from the sources.json file and return it as a dictionary."
    path = pathlib.Path(__file__).parent / "sources.json"
    if not path.exists():
        raise FileNotFoundError(f"Could not find sources.json at {path}")
    with open(path, "r") as f:
        return json.load(f)
    
SOURCE_METADATA = load_sources()

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
        elif score >=1.0:
            return "Far Right"
        else:
            return "Far Left"
        
def fetch_articles(topic: str, days_back: int = 3, max_articles: int=40) -> list[dict]:
    api_key =os.getenv("NEWSAPIKEY")
    if not api_key:
        raise ValueError("NEWSAPIKEY not set in .env")
    
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
    resp.raise_for_status() #to catch any http errors

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
