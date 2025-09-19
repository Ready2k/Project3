"""System Configuration Management UI for AAA System.

This module provides a comprehensive interface for managing system-wide
configuration parameters that are currently hardcoded throughout the system.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
from dataclasses import asdict
import yaml
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

from app.config import Settings, load_settings
from app.config.system_config import (
    AutonomyConfig, PatternMatchingConfig, LLMGenerationConfig, RecommendationConfig,
    SystemConfiguration, SystemConfigurationManager
)
from app.utils.imports import require_service, optional_service
from app.utils.audit import get_audit_logger
from app.security.security_event_logger import SecurityEventLogger


def render_system_configuration() -> None:
    """Render the system configuration management interface."""
    st.header("🔧 System Configuration")
    st.write("Configure advanced system parameters for autonomy assessment, pattern matching, and recommendations.")
    
    # Initialize configuration manager
    if 'config_manager' not in st.session_state:
        st.session_state.config_manager = SystemConfigurationManager()
    
    config_manager = st.session_state.config_manager
    
    # Debug: Check if config has required attributes and auto-fix if needed
    try:
        # Test access to the problematic attribute
        _ = config_manager.config.autonomy.agentic_necessity_threshold
    except AttributeError as e:
        st.error(f"⚠️ Configuration Error: {e}")
        st.warning("This is a cached configuration issue. The system will automatically fix this.")
        
        # Automatically fix the issue
        st.info("🔄 Automatically resetting configuration...")
        
        # Clear session state and recreate config manager
        if 'config_manager' in st.session_state:
            del st.session_state.config_manager
        
        # Force recreation of config manager
        st.session_state.config_manager = SystemConfigurationManager()
        config_manager = st.session_state.config_manager
        
        # Verify the fix worked
        try:
            _ = config_manager.config.autonomy.agentic_necessity_threshold
            st.success("✅ Configuration fixed! The page will refresh automatically.")
            st.rerun()
        except AttributeError:
            st.error("❌ Unable to fix configuration automatically. Please restart the application.")
            return
    
    # Configuration tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "🤖 Autonomy Assessment", 
        "🔍 Pattern Matching", 
        "🧠 LLM Generation", 
        "💡 Recommendations",
        "🚦 Rate Limiting",
        "🗄️ Database Management",
        "🔗 API Endpoints",
        "⚙️ Management"
    ])
    
    with tab1:
        # Additional safety check before rendering
        try:
            render_autonomy_config(config_manager.config.autonomy)
        except AttributeError as e:
            st.error(f"Configuration rendering error: {e}")
            st.info("Please refresh the page or use the Management tab to reset configuration.")
    
    with tab2:
        render_pattern_matching_config(config_manager.config.pattern_matching)
    
    with tab3:
        render_llm_generation_config(config_manager.config.llm_generation)
    
    with tab4:
        render_recommendation_config(config_manager.config.recommendations)
    
    with tab5:
        render_rate_limiting_config(config_manager.config.rate_limiting)
    
    with tab6:
        render_database_management()
    
    with tab7:
        render_api_endpoints()
    
    with tab8:
        render_configuration_management(config_manager)


def render_autonomy_config(config: AutonomyConfig) -> None:
    """Render autonomy assessment configuration."""
    st.subheader("Autonomy Assessment Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Thresholds**")
        config.min_autonomy_threshold = st.slider(
            "Minimum Autonomy Threshold",
            min_value=0.0, max_value=1.0, value=config.min_autonomy_threshold, step=0.05,
            help="Minimum autonomy score required for agentic recommendations"
        )
        
        config.confidence_boost_factor = st.slider(
            "Confidence Boost Factor",
            min_value=1.0, max_value=2.0, value=config.confidence_boost_factor, step=0.1,
            help="Multiplier for boosting confidence in agentic solutions"
        )
        
        config.fully_automatable_threshold = st.slider(
            "Fully Automatable Threshold",
            min_value=0.0, max_value=1.0, value=config.fully_automatable_threshold, step=0.05,
            help="Score threshold for 'Fully Automatable' classification"
        )
        
        config.partially_automatable_threshold = st.slider(
            "Partially Automatable Threshold",
            min_value=0.0, max_value=1.0, value=config.partially_automatable_threshold, step=0.05,
            help="Score threshold for 'Partially Automatable' classification"
        )
        
        st.write("**Agentic Necessity Assessment**")
        config.agentic_necessity_threshold = st.slider(
            "Agentic Necessity Threshold",
            min_value=0.0, max_value=1.0, value=config.agentic_necessity_threshold, step=0.05,
            help="Score above which agentic AI is recommended over traditional automation"
        )
        
        config.traditional_suitability_threshold = st.slider(
            "Traditional Suitability Threshold",
            min_value=0.0, max_value=1.0, value=config.traditional_suitability_threshold, step=0.05,
            help="Score above which traditional automation is recommended over agentic AI"
        )
        
        config.hybrid_zone_threshold = st.slider(
            "Hybrid Zone Threshold",
            min_value=0.0, max_value=0.3, value=config.hybrid_zone_threshold, step=0.01,
            help="Score difference threshold for recommending hybrid approaches"
        )
    
    with col2:
        st.write("**Scoring Weights**")
        total_weight = 1.0
        
        config.reasoning_capability_weight = st.slider(
            "Reasoning Capability Weight",
            min_value=0.0, max_value=1.0, value=config.reasoning_capability_weight, step=0.05,
            help="Weight for reasoning capability in autonomy scoring"
        )
        
        config.decision_independence_weight = st.slider(
            "Decision Independence Weight",
            min_value=0.0, max_value=1.0, value=config.decision_independence_weight, step=0.05,
            help="Weight for decision independence in autonomy scoring"
        )
        
        config.exception_handling_weight = st.slider(
            "Exception Handling Weight",
            min_value=0.0, max_value=1.0, value=config.exception_handling_weight, step=0.05,
            help="Weight for exception handling capability"
        )
        
        config.learning_adaptation_weight = st.slider(
            "Learning Adaptation Weight",
            min_value=0.0, max_value=1.0, value=config.learning_adaptation_weight, step=0.05,
            help="Weight for learning and adaptation capability"
        )
        
        config.self_monitoring_weight = st.slider(
            "Self Monitoring Weight",
            min_value=0.0, max_value=1.0, value=config.self_monitoring_weight, step=0.05,
            help="Weight for self-monitoring capability"
        )
        
        # Show weight total
        current_total = (config.reasoning_capability_weight + config.decision_independence_weight + 
                        config.exception_handling_weight + config.learning_adaptation_weight + 
                        config.self_monitoring_weight)
        
        if abs(current_total - 1.0) > 0.01:
            st.warning(f"⚠️ Weights sum to {current_total:.2f}, should sum to 1.0")
        else:
            st.success(f"✅ Weights sum to {current_total:.2f}")


def render_pattern_matching_config(config: PatternMatchingConfig) -> None:
    """Render pattern matching configuration."""
    st.subheader("Pattern Matching Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Blending Weights**")
        config.tag_weight = st.slider(
            "Tag Weight",
            min_value=0.0, max_value=1.0, value=config.tag_weight, step=0.05,
            help="Weight for tag-based matching in pattern scoring"
        )
        
        config.vector_weight = st.slider(
            "Vector Weight",
            min_value=0.0, max_value=1.0, value=config.vector_weight, step=0.05,
            help="Weight for vector similarity in pattern scoring"
        )
        
        config.confidence_weight = st.slider(
            "Confidence Weight",
            min_value=0.0, max_value=1.0, value=config.confidence_weight, step=0.05,
            help="Weight for pattern confidence in scoring"
        )
        
        # Show weight total
        total = config.tag_weight + config.vector_weight + config.confidence_weight
        if abs(total - 1.0) > 0.01:
            st.warning(f"⚠️ Weights sum to {total:.2f}, should sum to 1.0")
        else:
            st.success(f"✅ Weights sum to {total:.2f}")
    
    with col2:
        st.write("**Similarity Thresholds**")
        config.strong_tag_match_threshold = st.slider(
            "Strong Tag Match Threshold",
            min_value=0.0, max_value=1.0, value=config.strong_tag_match_threshold, step=0.05,
            help="Threshold for classifying as 'strong tag match'"
        )
        
        config.high_similarity_threshold = st.slider(
            "High Similarity Threshold",
            min_value=0.0, max_value=1.0, value=config.high_similarity_threshold, step=0.05,
            help="Threshold for 'high semantic similarity'"
        )
        
        config.excellent_fit_threshold = st.slider(
            "Excellent Fit Threshold",
            min_value=0.0, max_value=1.0, value=config.excellent_fit_threshold, step=0.05,
            help="Threshold for 'excellent overall fit'"
        )


def render_llm_generation_config(config: LLMGenerationConfig) -> None:
    """Render LLM generation configuration."""
    st.subheader("LLM Generation Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Generation Parameters**")
        config.temperature = st.slider(
            "Temperature",
            min_value=0.0, max_value=2.0, value=config.temperature, step=0.1,
            help="Controls randomness in generation (0.0 = deterministic, 2.0 = very random)"
        )
        
        config.max_tokens = st.number_input(
            "Max Tokens",
            min_value=100, max_value=4000, value=config.max_tokens, step=100,
            help="Maximum number of tokens to generate"
        )
        
        config.top_p = st.slider(
            "Top P",
            min_value=0.0, max_value=1.0, value=config.top_p, step=0.05,
            help="Nucleus sampling parameter"
        )
    
    with col2:
        st.write("**Penalties & Timeouts**")
        config.frequency_penalty = st.slider(
            "Frequency Penalty",
            min_value=-2.0, max_value=2.0, value=config.frequency_penalty, step=0.1,
            help="Penalty for frequent tokens"
        )
        
        config.presence_penalty = st.slider(
            "Presence Penalty",
            min_value=-2.0, max_value=2.0, value=config.presence_penalty, step=0.1,
            help="Penalty for tokens that have appeared"
        )
        
        config.llm_timeout = st.number_input(
            "LLM Timeout (seconds)",
            min_value=5, max_value=120, value=config.llm_timeout, step=5,
            help="Timeout for LLM API calls"
        )


def render_recommendation_config(config: RecommendationConfig) -> None:
    """Render recommendation configuration."""
    st.subheader("Recommendation Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Confidence Thresholds**")
        config.min_recommendation_confidence = st.slider(
            "Minimum Recommendation Confidence",
            min_value=0.0, max_value=1.0, value=config.min_recommendation_confidence, step=0.05,
            help="Minimum confidence required to show recommendations"
        )
        
        config.tech_stack_inclusion_threshold = st.slider(
            "Tech Stack Inclusion Threshold",
            min_value=0.0, max_value=1.0, value=config.tech_stack_inclusion_threshold, step=0.05,
            help="Minimum score for including technology in recommendations"
        )
        
        config.new_pattern_creation_threshold = st.slider(
            "New Pattern Creation Threshold",
            min_value=0.0, max_value=1.0, value=config.new_pattern_creation_threshold, step=0.05,
            help="Threshold for creating new patterns when no good matches exist"
        )
    
    with col2:
        st.write("**Boost Factors**")
        config.autonomy_boost_factor = st.slider(
            "Autonomy Boost Factor",
            min_value=0.0, max_value=0.5, value=config.autonomy_boost_factor, step=0.05,
            help="Maximum boost factor for high autonomy (as fraction)"
        )
        
        config.reasoning_boost_amount = st.slider(
            "Reasoning Boost Amount",
            min_value=0.0, max_value=0.3, value=config.reasoning_boost_amount, step=0.05,
            help="Boost amount for good reasoning capabilities"
        )
        
        config.multi_agent_boost = st.slider(
            "Multi-Agent Boost",
            min_value=0.0, max_value=0.3, value=config.multi_agent_boost, step=0.05,
            help="Boost for multi-agent potential when appropriate"
        )


def render_rate_limiting_config(config: Any) -> None:
    """Render rate limiting configuration."""
    from app.config.system_config import RateLimitConfig
    
    st.subheader("API Rate Limiting Configuration")
    st.info("Configure rate limits to prevent API abuse while allowing normal Q&A interactions.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Default Tier Limits**")
        config.default_requests_per_minute = st.number_input(
            "Requests per Minute",
            min_value=10, max_value=500, value=config.default_requests_per_minute,
            help="Maximum requests per minute for default users"
        )
        
        config.default_requests_per_hour = st.number_input(
            "Requests per Hour",
            min_value=100, max_value=5000, value=config.default_requests_per_hour,
            help="Maximum requests per hour for default users"
        )
        
        config.default_requests_per_day = st.number_input(
            "Requests per Day",
            min_value=1000, max_value=50000, value=config.default_requests_per_day,
            help="Maximum requests per day for default users"
        )
        
        config.default_burst_limit = st.number_input(
            "Burst Limit",
            min_value=5, max_value=100, value=config.default_burst_limit,
            help="Maximum burst requests (important for Q&A interactions)"
        )
        
        config.default_burst_window_seconds = st.number_input(
            "Burst Window (seconds)",
            min_value=30, max_value=300, value=config.default_burst_window_seconds,
            help="Time window for burst limit reset"
        )
    
    with col2:
        st.write("**Premium & Enterprise Tiers**")
        
        st.write("*Premium Tier*")
        config.premium_requests_per_minute = st.number_input(
            "Premium: Requests per Minute",
            min_value=50, max_value=1000, value=config.premium_requests_per_minute,
            help="Premium tier requests per minute"
        )
        
        config.premium_burst_limit = st.number_input(
            "Premium: Burst Limit",
            min_value=20, max_value=200, value=config.premium_burst_limit,
            help="Premium tier burst limit"
        )
        
        st.write("*Enterprise Tier*")
        config.enterprise_requests_per_minute = st.number_input(
            "Enterprise: Requests per Minute",
            min_value=100, max_value=2000, value=config.enterprise_requests_per_minute,
            help="Enterprise tier requests per minute"
        )
        
        config.enterprise_burst_limit = st.number_input(
            "Enterprise: Burst Limit",
            min_value=50, max_value=500, value=config.enterprise_burst_limit,
            help="Enterprise tier burst limit"
        )
        
        st.write("*IP-Based Limits (Restrictive)*")
        config.ip_burst_limit = st.number_input(
            "IP-Based: Burst Limit",
            min_value=5, max_value=50, value=config.ip_burst_limit,
            help="Burst limit for IP-based identification"
        )
    
    # Rate limiting status and recommendations
    st.write("**Current Configuration Impact**")
    
    if config.default_burst_limit < 15:
        st.warning("⚠️ Low burst limit may cause issues with Q&A interactions. Consider increasing to 20+.")
    elif config.default_burst_limit >= 25:
        st.success("✅ Burst limit is sufficient for smooth Q&A interactions.")
    else:
        st.info("ℹ️ Burst limit is adequate but could be higher for better user experience.")
    
    # Show example scenarios
    with st.expander("📊 Rate Limiting Scenarios"):
        st.write("**Q&A Interaction Example:**")
        st.write(f"- User loads questions: 1 request")
        st.write(f"- User submits answers: 1 request") 
        st.write(f"- System processes: 2-3 requests")
        st.write(f"- **Total burst needed: 4-5 requests**")
        st.write(f"- **Current burst limit: {config.default_burst_limit} requests** ✅" if config.default_burst_limit >= 10 else f"- **Current burst limit: {config.default_burst_limit} requests** ⚠️")


def render_configuration_management(config_manager: SystemConfigurationManager) -> None:
    """Render configuration management tools."""
    st.subheader("Configuration Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Configuration", use_container_width=True, key="save_config_btn"):
            if config_manager.save_config():
                st.success("✅ Configuration saved successfully!")
            else:
                st.error("❌ Failed to save configuration")
    
    with col2:
        if st.button("🔄 Reset to Defaults", use_container_width=True, key="reset_config_btn"):
            config_manager.reset_to_defaults()
            st.success("✅ Configuration reset to defaults")
            st.rerun()
    
    with col3:
        if st.button("📤 Export Configuration", use_container_width=True, key="export_config_btn"):
            config_dict = config_manager.export_config()
            st.download_button(
                "Download Config",
                data=yaml.dump(config_dict, default_flow_style=False, indent=2),
                file_name="system_config.yaml",
                mime="application/yaml",
                key="download_config_btn"
            )
    
    st.write("---")
    
    # Import configuration
    st.write("**Import Configuration**")
    uploaded_file = st.file_uploader("Upload configuration file", type=['yaml', 'yml'])
    
    if uploaded_file is not None:
        try:
            config_dict = yaml.safe_load(uploaded_file)
            if st.button("Import Configuration", key="import_config_btn"):
                if config_manager.import_config(config_dict):
                    st.success("✅ Configuration imported successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to import configuration")
        except Exception as e:
            st.error(f"Error reading configuration file: {e}")
    
    # Configuration preview
    with st.expander("📋 Current Configuration Preview"):
        st.code(yaml.dump(config_manager.export_config(), default_flow_style=False, indent=2), language='yaml')


def render_api_endpoints() -> None:
    """Render API endpoints information and testing interface."""
    st.subheader("🔗 API Endpoints")
    st.write("Explore and test the AAA system API endpoints directly from your browser.")
    
    # Try to determine the API base URL
    api_base_url = "http://localhost:8000"
    
    # API endpoint categories
    st.write("### 🏥 Health & Monitoring")
    
    health_endpoints = [
        {
            "method": "GET",
            "path": "/health",
            "description": "Enhanced basic health check with system metrics and component status",
            "color": "🟢"
        },
        {
            "method": "GET", 
            "path": "/health/detailed",
            "description": "Comprehensive health diagnostics with all system components",
            "color": "🟡"
        },
        {
            "method": "GET",
            "path": "/health/readiness", 
            "description": "Kubernetes readiness probe (critical components only)",
            "color": "🔵"
        },
        {
            "method": "GET",
            "path": "/health/liveness",
            "description": "Kubernetes liveness probe (basic system resources)",
            "color": "🔵"
        }
    ]
    
    for endpoint in health_endpoints:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.write(f"{endpoint['color']} **{endpoint['method']}**")
        with col2:
            st.write(f"`{endpoint['path']}`")
            st.caption(endpoint['description'])
        with col3:
            full_url = f"{api_base_url}{endpoint['path']}"
            st.link_button("🔗 Open", full_url, use_container_width=True)
    
    st.write("### 🔒 Security")
    
    security_endpoints = [
        {
            "method": "GET",
            "path": "/security/scan",
            "description": "Run security scans (full, code, dependencies, configuration)",
            "color": "🔴"
        },
        {
            "method": "GET",
            "path": "/security/history",
            "description": "Get security scan history with configurable limit",
            "color": "🟡"
        }
    ]
    
    for endpoint in security_endpoints:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.write(f"{endpoint['color']} **{endpoint['method']}**")
        with col2:
            st.write(f"`{endpoint['path']}`")
            st.caption(endpoint['description'])
        with col3:
            full_url = f"{api_base_url}{endpoint['path']}"
            st.link_button("🔗 Open", full_url, use_container_width=True)
    
    st.write("### 📋 Core Analysis Workflow")
    
    workflow_endpoints = [
        {
            "method": "POST",
            "path": "/ingest",
            "description": "Start new session - Ingest requirements from text, file, or Jira",
            "color": "🟢",
            "requires_data": True
        },
        {
            "method": "GET",
            "path": "/status/{session_id}",
            "description": "Get session status, progress, and current phase",
            "color": "🟢",
            "note": "Replace {session_id} with actual session ID"
        },
        {
            "method": "GET",
            "path": "/qa/{session_id}/questions",
            "description": "Get AI-generated clarifying questions",
            "color": "🟡",
            "note": "Replace {session_id} with actual session ID"
        },
        {
            "method": "POST",
            "path": "/qa/{session_id}",
            "description": "Submit Q&A answers to refine requirements",
            "color": "🟡",
            "requires_data": True,
            "note": "Replace {session_id} with actual session ID"
        },
        {
            "method": "POST",
            "path": "/match",
            "description": "Match requirements against pattern library",
            "color": "🔵",
            "requires_data": True
        },
        {
            "method": "POST",
            "path": "/recommend",
            "description": "Generate AI-powered feasibility assessment and recommendations",
            "color": "🟢",
            "requires_data": True
        },
        {
            "method": "POST",
            "path": "/export",
            "description": "Export results in JSON, Markdown, or HTML formats",
            "color": "🟢",
            "requires_data": True
        }
    ]
    
    for endpoint in workflow_endpoints:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.write(f"{endpoint['color']} **{endpoint['method']}**")
        with col2:
            st.write(f"`{endpoint['path']}`")
            st.caption(endpoint['description'])
            if endpoint.get('note'):
                st.caption(f"ℹ️ {endpoint['note']}")
            if endpoint.get('requires_data'):
                st.caption("📝 Requires request body")
        with col3:
            if endpoint.get('requires_data'):
                st.caption("POST endpoint")
            else:
                full_url = f"{api_base_url}{endpoint['path']}"
                st.link_button("🔗 Open", full_url, use_container_width=True)
    
    st.write("### 🤖 LLM Provider Management")
    
    provider_endpoints = [
        {
            "method": "POST",
            "path": "/providers/test",
            "description": "Test LLM provider connection and authentication",
            "color": "🟡",
            "requires_data": True
        },
        {
            "method": "POST",
            "path": "/providers/models",
            "description": "Discover available models for a provider",
            "color": "🟡",
            "requires_data": True
        },
        {
            "method": "POST",
            "path": "/providers/bedrock/generate-credentials",
            "description": "Generate short-term AWS credentials for Bedrock",
            "color": "🔴",
            "requires_data": True
        }
    ]
    
    for endpoint in provider_endpoints:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.write(f"{endpoint['color']} **{endpoint['method']}**")
        with col2:
            st.write(f"`{endpoint['path']}`")
            st.caption(endpoint['description'])
            if endpoint.get('requires_data'):
                st.caption("📝 Requires request body")
        with col3:
            st.caption("POST endpoint")
    
    st.write("### 🎫 Jira Integration")
    
    jira_endpoints = [
        {
            "method": "POST",
            "path": "/jira/test",
            "description": "Test Jira connection with Data Center support",
            "color": "🟡",
            "requires_data": True
        },
        {
            "method": "POST",
            "path": "/jira/fetch",
            "description": "Fetch Jira ticket data for analysis",
            "color": "🟡",
            "requires_data": True
        }
    ]
    
    for endpoint in jira_endpoints:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.write(f"{endpoint['color']} **{endpoint['method']}**")
        with col2:
            st.write(f"`{endpoint['path']}`")
            st.caption(endpoint['description'])
            if endpoint.get('requires_data'):
                st.caption("📝 Requires request body")
        with col3:
            st.caption("POST endpoint")
    
    st.write("### 📚 Documentation & API Info")
    
    doc_endpoints = [
        {
            "method": "GET",
            "path": "/docs",
            "description": "Interactive API documentation (Swagger UI)",
            "color": "🟢"
        },
        {
            "method": "GET",
            "path": "/redoc",
            "description": "Alternative API documentation (ReDoc)",
            "color": "🟢"
        },
        {
            "method": "GET",
            "path": "/openapi.json",
            "description": "OpenAPI specification in JSON format",
            "color": "🔵"
        }
    ]
    
    for endpoint in doc_endpoints:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.write(f"{endpoint['color']} **{endpoint['method']}**")
        with col2:
            st.write(f"`{endpoint['path']}`")
            st.caption(endpoint['description'])
        with col3:
            full_url = f"{api_base_url}{endpoint['path']}"
            st.link_button("🔗 Open", full_url, use_container_width=True)
    
    # Quick API testing section
    st.write("---")
    st.write("### 🧪 Quick API Testing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Health Check Test**")
        if st.button("🏥 Test Basic Health", use_container_width=True):
            try:
                import requests
                response = requests.get(f"{api_base_url}/health", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"✅ API is healthy! Status: {data.get('status', 'unknown')}")
                    st.json(data)
                else:
                    st.error(f"❌ API returned status {response.status_code}")
            except Exception as e:
                st.error(f"❌ Failed to connect to API: {e}")
                st.info("Make sure the API server is running on localhost:8000")
    
    with col2:
        st.write("**Documentation Access**")
        st.link_button("📖 Open Swagger UI", f"{api_base_url}/docs", use_container_width=True)
        st.link_button("📋 Open ReDoc", f"{api_base_url}/redoc", use_container_width=True)
    
    # Usage tips
    st.write("---")
    st.write("### 💡 Usage Tips")
    
    with st.expander("🔍 How to use these endpoints"):
        st.write("""
        **GET Endpoints (Green/Blue):**
        - Click the "🔗 Open" button to test directly in your browser
        - No additional data required
        
        **POST Endpoints (Yellow/Red):**
        - Require request body data (JSON)
        - Use tools like curl, Postman, or the Swagger UI at `/docs`
        - Examples available in the API documentation
        
        **Color Coding:**
        - 🟢 Green: Safe to test, read-only operations
        - 🟡 Yellow: Requires data, moderate complexity
        - 🔵 Blue: System information, safe to access
        - 🔴 Red: Advanced operations, use with caution
        
        **Session IDs:**
        - Replace `{session_id}` with actual session ID from `/ingest` response
        - Session IDs are UUIDs (e.g., `123e4567-e89b-12d3-a456-426614174000`)
        """)
    
    with st.expander("🚀 Common Workflows"):
        st.write("""
        **1. Basic Analysis Workflow:**
        1. POST `/ingest` - Start new session
        2. GET `/status/{session_id}` - Check progress
        3. GET `/qa/{session_id}/questions` - Get questions (if needed)
        4. POST `/qa/{session_id}` - Submit answers (if needed)
        5. POST `/recommend` - Generate recommendations
        6. POST `/export` - Export results
        
        **2. Health Monitoring:**
        1. GET `/health` - Quick system status
        2. GET `/health/detailed` - Comprehensive diagnostics
        3. GET `/security/scan` - Security assessment
        
        **3. Provider Testing:**
        1. POST `/providers/test` - Test LLM connection
        2. POST `/providers/models` - Discover available models
        """)


def render_database_management():
    """Render database management interface for viewing and managing database content."""
    st.subheader("🗄️ Database Management")
    st.write("View, filter, and manage content in the system databases.")
    
    # Database selection
    db_option = st.selectbox(
        "Select Database",
        ["Audit Database (audit.db)", "Security Database (security_audit.db)"],
        help="Choose which database to manage"
    )
    
    if db_option == "Audit Database (audit.db)":
        render_audit_database_management()
    else:
        render_security_database_management()


def render_audit_database_management():
    """Render audit database management interface."""
    st.write("### 📊 Audit Database Management")
    
    try:
        audit_logger = get_audit_logger()
        
        # Database statistics
        with sqlite3.connect(audit_logger.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM runs")
            total_runs = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM matches")
            total_matches = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT MIN(created_at), MAX(created_at) FROM runs WHERE created_at IS NOT NULL")
            date_range = cursor.fetchone()
        
        # Display statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total LLM Calls", total_runs)
        with col2:
            st.metric("Total Pattern Matches", total_matches)
        with col3:
            if date_range[0] and date_range[1]:
                st.metric("Date Range", f"{date_range[0][:10]} to {date_range[1][:10]}")
            else:
                st.metric("Date Range", "No data")
        
        # Management options
        st.write("### Management Options")
        
        tab1, tab2, tab3 = st.tabs(["🔍 View Data", "📊 Analytics", "🗑️ Cleanup"])
        
        with tab1:
            render_audit_data_viewer(audit_logger)
        
        with tab2:
            render_audit_analytics(audit_logger)
        
        with tab3:
            render_audit_cleanup(audit_logger)
            
    except Exception as e:
        st.error(f"Error accessing audit database: {e}")
        st.info("Make sure the audit database exists and is accessible.")


def render_audit_data_viewer(audit_logger):
    """Render audit data viewer."""
    st.write("#### 📋 Data Viewer")
    
    # Table selection
    table_option = st.selectbox("Select Table", ["LLM Calls (runs)", "Pattern Matches (matches)"])
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        limit = st.number_input("Limit Results", min_value=10, max_value=1000, value=100)
    with col2:
        if table_option == "LLM Calls (runs)":
            provider_filter = st.text_input("Provider Filter (optional)")
        else:
            pattern_filter = st.text_input("Pattern ID Filter (optional)")
    with col3:
        session_filter = st.text_input("Session ID Filter (optional)")
    
    if st.button("🔍 Load Data", key="load_audit_data_btn"):
        try:
            if table_option == "LLM Calls (runs)":
                # Load LLM calls
                query = "SELECT * FROM runs WHERE 1=1"
                params = []
                
                if provider_filter:
                    query += " AND provider LIKE ?"
                    params.append(f"%{provider_filter}%")
                
                if session_filter:
                    query += " AND session_id LIKE ?"
                    params.append(f"%{session_filter}%")
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                
                with sqlite3.connect(audit_logger.db_path) as conn:
                    df = pd.read_sql_query(query, conn, params=params)
                
                if not df.empty:
                    st.write(f"**Found {len(df)} LLM calls:**")
                    
                    # Display data with selection
                    selected_rows = st.dataframe(
                        df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "prompt": st.column_config.TextColumn("Prompt", width="medium"),
                            "response": st.column_config.TextColumn("Response", width="medium"),
                            "created_at": st.column_config.DatetimeColumn("Created At")
                        }
                    )
                    
                    # Bulk delete option
                    if st.checkbox("Enable bulk delete", key="enable_bulk_delete_runs"):
                        selected_ids = st.multiselect(
                            "Select records to delete",
                            options=df['id'].tolist(),
                            format_func=lambda x: f"ID {x} - {df[df['id']==x]['provider'].iloc[0]} - {df[df['id']==x]['created_at'].iloc[0]}",
                            key="select_runs_to_delete"
                        )
                        
                        if selected_ids and st.button("🗑️ Delete Selected Records", type="secondary", key="delete_selected_runs_btn"):
                            if st.checkbox("I confirm I want to delete these records", key="confirm_delete_selected_runs"):
                                with sqlite3.connect(audit_logger.db_path) as conn:
                                    placeholders = ','.join(['?' for _ in selected_ids])
                                    cursor = conn.execute(f"DELETE FROM runs WHERE id IN ({placeholders})", selected_ids)
                                    deleted_count = cursor.rowcount
                                    conn.commit()
                                st.success(f"✅ Deleted {deleted_count} records")
                                st.rerun()
                else:
                    st.info("No LLM calls found matching the criteria.")
            
            else:
                # Load pattern matches
                query = "SELECT * FROM matches WHERE 1=1"
                params = []
                
                if pattern_filter:
                    query += " AND pattern_id LIKE ?"
                    params.append(f"%{pattern_filter}%")
                
                if session_filter:
                    query += " AND session_id LIKE ?"
                    params.append(f"%{session_filter}%")
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                
                with sqlite3.connect(audit_logger.db_path) as conn:
                    df = pd.read_sql_query(query, conn, params=params)
                
                if not df.empty:
                    st.write(f"**Found {len(df)} pattern matches:**")
                    
                    # Display data
                    st.dataframe(
                        df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "created_at": st.column_config.DatetimeColumn("Created At"),
                            "score": st.column_config.NumberColumn("Score", format="%.3f")
                        }
                    )
                    
                    # Bulk delete option
                    if st.checkbox("Enable bulk delete", key="enable_bulk_delete_matches"):
                        selected_ids = st.multiselect(
                            "Select records to delete",
                            options=df['id'].tolist(),
                            format_func=lambda x: f"ID {x} - {df[df['id']==x]['pattern_id'].iloc[0]} - Score: {df[df['id']==x]['score'].iloc[0]:.3f}",
                            key="select_matches_to_delete"
                        )
                        
                        if selected_ids and st.button("🗑️ Delete Selected Records", type="secondary", key="delete_selected_matches_btn"):
                            if st.checkbox("I confirm I want to delete these records", key="confirm_delete_selected_matches"):
                                with sqlite3.connect(audit_logger.db_path) as conn:
                                    placeholders = ','.join(['?' for _ in selected_ids])
                                    cursor = conn.execute(f"DELETE FROM matches WHERE id IN ({placeholders})", selected_ids)
                                    deleted_count = cursor.rowcount
                                    conn.commit()
                                st.success(f"✅ Deleted {deleted_count} records")
                                st.rerun()
                else:
                    st.info("No pattern matches found matching the criteria.")
                    
        except Exception as e:
            st.error(f"Error loading data: {e}")


def render_audit_analytics(audit_logger):
    """Render audit analytics."""
    st.write("#### 📊 Analytics")
    
    try:
        with sqlite3.connect(audit_logger.db_path) as conn:
            # Provider statistics
            st.write("**Provider Usage:**")
            provider_df = pd.read_sql_query("""
                SELECT provider, COUNT(*) as calls, AVG(latency_ms) as avg_latency,
                       SUM(tokens) as total_tokens, MAX(created_at) as last_used
                FROM runs 
                GROUP BY provider 
                ORDER BY calls DESC
            """, conn)
            
            if not provider_df.empty:
                st.dataframe(
                    provider_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "avg_latency": st.column_config.NumberColumn("Avg Latency (ms)", format="%.1f"),
                        "total_tokens": st.column_config.NumberColumn("Total Tokens"),
                        "last_used": st.column_config.DatetimeColumn("Last Used")
                    }
                )
            
            # Pattern statistics
            st.write("**Pattern Match Statistics:**")
            pattern_df = pd.read_sql_query("""
                SELECT pattern_id, COUNT(*) as matches, AVG(score) as avg_score,
                       MAX(score) as max_score, MAX(created_at) as last_matched
                FROM matches 
                GROUP BY pattern_id 
                ORDER BY matches DESC
            """, conn)
            
            if not pattern_df.empty:
                st.dataframe(
                    pattern_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "avg_score": st.column_config.NumberColumn("Avg Score", format="%.3f"),
                        "max_score": st.column_config.NumberColumn("Max Score", format="%.3f"),
                        "last_matched": st.column_config.DatetimeColumn("Last Matched")
                    }
                )
            
            # Recent activity
            st.write("**Recent Activity (Last 24 Hours):**")
            recent_df = pd.read_sql_query("""
                SELECT DATE(created_at) as date, COUNT(*) as calls
                FROM runs 
                WHERE created_at >= datetime('now', '-7 days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """, conn)
            
            if not recent_df.empty:
                st.bar_chart(recent_df.set_index('date'))
            else:
                st.info("No recent activity found.")
                
    except Exception as e:
        st.error(f"Error generating analytics: {e}")


def render_audit_cleanup(audit_logger):
    """Render audit cleanup options."""
    st.write("#### 🗑️ Cleanup Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Clean Old Records**")
        days_to_keep = st.number_input("Keep records newer than (days)", min_value=1, max_value=365, value=30)
        
        if st.button("🗑️ Clean Old Records", type="secondary", key="clean_old_audit_records_btn"):
            if st.checkbox("I confirm I want to delete old records", key="confirm_clean_old_audit_records"):
                try:
                    deleted_count = audit_logger.cleanup_old_records(days=days_to_keep)
                    st.success(f"✅ Deleted {deleted_count} old records (older than {days_to_keep} days)")
                except Exception as e:
                    st.error(f"Error cleaning old records: {e}")
    
    with col2:
        st.write("**Clean Test Data**")
        st.info("Remove records from test providers and sessions")
        
        if st.button("🗑️ Clean Test Data", type="secondary", key="clean_test_audit_data_btn"):
            if st.checkbox("I confirm I want to delete test data", key="confirm_clean_test_audit_data"):
                try:
                    with sqlite3.connect(audit_logger.db_path) as conn:
                        # Delete test provider data
                        cursor = conn.execute("""
                            DELETE FROM runs 
                            WHERE provider IN ('fake', 'MockLLM', 'error-provider', 'AuditedLLMProvider')
                            OR session_id LIKE 'test-%'
                            OR session_id LIKE '%test%'
                        """)
                        runs_deleted = cursor.rowcount
                        
                        cursor = conn.execute("""
                            DELETE FROM matches 
                            WHERE session_id LIKE 'test-%'
                            OR session_id LIKE '%test%'
                        """)
                        matches_deleted = cursor.rowcount
                        
                        conn.commit()
                    
                    total_deleted = runs_deleted + matches_deleted
                    st.success(f"✅ Deleted {total_deleted} test records (runs: {runs_deleted}, matches: {matches_deleted})")
                except Exception as e:
                    st.error(f"Error cleaning test data: {e}")
    
    # Dangerous operations
    st.write("---")
    st.write("**⚠️ Dangerous Operations**")
    
    with st.expander("🚨 Complete Database Reset"):
        st.warning("This will delete ALL data in the audit database. This action cannot be undone!")
        
        if st.text_input("Type 'DELETE ALL DATA' to confirm", key="confirm_delete_all_audit_input") == "DELETE ALL DATA":
            if st.button("🚨 DELETE ALL AUDIT DATA", type="secondary", key="delete_all_audit_data_btn"):
                try:
                    with sqlite3.connect(audit_logger.db_path) as conn:
                        cursor = conn.execute("DELETE FROM runs")
                        runs_deleted = cursor.rowcount
                        
                        cursor = conn.execute("DELETE FROM matches")
                        matches_deleted = cursor.rowcount
                        
                        conn.commit()
                    
                    st.success(f"✅ Deleted ALL data: {runs_deleted} runs, {matches_deleted} matches")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting all data: {e}")


def render_security_database_management():
    """Render security database management interface."""
    st.write("### 🔒 Security Database Management")
    
    try:
        security_logger = SecurityEventLogger()
        
        # Database statistics
        with sqlite3.connect(security_logger.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM security_events")
            total_events = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM security_metrics")
            total_metrics = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT MIN(timestamp), MAX(timestamp) FROM security_events WHERE timestamp IS NOT NULL")
            date_range = cursor.fetchone()
        
        # Display statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Security Events", total_events)
        with col2:
            st.metric("Metrics Records", total_metrics)
        with col3:
            if date_range[0] and date_range[1]:
                st.metric("Date Range", f"{date_range[0][:10]} to {date_range[1][:10]}")
            else:
                st.metric("Date Range", "No data")
        
        # Management options
        st.write("### Management Options")
        
        tab1, tab2, tab3 = st.tabs(["🔍 View Events", "📊 Security Analytics", "🗑️ Cleanup"])
        
        with tab1:
            render_security_data_viewer(security_logger)
        
        with tab2:
            render_security_analytics(security_logger)
        
        with tab3:
            render_security_cleanup(security_logger)
            
    except Exception as e:
        st.error(f"Error accessing security database: {e}")
        st.info("Make sure the security database exists and is accessible.")


def render_security_data_viewer(security_logger):
    """Render security data viewer."""
    st.write("#### 🔍 Security Events Viewer")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        limit = st.number_input("Limit Results", min_value=10, max_value=500, value=50)
    with col2:
        action_filter = st.selectbox("Action Filter", ["All", "BLOCK", "FLAG", "PASS"])
    with col3:
        severity_filter = st.selectbox("Severity Filter", ["All", "low", "medium", "high", "critical"])
    with col4:
        session_filter = st.text_input("Session ID Filter (optional)")
    
    if st.button("🔍 Load Security Events", key="load_security_events_btn"):
        try:
            query = "SELECT * FROM security_events WHERE 1=1"
            params = []
            
            if action_filter != "All":
                query += " AND action = ?"
                params.append(action_filter)
            
            if severity_filter != "All":
                query += " AND alert_severity = ?"
                params.append(severity_filter)
            
            if session_filter:
                query += " AND session_id LIKE ?"
                params.append(f"%{session_filter}%")
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            with sqlite3.connect(security_logger.db_path) as conn:
                df = pd.read_sql_query(query, conn, params=params)
            
            if not df.empty:
                st.write(f"**Found {len(df)} security events:**")
                
                # Process JSON columns for display
                display_df = df.copy()
                if 'detected_attacks' in display_df.columns:
                    display_df['attack_count'] = display_df['detected_attacks'].apply(
                        lambda x: len(json.loads(x)) if x else 0
                    )
                
                # Display data
                st.dataframe(
                    display_df[['event_id', 'timestamp', 'action', 'confidence', 'alert_severity', 
                               'attack_count', 'input_length', 'processing_time_ms']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "timestamp": st.column_config.DatetimeColumn("Timestamp"),
                        "confidence": st.column_config.NumberColumn("Confidence", format="%.3f"),
                        "processing_time_ms": st.column_config.NumberColumn("Processing Time (ms)", format="%.1f")
                    }
                )
                
                # Event details
                if st.checkbox("Show detailed event information", key="show_security_event_details"):
                    selected_event_id = st.selectbox(
                        "Select event for details",
                        options=df['event_id'].tolist(),
                        key="select_security_event_details"
                    )
                    
                    if selected_event_id:
                        event_row = df[df['event_id'] == selected_event_id].iloc[0]
                        
                        st.write("**Event Details:**")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Event ID:** {event_row['event_id']}")
                            st.write(f"**Timestamp:** {event_row['timestamp']}")
                            st.write(f"**Action:** {event_row['action']}")
                            st.write(f"**Confidence:** {event_row['confidence']:.3f}")
                            st.write(f"**Alert Severity:** {event_row['alert_severity']}")
                            st.write(f"**Progressive Level:** {event_row['progressive_response_level']}")
                        
                        with col2:
                            st.write(f"**Input Length:** {event_row['input_length']}")
                            st.write(f"**Processing Time:** {event_row['processing_time_ms']:.1f}ms")
                            
                            if event_row['input_preview']:
                                st.write("**Input Preview:**")
                                st.text_area("", value=event_row['input_preview'], height=100, disabled=True, key="security_event_input_preview")
                        
                        # Show detected attacks
                        if event_row['detected_attacks']:
                            attacks = json.loads(event_row['detected_attacks'])
                            if attacks:
                                st.write("**Detected Attacks:**")
                                for i, attack in enumerate(attacks):
                                    st.write(f"{i+1}. **{attack.get('name', 'Unknown')}** ({attack.get('category', 'Unknown')})")
                                    st.write(f"   - Severity: {attack.get('severity', 'Unknown')}")
                                    st.write(f"   - Description: {attack.get('description', 'No description')}")
                
                # Bulk delete option
                if st.checkbox("Enable bulk delete", key="enable_bulk_delete_security_events"):
                    selected_ids = st.multiselect(
                        "Select events to delete",
                        options=df['id'].tolist(),
                        format_func=lambda x: f"ID {x} - {df[df['id']==x]['event_id'].iloc[0]} - {df[df['id']==x]['action'].iloc[0]}",
                        key="select_security_events_to_delete"
                    )
                    
                    if selected_ids and st.button("🗑️ Delete Selected Events", type="secondary", key="delete_selected_security_events_btn"):
                        if st.checkbox("I confirm I want to delete these security events", key="confirm_delete_selected_security_events"):
                            with sqlite3.connect(security_logger.db_path) as conn:
                                placeholders = ','.join(['?' for _ in selected_ids])
                                cursor = conn.execute(f"DELETE FROM security_events WHERE id IN ({placeholders})", selected_ids)
                                deleted_count = cursor.rowcount
                                conn.commit()
                            st.success(f"✅ Deleted {deleted_count} security events")
                            st.rerun()
            else:
                st.info("No security events found matching the criteria.")
                
        except Exception as e:
            st.error(f"Error loading security events: {e}")


def render_security_analytics(security_logger):
    """Render security analytics."""
    st.write("#### 📊 Security Analytics")
    
    try:
        with sqlite3.connect(security_logger.db_path) as conn:
            # Action statistics
            st.write("**Security Actions:**")
            action_df = pd.read_sql_query("""
                SELECT action, COUNT(*) as count, AVG(confidence) as avg_confidence,
                       AVG(processing_time_ms) as avg_processing_time
                FROM security_events 
                GROUP BY action 
                ORDER BY count DESC
            """, conn)
            
            if not action_df.empty:
                st.dataframe(
                    action_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "avg_confidence": st.column_config.NumberColumn("Avg Confidence", format="%.3f"),
                        "avg_processing_time": st.column_config.NumberColumn("Avg Processing Time (ms)", format="%.1f")
                    }
                )
            
            # Severity distribution
            st.write("**Alert Severity Distribution:**")
            severity_df = pd.read_sql_query("""
                SELECT alert_severity, COUNT(*) as count
                FROM security_events 
                GROUP BY alert_severity 
                ORDER BY 
                    CASE alert_severity 
                        WHEN 'critical' THEN 1 
                        WHEN 'high' THEN 2 
                        WHEN 'medium' THEN 3 
                        WHEN 'low' THEN 4 
                    END
            """, conn)
            
            if not severity_df.empty:
                st.bar_chart(severity_df.set_index('alert_severity'))
            
            # Recent activity
            st.write("**Recent Security Activity (Last 7 Days):**")
            recent_df = pd.read_sql_query("""
                SELECT DATE(timestamp) as date, action, COUNT(*) as count
                FROM security_events 
                WHERE timestamp >= datetime('now', '-7 days')
                GROUP BY DATE(timestamp), action
                ORDER BY date DESC
            """, conn)
            
            if not recent_df.empty:
                # Pivot for better visualization
                pivot_df = recent_df.pivot(index='date', columns='action', values='count').fillna(0)
                st.bar_chart(pivot_df)
            else:
                st.info("No recent security activity found.")
                
    except Exception as e:
        st.error(f"Error generating security analytics: {e}")


def render_security_cleanup(security_logger):
    """Render security cleanup options."""
    st.write("#### 🗑️ Security Cleanup Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Clean Old Events**")
        days_to_keep = st.number_input("Keep events newer than (days)", min_value=1, max_value=365, value=90)
        
        if st.button("🗑️ Clean Old Security Events", type="secondary", key="clean_old_security_events_btn"):
            if st.checkbox("I confirm I want to delete old security events", key="confirm_clean_old_security_events"):
                try:
                    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
                    
                    with sqlite3.connect(security_logger.db_path) as conn:
                        cursor = conn.execute("DELETE FROM security_events WHERE timestamp < ?", (cutoff_date,))
                        events_deleted = cursor.rowcount
                        
                        cursor = conn.execute("DELETE FROM security_metrics WHERE timestamp < ?", (cutoff_date,))
                        metrics_deleted = cursor.rowcount
                        
                        conn.commit()
                    
                    st.success(f"✅ Deleted {events_deleted} old events and {metrics_deleted} old metrics (older than {days_to_keep} days)")
                except Exception as e:
                    st.error(f"Error cleaning old security data: {e}")
    
    with col2:
        st.write("**Clean by Severity**")
        severity_to_clean = st.selectbox("Clean events with severity", ["low", "medium", "high", "critical"])
        
        if st.button(f"🗑️ Clean {severity_to_clean.title()} Severity Events", type="secondary", key="clean_severity_events_btn"):
            if st.checkbox(f"I confirm I want to delete all {severity_to_clean} severity events", key="confirm_clean_severity_events"):
                try:
                    with sqlite3.connect(security_logger.db_path) as conn:
                        cursor = conn.execute("DELETE FROM security_events WHERE alert_severity = ?", (severity_to_clean,))
                        deleted_count = cursor.rowcount
                        conn.commit()
                    
                    st.success(f"✅ Deleted {deleted_count} {severity_to_clean} severity events")
                except Exception as e:
                    st.error(f"Error cleaning {severity_to_clean} severity events: {e}")
    
    # Dangerous operations
    st.write("---")
    st.write("**⚠️ Dangerous Operations**")
    
    with st.expander("🚨 Complete Security Database Reset"):
        st.warning("This will delete ALL data in the security database. This action cannot be undone!")
        
        if st.text_input("Type 'DELETE ALL SECURITY DATA' to confirm", key="confirm_delete_all_security_input") == "DELETE ALL SECURITY DATA":
            if st.button("🚨 DELETE ALL SECURITY DATA", type="secondary", key="delete_all_security_data_btn"):
                try:
                    with sqlite3.connect(security_logger.db_path) as conn:
                        cursor = conn.execute("DELETE FROM security_events")
                        events_deleted = cursor.rowcount
                        
                        cursor = conn.execute("DELETE FROM security_metrics")
                        metrics_deleted = cursor.rowcount
                        
                        conn.commit()
                    
                    st.success(f"✅ Deleted ALL security data: {events_deleted} events, {metrics_deleted} metrics")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting all security data: {e}")