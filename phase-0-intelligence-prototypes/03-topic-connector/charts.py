from pyvis.network import Network
import networkx as nx
import tempfile
import os

ENTITY_TYPE_COLORS = {
    "PERSON":  "#00f5ff",
    "ORG":     "#bf00ff",
    "GPE":     "#00ff88",
    "EVENT":   "#ff6600",
    "NORP":    "#ffcc00",
    "FAC":     "#ff0066",
    "PRODUCT": "#99ccff",
}
DEFAULT_COLOR = "#888888"


def render_pyvis_graph(graph_data: dict, height: str = "600px") -> str:
    """
    Renders the NetworkX graph as a pyvis HTML string (cyberpunk styled).
    Returns the HTML content as a string.
    """
    G = graph_data["graph"]
    communities = graph_data["communities"]
    pagerank = graph_data["pagerank"]
    community_colors = graph_data["community_colors"]

    if len(G.nodes) == 0:
        return "<p style='color:#ff0066;'>No entities found to graph.</p>"

    net = Network(
        height=height,
        width="100%",
        bgcolor="#0a0a0f",
        font_color="#e0e0e0",
        directed=False,
    )

    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "forceAtlas2Based": {
          "gravitationalConstant": -60,
          "centralGravity": 0.005,
          "springLength": 120,
          "springConstant": 0.08,
          "damping": 0.6
        },
        "solver": "forceAtlas2Based",
        "stabilization": { "iterations": 150 }
      },
      "edges": {
        "smooth": { "type": "continuous" },
        "color": { "inherit": false }
      },
      "nodes": {
        "shape": "dot",
        "borderWidth": 2,
        "shadow": { "enabled": true, "color": "rgba(0,245,255,0.4)", "size": 10 }
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 100
      }
    }
    """)

    max_pr = max(pagerank.values()) if pagerank else 1.0

    for node in G.nodes:
        pr = pagerank.get(node, 0.01)
        size = 10 + (pr / max_pr) * 30

        community_id = communities.get(node, 0)
        color = community_colors.get(community_id, DEFAULT_COLOR)

        entity_type = G.nodes[node].get("entity_type", "ORG")
        freq = G.nodes[node].get("freq", 1)

        # Node hover tooltip contains context articles list summary
        node_articles = G.nodes[node].get("articles", [])
        art_titles = "".join([f"<li>• {a['source']}: {a['title'][:50]}...</li>" for a in node_articles[:3]])
        
        tooltip = (
            f"<div style='font-family:monospace; color:#fff;'>"
            f"<b style='color:{color}; font-size:14px;'>{node}</b><br>"
            f"Type: {entity_type}<br>"
            f"Centrality: {pr:.4f}<br>"
            f"Appears in {freq} articles:<br>"
            f"<ul style='margin:4px 0; padding-left:12px; font-size:11px; color:#aaa;'>{art_titles}</ul>"
            f"</div>"
        )

        net.add_node(
            node,
            label=node,
            size=size,
            color={
                "background": color,
                "border": "#ffffff",
                "highlight": {"background": "#ffffff", "border": color},
            },
            title=tooltip,
            font={"color": "#e0e0e0", "size": 12, "face": "monospace"},
        )

    max_weight = max((d.get("weight", 1) for _, _, d in G.edges(data=True)), default=1)

    for u, v, data in G.edges(data=True):
        weight = data.get("weight", 1)
        width = 1 + (weight / max_weight) * 5
        opacity = 0.3 + (weight / max_weight) * 0.6
        color_hex = f"rgba(0,245,255,{opacity:.2f})"

        # Edge hover tooltip showing actual intersecting sources
        shared_articles = data.get("articles", [])
        shared_list = "".join([f"<li>🎬 {a['source']}: {a['title'][:60]}...</li>" for a in shared_articles[:4]])
        
        edge_tooltip = (
            f"<div style='font-family:monospace; color:#fff; min-width:250px;'>"
            f"🤝 <b style='color:#00f5ff;'>Connection: {u} ── {v}</b><br>"
            f"Co-occurrences: <b>{weight} article(s)</b><br>"
            f"<hr style='border-color:#333; margin:4px 0;'>"
            f"<ul style='margin:0; padding-left:5px; list-style:none; font-size:11px; color:#bbb;'>{shared_list}</ul>"
            f"</div>"
        )

        net.add_edge(
            u, v,
            width=width,
            color=color_hex,
            title=edge_tooltip,
        )

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
        tmp_path = f.name

    net.save_graph(tmp_path)

    with open(tmp_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    os.unlink(tmp_path)
    return html_content