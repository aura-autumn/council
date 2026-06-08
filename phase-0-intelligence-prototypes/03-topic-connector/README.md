# ⚡ Council · Prototype 03 — Topic Connection Graph

Part of the [Council](../README.md) open-source intelligence platform.

**This prototype proves:** Council's Deep Analysis capability — the system's ability to ingest multi-source news, extract named entities, and map how people, organisations, and places are connected across the information landscape. Hidden connections are scored and surfaced automatically.

---

## What It Does

Enter any topic. Council fetches up to 40 live articles, then delivers:

- **Interactive Entity Graph** — a pyvis network graph where nodes are real-world entities (people, orgs, places) and edges represent co-occurrence across articles
- **Community Clusters** — Louvain algorithm groups tightly connected entities into themes, each colored distinctly
- **Node Centrality** — PageRank scores determine node size; the most connected entity is visually dominant
- **Hidden Connections Panel** — entity pairs with unexpectedly high co-occurrence relative to their individual frequency (the surprise score)
- **Entity Roster** — all mapped entities badged by type (PERSON, ORG, GPE, EVENT) sorted by centrality

---

## Quickstart

```bash
# 1. Clone
git clone https://github.com/aura-autumn/council.git
cd council/phase-0-intelligence-prototypes/03-topic-graph

# 2. Install
pip install -r requirements.txt

# 3. Download the spaCy model (one time)
python -m spacy download en_core_web_sm

# 4. Set your NewsAPI key
cp .env.example .env
# Edit .env → NEWSAPI_KEY=your_key

# 5. Run
streamlit run app.py
```

---

## How It Works

```
User enters topic
    ↓
fetcher.py       →  NewsAPI /everything + source metadata
    ↓
extractor.py     →  spaCy en_core_web_sm NER
                     Entity types: PERSON, ORG, GPE, EVENT, NORP
                     Filtered to top 20–30 by article frequency
    ↓
graph_builder.py →  NetworkX graph
                     Nodes = entities
                     Edges = co-occurrence within same article
                     Louvain community detection
                     PageRank centrality
                     Hidden connection scoring (surprise formula)
    ↓
charts.py        →  pyvis interactive graph (cyberpunk dark theme)
    ↓
app.py           →  Streamlit dashboard
```

### Hidden Connection Formula

```
surprise(A, B) = co_occurrences(A, B) / (freq(A) × freq(B)) × 100
```

High surprise score = entities that appear together often but are not individually dominant. These are the non-obvious signal pairs that a casual reader misses.

---

## Connection to Full Council System

| Prototype Component | Production Component |
|---|---|
| `extractor.py` | `backend/graphs/analyzer_agent.py` → entity extraction node |
| `graph_builder.py` | `backend/services/knowledge_graph.py` |
| Hidden connection scoring | `backend/graphs/advisor_agent.py` → connection surfacing |
| pyvis graph | Frontend holographic panel: "Topic Explorer View" |

---

## Limitations & Honest Notes

- `en_core_web_sm` misses uncommon Indian entity names; production uses GPT-4o extraction or a fine-tuned NER
- Co-occurrence is article-level, not sentence-level — noisier edges than semantic similarity
- Graph is rebuilt per query; production maintains a persistent, incrementally updated graph (Neo4j or pgvector)
- No temporal layer — production tracks how connection strength changes over time

---

## Stack

`Python` · `Streamlit` · `spaCy` · `NetworkX` · `python-louvain` · `pyvis` · `NewsAPI`
