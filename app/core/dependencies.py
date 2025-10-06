"""
Dependency validation system for managing and validating system dependencies.

This module provides comprehensive dependency validation including:
- Dependency information management
- Version constraint checking
- Installation instruction generation
- Startup validation
"""

from typing import List, Dict, Any, Optional, Tuple
import importlib
from dataclasses import dataclass
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class DependencyType(Enum):
    """Types of dependencies in the system."""
    REQUIRED = "required"
    OPTIONAL = "optional"
    DEVELOPMENT = "development"


@dataclass(frozen=True)
class DependencyInfo:
    """Information about a system dependency."""
    name: str
    version_constraint: Optional[str]
    dependency_type: DependencyType
    purpose: str
    alternatives: tuple  # Changed from List to tuple for hashability
    import_name: Optional[str] = None
    installation_name: Optional[str] = None
    
    def __post_init__(self):
        """Set default values after initialization."""
        if self.import_name is None:
            object.__setattr__(self, 'import_name', self.name)
        if self.installation_name is None:
            object.__setattr__(self, 'installation_name', self.name)
        # Convert list to tuple for hashability
        if isinstance(self.alternatives, list):
            object.__setattr__(self, 'alternatives', tuple(self.alternatives))


@dataclass
class ValidationResult:
    """Result of dependency validation."""
    is_valid: bool
    missing_required: List[str]
    missing_optional: List[str]
    version_conflicts: List[str]
    warnings: List[str]
    installation_instructions: str


@dataclass
class DependencyValidationResult:
    """Result of individual dependency validation."""
    is_available: bool
    installed_version: Optional[str] = None
    error_message: Optional[str] = None
    installation_instructions: Optional[str] = None


class DependencyValidator:
    """Validates system dependencies at startup and runtime."""
    
    def __init__(self):
        """Initialize the dependency validator."""
        self.dependencies: Dict[str, DependencyInfo] = {}
        self._version_cache: Dict[str, str] = {}
        self._load_dependency_definitions()
    
    def _load_dependency_definitions(self) -> None:
        """Load dependency definitions from configuration or defaults."""
        # Core required dependencies
        self.dependencies.update({
            "streamlit": DependencyInfo(
                name="streamlit",
                version_constraint=">=1.28.0",
                dependency_type=DependencyType.REQUIRED,
                purpose="Web UI framework for the application interface",
                alternatives=("dash", "gradio", "flask")
            ),
            "fastapi": DependencyInfo(
                name="fastapi",
                version_constraint=">=0.104.0",
                dependency_type=DependencyType.REQUIRED,
                purpose="API framework for backend services",
                alternatives=("flask", "django")
            ),
            "pydantic": DependencyInfo(
                name="pydantic",
                version_constraint=">=2.0.0",
                dependency_type=DependencyType.REQUIRED,
                purpose="Data validation and settings management",
                alternatives=("marshmallow", "cerberus")
            ),
            "pyyaml": DependencyInfo(
                name="pyyaml",
                version_constraint=">=6.0",
                dependency_type=DependencyType.REQUIRED,
                purpose="YAML configuration file parsing",
                alternatives=("ruamel.yaml",),
                import_name="yaml"
            )
        })
        
        # Optional dependencies
        self.dependencies.update({
            "openai": DependencyInfo(
                name="openai",
                version_constraint=">=1.3.0",
                dependency_type=DependencyType.OPTIONAL,
                purpose="OpenAI API integration for LLM services",
                alternatives=["anthropic", "local_llm", "huggingface_hub"]
            ),
            "anthropic": DependencyInfo(
                name="anthropic",
                version_constraint=">=0.7.0",
                dependency_type=DependencyType.OPTIONAL,
                purpose="Anthropic Claude API integration",
                alternatives=["openai", "local_llm"]
            ),
            "boto3": DependencyInfo(
                name="boto3",
                version_constraint=">=1.26.0",
                dependency_type=DependencyType.OPTIONAL,
                purpose="AWS services integration including Bedrock",
                alternatives=["direct_api_calls"]
            ),
            "diagrams": DependencyInfo(
                name="diagrams",
                version_constraint=">=0.23.0",
                dependency_type=DependencyType.OPTIONAL,
                purpose="Infrastructure diagram generation",
                alternatives=["mermaid_only", "manual_diagrams"]
            ),
            "graphviz": DependencyInfo(
                name="graphviz",
                version_constraint=">=0.20.0",
                dependency_type=DependencyType.OPTIONAL,
                purpose="Graph visualization for diagrams",
                alternatives=["mermaid", "manual_graphs"]
            ),
            "redis": DependencyInfo(
                name="redis",
                version_constraint=">=4.0.0",
                dependency_type=DependencyType.OPTIONAL,
                purpose="Redis client for caching services",
                alternatives=["memory_cache", "file_cache"]
            ),
            "requests": DependencyInfo(
                name="requests",
                version_constraint=">=2.28.0",
                dependency_type=DependencyType.OPTIONAL,
                purpose="HTTP client for external API calls",
                alternatives=["httpx", "urllib3"]
            )
        })
        
        # Development dependencies
        self.dependencies.update({
            "pytest": DependencyInfo(
                name="pytest",
                version_constraint=">=7.0.0",
                dependency_type=DependencyType.DEVELOPMENT,
                purpose="Testing framework",
                alternatives=["unittest", "nose2"]
            ),
            "mypy": DependencyInfo(
                name="mypy",
                version_constraint=">=1.0.0",
                dependency_type=DependencyType.DEVELOPMENT,
                purpose="Static type checking",
                alternatives=["pyright", "pyre"]
            ),
            "black": DependencyInfo(
                name="black",
                version_constraint=">=23.0.0",
                dependency_type=DependencyType.DEVELOPMENT,
                purpose="Code formatting",
                alternatives=["autopep8", "yapf"]
            )
        })
    
    def add_dependency(self, dependency: DependencyInfo) -> None:
        """Add a new dependency to the validator."""
        self.dependencies[dependency.name] = dependency
    
    def validate_dependency(self, dependency: DependencyInfo) -> DependencyValidationResult:
        """
        Validate a single dependency using DependencyInfo object.
        
        Args:
            dependency: DependencyInfo object to validate
            
        Returns:
            ValidationResult with validation details
        """
        try:
            if not dependency.import_name:
                return DependencyValidationResult(
                    is_available=False,
                    error_message="Import name is not specified",
                    installation_instructions=f"pip install {dependency.installation_name}"
                )
            
            module = importlib.import_module(dependency.import_name)
            module_version = self._get_module_version(module, dependency.import_name)
            
            if dependency.version_constraint and module_version:
                if not self._check_version_constraint(module_version, dependency.version_constraint):
                    return DependencyValidationResult(
                        is_available=False,
                        installed_version=module_version,
                        error_message=f"Version {module_version} does not satisfy constraint {dependency.version_constraint}",
                        installation_instructions=f"pip install {dependency.installation_name}{dependency.version_constraint}"
                    )
            
            return DependencyValidationResult(
                is_available=True,
                installed_version=module_version,
                installation_instructions=f"pip install {dependency.installation_name}"
            )
            
        except ImportError as e:
            return DependencyValidationResult(
                is_available=False,
                error_message=f"Import failed: {str(e)}",
                installation_instructions=f"pip install {dependency.installation_name}"
            )
        logger.debug(f"Added dependency: {dependency.name}")
    
    def remove_dependency(self, name: str) -> bool:
        """Remove a dependency from the validator."""
        if name in self.dependencies:
            del self.dependencies[name]
            logger.debug(f"Removed dependency: {name}")
            return True
        return False
    
    def validate_all(self, include_dev: bool = False) -> ValidationResult:
        """
        Validate all dependencies.
        
        Args:
            include_dev: Whether to include development dependencies in validation
            
        Returns:
            ValidationResult with detailed validation information
        """
        missing_required = []
        missing_optional = []
        version_conflicts = []
        warnings = []
        
        for name, dep_info in self.dependencies.items():
            # Skip development dependencies unless requested
            if dep_info.dependency_type == DependencyType.DEVELOPMENT and not include_dev:
                continue
            
            try:
                # Try to import the module
                if not dep_info.import_name:
                    continue
                module = importlib.import_module(dep_info.import_name)
                
                # Check version if constraint exists
                if dep_info.version_constraint:
                    module_version = self._get_module_version(module, dep_info.import_name)
                    if module_version:
                        if not self._check_version_constraint(module_version, dep_info.version_constraint):
                            conflict_msg = (
                                f"{name}: installed version {module_version} "
                                f"does not satisfy constraint {dep_info.version_constraint}"
                            )
                            version_conflicts.append(conflict_msg)
                            logger.warning(f"Version conflict detected: {conflict_msg}")
                    else:
                        warnings.append(f"Could not determine version for {name}")
                
                logger.debug(f"Dependency {name} validated successfully")
                
            except ImportError as e:
                error_msg = f"Failed to import {dep_info.import_name}: {str(e)}"
                logger.debug(error_msg)
                
                if dep_info.dependency_type == DependencyType.REQUIRED:
                    missing_required.append(name)
                    logger.error(f"Required dependency missing: {name}")
                else:
                    missing_optional.append(name)
                    warning_msg = (
                        f"Optional dependency '{name}' not available. "
                        f"Feature disabled: {dep_info.purpose}"
                    )
                    warnings.append(warning_msg)
                    logger.info(warning_msg)
        
        is_valid = len(missing_required) == 0 and len(version_conflicts) == 0
        
        # Generate installation instructions if needed
        installation_instructions = ""
        if missing_required or missing_optional:
            all_missing = missing_required + missing_optional
            installation_instructions = self.get_installation_instructions(all_missing)
        
        result = ValidationResult(
            is_valid=is_valid,
            missing_required=missing_required,
            missing_optional=missing_optional,
            version_conflicts=version_conflicts,
            warnings=warnings,
            installation_instructions=installation_instructions
        )
        
        logger.info(f"Dependency validation completed. Valid: {is_valid}")
        return result
    
    def validate_dependency_by_name(self, name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a single dependency.
        
        Args:
            name: Name of the dependency to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if name not in self.dependencies:
            return False, f"Dependency '{name}' not registered"
        
        dep_info = self.dependencies[name]
        
        try:
            if not dep_info.import_name:
                return False, "Import name is not specified"
            module = importlib.import_module(dep_info.import_name)
            
            if dep_info.version_constraint:
                module_version = self._get_module_version(module, dep_info.import_name)
                if module_version:
                    if not self._check_version_constraint(module_version, dep_info.version_constraint):
                        return False, (
                            f"Version {module_version} does not satisfy "
                            f"constraint {dep_info.version_constraint}"
                        )
            
            return True, None
            
        except ImportError as e:
            return False, f"Import failed: {str(e)}"
    
    def _get_module_version(self, module: Any, module_name: str) -> Optional[str]:
        """Get version of an imported module."""
        # Check cache first
        if module_name in self._version_cache:
            return self._version_cache[module_name]
        
        version = None
        
        # Try common version attributes
        for attr in ['__version__', 'version', 'VERSION']:
            if hasattr(module, attr):
                version_attr = getattr(module, attr)
                if isinstance(version_attr, str):
                    version = version_attr
                    break
                elif hasattr(version_attr, '__str__'):
                    version = str(version_attr)
                    break
        
        # Cache the result
        if version:
            self._version_cache[module_name] = version
            
        return version
    
    def _check_version_constraint(self, version: str, constraint: str) -> bool:
        """
        Check if version satisfies constraint.
        
        Supports constraints like: >=1.0.0, ==1.2.3, >2.0, <3.0, !=1.5.0
        """
        try:
            # Clean version strings
            version = version.strip()
            constraint = constraint.strip()
            
            # Parse constraint
            if constraint.startswith(">="):
                required_version = constraint[2:].strip()
                return self._compare_versions(version, required_version) >= 0
            elif constraint.startswith("<="):
                required_version = constraint[2:].strip()
                return self._compare_versions(version, required_version) <= 0
            elif constraint.startswith("=="):
                required_version = constraint[2:].strip()
                return self._compare_versions(version, required_version) == 0
            elif constraint.startswith("!="):
                required_version = constraint[2:].strip()
                return self._compare_versions(version, required_version) != 0
            elif constraint.startswith(">"):
                required_version = constraint[1:].strip()
                return self._compare_versions(version, required_version) > 0
            elif constraint.startswith("<"):
                required_version = constraint[1:].strip()
                return self._compare_versions(version, required_version) < 0
            else:
                # Assume exact match if no operator
                return self._compare_versions(version, constraint) == 0
                
        except Exception as e:
            logger.warning(f"Error checking version constraint '{constraint}' for version '{version}': {e}")
            return True  # Be permissive on parsing errors
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two version strings.
        
        Returns:
            -1 if version1 < version2
             0 if version1 == version2
             1 if version1 > version2
        """
        def normalize_version(v: str) -> List[int]:
            """Convert version string to list of integers."""
            # Remove any non-numeric suffixes (like 'a1', 'b2', 'rc1')
            v = re.split(r'[^\d\.]', v)[0]
            return [int(x) for x in v.split('.') if x.isdigit()]
        
        try:
            v1_parts = normalize_version(version1)
            v2_parts = normalize_version(version2)
            
            # Pad shorter version with zeros
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            # Compare part by part
            for v1_part, v2_part in zip(v1_parts, v2_parts):
                if v1_part < v2_part:
                    return -1
                elif v1_part > v2_part:
                    return 1
            
            return 0
            
        except Exception as e:
            logger.warning(f"Error comparing versions '{version1}' and '{version2}': {e}")
            return 0  # Assume equal on parsing errors
    
    def get_installation_instructions(self, missing_deps: List[str]) -> str:
        """
        Generate installation instructions for missing dependencies.
        
        Args:
            missing_deps: List of missing dependency names
            
        Returns:
            Formatted installation instructions
        """
        if not missing_deps:
            return ""
        
        instructions = ["Missing dependencies detected. Install with:\n"]
        
        # Group by installation method
        pip_packages = []
        special_instructions = []
        
        for dep_name in missing_deps:
            if dep_name in self.dependencies:
                dep_info = self.dependencies[dep_name]
                
                # Build pip package specification
                package_spec = dep_info.installation_name or dep_info.name
                if dep_info.version_constraint:
                    # Convert constraint to pip format
                    constraint = dep_info.version_constraint
                    if constraint.startswith(">="):
                        package_spec += constraint
                    elif constraint.startswith("=="):
                        package_spec += constraint
                    else:
                        # For other constraints, use >= as safe default
                        package_spec += f">={constraint.lstrip('<>=!')}"
                
                pip_packages.append(package_spec)
                
                # Add special instructions for certain packages
                if dep_name == "graphviz":
                    special_instructions.append(
                        "Note: graphviz also requires system-level installation:\n"
                        "  - Ubuntu/Debian: sudo apt-get install graphviz\n"
                        "  - macOS: brew install graphviz\n"
                        "  - Windows: Download from https://graphviz.org/download/"
                    )
                elif dep_name == "redis":
                    special_instructions.append(
                        "Note: redis package requires a Redis server:\n"
                        "  - Local: Install Redis server for your OS\n"
                        "  - Docker: docker run -d -p 6379:6379 redis:alpine\n"
                        "  - Cloud: Use managed Redis service"
                    )
        
        # Add pip install command
        if pip_packages:
            # Filter out any None values
            valid_packages = [pkg for pkg in pip_packages if pkg is not None]
            if valid_packages:
                instructions.append(f"pip install {' '.join(valid_packages)}")
        
        # Add special instructions
        if special_instructions:
            instructions.append("")
            instructions.extend(special_instructions)
        
        # Add alternatives information
        alternatives_info = []
        for dep_name in missing_deps:
            if dep_name in self.dependencies:
                dep_info = self.dependencies[dep_name]
                if dep_info.alternatives:
                    alternatives_info.append(
                        f"Alternative to {dep_name}: {', '.join(dep_info.alternatives)}"
                    )
        
        if alternatives_info:
            instructions.append("\nAlternatives:")
            instructions.extend(alternatives_info)
        
        return "\n".join(instructions)
    
    def get_dependency_report(self) -> str:
        """
        Generate a comprehensive dependency report.
        
        Returns:
            Formatted dependency report
        """
        report = ["Dependency Report", "=" * 50, ""]
        
        # Group dependencies by type
        by_type: Dict[DependencyType, List[Tuple[str, DependencyInfo]]] = {
            DependencyType.REQUIRED: [],
            DependencyType.OPTIONAL: [],
            DependencyType.DEVELOPMENT: []
        }
        
        for name, dep_info in self.dependencies.items():
            by_type[dep_info.dependency_type].append((name, dep_info))
        
        # Report each type
        for dep_type, deps in by_type.items():
            if not deps:
                continue
                
            report.append(f"{dep_type.value.title()} Dependencies:")
            report.append("-" * 30)
            
            for name, dep_info in sorted(deps):
                status = "✓" if self.validate_dependency(name)[0] else "✗"
                version_info = ""
                
                try:
                    module = importlib.import_module(dep_info.import_name)
                    version = self._get_module_version(module, dep_info.import_name)
                    if version:
                        version_info = f" (v{version})"
                except ImportError:
                    version_info = " (not installed)"
                
                report.append(f"  {status} {name}{version_info}")
                report.append(f"    Purpose: {dep_info.purpose}")
                if dep_info.version_constraint:
                    report.append(f"    Required: {dep_info.version_constraint}")
                if dep_info.alternatives:
                    report.append(f"    Alternatives: {', '.join(dep_info.alternatives)}")
                report.append("")
        
        return "\n".join(report)
    
    def get_dependency_info(self, name: str) -> Optional[DependencyInfo]:
        """Get information about a specific dependency."""
        return self.dependencies.get(name)
    
    def list_dependencies(self, dependency_type: Optional[DependencyType] = None) -> List[str]:
        """
        List all dependencies, optionally filtered by type.
        
        Args:
            dependency_type: Optional filter by dependency type
            
        Returns:
            List of dependency names
        """
        if dependency_type is None:
            return list(self.dependencies.keys())
        
        return [
            name for name, dep_info in self.dependencies.items()
            if dep_info.dependency_type == dependency_type
        ]


# Global dependency validator instance
_dependency_validator = DependencyValidator()


def get_dependency_validator() -> DependencyValidator:
    """Get the global dependency validator instance."""
    return _dependency_validator


def validate_startup_dependencies(include_dev: bool = False) -> ValidationResult:
    """
    Validate dependencies at application startup.
    
    Args:
        include_dev: Whether to include development dependencies
        
    Returns:
        ValidationResult with validation details
    """
    return _dependency_validator.validate_all(include_dev=include_dev)


def check_dependency(name: str) -> bool:
    """
    Quick check if a dependency is available.
    
    Args:
        name: Name of the dependency to check
        
    Returns:
        True if dependency is available and valid
    """
    is_valid, _ = _dependency_validator.validate_dependency(name)
    return is_valid