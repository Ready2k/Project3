"""
Application Startup and Initialization

This module provides startup validation and initialization for the application,
including service registration, dependency validation, and configuration loading.
"""

import sys
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from app.core.registry import get_registry, ServiceRegistry
from app.core.service_config import validate_startup_configuration, get_service_config_loader
from app.core.dependencies import validate_startup_dependencies
from app.core.service_registration import register_core_services, initialize_core_services

logger = logging.getLogger(__name__)


class StartupError(Exception):
    """Raised when application startup fails."""
    pass


class ApplicationStartup:
    """
    Manages application startup process including configuration loading,
    dependency validation, and service registration.
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize the startup manager.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = config_dir
        self.registry = get_registry()
        self.config_loader = get_service_config_loader(config_dir)
        self._startup_completed = False
        self._validation_results: Dict[str, Any] = {}
    
    def run_startup_sequence(self, include_dev_deps: bool = False) -> Dict[str, Any]:
        """
        Run the complete startup sequence.
        
        Args:
            include_dev_deps: Whether to validate development dependencies
            
        Returns:
            Dictionary with startup results and validation information
            
        Raises:
            StartupError: If startup fails
        """
        try:
            logger.info("Starting application startup sequence...")
            
            # Step 1: Load and validate configuration
            logger.info("Step 1: Loading and validating configuration...")
            config_results = self._validate_configuration()
            
            # Step 2: Validate dependencies
            logger.info("Step 2: Validating dependencies...")
            dependency_results = self._validate_dependencies(include_dev_deps)
            
            # Step 3: Register services
            logger.info("Step 3: Registering services...")
            service_results = self._register_services()
            
            # Step 4: Validate service registry
            logger.info("Step 4: Validating service registry...")
            registry_results = self._validate_registry()
            
            # Compile results
            self._validation_results = {
                'startup_successful': True,
                'configuration': config_results,
                'dependencies': dependency_results,
                'services': service_results,
                'registry': registry_results,
                'environment': self.config_loader.environment
            }
            
            self._startup_completed = True
            logger.info("Application startup completed successfully")
            
            return self._validation_results
            
        except Exception as e:
            error_msg = f"Application startup failed: {e}"
            logger.error(error_msg)
            
            self._validation_results = {
                'startup_successful': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
            
            raise StartupError(error_msg) from e
    
    def _validate_configuration(self) -> Dict[str, Any]:
        """Validate configuration files and settings."""
        try:
            # Load configuration
            self.config_loader.load_configuration()
            
            # Validate service configuration
            service_errors = self.config_loader.validate_service_configuration()
            
            # Get configuration summary
            services = self.config_loader.get_service_definitions()
            dependencies = self.config_loader.get_dependency_definitions()
            
            results = {
                'valid': len(service_errors) == 0,
                'service_errors': service_errors,
                'services_loaded': len(services),
                'dependencies_loaded': len(dependencies),
                'environment': self.config_loader.environment
            }
            
            if service_errors:
                logger.warning(f"Configuration validation found {len(service_errors)} errors")
                for error in service_errors:
                    logger.warning(f"  - {error}")
            else:
                logger.info("Configuration validation passed")
            
            return results
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise
    
    def _validate_dependencies(self, include_dev: bool = False) -> Dict[str, Any]:
        """Validate system dependencies."""
        try:
            # Set up dependency validator from configuration
            validator = self.config_loader.setup_dependency_validator()
            
            # Run validation
            validation_result = validator.validate_all(include_dev=include_dev)
            
            # Log results
            if validation_result.is_valid:
                logger.info("Dependency validation passed")
            else:
                logger.warning("Dependency validation found issues:")
                
                if validation_result.missing_required:
                    logger.error(f"Missing required dependencies: {validation_result.missing_required}")
                
                if validation_result.missing_optional:
                    logger.info(f"Missing optional dependencies: {validation_result.missing_optional}")
                
                if validation_result.version_conflicts:
                    logger.warning(f"Version conflicts: {validation_result.version_conflicts}")
            
            # Log warnings
            for warning in validation_result.warnings:
                logger.warning(warning)
            
            # Print installation instructions if needed
            if validation_result.installation_instructions:
                logger.info("Installation instructions:")
                for line in validation_result.installation_instructions.split('\n'):
                    if line.strip():
                        logger.info(f"  {line}")
            
            return {
                'valid': validation_result.is_valid,
                'missing_required': validation_result.missing_required,
                'missing_optional': validation_result.missing_optional,
                'version_conflicts': validation_result.version_conflicts,
                'warnings': validation_result.warnings,
                'installation_instructions': validation_result.installation_instructions
            }
            
        except Exception as e:
            logger.error(f"Dependency validation failed: {e}")
            raise
    
    def _register_services(self) -> Dict[str, Any]:
        """Register services in the service registry."""
        try:
            # First register core services
            core_services = register_core_services(self.registry)
            logger.info(f"Registered {len(core_services)} core services")
            
            # Then register additional services from configuration
            services = self.config_loader.get_service_definitions()
            additional_services = []
            failed_services = []
            
            # Skip core services that are already registered
            core_service_names = {"config", "logger", "cache", "security_validator", "advanced_prompt_defender"}
            
            for service_def in services:
                if service_def.name in core_service_names:
                    logger.debug(f"Skipping core service {service_def.name} (already registered)")
                    continue
                    
                if not service_def.enabled:
                    logger.debug(f"Skipping disabled service: {service_def.name}")
                    continue
                
                try:
                    # Import the service class
                    module_path, class_name = service_def.class_path.rsplit('.', 1)
                    module = __import__(module_path, fromlist=[class_name])
                    service_class = getattr(module, class_name)
                    
                    # Register the service
                    if service_def.singleton:
                        self.registry.register_class(
                            service_def.name,
                            service_class,
                            service_def.dependencies
                        )
                    else:
                        # For non-singleton services, register as factory
                        def create_service():
                            return service_class(**service_def.config)
                        
                        self.registry.register_factory(
                            service_def.name,
                            create_service,
                            service_def.dependencies
                        )
                    
                    additional_services.append(service_def.name)
                    logger.debug(f"Registered service: {service_def.name}")
                    
                except Exception as e:
                    error_msg = f"Failed to register service '{service_def.name}': {e}"
                    logger.error(error_msg)
                    failed_services.append({
                        'name': service_def.name,
                        'error': str(e)
                    })
            
            # Initialize core services
            init_results = initialize_core_services(self.registry)
            successful_inits = sum(1 for success in init_results.values() if success)
            
            all_registered = core_services + additional_services
            
            results = {
                'registered_count': len(all_registered),
                'failed_count': len(failed_services),
                'registered_services': all_registered,
                'failed_services': failed_services,
                'core_services': core_services,
                'additional_services': additional_services,
                'initialization_results': init_results,
                'initialized_count': successful_inits
            }
            
            if failed_services:
                logger.warning(f"Failed to register {len(failed_services)} services")
            else:
                logger.info(f"Successfully registered {len(all_registered)} services ({len(core_services)} core + {len(additional_services)} additional)")
            
            logger.info(f"Initialized {successful_inits}/{len(core_services)} core services")
            
            return results
            
        except Exception as e:
            logger.error(f"Service registration failed: {e}")
            raise
    
    def _validate_registry(self) -> Dict[str, Any]:
        """Validate the service registry after registration."""
        try:
            # Validate dependencies
            dependency_errors = self.registry.validate_dependencies()
            
            # Get registry status
            service_names = self.registry.list_services()
            health_status = self.registry.health_check()
            
            results = {
                'valid': len(dependency_errors) == 0,
                'dependency_errors': dependency_errors,
                'registered_services': service_names,
                'service_count': len(service_names),
                'health_status': health_status
            }
            
            if dependency_errors:
                logger.warning("Service registry validation found issues:")
                for error in dependency_errors:
                    logger.warning(f"  - {error}")
            else:
                logger.info(f"Service registry validation passed ({len(service_names)} services)")
            
            return results
            
        except Exception as e:
            logger.error(f"Registry validation failed: {e}")
            raise
    
    def get_startup_report(self) -> str:
        """
        Generate a comprehensive startup report.
        
        Returns:
            Formatted startup report string
        """
        if not self._validation_results:
            return "Startup has not been completed yet."
        
        lines = [
            "Application Startup Report",
            "=" * 50,
            ""
        ]
        
        # Overall status
        if self._validation_results.get('startup_successful', False):
            lines.append("✅ Startup Status: SUCCESS")
        else:
            lines.append("❌ Startup Status: FAILED")
            if 'error' in self._validation_results:
                lines.append(f"   Error: {self._validation_results['error']}")
        
        lines.append("")
        
        # Environment
        env = self._validation_results.get('environment', 'unknown')
        lines.append(f"🌍 Environment: {env}")
        lines.append("")
        
        # Configuration
        config = self._validation_results.get('configuration', {})
        lines.append("📋 Configuration:")
        lines.append(f"   Services loaded: {config.get('services_loaded', 0)}")
        lines.append(f"   Dependencies loaded: {config.get('dependencies_loaded', 0)}")
        if config.get('service_errors'):
            lines.append(f"   ⚠️  Configuration errors: {len(config['service_errors'])}")
        lines.append("")
        
        # Dependencies
        deps = self._validation_results.get('dependencies', {})
        lines.append("📦 Dependencies:")
        if deps.get('valid', False):
            lines.append("   ✅ All required dependencies available")
        else:
            if deps.get('missing_required'):
                lines.append(f"   ❌ Missing required: {', '.join(deps['missing_required'])}")
            if deps.get('version_conflicts'):
                lines.append(f"   ⚠️  Version conflicts: {len(deps['version_conflicts'])}")
        
        if deps.get('missing_optional'):
            lines.append(f"   ℹ️  Missing optional: {', '.join(deps['missing_optional'])}")
        lines.append("")
        
        # Services
        services = self._validation_results.get('services', {})
        lines.append("🔧 Services:")
        lines.append(f"   Registered: {services.get('registered_count', 0)}")
        if services.get('failed_count', 0) > 0:
            lines.append(f"   ❌ Failed: {services['failed_count']}")
        lines.append("")
        
        # Registry
        registry = self._validation_results.get('registry', {})
        lines.append("🏪 Service Registry:")
        if registry.get('valid', False):
            lines.append("   ✅ All dependencies resolved")
        else:
            lines.append(f"   ❌ Dependency errors: {len(registry.get('dependency_errors', []))}")
        
        health_status = registry.get('health_status', {})
        healthy_services = sum(1 for status in health_status.values() if status)
        total_services = len(health_status)
        lines.append(f"   Health: {healthy_services}/{total_services} services healthy")
        
        return "\n".join(lines)
    
    def is_startup_completed(self) -> bool:
        """Check if startup has been completed successfully."""
        return self._startup_completed
    
    def get_validation_results(self) -> Dict[str, Any]:
        """Get the validation results from startup."""
        return self._validation_results.copy()


def run_application_startup(config_dir: str = "config", include_dev_deps: bool = False) -> Dict[str, Any]:
    """
    Run the application startup sequence.
    
    Args:
        config_dir: Directory containing configuration files
        include_dev_deps: Whether to validate development dependencies
        
    Returns:
        Dictionary with startup results
        
    Raises:
        StartupError: If startup fails
    """
    startup = ApplicationStartup(config_dir)
    return startup.run_startup_sequence(include_dev_deps)


def validate_environment_setup(config_dir: str = "config") -> bool:
    """
    Quick validation of environment setup without full startup.
    
    Args:
        config_dir: Directory containing configuration files
        
    Returns:
        True if environment is properly set up, False otherwise
    """
    try:
        # Basic configuration validation
        config_results = validate_startup_configuration(config_dir)
        
        # Check for critical issues
        if config_results['service_errors']:
            logger.error("Service configuration has errors")
            return False
        
        if not config_results['dependency_validation'].is_valid:
            missing_required = config_results['dependency_validation'].missing_required
            if missing_required:
                logger.error(f"Missing required dependencies: {missing_required}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Environment validation failed: {e}")
        return False


def print_startup_summary(results: Dict[str, Any]) -> None:
    """
    Print a summary of startup results to console.
    
    Args:
        results: Startup results from run_application_startup
    """
    startup = ApplicationStartup()
    startup._validation_results = results
    print(startup.get_startup_report())


if __name__ == "__main__":
    """Run startup validation when executed directly."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate application startup")
    parser.add_argument("--config-dir", default="config", help="Configuration directory")
    parser.add_argument("--include-dev", action="store_true", help="Include development dependencies")
    parser.add_argument("--quick", action="store_true", help="Quick validation only")
    
    args = parser.parse_args()
    
    # Set up basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        if args.quick:
            # Quick validation
            if validate_environment_setup(args.config_dir):
                print("✅ Environment validation passed")
                sys.exit(0)
            else:
                print("❌ Environment validation failed")
                sys.exit(1)
        else:
            # Full startup validation
            results = run_application_startup(args.config_dir, args.include_dev)
            print_startup_summary(results)
            
            if results.get('startup_successful', False):
                sys.exit(0)
            else:
                sys.exit(1)
                
    except Exception as e:
        print(f"❌ Startup validation failed: {e}")
        sys.exit(1)