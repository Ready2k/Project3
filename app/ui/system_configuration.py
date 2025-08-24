"""System Configuration Management UI for AAA System.

This module provides a comprehensive interface for managing system-wide
configuration parameters that are currently hardcoded throughout the system.
"""

import streamlit as st
from typing import Dict, Any, Optional
from dataclasses import asdict
import yaml
from pathlib import Path

from app.config import Settings, load_settings
from app.config.system_config import (
    AutonomyConfig, PatternMatchingConfig, LLMGenerationConfig, RecommendationConfig,
    SystemConfiguration, SystemConfigurationManager
)


def render_system_configuration():
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
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🤖 Autonomy Assessment", 
        "🔍 Pattern Matching", 
        "🧠 LLM Generation", 
        "💡 Recommendations",
        "🚦 Rate Limiting",
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
        render_configuration_management(config_manager)


def render_autonomy_config(config: AutonomyConfig):
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


def render_pattern_matching_config(config: PatternMatchingConfig):
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


def render_llm_generation_config(config: LLMGenerationConfig):
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


def render_recommendation_config(config: RecommendationConfig):
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


def render_rate_limiting_config(config):
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


def render_configuration_management(config_manager: SystemConfigurationManager):
    """Render configuration management tools."""
    st.subheader("Configuration Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Configuration", use_container_width=True):
            if config_manager.save_config():
                st.success("✅ Configuration saved successfully!")
            else:
                st.error("❌ Failed to save configuration")
    
    with col2:
        if st.button("🔄 Reset to Defaults", use_container_width=True):
            config_manager.reset_to_defaults()
            st.success("✅ Configuration reset to defaults")
            st.rerun()
    
    with col3:
        if st.button("📤 Export Configuration", use_container_width=True):
            config_dict = config_manager.export_config()
            st.download_button(
                "Download Config",
                data=yaml.dump(config_dict, default_flow_style=False, indent=2),
                file_name="system_config.yaml",
                mime="application/yaml"
            )
    
    st.write("---")
    
    # Import configuration
    st.write("**Import Configuration**")
    uploaded_file = st.file_uploader("Upload configuration file", type=['yaml', 'yml'])
    
    if uploaded_file is not None:
        try:
            config_dict = yaml.safe_load(uploaded_file)
            if st.button("Import Configuration"):
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