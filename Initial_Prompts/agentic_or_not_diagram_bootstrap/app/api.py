from __future__ import annotations

from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import Literal, Dict

from app.diagrams.mermaid import build_context_diagram, build_container_diagram, build_sequence_diagram

app = FastAPI(title="AgenticOrNot API (bootstrap)")

# In-memory demo session store for the endpoint
_SESSIONS: Dict[str, Dict[str, str]] = {
    "demo": {"provider": "openai", "model": "gpt-4o"}
}

class DiagramResponse(BaseModel):
    mermaid: str

@app.get("/diagram/{session_id}", response_model=DiagramResponse)
def get_diagram(session_id: str, view: Literal["context", "container", "sequence"] = Query("sequence")):
    run = _SESSIONS.get(session_id, {"provider": "unknown", "model": "unknown"})
    cfg = {"provider": "openai", "model": "gpt-4o", "jira_enabled": True, "vector_index": True}
    if view == "context":
        return DiagramResponse(mermaid=build_context_diagram(cfg))
    if view == "container":
        return DiagramResponse(mermaid=build_container_diagram({"db": "SQLite", "state": "diskcache"}))
    if view == "sequence":
        return DiagramResponse(mermaid=build_sequence_diagram(run, phase="MATCHING"))
    raise HTTPException(status_code=400, detail="invalid view")
