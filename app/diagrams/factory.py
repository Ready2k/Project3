"""
Diagram Service Factory

This module provides a factory for creating diagram service instances with:
- Feature availability checking based on dependencies
- Graceful fallback to basic diagram functionality
- Configuration-based service selection
- Service registry integration
"""

from typing import Any, Dict, List, Optional, Protocol
import logging
from enum import Enum
from dataclasses import dataclass

from app.utils.imports import optional_service

from app.core.service import ConfigurableService
from app.core.types import Result, Success, Error
from app.utils.imports import ImportManager


class DiagramType(Enum):
    """Supported diagram types."""
    MERMAID = "mermaid"
    INFRASTRUCTURE = "infrastructure"
    DRAWIO = "drawio"


class DiagramServiceProtocol(Protocol):
    """Protocol for diagram services."""
    
    def is_available(self) -> bool:
        """Check if the service is available."""
        ...
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported output formats."""
        ...
    
    def health_check(self) -> bool:
        """Check service health."""
        ...


class MermaidServiceProtocol(DiagramServiceProtocol, Protocol):
    """Protocol for Mermaid diagram services."""
    
    async def generate_diagram(self, prompt: str, provider_config: Dict[str, Any], **kwargs) -> str:
        """Generate Mermaid diagram code from prompt."""
        ...
    
    def render_diagram(self, mermaid_code: str, height: int = 400) -> None:
        """Render Mermaid diagram in UI."""
        ...
    
    def validate_syntax(self, mermaid_code: str) -> tuple[bool, str]:
        """Validate Mermaid syntax."""
        ...


class InfrastructureServiceProtocol(DiagramServiceProtocol, Protocol):
    """Protocol for Infrastructure diagram services."""
    
    def generate_diagram(self, diagram_spec: Dict[str, Any], output_path: str, format: str = "png") -> tuple[str, str]:
        """Generate infrastructure diagram from specification."""
        ...
    
    def create_sample_spec(self) -> Dict[str, Any]:
        """Create a sample infrastructure specification."""
        ...


class DrawIOServiceProtocol(DiagramServiceProtocol, Protocol):
    """Protocol for Draw.io export services."""
    
    def export_mermaid_diagram(self, mermaid_code: str, diagram_title: str, output_path: str) -> str:
        """Export Mermaid diagram to Draw.io format."""
        ...
    
    def export_infrastructure_diagram(self, infrastructure_spec: Dict[str, Any], diagram_title: str, output_path: str) -> str:
        """Export Infrastructure diagram to Draw.io format."""
        ...
    
    def export_multiple_formats(self, diagram_data: Dict[str, Any], diagram_title: str, output_path: str) -> List[str]:
        """Export diagram in multiple formats."""
        ...


@dataclass
class DiagramServiceInfo:
    """Information about a diagram service."""
    name: str
    diagram_type: DiagramType
    class_path: str
    dependencies: List[str]
    required_packages: List[str]
    optional_packages: List[str]
    fallback_available: bool
    is_available: bool = False
    error_message: Optional[str] = None
    features: List[str] = None
    
    def __post_init__(self):
        if self.features is None:
            self.features = []


class BasicDiagramService:
    """Basic fallback diagram service with minimal functionality."""
    
    def __init__(self, logger: Optional[Any] = None):
        self._logger = logger or logging.getLogger(__name__)
    
    def is_available(self) -> bool:
        """Basic service is always available."""
        return True
    
    def get_supported_formats(self) -> List[str]:
        """Basic service supports text output only."""
        return ["text"]
    
    def health_check(self) -> bool:
        """Basic service is always healthy."""
        return True
    
    def generate_basic_text_diagram(self, description: str) -> str:
        """Generate a basic text representation of a diagram."""
        return f"""
Basic Text Diagram
==================

Description: {description}

Note: This is a fallback text representation.
For full diagram functionality, please install the required dependencies:
- For Mermaid diagrams: streamlit-mermaid
- For Infrastructure diagrams: diagrams, graphviz
- For Draw.io export: No additional dependencies required

To install dependencies:
pip install streamlit-mermaid diagrams

For Graphviz (required for infrastructure diagrams):
- Windows: choco install graphviz OR winget install graphviz
- macOS: brew install graphviz
- Linux: sudo apt-get install graphviz
"""


class MermaidServiceAdapter:
    """Adapter for MermaidDiagramGenerator to implement the protocol."""
    
    def __init__(self, mermaid_generator):
        self._generator = mermaid_generator
        self._logger = logging.getLogger(__name__)
    
    def is_available(self) -> bool:
        """Check if Mermaid service is available."""
        return True  # MermaidDiagramGenerator is always available
    
    def get_supported_formats(self) -> List[str]:
        """Get supported formats for Mermaid diagrams."""
        return ["mermaid", "html", "svg", "png"]
    
    def health_check(self) -> bool:
        """Check Mermaid service health."""
        return True
    
    async def generate_diagram(self, prompt: str, provider_config: Dict[str, Any], **kwargs) -> str:
        """Generate Mermaid diagram code from prompt."""
        return await self._generator.make_llm_request(prompt, provider_config, **kwargs)
    
    def render_diagram(self, mermaid_code: str, height: int = 400) -> None:
        """Render Mermaid diagram in UI."""
        return self._generator.render_mermaid_diagram(mermaid_code, height)
    
    def validate_syntax(self, mermaid_code: str) -> tuple[bool, str]:
        """Validate Mermaid syntax."""
        return self._generator.validate_mermaid_syntax(mermaid_code)


class InfrastructureServiceAdapter:
    """Adapter for InfrastructureDiagramGenerator to implement the protocol."""
    
    def __init__(self, infra_generator):
        self._generator = infra_generator
        self._logger = logging.getLogger(__name__)
    
    def is_available(self) -> bool:
        """Check if Infrastructure service is available."""
        # Check through service registry
        diagram_service = optional_service('diagram_service', context='InfrastructureService')
        return diagram_service is not None
    
    def get_supported_formats(self) -> List[str]:
        """Get supported formats for Infrastructure diagrams."""
        return ["png", "svg", "pdf", "json"]
    
    def health_check(self) -> bool:
        """Check Infrastructure service health."""
        return self.is_available()
    
    def generate_diagram(self, diagram_spec: Dict[str, Any], output_path: str, format: str = "png") -> tuple[str, str]:
        """Generate infrastructure diagram from specification."""
        return self._generator.generate_diagram(diagram_spec, output_path, format)
    
    def create_sample_spec(self) -> Dict[str, Any]:
        """Create a sample infrastructure specification."""
        from app.diagrams.infrastructure import create_sample_infrastructure_spec
        return create_sample_infrastructure_spec()


class DrawIOServiceAdapter:
    """Adapter for DrawIOExporter to implement the protocol."""
    
    def __init__(self, drawio_exporter):
        self._exporter = drawio_exporter
        self._logger = logging.getLogger(__name__)
    
    def is_available(self) -> bool:
        """Check if Draw.io service is available."""
        return True  # DrawIOExporter is pure Python
    
    def get_supported_formats(self) -> List[str]:
        """Get supported formats for Draw.io export."""
        return ["drawio", "xml", "json", "mmd"]
    
    def health_check(self) -> bool:
        """Check Draw.io service health."""
        return True
    
    def export_mermaid_diagram(self, mermaid_code: str, diagram_title: str, output_path: str) -> str:
        """Export Mermaid diagram to Draw.io format."""
        return self._exporter.export_mermaid_diagram(mermaid_code, diagram_title, output_path)
    
    def export_infrastructure_diagram(self, infrastructure_spec: Dict[str, Any], diagram_title: str, output_path: str) -> str:
        """Export Infrastructure diagram to Draw.io format."""
        return self._exporter.export_infrastructure_diagram(infrastructure_spec, diagram_title, output_path)
    
    def export_multiple_formats(self, diagram_data: Dict[str, Any], diagram_title: str, output_path: str) -> List[str]:
        """Export diagram in multiple formats."""
        return self._exporter.export_multiple_formats(diagram_data, diagram_title, output_path)


class DiagramServiceFactory(ConfigurableService):
    """
    Factory for creating diagram service instances.
    
    Handles feature availability checking, graceful fallback,
    and configuration-based service selection.
    """
    
    def __init__(self, config: Dict[str, Any], logger: Optional[Any] = None):
        """
        Initialize the diagram service factory.
        
        Args:
            config: Factory configuration
            logger: Logger instance (optional)
        """
        super().__init__(config, "diagram_service_factory")
        self._logger = logger or logging.getLogger(__name__)
        self._import_manager = ImportManager()
        self._services: Dict[str, DiagramServiceInfo] = {}
        self._service_instances: Dict[str, Any] = {}
        self._availability_checked = False
        
        # Initialize service definitions
        self._initialize_service_definitions()
    
    def _do_initialize(self) -> None:
        """Initialize the factory and check service availability."""
        self._logger.info("Initializing Diagram Service Factory")
        
        # Check availability of all services
        self._check_service_availability()
        
        # Log available services
        available_services = [name for name, info in self._services.items() if info.is_available]
        self._logger.info(f"Available diagram services: {available_services}")
        
        if not available_services:
            self._logger.warning("No diagram services are fully available, fallback mode will be used")
    
    def _do_shutdown(self) -> None:
        """Shutdown the factory and clean up service instances."""
        self._logger.info("Shutting down Diagram Service Factory")
        
        # Shutdown any service instances that support it
        for service_name, service in self._service_instances.items():
            try:
                if hasattr(service, 'shutdown'):
                    service.shutdown()
                    self._logger.debug(f"Shutdown service: {service_name}")
            except Exception as e:
                self._logger.error(f"Error shutting down service {service_name}: {e}")
        
        self._service_instances.clear()
    
    def _do_health_check(self) -> bool:
        """Check if at least one service is available."""
        if not self._availability_checked:
            self._check_service_availability()
        
        available_count = sum(1 for info in self._services.values() if info.is_available)
        return available_count > 0 or True  # Always healthy due to fallback
    
    def _initialize_service_definitions(self) -> None:
        """Initialize the definitions of all supported diagram services."""
        self._services = {
            "mermaid": DiagramServiceInfo(
                name="mermaid",
                diagram_type=DiagramType.MERMAID,
                class_path="app.ui.mermaid_diagrams.MermaidDiagramGenerator",
                dependencies=["logger", "config"],
                required_packages=[],  # Core functionality doesn't require external packages
                optional_packages=["streamlit-mermaid"],
                fallback_available=True,
                features=["generation", "validation", "rendering", "export"]
            ),
            "infrastructure": DiagramServiceInfo(
                name="infrastructure",
                diagram_type=DiagramType.INFRASTRUCTURE,
                class_path="app.diagrams.infrastructure.InfrastructureDiagramGenerator",
                dependencies=[],
                required_packages=["diagrams"],
                optional_packages=["graphviz"],
                fallback_available=True,
                features=["generation", "aws", "gcp", "azure", "k8s", "onprem", "export"]
            ),
            "drawio": DiagramServiceInfo(
                name="drawio",
                diagram_type=DiagramType.DRAWIO,
                class_path="app.exporters.drawio_exporter.DrawIOExporter",
                dependencies=["logger"],
                required_packages=[],  # Pure Python implementation
                optional_packages=[],
                fallback_available=True,
                features=["export", "mermaid_export", "infrastructure_export", "xml_generation"]
            )
        }
    
    def _check_service_availability(self) -> None:
        """Check availability of all diagram services."""
        self._logger.debug("Checking diagram service availability")
        
        # Clear any cached failed imports to allow retry
        self._import_manager.clear_failed_imports()
        
        for service_name, service_info in self._services.items():
            try:
                # Check if required packages are available
                missing_packages = []
                for package in service_info.required_packages:
                    if not self._import_manager.safe_import(package):
                        missing_packages.append(package)
                
                if missing_packages:
                    service_info.is_available = False
                    service_info.error_message = f"Missing required packages: {missing_packages}"
                    self._logger.debug(f"Service {service_name} missing packages: {missing_packages}")
                    continue
                
                # Check optional packages and note missing ones
                missing_optional = []
                for package in service_info.optional_packages:
                    if not self._import_manager.safe_import(package):
                        missing_optional.append(package)
                
                if missing_optional:
                    self._logger.debug(f"Service {service_name} missing optional packages: {missing_optional}")
                    # Still available but with reduced functionality
                
                # Try to import the service class
                module_path, class_name = service_info.class_path.rsplit(".", 1)
                service_module = self._import_manager.safe_import(module_path)
                if not service_module:
                    service_info.is_available = False
                    service_info.error_message = f"Could not import service module: {module_path}"
                    continue
                
                service_class = getattr(service_module, class_name, None)
                if not service_class:
                    service_info.is_available = False
                    service_info.error_message = f"Could not find service class: {class_name}"
                    continue
                
                # If we get here, service is available
                service_info.is_available = True
                service_info.error_message = None
                self._logger.debug(f"Service {service_name} is available")
                
            except Exception as e:
                service_info.is_available = False
                service_info.error_message = f"Availability check failed: {e}"
                self._logger.debug(f"Service {service_name} is not available: {e}")
        
        self._availability_checked = True
    
    def get_available_services(self) -> List[str]:
        """
        Get list of available service names.
        
        Returns:
            List of available service names
        """
        if not self._availability_checked:
            self._check_service_availability()
        
        return [name for name, info in self._services.items() if info.is_available]
    
    def is_service_available(self, service_name: str) -> bool:
        """
        Check if a specific service is available.
        
        Args:
            service_name: Name of the service to check
            
        Returns:
            True if service is available, False otherwise
        """
        if not self._availability_checked:
            self._check_service_availability()
        
        service_info = self._services.get(service_name)
        return service_info.is_available if service_info else False
    
    def get_service_info(self, service_name: str) -> Optional[DiagramServiceInfo]:
        """
        Get information about a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            DiagramServiceInfo if service exists, None otherwise
        """
        return self._services.get(service_name)
    
    def create_mermaid_service(self, **kwargs) -> Result[MermaidServiceProtocol, str]:
        """
        Create a Mermaid diagram service instance.
        
        Args:
            **kwargs: Additional configuration for the service
            
        Returns:
            Result containing MermaidServiceProtocol instance or error message
        """
        return self._create_service("mermaid", **kwargs)
    
    def create_infrastructure_service(self, **kwargs) -> Result[InfrastructureServiceProtocol, str]:
        """
        Create an Infrastructure diagram service instance.
        
        Args:
            **kwargs: Additional configuration for the service
            
        Returns:
            Result containing InfrastructureServiceProtocol instance or error message
        """
        return self._create_service("infrastructure", **kwargs)
    
    def create_drawio_service(self, **kwargs) -> Result[DrawIOServiceProtocol, str]:
        """
        Create a Draw.io export service instance.
        
        Args:
            **kwargs: Additional configuration for the service
            
        Returns:
            Result containing DrawIOServiceProtocol instance or error message
        """
        return self._create_service("drawio", **kwargs)
    
    def create_service(self, service_name: str, **kwargs) -> Result[DiagramServiceProtocol, str]:
        """
        Create a diagram service instance.
        
        Args:
            service_name: Name of the service to create
            **kwargs: Additional configuration for the service
            
        Returns:
            Result containing DiagramServiceProtocol instance or error message
        """
        return self._create_service(service_name, **kwargs)
    
    def create_service_with_fallback(self, service_name: str, **kwargs) -> Result[DiagramServiceProtocol, str]:
        """
        Create a diagram service with automatic fallback to basic functionality.
        
        Args:
            service_name: Name of the service to create
            **kwargs: Additional configuration for the service
            
        Returns:
            Result containing DiagramServiceProtocol instance or error message
        """
        # Try to create the requested service
        result = self._create_service(service_name, **kwargs)
        if result.is_success():
            return result
        
        # Check if fallback is available for this service
        service_info = self._services.get(service_name)
        if service_info and service_info.fallback_available:
            self._logger.warning(f"Service {service_name} failed, using basic fallback")
            basic_service = BasicDiagramService(self._logger)
            return Success(basic_service)
        
        return result
    
    def _create_service(self, service_name: str, **kwargs) -> Result[Any, str]:
        """
        Create an instance of the specified service.
        
        Args:
            service_name: Name of the service to create
            **kwargs: Additional configuration for the service
            
        Returns:
            Result containing service instance or error message
        """
        # Check if we already have an instance (for singleton behavior)
        cache_key = f"{service_name}_{hash(frozenset(kwargs.items()))}"
        if cache_key in self._service_instances:
            return Success(self._service_instances[cache_key])
        
        # Check if service is available
        if not self.is_service_available(service_name):
            service_info = self._services.get(service_name)
            error_msg = f"Service {service_name} is not available"
            if service_info and service_info.error_message:
                error_msg += f": {service_info.error_message}"
            return Error(error_msg)
        
        # Create new service instance
        try:
            service_instance = self._create_service_instance(service_name, **kwargs)
            
            # Cache the instance
            self._service_instances[cache_key] = service_instance
            
            self._logger.info(f"Created diagram service: {service_name}")
            return Success(service_instance)
            
        except Exception as e:
            error_msg = f"Failed to create service {service_name}: {e}"
            self._logger.error(error_msg)
            return Error(error_msg)
    
    def _create_service_instance(self, service_name: str, **kwargs) -> Any:
        """
        Create an instance of the specified service.
        
        Args:
            service_name: Name of the service to create
            **kwargs: Additional configuration for the service
            
        Returns:
            Service instance
            
        Raises:
            Exception: If service creation fails
        """
        service_info = self._services.get(service_name)
        if not service_info:
            raise ValueError(f"Unknown service: {service_name}")
        
        if not service_info.is_available:
            raise RuntimeError(f"Service {service_name} is not available: {service_info.error_message}")
        
        # Import the service class
        module_path, class_name = service_info.class_path.rsplit(".", 1)
        service_module = self._import_manager.safe_import(module_path)
        if not service_module:
            raise ImportError(f"Could not import service module: {module_path}")
        
        service_class = getattr(service_module, class_name)
        if not service_class:
            raise ImportError(f"Could not find service class: {class_name}")
        
        # Prepare service configuration
        service_config = self._prepare_service_config(service_name, **kwargs)
        
        # Create service instance based on service type
        try:
            if service_name == "mermaid":
                # Create MermaidDiagramGenerator and wrap it with adapter
                mermaid_generator = service_class()
                return MermaidServiceAdapter(mermaid_generator)
            elif service_name == "infrastructure":
                # Create InfrastructureDiagramGenerator and wrap it with adapter
                infra_generator = service_class()
                return InfrastructureServiceAdapter(infra_generator)
            elif service_name == "drawio":
                # Create DrawIOExporter and wrap it with adapter
                drawio_exporter = service_class()
                return DrawIOServiceAdapter(drawio_exporter)
            else:
                # Generic instantiation with config
                return service_class(**service_config)
                
        except Exception as e:
            raise RuntimeError(f"Failed to instantiate service {service_name}: {e}") from e
    
    def _prepare_service_config(self, service_name: str, **kwargs) -> Dict[str, Any]:
        """
        Prepare configuration for a service instance.
        
        Args:
            service_name: Name of the service
            **kwargs: Additional configuration
            
        Returns:
            Configuration dictionary for the service
        """
        # Start with factory configuration
        config = self.config.copy()
        
        # Add service-specific configuration
        service_config_key = f"{service_name}_config"
        if service_config_key in config:
            config.update(config[service_config_key])
        
        # Override with any provided kwargs
        config.update(kwargs)
        
        return config
    
    def get_service_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status information for all services.
        
        Returns:
            Dictionary mapping service names to their status information
        """
        if not self._availability_checked:
            self._check_service_availability()
        
        status = {}
        for service_name, service_info in self._services.items():
            status[service_name] = {
                "available": service_info.is_available,
                "error_message": service_info.error_message,
                "diagram_type": service_info.diagram_type.value,
                "required_packages": service_info.required_packages,
                "optional_packages": service_info.optional_packages,
                "fallback_available": service_info.fallback_available,
                "features": service_info.features,
                "has_instance": any(service_name in key for key in self._service_instances.keys())
            }
        
        return status
    
    def get_installation_instructions(self) -> Dict[str, str]:
        """
        Get installation instructions for missing dependencies.
        
        Returns:
            Dictionary mapping service names to installation instructions
        """
        if not self._availability_checked:
            self._check_service_availability()
        
        instructions = {}
        
        for service_name, service_info in self._services.items():
            if not service_info.is_available and service_info.error_message:
                if "Missing required packages" in service_info.error_message:
                    if service_name == "infrastructure":
                        instructions[service_name] = """
To enable Infrastructure diagrams:
1. Install Python package: pip install diagrams
2. Install Graphviz:
   • Windows: choco install graphviz OR winget install graphviz
   • macOS: brew install graphviz
   • Linux: sudo apt-get install graphviz
3. Restart the application
"""
                    elif service_name == "mermaid":
                        instructions[service_name] = """
To enable enhanced Mermaid diagrams:
1. Install Python package: pip install streamlit-mermaid
2. Restart the application

Note: Basic Mermaid functionality is available without this package.
"""
                    else:
                        missing_packages = service_info.required_packages
                        instructions[service_name] = f"""
To enable {service_name} service:
1. Install required packages: pip install {' '.join(missing_packages)}
2. Restart the application
"""
        
        return instructions
    
    @property
    def dependencies(self) -> List[str]:
        """Factory dependencies."""
        return ["config", "logger"]