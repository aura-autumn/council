import streamlit as st
import streamlit.components.v1 as components
from fetcher import fetch_articles
from extractor import extract_entities_from_articles
from graph_builder import build_graph
from charts import render_pyvis_graph

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Council · Topic Connection Graph",
    page_icon="⚡",
    layout="wide",
)

# ── Cyberpunk CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght=400;700&display=swap');

html, body, [class*="css"] {
    background-color: #0a0a0f !important;
    color: #e0e0e0 !important;
    font-family: 'Share Tech Mono', monospace !important;
}

h1, h2, h3 { font-family: 'Orbitron', monospace !important; }

.stButton > button {
    background: transparent;
    border: 1px solid #00f5ff;
    color: #00f5ff;
    font-family: 'Share Tech Mono', monospace;
    letter-spacing: 1px;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: #00f5ff22;
    box-shadow: 0 0 12px #00f5ff66;
}

.stTextInput > div > div > input {
    background-color: #0f0f1a !important;
    border: 1px solid #bf00ff !important;
    color: #e0e0e0 !important;
    font-family: 'Share Tech Mono', monospace !important;
}

.metric-card {
    background: #0f0f1a;
    border: 1px solid #bf00ff44;
    border-radius: 6px;
    padding: 16px 20px;
    margin-bottom: 10px;
}
.metric-label {
    font-size: 11px;
    color: #888;
    letter-spacing: 2px;
    text-transform: uppercase;
}
.metric-value {
    font-size: 28px;
    color: #00f5ff;
    font-family: 'Orbitron', monospace;
    margin-top: 4px;
}

.hidden-card {
    background: #0f0f1a;
    border-left: 3px solid #ff6600;
    padding: 12px 16px;
    margin-bottom: 8px;
    border-radius: 0 6px 6px 0;
}
.hidden-card .pair {
    font-size: 15px;
    color: #00f5ff;
}
.hidden-card .meta {
    font-size: 11px;
    color: #888;
    margin-top: 4px;
}

.entity-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 11px;
    margin: 2px;
    font-family: 'Share Tech Mono', monospace;
}

.legend-dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 6px;
}

.stSpinner > div { border-top-color: #00f5ff !important; }

hr { border-color: #bf00ff33 !important; }

.stSelectbox > div > div { background-color: #0f0f1a !important; border: 1px solid #bf00ff !important; }

section[data-testid="stSidebar"] {
    background-color: #0a0a0f !important;
    border-right: 1px solid #bf00ff33;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<h1 style='color:#00f5ff; letter-spacing:3px; margin-bottom:0;'>⚡ COUNCIL</h1>
<p style='color:#bf00ff; font-size:13px; letter-spacing:4px; margin-top:4px;'>
PROTOTYPE 03 · TOPIC CONNECTION GRAPH
</p>
<p style='color:#666; font-size:12px;'>
Map hidden connections between entities across live news. Node size = centrality. 
Color = community cluster. Edge thickness = co-occurrence strength.
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<p style='color:#00f5ff; letter-spacing:2px; font-size:13px;'>⚙ PARAMETERS</p>", unsafe_allow_html=True)

    max_articles = st.slider("Max articles to fetch", 10, 40, 30, step=5)
    top_entities = st.slider("Max entities in graph", 10, 30, 20, step=5)
    min_cooccurrence = st.slider("Min co-occurrence to show edge", 1, 5, 1)

    st.markdown("---")
    st.markdown("""
<p style='color:#666; font-size:11px; line-height:1.6;'>
<b style='color:#bf00ff;'>Node size</b> → PageRank centrality<br>
<b style='color:#bf00ff;'>Node color</b> → Community cluster<br>
<b style='color:#bf00ff;'>Edge thickness</b> → Co-occurrence count<br>
<b style='color:#bf00ff;'>Hidden connections</b> → High co-occurrence, low individual frequency
</p>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
<p style='color:#444; font-size:10px;'>
Council · Phase 0 · Prototype 03<br>
spaCy · NetworkX · Louvain · pyvis
</p>
""", unsafe_allow_html=True)

# ── Search bar ────────────────────────────────────────────────────────────────
col_input, col_btn = st.columns([5, 1])
with col_input:
    topic = st.text_input(
        "Topic",
        placeholder="Enter a topic — e.g. India interest rates, Gaza ceasefire, OpenAI ...",
        label_visibility="collapsed",
    )
with col_btn:
    run = st.button("ANALYZE", use_container_width=True)

# Quick scan buttons
st.markdown("<p style='color:#444; font-size:11px; margin-bottom:4px;'>QUICK SCAN</p>", unsafe_allow_html=True)
qcols = st.columns(5)
quick_topics = ["India economy", "AI regulation", "Gaza", "US elections", "Climate 2025"]
for i, qt in enumerate(quick_topics):
    if qcols[i].button(qt, key=f"q_{i}"):
        topic = qt
        run = True

st.markdown("---")

# ── Main pipeline ─────────────────────────────────────────────────────────────
if run and topic:
    with st.spinner(f"Fetching articles for **{topic}** ..."):
        try:
            articles = fetch_articles(topic, max_articles=max_articles)
        except Exception as e:
            st.error(f"NewsAPI error: {e}")
            st.stop()

    if not articles:
        st.warning("No articles returned. Try a different topic or check your API key.")
        st.stop()

    with st.spinner("Extracting entities with spaCy ..."):
        extraction = extract_entities_from_articles(articles, top_n=top_entities)

    if not extraction["entities"]:
        st.warning("No named entities found. Try a more specific topic.")
        st.stop()

    with st.spinner("Building connection graph ..."):
        graph_data = build_graph(extraction)

    G = graph_data["graph"]

    # Filter edges below min co-occurrence
    edges_to_remove = [
        (u, v) for u, v, d in G.edges(data=True)
        if d.get("weight", 1) < min_cooccurrence
    ]
    G.remove_edges_from(edges_to_remove)

    # ── Metrics row ───────────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.markdown(f"""
<div class='metric-card'>
<div class='metric-label'>Articles Analysed</div>
<div class='metric-value'>{len(articles)}</div>
</div>""", unsafe_allow_html=True)

    with m2:
        st.markdown(f"""
<div class='metric-card'>
<div class='metric-label'>Entities Mapped</div>
<div class='metric-value'>{len(G.nodes)}</div>
</div>""", unsafe_allow_html=True)

    with m3:
        st.markdown(f"""
<div class='metric-card'>
<div class='metric-label'>Connections</div>
<div class='metric-value'>{len(G.edges)}</div>
</div>""", unsafe_allow_html=True)

    with m4:
        n_communities = len(set(graph_data["communities"].values()))
        st.markdown(f"""
<div class='metric-card'>
<div class='metric-label'>Clusters Found</div>
<div class='metric-value'>{n_communities}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Graph + Hidden Connections side by side ───────────────────────────────
    graph_col, insight_col = st.columns([3, 1])

    with graph_col:
        st.markdown("<p style='color:#00f5ff; letter-spacing:2px; font-size:12px;'>ENTITY CONNECTION GRAPH</p>", unsafe_allow_html=True)
        html_content = render_pyvis_graph(graph_data, height="560px")
        components.html(html_content, height=580, scrolling=False)

    with insight_col:
        st.markdown("<p style='color:#ff6600; letter-spacing:2px; font-size:12px;'>HIDDEN CONNECTIONS</p>", unsafe_allow_html=True)
        st.markdown("<p style='color:#555; font-size:11px;'>Pairs with unexpectedly high co-occurrence — signal, not noise.</p>", unsafe_allow_html=True)

        hidden = graph_data["hidden_connections"]
        if hidden:
            for hc in hidden[:8]:
                surprise = hc["surprise_score"]
                bar_width = min(int(surprise * 300), 100)
                st.markdown(f"""
<div class='hidden-card'>
<div class='pair'>⟡ {hc['entity_a']} × {hc['entity_b']}</div>
<div style='background:#ff660022; border-radius:2px; height:3px; margin:6px 0;'>
  <div style='background:#ff6600; width:{bar_width}%; height:3px; border-radius:2px;'></div>
</div>
<div class='meta'>
  Co-occurs: {hc['co_occurrences']}x &nbsp;|&nbsp; Surprise: {surprise:.3f}
</div>
</div>""", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#444; font-size:12px;'>No strong hidden connections found for this topic.</p>", unsafe_allow_html=True)

    # ── ADDED: DEEP ANALYSIS INTERACTIVE REFERENCE EXPLORER ───────────────────
    st.markdown("---")
    st.markdown("<h3 style='color:#00f5ff; letter-spacing:2px;'>🔎 DEEP ANALYSIS PATHWAY</h3>", unsafe_allow_html=True)
    
    edge_options = [f"{u} ── {v}" for u, v in G.edges()]
    
    if edge_options:
        selected_edge = st.selectbox(
            "Select a specific connection path to investigate underlying intelligence vectors:",
            options=sorted(edge_options)
        )
        
        if selected_edge:
            node_a, node_b = selected_edge.split(" ── ")
            edge_data = G.get_edge_data(node_a, node_b)
            shared_articles = edge_data.get("articles", [])
            
            exp_col, art_col = st.columns([1, 1])
            
            with exp_col:
                st.markdown(f"<p style='color:#bf00ff; font-size:12px; letter-spacing:2px;'>INTELLIGENCE PROMPT EXPLANATION</p>", unsafe_allow_html=True)
                st.write(f"**Path Anchor:** `{node_a}` links to `{node_b}` across **{edge_data.get('weight')}** unique intelligence intercepts.")
                
                # Rule-based semantic reasoning explaining the connection context
                if shared_articles:
                    sample_text = shared_articles[0]["text"]
                    st.info(
                        f"🔹 **Context Evaluation:** `{node_a}` and `{node_b}` intersect structurally within the news feed cluster targeting **'{topic}'**. "
                        f"The primary convergence occurs within segments highlighting *\"{shared_articles[0]['title']}\"*. "
                        f"This co-occurrence indicates a shared operational ecosystem, cross-organizational dependency, or common narrative alignment."
                    )
                else:
                    st.warning("No explicit text fragments shared between components in filtered arrays.")
                    
            with art_col:
                st.markdown(f"<p style='color:#00f5ff; font-size:12px; letter-spacing:2px;'>SOURCE DOSSIERS ({len(shared_articles)})</p>", unsafe_allow_html=True)
                for index, art in enumerate(shared_articles):
                    with st.expander(f"📄 {art['source']} — {art['title'][:60]}..."):
                        st.markdown(f"**Full Captured Metadata Content Block:**")
                        st.markdown(f"<i style='color:#888;'>\"{art['text']}\"</i>", unsafe_allow_html=True)
                        st.markdown("---")
                        st.markdown(f"[🔗 Open Original Intel Stream Link]({art['url']})")
    else:
        st.info("No active edge links available under current slider filter constraints.")

    st.markdown("---")

    # ── Entity roster ─────────────────────────────────────────────────────────
    st.markdown("<p style='color:#00f5ff; letter-spacing:2px; font-size:12px;'>ENTITY ROSTER</p>", unsafe_allow_html=True)

    TYPE_COLORS = {
        "PERSON":  ("#00f5ff", "#00f5ff22"),
        "ORG":     ("#bf00ff", "#bf00ff22"),
        "GPE":     ("#00ff88", "#00ff8822"),
        "EVENT":   ("#ff6600", "#ff660022"),
        "NORP":    ("#ffcc00", "#ffcc0022"),
        "FAC":     ("#ff0066", "#ff006622"),
        "PRODUCT": ("#99ccff", "#99ccff22"),
    }

    pagerank = graph_data["pagerank"]
    sorted_entities = sorted(
        extraction["entities"],
        key=lambda e: -pagerank.get(e["name"], 0)
    )

    # Legend
    legend_html = ""
    for etype, (fg, bg) in TYPE_COLORS.items():
        legend_html += f"<span style='color:{fg}; font-size:11px; margin-right:12px;'><span style='background:{fg}; border-radius:50%; display:inline-block; width:8px; height:8px; margin-right:4px;'></span>{etype}</span>"
    st.markdown(f"<div style='margin-bottom:10px;'>{legend_html}</div>", unsafe_allow_html=True)

    # Render entity badges in rows
    badges_html = ""
    for ent in sorted_entities:
        etype = ent["type"]
        fg, bg = TYPE_COLORS.get(etype, ("#aaa", "#aaa22"))
        pr = pagerank.get(ent["name"], 0)
        badges_html += f"""
<span style='display:inline-block; border:1px solid {fg}; background:{bg}; 
color:{fg}; padding:4px 10px; border-radius:4px; font-size:12px; margin:3px;
font-family:monospace;' title='Type: {etype} | Articles: {ent["freq"]} | Centrality: {pr:.4f}'>
{ent["name"]} <span style='opacity:0.5; font-size:10px;'>×{ent["freq"]}</span>
</span>"""
    st.markdown(f"<div style='line-height:2;'>{badges_html}</div>", unsafe_allow_html=True)

    st.markdown("---")

    # ── Sources used ──────────────────────────────────────────────────────────
    st.markdown("<p style='color:#00f5ff; letter-spacing:2px; font-size:12px;'>SOURCES</p>", unsafe_allow_html=True)
    sources = list({a["source"] for a in articles})
    source_html = " &nbsp;·&nbsp; \"".join(f"<span style='color:#555; font-size:11px;'>{s}</span>" for s in sorted(sources))
    st.markdown(source_html, unsafe_allow_html=True)

elif not topic:
    st.markdown("""
<div style='text-align:center; padding:60px 0; color:#333;'>
<p style='font-size:40px;'>◈</p>
<p style='letter-spacing:3px; font-size:13px;'>ENTER A TOPIC TO BEGIN ANALYSIS</p>
<p style='font-size:11px; color:#222; margin-top:8px;'>
Council will fetch live articles, extract entities, and map their connections.
</p>
</div>
""", unsafe_allow_html=True)