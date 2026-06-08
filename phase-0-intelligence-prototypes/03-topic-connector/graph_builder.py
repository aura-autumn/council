import networkx as nx
from community import community_louvain
from collections import defaultdict


ENTITY_TYPE_COLORS = {
    "PERSON":  "#00f5ff",   # cyan
    "ORG":     "#bf00ff",   # purple
    "GPE":     "#00ff88",   # green
    "EVENT":   "#ff6600",   # orange
    "NORP":    "#ffcc00",   # yellow
    "FAC":     "#ff0066",   # pink
    "PRODUCT": "#99ccff",   # light blue
}

DEFAULT_COLOR = "#aaaaaa"


def build_graph(extraction: dict) -> dict:
    """
    Build a co-occurrence graph from extracted entities.

    Returns:
        {
            "graph": nx.Graph,
            "communities": {node: community_id},
            "pagerank": {node: score},
            "hidden_connections": [...],
            "community_colors": {community_id: hex_color},
        }
    """
    entities          = extraction["entities"]
    article_entities  = extraction["article_entities"]   # filtered, parallel to articles
    entity_freq       = extraction["entity_freq"]
    entity_to_articles = extraction.get("entity_to_articles", {})

    # Raw articles list is needed to resolve index → article object for edges.
    # article_entities is already filtered & parallel to the original articles list,
    # so we track co-occurring article indices and resolve them via entity_to_articles.

    G = nx.Graph()

    # ── Nodes ────────────────────────────────────────────────────────────────
    for ent in entities:
        G.add_node(
            ent["name"],
            entity_type=ent["type"],
            freq=ent["freq"],
            articles=entity_to_articles.get(ent["name"], []),
        )

    # ── Edges ────────────────────────────────────────────────────────────────
    # edge_article_indices[key] = list of article indices where both entities appeared.
    # We use article indices here so we can later dereference the *exact* shared article
    # objects (from entity_to_articles) rather than guessing.
    edge_weights        = defaultdict(int)
    edge_article_indices = defaultdict(list)   # key → [idx, ...]

    for idx, ae in enumerate(article_entities):
        for i in range(len(ae)):
            for j in range(i + 1, len(ae)):
                a, b = ae[i], ae[j]
                if a in G and b in G:
                    key = tuple(sorted([a, b]))
                    edge_weights[key] += 1
                    edge_article_indices[key].append(idx)

    for (a, b), weight in edge_weights.items():
        # Collect the actual article objects that mention BOTH entities.
        # entity_to_articles[x] lists articles in the same order as the original
        # articles list, but duplicates are possible if an entity appears many times.
        # We use a url-keyed dict to deduplicate, then convert back to a list.
        shared: dict[str, dict] = {}
        arts_a = {art["url"]: art for art in entity_to_articles.get(a, [])}
        arts_b = {art["url"]: art for art in entity_to_articles.get(b, [])}
        for url in arts_a:
            if url in arts_b:
                shared[url] = arts_a[url]

        # Fallback: if URL-based intersection is empty (e.g. missing URLs),
        # use articles from entity A at the recorded co-occurrence indices.
        if not shared:
            arts_a_list = entity_to_articles.get(a, [])
            for idx in edge_article_indices[(a, b)]:
                if idx < len(arts_a_list):
                    art = arts_a_list[idx]
                    shared[art.get("url", str(idx))] = art

        G.add_edge(a, b, weight=weight, articles=list(shared.values()))

    if len(G.nodes) == 0:
        return {"graph": G, "communities": {}, "pagerank": {},
                "hidden_connections": [], "community_colors": {}}

    # ── Community detection ───────────────────────────────────────────────────
    if len(G.edges) > 0:
        communities = community_louvain.best_partition(G, weight="weight", random_state=42)
    else:
        communities = {node: i for i, node in enumerate(G.nodes)}

    # ── PageRank centrality ───────────────────────────────────────────────────
    try:
        pagerank = nx.pagerank(G, weight="weight")
    except Exception:
        pagerank = {node: 1.0 / len(G.nodes) for node in G.nodes}

    # ── Community palette (cyberpunk) ─────────────────────────────────────────
    palette = [
        "#00f5ff", "#bf00ff", "#00ff88", "#ff6600",
        "#ffcc00", "#ff0066", "#99ccff", "#ff3399",
        "#66ff66", "#ff9900",
    ]
    unique_communities = sorted(set(communities.values()))
    community_colors = {c: palette[i % len(palette)] for i, c in enumerate(unique_communities)}

    # ── Hidden connections ────────────────────────────────────────────────────
    hidden = []
    for (a, b), weight in edge_weights.items():
        if weight < 2:
            continue
        freq_a = entity_freq.get(a, 1)
        freq_b = entity_freq.get(b, 1)
        surprise = weight / (freq_a * freq_b) * 100
        hidden.append({
            "entity_a": a,
            "entity_b": b,
            "co_occurrences": weight,
            "freq_a": freq_a,
            "freq_b": freq_b,
            "surprise_score": round(surprise, 3),
        })

    hidden = sorted(hidden, key=lambda x: -x["surprise_score"])[:10]

    return {
        "graph": G,
        "communities": communities,
        "pagerank": pagerank,
        "hidden_connections": hidden,
        "community_colors": community_colors,
    }