"""Load rag-agent-skills SKILL.md files and expose them as prompt strings.

Skills are loaded once at module import time from the closest ``rag-agent-skills``
directory found on the filesystem.  If no skills directory is reachable (e.g.
a bare Docker image without the volume mount), every skill falls back to an
empty string and the agents continue to work using only their base system
prompts.

Lookup order:
  1. Sibling of the repo root: <repo-root>/rag-agent-skills/
     (standard local-dev layout: onboarding_guide/rag-agent-skills/)
  2. /app/rag-agent-skills/
     (Docker: requires the volume mount in docker-compose.yml)
"""

import re
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Directory resolution
# ---------------------------------------------------------------------------

def _find_skills_dir() -> Optional[Path]:
    candidates = [
        # Local dev: skills.py lives at rag_backend/prompts/skills.py
        # so three .parent calls reach the repo root.
        Path(__file__).resolve().parent.parent.parent / "rag-agent-skills",
        # Docker with volume mount ../rag-agent-skills:/app/rag-agent-skills
        Path("/app/rag-agent-skills"),
    ]
    for path in candidates:
        if path.is_dir():
            return path
    return None


_SKILL_DIR: Optional[Path] = _find_skills_dir()


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n?", re.DOTALL)


def _load_skill(name: str) -> str:
    """Read ``<name>/SKILL.md``, strip YAML frontmatter, return the body.

    Returns an empty string when the skills directory or the file is absent.
    """
    if _SKILL_DIR is None:
        return ""
    path = _SKILL_DIR / name / "SKILL.md"
    if not path.exists():
        return ""
    raw = path.read_text(encoding="utf-8")
    return _FRONTMATTER_RE.sub("", raw).strip()


# ---------------------------------------------------------------------------
# Individual skills (loaded once at import time — no per-request disk I/O)
# ---------------------------------------------------------------------------

RAG_RETRIEVAL_SKILL       = _load_skill("rag-retrieval")
CONVERSATIONAL_STYLE_SKILL = _load_skill("conversational-style")
UNCERTAINTY_PROTOCOL_SKILL = _load_skill("uncertainty-protocol")
CITATION_DISCIPLINE_SKILL  = _load_skill("citation-discipline")
TASK_EXECUTION_SKILL       = _load_skill("task-execution")


# ---------------------------------------------------------------------------
# Per-agent skill assembly
# ---------------------------------------------------------------------------

_DIVIDER = "\n\n────────────────────────────────────────\n\n"


def _assemble(skill_pairs: list) -> str:
    """Join non-empty skills with a divider under a shared header."""
    blocks = []
    for heading, content in skill_pairs:
        if content:
            blocks.append(f"## {heading}\n\n{content}")
    if not blocks:
        return ""
    header = (
        "════════════════════════════════════════\n"
        "OPERATIONAL SKILLS\n"
        "(detailed guidance that extends the rules above)\n"
        "════════════════════════════════════════"
    )
    return header + _DIVIDER + _DIVIDER.join(blocks)


def build_main_agent_skills() -> str:
    """Skills block for the main VaultMind RAG agent (chat + Q&A).

    Injects: RAG Retrieval · Conversational Style · Uncertainty Protocol ·
             Citation Discipline
    Excludes: Task Execution (backend ops — not relevant for chat Q&A).
    """
    return _assemble([
        ("RAG Retrieval",        RAG_RETRIEVAL_SKILL),
        ("Conversational Style", CONVERSATIONAL_STYLE_SKILL),
        ("Uncertainty Protocol", UNCERTAINTY_PROTOCOL_SKILL),
        ("Citation Discipline",  CITATION_DISCIPLINE_SKILL),
    ])


def build_trainer_agent_skills() -> str:
    """Skills block for the TrainerSubAgent (employee training Q&A).

    Injects: Conversational Style · Uncertainty Protocol · Citation Discipline
    Excludes: RAG Retrieval (Trainer uses Drive snapshots, not ChromaDB directly).
    """
    return _assemble([
        ("Conversational Style", CONVERSATIONAL_STYLE_SKILL),
        ("Uncertainty Protocol", UNCERTAINTY_PROTOCOL_SKILL),
        ("Citation Discipline",  CITATION_DISCIPLINE_SKILL),
    ])
