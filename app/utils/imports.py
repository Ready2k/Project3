"""
Safe Import Utilities for Dependency Management

This module provides safe import utilities and service resolution functionality:
- ImportManager class for managing safe imports
- Service requirement and optional service patterns
- Proper error handling for import failures
- Integration with the service registry
"""

from typing import Any, Optional, Type, TypeVar, Callable, Dict, List
import importlib
import logging
from app.core.registry import get_registry, ServiceNotFoundError

T = TypeVar('T')

logger = logging.getLogger(__name__)


class ServiceRequiredError(Exception):
    """Raised when a required service is not available."""
    
    def __init__(self, service_name: str, message: Optional[str] = None):
        """
        Initialize ServiceRequiredError.
        
        Args:
            service_name: Name of the required service
            message: Optional custom error message
        """
        self.service_name = service_name
        if message is None:
            message = f"Required service '{service_name}' is not available"
        super().__init__(message)


class ImportError(Exception):
    """Custom import error with additional context."""
    
    def __init__(self, module_name: str, original_error: Exception, context: Optional[str] = None):
        """
        Initialize ImportError.
        
        Args:
            module_name: Name of the module that failed to import
            original_error: Original import exception
            context: Optional context about where the import was attempted
        """
        self.module_name = module_name
        self.original_error = original_error
        self.context = context
        
        message = f"Failed to import '{module_name}': {original_error}"
        if context:
            message = f"{message} (Context: {context})"
        
        super().__init__(message)


class ImportManager:
    """
    Manages safe imports and service resolution.
    
    Provides utilities for safely importing modules and resolving services
    through the service registry with proper error handling and logging.
    """
    
    def __init__(self):
        """Initialize the ImportManager."""
        self._registry = None  # Lazy initialization to avoid circular imports
        self._import_cache: Dict[str, Any] = {}
        self._failed_imports: Dict[str, Exception] = {}
        self._logger = logging.getLogger(f"{__name__}.ImportManager")
    
    @property
    def registry(self):
        """Get the registry instance (lazy initialization)."""
        if self._registry is None:
            self._registry = get_registry()
        return self._registry
    
    def safe_import(
        self, 
        module_name: str, 
        class_name: Optional[str] = None,
        context: Optional[str] = None,
        cache: bool = True
    ) -> Optional[Any]:
        """
        Safely import a module or class with proper error handling.
        
        Args:
            module_name: Name of the module to import
            class_name: Optional class name to extract from module
            context: Optional context for error reporting
            cache: Whether to cache successful imports
            
        Returns:
            Imported module or class, None if import fails
        """
        cache_key = f"{module_name}.{class_name}" if class_name else module_name
        
        # Check cache first
        if cache and cache_key in self._import_cache:
            self._logger.debug(f"Returning cached import: {cache_key}")
            return self._import_cache[cache_key]
        
        # Check if we've already failed to import this
        if cache_key in self._failed_imports:
            self._logger.debug(f"Skipping previously failed import: {cache_key}")
            return None
        
        try:
            self._logger.debug(f"Attempting to import: {module_name}")
            module = importlib.import_module(module_name)
            
            result = module
            if class_name:
                if hasattr(module, class_name):
                    result = getattr(module, class_name)
                    self._logger.debug(f"Successfully imported class: {module_name}.{class_name}")
                else:
                    error_msg = f"Class '{class_name}' not found in module '{module_name}'"
                    self._logger.warning(error_msg)
                    if cache:
                        self._failed_imports[cache_key] = AttributeError(error_msg)
                    return None
            else:
                self._logger.debug(f"Successfully imported module: {module_name}")
            
            # Cache successful import
            if cache:
                self._import_cache[cache_key] = result
            
            return result
            
        except ImportError as e:
            error_msg = f"Failed to import {module_name}"
            if context:
                error_msg += f" (Context: {context})"
            
            self._logger.info(f"{error_msg}: {e}")
            
            # Cache the failure to avoid repeated attempts
            if cache:
                self._failed_imports[cache_key] = ImportError(module_name, e, context)
            
            return None
        except Exception as e:
            error_msg = f"Unexpected error importing {module_name}"
            if context:
                error_msg += f" (Context: {context})"
            
            self._logger.error(f"{error_msg}: {e}")
            
            # Cache the failure
            if cache:
                self._failed_imports[cache_key] = ImportError(module_name, e, context)
            
            return None
    
    def require_service(self, service_name: str, context: Optional[str] = None) -> Any:
        """
        Require a service from the registry.
        
        Args:
            service_name: Name of the required service
            context: Optional context for error reporting
            
        Returns:
            Service instance
            
        Raises:
            ServiceRequiredError: If service is not available
        """
        try:
            if not self.registry.has(service_name):
                error_msg = f"Required service '{service_name}' is not registered"
                if context:
                    error_msg += f" (Context: {context})"
                
                self._logger.error(error_msg)
                raise ServiceRequiredError(service_name, error_msg)
            
            service = self.registry.get(service_name)
            self._logger.debug(f"Successfully resolved required service: {service_name}")
            return service
            
        except ServiceNotFoundError as e:
            error_msg = f"Required service '{service_name}' could not be resolved: {e}"
            if context:
                error_msg += f" (Context: {context})"
            
            self._logger.error(error_msg)
            raise ServiceRequiredError(service_name, error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error resolving required service '{service_name}': {e}"
            if context:
                error_msg += f" (Context: {context})"
            
            self._logger.error(error_msg)
            raise ServiceRequiredError(service_name, error_msg) from e
    
    def optional_service(
        self, 
        service_name: str, 
        default: Any = None, 
        context: Optional[str] = None
    ) -> Any:
        """
        Get an optional service with fallback.
        
        Args:
            service_name: Name of the optional service
            default: Default value if service is not available
            context: Optional context for logging
            
        Returns:
            Service instance or default value
        """
        try:
            if self.registry.has(service_name):
                service = self.registry.get(service_name)
                self._logger.debug(f"Successfully resolved optional service: {service_name}")
                return service
            else:
                log_msg = f"Optional service '{service_name}' not available, using default"
                if context:
                    log_msg += f" (Context: {context})"
                
                self._logger.debug(log_msg)
                return default
                
        except Exception as e:
            log_msg = f"Error resolving optional service '{service_name}', using default: {e}"
            if context:
                log_msg += f" (Context: {context})"
            
            self._logger.warning(log_msg)
            return default
    
    def try_import_service(
        self, 
        module_name: str, 
        service_name: str,
        class_name: Optional[str] = None,
        factory_args: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None
    ) -> bool:
        """
        Try to import a module and register it as a service.
        
        Args:
            module_name: Name of the module to import
            service_name: Name to register the service under
            class_name: Optional class name to extract from module
            factory_args: Optional arguments for service factory
            context: Optional context for error reporting
            
        Returns:
            True if import and registration succeeded, False otherwise
        """
        try:
            imported = self.safe_import(module_name, class_name, context)
            if imported is None:
                return False
            
            # Register as a factory if it's a class, otherwise as singleton
            if class_name and hasattr(imported, '__call__'):
                # It's a class, register as factory
                def factory():
                    if factory_args:
                        return imported(**factory_args)
                    return imported()
                
                self.registry.register_factory(service_name, factory)
                self._logger.info(f"Registered service factory: {service_name} from {module_name}.{class_name}")
            else:
                # It's a module or instance, register as singleton
                self.registry.register_singleton(service_name, imported)
                self._logger.info(f"Registered service singleton: {service_name} from {module_name}")
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to import and register service '{service_name}' from '{module_name}': {e}"
            if context:
                error_msg += f" (Context: {context})"
            
            self._logger.error(error_msg)
            return False
    
    def get_import_status(self) -> Dict[str, Any]:
        """
        Get status of all import attempts.
        
        Returns:
            Dictionary with import status information
        """
        return {
            "successful_imports": list(self._import_cache.keys()),
            "failed_imports": {
                key: str(error) for key, error in self._failed_imports.items()
            },
            "cache_size": len(self._import_cache),
            "failed_count": len(self._failed_imports)
        }
    
    def clear_cache(self) -> None:
        """Clear the import cache."""
        self._import_cache.clear()
        self._failed_imports.clear()
        self._logger.debug("Import cache cleared")
    
    def clear_failed_imports(self) -> None:
        """Clear only the failed imports cache to allow retry."""
        self._failed_imports.clear()
        self._logger.debug("Failed imports cache cleared")
    
    def is_available(self, module_name: str, class_name: Optional[str] = None) -> bool:
        """
        Check if a module/class is available for import.
        
        Args:
            module_name: Name of the module to check
            class_name: Optional class name to check
            
        Returns:
            True if module/class is available, False otherwise
        """
        cache_key = f"{module_name}.{class_name}" if class_name else module_name
        
        # Check cache first
        if cache_key in self._import_cache:
            return True
        
        if cache_key in self._failed_imports:
            return False
        
        # Try the import without caching
        result = self.safe_import(module_name, class_name, cache=False)
        return result is not None


# Global import manager instance
_import_manager: Optional[ImportManager] = None


def get_import_manager() -> ImportManager:
    """
    Get the global import manager instance.
    
    Returns:
        Global ImportManager instance
    """
    global _import_manager
    if _import_manager is None:
        _import_manager = ImportManager()
    return _import_manager


def reset_import_manager() -> None:
    """Reset the global import manager (primarily for testing)."""
    global _import_manager
    _import_manager = None


# Convenience functions for common operations

def safe_import(
    module_name: str, 
    class_name: Optional[str] = None,
    context: Optional[str] = None
) -> Optional[Any]:
    """
    Safely import a module or class.
    
    Args:
        module_name: Name of the module to import
        class_name: Optional class name to extract from module
        context: Optional context for error reporting
        
    Returns:
        Imported module or class, None if import fails
    """
    return get_import_manager().safe_import(module_name, class_name, context)


def require_service(service_name: str, context: Optional[str] = None) -> Any:
    """
    Require a service from the registry.
    
    Args:
        service_name: Name of the required service
        context: Optional context for error reporting
        
    Returns:
        Service instance
        
    Raises:
        ServiceRequiredError: If service is not available
    """
    return get_import_manager().require_service(service_name, context)


def optional_service(
    service_name: str, 
    default: Any = None, 
    context: Optional[str] = None
) -> Any:
    """
    Get an optional service with fallback.
    
    Args:
        service_name: Name of the optional service
        default: Default value if service is not available
        context: Optional context for logging
        
    Returns:
        Service instance or default value
    """
    return get_import_manager().optional_service(service_name, default, context)


def is_available(module_name: str, class_name: Optional[str] = None) -> bool:
    """
    Check if a module/class is available for import.
    
    Args:
        module_name: Name of the module to check
        class_name: Optional class name to check
        
    Returns:
        True if module/class is available, False otherwise
    """
    return get_import_manager().is_available(module_name, class_name)


def try_import_service(
    module_name: str, 
    service_name: str,
    class_name: Optional[str] = None,
    factory_args: Optional[Dict[str, Any]] = None,
    context: Optional[str] = None
) -> bool:
    """
    Try to import a module and register it as a service.
    
    Args:
        module_name: Name of the module to import
        service_name: Name to register the service under
        class_name: Optional class name to extract from module
        factory_args: Optional arguments for service factory
        context: Optional context for error reporting
        
    Returns:
        True if import and registration succeeded, False otherwise
    """
    return get_import_manager().try_import_service(
        module_name, service_name, class_name, factory_args, context
    )


# Utility functions for common import patterns

def import_optional_dependency(
    module_name: str,
    class_name: Optional[str] = None,
    feature_name: Optional[str] = None
) -> Optional[Any]:
    """
    Import an optional dependency with user-friendly error handling.
    
    Args:
        module_name: Name of the module to import
        class_name: Optional class name to extract
        feature_name: Optional feature name for error messages
        
    Returns:
        Imported module/class or None if not available
    """
    feature_desc = feature_name or f"{module_name} functionality"
    context = f"Optional dependency for {feature_desc}"
    
    result = safe_import(module_name, class_name, context)
    
    if result is None:
        logger.info(f"{feature_desc} is not available (missing {module_name})")
    else:
        logger.debug(f"{feature_desc} is available")
    
    return result


def require_dependency(
    module_name: str,
    class_name: Optional[str] = None,
    feature_name: Optional[str] = None,
    installation_hint: Optional[str] = None
) -> Any:
    """
    Import a required dependency with detailed error messages.
    
    Args:
        module_name: Name of the module to import
        class_name: Optional class name to extract
        feature_name: Optional feature name for error messages
        installation_hint: Optional installation instructions
        
    Returns:
        Imported module/class
        
    Raises:
        ImportError: If dependency is not available
    """
    feature_desc = feature_name or f"{module_name} functionality"
    context = f"Required dependency for {feature_desc}"
    
    result = safe_import(module_name, class_name, context)
    
    if result is None:
        error_msg = f"Required dependency '{module_name}' is not available for {feature_desc}"
        
        if installation_hint:
            error_msg += f"\n\nInstallation: {installation_hint}"
        else:
            error_msg += f"\n\nInstall with: pip install {module_name}"
        
        raise ImportError(module_name, Exception(error_msg), context)
    
    return result


def create_fallback_service(
    primary_service: str,
    fallback_service: str,
    context: Optional[str] = None
) -> Any:
    """
    Create a service with fallback to another service.
    
    Args:
        primary_service: Name of the primary service to try
        fallback_service: Name of the fallback service
        context: Optional context for logging
        
    Returns:
        Primary service if available, otherwise fallback service
        
    Raises:
        ServiceRequiredError: If neither service is available
    """
    import_manager = get_import_manager()
    
    # Try primary service first
    primary = import_manager.optional_service(primary_service, context=context)
    if primary is not None:
        logger.debug(f"Using primary service: {primary_service}")
        return primary
    
    # Fall back to secondary service
    fallback = import_manager.optional_service(fallback_service, context=context)
    if fallback is not None:
        logger.info(f"Primary service '{primary_service}' not available, using fallback: {fallback_service}")
        return fallback
    
    # Neither service available
    error_msg = f"Neither primary service '{primary_service}' nor fallback service '{fallback_service}' is available"
    if context:
        error_msg += f" (Context: {context})"
    
    raise ServiceRequiredError(primary_service, error_msg)