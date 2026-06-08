import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

SOURCE_METADATA = {
    "the-hindu": {"credibility": 0.85, "region": "India"},
    "the-times-of-india": {"credibility": 0.75, "region": "India"},
    "ndtv": {"credibility": 0.78, "region": "India"},
    "the-indian-express": {"credibility": 0.83, "region": "India"},
    "bbc-news": {"credibility": 0.90, "region": "Global"},
    "reuters": {"credibility": 0.93, "region": "Global"},
    "al-jazeera-english": {"credibility": 0.82, "region": "Global"},
    "the-guardian": {"credibility": 0.85, "region": "Global"},
    "bloomberg": {"credibility": 0.88, "region": "Global"},
    "the-washington-post": {"credibility": 0.84, "region": "Global"},
}


def fetch_articles(topic: str, max_articles: int = 40) -> list[dict]:
    api_key = os.getenv("NEWSAPIKEY")
    if not api_key:
        raise ValueError("NEWSAPIKEY not set in .env")

    from_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": topic,
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": min(max_articles, 60),
        "from": from_date,
        "apiKey": api_key,
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    articles = []
    for item in data.get("articles", []):
        source_id = (item.get("source", {}).get("id") or "").lower()
        meta = SOURCE_METADATA.get(source_id, {"credibility": 0.60, "region": "Unknown"})

        title = item.get("title") or ""
        description = item.get("description") or ""
        content = item.get("content") or ""
        full_text = f"{title}. {description}. {content}".strip()

        if len(full_text) < 40:
            continue

        articles.append({
            "title": title,
            "source": item.get("source", {}).get("name", "Unknown"),
            "source_id": source_id,
            "url": item.get("url", ""),
            "published_at": item.get("publishedAt", ""),
            "text": full_text,
            "credibility": meta["credibility"],
            "region": meta["region"],
        })

    return articles
