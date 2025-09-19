"""System Configuration Data Classes.

This module contains the configuration data classes separated from UI components
to avoid circular dependencies.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from pathlib import Path
import yaml


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
    
    # Agentic necessity assessment thresholds
    agentic_necessity_threshold: float = 0.4  # More inclusive for agentic solutions
    traditional_suitability_threshold: float = 0.6  # Slightly lower traditional threshold
    hybrid_zone_threshold: float = 0.15  # Wider hybrid zone


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
class RateLimitConfig:
    """Configuration for API rate limiting."""
    # Default tier limits
    default_requests_per_minute: int = 60
    default_requests_per_hour: int = 1000
    default_requests_per_day: int = 10000
    default_burst_limit: int = 25
    default_burst_window_seconds: int = 60
    
    # Premium tier limits
    premium_requests_per_minute: int = 120
    premium_requests_per_hour: int = 3000
    premium_requests_per_day: int = 30000
    premium_burst_limit: int = 40
    
    # Enterprise tier limits
    enterprise_requests_per_minute: int = 300
    enterprise_requests_per_hour: int = 10000
    enterprise_requests_per_day: int = 100000
    enterprise_burst_limit: int = 100
    
    # IP-based limits (more restrictive)
    ip_requests_per_minute: int = 30
    ip_requests_per_hour: int = 500
    ip_requests_per_day: int = 5000
    ip_burst_limit: int = 15


@dataclass
class SystemConfiguration:
    """Complete system configuration container."""
    autonomy: AutonomyConfig
    pattern_matching: PatternMatchingConfig
    llm_generation: LLMGenerationConfig
    recommendations: RecommendationConfig
    rate_limiting: RateLimitConfig


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
                
                # Create configs with defaults first, then update with loaded values
                autonomy_data = data.get('autonomy', {})
                autonomy_config = AutonomyConfig()
                for key, value in autonomy_data.items():
                    if hasattr(autonomy_config, key):
                        setattr(autonomy_config, key, value)
                
                pattern_data = data.get('pattern_matching', {})
                pattern_config = PatternMatchingConfig()
                for key, value in pattern_data.items():
                    if hasattr(pattern_config, key):
                        setattr(pattern_config, key, value)
                
                llm_data = data.get('llm_generation', {})
                llm_config = LLMGenerationConfig()
                for key, value in llm_data.items():
                    if hasattr(llm_config, key):
                        setattr(llm_config, key, value)
                
                rec_data = data.get('recommendations', {})
                rec_config = RecommendationConfig()
                for key, value in rec_data.items():
                    if hasattr(rec_config, key):
                        setattr(rec_config, key, value)
                
                rate_limit_data = data.get('rate_limiting', {})
                rate_limit_config = RateLimitConfig()
                for key, value in rate_limit_data.items():
                    if hasattr(rate_limit_config, key):
                        setattr(rate_limit_config, key, value)
                
                return SystemConfiguration(
                    autonomy=autonomy_config,
                    pattern_matching=pattern_config,
                    llm_generation=llm_config,
                    recommendations=rec_config,
                    rate_limiting=rate_limit_config
                )
            except Exception as e:
                # Use logging instead of streamlit here
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error loading configuration: {e}")
        
        # Return defaults
        return SystemConfiguration(
            autonomy=AutonomyConfig(),
            pattern_matching=PatternMatchingConfig(),
            llm_generation=LLMGenerationConfig(),
            recommendations=RecommendationConfig(),
            rate_limiting=RateLimitConfig()
        )
    
    def save_config(self) -> bool:
        """Save current configuration to file."""
        try:
            from dataclasses import asdict
            config_dict = {
                'autonomy': asdict(self.config.autonomy),
                'pattern_matching': asdict(self.config.pattern_matching),
                'llm_generation': asdict(self.config.llm_generation),
                'recommendations': asdict(self.config.recommendations),
                'rate_limiting': asdict(self.config.rate_limiting)
            }
            
            with open(self.config_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
            return True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def reset_to_defaults(self):
        """Reset configuration to default values."""
        self.config = SystemConfiguration(
            autonomy=AutonomyConfig(),
            pattern_matching=PatternMatchingConfig(),
            llm_generation=LLMGenerationConfig(),
            recommendations=RecommendationConfig(),
            rate_limiting=RateLimitConfig()
        )
    
    def export_config(self) -> Dict[str, Any]:
        """Export configuration as dictionary."""
        from dataclasses import asdict
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
                recommendations=RecommendationConfig(**config_dict.get('recommendations', {})),
                rate_limiting=RateLimitConfig(**config_dict.get('rate_limiting', {}))
            )
            return True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error importing configuration: {e}")
            return False