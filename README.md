# ⚡ Council — Personal Strategic Intelligence Engine

> *The modern world overwhelms us with information while we starve of true understanding.*

Council is an open-source, AI-powered personal intelligence platform that learns you deeply — your interests, goals, and values — and delivers clarity, depth, and foresight from real-time global and Indian sources. No noise. No agendas. Just intelligence that works for you.

**This repository is structured as a phased build, documented in public.**
Every phase is designed to be independently useful and impressive — not just scaffolding for something that might ship someday.

---

## 🗂️ Repository Structure

```
council/
├── phase-0-intelligence-prototypes/   ← You are here
│   ├── 01-bias-detector/              # News bias & contradiction analysis
│   ├── 02-relevance-engine/           # Personalized scoring pipeline
│   ├── 03-topic-graph/                # Knowledge graph & hidden connections
│   ├── 04-ingestion-monitor/          # Real-time pipeline observability
│   └── 05-eval-dashboard/             # RAGAS-style evaluation framework
│
├── phase-1-backend/                   # FastAPI + LangGraph (coming soon)
├── phase-2-frontend/                  # Next.js 15 cyberpunk UI (coming soon)
└── docs/
    ├── VISION.md                      # Full product vision & manifesto
    ├── HLD.md                         # High-level system design
    └── USER_STORIES.md                # MoSCoW-prioritized user stories
```

---

## 🧠 Phase 0 — Intelligence Prototypes

Each prototype is a **standalone, runnable demo** that proves a core Council capability. Together they form the analytical brain of the platform.

| # | Dashboard | Council Feature It Proves | Status |
|---|-----------|--------------------------|--------|
| 01 | **News Bias & Contradiction Detector** | Analyzer Agent — bias flags, cross-source contradictions | 🔨 Building |
| 02 | **Relevance Engine** | Feed ranking — cosine similarity, user embeddings | 📋 Planned |
| 03 | **Topic Connection Graph** | Deep Analysis — hidden connections between events | 📋 Planned |
| 04 | **Real-time Ingestion Monitor** | Pipeline observability — live chunking & embedding | 📋 Planned |
| 05 | **Eval & Feedback Analytics** | RAGAS-style evaluation — relevance, faithfulness, actionability | 📋 Planned |

### Why prototypes first?

Building the full stack from day one is the slowest path to something impressive.
Each prototype here:
- **Runs independently** — clone, install, run. No backend required.
- **Demonstrates a real AI engineering concept** — not just pretty charts.
- **Maps directly to a production feature** — these aren't throwaways. The code migrates into the main system.
- **Ships fast** — each one takes 1–2 weeks solo, and looks great on a portfolio immediately.

---

## 🏗️ Full System Architecture (Phase 1+)

```
Users (Browser)
    ↓ HTTPS + JWT
Next.js 15 Frontend (Vercel)
    — Cyberpunk dashboard (Framer Motion holographic panels)
    — Onboarding quiz, feed, topic explorer, advisory chat
    ↓ REST + SSE/WebSocket
FastAPI Backend (Python + Uvicorn)
    — LangGraph multi-agent workflows
    — RAG ingestion pipeline
    — Evaluation & feedback system
    ↔ PostgreSQL + pgvector (Neon/Railway)
        — User profiles, embeddings, hybrid search
External Sources
    — NewsAPI, GNews, RSS (The Hindu, Indian Express)
    — X/Twitter (free tier), Reddit, academic endpoints
```

**Stack:** Next.js 15 · FastAPI · PostgreSQL + pgvector · LangChain/LangGraph · Framer Motion · Docker · Vercel · Railway

---

## 🎯 Target User

Ambitious, time-constrained knowledge seekers aged 25–35 — working professionals in tech, finance, consulting, and public policy; postgraduate students. People who are intellectually curious but overwhelmed by fragmented, biased information flows.

**Core problem:** No trusted, personalized system that filters noise, surfaces meaningful connections, and supports better decisions — without the user spending hours on it.

---

## 📊 MVP Success Metrics

| Metric | Target |
|--------|--------|
| Briefing relevance rating | ≥ 80% "highly relevant" |
| Novel insights surfaced | ≥ 60% of interactions |
| Conversation quality score | ≥ 4.5 / 5 |
| Week-1 retention | 4/5 test users return on 3+ days |

---

## 🚀 Running a Prototype

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/council.git
cd council/phase-0-intelligence-prototypes/01-bias-detector

# Install dependencies
pip install -r requirements.txt

# Add your NewsAPI key
cp .env.example .env
# Edit .env: NEWSAPI_KEY=your_key_here

# Run
streamlit run app.py
```

---

## 🗺️ Roadmap

- [x] Project vision & architecture documented
- [ ] **Phase 0:** Intelligence prototypes (active)
- [ ] Phase 1: FastAPI backend skeleton + LangGraph agents
- [ ] Phase 2: Next.js cyberpunk UI + frontend-backend integration
- [ ] Phase 3: Real-time layer (SSE) + feedback system
- [ ] Phase 4: Open-source release + demo video

---

## 💡 Design Philosophy

**Separation of concerns** — Frontend = experience. Backend = intelligence.

**Alive & wise** — Streaming responses, thoughtful loading states, dynamic updates. The system should *feel* like it's thinking.

**Eval-first** — Every feature ships with measurable quality metrics. Not vibes, not demos — numbers.

**Open source, zero cost to run** — Free tiers only (Vercel, Railway, Neon, Groq/HuggingFace). Anyone can fork and deploy their own Council.

---

## 📄 License

MIT — build on this, learn from it, make it yours.

---

*Built with focused, relentless execution. Council exists because information without understanding is just noise.*