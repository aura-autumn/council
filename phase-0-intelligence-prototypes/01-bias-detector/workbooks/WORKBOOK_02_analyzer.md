# WORKBOOK 02 — `analyzer.py`
### The Brain. Sentiment, contradiction detection, and diversity scoring.

> **Prerequisite:** You have a working `fetch_articles()` that returns a list of article dicts. Each dict has `title`, `description`, `source_name`, `bias_score`, `bias_label`, `region`, `credibility`.

---

## 🧭 What This File Does

This file takes the raw article list from fetcher.py and adds three layers of intelligence:

1. **Sentiment scoring** — Is each article positive or negative in tone?
2. **Contradiction detection** — Which pairs of articles cover the same story but frame it oppositely?
3. **Diversity scoring** — How diverse is the overall set of sources?

These three things are independent functions. Write them in order — each one builds on the previous.

---

## 📦 Step 1 — Imports

You need:
- `re` — for basic text cleaning
- `numpy as np` — for math (std deviation, mean)
- `cosine_similarity` from `sklearn.metrics.pairwise`
- `TfidfVectorizer` from `sklearn.feature_extraction.text`

Don't import `transformers` at the top level. You'll handle that differently (see Step 2).

---

## 🤖 Step 2 — Lazy-Loading the Sentiment Pipeline

**Write a module-level variable `_pipeline = None`.**

Then write a function `_get_pipeline()` that:
1. Checks if `_pipeline` is `None`
2. If so, imports `pipeline` from `transformers` and creates one using model `"distilbert-base-uncased-finetuned-sst-2-english"` with `truncation=True` and `max_length=512`
3. Stores it in the global `_pipeline`
4. Returns `_pipeline`

💡 **Why lazy-load?** This model is ~250MB and takes a few seconds to load. If you import it at the top of the file, the entire app slows down on startup even if no one ever clicks "Analyze". By loading it only when first called, you keep startup instant. This pattern is called lazy initialization.

💡 **Why `global _pipeline`?** Normally Python functions can't modify module-level variables. The `global` keyword tells Python "when I say `_pipeline =` here, I mean the module-level one, not a new local variable."

---

## 🎭 Step 3 — `score_sentiment(text)`

**Write a function that takes a string and returns a float between -1.0 and +1.0.**

Steps inside:
1. Guard clause: if text is empty or whitespace, return `0.0`
2. Call `_get_pipeline()` to get the model
3. Run `pipe(text[:512])[0]` — the `[:512]` slices to model's max length, `[0]` gets the first (only) result
4. The result is a dict like `{"label": "POSITIVE", "score": 0.92}`
5. If the label is `"POSITIVE"`, return the score as-is. If `"NEGATIVE"`, return its negative.

💡 **Why negate the score?** The model returns a confidence score (always 0–1). A score of 0.9 with label NEGATIVE means it's 90% confident it's negative — so you represent that as -0.9 on your scale.

---

## 📰 Step 4 — `analyze_articles(articles)`

**Write a function that takes the list from fetcher.py and returns an enriched list.**

For each article:
1. Build `text = f"{article['title']}. {article['description']}"`
2. Call `score_sentiment(text)` to get a float
3. Return a new dict that spreads the original (`**art`) and adds:
   - `"sentiment_score"` → the float
   - `"sentiment_label"` → `"Positive"` / `"Negative"` / `"Neutral"` based on thresholds (you decide where the cutoffs are — try ±0.15)
   - `"text_for_analysis"` → the combined text string

Return the enriched list.

💡 **Why combine title and description?** Titles alone are often too short for reliable sentiment. Descriptions add context. Content is sometimes truncated by NewsAPI, so it's less reliable.

---

## 🔍 Step 5 — `detect_contradictions(articles, threshold=0.25)`

This is the most complex function. Take it one piece at a time.

### 5a. Guard clause
If there are fewer than 2 articles, return an empty list immediately.

### 5b. Prepare texts for TF-IDF
Write a small helper `_clean(text)` that strips extra whitespace and lowercases. Apply it to each article's `text_for_analysis` field.

### 5c. Build the TF-IDF similarity matrix
Create a `TfidfVectorizer(stop_words="english", max_features=500)` and call `.fit_transform(texts)`. Wrap this in a try/except — if all texts are empty, sklearn will raise a `ValueError`. Then call `cosine_similarity(tfidf_matrix)` to get an NxN matrix where `sim_matrix[i][j]` is how similar articles i and j are.

💡 **What is TF-IDF?** Term Frequency-Inverse Document Frequency. It turns a text into a vector where each dimension represents a word, weighted by how often it appears in this document vs how rare it is across all documents. Articles about the same topic will have similar vectors, so their cosine similarity will be high.

💡 **What is cosine similarity?** It measures the angle between two vectors. 1.0 = identical direction (same topic), 0.0 = perpendicular (completely unrelated). You don't care about length (article length), only direction (topic focus).

### 5d. Extract sentiment scores as a numpy array
`sentiments = np.array([a["sentiment_score"] for a in articles])`

### 5e. The nested loop
Loop `i` from 0 to `len(articles)`. For each i, loop `j` from `i+1` to `len(articles)`. This gives you every unique pair without repeating (i=0,j=1 is the same pair as i=1,j=0).

For each pair, check three conditions:
- `sim_matrix[i, j] >= 0.35` → they cover similar content
- `abs(sentiments[i] - sentiments[j]) >= threshold` → they have opposing sentiment
- `articles[i]["source_name"] != articles[j]["source_name"]` → they're from different sources

If all three are true, append a contradiction dict to your results list. The dict should contain full info about both articles and the similarity/divergence scores.

### 5f. Severity rating and sorting
After the loop, sort contradictions by severity. Assign severity as `"High"` if divergence > 0.6, `"Medium"` if > 0.35, else `"Low"`. Return only the top 15.

---

## 📊 Step 6 — `compute_diversity_score(articles)`

**Write a function that returns a dict with a score (0–100) and a breakdown.**

Compute four sub-scores:
- **Source variety** → `len(set of source names)` / 8, capped at 1.0 (worth 30 points)
- **Bias spread** → `np.std([bias scores])` / 0.3, capped at 1.0 (worth 35 points)
- **Regional mix** → `len(set of regions)` / 2, capped at 1.0 (worth 15 points)
- **Credibility average** → `np.mean([credibility scores])`, already 0–1 (worth 20 points)

Final score = sum of (sub_score × weight). Return a dict with `"score"`, `"breakdown"`, and some extras like `unique_sources` and `bias_spread_std`.

💡 **Why these weights?** Bias spread is weighted most (35pts) because a truly diverse news diet spans the political spectrum, not just many outlets with the same lean. You can adjust these weights — they're a design decision, not a fact.

---

## ✅ Quick Sanity Check

```python
if __name__ == "__main__":
    from fetcher import fetch_articles
    raw = fetch_articles("climate change", days_back=2, max_articles=10)
    enriched = analyze_articles(raw)
    print(enriched[0]["sentiment_label"], enriched[0]["sentiment_score"])
    
    contradictions = detect_contradictions(enriched)
    print(f"Found {len(contradictions)} contradictions")
    
    diversity = compute_diversity_score(enriched)
    print(f"Diversity score: {diversity['score']}")
```

**Common errors:**
- Model download fails → check internet connection; the model downloads once to `~/.cache/huggingface`
- `ValueError` in TF-IDF → usually all articles are empty strings; check your fetcher returns real text
- No contradictions found → normal for small article sets or when sources agree; try a political topic

---

## 🔜 Next: WORKBOOK_03_charts.py

You now have enriched articles with sentiment scores, a list of contradiction pairs, and a diversity dict. The next file turns all of this into Plotly visualizations.

**Concepts you'll meet there:** Plotly Figure objects, custom color palettes, scatter plots, gauge charts, horizontal bar charts.
