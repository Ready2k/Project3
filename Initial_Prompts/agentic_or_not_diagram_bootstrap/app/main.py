from __future__ import annotations

import streamlit as st

from app.diagrams.mermaid import (
    build_context_diagram,
    build_container_diagram,
    build_sequence_diagram,
)

st.set_page_config(page_title="AgenticOrNot – Demo", layout="wide")

st.title("AgenticOrNot – Architecture Panel Demo")


def mermaid_block(mermaid_src: str, height: int = 420):
    html = f"""
    <div class='mermaid'>{mermaid_src}</div>
    <script>
      if (!window.mermaidLoaded) {{
        var s = document.createElement('script');
        s.src = 'https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js';
        s.onload = function() {{ window.mermaid.initialize({{ startOnLoad: true }}) }};
        document.head.appendChild(s);
        window.mermaidLoaded = true;
      }} else {{
        window.mermaid.initialize({{ startOnLoad: true }});
      }}
    </script>
    """
    st.components.v1.html(html, height=height, scrolling=True)


with st.sidebar:
    st.header("Config (demo)")
    provider = st.selectbox("Provider", ["openai", "bedrock", "claude", "internal", "meta"], index=0)
    model = st.text_input("Model", value="gpt-4o")
    jira_enabled = st.checkbox("Jira enabled", value=True)
    vec_enabled = st.checkbox("Vector index", value=True)
    db = st.selectbox("DB", ["SQLite", "PostgreSQL"], index=0)
    state = st.selectbox("State", ["diskcache", "redis"], index=0)

cfg = {
    "provider": provider,
    "model": model,
    "jira_enabled": jira_enabled,
    "vector_index": vec_enabled,
    "db": db,
    "state": state,
    "user_role": "Business User",
}

tab1, tab2, tab3 = st.tabs(["Sequence", "Context", "Container"])

with tab1:
    st.subheader("Sequence (live phase demo)")
    mermaid_block(build_sequence_diagram({"provider": provider, "model": model}, phase="MATCHING"))

with tab2:
    st.subheader("Context (C4 L1)")
    mermaid_block(build_context_diagram(cfg))

with tab3:
    st.subheader("Container (C4 L2)")
    mermaid_block(build_container_diagram(cfg))

st.caption("This is a bootstrap demo; in the full app the diagram updates on each phase via the /diagram API.")
