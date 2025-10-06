"""
Core Service Registration

This module handles the registration of core services in the service registry.
It provides functions to register logger, configuration, cache, and security services.
"""

import logging
from typing import Dict, Any, List, Optional

from app.core.registry import get_registry, ServiceRegistry
from app.core.services.logger_service import LoggerService
from app.core.services.config_service import ConfigService
from app.core.services.cache_service_wrapper import CacheService
from app.core.services.security_service import SecurityService, AdvancedPromptDefenseService
from app.llm.factory import LLMProviderFactory
from app.diagrams.factory import DiagramServiceFactory

logger = logging.getLogger(__name__)


def register_core_services(registry: Optional[ServiceRegistry] = None, 
                          config_overrides: Optional[Dict[str, Dict[str, Any]]] = None) -> List[str]:
    """
    Register all core services in the service registry.
    
    Args:
        registry: Service registry instance (uses global if None)
        config_overrides: Optional configuration overrides for services
        
    Returns:
        List of successfully registered service names
        
    Raises:
        Exception: If critical service registration fails
    """
    if registry is None:
        registry = get_registry()
    
    config_overrides = config_overrides or {}
    registered_services = []
    
    logger.info("Starting core service registration...")
    
    try:
        # 1. Register Configuration Service (no dependencies)
        config_service_config = config_overrides.get("config", {
            "config_file": "config.yaml",
            "environment_prefix": "AAA",
            "auto_reload": False,
            "validation_enabled": True
        })
        
        config_service = ConfigService(config_service_config)
        registry.register_singleton("config", config_service, dependencies=[])
        registered_services.append("config")
        logger.info("✅ Registered config service")
        
        # 2. Register Logger Service (depends on config)
        logger_service_config = config_overrides.get("logger", {
            "level": "INFO",
            "format": "structured",
            "redact_pii": True,
            "file_path": "logs/aaa.log",
            "rotation": "1 day",
            "retention": "30 days"
        })
        
        logger_service = LoggerService(logger_service_config)
        registry.register_singleton("logger", logger_service, dependencies=["config"])
        registered_services.append("logger")
        logger.info("✅ Registered logger service")
        
        # 3. Register Cache Service (depends on config and logger)
        cache_service_config = config_overrides.get("cache", {
            "backend": "memory",
            "default_ttl_seconds": 3600,
            "max_size_mb": 100,
            "cleanup_interval_seconds": 300,
            "redis_config": {
                "host": "localhost",
                "port": 6379,
                "db": 0,
                "password": None,
                "ssl": False
            }
        })
        
        cache_service = CacheService(cache_service_config)
        registry.register_singleton("cache", cache_service, dependencies=["config", "logger"])
        registered_services.append("cache")
        logger.info("✅ Registered cache service")
        
        # 4. Register Security Validator Service (depends on config and logger)
        security_service_config = config_overrides.get("security_validator", {
            "enable_input_validation": True,
            "enable_output_sanitization": True,
            "max_input_length": 10000,
            "blocked_patterns": [],
            "rate_limiting": {
                "enabled": True,
                "requests_per_minute": 60,
                "requests_per_hour": 1000
            }
        })
        
        security_service = SecurityService(security_service_config)
        registry.register_singleton("security_validator", security_service, dependencies=["config", "logger"])
        registered_services.append("security_validator")
        logger.info("✅ Registered security validator service")
        
        # 5. Register Advanced Prompt Defense Service (depends on config, logger, cache)
        advanced_defense_config = config_overrides.get("advanced_prompt_defender", {
            "enabled": True,
            "detection_confidence_threshold": 0.7,
            "flag_threshold": 0.5,
            "block_threshold": 0.9,
            "max_validation_time_ms": 100,
            "enable_caching": True,
            "cache_ttl_seconds": 300,
            "parallel_detection": True,
            "educational_messages": True
        })
        
        advanced_defense_service = AdvancedPromptDefenseService(advanced_defense_config)
        registry.register_singleton("advanced_prompt_defender", advanced_defense_service, 
                                   dependencies=["config", "logger", "cache"])
        registered_services.append("advanced_prompt_defender")
        logger.info("✅ Registered advanced prompt defender service")
        
        # 6. Register LLM Provider Factory (depends on config and logger)
        llm_factory_config = config_overrides.get("llm_provider_factory", {
            "default_provider": "openai",
            "fallback_providers": ["anthropic", "bedrock"],
            "timeout_seconds": 30,
            "max_retries": 3,
            "retry_delay_seconds": 1.0
        })
        
        llm_factory = LLMProviderFactory(llm_factory_config)
        registry.register_singleton("llm_provider_factory", llm_factory, dependencies=["config", "logger"])
        registered_services.append("llm_provider_factory")
        logger.info("✅ Registered LLM provider factory service")
        
        # 7. Register Diagram Service Factory (depends on config and logger)
        diagram_factory_config = config_overrides.get("diagram_service_factory", {
            "mermaid_config": {
                "default_height": 400,
                "enable_enhanced_rendering": True
            },
            "infrastructure_config": {
                "default_format": "png",
                "enable_dynamic_mapping": True
            },
            "drawio_config": {
                "enable_multiple_formats": True,
                "include_metadata": True
            }
        })
        
        diagram_factory = DiagramServiceFactory(diagram_factory_config)
        registry.register_singleton("diagram_service_factory", diagram_factory, dependencies=["config", "logger"])
        registered_services.append("diagram_service_factory")
        logger.info("✅ Registered diagram service factory")
        
        # 8. Register Pattern Loader Service (depends on config)
        pattern_loader_config = config_overrides.get("pattern_loader", {
            "pattern_library_path": "./data/patterns"
        })
        
        from app.pattern.loader import PatternLoader
        pattern_loader = PatternLoader(pattern_loader_config.get("pattern_library_path", "./data/patterns"))
        registry.register_singleton("pattern_loader", pattern_loader, dependencies=["config"])
        registered_services.append("pattern_loader")
        logger.info("✅ Registered pattern loader service")
        
        # 9. Register Audit Logger Service (depends on config)
        audit_logger_config = config_overrides.get("audit_logger", {
            "db_path": "audit.db",
            "redact_pii": True
        })
        
        from app.utils.audit import AuditLogger
        audit_logger = AuditLogger(
            db_path=audit_logger_config.get("db_path", "audit.db"),
            redact_pii=audit_logger_config.get("redact_pii", True)
        )
        registry.register_singleton("audit_logger", audit_logger, dependencies=["config"])
        registered_services.append("audit_logger")
        logger.info("✅ Registered audit logger service")
        
        # 10. Register Infrastructure Diagram Service (depends on config and logger)
        config_overrides.get("infrastructure_diagram_service", {
            "output_format": "png",
            "dpi": 300,
            "font_size": 12,
            "max_components": 50
        })
        
        from app.diagrams.infrastructure import InfrastructureDiagramService
        infrastructure_diagram_service = InfrastructureDiagramService()
        registry.register_singleton("infrastructure_diagram_service", infrastructure_diagram_service, dependencies=["config", "logger"])
        registered_services.append("infrastructure_diagram_service")
        logger.info("✅ Registered infrastructure diagram service")
        
        # 11. Register Enhanced Pattern Loader Service (depends on config, logger, cache)
        enhanced_pattern_loader_config = config_overrides.get("enhanced_pattern_loader", {
            "pattern_library_path": "./data/patterns",
            "enable_analytics": True,
            "enable_caching": True,
            "cache_ttl_seconds": 3600,
            "enable_validation": True,
            "auto_reload": False,
            "performance_tracking": True
        })
        
        from app.services.enhanced_pattern_loader import EnhancedPatternLoader
        enhanced_pattern_loader = EnhancedPatternLoader(enhanced_pattern_loader_config)
        enhanced_pattern_loader.initialize()  # Initialize the service
        registry.register_singleton("enhanced_pattern_loader", enhanced_pattern_loader, dependencies=["config", "logger", "cache"])
        registered_services.append("enhanced_pattern_loader")
        logger.info("✅ Registered enhanced pattern loader service")
        
        # 12. Register Pattern Analytics Service (depends on config, logger, enhanced_pattern_loader)
        pattern_analytics_config = config_overrides.get("pattern_analytics_service", {
            "enable_real_time_analytics": True,
            "analytics_retention_days": 30,
            "performance_window_minutes": 60,
            "trend_analysis_enabled": True,
            "export_analytics": True,
            "alert_thresholds": {
                "low_success_rate": 0.7,
                "high_response_time_ms": 1000,
                "pattern_usage_spike": 5.0
            }
        })
        
        from app.services.pattern_analytics_service import PatternAnalyticsService
        pattern_analytics_service = PatternAnalyticsService(pattern_analytics_config)
        pattern_analytics_service.initialize()  # Initialize the service
        registry.register_singleton("pattern_analytics_service", pattern_analytics_service, dependencies=["config", "logger", "enhanced_pattern_loader"])
        registered_services.append("pattern_analytics_service")
        logger.info("✅ Registered pattern analytics service")
        
        # 13. Register Pattern Enhancement Service (depends on config, logger, llm_provider_factory, enhanced_pattern_loader)
        config_overrides.get("pattern_enhancement_service", {
            "enhancement_types": ["full", "technical", "agentic"],
            "default_enhancement_type": "full",
            "max_concurrent_enhancements": 3,
            "enhancement_timeout_seconds": 300,
            "enable_validation": True,
            "backup_original_patterns": True,
            "llm_provider": "openai",
            "llm_model": "gpt-4o",
            "temperature": 0.3,
            "max_tokens": 4000
        })
        
        from app.services.pattern_enhancement_service import PatternEnhancementService
        
        # Get the required dependencies
        llm_factory_service = registry.get("llm_provider_factory")
        enhanced_loader = registry.get("enhanced_pattern_loader")
        
        # Create a default LLM provider for the enhancement service
        default_llm_config = {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.3,
            "max_tokens": 4000
        }
        
        # Create LLM provider instance
        llm_provider_result = llm_factory_service.create_provider("openai", **default_llm_config)
        
        if not llm_provider_result.is_success():
            # Fallback to fake provider for testing
            llm_provider_result = llm_factory_service.create_provider("fake")
        
        llm_provider = llm_provider_result.value
        
        pattern_enhancement_service = PatternEnhancementService(enhanced_loader, llm_provider)
        registry.register_singleton("pattern_enhancement_service", pattern_enhancement_service, dependencies=["config", "logger", "llm_provider_factory", "enhanced_pattern_loader"])
        registered_services.append("pattern_enhancement_service")
        logger.info("✅ Registered pattern enhancement service")
        
        # 14. Register Tech Stack Monitoring Integration Service (depends on config, logger)
        monitoring_integration_config = config_overrides.get("tech_stack_monitoring_integration", {
            "enable_monitoring": True,
            "session_timeout": 3600,
            "max_sessions": 100
        })
        
        from app.services.monitoring_integration_service import TechStackMonitoringIntegrationService
        monitoring_integration_service = TechStackMonitoringIntegrationService(monitoring_integration_config)
        registry.register_singleton("tech_stack_monitoring_integration", monitoring_integration_service, dependencies=["config", "logger"])
        registered_services.append("tech_stack_monitoring_integration")
        logger.info("✅ Registered tech stack monitoring integration service")
        
        logger.info(f"Successfully registered {len(registered_services)} core services: {registered_services}")
        
        return registered_services
        
    except Exception as e:
        logger.error(f"Failed to register core services: {e}")
        
        # Clean up any partially registered services
        for service_name in registered_services:
            try:
                if registry.has(service_name):
                    # Note: The registry doesn't have an unregister method,
                    # so we'll just log the cleanup attempt
                    logger.warning(f"Service {service_name} may need manual cleanup")
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup of {service_name}: {cleanup_error}")
        
        raise


def register_logger_service(registry: Optional[ServiceRegistry] = None, 
                           config: Optional[Dict[str, Any]] = None) -> None:
    """
    Register the logger service.
    
    Args:
        registry: Service registry instance (uses global if None)
        config: Logger service configuration
    """
    if registry is None:
        registry = get_registry()
    
    config = config or {
        "level": "INFO",
        "format": "structured",
        "redact_pii": True,
        "file_path": "logs/aaa.log"
    }
    
    logger_service = LoggerService(config)
    registry.register_singleton("logger", logger_service, dependencies=["config"])
    logger.info("Logger service registered")


def register_config_service(registry: Optional[ServiceRegistry] = None, 
                           config: Optional[Dict[str, Any]] = None) -> None:
    """
    Register the configuration service.
    
    Args:
        registry: Service registry instance (uses global if None)
        config: Configuration service settings
    """
    if registry is None:
        registry = get_registry()
    
    config = config or {
        "config_file": "config.yaml",
        "environment_prefix": "AAA",
        "auto_reload": False,
        "validation_enabled": True
    }
    
    config_service = ConfigService(config)
    registry.register_singleton("config", config_service, dependencies=[])
    logger.info("Configuration service registered")


def register_cache_service(registry: Optional[ServiceRegistry] = None, 
                          config: Optional[Dict[str, Any]] = None) -> None:
    """
    Register the cache service.
    
    Args:
        registry: Service registry instance (uses global if None)
        config: Cache service configuration
    """
    if registry is None:
        registry = get_registry()
    
    config = config or {
        "backend": "memory",
        "default_ttl_seconds": 3600,
        "max_size_mb": 100
    }
    
    cache_service = CacheService(config)
    registry.register_singleton("cache", cache_service, dependencies=["config", "logger"])
    logger.info("Cache service registered")


def register_security_services(registry: Optional[ServiceRegistry] = None, 
                               validator_config: Optional[Dict[str, Any]] = None,
                               defender_config: Optional[Dict[str, Any]] = None) -> None:
    """
    Register security services (validator and advanced defender).
    
    Args:
        registry: Service registry instance (uses global if None)
        validator_config: Security validator configuration
        defender_config: Advanced prompt defender configuration
    """
    if registry is None:
        registry = get_registry()
    
    # Register security validator
    validator_config = validator_config or {
        "enable_input_validation": True,
        "enable_output_sanitization": True,
        "max_input_length": 10000
    }
    
    security_service = SecurityService(validator_config)
    registry.register_singleton("security_validator", security_service, dependencies=["config", "logger"])
    logger.info("Security validator service registered")
    
    # Register advanced prompt defender
    defender_config = defender_config or {
        "enabled": True,
        "detection_confidence_threshold": 0.7,
        "enable_caching": True
    }
    
    advanced_defense_service = AdvancedPromptDefenseService(defender_config)
    registry.register_singleton("advanced_prompt_defender", advanced_defense_service, 
                               dependencies=["config", "logger", "cache"])
    logger.info("Advanced prompt defender service registered")


def register_llm_provider_factory(registry: Optional[ServiceRegistry] = None, 
                                  config: Optional[Dict[str, Any]] = None) -> None:
    """
    Register the LLM provider factory service.
    
    Args:
        registry: Service registry instance (uses global if None)
        config: LLM provider factory configuration
    """
    if registry is None:
        registry = get_registry()
    
    config = config or {
        "default_provider": "openai",
        "fallback_providers": ["anthropic", "bedrock"],
        "timeout_seconds": 30,
        "max_retries": 3,
        "retry_delay_seconds": 1.0
    }
    
    llm_factory = LLMProviderFactory(config)
    registry.register_singleton("llm_provider_factory", llm_factory, dependencies=["config", "logger"])
    logger.info("LLM provider factory service registered")


def register_diagram_service_factory(registry: Optional[ServiceRegistry] = None, 
                                     config: Optional[Dict[str, Any]] = None) -> None:
    """
    Register the diagram service factory.
    
    Args:
        registry: Service registry instance (uses global if None)
        config: Diagram service factory configuration
    """
    if registry is None:
        registry = get_registry()
    
    config = config or {
        "mermaid_config": {
            "default_height": 400,
            "enable_enhanced_rendering": True
        },
        "infrastructure_config": {
            "default_format": "png",
            "enable_dynamic_mapping": True
        },
        "drawio_config": {
            "enable_multiple_formats": True,
            "include_metadata": True
        }
    }
    
    diagram_factory = DiagramServiceFactory(config)
    registry.register_singleton("diagram_service_factory", diagram_factory, dependencies=["config", "logger"])
    logger.info("Diagram service factory registered")


def register_pattern_loader(registry: Optional[ServiceRegistry] = None, 
                           config: Optional[Dict[str, Any]] = None) -> None:
    """
    Register the pattern loader service.
    
    Args:
        registry: Service registry instance (uses global if None)
        config: Pattern loader configuration
    """
    if registry is None:
        registry = get_registry()
    
    config = config or {
        "pattern_library_path": "./data/patterns"
    }
    
    from app.pattern.loader import PatternLoader
    pattern_loader = PatternLoader(config.get("pattern_library_path", "./data/patterns"))
    registry.register_singleton("pattern_loader", pattern_loader, dependencies=["config"])
    logger.info("Pattern loader service registered")


def initialize_core_services(registry: Optional[ServiceRegistry] = None) -> Dict[str, bool]:
    """
    Initialize all registered core services.
    
    Args:
        registry: Service registry instance (uses global if None)
        
    Returns:
        Dictionary mapping service names to initialization success status
    """
    if registry is None:
        registry = get_registry()
    
    core_services = ["config", "logger", "cache", "security_validator", "advanced_prompt_defender", "llm_provider_factory", "diagram_service_factory", "pattern_loader", "audit_logger", "infrastructure_diagram_service", "enhanced_pattern_loader", "pattern_analytics_service", "pattern_enhancement_service"]
    initialization_results = {}
    
    logger.info("Initializing core services...")
    
    for service_name in core_services:
        try:
            if registry.has(service_name):
                service = registry.get(service_name)
                if hasattr(service, 'initialize'):
                    service.initialize()
                    initialization_results[service_name] = True
                    logger.info(f"✅ Initialized {service_name} service")
                else:
                    logger.warning(f"Service {service_name} does not have initialize method")
                    initialization_results[service_name] = False
            else:
                logger.warning(f"Service {service_name} not registered")
                initialization_results[service_name] = False
                
        except Exception as e:
            logger.error(f"Failed to initialize {service_name} service: {e}")
            initialization_results[service_name] = False
    
    successful_count = sum(1 for success in initialization_results.values() if success)
    total_count = len(initialization_results)
    
    logger.info(f"Core service initialization complete: {successful_count}/{total_count} services initialized")
    
    return initialization_results


def get_core_service_health() -> Dict[str, bool]:
    """
    Get health status of all core services.
    
    Returns:
        Dictionary mapping service names to health status
    """
    registry = get_registry()
    core_services = ["config", "logger", "cache", "security_validator", "advanced_prompt_defender", "llm_provider_factory", "diagram_service_factory", "pattern_loader", "audit_logger", "infrastructure_diagram_service", "enhanced_pattern_loader", "pattern_analytics_service", "pattern_enhancement_service"]
    health_status = {}
    
    for service_name in core_services:
        try:
            if registry.has(service_name):
                service = registry.get(service_name)
                if hasattr(service, 'health_check'):
                    health_status[service_name] = service.health_check()
                else:
                    health_status[service_name] = True  # Assume healthy if no health check
            else:
                health_status[service_name] = False
        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            health_status[service_name] = False
    
    return health_status


def validate_core_service_dependencies() -> List[str]:
    """
    Validate that all core service dependencies are properly registered.
    
    Returns:
        List of dependency validation errors (empty if all valid)
    """
    registry = get_registry()
    return registry.validate_dependencies()


if __name__ == "__main__":
    """Test core service registration when run directly."""
    import sys
    
    # Set up basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Register core services
        registered = register_core_services()
        print(f"✅ Successfully registered services: {registered}")
        
        # Initialize services
        init_results = initialize_core_services()
        print(f"✅ Service initialization results: {init_results}")
        
        # Check health
        health_status = get_core_service_health()
        print(f"✅ Service health status: {health_status}")
        
        # Validate dependencies
        dependency_errors = validate_core_service_dependencies()
        if dependency_errors:
            print(f"⚠️  Dependency validation errors: {dependency_errors}")
        else:
            print("✅ All dependencies validated successfully")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Core service registration failed: {e}")
        sys.exit(1)