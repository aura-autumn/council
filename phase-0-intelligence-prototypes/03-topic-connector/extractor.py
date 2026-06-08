import spacy
from collections import defaultdict
import re

# Load once at module level
_nlp = None

STOP_ENTITIES = {
    "monday", "tuesday", "wednesday", "thursday", "friday",
    "saturday", "sunday", "january", "february", "march", "april",
    "may", "june", "july", "august", "september", "october",
    "november", "december", "today", "yesterday", "week", "month",
    "year", "reuters", "afp", "ap", "pti", "ani", "ians",
}

ALLOWED_ENTITY_TYPES = {"PERSON", "ORG", "GPE", "EVENT", "NORP", "FAC", "PRODUCT"}


def _get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


def _clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s\-\']", " ", text)
    return text.strip()


def extract_entities_from_articles(articles: list[dict], top_n: int = 25) -> dict:
    """
    Returns:
        {
            "entities": [{"name": str, "type": str, "freq": int}, ...],
            "article_entities": [[entity_names], ...],   # parallel to articles
            "entity_freq": {name: int},
            "entity_to_articles": {name: [article_dict, ...]},  # NEW
        }
    """
    nlp = _get_nlp()

    entity_freq = defaultdict(int)
    entity_type_map = {}
    article_entities = []

    for article in articles:
        text = _clean(article["text"])[:1500]  # cap for speed
        doc = nlp(text)

        seen_in_article = set()
        for ent in doc.ents:
            if ent.label_ not in ALLOWED_ENTITY_TYPES:
                continue
            name = ent.text.strip().title()
            if len(name) < 3 or name.lower() in STOP_ENTITIES:
                continue
            if any(char.isdigit() for char in name):
                continue
            seen_in_article.add(name)
            entity_type_map[name] = ent.label_

        article_entities.append(list(seen_in_article))
        for name in seen_in_article:
            entity_freq[name] += 1

    # Filter: must appear in at least 2 articles, take top_n by freq
    filtered = {k: v for k, v in entity_freq.items() if v >= 2}
    top_entities = sorted(filtered, key=lambda x: -filtered[x])[:top_n]

    entities = [
        {
            "name": name,
            "type": entity_type_map.get(name, "ORG"),
            "freq": entity_freq[name],
        }
        for name in top_entities
    ]

    # Re-filter article_entities to only include top entities
    top_set = set(top_entities)
    article_entities_filtered = [
        [e for e in ae if e in top_set] for ae in article_entities
    ]

    # Build entity_to_articles: maps each entity to the articles it appeared in.
    # We iterate over the ORIGINAL article_entities (pre-filter) so we capture
    # all appearances, then only store entries for top entities.
    entity_to_articles = defaultdict(list)
    for idx, article in enumerate(articles):
        for ent_name in article_entities[idx]:          # use pre-filter list
            if ent_name in top_set:
                entity_to_articles[ent_name].append({
                    "title":  article.get("title", "Untitled"),
                    "source": article.get("source", "Unknown"),
                    "url":    article.get("url", ""),
                    "text":   article.get("text", ""),
                })

    return {
        "entities": entities,
        "article_entities": article_entities_filtered,
        "entity_freq": {name: entity_freq[name] for name in top_entities},
        "entity_to_articles": dict(entity_to_articles),   # NEW
    }