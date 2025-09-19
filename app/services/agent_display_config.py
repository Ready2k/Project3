"""Configuration management for agent display preferences and settings."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
import os

from app.utils.imports import require_service


class DisplayDensity(Enum):
    """Information density levels for agent display."""
    MINIMAL = "minimal"
    COMPACT = "compact"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


class AutonomyThreshold(Enum):
    """Autonomy level thresholds for display filtering."""
    ALL = 0.0
    LOW = 0.3
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.9


@dataclass
class AgentDisplayPreferences:
    """User preferences for agent display."""
    display_density: DisplayDensity = DisplayDensity.DETAILED
    autonomy_threshold: AutonomyThreshold = AutonomyThreshold.ALL
    show_performance_metrics: bool = True
    show_security_details: bool = True
    show_coordination_diagrams: bool = True
    show_deployment_guidance: bool = True
    expand_first_agent: bool = True
    group_by_role: bool = False
    highlight_high_autonomy: bool = True
    show_mock_data: bool = True  # For demonstration purposes


@dataclass
class TechStackValidationRules:
    """Rules for tech stack validation."""
    required_frameworks: List[str] = field(default_factory=lambda: ["LangChain", "CrewAI"])
    required_orchestration: List[str] = field(default_factory=lambda: ["Redis", "Celery"])
    required_monitoring: List[str] = field(default_factory=lambda: ["Prometheus", "Grafana"])
    minimum_readiness_score: float = 0.7
    critical_missing_threshold: int = 2


@dataclass
class AgentDisplayTemplates:
    """Templates for agent display customization."""
    agent_card_template: str = "default"
    coordination_diagram_style: str = "mermaid"
    performance_chart_type: str = "metrics"
    security_display_format: str = "detailed"


@dataclass
class AgentDisplayConfig:
    """Complete configuration for agent display system."""
    preferences: AgentDisplayPreferences = field(default_factory=AgentDisplayPreferences)
    validation_rules: TechStackValidationRules = field(default_factory=TechStackValidationRules)
    templates: AgentDisplayTemplates = field(default_factory=AgentDisplayTemplates)
    custom_metrics: List[str] = field(default_factory=list)
    custom_security_requirements: List[str] = field(default_factory=list)


class AgentDisplayConfigManager:
    """Manages agent display configuration and preferences."""
    
    def __init__(self, config_file: str = "agent_display_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> AgentDisplayConfig:
        """Load configuration from file or create default."""
        
        if os.path.exists(self.config_file):
            # Get logger from service registry
            self.logger = require_service('logger', context='DisplayDensity')
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Convert dict to dataclass
                preferences = AgentDisplayPreferences(**config_data.get("preferences", {}))
                validation_rules = TechStackValidationRules(**config_data.get("validation_rules", {}))
                templates = AgentDisplayTemplates(**config_data.get("templates", {}))
                
                config = AgentDisplayConfig(
                    preferences=preferences,
                    validation_rules=validation_rules,
                    templates=templates,
                    custom_metrics=config_data.get("custom_metrics", []),
                    custom_security_requirements=config_data.get("custom_security_requirements", [])
                )
                
                self.logger.info("Agent display configuration loaded from file")
                return config
                
            except Exception as e:
                self.logger.error(f"Error loading agent display config: {e}")
                return AgentDisplayConfig()
        
        else:
            self.logger.info("Creating default agent display configuration")
            return AgentDisplayConfig()
    
    def save_config(self) -> bool:
        """Save current configuration to file."""
        
        try:
            config_data = {
                "preferences": {
                    "display_density": self.config.preferences.display_density.value if hasattr(self.config.preferences.display_density, 'value') else self.config.preferences.display_density,
                    "autonomy_threshold": self.config.preferences.autonomy_threshold.value if hasattr(self.config.preferences.autonomy_threshold, 'value') else self.config.preferences.autonomy_threshold,
                    "show_performance_metrics": self.config.preferences.show_performance_metrics,
                    "show_security_details": self.config.preferences.show_security_details,
                    "show_coordination_diagrams": self.config.preferences.show_coordination_diagrams,
                    "show_deployment_guidance": self.config.preferences.show_deployment_guidance,
                    "expand_first_agent": self.config.preferences.expand_first_agent,
                    "group_by_role": self.config.preferences.group_by_role,
                    "highlight_high_autonomy": self.config.preferences.highlight_high_autonomy,
                    "show_mock_data": self.config.preferences.show_mock_data
                },
                "validation_rules": {
                    "required_frameworks": self.config.validation_rules.required_frameworks,
                    "required_orchestration": self.config.validation_rules.required_orchestration,
                    "required_monitoring": self.config.validation_rules.required_monitoring,
                    "minimum_readiness_score": self.config.validation_rules.minimum_readiness_score,
                    "critical_missing_threshold": self.config.validation_rules.critical_missing_threshold
                },
                "templates": {
                    "agent_card_template": self.config.templates.agent_card_template,
                    "coordination_diagram_style": self.config.templates.coordination_diagram_style,
                    "performance_chart_type": self.config.templates.performance_chart_type,
                    "security_display_format": self.config.templates.security_display_format
                },
                "custom_metrics": self.config.custom_metrics,
                "custom_security_requirements": self.config.custom_security_requirements
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.info("Agent display configuration saved")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving agent display config: {e}")
            return False
    
    def update_preferences(self, **kwargs) -> bool:
        """Update display preferences."""
        
        try:
            for key, value in kwargs.items():
                if hasattr(self.config.preferences, key):
                    # Handle enum conversions
                    if key == "display_density" and isinstance(value, str):
                        value = DisplayDensity(value)
                    elif key == "autonomy_threshold" and isinstance(value, (str, float)):
                        if isinstance(value, str):
                            # Convert string to float first, then find closest enum
                            float_value = float(value)
                            # Find closest threshold
                            closest_threshold = AutonomyThreshold.ALL
                            for threshold in AutonomyThreshold:
                                if threshold.value <= float_value:
                                    closest_threshold = threshold
                            value = closest_threshold
                        else:
                            # Find closest threshold for float value
                            closest_threshold = AutonomyThreshold.ALL
                            for threshold in AutonomyThreshold:
                                if threshold.value <= value:
                                    closest_threshold = threshold
                            value = closest_threshold
                    
                    setattr(self.config.preferences, key, value)
            
            return self.save_config()
            
        except Exception as e:
            self.logger.error(f"Error updating preferences: {e}")
            return False
    
    def update_validation_rules(self, **kwargs) -> bool:
        """Update tech stack validation rules."""
        
        try:
            for key, value in kwargs.items():
                if hasattr(self.config.validation_rules, key):
                    setattr(self.config.validation_rules, key, value)
            
            return self.save_config()
            
        except Exception as e:
            self.logger.error(f"Error updating validation rules: {e}")
            return False
    
    def add_custom_metric(self, metric: str) -> bool:
        """Add a custom performance metric."""
        
        if metric not in self.config.custom_metrics:
            self.config.custom_metrics.append(metric)
            return self.save_config()
        
        return True
    
    def remove_custom_metric(self, metric: str) -> bool:
        """Remove a custom performance metric."""
        
        if metric in self.config.custom_metrics:
            self.config.custom_metrics.remove(metric)
            return self.save_config()
        
        return True
    
    def add_custom_security_requirement(self, requirement: str) -> bool:
        """Add a custom security requirement."""
        
        if requirement not in self.config.custom_security_requirements:
            self.config.custom_security_requirements.append(requirement)
            return self.save_config()
        
        return True
    
    def get_filtered_agents(self, agents: List[Any]) -> List[Any]:
        """Filter agents based on autonomy threshold."""
        
        threshold = self.config.preferences.autonomy_threshold.value
        if threshold == 0.0:
            return agents
        
        return [agent for agent in agents if agent.autonomy_level >= threshold]
    
    def should_show_component(self, component: str) -> bool:
        """Check if a component should be displayed based on preferences."""
        
        component_map = {
            "performance_metrics": self.config.preferences.show_performance_metrics,
            "security_details": self.config.preferences.show_security_details,
            "coordination_diagrams": self.config.preferences.show_coordination_diagrams,
            "deployment_guidance": self.config.preferences.show_deployment_guidance
        }
        
        return component_map.get(component, True)
    
    def get_display_density_config(self) -> Dict[str, Any]:
        """Get configuration based on display density setting."""
        
        density = self.config.preferences.display_density
        
        if density == DisplayDensity.MINIMAL:
            return {
                "show_details": False,
                "max_capabilities_preview": 2,
                "max_metrics_preview": 2,
                "show_expandable_sections": False,
                "show_diagrams": False
            }
        elif density == DisplayDensity.COMPACT:
            return {
                "show_details": True,
                "max_capabilities_preview": 3,
                "max_metrics_preview": 3,
                "show_expandable_sections": True,
                "show_diagrams": False
            }
        elif density == DisplayDensity.DETAILED:
            return {
                "show_details": True,
                "max_capabilities_preview": 4,
                "max_metrics_preview": 4,
                "show_expandable_sections": True,
                "show_diagrams": True
            }
        else:  # COMPREHENSIVE
            return {
                "show_details": True,
                "max_capabilities_preview": 999,
                "max_metrics_preview": 999,
                "show_expandable_sections": True,
                "show_diagrams": True
            }
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults."""
        
        self.config = AgentDisplayConfig()
        return self.save_config()


# Global configuration manager instance
_config_manager = None

def get_agent_display_config() -> AgentDisplayConfigManager:
    """Get the global agent display configuration manager."""
    
    global _config_manager
    if _config_manager is None:
        _config_manager = AgentDisplayConfigManager()
    
    return _config_manager