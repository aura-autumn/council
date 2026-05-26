"""
user_profile.py — Manages the user interest profile and embedding vector.

The profile is a weighted bag of interest topics. Weights are updated via
explicit quiz input (onboarding) and implicit feedback (article interactions).
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np

# ── Interest taxonomy ────────────────────────────────────────────────────────
INTEREST_CATEGORIES = {
    "Technology": [
        "Artificial Intelligence", "Cybersecurity", "Startups & VC",
        "Web3 & Crypto", "Space & Deep Tech", "Open Source",
    ],
    "Finance & Economy": [
        "Indian Markets", "Global Macro", "Personal Finance",
        "Policy & RBI", "Startups & Funding",
    ],
    "Geopolitics": [
        "India-China Relations", "US Politics", "Middle East",
        "South Asia", "International Trade",
    ],
    "Science": [
        "Climate & Environment", "Biotech & Health", "Physics",
        "Astronomy", "Research & Academia",
    ],
    "Society & Culture": [
        "Education", "Urban India", "Sports", "Entertainment",
        "Philosophy & Ideas",
    ],
    "Public Policy": [
        "Indian Government", "Defence", "Infrastructure",
        "Healthcare Policy", "Legal & Courts",
    ],
}

# Flat list for embedding lookup
ALL_INTERESTS: List[str] = [
    topic for topics in INTEREST_CATEGORIES.values() for topic in topics
]

PROFILE_PATH = Path("user_profile.json")


@dataclass
class UserProfile:
    interests: Dict[str, float] = field(default_factory=dict)   # topic → weight [0,1]
    goal: str = ""
    expertise_level: str = "intermediate"   # beginner / intermediate / expert
    preferred_depth: str = "balanced"       # quick / balanced / deep-dive
    region_focus: str = "both"              # india / global / both
    interaction_log: List[dict] = field(default_factory=list)

    # ── persistence ──────────────────────────────────────────────────────────

    def save(self, path: Path = PROFILE_PATH) -> None:
        data = {
            "interests": self.interests,
            "goal": self.goal,
            "expertise_level": self.expertise_level,
            "preferred_depth": self.preferred_depth,
            "region_focus": self.region_focus,
            "interaction_log": self.interaction_log[-50:],   # cap log
        }
        path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: Path = PROFILE_PATH) -> "UserProfile":
        if not path.exists():
            return cls()
        data = json.loads(path.read_text())
        return cls(**data)

    # ── embedding ────────────────────────────────────────────────────────────

    def to_vector(self, all_interests: List[str] = ALL_INTERESTS) -> np.ndarray:
        """Return a dense weight vector aligned to all_interests."""
        vec = np.array([self.interests.get(t, 0.0) for t in all_interests], dtype=float)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    # ── feedback ─────────────────────────────────────────────────────────────

    def record_interaction(self, article_topics: List[str], action: str) -> None:
        """
        action: 'read' | 'save' | 'skip' | 'dislike'
        Nudges weights up or down for topics in the article.
        """
        delta_map = {"read": 0.05, "save": 0.10, "skip": -0.02, "dislike": -0.05}
        delta = delta_map.get(action, 0.0)
        for topic in article_topics:
            if topic in self.interests:
                self.interests[topic] = float(
                    np.clip(self.interests[topic] + delta, 0.0, 1.0)
                )
        self.interaction_log.append({"topics": article_topics, "action": action})

    # ── helpers ──────────────────────────────────────────────────────────────

    def top_interests(self, n: int = 8) -> List[tuple]:
        return sorted(self.interests.items(), key=lambda x: x[1], reverse=True)[:n]

    def profile_completeness(self) -> float:
        if not self.interests:
            return 0.0
        filled = sum(1 for v in self.interests.values() if v > 0)
        return filled / max(len(self.interests), 1)
