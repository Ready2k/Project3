"""
Simplified integration tests for startup validation system.

Tests cover:
- Complete dependency validation at startup
- Error reporting for missing dependencies
- Graceful handling of optional dependency failures
- Dependency report generation

Requirements covered: 4.1, 4.4, 5.1
"""

import pytest
import tempfile
import os
import yaml
from unittest.mock import Mock, patch
from typing import Dict, Any

from app.core.startup import ApplicationStartup, StartupError
from app.core.dependencies import ValidationResult
from app.core.registry import get_registry, reset_registry


class TestStartupValidationIntegrationSimple:
    """Simplified integration tests for startup validation system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_registry()
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.temp_dir, "config")
        os.makedirs(self.config_dir, exist_ok=True)
        self._create_minimal_config()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        reset_registry()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_minimal_config(self):
        """Create minimal test configuration."""
        # Create empty services config
        services_config = {'services': {}}
        with open(os.path.join(self.config_dir, "services.yaml"), 'w') as f:
            yaml.dump(services_config, f)
        
        # Create empty dependencies config
        deps_config = {'dependencies': {'required': [], 'optional': [], 'development': []}}
        with open(os.path.join(self.config_dir, "dependencies.yaml"), 'w') as f:
            yaml.dump(deps_config, f)
    
    def test_successful_startup_validation(self):
        """Test successful startup validation with all dependencies available."""
        with patch('app.core.service_config.ServiceConfigLoader.setup_dependency_validator') as mock_setup, \
             patch('app.core.service_registration.register_core_services') as mock_register, \
             patch('app.core.service_registration.initialize_core_services') as mock_init:
            
            # Mock successful dependency validation
            mock_validator = Mock()
            mock_validator.validate_all.return_value = ValidationResult(
                is_valid=True,
                missing_required=[],
                missing_optional=[],
                version_conflicts=[],
                warnings=[],
                installation_instructions=""
            )
            mock_setup.return_value = mock_validator
            
            # Mock service registration
            mock_register.return_value = ['config', 'logger', 'cache']
            mock_init.return_value = {'config': True, 'logger': True, 'cache': True}
            
            # Mock registry
            registry = get_registry()
            registry.validate_dependencies = Mock(return_value=[])
            registry.list_services = Mock(return_value=['config', 'logger', 'cache'])
            registry.health_check = Mock(return_value={'config': True, 'logger': True, 'cache': True})
            
            startup = ApplicationStartup(self.config_dir)
            results = startup.run_startup_sequence()
            
            # Verify successful startup
            assert results['startup_successful'] is True
            assert results['dependencies']['valid'] is True
            assert len(results['dependencies']['missing_required']) == 0
            assert results['services']['registered_count'] > 0
            assert results['registry']['valid'] is True
    
    def test_missing_required_dependencies(self):
        """Test startup validation with missing required dependencies."""
        with patch('app.core.service_config.ServiceConfigLoader.setup_dependency_validator') as mock_setup, \
             patch('app.core.service_registration.register_core_services') as mock_register, \
             patch('app.core.service_registration.initialize_core_services') as mock_init:
            
            # Mock dependency validation with missing required
            mock_validator = Mock()
            mock_validator.validate_all.return_value = ValidationResult(
                is_valid=False,
                missing_required=['streamlit', 'fastapi'],
                missing_optional=['redis'],
                version_conflicts=[],
                warnings=['Optional dependency redis not available'],
                installation_instructions="pip install streamlit>=1.28.0 fastapi>=0.104.0 redis>=4.0.0"
            )
            mock_setup.return_value = mock_validator
            
            # Mock service registration
            mock_register.return_value = ['config', 'logger', 'cache']
            mock_init.return_value = {'config': True, 'logger': True, 'cache': True}
            
            # Mock registry
            registry = get_registry()
            registry.validate_dependencies = Mock(return_value=[])
            registry.list_services = Mock(return_value=['config', 'logger', 'cache'])
            registry.health_check = Mock(return_value={'config': True, 'logger': True, 'cache': True})
            
            startup = ApplicationStartup(self.config_dir)
            results = startup.run_startup_sequence()
            
            # Startup completes but dependencies are invalid
            assert results['startup_successful'] is True
            assert results['dependencies']['valid'] is False
            assert 'streamlit' in results['dependencies']['missing_required']
            assert 'fastapi' in results['dependencies']['missing_required']
            assert 'redis' in results['dependencies']['missing_optional']
            assert 'pip install' in results['dependencies']['installation_instructions']
    
    def test_graceful_optional_dependency_handling(self):
        """Test graceful handling of missing optional dependencies."""
        with patch('app.core.service_config.ServiceConfigLoader.setup_dependency_validator') as mock_setup, \
             patch('app.core.service_registration.register_core_services') as mock_register, \
             patch('app.core.service_registration.initialize_core_services') as mock_init:
            
            # Mock dependency validation with only optional missing
            mock_validator = Mock()
            mock_validator.validate_all.return_value = ValidationResult(
                is_valid=True,  # Valid because only optional deps missing
                missing_required=[],
                missing_optional=['redis', 'openai', 'diagrams'],
                version_conflicts=[],
                warnings=[
                    'Optional dependency redis not available. Feature disabled: Caching',
                    'Optional dependency openai not available. Feature disabled: LLM provider',
                    'Optional dependency diagrams not available. Feature disabled: Infrastructure diagrams'
                ],
                installation_instructions="pip install redis>=4.0.0 openai>=1.3.0 diagrams>=0.23.0"
            )
            mock_setup.return_value = mock_validator
            
            # Mock service registration
            mock_register.return_value = ['config', 'logger', 'cache']
            mock_init.return_value = {'config': True, 'logger': True, 'cache': True}
            
            # Mock registry
            registry = get_registry()
            registry.validate_dependencies = Mock(return_value=[])
            registry.list_services = Mock(return_value=['config', 'logger', 'cache'])
            registry.health_check = Mock(return_value={'config': True, 'logger': True, 'cache': True})
            
            startup = ApplicationStartup(self.config_dir)
            results = startup.run_startup_sequence()
            
            # System should be valid despite missing optional dependencies
            assert results['startup_successful'] is True
            assert results['dependencies']['valid'] is True
            assert len(results['dependencies']['missing_required']) == 0
            assert len(results['dependencies']['missing_optional']) > 0
            assert len(results['dependencies']['warnings']) > 0
            
            # Verify specific optional dependencies are reported
            missing_optional = results['dependencies']['missing_optional']
            assert 'redis' in missing_optional
            assert 'openai' in missing_optional
            assert 'diagrams' in missing_optional
    
    def test_version_conflicts_detection(self):
        """Test detection and reporting of version conflicts."""
        with patch('app.core.service_config.ServiceConfigLoader.setup_dependency_validator') as mock_setup, \
             patch('app.core.service_registration.register_core_services') as mock_register, \
             patch('app.core.service_registration.initialize_core_services') as mock_init:
            
            # Mock dependency validation with version conflicts
            mock_validator = Mock()
            mock_validator.validate_all.return_value = ValidationResult(
                is_valid=False,
                missing_required=[],
                missing_optional=[],
                version_conflicts=[
                    'streamlit: installed version 1.20.0 does not satisfy constraint >=1.28.0',
                    'fastapi: installed version 0.90.0 does not satisfy constraint >=0.104.0'
                ],
                warnings=[],
                installation_instructions="pip install streamlit>=1.28.0 fastapi>=0.104.0"
            )
            mock_setup.return_value = mock_validator
            
            # Mock service registration
            mock_register.return_value = ['config', 'logger', 'cache']
            mock_init.return_value = {'config': True, 'logger': True, 'cache': True}
            
            # Mock registry
            registry = get_registry()
            registry.validate_dependencies = Mock(return_value=[])
            registry.list_services = Mock(return_value=['config', 'logger', 'cache'])
            registry.health_check = Mock(return_value={'config': True, 'logger': True, 'cache': True})
            
            startup = ApplicationStartup(self.config_dir)
            results = startup.run_startup_sequence()
            
            # System should be invalid due to version conflicts
            assert results['startup_successful'] is True  # Startup completes
            assert results['dependencies']['valid'] is False
            assert len(results['dependencies']['version_conflicts']) > 0
            
            # Verify specific version conflicts are reported
            conflicts = results['dependencies']['version_conflicts']
            assert any('streamlit' in conflict and '1.20.0' in conflict for conflict in conflicts)
            assert any('fastapi' in conflict and '0.90.0' in conflict for conflict in conflicts)
    
    def test_dependency_report_generation(self):
        """Test comprehensive dependency report generation."""
        with patch('app.core.service_config.ServiceConfigLoader.setup_dependency_validator') as mock_setup, \
             patch('app.core.service_registration.register_core_services') as mock_register, \
             patch('app.core.service_registration.initialize_core_services') as mock_init:
            
            # Mock mixed dependency status
            mock_validator = Mock()
            mock_validator.validate_all.return_value = ValidationResult(
                is_valid=False,
                missing_required=['streamlit'],
                missing_optional=['redis', 'openai'],
                version_conflicts=['fastapi: installed version 0.90.0 does not satisfy constraint >=0.104.0'],
                warnings=[
                    'Optional dependency redis not available',
                    'Optional dependency openai not available'
                ],
                installation_instructions="pip install streamlit>=1.28.0 fastapi>=0.104.0 redis>=4.0.0 openai>=1.3.0"
            )
            mock_setup.return_value = mock_validator
            
            # Mock service registration
            mock_register.return_value = ['config', 'logger', 'cache']
            mock_init.return_value = {'config': True, 'logger': True, 'cache': True}
            
            # Mock registry
            registry = get_registry()
            registry.validate_dependencies = Mock(return_value=[])
            registry.list_services = Mock(return_value=['config', 'logger', 'cache'])
            registry.health_check = Mock(return_value={'config': True, 'logger': True, 'cache': True})
            
            startup = ApplicationStartup(self.config_dir)
            results = startup.run_startup_sequence()
            
            # Generate and verify startup report
            report = startup.get_startup_report()
            
            # Verify report structure
            assert "Application Startup Report" in report
            assert "Startup Status:" in report
            assert "Dependencies:" in report
            assert "Services:" in report
            assert "Service Registry:" in report
            
            # Verify dependency information in report
            assert "Missing required: streamlit" in report
            assert "Missing optional: redis, openai" in report
            assert "Version conflicts: 1" in report
            
            # Verify service information (system registers more services than we mock)
            assert "Registered:" in report
            assert "Health:" in report
            assert "Health:" in report
    
    def test_service_registration_failure(self):
        """Test startup behavior when service registration fails."""
        with patch('app.core.service_config.ServiceConfigLoader.setup_dependency_validator') as mock_setup, \
             patch('app.core.service_config.ServiceConfigLoader.load_configuration') as mock_load:
            
            # Mock successful dependency validation
            mock_validator = Mock()
            mock_validator.validate_all.return_value = ValidationResult(
                is_valid=True,
                missing_required=[],
                missing_optional=[],
                version_conflicts=[],
                warnings=[],
                installation_instructions=""
            )
            mock_setup.return_value = mock_validator
            
            # Mock configuration loading failure to trigger startup error
            mock_load.side_effect = RuntimeError("Failed to load configuration")
            
            startup = ApplicationStartup(self.config_dir)
            
            # Should raise StartupError
            with pytest.raises(StartupError) as exc_info:
                startup.run_startup_sequence()
            
            assert "Application startup failed" in str(exc_info.value)
            assert "Failed to load configuration" in str(exc_info.value)
            
            # Verify error is recorded
            results = startup.get_validation_results()
            assert results['startup_successful'] is False
            assert 'error' in results
    
    def test_configuration_validation_errors(self):
        """Test startup behavior with configuration validation errors."""
        with patch('app.core.service_config.ServiceConfigLoader.setup_dependency_validator') as mock_setup, \
             patch('app.core.service_config.ServiceConfigLoader.validate_service_configuration') as mock_validate, \
             patch('app.core.service_registration.register_core_services') as mock_register, \
             patch('app.core.service_registration.initialize_core_services') as mock_init:
            
            # Mock dependency validation as successful
            mock_validator = Mock()
            mock_validator.validate_all.return_value = ValidationResult(
                is_valid=True,
                missing_required=[],
                missing_optional=[],
                version_conflicts=[],
                warnings=[],
                installation_instructions=""
            )
            mock_setup.return_value = mock_validator
            
            # Mock service configuration validation with errors
            mock_validate.return_value = [
                'Service invalid_service missing required field class_path',
                'Service another_service has invalid dependency missing_dep'
            ]
            
            # Mock service registration
            mock_register.return_value = ['config', 'logger', 'cache']
            mock_init.return_value = {'config': True, 'logger': True, 'cache': True}
            
            # Mock registry
            registry = get_registry()
            registry.validate_dependencies = Mock(return_value=[])
            registry.list_services = Mock(return_value=['config', 'logger', 'cache'])
            registry.health_check = Mock(return_value={'config': True, 'logger': True, 'cache': True})
            
            startup = ApplicationStartup(self.config_dir)
            results = startup.run_startup_sequence()
            
            # Startup should complete but configuration should be invalid
            assert results['startup_successful'] is True
            assert results['configuration']['valid'] is False
            assert len(results['configuration']['service_errors']) > 0
            
            # Verify specific errors are reported
            errors = results['configuration']['service_errors']
            assert any('class_path' in error for error in errors)
            assert any('missing_dep' in error for error in errors)


if __name__ == "__main__":
    """Run integration tests when executed directly."""
    pytest.main([__file__, "-v", "--tb=short"])