"""
council/phase-0/01-bias-detector
charts.py — All Plotly visualizations for the dashboard.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# ── Council color palette (cyberpunk-inspired) ──
COLORS = {
    "bg": "#0d1117",
    "panel": "#161b22",
    "accent_blue": "#58a6ff",
    "accent_green": "#3fb950",
    "accent_red": "#f85149",
    "accent_orange": "#d29922",
    "accent_purple": "#bc8cff",
    "text": "#c9d1d9",
    "subtext": "#8b949e",
    "border": "#30363d",
}

BIAS_COLORS = {
    "Far Left": "#818cf8",
    "Left-Leaning": "#60a5fa",
    "Center": "#3fb950",
    "Right-Leaning": "#fb923c",
    "Far Right": "#f85149",
    "Unknown": "#8b949e",
}

SENTIMENT_COLORS = {
    "Positive": "#3fb950",
    "Neutral": "#d29922",
    "Negative": "#f85149",
}

SEVERITY_COLORS = {
    "High": "#f85149",
    "Medium": "#d29922",
    "Low": "#58a6ff",
}


def _base_layout(title: str = "") -> dict:
    return dict(
        title=dict(text=title, font=dict(color=COLORS["text"], size=15), x=0.01),
        paper_bgcolor=COLORS["panel"],
        plot_bgcolor=COLORS["panel"],
        font=dict(color=COLORS["text"], family="monospace"),
        margin=dict(t=45, b=30, l=30, r=30),
        xaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
        yaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
    )


# ── 1. Bias Distribution Bar Chart ──────────────────────────────────────────

def bias_distribution_chart(articles: list[dict]) -> go.Figure:
    df = pd.DataFrame(articles)
    counts = df["bias_label"].value_counts().reset_index()
    counts.columns = ["bias_label", "count"]

    order = ["Far Left", "Left-Leaning", "Center", "Right-Leaning", "Far Right", "Unknown"]
    counts["bias_label"] = pd.Categorical(counts["bias_label"], categories=order, ordered=True)
    counts = counts.sort_values("bias_label")

    fig = go.Figure(go.Bar(
        x=counts["bias_label"],
        y=counts["count"],
        marker_color=[BIAS_COLORS.get(b, "#8b949e") for b in counts["bias_label"]],
        text=counts["count"],
        textposition="outside",
        textfont=dict(color=COLORS["text"]),
    ))

    fig.update_layout(
        **_base_layout("Bias Distribution Across Sources"),
        xaxis_title="",
        yaxis_title="Article Count",
        showlegend=False,
    )
    return fig


# ── 2. Sentiment vs Bias Scatter ─────────────────────────────────────────────

def sentiment_bias_scatter(articles: list[dict]) -> go.Figure:
    known = [a for a in articles if a["bias_score"] is not None]
    if not known:
        return go.Figure()

    df = pd.DataFrame(known)

    fig = px.scatter(
        df,
        x="bias_score",
        y="sentiment_score",
        color="bias_label",
        color_discrete_map=BIAS_COLORS,
        hover_data=["source_name", "title"],
        size_max=12,
    )

    fig.update_traces(marker=dict(size=9, opacity=0.85, line=dict(width=0.5, color="#0d1117")))

    # Quadrant lines
    fig.add_hline(y=0, line_dash="dot", line_color=COLORS["border"], opacity=0.7)
    fig.add_vline(x=0, line_dash="dot", line_color=COLORS["border"], opacity=0.7)

    # Quadrant labels
    for x, y, text in [
        (-0.9, 0.85, "Left +<br>Positive"), (0.6, 0.85, "Right +<br>Positive"),
        (-0.9, -0.85, "Left +<br>Negative"), (0.6, -0.85, "Right +<br>Negative"),
    ]:
        fig.add_annotation(x=x, y=y, text=text, showarrow=False,
                           font=dict(size=9, color=COLORS["subtext"]), align="center")

    fig.update_layout(
        **_base_layout("Sentiment vs Political Lean"),
        xaxis=dict(title="← Left  |  Bias Score  |  Right →",
                   range=[-1.05, 1.05], gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
        yaxis=dict(title="← Negative  |  Sentiment  |  Positive →",
                   range=[-1.05, 1.05], gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
        paper_bgcolor=COLORS["panel"],
        plot_bgcolor=COLORS["panel"],
        font=dict(color=COLORS["text"], family="monospace"),
        margin=dict(t=45, b=30, l=60, r=30),
        legend=dict(bgcolor=COLORS["bg"], bordercolor=COLORS["border"], borderwidth=1),
    )
    return fig


# ── 3. Credibility Heatmap ────────────────────────────────────────────────────

def credibility_heatmap(articles: list[dict]) -> go.Figure:
    known = [a for a in articles if a["credibility"] is not None]
    if not known:
        return go.Figure()

    df = pd.DataFrame(known)
    agg = (df.groupby("source_name")
             .agg(credibility=("credibility", "first"),
                  bias_score=("bias_score", "first"),
                  article_count=("title", "count"))
             .reset_index()
             .sort_values("credibility", ascending=True))

    fig = go.Figure(go.Bar(
        x=agg["credibility"],
        y=agg["source_name"],
        orientation="h",
        marker=dict(
            color=agg["credibility"],
            colorscale=[[0, "#f85149"], [0.5, "#d29922"], [1, "#3fb950"]],
            showscale=True,
            colorbar=dict(
                title="Score",
                tickfont=dict(color=COLORS["text"]),
                titlefont=dict(color=COLORS["text"]),
            ),
            cmin=0, cmax=1,
        ),
        text=[f"{v:.2f}" for v in agg["credibility"]],
        textposition="outside",
        customdata=agg["article_count"],
        hovertemplate="<b>%{y}</b><br>Credibility: %{x:.2f}<br>Articles: %{customdata}<extra></extra>",
    ))

    fig.update_layout(
        **_base_layout("Source Credibility Scores"),
        xaxis=dict(title="Credibility Score", range=[0, 1.1],
                   gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
        yaxis=dict(title=""),
        height=max(300, len(agg) * 38),
        paper_bgcolor=COLORS["panel"],
        plot_bgcolor=COLORS["panel"],
        font=dict(color=COLORS["text"], family="monospace"),
        margin=dict(t=45, b=30, l=140, r=60),
    )
    return fig


# ── 4. Diversity Score Gauge ──────────────────────────────────────────────────

def diversity_gauge(diversity: dict) -> go.Figure:
    score = diversity["score"]

    color = (
        COLORS["accent_green"] if score >= 65
        else COLORS["accent_orange"] if score >= 40
        else COLORS["accent_red"]
    )

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number=dict(suffix="/100", font=dict(color=color, size=36)),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=1, tickcolor=COLORS["subtext"],
                      tickfont=dict(color=COLORS["subtext"])),
            bar=dict(color=color, thickness=0.25),
            bgcolor=COLORS["bg"],
            borderwidth=1,
            bordercolor=COLORS["border"],
            steps=[
                dict(range=[0, 40], color="#1a1f2e"),
                dict(range=[40, 65], color="#1a2420"),
                dict(range=[65, 100], color="#162520"),
            ],
            threshold=dict(
                line=dict(color=COLORS["text"], width=2),
                thickness=0.75,
                value=score,
            ),
        ),
        title=dict(text="Source Diversity Score", font=dict(color=COLORS["text"], size=14)),
    ))

    fig.update_layout(
        paper_bgcolor=COLORS["panel"],
        font=dict(color=COLORS["text"], family="monospace"),
        height=260,
        margin=dict(t=30, b=10, l=20, r=20),
    )
    return fig


# ── 5. Contradiction Severity Chart ──────────────────────────────────────────

def contradiction_chart(contradictions: list[dict]) -> go.Figure:
    if not contradictions:
        return go.Figure()

    df = pd.DataFrame([{
        "pair": f"{c['article_a']['source']} vs {c['article_b']['source']}",
        "divergence": c["sentiment_divergence"],
        "severity": c["severity"],
        "similarity": c["content_similarity"],
    } for c in contradictions[:10]])

    fig = go.Figure(go.Bar(
        x=df["divergence"],
        y=df["pair"],
        orientation="h",
        marker_color=[SEVERITY_COLORS[s] for s in df["severity"]],
        text=[f"{v:.2f}" for v in df["divergence"]],
        textposition="outside",
        customdata=df[["severity", "similarity"]].values,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Sentiment Divergence: %{x:.2f}<br>"
            "Severity: %{customdata[0]}<br>"
            "Content Similarity: %{customdata[1]:.2f}<extra></extra>"
        ),
    ))

    fig.update_layout(
        **_base_layout("Detected Contradictions (Sentiment Divergence)"),
        xaxis=dict(title="Sentiment Divergence", range=[0, 2.2],
                   gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
        yaxis=dict(title=""),
        height=max(250, len(df) * 42),
        paper_bgcolor=COLORS["panel"],
        plot_bgcolor=COLORS["panel"],
        font=dict(color=COLORS["text"], family="monospace"),
        margin=dict(t=45, b=30, l=170, r=60),
    )
    return fig
