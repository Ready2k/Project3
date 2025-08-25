"""
Global test configuration and fixtures for the refactored AAA system.

This module provides test fixtures that work with the new modular architecture,
including configuration management, service registry, and UI components.
"""

import pytest
import tempfile
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch

from app.config.settings import ConfigurationManager, AppConfig, Environment
from app.core.registry import ServiceRegistry, ServiceLifetime
from app.utils.result import Result
from app.state.store import SessionState


@pytest.fixture(scope="session")
def temp_config_dir():
    """Create a temporary directory for test configuration files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        
        # Create base configuration
        base_config = {
            "environment": "testing",
            "debug": True,
            "log_level": "DEBUG",
            "database": {
                "url": "sqlite:///:memory:",
                "pool_size": 1
            },
            "cache": {
                "type": "memory",
                "size_limit": 1024 * 1024  # 1MB for tests
            },
            "security": {
                "enable_prompt_defense": False,
                "max_input_length": 1000
            },
            "ui": {
                "show_debug": True,
                "theme": "light"
            },
            "llm_providers": [
                {
                    "name": "test_provider",
                    "model": "test-model",
                    "timeout": 5,
                    "temperature": 0.0
                }
            ],
            "default_llm_provider": "test_provider"
        }
        
        with open(config_dir / "base.yaml", 'w') as f:
            yaml.dump(base_config, f)
        
        # Create testing environment config
        test_config = {
            "debug": True,
            "log_level": "DEBUG",
            "cache": {
                "ttl_seconds": 60  # Short TTL for tests
            }
        }
        
        with open(config_dir / "testing.yaml", 'w') as f:
            yaml.dump(test_config, f)
        
        yield config_dir


@pytest.fixture
def test_config_manager(temp_config_dir):
    """Create a configuration manager for testing."""
    manager = ConfigurationManager(temp_config_dir)
    result = manager.load_config("testing")
    
    if result.is_error:
        pytest.fail(f"Failed to load test configuration: {result.error}")
    
    return manager


@pytest.fixture
def test_config(test_config_manager):
    """Get test configuration."""
    return test_config_manager.get_config()


@pytest.fixture
def test_service_registry():
    """Create a fresh service registry for testing."""
    registry = ServiceRegistry()
    
    # Register common test services
    registry.register_factory(
        ConfigurationManager,
        lambda: Mock(spec=ConfigurationManager),
        ServiceLifetime.SINGLETON
    )
    
    return registry


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider for testing."""
    provider = Mock()
    provider.generate_text.return_value = Result.success("Test response")
    provider.generate_questions.return_value = Result.success([
        {"text": "Test question?", "field": "test_field"}
    ])
    return provider


@pytest.fixture
def sample_requirements():
    """Sample requirements for testing."""
    return {
        "description": "Automate daily data processing from CSV files",
        "domain": "data_processing",
        "frequency": "daily",
        "data_sensitivity": "medium",
        "volume": {"daily": 10000},
        "integrations": ["database", "email"],
        "workflow_steps": ["download", "validate", "process", "store", "notify"],
        "criticality": "high"
    }


@pytest.fixture
def sample_session_state(sample_requirements):
    """Create a sample session state for testing."""
    return SessionState(
        session_id="test-session-123",
        requirements=sample_requirements
    )


@pytest.fixture
def temp_pattern_dir():
    """Create temporary directory with test patterns."""
    with tempfile.TemporaryDirectory() as temp_dir:
        patterns_dir = Path(temp_dir) / "patterns"
        patterns_dir.mkdir()
        
        # Create test patterns
        test_patterns = [
            {
                "pattern_id": "PAT-001",
                "name": "Data Processing Automation",
                "description": "Automate data processing workflows",
                "feasibility": "Automatable",
                "confidence_score": 0.9,
                "tech_stack": ["Python", "Pandas"],
                "tags": ["data", "processing", "automation"]
            },
            {
                "pattern_id": "PAT-002", 
                "name": "API Integration",
                "description": "Automate API integrations",
                "feasibility": "Partially Automatable",
                "confidence_score": 0.75,
                "tech_stack": ["Python", "FastAPI"],
                "tags": ["api", "integration"]
            }
        ]
        
        for pattern in test_patterns:
            pattern_file = patterns_dir / f"{pattern['pattern_id']}.json"
            with open(pattern_file, 'w') as f:
                json.dump(pattern, f, indent=2)
        
        yield patterns_dir


@pytest.fixture
def mock_streamlit():
    """Mock Streamlit components for UI testing."""
    with patch('streamlit.session_state', {}), \
         patch('streamlit.sidebar') as mock_sidebar, \
         patch('streamlit.tabs') as mock_tabs, \
         patch('streamlit.container') as mock_container:
        
        # Configure mock returns
        mock_tabs.return_value = [Mock() for _ in range(5)]
        mock_container.return_value.__enter__ = Mock(return_value=Mock())
        mock_container.return_value.__exit__ = Mock(return_value=None)
        
        yield {
            'sidebar': mock_sidebar,
            'tabs': mock_tabs,
            'container': mock_container
        }


@pytest.fixture
def ui_test_environment(test_config, test_service_registry, mock_streamlit):
    """Complete UI testing environment."""
    # Register UI-related services
    test_service_registry.register_instance(AppConfig, test_config)
    
    return {
        'config': test_config,
        'registry': test_service_registry,
        'streamlit_mocks': mock_streamlit
    }


class TestDataBuilder:
    """Builder for creating test data with various configurations."""
    
    @staticmethod
    def requirements(**overrides):
        """Build test requirements with overrides."""
        base = {
            "description": "Test automation requirement",
            "domain": "test_domain",
            "frequency": "daily",
            "data_sensitivity": "medium",
            "volume": {"daily": 1000},
            "integrations": ["test_system"],
            "criticality": "medium"
        }
        base.update(overrides)
        return base
    
    @staticmethod
    def pattern(**overrides):
        """Build test pattern with overrides."""
        base = {
            "pattern_id": "TEST-001",
            "name": "Test Pattern",
            "description": "Test pattern description",
            "feasibility": "Automatable",
            "confidence_score": 0.8,
            "tech_stack": ["Python"],
            "tags": ["test"]
        }
        base.update(overrides)
        return base
    
    @staticmethod
    def session_state(session_id="test-session", **overrides):
        """Build test session state with overrides."""
        requirements = TestDataBuilder.requirements()
        requirements.update(overrides.pop("requirements", {}))
        
        session = SessionState(session_id=session_id, requirements=requirements)
        
        for key, value in overrides.items():
            setattr(session, key, value)
        
        return session


@pytest.fixture
def test_data_builder():
    """Provide test data builder."""
    return TestDataBuilder


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "ui: mark test as UI test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file location."""
    for item in items:
        # Add integration marker for integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add ui marker for UI tests
        if "ui" in str(item.fspath) or "streamlit" in str(item.fspath):
            item.add_marker(pytest.mark.ui)
        
        # Add slow marker for e2e tests
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.slow)