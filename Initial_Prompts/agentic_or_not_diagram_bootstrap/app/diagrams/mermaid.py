from __future__ import annotations

from typing import Dict

# Minimal sanitizer to keep Mermaid safe (no HTML/JS injection).
# Keeps letters, numbers, spaces, dashes, underscores, and dots.
def _sanitize(label: str) -> str:
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_.:")
    return ''.join(ch if ch in allowed else '_' for ch in (label or '')) or 'unknown'


def build_context_diagram(cfg: Dict[str, str]) -> str:
    user_role = _sanitize(cfg.get('user_role', 'User'))
    provider = _sanitize(cfg.get('provider', 'LLM Provider'))
    model = _sanitize(cfg.get('model', 'Model'))
    jira_enabled = cfg.get('jira_enabled', True)
    vec_enabled = cfg.get('vector_index', True)

    lines = [
        "flowchart LR",
        f"  user([{user_role}])",
        "  ui[Streamlit UI]",
        "  api[FastAPI API]",
        f"  llm[{provider}:{model}]",
        "  patterns[(Pattern Library)]",
    ]
    if jira_enabled:
        lines.append("  jira[(Jira)]")
    if vec_enabled:
        lines.append("  vec[(FAISS Index)]")

    lines += [
        "  user --> ui --> api",
        "  api --> llm",
        "  api --> patterns",
    ]
    if jira_enabled:
        lines.append("  api --> jira")
    if vec_enabled:
        lines.append("  api --> vec")
    return "\n".join(lines)


def build_container_diagram(cfg: Dict[str, str]) -> str:
    db = _sanitize(cfg.get('db', 'SQLite/PG'))
    state = _sanitize(cfg.get('state', 'diskcache/redis'))
    lines = [
        "flowchart TB",
        "  subgraph AgenticOrNot",
        "    ui[Streamlit UI]",
        "    api[FastAPI API]",
        f"    state[{state}]",
        "    embeddings[Embeddings + FAISS]",
        "    exporters[Exporters]",
        "  end",
        f"  db[({db})]",
        "  ui --> api",
        "  api --> state",
        "  api --> embeddings",
        "  api --> exporters",
        "  api --> db",
    ]
    return "\n".join(lines)


def build_sequence_diagram(run: Dict[str, str], phase: str) -> str:
    provider = _sanitize(run.get('provider', 'Provider'))
    model = _sanitize(run.get('model', 'Model'))
    phase = _sanitize(phase)
    lines = [
        "sequenceDiagram",
        "  participant U as User",
        "  participant UI as Streamlit UI",
        "  participant API as FastAPI",
        f"  participant LLM as {provider}:{model}",
        "  participant LIB as Pattern Library",
        "  U->>UI: Submit requirement",
        "  UI->>API: POST /ingest",
        "  API-->>UI: session_id",
        f"  Note over API: phase={phase}",
        "  UI->>API: GET /status",
        "  API->>LLM: Clarify / Embed (if needed)",
        "  API->>LIB: Vector match",
        "  API-->>UI: Recommendations + Confidence",
        "  UI-->>U: Feasibility + Tech Stack",
    ]
    return "\n".join(lines)
