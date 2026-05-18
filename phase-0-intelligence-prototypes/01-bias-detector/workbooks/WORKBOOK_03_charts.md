# WORKBOOK 03 — `charts.py`
### Making data visible. Five Plotly charts with a unified dark theme.

> **Prerequisite:** `analyze_articles()` returns enriched articles. `detect_contradictions()` returns contradiction pairs. `compute_diversity_score()` returns a score dict. Now you need to make those numbers visual.

---

## 🧭 What This File Does

This file is purely presentational — it takes data in, returns Plotly `Figure` objects out. No logic, no fetching, no analysis. One function per chart. Five charts total.

This separation matters: charts.py doesn't know anything about how the data was produced. It only knows the shape of the data it receives.

---

## 📦 Step 1 — Imports & Color Palette

**Start with your imports:**
- `plotly.graph_objects as go`
- `plotly.express as px`
- `pandas as pd`
- `numpy as np`

**Then define your color palette as a dictionary called `COLORS`.**

Pick a consistent set of named colors. Use hex strings. You'll need at minimum:
- `"bg"` → the darkest background
- `"panel"` → slightly lighter (for chart backgrounds)
- `"text"` → main text color
- `"subtext"` → dimmer secondary text
- `"border"` → subtle lines
- `"accent_blue"`, `"accent_green"`, `"accent_red"`, `"accent_orange"` → highlights

**Then define two more dicts:**
- `BIAS_COLORS` → maps `"Far Left"`, `"Left-Leaning"`, `"Center"`, `"Right-Leaning"`, `"Far Right"`, `"Unknown"` to distinct colors
- `SENTIMENT_COLORS` → maps `"Positive"`, `"Neutral"`, `"Negative"` to green/yellow/red

💡 **Why define colors at the top?** Every chart shares the same palette. If you ever want to change the theme, you change it in one place. This is the "single source of truth" principle.

---

## 🔧 Step 2 — `_base_layout(title)` Helper

**Write a private helper function (underscore prefix = internal use only)** that returns a dictionary of common Plotly layout settings:
- `title` (with font color and size)
- `paper_bgcolor` and `plot_bgcolor` → set to your panel color
- `font` → monospace family, your text color
- `margin` → sensible defaults like `dict(t=45, b=30, l=30, r=30)`
- `xaxis` and `yaxis` → grid color set to your border color

Return this dict. Every chart function will use `**_base_layout("My Title")` to spread it into their layout, then override specific things on top.

💡 **Why a helper?** Without it, you'd copy-paste 15 lines of layout config into every chart. If you later decide margins should be different, you'd have to change it in 5 places.

---

## 📊 Chart 1 — `bias_distribution_chart(articles)`

**A vertical bar chart showing how many articles come from each bias category.**

Steps:
1. Convert articles to a DataFrame
2. Use `.value_counts()` on the `"bias_label"` column to count articles per category
3. Sort the categories in the correct Left→Right order (make it a `pd.Categorical`)
4. Build a `go.Bar` with x=bias labels, y=counts, and `marker_color` mapped through `BIAS_COLORS`
5. Add `text=counts` with `textposition="outside"` so counts appear above bars
6. Apply `_base_layout()` and return the figure

---

## 🔵 Chart 2 — `sentiment_bias_scatter(articles)`

**A scatter plot: x = political lean (bias_score), y = sentiment score. Each dot is an article.**

Steps:
1. Filter to articles where `bias_score is not None` (unknown sources can't be placed on the x-axis)
2. Use `px.scatter()` with `color="bias_label"` and `color_discrete_map=BIAS_COLORS`
3. Include `hover_data=["source_name", "title"]` so hovering shows the article
4. Add two reference lines: `fig.add_hline(y=0)` and `fig.add_vline(x=0)` to divide into quadrants
5. Add quadrant label annotations in the corners: "Left + Positive", "Right + Negative", etc. Use `fig.add_annotation()` with `showarrow=False`
6. Set axis ranges to `[-1.05, 1.05]` on both axes

💡 **What are you looking for in this chart?** Ideally, dots scatter across all four quadrants. If all left-leaning dots are in the bottom-left (negative sentiment) and all right-leaning in the top-right, that's a sign of confirmation bias in coverage — both sides are spinning the same story to fit their narrative.

---

## 🌡️ Chart 3 — `credibility_heatmap(articles)`

**A horizontal bar chart: each source gets one bar, colored green (high) to red (low) by credibility.**

Steps:
1. Filter to articles with a credibility score
2. Group by `"source_name"` and take the first credibility value per source (they're the same for all articles from the same source)
3. Sort ascending by credibility so the highest-credibility source is at the top
4. Use `go.Bar` with `orientation="h"`, and `marker=dict(color=credibility_values, colorscale=[[0, red], [0.5, orange], [1, green]])`
5. Add `showscale=True` with a colorbar
6. Set `height` dynamically: `max(300, len(sources) * 38)` so the chart grows with more sources

---

## ⏱️ Chart 4 — `diversity_gauge(diversity)`

**A gauge/speedometer showing the diversity score from 0 to 100.**

Steps:
1. Extract `score = diversity["score"]`
2. Pick a color: green if score ≥ 65, orange if ≥ 40, red otherwise
3. Use `go.Indicator` with `mode="gauge+number"`
4. Configure the `gauge` dict with:
   - `axis=dict(range=[0, 100])`
   - `bar=dict(color=your_color)`
   - `steps` → three background bands (red zone 0–40, yellow 40–65, green 65–100)
5. Set a fixed `height=260`

💡 **Why a gauge and not just a number?** Gauges create immediate visual intuition — at a glance you can tell if coverage is in the "danger zone" or healthy. A number alone requires mental effort to interpret.

---

## ⚡ Chart 5 — `contradiction_chart(contradictions)`

**A horizontal bar chart where each bar is a source pair, and length = sentiment divergence.**

Steps:
1. Guard: if empty list, return an empty `go.Figure()`
2. Take only the top 10 contradictions
3. Build a DataFrame with columns: `pair` (e.g. `"BBC vs Fox News"`), `divergence`, `severity`, `similarity`
4. Use `go.Bar` with `orientation="h"`, bars colored by `severity` using `SEVERITY_COLORS`
5. Set x-axis range to `[0, 2.2]` (max possible divergence is 2.0: -1.0 vs +1.0)
6. Add `customdata` for severity and similarity so the hover tooltip shows them

---

## ✅ Quick Sanity Check

You can test charts independently without the full pipeline:

```python
if __name__ == "__main__":
    # Fake minimal data
    test_articles = [
        {"bias_label": "Left-Leaning", "sentiment_score": -0.3, "bias_score": -0.2,
         "source_name": "BBC", "title": "Test", "credibility": 0.9, "region": "Global"},
        {"bias_label": "Right-Leaning", "sentiment_score": 0.5, "bias_score": 0.3,
         "source_name": "Fox", "title": "Test 2", "credibility": 0.6, "region": "Global"},
    ]
    fig = bias_distribution_chart(test_articles)
    fig.show()  # Opens in browser
```

**Common issues:**
- Chart appears but colors are wrong → check your BIAS_COLORS keys match exactly what's in the data
- Chart is blank → usually the filter (e.g. `bias_score is not None`) removed all articles
- Layout looks broken → check `_base_layout()` returns a proper dict, not a Figure

---

## 🔜 Next: WORKBOOK_04_app.py

You now have five chart functions that take data and return Figures. The final file wires everything together into a Streamlit dashboard — sidebar controls, button triggers, layout columns, and all your charts rendered in sequence.

**Concepts you'll meet there:** Streamlit's execution model, session state, `st.columns()`, `st.spinner()`, custom CSS injection with `st.markdown()`.
