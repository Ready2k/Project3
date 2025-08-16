"""
Configuration management for advanced prompt defense settings.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path
import yaml

from app.utils.logger import app_logger


@dataclass
class DetectorConfig:
    """Configuration for individual attack detectors."""
    enabled: bool = True
    sensitivity: str = "medium"  # low, medium, high
    confidence_threshold: float = 0.5
    custom_settings: Dict = field(default_factory=dict)


@dataclass
class AdvancedPromptDefenseConfig:
    """Configuration for the advanced prompt defense system."""
    
    # Global settings
    enabled: bool = True
    attack_pack_version: str = "v2"
    detection_confidence_threshold: float = 0.7
    max_validation_time_ms: int = 100
    
    # Detector configurations
    overt_injection: DetectorConfig = field(default_factory=lambda: DetectorConfig(
        enabled=True,
        sensitivity="high",
        confidence_threshold=0.7,
        custom_settings={
            "check_role_manipulation": True,
            "check_instruction_override": True,
            "check_system_access": True
        }
    ))
    
    covert_injection: DetectorConfig = field(default_factory=lambda: DetectorConfig(
        enabled=True,
        sensitivity="high",
        confidence_threshold=0.7,
        custom_settings={
            "decode_base64": True,
            "normalize_unicode": True,
            "detect_zero_width": True,
            "check_markdown_links": True
        }
    ))
    
    scope_validator: DetectorConfig = field(default_factory=lambda: DetectorConfig(
        enabled=True,
        sensitivity="medium",
        confidence_threshold=0.6,
        custom_settings={
            "allowed_business_domains": ["feasibility", "automation", "assessment"],
            "blocked_tasks": ["summarization", "translation", "code_generation", "creative_writing"]
        }
    ))
    
    data_egress_detector: DetectorConfig = field(default_factory=lambda: DetectorConfig(
        enabled=True,
        sensitivity="high",
        confidence_threshold=0.9,
        custom_settings={
            "protect_environment_vars": True,
            "protect_system_prompt": True,
            "protect_user_data": True,
            "detect_canary_extraction": True
        }
    ))
    
    protocol_tampering_detector: DetectorConfig = field(default_factory=lambda: DetectorConfig(
        enabled=True,
        sensitivity="medium",
        confidence_threshold=0.6,
        custom_settings={
            "validate_json_requests": True,
            "check_unauthorized_fields": True,
            "prevent_format_manipulation": True
        }
    ))
    
    context_attack_detector: DetectorConfig = field(default_factory=lambda: DetectorConfig(
        enabled=True,
        sensitivity="high",
        confidence_threshold=0.8,
        custom_settings={
            "max_input_length": 10000,
            "scan_entire_input": True,
            "detect_buried_instructions": True,
            "lorem_ipsum_threshold": 0.3
        }
    ))
    
    multilingual_attack: DetectorConfig = field(default_factory=lambda: DetectorConfig(
        enabled=True,
        sensitivity="medium",
        confidence_threshold=0.7,
        custom_settings={
            "supported_languages": ["en", "es", "fr", "de", "zh", "ja"],
            "normalize_unicode": True,
            "detect_language_switching": True
        }
    ))
    
    business_logic: DetectorConfig = field(default_factory=lambda: DetectorConfig(
        enabled=True,
        sensitivity="high",
        confidence_threshold=0.9,
        custom_settings={
            "protect_provider_settings": True,
            "protect_safety_toggles": True,
            "protect_system_parameters": True,
            "monitor_configuration_access": True
        }
    ))
    
    # Response action thresholds
    block_threshold: float = 0.9
    flag_threshold: float = 0.5
    
    # Monitoring and logging
    log_all_detections: bool = True
    alert_on_attacks: bool = True
    metrics_enabled: bool = True
    
    # Performance settings
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    cache_size: int = 1000
    parallel_detection: bool = True
    max_workers: int = 8
    max_validation_time_ms: int = 100
    max_memory_mb: int = 512
    enable_performance_monitoring: bool = True
    performance_alert_threshold_ms: float = 50.0
    cache_optimization_interval: int = 1000  # Optimize cache every N validations
    
    # User experience settings
    provide_user_guidance: bool = True
    educational_messages: bool = True
    appeal_mechanism: bool = True
    
    @classmethod
    def load_from_file(cls, config_file: str) -> 'AdvancedPromptDefenseConfig':
        """Load configuration from YAML file."""
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                app_logger.warning(f"Config file {config_file} not found, using defaults")
                return cls()
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # Extract advanced prompt defense config
            defense_config = config_data.get('advanced_prompt_defense', {})
            
            # Create config instance
            config = cls()
            
            # Update global settings
            for key, value in defense_config.items():
                if hasattr(config, key) and not key.startswith('_') and not callable(getattr(config, key)):
                    if key in ['overt_injection', 'covert_injection', 'scope_validator', 
                              'data_egress_detector', 'protocol_tampering_detector', 
                              'context_attack_detector', 'multilingual_attack', 
                              'business_logic']:
                        # Handle detector configs
                        detector_config = getattr(config, key)
                        detector_data = value if isinstance(value, dict) else {}
                        
                        # Update detector config fields
                        for detector_key, detector_value in detector_data.items():
                            if hasattr(detector_config, detector_key):
                                if detector_key == 'custom_settings':
                                    detector_config.custom_settings.update(detector_value)
                                else:
                                    setattr(detector_config, detector_key, detector_value)
                    else:
                        setattr(config, key, value)
            
            app_logger.info(f"Loaded advanced prompt defense config from {config_file}")
            return config
            
        except Exception as e:
            app_logger.error(f"Failed to load config from {config_file}: {e}")
            app_logger.info("Using default configuration")
            return cls()
    
    def save_to_file(self, config_file: str) -> None:
        """Save configuration to YAML file."""
        try:
            # Load existing config file to preserve other settings
            config_path = Path(config_file)
            existing_config = {}
            
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    existing_config = yaml.safe_load(f) or {}
            
            # Convert config to dict
            defense_config = {
                'enabled': self.enabled,
                'attack_pack_version': self.attack_pack_version,
                'detection_confidence_threshold': self.detection_confidence_threshold,
                'max_validation_time_ms': self.max_validation_time_ms,
                'block_threshold': self.block_threshold,
                'flag_threshold': self.flag_threshold,
                'log_all_detections': self.log_all_detections,
                'alert_on_attacks': self.alert_on_attacks,
                'metrics_enabled': self.metrics_enabled,
                'enable_caching': self.enable_caching,
                'cache_ttl_seconds': self.cache_ttl_seconds,
                'cache_size': self.cache_size,
                'parallel_detection': self.parallel_detection,
                'max_workers': self.max_workers,
                'max_memory_mb': self.max_memory_mb,
                'enable_performance_monitoring': self.enable_performance_monitoring,
                'performance_alert_threshold_ms': self.performance_alert_threshold_ms,
                'cache_optimization_interval': self.cache_optimization_interval,
                'provide_user_guidance': self.provide_user_guidance,
                'educational_messages': self.educational_messages,
                'appeal_mechanism': self.appeal_mechanism
            }
            
            # Add detector configs
            detectors = [
                'overt_injection', 'covert_injection', 'scope_validator',
                'data_egress_detector', 'protocol_tampering_detector',
                'context_attack_detector', 'multilingual_attack',
                'business_logic'
            ]
            
            for detector_name in detectors:
                detector_config = getattr(self, detector_name)
                defense_config[detector_name] = {
                    'enabled': detector_config.enabled,
                    'sensitivity': detector_config.sensitivity,
                    'confidence_threshold': detector_config.confidence_threshold,
                    'custom_settings': detector_config.custom_settings
                }
            
            # Update existing config
            existing_config['advanced_prompt_defense'] = defense_config
            
            # Save to file
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_config, f, default_flow_style=False, indent=2)
            
            app_logger.info(f"Saved advanced prompt defense config to {config_file}")
            
        except Exception as e:
            app_logger.error(f"Failed to save config to {config_file}: {e}")
            raise
    
    def get_detector_config(self, detector_name: str) -> Optional[DetectorConfig]:
        """Get configuration for a specific detector."""
        return getattr(self, detector_name, None)
    
    def is_detector_enabled(self, detector_name: str) -> bool:
        """Check if a specific detector is enabled."""
        detector_config = self.get_detector_config(detector_name)
        return detector_config.enabled if detector_config else False
    
    def get_detector_threshold(self, detector_name: str) -> float:
        """Get confidence threshold for a specific detector."""
        detector_config = self.get_detector_config(detector_name)
        return detector_config.confidence_threshold if detector_config else self.detection_confidence_threshold
    
    def update_detector_config(self, detector_name: str, **kwargs) -> None:
        """Update configuration for a specific detector."""
        detector_config = self.get_detector_config(detector_name)
        if detector_config:
            for key, value in kwargs.items():
                if hasattr(detector_config, key):
                    if key == 'custom_settings':
                        detector_config.custom_settings.update(value)
                    else:
                        setattr(detector_config, key, value)
            app_logger.info(f"Updated {detector_name} configuration")
        else:
            app_logger.warning(f"Detector {detector_name} not found")
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Validate thresholds
        if not 0.0 <= self.detection_confidence_threshold <= 1.0:
            issues.append("detection_confidence_threshold must be between 0.0 and 1.0")
        
        if not 0.0 <= self.block_threshold <= 1.0:
            issues.append("block_threshold must be between 0.0 and 1.0")
        
        if not 0.0 <= self.flag_threshold <= 1.0:
            issues.append("flag_threshold must be between 0.0 and 1.0")
        
        if self.flag_threshold >= self.block_threshold:
            issues.append("flag_threshold should be less than block_threshold")
        
        # Validate timing
        if self.max_validation_time_ms <= 0:
            issues.append("max_validation_time_ms must be positive")
        
        if self.cache_ttl_seconds <= 0:
            issues.append("cache_ttl_seconds must be positive")
        
        # Validate performance settings
        if self.cache_size <= 0:
            issues.append("cache_size must be positive")
        
        if self.max_workers <= 0:
            issues.append("max_workers must be positive")
        
        if self.max_memory_mb <= 0:
            issues.append("max_memory_mb must be positive")
        
        if self.performance_alert_threshold_ms <= 0:
            issues.append("performance_alert_threshold_ms must be positive")
        
        if self.cache_optimization_interval <= 0:
            issues.append("cache_optimization_interval must be positive")
        
        # Validate detector configs
        detectors = [
            'overt_injection', 'covert_injection', 'scope_validator',
            'data_egress_detector', 'protocol_tampering_detector',
            'context_attack_detector', 'multilingual_attack',
            'business_logic'
        ]
        
        for detector_name in detectors:
            detector_config = getattr(self, detector_name)
            if not 0.0 <= detector_config.confidence_threshold <= 1.0:
                issues.append(f"{detector_name}.confidence_threshold must be between 0.0 and 1.0")
            
            if detector_config.sensitivity not in ['low', 'medium', 'high']:
                issues.append(f"{detector_name}.sensitivity must be 'low', 'medium', or 'high'")
        
        return issues


# Global configuration instance
_defense_config: Optional[AdvancedPromptDefenseConfig] = None


def get_defense_config() -> AdvancedPromptDefenseConfig:
    """Get the global defense configuration instance."""
    global _defense_config
    if _defense_config is None:
        _defense_config = AdvancedPromptDefenseConfig.load_from_file("config.yaml")
    return _defense_config


def reload_defense_config() -> AdvancedPromptDefenseConfig:
    """Reload the defense configuration from file."""
    global _defense_config
    _defense_config = AdvancedPromptDefenseConfig.load_from_file("config.yaml")
    return _defense_config


def update_defense_config(**kwargs) -> None:
    """Update the global defense configuration."""
    config = get_defense_config()
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    # Save updated config
    config.save_to_file("config.yaml")