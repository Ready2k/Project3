# AgenticOrNot – Diagram Bootstrap (AI-first)

This tiny starter proves the **live Mermaid C4 panel** concept so an AI codegen can expand it to the full app.

## What’s here
- `app/diagrams/mermaid.py` – sanitization + builders for **context**, **container**, **sequence**.
- `app/api.py` – FastAPI with `/diagram/{session_id}` returning Mermaid text.
- `app/main.py` – Streamlit with tabs rendering Mermaid via CDN script.
- Tests for builders and endpoint.

## Run locally
```bash
pip install -r requirements.txt
# API
uvicorn app.api:app --reload
# UI
streamlit run app/main.py
```

## Tests
```bash
pytest -q
```

## Notes
- In the full system, the UI will fetch Mermaid via `/diagram` on each phase change.
- Sanitization is minimal but safe for Mermaid.
- This repo is meant for **AI-driven completion**: the codegen can flesh out the rest per SPEC v1.3.2.
