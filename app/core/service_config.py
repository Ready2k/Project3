"""
Service Configuration Management

This module provides configuration loading and validation for services,
integrating with the existing configuration system and supporting
environment-specific overrides.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
import logging

from app.core.dependencies import DependencyValidator, DependencyInfo, DependencyType

logger = logging.getLogger(__name__)


class ServiceConfigError(Exception):
    """Raised when service configuration is invalid."""

    pass


@dataclass
class ServiceDefinition:
    """Definition of a service from configuration."""

    name: str
    class_path: str
    singleton: bool = True
    dependencies: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    health_check: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class DependencyDefinition:
    """Definition of a dependency from configuration."""

    name: str
    version_constraint: Optional[str]
    import_name: str
    installation_name: str
    purpose: str
    alternatives: List[str]
    category: str
    dependency_type: DependencyType
    documentation_url: Optional[str] = None
    features_enabled: List[str] = field(default_factory=list)
    system_requirements: List[str] = field(default_factory=list)
    installation_notes: Optional[str] = None


class ServiceConfigLoader:
    """
    Loads and validates service configuration from YAML files.

    Supports environment-specific overrides and integration with
    the existing configuration system.
    """

    def __init__(self, config_dir: Union[str, Path] = "config"):
        """
        Initialize the service configuration loader.

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.services_config_path = self.config_dir / "services.yaml"
        self.dependencies_config_path = self.config_dir / "dependencies.yaml"
        self.environment = self._detect_environment()

        self._services_config: Dict[str, Any] = {}
        self._dependencies_config: Dict[str, Any] = {}
        self._loaded = False

    def _detect_environment(self) -> str:
        """Detect the current environment from various sources."""
        # Check environment variable first
        env = os.getenv("ENVIRONMENT", os.getenv("ENV", ""))
        if env:
            return env.lower()

        # Check for common environment indicators
        if os.getenv("PYTEST_CURRENT_TEST"):
            return "testing"

        if os.getenv("DEBUG", "").lower() in ("true", "1", "yes"):
            return "development"

        # Default to development
        return "development"

    def load_configuration(self) -> None:
        """Load service and dependency configuration from files."""
        try:
            # Load services configuration
            if self.services_config_path.exists():
                with open(self.services_config_path, "r") as f:
                    self._services_config = yaml.safe_load(f) or {}
                logger.info(
                    f"Loaded services configuration from {self.services_config_path}"
                )
            else:
                logger.warning(
                    f"Services configuration file not found: {self.services_config_path}"
                )
                self._services_config = {}

            # Load dependencies configuration
            if self.dependencies_config_path.exists():
                with open(self.dependencies_config_path, "r") as f:
                    self._dependencies_config = yaml.safe_load(f) or {}
                logger.info(
                    f"Loaded dependencies configuration from {self.dependencies_config_path}"
                )
            else:
                logger.warning(
                    f"Dependencies configuration file not found: {self.dependencies_config_path}"
                )
                self._dependencies_config = {}

            # Apply environment-specific overrides
            self._apply_environment_overrides()

            self._loaded = True
            logger.info(
                f"Configuration loaded successfully for environment: {self.environment}"
            )

        except Exception as e:
            raise ServiceConfigError(f"Failed to load configuration: {e}") from e

    def _apply_environment_overrides(self) -> None:
        """Apply environment-specific configuration overrides."""
        # Apply service environment overrides
        if "environments" in self._services_config:
            env_overrides = self._services_config["environments"].get(
                self.environment, {}
            )
            if env_overrides:
                logger.info(
                    f"Applying service environment overrides for: {self.environment}"
                )
                self._apply_service_overrides(env_overrides)

        # Apply dependency environment overrides
        if "environments" in self._dependencies_config:
            env_config = self._dependencies_config["environments"].get(
                self.environment, {}
            )
            if env_config:
                logger.info(
                    f"Applying dependency environment overrides for: {self.environment}"
                )
                # Environment-specific dependency configuration is handled by dependency validator

    def _apply_service_overrides(self, overrides: Dict[str, Any]) -> None:
        """Apply service configuration overrides."""
        services = self._services_config.get("services", {})

        for service_name, override_config in overrides.items():
            if service_name in services:
                # Deep merge the override configuration
                self._deep_merge(services[service_name], override_config)
                logger.debug(f"Applied overrides for service: {service_name}")

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Deep merge override configuration into base configuration."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def get_service_definitions(self) -> List[ServiceDefinition]:
        """
        Get all service definitions from configuration.

        Returns:
            List of ServiceDefinition objects
        """
        if not self._loaded:
            self.load_configuration()

        services = []
        services_config = self._services_config.get("services", {})

        for name, config in services_config.items():
            try:
                service_def = ServiceDefinition(
                    name=name,
                    class_path=config["class_path"],
                    singleton=config.get("singleton", True),
                    dependencies=config.get("dependencies", []),
                    config=config.get("config", {}),
                    health_check=config.get("health_check", {}),
                    enabled=config.get("enabled", True),
                )
                services.append(service_def)

            except KeyError as e:
                logger.error(f"Invalid service configuration for '{name}': missing {e}")
                continue

        logger.info(f"Loaded {len(services)} service definitions")
        return services

    def get_service_definition(self, name: str) -> Optional[ServiceDefinition]:
        """
        Get a specific service definition by name.

        Args:
            name: Service name

        Returns:
            ServiceDefinition if found, None otherwise
        """
        services = self.get_service_definitions()
        for service in services:
            if service.name == name:
                return service
        return None

    def get_dependency_definitions(self) -> List[DependencyDefinition]:
        """
        Get all dependency definitions from configuration.

        Returns:
            List of DependencyDefinition objects
        """
        if not self._loaded:
            self.load_configuration()

        dependencies = []
        deps_config = self._dependencies_config.get("dependencies", {})

        # Process each dependency type
        for dep_type_name, dep_list in deps_config.items():
            if not isinstance(dep_list, list):
                continue

            # Map dependency type name to enum
            try:
                dep_type = DependencyType(dep_type_name)
            except ValueError:
                logger.warning(f"Unknown dependency type: {dep_type_name}")
                continue

            for dep_config in dep_list:
                try:
                    dep_def = DependencyDefinition(
                        name=dep_config["name"],
                        version_constraint=dep_config.get("version_constraint"),
                        import_name=dep_config.get("import_name", dep_config["name"]),
                        installation_name=dep_config.get(
                            "installation_name", dep_config["name"]
                        ),
                        purpose=dep_config["purpose"],
                        alternatives=dep_config.get("alternatives", []),
                        category=dep_config.get("category", "general"),
                        dependency_type=dep_type,
                        documentation_url=dep_config.get("documentation_url"),
                        features_enabled=dep_config.get("features_enabled", []),
                        system_requirements=dep_config.get("system_requirements", []),
                        installation_notes=dep_config.get("installation_notes"),
                    )
                    dependencies.append(dep_def)

                except KeyError as e:
                    logger.error(
                        f"Invalid dependency configuration for '{dep_config.get('name', 'unknown')}': missing {e}"
                    )
                    continue

        logger.info(f"Loaded {len(dependencies)} dependency definitions")
        return dependencies

    def get_dependency_groups(self) -> Dict[str, Dict[str, Any]]:
        """
        Get dependency groups for easy installation.

        Returns:
            Dictionary mapping group names to group configuration
        """
        if not self._loaded:
            self.load_configuration()

        return self._dependencies_config.get("dependency_groups", {})

    def get_feature_dependencies(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Get feature to dependency mapping.

        Returns:
            Dictionary mapping features to their required and optional dependencies
        """
        if not self._loaded:
            self.load_configuration()

        return self._dependencies_config.get("feature_dependencies", {})

    def validate_service_configuration(self) -> List[str]:
        """
        Validate service configuration for consistency and completeness.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        services = self.get_service_definitions()
        service_names = {service.name for service in services}

        # Check for dependency references
        for service in services:
            for dep_name in service.dependencies:
                if dep_name not in service_names:
                    errors.append(
                        f"Service '{service.name}' depends on undefined service '{dep_name}'"
                    )

        # Check for circular dependencies (basic check)
        for service in services:
            if self._has_circular_dependency(service, services, set()):
                errors.append(
                    f"Circular dependency detected involving service '{service.name}'"
                )

        # Validate class paths (basic format check)
        for service in services:
            if not self._is_valid_class_path(service.class_path):
                errors.append(
                    f"Invalid class path for service '{service.name}': {service.class_path}"
                )

        return errors

    def _has_circular_dependency(
        self,
        service: ServiceDefinition,
        all_services: List[ServiceDefinition],
        visited: set,
    ) -> bool:
        """Check for circular dependencies in service definitions."""
        if service.name in visited:
            return True

        visited.add(service.name)
        service_map = {s.name: s for s in all_services}

        for dep_name in service.dependencies:
            if dep_name in service_map:
                if self._has_circular_dependency(
                    service_map[dep_name], all_services, visited.copy()
                ):
                    return True

        return False

    def _is_valid_class_path(self, class_path: str) -> bool:
        """Validate that a class path has the correct format."""
        if not class_path or "." not in class_path:
            return False

        parts = class_path.split(".")
        # Should have at least module.class format
        return len(parts) >= 2 and all(part.isidentifier() for part in parts)

    def setup_dependency_validator(self) -> DependencyValidator:
        """
        Set up the dependency validator with configuration from files.

        Returns:
            Configured DependencyValidator instance
        """
        from app.core.dependencies import get_dependency_validator

        validator = get_dependency_validator()
        dependency_defs = self.get_dependency_definitions()

        # Clear existing dependencies and add from configuration
        validator.dependencies.clear()

        for dep_def in dependency_defs:
            dep_info = DependencyInfo(
                name=dep_def.name,
                version_constraint=dep_def.version_constraint,
                dependency_type=dep_def.dependency_type,
                purpose=dep_def.purpose,
                alternatives=dep_def.alternatives,
                import_name=dep_def.import_name,
                installation_name=dep_def.installation_name,
            )
            validator.add_dependency(dep_info)

        logger.info(
            f"Configured dependency validator with {len(dependency_defs)} dependencies"
        )
        return validator

    def get_installation_command(self, group_name: str) -> Optional[str]:
        """
        Get pip installation command for a dependency group.

        Args:
            group_name: Name of the dependency group

        Returns:
            Pip install command string or None if group not found
        """
        groups = self.get_dependency_groups()
        if group_name not in groups:
            return None

        group_config = groups[group_name]
        dependencies = group_config.get("dependencies", [])

        if not dependencies:
            return None

        return f"pip install {' '.join(dependencies)}"

    def get_environment_requirements(self) -> Dict[str, List[str]]:
        """
        Get dependency requirements for the current environment.

        Returns:
            Dictionary with 'required_groups' and 'optional_groups' lists
        """
        if not self._loaded:
            self.load_configuration()

        env_config = self._dependencies_config.get("environments", {}).get(
            self.environment, {}
        )

        return {
            "required_groups": env_config.get("required_groups", []),
            "optional_groups": env_config.get("optional_groups", []),
        }


# Global service configuration loader
_service_config_loader: Optional[ServiceConfigLoader] = None


def get_service_config_loader(
    config_dir: Union[str, Path] = "config",
) -> ServiceConfigLoader:
    """
    Get the global service configuration loader instance.

    Args:
        config_dir: Directory containing configuration files

    Returns:
        ServiceConfigLoader instance
    """
    global _service_config_loader
    if _service_config_loader is None:
        _service_config_loader = ServiceConfigLoader(config_dir)
    return _service_config_loader


def load_service_configuration(
    config_dir: Union[str, Path] = "config",
) -> ServiceConfigLoader:
    """
    Load service configuration and return the loader.

    Args:
        config_dir: Directory containing configuration files

    Returns:
        Loaded ServiceConfigLoader instance
    """
    loader = get_service_config_loader(config_dir)
    loader.load_configuration()
    return loader


def validate_startup_configuration(
    config_dir: Union[str, Path] = "config",
) -> Dict[str, Any]:
    """
    Validate configuration at application startup.

    Args:
        config_dir: Directory containing configuration files

    Returns:
        Dictionary with validation results
    """
    loader = load_service_configuration(config_dir)

    # Validate service configuration
    service_errors = loader.validate_service_configuration()

    # Set up and validate dependencies
    validator = loader.setup_dependency_validator()
    dependency_result = validator.validate_all()

    # Get environment requirements
    env_requirements = loader.get_environment_requirements()

    return {
        "service_errors": service_errors,
        "dependency_validation": dependency_result,
        "environment_requirements": env_requirements,
        "environment": loader.environment,
        "services_loaded": len(loader.get_service_definitions()),
        "dependencies_loaded": len(loader.get_dependency_definitions()),
    }
