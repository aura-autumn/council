# WORKBOOK 01 — `fetcher.py`
### Start Here. This is the foundation of everything.

---

## 🧭 What This File Does (Before You Write a Single Line)

Before writing code, understand the job of this file:

> **fetcher.py is the mouth of the system.** It goes out to the internet, grabs news articles, and stamps each one with metadata (bias score, credibility, region) before handing them off to the analyzer.

Every other file depends on what this file returns. Get this right and the rest follows naturally.

---

## 📦 Step 1 — Imports & Environment Setup

**Start by writing your imports at the top of the file.**

You need four things:
- `os` — to read environment variables (your secret API key)
- `requests` — to make HTTP calls to NewsAPI
- `datetime` and `timedelta` from the `datetime` module — to calculate date ranges
- `load_dotenv` from the `dotenv` package — to load your `.env` file

💡 **Why a `.env` file?** API keys should never be hardcoded in your source code. Anyone who sees your code would see your key. Instead, you store it in a file called `.env` (which you add to `.gitignore`) and load it at runtime.

After your imports, call `load_dotenv()` so Python can read your `.env` file.

---

## 🗂️ Step 2 — The Source Metadata Dictionary

**This is the heart of the bias detection — write a load_sources() function and point it at a sources.json file.".**

Call it `SOURCE_METADATA`. The keys are NewsAPI's source IDs (like `"bbc-news"`, `"the-hindu"`). Each value is another dictionary with:
- `"label"` → the human-readable name
- `"bias"` → a float from `-1.0` (far left) to `+1.0` (far right), `0` = center
- `"credibility"` → a float from `0.0` to `1.0`
- `"region"` → `"India"` or `"Global"`

**Include at least 5–6 sources.** Mix Indian sources (the-hindu, ndtv, times-of-india) with global ones (bbc-news, reuters, cnn).

💡 **Where do these bias numbers come from?** They're manually curated from research by organizations like AllSides and Ad Fontes Media. This is a deliberate design choice — being transparent about how bias is scored rather than hiding it inside a model.

---

## 🏷️ Step 3 — The Bias Label Map

**Write a second dictionary called `BIAS_LABEL_MAP`.**

This maps score ranges to human-readable labels. The keys are tuples of `(low, high)` floats representing a range, and the values are strings like `"Far Left"`, `"Left-Leaning"`, `"Center"`, `"Right-Leaning"`, `"Far Right"`.

Then write a function `get_bias_label(score: float) -> str` that loops through this dictionary and returns the matching label. Handle edge cases (what if the score is exactly 1.0?).

💡 **Why separate this into its own function?** You'll call this repeatedly — once per article — and you want the logic in one place so if you adjust the ranges later, you only change it here.

---

## 🔌 Step 4 — The Main Fetch Function

**Write a function called `fetch_articles(topic, days_back=3, max_articles=40)`.**

This is the only function the rest of the app will call from this file. Here's what it needs to do, step by step:

### 4a. Read the API key
Use `os.getenv("NEWSAPI_KEY")` to read the key. If it's `None`, raise a `ValueError` with a helpful message telling the user to set it in their `.env`.

### 4b. Build the date range
Use `datetime.now()` and `timedelta(days=days_back)` to calculate how far back to search. Format it as `"YYYY-MM-DD"` using `.strftime()`.

### 4c. Make the API call
The NewsAPI endpoint is `https://newsapi.org/v2/everything`. Use `requests.get()` with these parameters:
- `q` → the topic
- `from` → your calculated date
- `sortBy` → `"relevancy"`
- `language` → `"en"`
- `pageSize` → max_articles
- `apiKey` → your key

Set a `timeout=10` so the app doesn't hang. Call `.raise_for_status()` on the response to catch HTTP errors.

### 4d. Parse and enrich each article
Loop through `data.get("articles", [])`. For each article:
1. Extract the `source.id` and `source.name`
2. Look up the source ID in `SOURCE_METADATA` (use `.get()` with a fallback dict for unknown sources)
3. Build a clean dictionary with these keys: `title`, `description`, `content`, `url`, `published_at`, `source_id`, `source_name`, `bias_score`, `bias_label`, `credibility`, `region`

Return the list of these enriched dicts.

💡 **What's the fallback for unknown sources?** When a source isn't in your `SOURCE_METADATA`, use `{"label": source_name, "bias": None, "credibility": None, "region": "Unknown"}`. The downstream code is designed to handle `None` values gracefully.

---

## ✅ Quick Sanity Check

Before moving on, test this file in isolation:

```python
# At the bottom of fetcher.py, wrapped in if __name__ == "__main__":
articles = fetch_articles("India economy", days_back=2, max_articles=5)
for a in articles:
    print(a["source_name"], a["bias_label"], a["title"][:60])
```

Run it with `python fetcher.py`. If you see article titles printing with source names and bias labels, you're ready for the next file.

**Common errors at this stage:**
- `ValueError: NEWSAPI_KEY not set` → your `.env` file isn't set up correctly
- `requests.exceptions.ConnectionError` → no internet or the URL is wrong
- KeyError when parsing → check what keys the API actually returns (print `data.keys()` first)

---

## 🔜 Next: WORKBOOK_02_analyzer.py

You now have a list of article dicts flowing out of fetcher.py. The next file takes that list and adds sentiment scores, then finds contradictions between articles.

**Concepts you'll meet there:** HuggingFace pipelines, TF-IDF vectorization, cosine similarity, lazy loading.
