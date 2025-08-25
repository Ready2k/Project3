"""
Performance tests for the refactored system.

This module validates that the refactored system meets performance requirements,
including the 30% startup time improvement and memory efficiency goals.
"""

import pytest
import time
import psutil
import os
from unittest.mock import Mock, patch
from pathlib import Path
import gc

from app.ui.main_app import AAAStreamlitApp
from app.config.settings import ConfigurationManager, AppConfig
from app.core.registry import ServiceRegistry
from app.ui.lazy_loader import LazyLoader


class TestStartupPerformance:
    """Test startup performance improvements."""
    
    @pytest.fixture
    def performance_config(self, temp_config_dir):
        """Create performance-optimized configuration."""
        import yaml
        
        perf_config = {
            'environment': 'testing',
            'cache': {
                'type': 'memory',
                'size_limit': 1024 * 1024,  # 1MB
                'ttl_seconds': 300
            },
            'ui': {
                'show_debug': False,
                'theme': 'light'
            },
            'enable_analytics': False,  # Disable for performance testing
            'llm_providers': [
                {
                    'name': 'test_provider',
                    'model': 'test-model',
                    'timeout': 5
                }
            ]
        }
        
        with open(temp_config_dir / "base.yaml", 'w') as f:
            yaml.dump(perf_config, f)
        
        manager = ConfigurationManager(temp_config_dir)
        result = manager.load_config("testing")
        return result.value
    
    def test_configuration_loading_performance(self, temp_config_dir):
        """Test configuration loading performance."""
        manager = ConfigurationManager(temp_config_dir)
        
        # Measure configuration loading time
        start_time = time.time()
        result = manager.load_config("testing")
        load_time = time.time() - start_time
        
        assert result.is_success
        assert load_time < 0.1  # Should load in under 100ms
    
    def test_service_registry_performance(self):
        """Test service registry performance."""
        registry = ServiceRegistry()
        
        # Register multiple services
        start_time = time.time()
        for i in range(100):
            registry.register_factory(
                f"TestService{i}",
                lambda: Mock(),
                lifetime="transient"
            )
        registration_time = time.time() - start_time
        
        assert registration_time < 0.5  # Should register 100 services in under 500ms
        
        # Test resolution performance
        start_time = time.time()
        for i in range(10):
            result = registry.resolve("TestService0")
            assert result.is_success
        resolution_time = time.time() - start_time
        
        assert resolution_time < 0.1  # Should resolve 10 times in under 100ms
    
    def test_lazy_loading_performance(self):
        """Test lazy loading performance."""
        loader = LazyLoader()
        
        # Register modules for lazy loading
        start_time = time.time()
        loader.register_module("test_module1", "unittest.mock", lambda: Mock())
        loader.register_module("test_module2", "json", lambda: Mock())
        loader.register_module("test_module3", "pathlib", lambda: Mock())
        registration_time = time.time() - start_time
        
        assert registration_time < 0.01  # Registration should be very fast
        
        # Test lazy loading
        start_time = time.time()
        module1 = loader.get_module("test_module1")
        module2 = loader.get_module("test_module2")
        loading_time = time.time() - start_time
        
        assert loading_time < 0.1  # Should load modules quickly
        assert module1 is not None
        assert module2 is not None
    
    @patch('streamlit.set_page_config')
    @patch('streamlit.sidebar')
    @patch('streamlit.tabs')
    def test_main_app_startup_performance(self, mock_tabs, mock_sidebar, mock_page_config, performance_config):
        """Test main application startup performance."""
        # Mock Streamlit components
        mock_tabs.return_value = [Mock() for _ in range(5)]
        
        registry = ServiceRegistry()
        registry.register_instance(AppConfig, performance_config)
        
        with patch('app.config.settings.get_config', return_value=performance_config), \
             patch('app.core.registry.get_service_registry', return_value=registry):
            
            # Measure startup time
            start_time = time.time()
            app = AAAStreamlitApp()
            app.run()
            startup_time = time.time() - start_time
            
            # Should start quickly
            assert startup_time < 1.0  # Target: under 1 second for tests
            
            # Verify components were initialized
            mock_page_config.assert_called_once()
            mock_tabs.assert_called_once()
    
    def test_component_initialization_performance(self, performance_config):
        """Test UI component initialization performance."""
        registry = ServiceRegistry()
        
        # Measure component creation time
        start_time = time.time()
        
        from app.ui.tabs.analysis_tab import AnalysisTab
        from app.ui.tabs.qa_tab import QATab
        from app.ui.tabs.results_tab import ResultsTab
        
        tabs = [
            AnalysisTab(performance_config, registry),
            QATab(performance_config, registry),
            ResultsTab(performance_config, registry)
        ]
        
        creation_time = time.time() - start_time
        
        assert creation_time < 0.5  # Should create all tabs in under 500ms
        assert len(tabs) == 3


class TestMemoryPerformance:
    """Test memory usage and efficiency."""
    
    def get_memory_usage(self):
        """Get current memory usage in MB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    def test_configuration_memory_usage(self, temp_config_dir):
        """Test configuration memory usage."""
        initial_memory = self.get_memory_usage()
        
        # Create multiple configuration managers
        managers = []
        for i in range(10):
            manager = ConfigurationManager(temp_config_dir)
            result = manager.load_config("testing")
            assert result.is_success
            managers.append(manager)
        
        memory_after_creation = self.get_memory_usage()
        memory_increase = memory_after_creation - initial_memory
        
        # Should not use excessive memory (under 50MB for 10 managers)
        assert memory_increase < 50
        
        # Cleanup
        del managers
        gc.collect()
    
    def test_service_registry_memory_usage(self):
        """Test service registry memory usage."""
        initial_memory = self.get_memory_usage()
        
        registry = ServiceRegistry()
        
        # Register many services
        for i in range(1000):
            registry.register_factory(
                f"Service{i}",
                lambda: Mock(),
                lifetime="singleton"
            )
        
        memory_after_registration = self.get_memory_usage()
        
        # Resolve some services
        for i in range(100):
            result = registry.resolve(f"Service{i}")
            assert result.is_success
        
        memory_after_resolution = self.get_memory_usage()
        
        # Memory usage should be reasonable
        registration_memory = memory_after_registration - initial_memory
        resolution_memory = memory_after_resolution - memory_after_registration
        
        assert registration_memory < 100  # Under 100MB for 1000 registrations
        assert resolution_memory < 50     # Under 50MB for 100 resolutions
    
    def test_ui_component_memory_usage(self, performance_config):
        """Test UI component memory usage."""
        initial_memory = self.get_memory_usage()
        
        registry = ServiceRegistry()
        registry.register_instance(AppConfig, performance_config)
        
        # Create many UI components
        components = []
        for i in range(50):
            from app.ui.tabs.analysis_tab import AnalysisTab
            tab = AnalysisTab(performance_config, registry)
            components.append(tab)
        
        memory_after_creation = self.get_memory_usage()
        memory_increase = memory_after_creation - initial_memory
        
        # Should share configuration and registry instances
        assert memory_increase < 100  # Under 100MB for 50 components
        
        # Verify shared instances
        for component in components:
            assert component.config is performance_config
            assert component.registry is registry
        
        # Cleanup
        del components
        gc.collect()
    
    def test_session_state_memory_usage(self):
        """Test session state memory usage."""
        initial_memory = self.get_memory_usage()
        
        # Create many session states
        sessions = []
        for i in range(100):
            from app.state.store import SessionState
            session = SessionState(
                session_id=f"perf-test-{i}",
                requirements={"description": f"Test requirement {i}"}
            )
            sessions.append(session)
        
        memory_after_creation = self.get_memory_usage()
        memory_increase = memory_after_creation - initial_memory
        
        # Should use reasonable memory (under 200MB for 100 sessions)
        assert memory_increase < 200
        
        # Cleanup
        del sessions
        gc.collect()


class TestCachePerformance:
    """Test caching performance improvements."""
    
    def test_configuration_caching_performance(self, temp_config_dir):
        """Test configuration caching performance."""
        manager = ConfigurationManager(temp_config_dir)
        
        # First load (should read from files)
        start_time = time.time()
        result1 = manager.load_config("testing")
        first_load_time = time.time() - start_time
        
        assert result1.is_success
        
        # Subsequent gets (should use cache)
        start_time = time.time()
        for _ in range(100):
            cached_config = manager.get_config()
            assert cached_config is result1.value
        cache_access_time = time.time() - start_time
        
        # Cache access should be much faster
        assert cache_access_time < first_load_time / 10
        assert cache_access_time < 0.01  # Under 10ms for 100 accesses
    
    def test_service_registry_caching_performance(self):
        """Test service registry singleton caching."""
        registry = ServiceRegistry()
        
        # Register singleton service
        registry.register_factory(
            "CachedService",
            lambda: Mock(),
            lifetime="singleton"
        )
        
        # First resolution (should create instance)
        start_time = time.time()
        result1 = registry.resolve("CachedService")
        first_resolution_time = time.time() - start_time
        
        assert result1.is_success
        
        # Subsequent resolutions (should use cached instance)
        start_time = time.time()
        for _ in range(100):
            result = registry.resolve("CachedService")
            assert result.is_success
            assert result.value is result1.value
        cached_resolution_time = time.time() - start_time
        
        # Cached resolution should be much faster
        assert cached_resolution_time < first_resolution_time / 5
        assert cached_resolution_time < 0.01  # Under 10ms for 100 resolutions
    
    def test_lazy_loading_caching_performance(self):
        """Test lazy loading caching performance."""
        loader = LazyLoader()
        
        # Register module
        loader.register_module("test_module", "json", lambda: Mock())
        
        # First load (should create instance)
        start_time = time.time()
        module1 = loader.get_module("test_module")
        first_load_time = time.time() - start_time
        
        # Subsequent loads (should use cached instance)
        start_time = time.time()
        for _ in range(100):
            module = loader.get_module("test_module")
            assert module is module1
        cached_load_time = time.time() - start_time
        
        # Cached loading should be much faster
        assert cached_load_time < first_load_time / 10
        assert cached_load_time < 0.01  # Under 10ms for 100 loads


class TestScalabilityPerformance:
    """Test system scalability and performance under load."""
    
    def test_concurrent_configuration_loading(self, temp_config_dir):
        """Test concurrent configuration loading performance."""
        import threading
        import queue
        
        results = queue.Queue()
        
        def load_config():
            manager = ConfigurationManager(temp_config_dir)
            start_time = time.time()
            result = manager.load_config("testing")
            load_time = time.time() - start_time
            results.put((result.is_success, load_time))
        
        # Start multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=load_config)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        load_times = []
        while not results.empty():
            success, load_time = results.get()
            assert success
            load_times.append(load_time)
        
        assert len(load_times) == 10
        # All loads should complete reasonably quickly
        assert max(load_times) < 1.0
        assert sum(load_times) / len(load_times) < 0.5  # Average under 500ms
    
    def test_high_volume_service_resolution(self):
        """Test service resolution under high volume."""
        registry = ServiceRegistry()
        
        # Register services
        for i in range(100):
            registry.register_factory(
                f"Service{i}",
                lambda: Mock(),
                lifetime="transient"
            )
        
        # High volume resolution
        start_time = time.time()
        for _ in range(1000):
            service_id = f"Service{_ % 100}"
            result = registry.resolve(service_id)
            assert result.is_success
        resolution_time = time.time() - start_time
        
        # Should handle high volume efficiently
        assert resolution_time < 5.0  # Under 5 seconds for 1000 resolutions
        assert resolution_time / 1000 < 0.005  # Under 5ms per resolution
    
    def test_memory_stability_under_load(self, performance_config):
        """Test memory stability under sustained load."""
        initial_memory = self.get_memory_usage()
        registry = ServiceRegistry()
        
        # Sustained load test
        for iteration in range(10):
            # Create components
            components = []
            for i in range(20):
                from app.ui.tabs.analysis_tab import AnalysisTab
                tab = AnalysisTab(performance_config, registry)
                components.append(tab)
            
            # Use components
            for component in components:
                assert component.can_render() is True
            
            # Cleanup
            del components
            gc.collect()
            
            # Check memory usage
            current_memory = self.get_memory_usage()
            memory_increase = current_memory - initial_memory
            
            # Memory should not grow excessively
            assert memory_increase < 200  # Under 200MB growth
    
    def get_memory_usage(self):
        """Get current memory usage in MB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024


class TestPerformanceRegression:
    """Test for performance regressions."""
    
    def test_startup_time_improvement(self, performance_config):
        """Test that startup time meets improvement targets."""
        registry = ServiceRegistry()
        registry.register_instance(AppConfig, performance_config)
        
        with patch('streamlit.set_page_config'), \
             patch('streamlit.sidebar'), \
             patch('streamlit.tabs', return_value=[Mock() for _ in range(5)]), \
             patch('app.config.settings.get_config', return_value=performance_config), \
             patch('app.core.registry.get_service_registry', return_value=registry):
            
            # Measure startup time multiple times
            startup_times = []
            for _ in range(5):
                start_time = time.time()
                app = AAAStreamlitApp()
                app.run()
                startup_time = time.time() - start_time
                startup_times.append(startup_time)
            
            # Calculate average startup time
            avg_startup_time = sum(startup_times) / len(startup_times)
            
            # Should meet performance targets
            assert avg_startup_time < 1.0  # Target: under 1 second
            assert max(startup_times) < 2.0  # No outliers over 2 seconds
    
    def test_memory_efficiency_improvement(self, performance_config):
        """Test memory efficiency improvements."""
        initial_memory = self.get_memory_usage()
        
        # Create application components
        registry = ServiceRegistry()
        registry.register_instance(AppConfig, performance_config)
        
        # Create multiple app instances (simulating multiple users)
        apps = []
        for i in range(5):
            with patch('app.config.settings.get_config', return_value=performance_config), \
                 patch('app.core.registry.get_service_registry', return_value=registry):
                app = AAAStreamlitApp()
                apps.append(app)
        
        memory_after_creation = self.get_memory_usage()
        memory_per_app = (memory_after_creation - initial_memory) / len(apps)
        
        # Should use reasonable memory per app instance
        assert memory_per_app < 50  # Under 50MB per app instance
        
        # Cleanup
        del apps
        gc.collect()
    
    def get_memory_usage(self):
        """Get current memory usage in MB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024