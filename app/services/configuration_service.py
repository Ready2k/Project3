"""Configuration Service for Dynamic System Parameters.

This service provides centralized access to configurable system parameters
that were previously hardcoded throughout the application.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import yaml
from dataclasses import asdict

from app.config.system_config import (
    SystemConfiguration, SystemConfigurationManager,
    AutonomyConfig, PatternMatchingConfig, LLMGenerationConfig, RecommendationConfig
)
from app.utils.logger import app_logger


class ConfigurationService:
    """Centralized service for accessing dynamic system configuration."""
    
    _instance: Optional['ConfigurationService'] = None
    _config_manager: Optional[SystemConfigurationManager] = None
    
    def __new__(cls) -> 'ConfigurationService':
        """Singleton pattern to ensure single configuration instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize configuration service."""
        if self._config_manager is None:
            self._config_manager = SystemConfigurationManager()
            app_logger.info("Configuration service initialized")
    
    @property
    def autonomy(self) -> AutonomyConfig:
        """Get autonomy assessment configuration."""
        return self._config_manager.config.autonomy
    
    @property
    def pattern_matching(self) -> PatternMatchingConfig:
        """Get pattern matching configuration."""
        return self._config_manager.config.pattern_matching
    
    @property
    def llm_generation(self) -> LLMGenerationConfig:
        """Get LLM generation configuration."""
        return self._config_manager.config.llm_generation
    
    @property
    def recommendations(self) -> RecommendationConfig:
        """Get recommendation configuration."""
        return self._config_manager.config.recommendations
    
    def reload_config(self) -> bool:
        """Reload configuration from file."""
        try:
            self._config_manager = SystemConfigurationManager()
            app_logger.info("Configuration reloaded successfully")
            return True
        except Exception as e:
            app_logger.error(f"Failed to reload configuration: {e}")
            return False
    
    def get_autonomy_weights(self) -> Dict[str, float]:
        """Get autonomy scoring weights as dictionary."""
        config = self.autonomy
        return {
            "reasoning_capability": config.reasoning_capability_weight,
            "decision_independence": config.decision_independence_weight,
            "exception_handling": config.exception_handling_weight,
            "learning_adaptation": config.learning_adaptation_weight,
            "self_monitoring": config.self_monitoring_weight,
        }
    
    def get_pattern_matching_weights(self) -> Dict[str, float]:
        """Get pattern matching weights as dictionary."""
        config = self.pattern_matching
        return {
            "tag_weight": config.tag_weight,
            "vector_weight": config.vector_weight,
            "confidence_weight": config.confidence_weight,
        }
    
    def get_agentic_scoring_weights(self) -> Dict[str, float]:
        """Get agentic scoring weights as dictionary."""
        config = self.pattern_matching
        return {
            "autonomy_level": config.autonomy_level_weight,
            "reasoning_capability": config.reasoning_capability_weight,
            "decision_independence": config.decision_independence_weight,
            "exception_handling": config.exception_handling_weight,
            "learning_potential": config.learning_potential_weight,
        }
    
    def get_llm_params(self) -> Dict[str, Any]:
        """Get LLM generation parameters as dictionary."""
        config = self.llm_generation
        return {
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
            "frequency_penalty": config.frequency_penalty,
            "presence_penalty": config.presence_penalty,
        }
    
    def is_fully_automatable(self, score: float) -> bool:
        """Check if score meets fully automatable threshold."""
        return score >= self.autonomy.fully_automatable_threshold
    
    def is_partially_automatable(self, score: float) -> bool:
        """Check if score meets partially automatable threshold."""
        return score >= self.autonomy.partially_automatable_threshold
    
    def get_feasibility_classification(self, autonomy_score: float) -> str:
        """Get feasibility classification based on autonomy score."""
        if self.is_fully_automatable(autonomy_score):
            return "Fully Automatable"
        elif self.is_partially_automatable(autonomy_score):
            return "Partially Automatable"
        else:
            return "Manual Process"
    
    def should_create_new_pattern(self, recommendations: list, min_confidence: Optional[float] = None) -> bool:
        """Determine if new pattern should be created based on existing recommendations."""
        threshold = min_confidence or self.recommendations.new_pattern_creation_threshold
        return not recommendations or all(r.confidence < threshold for r in recommendations)
    
    def calculate_autonomy_boost(self, autonomy_score: float) -> float:
        """Calculate autonomy boost factor."""
        return autonomy_score * self.recommendations.autonomy_boost_factor
    
    def meets_tech_inclusion_threshold(self, score: float) -> bool:
        """Check if technology score meets inclusion threshold."""
        return score > self.recommendations.tech_stack_inclusion_threshold
    
    def get_similarity_classification(self, tag_score: float, vector_score: float, blended_score: float) -> list:
        """Get similarity classification based on scores."""
        classifications = []
        
        if tag_score > self.pattern_matching.strong_tag_match_threshold:
            classifications.append("Strong tag-based match")
        elif tag_score > self.pattern_matching.moderate_tag_match_threshold:
            classifications.append("Moderate tag-based match")
        
        if vector_score > self.pattern_matching.high_similarity_threshold:
            classifications.append("high semantic similarity")
        elif vector_score > self.pattern_matching.moderate_similarity_threshold:
            classifications.append("moderate semantic similarity")
        
        if blended_score > self.pattern_matching.excellent_fit_threshold:
            classifications.append("excellent overall fit")
        elif blended_score > self.pattern_matching.good_fit_threshold:
            classifications.append("good overall fit")
        
        return classifications
    
    def export_current_config(self) -> Dict[str, Any]:
        """Export current configuration for debugging or backup."""
        return {
            'autonomy': asdict(self.autonomy),
            'pattern_matching': asdict(self.pattern_matching),
            'llm_generation': asdict(self.llm_generation),
            'recommendations': asdict(self.recommendations)
        }


# Global configuration service instance
config_service = ConfigurationService()


def get_config() -> ConfigurationService:
    """Get the global configuration service instance."""
    return config_service


# Convenience functions for backward compatibility
def get_autonomy_weights() -> Dict[str, float]:
    """Get autonomy scoring weights."""
    return config_service.get_autonomy_weights()


def get_pattern_matching_weights() -> Dict[str, float]:
    """Get pattern matching weights."""
    return config_service.get_pattern_matching_weights()


def get_llm_params() -> Dict[str, Any]:
    """Get LLM generation parameters."""
    return config_service.get_llm_params()


def is_fully_automatable(score: float) -> bool:
    """Check if score meets fully automatable threshold."""
    return config_service.is_fully_automatable(score)


def is_partially_automatable(score: float) -> bool:
    """Check if score meets partially automatable threshold."""
    return config_service.is_partially_automatable(score)