"""
Import optimization utilities for reducing startup time.

This module provides utilities for optimizing imports and reducing
application startup time through lazy loading and import management.
"""

import sys
import time
import importlib
from typing import Any, Dict, List, Optional, Set, Callable
from functools import wraps
from dataclasses import dataclass
import threading

from app.utils.logger import app_logger


@dataclass
class ImportMetrics:
    """Metrics for import performance."""
    module_name: str
    import_time: float
    size_bytes: int
    dependencies: List[str]
    first_import: bool = True


class ImportOptimizer:
    """
    Import optimization manager for reducing startup time.
    
    Tracks import performance and provides lazy loading capabilities
    for heavy modules.
    """
    
    def __init__(self):
        self._import_metrics: Dict[str, ImportMetrics] = {}
        self._lazy_modules: Dict[str, Any] = {}
        self._import_hooks: List[Callable] = []
        self._lock = threading.RLock()
        self._startup_time = time.time()
    
    def track_import(self, module_name: str) -> Callable:
        """
        Decorator to track import performance.
        
        Args:
            module_name: Name of the module being imported
            
        Returns:
            Decorator function
        """
        def decorator(import_func: Callable) -> Callable:
            @wraps(import_func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = import_func(*args, **kwargs)
                    import_time = time.time() - start_time
                    
                    # Calculate module size (approximate)
                    size_bytes = 0
                    if hasattr(result, '__file__') and result.__file__:
                        try:
                            import os
                            size_bytes = os.path.getsize(result.__file__)
                        except (OSError, AttributeError):
                            pass
                    
                    # Get dependencies
                    dependencies = []
                    if hasattr(result, '__dict__'):
                        for attr_name in dir(result):
                            attr = getattr(result, attr_name, None)
                            if hasattr(attr, '__module__') and attr.__module__ != module_name:
                                dependencies.append(attr.__module__)
                    
                    # Record metrics
                    with self._lock:
                        first_import = module_name not in self._import_metrics
                        self._import_metrics[module_name] = ImportMetrics(
                            module_name=module_name,
                            import_time=import_time,
                            size_bytes=size_bytes,
                            dependencies=list(set(dependencies[:10])),  # Limit to top 10
                            first_import=first_import
                        )
                    
                    if import_time > 0.1:  # Log slow imports
                        app_logger.warning(f"Slow import detected: {module_name} took {import_time:.3f}s")
                    
                    return result
                    
                except Exception as e:
                    import_time = time.time() - start_time
                    app_logger.error(f"Import failed for {module_name} after {import_time:.3f}s: {e}")
                    raise
            
            return wrapper
        return decorator
    
    def lazy_import(self, module_name: str, attribute: Optional[str] = None) -> Any:
        """
        Lazy import a module or attribute.
        
        Args:
            module_name: Name of the module to import
            attribute: Specific attribute to get from the module
            
        Returns:
            The imported module or attribute
        """
        cache_key = f"{module_name}.{attribute}" if attribute else module_name
        
        with self._lock:
            if cache_key in self._lazy_modules:
                return self._lazy_modules[cache_key]
        
        start_time = time.time()
        
        try:
            module = importlib.import_module(module_name)
            
            if attribute:
                result = getattr(module, attribute)
            else:
                result = module
            
            import_time = time.time() - start_time
            
            with self._lock:
                self._lazy_modules[cache_key] = result
            
            app_logger.debug(f"Lazy imported {cache_key} in {import_time:.3f}s")
            return result
            
        except Exception as e:
            import_time = time.time() - start_time
            app_logger.error(f"Lazy import failed for {cache_key} after {import_time:.3f}s: {e}")
            raise
    
    def preload_critical_modules(self, module_names: List[str]) -> Dict[str, bool]:
        """
        Preload critical modules during startup.
        
        Args:
            module_names: List of module names to preload
            
        Returns:
            Dictionary mapping module names to success status
        """
        results = {}
        
        for module_name in module_names:
            try:
                start_time = time.time()
                importlib.import_module(module_name)
                import_time = time.time() - start_time
                
                results[module_name] = True
                app_logger.debug(f"Preloaded {module_name} in {import_time:.3f}s")
                
            except Exception as e:
                results[module_name] = False
                app_logger.error(f"Failed to preload {module_name}: {e}")
        
        return results
    
    def get_import_stats(self) -> Dict[str, Any]:
        """
        Get import performance statistics.
        
        Returns:
            Dictionary with import statistics
        """
        with self._lock:
            if not self._import_metrics:
                return {
                    "total_modules": 0,
                    "total_import_time": 0.0,
                    "average_import_time": 0.0,
                    "slowest_imports": [],
                    "startup_time": time.time() - self._startup_time
                }
            
            total_time = sum(m.import_time for m in self._import_metrics.values())
            avg_time = total_time / len(self._import_metrics)
            
            # Get slowest imports
            slowest = sorted(
                self._import_metrics.values(),
                key=lambda x: x.import_time,
                reverse=True
            )[:10]
            
            slowest_imports = [
                {
                    "module": m.module_name,
                    "time": round(m.import_time, 3),
                    "size_kb": round(m.size_bytes / 1024, 1) if m.size_bytes > 0 else 0,
                    "dependencies": len(m.dependencies)
                }
                for m in slowest
            ]
            
            return {
                "total_modules": len(self._import_metrics),
                "total_import_time": round(total_time, 3),
                "average_import_time": round(avg_time, 3),
                "slowest_imports": slowest_imports,
                "startup_time": round(time.time() - self._startup_time, 3),
                "lazy_modules_cached": len(self._lazy_modules)
            }
    
    def optimize_imports(self) -> List[str]:
        """
        Analyze imports and provide optimization recommendations.
        
        Returns:
            List of optimization recommendations
        """
        recommendations = []
        
        with self._lock:
            if not self._import_metrics:
                return ["No import data available for analysis"]
            
            # Find slow imports
            slow_imports = [
                m for m in self._import_metrics.values()
                if m.import_time > 0.1
            ]
            
            if slow_imports:
                recommendations.append(
                    f"Consider lazy loading for {len(slow_imports)} slow imports: "
                    f"{', '.join([m.module_name for m in slow_imports[:5]])}"
                )
            
            # Find large modules
            large_modules = [
                m for m in self._import_metrics.values()
                if m.size_bytes > 100 * 1024  # > 100KB
            ]
            
            if large_modules:
                recommendations.append(
                    f"Consider lazy loading for {len(large_modules)} large modules: "
                    f"{', '.join([m.module_name for m in large_modules[:5]])}"
                )
            
            # Find modules with many dependencies
            heavy_deps = [
                m for m in self._import_metrics.values()
                if len(m.dependencies) > 10
            ]
            
            if heavy_deps:
                recommendations.append(
                    f"Consider refactoring {len(heavy_deps)} modules with heavy dependencies: "
                    f"{', '.join([m.module_name for m in heavy_deps[:3]])}"
                )
            
            # Overall startup time recommendation
            total_time = sum(m.import_time for m in self._import_metrics.values())
            if total_time > 2.0:
                recommendations.append(
                    f"Total import time is {total_time:.1f}s. Consider implementing "
                    "lazy loading for non-critical modules."
                )
        
        return recommendations if recommendations else ["Import performance looks good!"]


# Global import optimizer instance
_global_optimizer: Optional[ImportOptimizer] = None
_optimizer_lock = threading.Lock()


def get_import_optimizer() -> ImportOptimizer:
    """
    Get the global import optimizer instance.
    
    Returns:
        The global import optimizer
    """
    global _global_optimizer
    
    if _global_optimizer is None:
        with _optimizer_lock:
            if _global_optimizer is None:
                _global_optimizer = ImportOptimizer()
    
    return _global_optimizer


def lazy_import(module_name: str, attribute: Optional[str] = None) -> Any:
    """
    Lazy import a module or attribute using the global optimizer.
    
    Args:
        module_name: Name of the module to import
        attribute: Specific attribute to get from the module
        
    Returns:
        The imported module or attribute
    """
    optimizer = get_import_optimizer()
    return optimizer.lazy_import(module_name, attribute)


def track_import(module_name: str) -> Callable:
    """
    Decorator to track import performance using the global optimizer.
    
    Args:
        module_name: Name of the module being imported
        
    Returns:
        Decorator function
    """
    optimizer = get_import_optimizer()
    return optimizer.track_import(module_name)


def get_import_stats() -> Dict[str, Any]:
    """
    Get import performance statistics using the global optimizer.
    
    Returns:
        Dictionary with import statistics
    """
    optimizer = get_import_optimizer()
    return optimizer.get_import_stats()


def optimize_imports() -> List[str]:
    """
    Get import optimization recommendations using the global optimizer.
    
    Returns:
        List of optimization recommendations
    """
    optimizer = get_import_optimizer()
    return optimizer.optimize_imports()


# Commonly used lazy imports for the AAA system
def lazy_streamlit():
    """Lazy import streamlit."""
    return lazy_import("streamlit")


def lazy_pandas():
    """Lazy import pandas."""
    return lazy_import("pandas")


def lazy_numpy():
    """Lazy import numpy."""
    return lazy_import("numpy")


def lazy_faiss():
    """Lazy import faiss."""
    return lazy_import("faiss")


def lazy_sentence_transformers():
    """Lazy import sentence_transformers."""
    return lazy_import("sentence_transformers")


def lazy_openai():
    """Lazy import openai."""
    return lazy_import("openai")


def lazy_anthropic():
    """Lazy import anthropic."""
    return lazy_import("anthropic")


def lazy_boto3():
    """Lazy import boto3."""
    return lazy_import("boto3")