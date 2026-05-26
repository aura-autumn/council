"""
app.py — Council · Prototype 02: Relevance Engine
Streamlit dashboard for personalised article scoring.

Run:
    streamlit run app.py
"""

import streamlit as st
import time
import json
import pandas as pd
from pathlib import Path

from user_profile import UserProfile, INTEREST_CATEGORIES, ALL_INTERESTS
from fetcher import fetch_articles, Article
from scorer import score_articles, compute_feed_stats
import charts

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Council · Relevance Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS (cyberpunk) ─────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&display=swap');

  html, body, [class*="css"] {
    background-color: #0a0a0f !important;
    color: #e0e0ff !important;
    font-family: 'Share Tech Mono', monospace !important;
  }

  /* Header */
  .council-header {
    text-align: center;
    padding: 1.5rem 0 0.5rem;
    border-bottom: 1px solid #1a1a2e;
    margin-bottom: 1.5rem;
  }
  .council-title {
    font-family: 'Orbitron', monospace;
    font-size: 2.2rem;
    font-weight: 900;
    letter-spacing: 0.2em;
    color: #00f5ff;
    text-shadow: 0 0 20px rgba(0,245,255,0.4);
  }
  .council-sub {
    color: #6060a0;
    font-size: 0.85rem;
    letter-spacing: 0.1em;
    margin-top: 0.25rem;
  }

  /* Metric cards */
  .metric-card {
    background: #0f0f1a;
    border: 1px solid #1a1a2e;
    border-left: 3px solid #00f5ff;
    border-radius: 4px;
    padding: 1rem 1.25rem;
    text-align: center;
  }
  .metric-value {
    font-family: 'Orbitron', monospace;
    font-size: 1.8rem;
    font-weight: 700;
    color: #00f5ff;
  }
  .metric-label {
    font-size: 0.7rem;
    color: #6060a0;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-top: 0.2rem;
  }

  /* Article card */
  .article-card {
    background: #0f0f1a;
    border: 1px solid #1a1a2e;
    border-radius: 6px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.2s;
  }
  .article-card:hover { border-color: #00f5ff; }
  .article-title {
    font-size: 0.95rem;
    color: #e0e0ff;
    font-weight: 600;
    margin-bottom: 0.25rem;
  }
  .article-meta {
    font-size: 0.72rem;
    color: #6060a0;
    letter-spacing: 0.05em;
  }
  .score-badge {
    display: inline-block;
    padding: 0.1rem 0.5rem;
    border-radius: 2px;
    font-family: 'Orbitron', monospace;
    font-size: 0.75rem;
    font-weight: 700;
  }
  .score-high  { background: rgba(57,255,20,0.15);  color: #39ff14; border: 1px solid #39ff14; }
  .score-med   { background: rgba(0,245,255,0.10);  color: #00f5ff; border: 1px solid #00f5ff; }
  .score-low   { background: rgba(255,110,0,0.10);  color: #ff6e00; border: 1px solid #ff6e00; }
  .score-noise { background: rgba(255,45,107,0.10); color: #ff2d6b; border: 1px solid #ff2d6b; }

  .topic-tag {
    display: inline-block;
    background: rgba(0,245,255,0.08);
    color: #00f5ff;
    border: 1px solid rgba(0,245,255,0.2);
    border-radius: 2px;
    padding: 0.05rem 0.4rem;
    font-size: 0.65rem;
    margin: 0.1rem;
    letter-spacing: 0.04em;
  }

  /* Section headers */
  .section-header {
    font-family: 'Orbitron', monospace;
    font-size: 0.8rem;
    letter-spacing: 0.15em;
    color: #00f5ff;
    text-transform: uppercase;
    border-bottom: 1px solid #1a1a2e;
    padding-bottom: 0.4rem;
    margin: 1.5rem 0 0.75rem;
  }

  /* Onboarding box */
  .onboarding-box {
    background: linear-gradient(135deg, #0f0f1a 0%, #0a0a1a 100%);
    border: 1px solid rgba(0,245,255,0.2);
    border-radius: 8px;
    padding: 1.5rem;
    text-align: center;
  }

  /* Streamlit widget overrides */
  .stSlider > div > div { background: #1a1a2e !important; }
  div[data-baseweb="slider"] > div { background: #00f5ff !important; }
  .stTextInput > div > div > input {
    background: #0f0f1a !important;
    border: 1px solid #1a1a2e !important;
    color: #e0e0ff !important;
    font-family: 'Share Tech Mono', monospace !important;
  }
  .stButton > button {
    background: transparent !important;
    border: 1px solid #00f5ff !important;
    color: #00f5ff !important;
    font-family: 'Orbitron', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.08em !important;
    padding: 0.4rem 1rem !important;
  }
  .stButton > button:hover {
    background: rgba(0,245,255,0.1) !important;
    box-shadow: 0 0 12px rgba(0,245,255,0.3) !important;
  }
  .stSelectbox > div > div {
    background: #0f0f1a !important;
    border: 1px solid #1a1a2e !important;
    color: #e0e0ff !important;
  }
  .stExpander {
    background: #0f0f1a !important;
    border: 1px solid #1a1a2e !important;
  }
  div[data-testid="stSidebar"] {
    background: #070710 !important;
    border-right: 1px solid #1a1a2e !important;
  }
  div[data-testid="metric-container"] {
    background: #0f0f1a !important;
    border: 1px solid #1a1a2e !important;
    border-radius: 4px !important;
    padding: 0.5rem !important;
  }
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
if "profile" not in st.session_state:
    st.session_state.profile = UserProfile.load()
if "articles" not in st.session_state:
    st.session_state.articles = []
if "onboarding_done" not in st.session_state:
    st.session_state.onboarding_done = bool(st.session_state.profile.interests)
if "last_query" not in st.session_state:
    st.session_state.last_query = ""


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="council-header">
  <div class="council-title">⚡ COUNCIL</div>
  <div class="council-sub">PROTOTYPE 02 · RELEVANCE ENGINE · COSINE SIMILARITY + USER EMBEDDINGS</div>
</div>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-header">SYSTEM</div>', unsafe_allow_html=True)

    profile = st.session_state.profile
    completeness = profile.profile_completeness()

    st.progress(completeness, text=f"Profile: {completeness*100:.0f}% complete")

    if profile.top_interests(n=3):
        st.markdown("**Top interests:**")
        for topic, weight in profile.top_interests(n=5):
            st.markdown(f"`{weight:.2f}` {topic}")

    st.markdown('<div class="section-header">SETTINGS</div>', unsafe_allow_html=True)

    region_focus = st.selectbox(
        "Region focus",
        ["both", "india", "global"],
        index=["both", "india", "global"].index(profile.region_focus),
        key="region_select",
    )
    profile.region_focus = region_focus

    expertise = st.selectbox(
        "Expertise level",
        ["beginner", "intermediate", "expert"],
        index=["beginner", "intermediate", "expert"].index(profile.expertise_level),
        key="expertise_select",
    )
    profile.expertise_level = expertise

    depth = st.selectbox(
        "Preferred depth",
        ["quick", "balanced", "deep-dive"],
        index=["quick", "balanced", "deep-dive"].index(profile.preferred_depth),
        key="depth_select",
    )
    profile.preferred_depth = depth

    st.markdown("---")
    if st.button("↩ Reset Profile"):
        st.session_state.profile = UserProfile()
        st.session_state.onboarding_done = False
        st.session_state.articles = []
        UserProfile().save()
        st.rerun()

    st.markdown(
        '<div style="color:#3a3a5c;font-size:0.65rem;margin-top:2rem;text-align:center;">'
        'council · prototype 02<br>part of the council intelligence platform'
        '</div>',
        unsafe_allow_html=True,
    )


# ── Onboarding ────────────────────────────────────────────────────────────────
if not st.session_state.onboarding_done:
    st.markdown('<div class="section-header">◈ CALIBRATE YOUR INTELLIGENCE FEED</div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#6060a0;font-size:0.85rem;margin-bottom:1.5rem;">'
        'Set interest weights so Council knows what matters to you. Drag each slider — '
        '0 = ignore, 1 = always surface.</p>',
        unsafe_allow_html=True,
    )

    interests_draft: dict = {}

    for category, topics in INTEREST_CATEGORIES.items():
        with st.expander(f"📂 {category}", expanded=False):
            cols = st.columns(2)
            for i, topic in enumerate(topics):
                with cols[i % 2]:
                    val = st.slider(
                        topic,
                        min_value=0.0, max_value=1.0, step=0.05,
                        value=st.session_state.profile.interests.get(topic, 0.0),
                        key=f"onboard_{topic}",
                    )
                    interests_draft[topic] = val

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        goal_input = st.text_input(
            "What's your main goal? (optional)",
            value=profile.goal,
            placeholder="e.g. Stay sharp on AI and Indian macro for my next role",
            key="goal_input",
        )

    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_b:
        if st.button("⚡  SAVE PROFILE & ENTER", use_container_width=True):
            profile.interests = interests_draft
            profile.goal = goal_input
            profile.save()
            st.session_state.onboarding_done = True
            st.rerun()

    st.stop()


# ── Main dashboard ────────────────────────────────────────────────────────────
profile = st.session_state.profile

# Search bar
st.markdown('<div class="section-header">◈ INTELLIGENCE QUERY</div>', unsafe_allow_html=True)
col_q, col_btn = st.columns([5, 1])
with col_q:
    query = st.text_input(
        "Topic",
        value=st.session_state.last_query,
        placeholder="e.g.  AI regulation  /  RBI policy  /  India startup funding",
        label_visibility="collapsed",
        key="search_query",
    )
with col_btn:
    run_search = st.button("⚡ SCAN", use_container_width=True)

# Quick topics
st.markdown(
    '<div style="margin-top:0.3rem;margin-bottom:1rem;">'
    '<span style="color:#3a3a5c;font-size:0.7rem;letter-spacing:0.08em;">QUICK SCAN → </span>',
    unsafe_allow_html=True,
)
quick_cols = st.columns(7)
quick_topics = ["Artificial Intelligence", "Indian Markets", "Climate", "Geopolitics", "Startups", "Cybersecurity", "Space"]
for i, qt in enumerate(quick_topics):
    with quick_cols[i]:
        if st.button(qt, key=f"qt_{qt}"):
            st.session_state.last_query = qt
            run_search = True
            query = qt
st.markdown("</div>", unsafe_allow_html=True)


# ── Fetch & score ─────────────────────────────────────────────────────────────
if run_search and query.strip():
    st.session_state.last_query = query
    with st.spinner("⚡ Scanning intelligence streams…"):
        try:
            articles = fetch_articles(
                query=query,
                max_articles=60,
                region_focus=profile.region_focus,
            )
            if not articles:
                st.warning("No articles returned. Check your NewsAPI key or try a different query.")
            else:
                articles = score_articles(articles, profile, query=query)
                st.session_state.articles = articles
                st.success(f"✓ {len(articles)} articles scored")
        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Fetch error: {e}")

articles = st.session_state.articles

if not articles:
    st.markdown(
        '<div class="onboarding-box" style="margin-top:3rem;">'
        '<div style="font-family:Orbitron,monospace;color:#00f5ff;font-size:1.1rem;margin-bottom:0.5rem;">AWAITING QUERY</div>'
        '<div style="color:#6060a0;font-size:0.85rem;">Enter a topic above to score and rank articles against your profile.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.stop()


# ── Metrics row ───────────────────────────────────────────────────────────────
stats = compute_feed_stats(articles)

st.markdown('<div class="section-header">◈ FEED METRICS</div>', unsafe_allow_html=True)
m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-value">{len(articles)}</div>
      <div class="metric-label">Articles Scored</div>
    </div>""", unsafe_allow_html=True)
with m2:
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-value">{stats.get('mean_relevance', 0):.2f}</div>
      <div class="metric-label">Avg Relevance</div>
    </div>""", unsafe_allow_html=True)
with m3:
    pct = stats.get("high_relevance_pct", 0) * 100
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-value">{pct:.0f}%</div>
      <div class="metric-label">High Relevance</div>
    </div>""", unsafe_allow_html=True)
with m4:
    top = articles[0].relevance_score if articles else 0
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-value">{top:.2f}</div>
      <div class="metric-label">Peak Score</div>
    </div>""", unsafe_allow_html=True)
with m5:
    n_topics = len({t for a in articles for t in a.matched_topics})
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-value">{n_topics}</div>
      <div class="metric-label">Topics Matched</div>
    </div>""", unsafe_allow_html=True)


# ── Two-column layout: Feed + Charts ─────────────────────────────────────────
feed_col, chart_col = st.columns([1, 1], gap="medium")

with feed_col:
    st.markdown('<div class="section-header">◈ RANKED FEED</div>', unsafe_allow_html=True)

    # Filter controls
    fc1, fc2 = st.columns(2)
    with fc1:
        tier_filter = st.selectbox(
            "Min tier",
            ["All", "High (≥0.5)", "Medium (≥0.3)", "Low (≥0.15)"],
            key="tier_filter",
        )
    with fc2:
        show_n = st.slider("Show top N", 5, min(60, len(articles)), min(20, len(articles)), key="show_n")

    tier_map = {
        "All": 0.0,
        "High (≥0.5)": 0.5,
        "Medium (≥0.3)": 0.3,
        "Low (≥0.15)": 0.15,
    }
    min_score = tier_map[tier_filter]
    filtered = [a for a in articles if a.relevance_score >= min_score][:show_n]

    if not filtered:
        st.info("No articles match the selected tier filter.")
    else:
        for article in filtered:
            s = article.relevance_score
            if s >= 0.5:
                badge_class, tier_label = "score-high", "HIGH"
            elif s >= 0.3:
                badge_class, tier_label = "score-med", "MED"
            elif s >= 0.15:
                badge_class, tier_label = "score-low", "LOW"
            else:
                badge_class, tier_label = "score-noise", "NOISE"

            topics_html = " ".join(
                f'<span class="topic-tag">{t}</span>'
                for t in article.matched_topics[:4]
            )
            age_str = f"{article.age_hours:.0f}h ago" if article.age_hours < 168 else "7d+ ago"

            st.markdown(f"""
            <div class="article-card">
              <div class="article-title">{article.title[:100]}</div>
              <div class="article-meta">
                {article.source} · {age_str} · Credibility: {article.credibility:.2f}
              </div>
              <div style="margin-top:0.4rem;">
                <span class="score-badge {badge_class}">{tier_label} {s:.2f}</span>
                {topics_html}
              </div>
              <div style="margin-top:0.3rem;">
                <a href="{article.url}" target="_blank"
                   style="color:#3a3a5c;font-size:0.7rem;text-decoration:none;">
                  ↗ Read →
                </a>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Feedback buttons
            fb_cols = st.columns(4)
            actions = [("✓ Read", "read"), ("⭐ Save", "save"), ("↓ Skip", "skip"), ("✗ Dislike", "dislike")]
            for col, (label, action) in zip(fb_cols, actions):
                with col:
                    if st.button(label, key=f"fb_{article.id}_{action}"):
                        profile.record_interaction(article.matched_topics, action)
                        profile.save()
                        st.toast(f"Feedback recorded: {action}", icon="⚡")


with chart_col:
    st.markdown('<div class="section-header">◈ ANALYTICS</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Score Dist", "Topics", "Matrix", "Decay"])

    with tab1:
        st.plotly_chart(charts.score_distribution(articles), use_container_width=True)
        st.plotly_chart(charts.profile_radar(profile), use_container_width=True)

    with tab2:
        st.plotly_chart(charts.topic_frequency(articles), use_container_width=True)
        st.plotly_chart(charts.interest_heatmap(profile), use_container_width=True)

    with tab3:
        st.plotly_chart(charts.relevance_credibility_scatter(articles), use_container_width=True)

    with tab4:
        st.plotly_chart(charts.cumulative_relevance(articles), use_container_width=True)


# ── Edit Profile inline ───────────────────────────────────────────────────────
with st.expander("⚙ Edit Interest Profile"):
    st.markdown(
        '<p style="color:#6060a0;font-size:0.8rem;margin-bottom:1rem;">'
        'Adjust weights. Changes apply immediately to the next scan.</p>',
        unsafe_allow_html=True,
    )
    for category, topics in INTEREST_CATEGORIES.items():
        st.markdown(f'<div style="color:#00f5ff;font-size:0.75rem;margin:0.75rem 0 0.25rem;">{category}</div>', unsafe_allow_html=True)
        cols = st.columns(3)
        for i, topic in enumerate(topics):
            with cols[i % 3]:
                new_val = st.slider(
                    topic, 0.0, 1.0, step=0.05,
                    value=float(profile.interests.get(topic, 0.0)),
                    key=f"edit_{topic}",
                )
                profile.interests[topic] = new_val
    if st.button("💾 Save Profile"):
        profile.save()
        st.success("Profile saved.")


# ── Export ────────────────────────────────────────────────────────────────────
with st.expander("📤 Export Feed"):
    df = pd.DataFrame([{
        "title": a.title,
        "source": a.source,
        "relevance": a.relevance_score,
        "credibility": a.credibility,
        "bias": a.bias_score,
        "topics": ", ".join(a.matched_topics),
        "url": a.url,
        "published_at": a.published_at,
    } for a in articles])

    csv = df.to_csv(index=False)
    st.download_button(
        label="⬇ Download CSV",
        data=csv,
        file_name=f"council_feed_{st.session_state.last_query.replace(' ','_')}.csv",
        mime="text/csv",
    )
    st.dataframe(
        df[["title", "source", "relevance", "topics"]].head(20),
        use_container_width=True,
        hide_index=True,
    )
