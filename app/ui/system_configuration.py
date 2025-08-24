"""System Configuration Management UI for AAA System.

This module provides a comprehensive interface for managing system-wide
configuration parameters that are currently hardcoded throughout the system.
"""

import streamlit as st
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import yaml
from pathlib import Path

from app.config import Settings, load_settings


@dataclass
class AutonomyConfig:
    """Configuration for autonomy assessment parameters."""
    min_autonomy_threshold: float = 0.7
    confidence_boost_factor: float = 1.2
    
    # Autonomy scoring weights
    reasoning_capability_weight: float = 0.3
    decision_independence_weight: float = 0.25
    exception_handling_weight: float = 0.2
    learning_adaptation_weight: float = 0.15
    self_monitoring_weight: float = 0.1
    
    # Feasibility thresholds
    fully_automatable_threshold: float = 0.8
    partially_automatable_threshold: float = 0.6
    high_autonomy_boost_threshold: float = 0.7
    autonomy_boost_multiplier: float = 1.1


@dataclass
class PatternMatchingConfig:
    """Configuration for pattern matching and similarity calculations."""
    # Blending weights
    tag_weight: float = 0.3
    vector_weight: float = 0.5
    confidence_weight: float = 0.2
    
    # Tag score thresholds
    strong_tag_match_threshold: float = 0.7
    moderate_tag_match_threshold: float = 0.4
    
    # Vector similarity thresholds
    high_similarity_threshold: float = 0.7
    moderate_similarity_threshold: float = 0.4
    
    # Overall match thresholds
    excellent_fit_threshold: float = 0.8
    good_fit_threshold: float = 0.6
    
    # Agentic scoring weights
    autonomy_level_weight: float = 0.4
    reasoning_capability_weight: float = 0.25
    decision_independence_weight: float = 0.2
    exception_handling_weight: float = 0.1
    learning_potential_weight: float = 0.05


@dataclass
class LLMGenerationConfig:
    """Configuration for LLM generation parameters."""
    temperature: float = 0.3
    max_tokens: int = 1000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    
    # Timeout configurations
    llm_timeout: int = 20
    http_timeout: int = 10
    api_request_timeout: float = 30.0


@dataclass
class RecommendationConfig:
    """Configuration for recommendation generation and filtering."""
    min_recommendation_confidence: float = 0.7
    tech_stack_inclusion_threshold: float = 0.6
    new_pattern_creation_threshold: float = 0.7
    
    # Enhancement thresholds
    pattern_enhancement_similarity_threshold: float = 0.7
    conceptual_similarity_threshold: float = 0.7
    
    # Confidence calculation
    autonomy_boost_factor: float = 0.2  # Up to 20% boost
    reasoning_boost_threshold: int = 3
    reasoning_boost_amount: float = 0.1
    multi_agent_boost: float = 0.1


@dataclass
class SystemConfiguration:
    """Complete system configuration container."""
    autonomy: AutonomyConfig
    pattern_matching: PatternMatchingConfig
    llm_generation: LLMGenerationConfig
    recommendations: RecommendationConfig


class SystemConfigurationManager:
    """Manager for system configuration with persistence."""
    
    def __init__(self, config_path: str = "system_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> SystemConfiguration:
        """Load configuration from file or create defaults."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = yaml.safe_load(f)
                
                return SystemConfiguration(
                    autonomy=AutonomyConfig(**data.get('autonomy', {})),
                    pattern_matching=PatternMatchingConfig(**data.get('pattern_matching', {})),
                    llm_generation=LLMGenerationConfig(**data.get('llm_generation', {})),
                    recommendations=RecommendationConfig(**data.get('recommendations', {}))
                )
            except Exception as e:
                st.error(f"Error loading configuration: {e}")
        
        # Return defaults
        return SystemConfiguration(
            autonomy=AutonomyConfig(),
            pattern_matching=PatternMatchingConfig(),
            llm_generation=LLMGenerationConfig(),
            recommendations=RecommendationConfig()
        )
    
    def save_config(self) -> bool:
        """Save current configuration to file."""
        try:
            config_dict = {
                'autonomy': asdict(self.config.autonomy),
                'pattern_matching': asdict(self.config.pattern_matching),
                'llm_generation': asdict(self.config.llm_generation),
                'recommendations': asdict(self.config.recommendations)
            }
            
            with open(self.config_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
            return True
        except Exception as e:
            st.error(f"Error saving configuration: {e}")
            return False
    
    def reset_to_defaults(self):
        """Reset configuration to default values."""
        self.config = SystemConfiguration(
            autonomy=AutonomyConfig(),
            pattern_matching=PatternMatchingConfig(),
            llm_generation=LLMGenerationConfig(),
            recommendations=RecommendationConfig()
        )
    
    def export_config(self) -> Dict[str, Any]:
        """Export configuration as dictionary."""
        return {
            'autonomy': asdict(self.config.autonomy),
            'pattern_matching': asdict(self.config.pattern_matching),
            'llm_generation': asdict(self.config.llm_generation),
            'recommendations': asdict(self.config.recommendations)
        }
    
    def import_config(self, config_dict: Dict[str, Any]) -> bool:
        """Import configuration from dictionary."""
        try:
            self.config = SystemConfiguration(
                autonomy=AutonomyConfig(**config_dict.get('autonomy', {})),
                pattern_matching=PatternMatchingConfig(**config_dict.get('pattern_matching', {})),
                llm_generation=LLMGenerationConfig(**config_dict.get('llm_generation', {})),
                recommendations=RecommendationConfig(**config_dict.get('recommendations', {}))
            )
            return True
        except Exception as e:
            st.error(f"Error importing configuration: {e}")
            return False


def render_system_configuration():
    """Render the system configuration management interface."""
    st.header("🔧 System Configuration")
    st.write("Configure advanced system parameters for autonomy assessment, pattern matching, and recommendations.")
    
    # Initialize configuration manager
    if 'config_manager' not in st.session_state:
        st.session_state.config_manager = SystemConfigurationManager()
    
    config_manager = st.session_state.config_manager
    
    # Configuration tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🤖 Autonomy Assessment", 
        "🔍 Pattern Matching", 
        "🧠 LLM Generation", 
        "💡 Recommendations",
        "⚙️ Management"
    ])
    
    with tab1:
        render_autonomy_config(config_manager.config.autonomy)
    
    with tab2:
        render_pattern_matching_config(config_manager.config.pattern_matching)
    
    with tab3:
        render_llm_generation_config(config_manager.config.llm_generation)
    
    with tab4:
        render_recommendation_config(config_manager.config.recommendations)
    
    with tab5:
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