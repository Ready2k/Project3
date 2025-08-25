"""
Lazy loading infrastructure for the AAA system.

This module provides lazy loading capabilities for heavy components and modules,
improving startup time and memory usage.
"""

import time
import threading
from typing import Any, Dict, Callable, Optional, Type, TypeVar, Generic, List
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import importlib
import sys
from functools import wraps

from app.utils.result import Result
from app.utils.error_handler import ErrorHandler, ErrorContext, ErrorCategory


T = TypeVar('T')


class LoadingState(Enum):
    """States for lazy-loaded components."""
    NOT_LOADED = "not_loaded"
    LOADING = "loading"
    LOADED = "loaded"
    FAILED = "failed"


@dataclass
class LoadingMetrics:
    """Metrics for lazy loading performance."""
    load_start_time: float = 0.0
    load_end_time: float = 0.0
    load_duration: float = 0.0
    memory_before: int = 0
    memory_after: int = 0
    success: bool = False
    error_message: Optional[str] = None


@dataclass
class ComponentDescriptor:
    """Describes a lazy-loadable component."""
    component_id: str
    module_path: str
    class_name: Optional[str] = None
    factory_function: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    priority: int = 0  # Higher priority loads first
    cache_result: bool = True
    timeout_seconds: float = 30.0
    
    # Runtime state
    state: LoadingState = LoadingState.NOT_LOADED
    instance: Optional[Any] = None
    metrics: LoadingMetrics = field(default_factory=LoadingMetrics)
    last_access: float = 0.0
    access_count: int = 0


class ILazyLoader(ABC):
    """Interface for lazy loader implementations."""
    
    @abstractmethod
    def register_component(self, descriptor: ComponentDescriptor) -> None:
        """Register a component for lazy loading."""
        pass
    
    @abstractmethod
    def load_component(self, component_id: str) -> Result[Any, Exception]:
        """Load a specific component."""
        pass
    
    @abstractmethod
    def get_component(self, component_id: str) -> Result[Any, Exception]:
        """Get a component, loading it if necessary."""
        pass
    
    @abstractmethod
    def is_loaded(self, component_id: str) -> bool:
        """Check if a component is loaded."""
        pass


class LazyLoader(ILazyLoader):
    """
    Default implementation of lazy loading infrastructure.
    
    Provides on-demand loading of heavy components with caching,
    dependency resolution, and performance monitoring.
    """
    
    def __init__(self, error_handler: ErrorHandler = None):
        """
        Initialize the lazy loader.
        
        Args:
            error_handler: Error handler for loading failures
        """
        self._components: Dict[str, ComponentDescriptor] = {}
        self._loading_locks: Dict[str, threading.Lock] = {}
        self._global_lock = threading.RLock()
        self._error_handler = error_handler or ErrorHandler()
        self._startup_time = time.time()
    
    def register_component(self, descriptor: ComponentDescriptor) -> None:
        """
        Register a component for lazy loading.
        
        Args:
            descriptor: Component descriptor with loading information
        """
        with self._global_lock:
            self._components[descriptor.component_id] = descriptor
            self._loading_locks[descriptor.component_id] = threading.Lock()
    
    def register_module(self, component_id: str, module_path: str, 
                       class_name: str = None, factory_function: str = None,
                       dependencies: List[str] = None, priority: int = 0,
                       cache_result: bool = True, timeout_seconds: float = 30.0) -> None:
        """
        Register a module for lazy loading.
        
        Args:
            component_id: Unique identifier for the component
            module_path: Python module path (e.g., 'app.services.pattern_service')
            class_name: Class name to instantiate from the module
            factory_function: Factory function name to call
            dependencies: List of component IDs this component depends on
            priority: Loading priority (higher loads first)
            cache_result: Whether to cache the loaded instance
            timeout_seconds: Timeout for loading operation
        """
        descriptor = ComponentDescriptor(
            component_id=component_id,
            module_path=module_path,
            class_name=class_name,
            factory_function=factory_function,
            dependencies=dependencies or [],
            priority=priority,
            cache_result=cache_result,
            timeout_seconds=timeout_seconds
        )
        self.register_component(descriptor)
    
    def load_component(self, component_id: str) -> Result[Any, Exception]:
        """
        Load a specific component.
        
        Args:
            component_id: ID of the component to load
            
        Returns:
            Result containing the loaded component or error
        """
        if component_id not in self._components:
            return Result.error(ValueError(f"Component '{component_id}' not registered"))
        
        descriptor = self._components[component_id]
        
        # Check if already loaded and cached
        if descriptor.state == LoadingState.LOADED and descriptor.cache_result and descriptor.instance:
            descriptor.last_access = time.time()
            descriptor.access_count += 1
            return Result.success(descriptor.instance)
        
        # Check if currently loading (prevent circular dependencies)
        if descriptor.state == LoadingState.LOADING:
            return Result.error(RuntimeError(f"Circular dependency detected for component '{component_id}'"))
        
        # Use component-specific lock to prevent concurrent loading
        with self._loading_locks[component_id]:
            # Double-check after acquiring lock
            if descriptor.state == LoadingState.LOADED and descriptor.cache_result and descriptor.instance:
                descriptor.last_access = time.time()
                descriptor.access_count += 1
                return Result.success(descriptor.instance)
            
            return self._load_component_internal(descriptor)
    
    def _load_component_internal(self, descriptor: ComponentDescriptor) -> Result[Any, Exception]:
        """Internal component loading logic."""
        descriptor.state = LoadingState.LOADING
        descriptor.metrics = LoadingMetrics()
        descriptor.metrics.load_start_time = time.time()
        
        try:
            # Load dependencies first
            dependency_instances = []
            for dep_id in descriptor.dependencies:
                dep_result = self.load_component(dep_id)
                if dep_result.is_error:
                    descriptor.state = LoadingState.FAILED
                    descriptor.metrics.error_message = f"Failed to load dependency '{dep_id}': {dep_result.error}"
                    return Result.error(RuntimeError(descriptor.metrics.error_message))
                dependency_instances.append(dep_result.value)
            
            # Import the module
            try:
                module = importlib.import_module(descriptor.module_path)
            except ImportError as e:
                descriptor.state = LoadingState.FAILED
                descriptor.metrics.error_message = f"Failed to import module '{descriptor.module_path}': {e}"
                return Result.error(e)
            
            # Create the component instance
            instance = None
            
            if descriptor.factory_function:
                # Use factory function
                if not hasattr(module, descriptor.factory_function):
                    error_msg = f"Factory function '{descriptor.factory_function}' not found in module '{descriptor.module_path}'"
                    descriptor.state = LoadingState.FAILED
                    descriptor.metrics.error_message = error_msg
                    return Result.error(AttributeError(error_msg))
                
                factory = getattr(module, descriptor.factory_function)
                if dependency_instances:
                    instance = factory(*dependency_instances)
                else:
                    instance = factory()
            
            elif descriptor.class_name:
                # Instantiate class
                if not hasattr(module, descriptor.class_name):
                    error_msg = f"Class '{descriptor.class_name}' not found in module '{descriptor.module_path}'"
                    descriptor.state = LoadingState.FAILED
                    descriptor.metrics.error_message = error_msg
                    return Result.error(AttributeError(error_msg))
                
                cls = getattr(module, descriptor.class_name)
                if dependency_instances:
                    instance = cls(*dependency_instances)
                else:
                    instance = cls()
            
            else:
                # Return the module itself
                instance = module
            
            # Update descriptor
            descriptor.state = LoadingState.LOADED
            descriptor.metrics.load_end_time = time.time()
            descriptor.metrics.load_duration = descriptor.metrics.load_end_time - descriptor.metrics.load_start_time
            descriptor.metrics.success = True
            descriptor.last_access = time.time()
            descriptor.access_count += 1
            
            if descriptor.cache_result:
                descriptor.instance = instance
            
            return Result.success(instance)
            
        except Exception as e:
            descriptor.state = LoadingState.FAILED
            descriptor.metrics.load_end_time = time.time()
            descriptor.metrics.load_duration = descriptor.metrics.load_end_time - descriptor.metrics.load_start_time
            descriptor.metrics.error_message = str(e)
            
            # Log the error
            context = ErrorContext(
                component=descriptor.component_id,
                operation="lazy_load",
                additional_data={
                    "module_path": descriptor.module_path,
                    "class_name": descriptor.class_name,
                    "factory_function": descriptor.factory_function
                }
            )
            self._error_handler.handle_exception(e, context)
            
            return Result.error(e)
    
    def get_component(self, component_id: str) -> Result[Any, Exception]:
        """
        Get a component, loading it if necessary.
        
        Args:
            component_id: ID of the component to get
            
        Returns:
            Result containing the component or error
        """
        return self.load_component(component_id)
    
    def is_loaded(self, component_id: str) -> bool:
        """
        Check if a component is loaded.
        
        Args:
            component_id: ID of the component to check
            
        Returns:
            True if loaded, False otherwise
        """
        if component_id not in self._components:
            return False
        
        return self._components[component_id].state == LoadingState.LOADED
    
    def preload_components(self, component_ids: List[str] = None, 
                          priority_threshold: int = 0) -> Dict[str, Result[Any, Exception]]:
        """
        Preload components based on priority or specific list.
        
        Args:
            component_ids: Specific components to preload (None for all)
            priority_threshold: Minimum priority for preloading
            
        Returns:
            Dictionary mapping component IDs to load results
        """
        if component_ids is None:
            # Load components above priority threshold
            components_to_load = [
                desc for desc in self._components.values()
                if desc.priority >= priority_threshold
            ]
            # Sort by priority (highest first)
            components_to_load.sort(key=lambda x: x.priority, reverse=True)
            component_ids = [desc.component_id for desc in components_to_load]
        
        results = {}
        for component_id in component_ids:
            results[component_id] = self.load_component(component_id)
        
        return results
    
    def unload_component(self, component_id: str) -> None:
        """
        Unload a component and clear its cache.
        
        Args:
            component_id: ID of the component to unload
        """
        if component_id in self._components:
            descriptor = self._components[component_id]
            descriptor.state = LoadingState.NOT_LOADED
            descriptor.instance = None
    
    def get_loading_stats(self) -> Dict[str, Any]:
        """
        Get loading statistics and performance metrics.
        
        Returns:
            Dictionary with loading statistics
        """
        total_components = len(self._components)
        loaded_components = sum(1 for desc in self._components.values() 
                              if desc.state == LoadingState.LOADED)
        failed_components = sum(1 for desc in self._components.values() 
                              if desc.state == LoadingState.FAILED)
        
        total_load_time = sum(desc.metrics.load_duration for desc in self._components.values() 
                            if desc.metrics.success)
        
        avg_load_time = total_load_time / max(loaded_components, 1)
        
        # Component access statistics
        access_stats = {
            desc.component_id: {
                "access_count": desc.access_count,
                "last_access": desc.last_access,
                "load_duration": desc.metrics.load_duration,
                "state": desc.state.value
            }
            for desc in self._components.values()
        }
        
        return {
            "total_components": total_components,
            "loaded_components": loaded_components,
            "failed_components": failed_components,
            "loading_components": total_components - loaded_components - failed_components,
            "total_load_time": total_load_time,
            "average_load_time": avg_load_time,
            "uptime": time.time() - self._startup_time,
            "component_stats": access_stats
        }
    
    def get_component_info(self, component_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a component.
        
        Args:
            component_id: ID of the component
            
        Returns:
            Dictionary with component information or None if not found
        """
        if component_id not in self._components:
            return None
        
        descriptor = self._components[component_id]
        return {
            "component_id": descriptor.component_id,
            "module_path": descriptor.module_path,
            "class_name": descriptor.class_name,
            "factory_function": descriptor.factory_function,
            "dependencies": descriptor.dependencies,
            "priority": descriptor.priority,
            "cache_result": descriptor.cache_result,
            "timeout_seconds": descriptor.timeout_seconds,
            "state": descriptor.state.value,
            "access_count": descriptor.access_count,
            "last_access": descriptor.last_access,
            "metrics": {
                "load_duration": descriptor.metrics.load_duration,
                "success": descriptor.metrics.success,
                "error_message": descriptor.metrics.error_message
            }
        }


# Global lazy loader instance
_global_lazy_loader: Optional[LazyLoader] = None
_loader_lock = threading.Lock()


def get_lazy_loader() -> LazyLoader:
    """
    Get the global lazy loader instance.
    
    Returns:
        The global lazy loader
    """
    global _global_lazy_loader
    
    if _global_lazy_loader is None:
        with _loader_lock:
            if _global_lazy_loader is None:
                _global_lazy_loader = LazyLoader()
    
    return _global_lazy_loader


def lazy_load(component_id: str, module_path: str, class_name: str = None,
              factory_function: str = None, dependencies: List[str] = None,
              priority: int = 0, cache_result: bool = True) -> Callable:
    """
    Decorator for lazy loading components.
    
    Args:
        component_id: Unique identifier for the component
        module_path: Python module path
        class_name: Class name to instantiate
        factory_function: Factory function name
        dependencies: List of dependency component IDs
        priority: Loading priority
        cache_result: Whether to cache the result
        
    Returns:
        Decorator function
    """
    def decorator(func):
        # Register the component
        loader = get_lazy_loader()
        loader.register_module(
            component_id=component_id,
            module_path=module_path,
            class_name=class_name,
            factory_function=factory_function,
            dependencies=dependencies,
            priority=priority,
            cache_result=cache_result
        )
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Load the component and call the original function
            result = loader.get_component(component_id)
            if result.is_error:
                raise result.error
            
            # Call original function with loaded component
            return func(result.value, *args, **kwargs)
        
        return wrapper
    return decorator


def register_component(component_id: str, module_path: str, class_name: str = None,
                      factory_function: str = None, dependencies: List[str] = None,
                      priority: int = 0, cache_result: bool = True) -> None:
    """
    Register a component for lazy loading.
    
    Args:
        component_id: Unique identifier for the component
        module_path: Python module path
        class_name: Class name to instantiate
        factory_function: Factory function name
        dependencies: List of dependency component IDs
        priority: Loading priority
        cache_result: Whether to cache the result
    """
    loader = get_lazy_loader()
    loader.register_module(
        component_id=component_id,
        module_path=module_path,
        class_name=class_name,
        factory_function=factory_function,
        dependencies=dependencies,
        priority=priority,
        cache_result=cache_result
    )


def get_component(component_id: str) -> Result[Any, Exception]:
    """
    Get a component, loading it if necessary.
    
    Args:
        component_id: ID of the component to get
        
    Returns:
        Result containing the component or error
    """
    loader = get_lazy_loader()
    return loader.get_component(component_id)