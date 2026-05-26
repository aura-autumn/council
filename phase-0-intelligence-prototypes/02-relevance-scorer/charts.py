"""
charts.py — Plotly visualisations for the Relevance Engine dashboard.

Cyberpunk dark theme matching prototype 01.
"""

from __future__ import annotations
from typing import List, Dict, Tuple
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from user_profile import UserProfile, ALL_INTERESTS, INTEREST_CATEGORIES
from fetcher import Article

# ── Theme ────────────────────────────────────────────────────────────────────
BG = "#0a0a0f"
PANEL = "#0f0f1a"
GRID = "#1a1a2e"
ACCENT_CYAN = "#00f5ff"
ACCENT_GREEN = "#39ff14"
ACCENT_PURPLE = "#bf5fff"
ACCENT_ORANGE = "#ff6e00"
ACCENT_PINK = "#ff2d6b"
TEXT = "#e0e0ff"
TEXT_DIM = "#6060a0"

LAYOUT_BASE = dict(
    paper_bgcolor=BG,
    plot_bgcolor=PANEL,
    font=dict(family="'Share Tech Mono', 'Courier New', monospace", color=TEXT, size=12),
    margin=dict(l=40, r=40, t=50, b=40),
)


def _axis(title="", color=TEXT_DIM):
    return dict(
        title=title,
        gridcolor=GRID,
        zerolinecolor=GRID,
        tickfont=dict(color=TEXT_DIM, size=10),
        titlefont=dict(color=color, size=11),
    )


# ── 1. Profile Radar Chart ───────────────────────────────────────────────────

def profile_radar(profile: UserProfile) -> go.Figure:
    """Radar chart of the user's top interests."""
    top = profile.top_interests(n=12)
    if not top:
        top = [(t, 0) for t in ALL_INTERESTS[:12]]
    labels, values = zip(*top)
    labels = list(labels) + [labels[0]]
    values = list(values) + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=labels,
        fill="toself",
        fillcolor=f"rgba(0,245,255,0.12)",
        line=dict(color=ACCENT_CYAN, width=2),
        marker=dict(color=ACCENT_CYAN, size=6),
        name="Interest Weight",
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="◈ USER INTEREST PROFILE", font=dict(color=ACCENT_CYAN, size=14), x=0.5),
        polar=dict(
            bgcolor=PANEL,
            radialaxis=dict(
                visible=True, range=[0, 1],
                gridcolor=GRID, tickfont=dict(color=TEXT_DIM, size=9),
                linecolor=GRID,
            ),
            angularaxis=dict(
                gridcolor=GRID,
                tickfont=dict(color=TEXT, size=10),
            ),
        ),
        showlegend=False,
        height=380,
    )
    return fig


# ── 2. Relevance Score Distribution ─────────────────────────────────────────

def score_distribution(articles: List[Article]) -> go.Figure:
    """Histogram of article relevance scores with tier colouring."""
    scores = [a.relevance_score for a in articles]

    colors = []
    for s in scores:
        if s >= 0.5:
            colors.append(ACCENT_GREEN)
        elif s >= 0.3:
            colors.append(ACCENT_CYAN)
        elif s >= 0.15:
            colors.append(ACCENT_ORANGE)
        else:
            colors.append(ACCENT_PINK)

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=scores,
        nbinsx=20,
        marker=dict(
            color=scores,
            colorscale=[
                [0, ACCENT_PINK],
                [0.3, ACCENT_ORANGE],
                [0.6, ACCENT_CYAN],
                [1.0, ACCENT_GREEN],
            ],
            line=dict(color=BG, width=0.5),
        ),
        name="Articles",
    ))

    # Tier threshold lines
    for val, label, color in [(0.5, "HIGH", ACCENT_GREEN), (0.3, "MED", ACCENT_CYAN), (0.15, "LOW", ACCENT_ORANGE)]:
        fig.add_vline(
            x=val, line=dict(color=color, width=1, dash="dot"),
            annotation_text=label, annotation_font=dict(color=color, size=9),
        )

    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="◈ RELEVANCE SCORE DISTRIBUTION", font=dict(color=ACCENT_CYAN, size=14), x=0.5),
        xaxis=dict(**_axis("Relevance Score"), range=[0, 1]),
        yaxis=_axis("Article Count"),
        height=300,
        bargap=0.05,
    )
    return fig


# ── 3. Topic Match Frequency ─────────────────────────────────────────────────

def topic_frequency(articles: List[Article], top_n: int = 12) -> go.Figure:
    """Horizontal bar chart of the most-matched interest topics in the feed."""
    freq: Dict[str, int] = {}
    for a in articles:
        for t in a.matched_topics:
            freq[t] = freq.get(t, 0) + 1

    if not freq:
        freq = {"No matches found": 0}

    sorted_items = sorted(freq.items(), key=lambda x: x[1])[-top_n:]
    labels = [x[0] for x in sorted_items]
    values = [x[1] for x in sorted_items]

    max_v = max(values) if values else 1
    bar_colors = [
        f"rgba(0,245,255,{0.4 + 0.6 * v / max_v})" for v in values
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=labels,
        x=values,
        orientation="h",
        marker=dict(
            color=bar_colors,
            line=dict(color=ACCENT_CYAN, width=0.5),
        ),
        text=[str(v) for v in values],
        textposition="outside",
        textfont=dict(color=TEXT_DIM, size=10),
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="◈ TOP MATCHED TOPICS IN FEED", font=dict(color=ACCENT_CYAN, size=14), x=0.5),
        xaxis=_axis("Match Count"),
        yaxis=dict(**_axis(), tickfont=dict(color=TEXT, size=10)),
        height=max(300, 30 * len(labels) + 80),
    )
    return fig


# ── 4. Relevance × Credibility Scatter ───────────────────────────────────────

def relevance_credibility_scatter(articles: List[Article]) -> go.Figure:
    """Scatter: x=credibility, y=relevance, coloured by bias."""
    shown = [a for a in articles if a.relevance_score > 0][:60]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[a.credibility for a in shown],
        y=[a.relevance_score for a in shown],
        mode="markers",
        marker=dict(
            size=[8 + a.relevance_score * 10 for a in shown],
            color=[a.bias_score for a in shown],
            colorscale=[
                [0, "#3a86ff"],    # left
                [0.5, ACCENT_CYAN],  # center
                [1.0, "#ff4040"],  # right
            ],
            cmin=-0.6, cmax=0.6,
            colorbar=dict(
                title=dict(text="Bias ←L/R→", font=dict(color=TEXT_DIM, size=10)),
                tickfont=dict(color=TEXT_DIM, size=9),
                len=0.7,
                bgcolor=PANEL,
                bordercolor=GRID,
            ),
            line=dict(color=BG, width=0.5),
            opacity=0.85,
        ),
        text=[f"{a.source}<br>{a.title[:60]}..." for a in shown],
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Relevance: %{y:.2f}<br>"
            "Credibility: %{x:.2f}<br>"
            "<extra></extra>"
        ),
        name="Articles",
    ))

    # Quadrant line
    fig.add_hline(y=0.3, line=dict(color=GRID, dash="dot", width=1))
    fig.add_vline(x=0.75, line=dict(color=GRID, dash="dot", width=1))

    # Sweet-spot annotation
    fig.add_annotation(
        x=0.9, y=0.75, text="★ SWEET SPOT",
        font=dict(color=ACCENT_GREEN, size=10),
        showarrow=False,
    )

    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="◈ RELEVANCE × CREDIBILITY MATRIX", font=dict(color=ACCENT_CYAN, size=14), x=0.5),
        xaxis=dict(**_axis("Source Credibility"), range=[0.4, 1.0]),
        yaxis=dict(**_axis("Relevance Score"), range=[0, 1]),
        height=400,
    )
    return fig


# ── 5. Interest Weight Heatmap (categories) ───────────────────────────────────

def interest_heatmap(profile: UserProfile) -> go.Figure:
    """Heatmap of interest weights grouped by category."""
    categories = list(INTEREST_CATEGORIES.keys())
    max_topics = max(len(v) for v in INTEREST_CATEGORIES.values())

    z = []
    y_labels = categories
    x_labels = [f"T{i+1}" for i in range(max_topics)]
    hover = []

    for cat in categories:
        topics = INTEREST_CATEGORIES[cat]
        row = [profile.interests.get(t, 0.0) for t in topics]
        row_hover = [t for t in topics]
        # Pad
        row += [None] * (max_topics - len(row))
        row_hover += [""] * (max_topics - len(row_hover))
        z.append(row)
        hover.append(row_hover)

    fig = go.Figure(go.Heatmap(
        z=z,
        x=x_labels,
        y=y_labels,
        colorscale=[
            [0.0, PANEL],
            [0.001, "#0d2137"],
            [0.3, "#003d5c"],
            [0.7, ACCENT_CYAN],
            [1.0, ACCENT_GREEN],
        ],
        zmin=0, zmax=1,
        text=hover,
        hovertemplate="<b>%{text}</b><br>Weight: %{z:.2f}<extra></extra>",
        colorbar=dict(
            title=dict(text="Weight", font=dict(color=TEXT_DIM, size=10)),
            tickfont=dict(color=TEXT_DIM, size=9),
            bgcolor=PANEL, bordercolor=GRID,
        ),
        xgap=2, ygap=2,
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="◈ INTEREST WEIGHT HEATMAP", font=dict(color=ACCENT_CYAN, size=14), x=0.5),
        xaxis=dict(showticklabels=False, title="Topics →"),
        yaxis=dict(tickfont=dict(color=TEXT, size=11)),
        height=300,
    )
    return fig


# ── 6. Cumulative Relevance Curve ────────────────────────────────────────────

def cumulative_relevance(articles: List[Article]) -> go.Figure:
    """Shows how fast relevance drops off as you scroll down the feed."""
    sorted_scores = sorted([a.relevance_score for a in articles], reverse=True)
    x = list(range(1, len(sorted_scores) + 1))
    cumavg = [np.mean(sorted_scores[:i]) for i in x]

    fig = go.Figure()
    # Area under the curve
    fig.add_trace(go.Scatter(
        x=x, y=sorted_scores,
        fill="tozeroy",
        fillcolor=f"rgba(0,245,255,0.07)",
        line=dict(color=ACCENT_CYAN, width=1.5),
        name="Score",
        mode="lines",
    ))
    # Cumulative average
    fig.add_trace(go.Scatter(
        x=x, y=cumavg,
        line=dict(color=ACCENT_GREEN, width=2, dash="dash"),
        name="Cumulative Avg",
        mode="lines",
    ))

    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="◈ RELEVANCE DECAY CURVE", font=dict(color=ACCENT_CYAN, size=14), x=0.5),
        xaxis=_axis("Article Rank"),
        yaxis=dict(**_axis("Relevance Score"), range=[0, 1]),
        height=280,
        legend=dict(font=dict(color=TEXT_DIM, size=10), bgcolor="rgba(0,0,0,0)"),
    )
    return fig
