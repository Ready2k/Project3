# AgenticOrNot v1.3.1 – Implementation Spec

## Goal
Interactive GUI + API that judges if user stories/requirements are automatable with agentic AI, asks clarifying Qs, matches to reusable solution patterns, and exports results. Pluggable LLMs, vector matching, constraint-aware recommendations.

## Non-Goals (v1.3.1)
- Fancy React UI (Streamlit only)
- External RAG beyond Jira + files
- Cloud deployment (local + Docker only)

---

## Architecture

### Overview
- **UI:** Streamlit (`app/main.py`)
- **API:** FastAPI (`app/api.py`)
- **Providers:** LLM abstraction with OpenAI, Anthropic/Bedrock, Claude Direct, Internal
- **Embeddings:** sentence-transformers + FAISS
- **State:** diskcache (Redis optional in docker-compose)
- **Config:** Pydantic + `config.yaml` + `.env`
- **Storage:** local `data/patterns/` JSON library; SQLite for metrics/audit

### Request Flow
1. Ingest (text/file/Jira) → create `session_id`
2. Phases stream: Parsing → Validating → QnA → Matching → Recommending
3. Q&A fills missing fields (stateful)
4. Matcher = tag filter + vector similarity
5. Apply constraints (ban list) pre-prompt + pre-recommend
6. Output feasibility, patterns, reasoning, tech stack → export JSON/MD

---

## Directory Layout
```
agentic_or_not/
├── app/
│   ├── main.py                  # Streamlit UI
│   ├── api.py                   # FastAPI app (SSE/polling for status)
│   ├── config.py                # Pydantic settings, redaction helpers
│   ├── state/store.py           # diskcache/redis
│   ├── services/jira.py         # Jira fetch + mapping
│   ├── llm/
│   │   ├── base.py              # Provider interface
│   │   ├── openai_provider.py
│   │   ├── bedrock_provider.py
│   │   ├── claude_provider.py
│   │   ├── internal_provider.py
│   │   └── fakes.py             # FakeLLM/FakeEmbedder for tests
│   ├── embeddings/{engine.py,index.py}
│   ├── pattern/{matcher.py,generator.py,loader.py,schema.json}
│   ├── qa/{question_loop.py,templates.json}
│   ├── exporters/{json_exporter.py,markdown_exporter.py}
│   ├── utils/{logger.py,redact.py}
│   └── tests/                   # unit/integration/e2e
├── data/patterns/               # pattern JSONs
├── data/benchmarks/              # synthetic pattern sets for tests
├── exports/                     # generated outputs
├── config.yaml
├── .env.example
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── Makefile
```

---

## API Contracts (FastAPI)

- `POST /ingest`
  - Req: `{ "source": "text|file|jira", "payload": {...} }`
  - Res: `{ "session_id": "uuid" }`

- `GET /status/{session_id}`
  - Res: `{ "phase": "PARSING|VALIDATING|QNA|MATCHING|RECOMMENDING|DONE", "progress": 0-100, "missing_fields": [..] }`

- `POST /qa/{session_id}`
  - Req: `{ "answers": { "field": "value", ... } }`
  - Res: `{ "complete": true|false, "next_questions": [ ... ] }`

- `POST /match`
  - Req: `{ "session_id": "uuid", "top_k": 5 }`
  - Res: `{ "candidates": [{ "pattern_id": "...", "score": 0-1, "rationale": "..." }...] }`

- `POST /recommend`
  - Req: `{ "session_id": "uuid", "top_k": 3 }`
  - Res:
    ```json
    {
      "feasibility": "Yes|Partial|No",
      "recommendations": [{ "pattern_id": "...", "confidence": 0-1 }],
      "tech_stack": ["..."],
      "reasoning": "string"
    }
    ```

- `POST /export`
  - Req: `{ "session_id": "uuid", "format": "json|md" }`
  - Res: `{ "download_url": "sandbox or file://" }`

- `POST /providers/test`
  - Req: `{ "provider": "openai|bedrock|claude|internal", "model": "...", "api_key": "...", "endpoint_url": "...", "region": "..." }`
  - Res: `{ "ok": true|false, "message": "..." }`

---

## Pattern JSON Schema (excerpt)
```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["pattern_id","name","description","feasibility","pattern_type","input_requirements","tech_stack","confidence_score"],
  "properties": {
    "pattern_id": {"type":"string","pattern":"^PAT-[0-9]{3,}$"},
    "name": {"type":"string"},
    "description": {"type":"string"},
    "feasibility": {"enum":["Automatable","Partially Automatable","Not Automatable"]},
    "pattern_type": {"type":"array","items":{"type":"string"}},
    "input_requirements": {"type":"array","items":{"type":"string"}},
    "tech_stack": {"type":"array","items":{"type":"string"}},
    "related_patterns": {"type":"array","items":{"type":"string"}},
    "confidence_score": {"type":"number","minimum":0,"maximum":1}
  },
  "additionalProperties": true
}
```

---

## Config

### `config.yaml` (default)
```yaml
provider: openai
model: gpt-4o
pattern_library_path: ./data/patterns
export_path: ./exports
constraints:
  unavailable_tools: []
timeouts:
  llm: 20
  http: 10
logging:
  level: INFO
  redact_pii: true
bedrock:
  region: eu-west-2
```

### `.env.example`
```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=...
```

---

## Streamlit UI (v1)
- Inputs: text area, file upload (txt/docx/json/csv), Jira link + creds
- Progress: phases + progress bar (poll `/status`)
- Provider panel: live switch + “Test connection”
- Output cards: Feasibility, Patterns (+confidence), Reasoning, Tech Stack
- Exports: JSON + Markdown buttons

---

## Matching Logic
1. **Fast filter** by tags/domain extracted from input + existing pattern metadata.
2. **Vector** embeddings of requirement → FAISS index search.
3. **Score blend** = `w1*tag_score + w2*vector_score (+ w3*pattern_confidence)` (weights in config).
4. **Constraints** remove banned tech/patterns pre-ranking.

---

## Q&A State Machine
- States: `PARSING → VALIDATING → QNA → MATCHING → RECOMMENDING → DONE`
- Guards: `missing_fields`, `confidence_threshold`, `max_questions` (default 5)
- Questions from `qa/templates.json` keyed by domain/missing fields.
- Persist in `state/store.py` keyed by `session_id`.

---

## Security
- Redact secrets in logs/audit.
- Never persist API keys.
- Provider allowlist for outbound HTTP.
- PII scrubber in prompts and audit.

---

## Observability
- SQLite tables:
  - `runs(provider, model, latency_ms, tokens, created_at)`
  - `matches(session_id, pattern_id, score, accepted)`
- Simple Streamlit charting tab (model comparison).

---

## Testing (TDD)
- **Coverage:** 100% statements + branches (CI gate)
- **Static:** `mypy --strict`, `ruff`, `black`
- **Unit:** config, providers (mock httpx), matcher, generator, QA loop, exporters, logger/redact
- **Integration:** FastAPI routes, FAISS index flow, Jira fetch (mocked)
- **E2E:** Streamlit ↔ FastAPI happy path; provider switch; exports validate schema
- **Fakes:** `FakeLLM`, `FakeEmbedder` deterministic

---

## Make Targets
```
make fmt       # black + ruff --fix
make lint      # ruff + mypy
make test      # pytest + coverage
make e2e       # headless e2e
make up        # docker-compose up
```

---

## Definition of Done
- All tests green, coverage 100%
- `docker-compose up` yields working UI+API
- “Test connection” works for configured provider
- Exported JSON validates with schema; MD exports open
- Banned tools never appear in suggestions, tech stack, or prompts
