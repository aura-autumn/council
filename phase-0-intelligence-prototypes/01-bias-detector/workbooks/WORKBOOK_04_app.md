# WORKBOOK 04 — `app.py`
### The Dashboard. Wiring everything together with Streamlit.

> **Prerequisite:** `fetcher.py`, `analyzer.py`, and `charts.py` are all working individually. Now you connect them into a live interactive app.

---

## 🧭 What This File Does

app.py is the orchestrator. It:
1. Configures the Streamlit page
2. Renders the sidebar (controls)
3. On button click: calls fetcher → analyzer → diversity scorer → chart renderer
4. Lays out all results in a structured dashboard

**Critical thing to understand about Streamlit:** Every time a user interacts with anything (moves a slider, clicks a button), the entire script reruns from top to bottom. This is different from most UI frameworks. Keep this in mind as you write — the order of your code is the order of execution.

---

## 📦 Step 1 — Imports

You need:
- `streamlit as st`
- `pandas as pd`
- `time` (optional, sometimes useful for timing)
- All five chart functions from `charts.py`
- `fetch_articles` from `fetcher.py`
- `analyze_articles`, `detect_contradictions`, `compute_diversity_score` from `analyzer.py`

---

## ⚙️ Step 2 — Page Config

**This must be the very first Streamlit call in your script, before any other `st.*` calls.**

Call `st.set_page_config()` with:
- `page_title` → your app's browser tab title
- `page_icon` → an emoji
- `layout="wide"` → uses the full browser width instead of the narrow default
- `initial_sidebar_state="expanded"`

💡 **Why must it be first?** Streamlit builds the page structure before rendering anything. `set_page_config` tells it the structure. If you call it after rendering something, Streamlit throws an error.

---

## 🎨 Step 3 — Custom CSS

**Inject custom styles using `st.markdown()` with `unsafe_allow_html=True`.**

Wrap your CSS in a `<style>` tag inside a triple-quoted string. You'll want styles for:
- The main background and text color (targeting `[data-testid="stAppViewContainer"]`)
- The sidebar background and border
- Custom card components (metric cards, contradiction cards) — these are `<div>` elements you'll write manually in later steps
- Hiding Streamlit's default footer and deploy button

💡 **Why `unsafe_allow_html=True`?** Streamlit sanitizes HTML by default for security. You need to opt into raw HTML rendering. Only use this for your own trusted strings — never pass user input directly into this.

💡 **Tip for selectors:** Streamlit's internal DOM uses `data-testid` attributes. Inspect the page with browser DevTools to find the right selectors if something isn't styling correctly.

---

## 🏠 Step 4 — Header

Write a brief title section using `st.markdown()` with custom-styled `<p>` tags. Make it feel like a header/hero area — your project name and a subtitle. This appears above everything else on every page load.

---

## 🔧 Step 5 — The Sidebar

**Use a `with st.sidebar:` block.** Everything inside renders in the left panel.

Build these controls:
- `st.text_input()` → topic input with a placeholder
- `st.slider()` for `days_back` (1–7)
- `st.slider()` for `max_articles` (10–60)
- `st.slider()` for `contradiction_threshold` (0.1–0.8, step 0.05)
- `st.checkbox()` for whether to include unknown-bias sources
- A markdown section with project info/links
- `st.button("ANALYZE", use_container_width=True, type="primary")` — store the return value in a variable like `analyze_btn`

💡 **Why put the button in the sidebar?** Keeps it always visible even when the user scrolls down through results. The button returns `True` only on the click that triggers it — on all other reruns, it returns `False`.

---

## 🚦 Step 6 — The Idle State

**Write an `if not analyze_btn: ... st.stop()` block right after the sidebar.**

When the button hasn't been clicked yet, show a welcome/instructions panel and call `st.stop()`. This is Streamlit's way of halting execution — nothing below it runs.

💡 **Why `st.stop()`?** Without it, the code below (which tries to use data that doesn't exist yet) would run and crash. `st.stop()` is cleaner than wrapping everything in a huge `if` block.

---

## ⚡ Step 7 — Fetch, Analyze, Detect (the data pipeline)

This runs only when the button was clicked. Use `st.spinner("message...")` context managers to show loading indicators for each slow step:

```
with st.spinner("Fetching..."):
    raw_articles = fetch_articles(topic, days_back=days_back, max_articles=max_articles)
```

Wrap the fetch in a try/except — if it fails (bad API key, no internet), call `st.error(message)` and `st.stop()`.

Then check: if `raw_articles` is empty, call `st.warning()` and `st.stop()`.

Run `analyze_articles()`, optionally filter out unknown-bias articles based on the checkbox, then run `detect_contradictions()` and `compute_diversity_score()`.

---

## 📏 Step 8 — Metrics Row

**Use `st.columns(5)` to create five equal columns.** Unpack them:
```python
col1, col2, col3, col4, col5 = st.columns(5)
```

In each column, use `with colN:` and render a styled `<div>` using `st.markdown(unsafe_allow_html=True)`. Each card shows a big number (metric value) and a small label. Values to show:
- Article count
- Unique source count
- Contradiction count
- Diversity score
- Average credibility

---

## 📉 Step 9 — Charts Layout

**Create two rows of charts using `st.columns()`.**

Row 1 — two equal columns:
- Left: `bias_distribution_chart(articles)`
- Right: `sentiment_bias_scatter(articles)`

Render each with `st.plotly_chart(fig, use_container_width=True)`.

Row 2 — two columns (adjust width ratio with e.g. `[1, 1.4]`):
- Left: `diversity_gauge(diversity)` + a breakdown section below it
- Right: `credibility_heatmap(articles)`

For the diversity breakdown, loop through `diversity["breakdown"]` and render a label + `st.progress(percentage)` bar for each component.

---

## ⚡ Step 10 — Contradictions Section

Check if `contradictions` is empty. If so, show `st.info("No contradictions found...")`.

If contradictions exist, use two columns:
- Left: `contradiction_chart(contradictions)`
- Right: Loop through the first 6 contradictions and render each as a styled `<div>` card using `st.markdown(unsafe_allow_html=True)`. Each card shows both article titles, their sources, bias labels, sentiment labels, and a severity badge.

💡 **For the card HTML:** Use CSS classes you defined in Step 3 (`contradiction-card high/medium/low`, `severity-badge badge-high/medium/low`) so severity is visually distinct. Add `<a href="...">` links to article URLs.

---

## 📋 Step 11 — Raw Data Table

Wrap this in `st.expander("📋 Raw Article Data", expanded=False)` so it's collapsed by default.

Inside, convert articles to a DataFrame, select the display columns, and render with `st.dataframe()`. Configure special column types:
- URL column → `st.column_config.LinkColumn()`
- Credibility → `st.column_config.ProgressColumn()` for a visual bar

---

## ✅ Running the App

```bash
streamlit run app.py
```

This opens a browser tab at `localhost:8501`. Enter a topic and click ANALYZE.

**Common errors at this stage:**
- Streamlit can't find your other files → make sure all `.py` files are in the same directory
- Charts don't render → check that `use_container_width=True` is set and the figure isn't an empty `go.Figure()`
- CSS not applying → browser-inspect the element to confirm the selector is correct
- App reruns unexpectedly → this is normal; any widget interaction reruns the whole script

---

## 🗺️ Full System Map

```
app.py  (entry point — Streamlit runs this)
  │
  ├── fetcher.py       → fetch_articles()
  │     └── NewsAPI HTTP call + SOURCE_METADATA enrichment
  │
  ├── analyzer.py      → analyze_articles(), detect_contradictions(), compute_diversity_score()
  │     ├── DistilBERT sentiment model (HuggingFace)
  │     └── TF-IDF + cosine similarity (scikit-learn)
  │
  └── charts.py        → 5 chart functions
        └── Plotly figures with unified dark theme
```

You built each piece in isolation first, then connected them here. That's the right way to do it — testable components assembled into a working system.

---

## 🚀 Where to Go From Here

Once the basic pipeline works, here are natural extensions to try:

- **Better similarity:** Replace TF-IDF with sentence embeddings (`sentence-transformers`) for semantic similarity — catches contradictions even when articles use different words
- **Dynamic bias scoring:** Fine-tune a classifier on labeled news data instead of using static scores
- **More sources:** Extend `SOURCE_METADATA` with more outlets; consider adding an `"Unknown"` auto-labeling heuristic based on domain
- **Caching:** Add `@st.cache_data` decorator to `fetch_articles()` so re-running the same topic in the same session doesn't re-fetch
- **Export:** Add a download button for the contradictions as a CSV
