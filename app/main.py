"""Streamlit UI for AgenticOrNot."""

import json
import time
from typing import Dict, Any

import requests
import streamlit as st

# Configure page
st.set_page_config(
    page_title="AgenticOrNot v1.3.2",
    page_icon="🤖",
    layout="wide"
)

# API base URL
API_BASE = "http://localhost:8000"

def call_api(endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Call the FastAPI backend."""
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        try:
            error_detail = response.json().get("detail", str(e))
            st.error(f"API Error: {error_detail}")
        except:
            st.error(f"API Error: {e}")
        return {}
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {e}")
        return {}

def main():
    """Main Streamlit application."""
    st.title("🤖 AgenticOrNot v1.3.2")
    st.markdown("**Assess automation feasibility of your requirements**")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Debug mode
        debug_mode = st.checkbox("🐛 Debug Mode", help="Show detailed error messages and logs")
        
        # Provider selection
        provider = st.selectbox(
            "LLM Provider",
            ["fake", "openai", "claude", "bedrock"],
            index=0
        )
        
        if provider == "openai":
            model = st.selectbox(
                "Model",
                ["gpt-4o", "gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
                index=0
            )
        else:
            model = st.text_input("Model", value="fake-model")
        
        if provider != "fake":
            api_key = st.text_input("API Key", type="password")
            
            if st.button("Test Connection"):
                if api_key:
                    if debug_mode:
                        st.info(f"🔍 Testing {provider} with model {model}")
                    
                    result = call_api("/providers/test", "POST", {
                        "provider": provider,
                        "model": model,
                        "api_key": api_key
                    })
                    
                    if debug_mode:
                        st.json(result)
                    
                    if result.get("ok"):
                        st.success("✅ Connection successful")
                    else:
                        error_msg = result.get('message', 'Connection failed')
                        st.error(f"❌ {error_msg}")
                        
                        # Show helpful hints
                        if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
                            st.info("💡 **Tip**: Check that your API key is correct and has the right permissions")
                        elif "model" in error_msg.lower() and "not found" in error_msg.lower():
                            st.info("💡 **Tip**: Try using 'gpt-4o' or 'gpt-3.5-turbo' instead")
                        elif "rate limit" in error_msg.lower():
                            st.info("💡 **Tip**: You've hit the rate limit. Wait a moment and try again")
                else:
                    st.warning("Please enter an API key")
    
    # Main interface
    tab1, tab2, tab3 = st.tabs(["📝 Input", "❓ Q&A", "📊 Results"])
    
    with tab1:
        st.header("Requirement Input")
        
        # Input method selection
        input_method = st.radio(
            "Input Method",
            ["Text", "File Upload", "Jira"],
            horizontal=True
        )
        
        if input_method == "Text":
            description = st.text_area(
                "Describe your automation requirement:",
                placeholder="e.g., I need to automatically extract data from websites and store it in a database...",
                height=150
            )
            
            col1, col2 = st.columns(2)
            with col1:
                domain = st.selectbox(
                    "Domain (optional)",
                    ["", "data_processing", "system_integration", "document_management", "machine_learning"],
                    index=0
                )
            
            with col2:
                pattern_types = st.multiselect(
                    "Pattern Types (optional)",
                    ["web_automation", "api_integration", "document_processing", "ml_pipeline", "workflow_automation"]
                )
            
            if st.button("🚀 Start Analysis", type="primary"):
                if description:
                    payload = {
                        "text": description,
                        "domain": domain if domain else None,
                        "pattern_types": pattern_types
                    }
                    
                    result = call_api("/ingest", "POST", {
                        "source": "text",
                        "payload": payload
                    })
                    
                    if result.get("session_id"):
                        st.session_state.session_id = result["session_id"]
                        st.success(f"✅ Analysis started! Session ID: {result['session_id']}")
                        st.rerun()
                    else:
                        st.error("Failed to start analysis")
                else:
                    st.warning("Please enter a description")
        
        elif input_method == "File Upload":
            uploaded_file = st.file_uploader(
                "Upload requirement document",
                type=["txt", "md", "json"]
            )
            
            if uploaded_file and st.button("🚀 Start Analysis", type="primary"):
                content = uploaded_file.read().decode("utf-8")
                
                result = call_api("/ingest", "POST", {
                    "source": "file",
                    "payload": {
                        "content": content,
                        "filename": uploaded_file.name
                    }
                })
                
                if result.get("session_id"):
                    st.session_state.session_id = result["session_id"]
                    st.success(f"✅ Analysis started! Session ID: {result['session_id']}")
                    st.rerun()
        
        elif input_method == "Jira":
            st.info("🚧 Jira integration coming soon!")
    
    with tab2:
        st.header("Questions & Answers")
        
        if "session_id" not in st.session_state:
            st.info("👈 Please start an analysis in the Input tab first")
        else:
            session_id = st.session_state.session_id
            
            # Get session status
            status = call_api(f"/status/{session_id}")
            
            if status:
                st.write(f"**Phase:** {status.get('phase', 'Unknown')}")
                st.progress(status.get('progress', 0) / 100)
                
                if status.get('phase') == 'QNA' or status.get('missing_fields'):
                    st.subheader("Please answer the following questions:")
                    
                    # Generate questions (simplified - in real implementation, this would be more dynamic)
                    questions = [
                        {"text": "How often should this automation run?", "field": "frequency"},
                        {"text": "What is the criticality of this process?", "field": "criticality"},
                        {"text": "Does this process handle sensitive data?", "field": "data_sensitivity"}
                    ]
                    
                    answers = {}
                    for q in questions:
                        if q["field"] == "frequency":
                            answers[q["field"]] = st.selectbox(
                                q["text"],
                                ["", "hourly", "daily", "weekly", "monthly", "on-demand"],
                                key=f"q_{q['field']}"
                            )
                        elif q["field"] == "criticality":
                            answers[q["field"]] = st.selectbox(
                                q["text"],
                                ["", "low", "medium", "high", "critical"],
                                key=f"q_{q['field']}"
                            )
                        elif q["field"] == "data_sensitivity":
                            answers[q["field"]] = st.selectbox(
                                q["text"],
                                ["", "low", "medium", "high"],
                                key=f"q_{q['field']}"
                            )
                    
                    if st.button("Submit Answers"):
                        # Filter out empty answers
                        filtered_answers = {k: v for k, v in answers.items() if v}
                        
                        if filtered_answers:
                            result = call_api(f"/qa/{session_id}", "POST", {
                                "answers": filtered_answers
                            })
                            
                            if result.get("complete"):
                                st.success("✅ Q&A complete! Moving to pattern matching...")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.info("Thank you! Please refresh to see if more questions are needed.")
                        else:
                            st.warning("Please answer at least one question")
                else:
                    st.success("✅ Q&A phase complete!")
    
    with tab3:
        st.header("Analysis Results")
        
        if "session_id" not in st.session_state:
            st.info("👈 Please start an analysis in the Input tab first")
        else:
            session_id = st.session_state.session_id
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔍 Find Pattern Matches"):
                    with st.spinner("Finding pattern matches..."):
                        result = call_api("/match", "POST", {
                            "session_id": session_id,
                            "top_k": 5
                        })
                        
                        if result.get("candidates"):
                            st.session_state.matches = result["candidates"]
                            st.success(f"Found {len(result['candidates'])} pattern matches!")
                        else:
                            st.warning("No pattern matches found")
            
            with col2:
                if st.button("💡 Generate Recommendations"):
                    with st.spinner("Generating recommendations..."):
                        result = call_api("/recommend", "POST", {
                            "session_id": session_id,
                            "top_k": 3
                        })
                        
                        if result:
                            st.session_state.recommendations = result
                            st.success("Recommendations generated!")
                        else:
                            st.warning("Failed to generate recommendations")
            
            # Display results
            if "recommendations" in st.session_state:
                rec = st.session_state.recommendations
                
                st.subheader("🎯 Feasibility Assessment")
                
                # Feasibility badge
                feasibility = rec.get("feasibility", "Unknown")
                if feasibility == "Automatable":
                    st.success(f"✅ **{feasibility}**")
                elif feasibility == "Partially Automatable":
                    st.warning(f"⚠️ **{feasibility}**")
                else:
                    st.error(f"❌ **{feasibility}**")
                
                # Technology stack
                if rec.get("tech_stack"):
                    st.subheader("🛠️ Recommended Technology Stack")
                    cols = st.columns(min(len(rec["tech_stack"]), 4))
                    for i, tech in enumerate(rec["tech_stack"]):
                        with cols[i % 4]:
                            st.code(tech)
                
                # Reasoning
                if rec.get("reasoning"):
                    st.subheader("🧠 Reasoning")
                    st.write(rec["reasoning"])
                
                # Detailed recommendations
                if rec.get("recommendations"):
                    st.subheader("📋 Detailed Recommendations")
                    for i, recommendation in enumerate(rec["recommendations"], 1):
                        with st.expander(f"Recommendation {i}: {recommendation.get('pattern_id', 'Unknown')}"):
                            st.write(f"**Feasibility:** {recommendation.get('feasibility', 'Unknown')}")
                            st.write(f"**Confidence:** {recommendation.get('confidence', 0):.0%}")
                            st.write(f"**Reasoning:** {recommendation.get('reasoning', 'No reasoning provided')}")
                
                # Export options
                st.subheader("📤 Export Results")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("📄 Export JSON"):
                        result = call_api("/export", "POST", {
                            "session_id": session_id,
                            "format": "json"
                        })
                        if result.get("download_url"):
                            st.success(f"✅ Exported to: {result['download_url']}")
                
                with col2:
                    if st.button("📝 Export Markdown"):
                        result = call_api("/export", "POST", {
                            "session_id": session_id,
                            "format": "md"
                        })
                        if result.get("download_url"):
                            st.success(f"✅ Exported to: {result['download_url']}")
            
            elif "matches" in st.session_state:
                st.subheader("🔍 Pattern Matches")
                
                for i, match in enumerate(st.session_state.matches, 1):
                    with st.expander(f"Match {i}: {match.get('pattern_id', 'Unknown')} ({match.get('blended_score', 0):.0%})"):
                        st.write(f"**Pattern:** {match.get('pattern_name', 'Unknown')}")
                        st.write(f"**Score:** {match.get('blended_score', 0):.0%}")
                        st.write(f"**Rationale:** {match.get('rationale', 'No rationale provided')}")


if __name__ == "__main__":
    main()