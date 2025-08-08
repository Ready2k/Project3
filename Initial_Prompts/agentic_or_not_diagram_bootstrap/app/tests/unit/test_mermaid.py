from app.diagrams.mermaid import _sanitize, build_context_diagram, build_container_diagram, build_sequence_diagram

def test_sanitize_allows_basic_chars():
    assert _sanitize("OpenAI:gpt-4o") == "OpenAI:gpt-4o"
    assert _sanitize("Bad<script>") == "Bad_script_"

def test_context_diagram_contains_expected_nodes():
    m = build_context_diagram({"user_role":"Tester","provider":"meta","model":"llama3","jira_enabled":True,"vector_index":True})
    assert "user([Tester])" in m
    assert "llm[meta:llama3]" in m
    assert "jira[(Jira)]" in m
    assert "vec[(FAISS Index)]" in m

def test_sequence_diagram_mentions_phase():
    m = build_sequence_diagram({"provider":"bedrock","model":"claude"}, phase="QNA")
    assert "participant LLM as bedrock:claude" in m
    assert "phase=QNA" in m
