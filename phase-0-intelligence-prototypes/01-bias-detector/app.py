"""
council/phase-0/01-bias-detector
app.py — Streamlit dashboard: News Bias & Contradiction Detector

Run:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd

from fetcher import fetch_articles
from analyzer import analyze_articles, detect_contradictions, compute_diversity_score
from charts import (
    bias_distribution_chart,
    sentiment_bias_scatter,
    credibility_heatmap,
    diversity_gauge,
    contradiction_chart,
)

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Council // Bias Detector",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* Base */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    /* Header */
    .council-header {
        font-family: monospace;
        font-size: 2rem;
        font-weight: 700;
        color: #58a6ff;
        letter-spacing: 0.05em;
        margin-bottom: 0;
    }
    .council-subheader {
        font-family: monospace;
        font-size: 0.85rem;
        color: #8b949e;
        margin-top: 0;
        margin-bottom: 1.5rem;
    }
    /* Metric cards */
    .metric-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 1rem 1.2rem;
        text-align: center;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        font-family: monospace;
        color: #58a6ff;
    }
    .metric-label {
        font-size: 0.75rem;
        color: #8b949e;
        font-family: monospace;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    /* Contradiction cards */
    .contradiction-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }
    .contradiction-card.high { border-left: 3px solid #f85149; }
    .contradiction-card.medium { border-left: 3px solid #d29922; }
    .contradiction-card.low { border-left: 3px solid #58a6ff; }
    .severity-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-family: monospace;
        font-weight: 700;
        letter-spacing: 0.05em;
    }
    .badge-high { background: #3d1a1a; color: #f85149; }
    .badge-medium { background: #2d2010; color: #d29922; }
    .badge-low { background: #1a2535; color: #58a6ff; }
    /* Section divider */
    .section-title {
        font-family: monospace;
        font-size: 0.8rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        border-bottom: 1px solid #30363d;
        padding-bottom: 0.4rem;
        margin: 1.5rem 0 1rem 0;
    }
    /* Hide Streamlit branding */
    #MainMenu, footer { visibility: hidden; }
    .stDeployButton { display: none; }
</style>
""", unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────

st.markdown('<p class="council-header">⚡ COUNCIL</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="council-subheader">// PHASE 0 · PROTOTYPE 01 · NEWS BIAS & CONTRADICTION DETECTOR</p>',
    unsafe_allow_html=True,
)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🔍 Query Parameters")

    topic = st.text_input(
        "Topic",
        value="India economy",
        placeholder="e.g. India elections, AI regulation, Ukraine...",
        help="Enter any topic — Council will fetch and analyze live news coverage.",
    )

    days_back = st.slider("Days back", min_value=1, max_value=7, value=3,
                          help="How many days of news to analyze")

    max_articles = st.slider("Max articles", min_value=10, max_value=60, value=30,
                             help="More articles = richer analysis but slower")

    st.markdown("---")
    st.markdown("### ⚙️ Analysis Settings")

    contradiction_threshold = st.slider(
        "Contradiction sensitivity",
        min_value=0.1, max_value=0.8, value=0.25, step=0.05,
        help="Lower = more contradictions detected; Higher = only strong divergences",
    )

    show_unknown_bias = st.checkbox("Include unknown-bias sources", value=True)

    st.markdown("---")
    st.markdown(
        """
        <div style="font-family:monospace;font-size:0.7rem;color:#8b949e;line-height:1.8;">
        <b style="color:#58a6ff">COUNCIL</b> · Phase 0<br>
        Prototype 01: Bias Detector<br>
        Feeds into: Analyzer Agent<br>
        <a href="https://github.com/aura-autumn/council" 
           style="color:#3fb950">github.com/council</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    analyze_btn = st.button("⚡ ANALYZE", use_container_width=True, type="primary")


# ── Main content ──────────────────────────────────────────────────────────────

if not analyze_btn:
    st.markdown("""
    <div style="
        background:#161b22;
        border:1px solid #30363d;
        border-radius:8px;
        padding:2rem;
        margin-top:2rem;
        font-family:monospace;
        color:#8b949e;
        text-align:center;
    ">
        <div style="font-size:2rem;margin-bottom:1rem">⚡</div>
        <div style="font-size:1rem;color:#c9d1d9;margin-bottom:0.5rem">
            Enter a topic and press <b style="color:#58a6ff">ANALYZE</b>
        </div>
        <div style="font-size:0.8rem;line-height:1.8">
            Council will fetch live news · detect political lean · surface contradictions<br>
            score source diversity · and show you what the full media landscape looks like
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ── Fetch & analyze ───────────────────────────────────────────────────────────

with st.spinner(f"Fetching coverage for **{topic}**..."):
    try:
        raw_articles = fetch_articles(topic, days_back=days_back, max_articles=max_articles)
    except Exception as e:
        st.error(f"Failed to fetch articles: {e}")
        st.stop()

if not raw_articles:
    st.warning("No articles found for this topic and timeframe. Try broadening the query.")
    st.stop()

with st.spinner("Running sentiment & bias analysis..."):
    articles = analyze_articles(raw_articles)

if not show_unknown_bias:
    articles = [a for a in articles if a["bias_score"] is not None]

with st.spinner("Detecting contradictions..."):
    contradictions = detect_contradictions(articles, threshold=contradiction_threshold)

diversity = compute_diversity_score(articles)


# ── Top metrics row ───────────────────────────────────────────────────────────

st.markdown(f'<p class="section-title">Intelligence Summary · "{topic}"</p>', unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

metrics = [
    (col1, str(len(articles)), "Articles Analyzed"),
    (col2, str(len(set(a["source_name"] for a in articles))), "Unique Sources"),
    (col3, str(len(contradictions)), "Contradictions"),
    (col4, f"{diversity['score']:.0f}/100", "Diversity Score"),
    (col5, f"{diversity['credibility_avg']:.2f}", "Avg Credibility"),
]

for col, value, label in metrics:
    with col:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-value">{value}</div>'
            f'<div class="metric-label">{label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── Charts row 1 ──────────────────────────────────────────────────────────────

st.markdown('<p class="section-title">Bias & Sentiment Analysis</p>', unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1])

with col_left:
    st.plotly_chart(bias_distribution_chart(articles), use_container_width=True)

with col_right:
    st.plotly_chart(sentiment_bias_scatter(articles), use_container_width=True)


# ── Charts row 2 ──────────────────────────────────────────────────────────────

col_gauge, col_cred = st.columns([1, 1.4])

with col_gauge:
    st.plotly_chart(diversity_gauge(diversity), use_container_width=True)

    # Diversity breakdown
    st.markdown("**Score Breakdown**")
    for component, score in diversity["breakdown"].items():
        max_score = {"Source Variety": 30, "Bias Spread": 35, "Regional Mix": 15, "Credibility": 20}
        pct = score / max_score[component]
        color = "#3fb950" if pct > 0.6 else "#d29922" if pct > 0.35 else "#f85149"
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;'
            f'font-family:monospace;font-size:0.8rem;margin-bottom:4px;">'
            f'<span style="color:#8b949e">{component}</span>'
            f'<span style="color:{color}">{score:.1f} / {max_score[component]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.progress(pct)

with col_cred:
    st.plotly_chart(credibility_heatmap(articles), use_container_width=True)


# ── Contradictions ────────────────────────────────────────────────────────────

st.markdown('<p class="section-title">Detected Contradictions</p>', unsafe_allow_html=True)

if not contradictions:
    st.info("No significant contradictions detected for this topic and sensitivity setting.")
else:
    col_chart, col_cards = st.columns([1, 1])

    with col_chart:
        st.plotly_chart(contradiction_chart(contradictions), use_container_width=True)

    with col_cards:
        for c in contradictions[:6]:
            severity_class = c["severity"].lower()
            badge_class = f"badge-{severity_class}"
            st.markdown(
                f"""
                <div class="contradiction-card {severity_class}">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem">
                        <span style="font-family:monospace;font-size:0.7rem;color:#8b949e">
                            Content similarity: {c['content_similarity']:.2f}
                        </span>
                        <span class="severity-badge {badge_class}">{c['severity'].upper()}</span>
                    </div>
                    <div style="margin-bottom:0.4rem">
                        <span style="color:#58a6ff;font-family:monospace;font-size:0.75rem">
                            {c['article_a']['source']}
                        </span>
                        <span style="color:#8b949e;font-family:monospace;font-size:0.7rem">
                             [{c['article_a']['bias_label']}] · {c['article_a']['sentiment']}
                        </span>
                        <div style="font-size:0.8rem;color:#c9d1d9;margin-top:2px">
                            <a href="{c['article_a']['url']}" target="_blank"
                               style="color:#c9d1d9;text-decoration:none">
                                {c['article_a']['title'][:80]}{"..." if len(c['article_a']['title']) > 80 else ""}
                            </a>
                        </div>
                    </div>
                    <div style="color:#30363d;font-family:monospace;font-size:0.75rem;margin:0.3rem 0">
                        ── vs ──
                    </div>
                    <div>
                        <span style="color:#f85149;font-family:monospace;font-size:0.75rem">
                            {c['article_b']['source']}
                        </span>
                        <span style="color:#8b949e;font-family:monospace;font-size:0.7rem">
                             [{c['article_b']['bias_label']}] · {c['article_b']['sentiment']}
                        </span>
                        <div style="font-size:0.8rem;color:#c9d1d9;margin-top:2px">
                            <a href="{c['article_b']['url']}" target="_blank"
                               style="color:#c9d1d9;text-decoration:none">
                                {c['article_b']['title'][:80]}{"..." if len(c['article_b']['title']) > 80 else ""}
                            </a>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ── Raw data table ────────────────────────────────────────────────────────────

with st.expander("📋 Raw Article Data", expanded=False):
    df_display = pd.DataFrame(articles)[
        ["title", "source_name", "bias_label", "sentiment_label",
         "credibility", "region", "published_at", "url"]
    ].rename(columns={
        "source_name": "Source",
        "bias_label": "Bias",
        "sentiment_label": "Sentiment",
        "credibility": "Credibility",
        "published_at": "Published",
    })
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "url": st.column_config.LinkColumn("URL"),
            "Credibility": st.column_config.ProgressColumn(
                "Credibility", min_value=0, max_value=1, format="%.2f"
            ),
        },
    )
