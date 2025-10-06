"""
Integration tests for startup validation system.

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

from app.core.startup import (
    ApplicationStartup, 
    StartupError, 
    run_application_startup,
    validate_environment_setup,
    print_startup_summary
)
from app.core.registry import get_registry, reset_registry


class TestStartupValidationIntegration:
    """Integration tests for complete startup validation system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_registry()
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.temp_dir, "config")
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Create minimal test configuration files
        self._create_test_config_files()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        reset_registry()
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_config_files(self):
        """Create test configuration files."""
        # Create services.yaml - using correct format (dict, not list)
        services_config = {
            'services': {
                'test_service': {
                    'class_path': 'app.tests.fixtures.mock_services.TestService',
                    'enabled': True,
                    'singleton': True,
                    'dependencies': [],
                    'config': {}
                }
            }
        }
        
        with open(os.path.join(self.config_dir, "services.yaml"), 'w') as f:
            yaml.dump(services_config, f)
        
        # Create dependencies.yaml
        dependencies_config = {
            'dependencies': {
                'required': [
                    {
                        'name': 'streamlit',
                        'version_constraint': '>=1.28.0',
                        'import_name': 'streamlit',
                        'installation_name': 'streamlit',
                        'purpose': 'Web UI framework',
                        'alternatives': ['dash', 'gradio']
                    },
                    {
                        'name': 'fastapi',
                        'version_constraint': '>=0.104.0',
                        'import_name': 'fastapi',
                        'installation_name': 'fastapi',
                        'purpose': 'API framework',
                        'alternatives': ['flask']
                    }
                ],
                'optional': [
                    {
                        'name': 'redis',
                        'version_constraint': '>=4.0.0',
                        'import_name': 'redis',
                        'installation_name': 'redis',
                        'purpose': 'Caching backend',
                        'alternatives': ['memory_cache']
                    },
                    {
                        'name': 'openai',
                        'version_constraint': '>=1.3.0',
                        'import_name': 'openai',
                        'installation_name': 'openai',
                        'purpose': 'LLM provider',
                        'alternatives': ['anthropic']
                    }
                ],
                'development': [
                    {
                        'name': 'pytest',
                        'version_constraint': '>=7.0.0',
                        'import_name': 'pytest',
                        'installation_name': 'pytest',
                        'purpose': 'Testing framework',
                        'alternatives': ['unittest']
                    }
                ]
            }
        }
        
        with open(os.path.join(self.config_dir, "dependencies.yaml"), 'w') as f:
            yaml.dump(dependencies_config, f)
    
    def test_complete_dependency_validation_at_startup_success(self):
        """Test complete dependency validation during successful startup."""
        with patch('importlib.import_module') as mock_import, \
             patch('app.core.service_registration.register_core_services') as mock_register, \
             patch('app.core.service_registration.initialize_core_services') as mock_init, \
             patch('app.core.dependencies.validate_startup_dependencies') as mock_dep_validation, \
             patch('app.core.service_config.ServiceConfigLoader.validate_service_configuration') as mock_service_validation:
            
            # Mock successful imports for all required dependencies
            mock_modules = {
                'streamlit': Mock(__version__='1.30.0'),
                'fastapi': Mock(__version__='0.105.0'),
                'redis': Mock(__version__='4.5.0'),  # Optional but available
                'openai': Mock(__version__='1.5.0')   # Optional but available
            }
            
            def import_side_effect(name):
                if name in mock_modules:
                    return mock_modules[name]
                raise ImportError(f"No module named '{name}'")
            
            mock_import.side_effect = import_side_effect
            
            # Mock dependency validation to return success
            from app.core.dependencies import ValidationResult
            mock_dep_validation.return_value = ValidationResult(
                is_valid=True,
                missing_required=[],
                missing_optional=[],
                version_conflicts=[],
                warnings=[],
                installation_instructions=""
            )
            
            # Mock service configuration validation to return no errors
            mock_service_validation.return_value = []
            
            # Mock service registration
            mock_register.return_value = ['config', 'logger', 'cache']
            mock_init.return_value = {'config': True, 'logger': True, 'cache': True}
            
            # Mock registry validation
            registry = get_registry()
            registry.validate_dependencies = Mock(return_value=[])
            registry.list_services = Mock(return_value=['config', 'logger', 'cache'])
            registry.health_check = Mock(return_value={'config': True, 'logger': True, 'cache': True})
            
            startup = ApplicationStartup(self.config_dir)
            results = startup.run_startup_sequence()
            
            # Verify startup was successful
            assert results['startup_successful'] is True
            
            # Verify dependency validation results
            deps = results['dependencies']
            assert deps['valid'] is True
            assert len(deps['missing_required']) == 0
            assert len(deps['version_conflicts']) == 0
            
            # Verify optional dependencies were found
            assert len(deps['missing_optional']) == 0
            
            # Verify configuration was loaded
            config = results['configuration']
            assert config['valid'] is True
            
            # Verify services were registered
            services = results['services']
            assert services['registered_count'] > 0
            assert services['failed_count'] == 0
            
            # Verify registry validation
            registry_results = results['registry']
            assert registry_results['valid'] is True
            assert len(registry_results['dependency_errors']) == 0
    
    def test_complete_dependency_validation_missing_required(self):
        """Test startup validation with missing required dependencies."""
        with patch('importlib.import_module') as mock_import, \
             patch('app.core.service_registration.register_core_services') as mock_register, \
             patch('app.core.service_registration.initialize_core_services') as mock_init, \
             patch('app.core.dependencies.validate_startup_dependencies') as mock_dep_validation:
            
            # Mock missing required dependencies
            def import_side_effect(name):
                if name == 'streamlit':
                    raise ImportError("No module named 'streamlit'")
                elif name == 'fastapi':
                    return Mock(__version__='0.105.0')
                else:
                    raise ImportError(f"No module named '{name}'")
            
            mock_import.side_effect = import_side_effect
            
            # Mock dependency validation to return missing required
            from app.core.dependencies import ValidationResult
            mock_dep_validation.return_value = ValidationResult(
                is_valid=False,
                missing_required=['streamlit'],
                missing_optional=['redis', 'openai'],
                version_conflicts=[],
                warnings=['Optional dependency redis not available', 'Optional dependency openai not available'],
                installation_instructions="pip install streamlit>=1.28.0 redis>=4.0.0 openai>=1.3.0"
            )
            
            # Also need to mock the service configuration validation to avoid errors
            with patch('app.core.service_config.ServiceConfigLoader.validate_service_configuration') as mock_service_validation:
                mock_service_validation.return_value = []
            
            # Mock service registration (should still work)
            mock_register.return_value = ['config', 'logger', 'cache']
            mock_init.return_value = {'config': True, 'logger': True, 'cache': True}
            
            # Mock registry validation
            registry = get_registry()
            registry.validate_dependencies = Mock(return_value=[])
            registry.list_services = Mock(return_value=['config', 'logger', 'cache'])
            registry.health_check = Mock(return_value={'config': True, 'logger': True, 'cache': True})
            
            startup = ApplicationStartup(self.config_dir)
            results = startup.run_startup_sequence()
            
            # Startup should complete but dependency validation should fail
            assert results['startup_successful'] is True  # Startup completes
            
            # Verify dependency validation detected missing required
            deps = results['dependencies']
            assert deps['valid'] is False  # Dependencies not valid
            assert 'streamlit' in deps['missing_required']
            assert 'fastapi' not in deps['missing_required']  # This one was available
            
            # Verify installation instructions were generated
            assert deps['installation_instructions'] != ""
            assert 'streamlit' in deps['installation_instructions']
            assert 'pip install' in deps['installation_instructions']
    
    def test_error_reporting_for_missing_dependencies(self):
        """Test comprehensive error reporting for missing dependencies."""
        with patch('importlib.import_module') as mock_import, \
             patch('app.core.dependencies.validate_startup_dependencies') as mock_dep_validation:
            
            # Mock all dependencies as missing
            mock_import.side_effect = ImportError("No module found")
            
            # Mock dependency validation to return comprehensive errors
            from app.core.dependencies import ValidationResult
            mock_dep_validation.return_value = ValidationResult(
                is_valid=False,
                missing_required=['streamlit', 'fastapi'],
                missing_optional=['redis', 'openai', 'pytest'],
                version_conflicts=[],
                warnings=[
                    'Optional dependency redis not available. Feature disabled: Caching backend',
                    'Optional dependency openai not available. Feature disabled: LLM provider',
                    'Optional dependency pytest not available. Feature disabled: Testing framework'
                ],
                installation_instructions="pip install streamlit>=1.28.0 fastapi>=0.104.0 redis>=4.0.0 openai>=1.3.0 pytest>=7.0.0"
            )
            
            # Create startup instance
            startup = ApplicationStartup(self.config_dir)
            
            # Test dependency validation specifically
            results = startup._validate_dependencies(include_dev=True)
            
            # Verify comprehensive error reporting
            assert results['valid'] is False
            assert len(results['missing_required']) > 0
            assert len(results['missing_optional']) > 0
            
            # Verify installation instructions are comprehensive
            instructions = results['installation_instructions']
            assert 'pip install' in instructions
            assert 'streamlit' in instructions
            assert 'fastapi' in instructions
            
            # Test error message clarity
            assert isinstance(results['missing_required'], list)
            assert isinstance(results['missing_optional'], list)
            
            # Verify warnings are generated for optional dependencies
            assert len(results['warnings']) >= len(results['missing_optional'])
    
    def test_graceful_handling_of_optional_dependency_failures(self):
        """Test graceful handling when optional dependencies fail."""
        with patch('importlib.import_module') as mock_import, \
             patch('app.core.service_registration.register_core_services') as mock_register, \
             patch('app.core.service_registration.initialize_core_services') as mock_init, \
             patch('app.core.dependencies.validate_startup_dependencies') as mock_dep_validation:
            
            # Mock required dependencies as available, optional as missing
            def import_side_effect(name):
                if name in ['streamlit', 'fastapi']:
                    return Mock(__version__='1.0.0')
                elif name in ['redis', 'openai']:
                    raise ImportError(f"No module named '{name}'")
                else:
                    raise ImportError(f"No module named '{name}'")
            
            mock_import.side_effect = import_side_effect
            
            # Mock dependency validation - valid because only optional deps missing
            from app.core.dependencies import ValidationResult
            mock_dep_validation.return_value = ValidationResult(
                is_valid=True,  # Valid because only optional deps missing
                missing_required=[],
                missing_optional=['redis', 'openai'],
                version_conflicts=[],
                warnings=[
                    'Optional dependency redis not available. Feature disabled: Caching backend',
                    'Optional dependency openai not available. Feature disabled: LLM provider'
                ],
                installation_instructions="pip install redis>=4.0.0 openai>=1.3.0"
            )
            
            # Mock service registration
            mock_register.return_value = ['config', 'logger', 'cache']
            mock_init.return_value = {'config': True, 'logger': True, 'cache': True}
            
            # Mock registry validation
            registry = get_registry()
            registry.validate_dependencies = Mock(return_value=[])
            registry.list_services = Mock(return_value=['config', 'logger', 'cache'])
            registry.health_check = Mock(return_value={'config': True, 'logger': True, 'cache': True})
            
            startup = ApplicationStartup(self.config_dir)
            results = startup.run_startup_sequence()
            
            # Startup should succeed despite missing optional dependencies
            assert results['startup_successful'] is True
            
            # Verify dependency validation shows system as valid
            deps = results['dependencies']
            assert deps['valid'] is True  # Valid because only optional deps missing
            assert len(deps['missing_required']) == 0
            assert len(deps['missing_optional']) > 0
            
            # Verify optional dependencies are properly reported
            assert 'redis' in deps['missing_optional']
            assert 'openai' in deps['missing_optional']
            
            # Verify warnings are generated for missing optional dependencies
            assert len(deps['warnings']) > 0
            optional_warnings = [w for w in deps['warnings'] if 'Optional dependency' in w]
            assert len(optional_warnings) > 0
            
            # Verify system continues to function
            assert results['services']['registered_count'] > 0
            assert results['registry']['valid'] is True
    
    def test_dependency_report_generation(self):
        """Test comprehensive dependency report generation during startup."""
        with patch('importlib.import_module') as mock_import, \
             patch('app.core.service_registration.register_core_services') as mock_register, \
             patch('app.core.service_registration.initialize_core_services') as mock_init:
            
            # Mock mixed dependency availability
            mock_modules = {
                'streamlit': Mock(__version__='1.30.0'),  # Available
                'fastapi': Mock(__version__='0.105.0'),   # Available
                'redis': None,  # Missing
                'openai': Mock(__version__='1.5.0'),      # Available
                'pytest': None  # Missing dev dependency
            }
            
            def import_side_effect(name):
                if name in mock_modules and mock_modules[name] is not None:
                    return mock_modules[name]
                raise ImportError(f"No module named '{name}'")
            
            mock_import.side_effect = import_side_effect
            
            # Mock service registration
            mock_register.return_value = ['config', 'logger', 'cache']
            mock_init.return_value = {'config': True, 'logger': True, 'cache': True}
            
            # Mock registry validation
            registry = get_registry()
            registry.validate_dependencies = Mock(return_value=[])
            registry.list_services = Mock(return_value=['config', 'logger', 'cache'])
            registry.health_check = Mock(return_value={'config': True, 'logger': True, 'cache': True})
            
            startup = ApplicationStartup(self.config_dir)
            results = startup.run_startup_sequence(include_dev_deps=True)
            
            # Generate startup report
            report = startup.get_startup_report()
            
            # Verify report structure and content
            assert "Application Startup Report" in report
            assert "Startup Status:" in report
            assert "Environment:" in report
            assert "Configuration:" in report
            assert "Dependencies:" in report
            assert "Services:" in report
            assert "Service Registry:" in report
            
            # Verify dependency information in report
            deps = results['dependencies']
            if deps['valid']:
                assert "✅ All required dependencies available" in report
            else:
                assert "❌ Missing required:" in report
            
            if deps['missing_optional']:
                assert "Missing optional:" in report
                for missing in deps['missing_optional']:
                    assert missing in report
            
            # Verify service information in report
            services = results['services']
            assert f"Registered: {services['registered_count']}" in report
            
            if services['failed_count'] > 0:
                assert f"❌ Failed: {services['failed_count']}" in report
            
            # Verify registry health information
            registry_info = results['registry']
            health_status = registry_info['health_status']
            healthy_count = sum(1 for status in health_status.values() if status)
            total_count = len(health_status)
            assert f"Health: {healthy_count}/{total_count} services healthy" in report
    
    def test_startup_validation_with_version_conflicts(self):
        """Test startup validation when dependencies have version conflicts."""
        with patch('importlib.import_module') as mock_import, \
             patch('app.core.service_registration.register_core_services') as mock_register, \
             patch('app.core.service_registration.initialize_core_services') as mock_init, \
             patch('app.core.dependencies.validate_startup_dependencies') as mock_dep_validation:
            
            # Mock dependencies with version conflicts
            mock_modules = {
                'streamlit': Mock(__version__='1.20.0'),  # Too old (requires >=1.28.0)
                'fastapi': Mock(__version__='0.105.0'),   # OK
                'redis': Mock(__version__='3.5.0'),       # Too old (requires >=4.0.0)
                'openai': Mock(__version__='1.5.0')       # OK
            }
            
            def import_side_effect(name):
                if name in mock_modules:
                    return mock_modules[name]
                raise ImportError(f"No module named '{name}'")
            
            mock_import.side_effect = import_side_effect
            
            # Mock dependency validation with version conflicts
            from app.core.dependencies import ValidationResult
            mock_dep_validation.return_value = ValidationResult(
                is_valid=False,
                missing_required=[],
                missing_optional=[],
                version_conflicts=[
                    'streamlit: installed version 1.20.0 does not satisfy constraint >=1.28.0',
                    'redis: installed version 3.5.0 does not satisfy constraint >=4.0.0'
                ],
                warnings=[],
                installation_instructions="pip install streamlit>=1.28.0 redis>=4.0.0"
            )
            
            # Mock service registration
            mock_register.return_value = ['config', 'logger', 'cache']
            mock_init.return_value = {'config': True, 'logger': True, 'cache': True}
            
            # Mock registry validation
            registry = get_registry()
            registry.validate_dependencies = Mock(return_value=[])
            registry.list_services = Mock(return_value=['config', 'logger', 'cache'])
            registry.health_check = Mock(return_value={'config': True, 'logger': True, 'cache': True})
            
            startup = ApplicationStartup(self.config_dir)
            results = startup.run_startup_sequence()
            
            # Verify version conflicts are detected
            deps = results['dependencies']
            assert deps['valid'] is False  # Should be invalid due to version conflicts
            assert len(deps['version_conflicts']) > 0
            
            # Verify specific version conflicts
            conflicts = deps['version_conflicts']
            streamlit_conflict = any('streamlit' in conflict and '1.20.0' in conflict for conflict in conflicts)
            assert streamlit_conflict, f"Expected streamlit version conflict, got: {conflicts}"
            
            # Verify installation instructions include version requirements
            instructions = deps['installation_instructions']
            assert 'streamlit>=1.28.0' in instructions
    
    def test_startup_validation_configuration_errors(self):
        """Test startup validation when configuration has errors."""
        # Create invalid configuration
        invalid_services_config = {
            'services': {
                'invalid_service': {
                    # Missing required fields like class_path
                    'enabled': True
                }
            }
        }
        
        with open(os.path.join(self.config_dir, "services.yaml"), 'w') as f:
            yaml.dump(invalid_services_config, f)
        
        with patch('importlib.import_module') as mock_import, \
             patch('app.core.service_config.ServiceConfigLoader.validate_service_configuration') as mock_validate:
            
            # Mock all dependencies as available
            mock_import.return_value = Mock(__version__='1.0.0')
            
            # Mock service configuration validation to return errors
            mock_validate.return_value = ['Missing class_path for service invalid_service']
            
            startup = ApplicationStartup(self.config_dir)
            
            # Configuration validation should detect errors
            config_results = startup._validate_configuration()
            
            # Verify configuration errors are detected
            assert config_results['valid'] is False
            assert len(config_results['service_errors']) > 0
            
            # Verify error messages are descriptive
            errors = config_results['service_errors']
            assert any('class_path' in error for error in errors)
    
    def test_startup_validation_service_registration_failures(self):
        """Test startup validation when service registration fails."""
        with patch('importlib.import_module') as mock_import, \
             patch('app.core.service_registration.register_core_services') as mock_register, \
             patch('app.core.service_registration.initialize_core_services'), \
             patch('app.core.dependencies.validate_startup_dependencies') as mock_dep_validation:
            
            # Mock dependencies as available
            mock_import.return_value = Mock(__version__='1.0.0')
            
            # Mock dependency validation as successful
            from app.core.dependencies import ValidationResult
            mock_dep_validation.return_value = ValidationResult(
                is_valid=True,
                missing_required=[],
                missing_optional=[],
                version_conflicts=[],
                warnings=[],
                installation_instructions=""
            )
            
            # Mock service registration failure
            mock_register.side_effect = RuntimeError("Failed to register core services")
            
            startup = ApplicationStartup(self.config_dir)
            
            # Startup should fail due to service registration error
            with pytest.raises(StartupError) as exc_info:
                startup.run_startup_sequence()
            
            assert "Application startup failed" in str(exc_info.value)
            assert "Failed to register core services" in str(exc_info.value)
            
            # Verify error is recorded in validation results
            results = startup.get_validation_results()
            assert results['startup_successful'] is False
            assert 'error' in results
            assert 'Failed to register core services' in results['error']
    
    def test_environment_setup_validation(self):
        """Test quick environment setup validation."""
        with patch('app.core.startup.validate_startup_configuration') as mock_config_val:
            
            # Test successful environment validation
            mock_config_val.return_value = {
                'service_errors': [],
                'dependency_validation': Mock(is_valid=True, missing_required=[])
            }
            
            is_valid = validate_environment_setup(self.config_dir)
            assert is_valid is True
            
            # Test failed environment validation - missing required dependency
            mock_config_val.return_value = {
                'service_errors': [],
                'dependency_validation': Mock(is_valid=False, missing_required=['streamlit'])
            }
            
            is_valid = validate_environment_setup(self.config_dir)
            assert is_valid is False
            
            # Test failed environment validation - service configuration errors
            mock_config_val.return_value = {
                'service_errors': ['Missing class_path for service invalid_service'],
                'dependency_validation': Mock(is_valid=True, missing_required=[])
            }
            
            is_valid = validate_environment_setup(self.config_dir)
            assert is_valid is False
    
    def test_startup_summary_printing(self, capsys):
        """Test startup summary printing functionality."""
        # Create mock results
        mock_results = {
            'startup_successful': True,
            'environment': 'testing',
            'configuration': {
                'services_loaded': 3,
                'dependencies_loaded': 8,
                'service_errors': []
            },
            'dependencies': {
                'valid': True,
                'missing_required': [],
                'missing_optional': ['redis'],
                'version_conflicts': [],
                'warnings': ['Optional dependency redis not available']
            },
            'services': {
                'registered_count': 5,
                'failed_count': 0
            },
            'registry': {
                'valid': True,
                'dependency_errors': [],
                'health_status': {'config': True, 'logger': True, 'cache': True}
            }
        }
        
        print_startup_summary(mock_results)
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Verify summary contains expected information
        assert "Application Startup Report" in output
        assert "✅ Startup Status: SUCCESS" in output
        assert "Environment: testing" in output
        assert "Services loaded: 3" in output
        assert "Dependencies loaded: 8" in output
        assert "Registered: 5" in output
        assert "All required dependencies available" in output
        assert "Missing optional: redis" in output
    
    def test_run_application_startup_function(self):
        """Test the run_application_startup utility function."""
        with patch('importlib.import_module') as mock_import, \
             patch('app.core.service_registration.register_core_services') as mock_register, \
             patch('app.core.service_registration.initialize_core_services') as mock_init:
            
            # Mock successful startup
            mock_import.return_value = Mock(__version__='1.0.0')
            mock_register.return_value = ['config', 'logger', 'cache']
            mock_init.return_value = {'config': True, 'logger': True, 'cache': True}
            
            # Mock registry validation
            registry = get_registry()
            registry.validate_dependencies = Mock(return_value=[])
            registry.list_services = Mock(return_value=['config', 'logger', 'cache'])
            registry.health_check = Mock(return_value={'config': True, 'logger': True, 'cache': True})
            
            # Test successful startup
            results = run_application_startup(self.config_dir, include_dev_deps=True)
            
            assert results['startup_successful'] is True
            assert 'dependencies' in results
            assert 'services' in results
            assert 'registry' in results
            
            # Test failed startup
            with patch.object(ApplicationStartup, 'run_startup_sequence') as mock_startup:
                mock_startup.side_effect = StartupError("Startup failed")
                
                with pytest.raises(StartupError):
                    run_application_startup(self.config_dir)


class TestStartupValidationEdgeCases:
    """Test edge cases and error conditions in startup validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_registry()
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.temp_dir, "config")
        os.makedirs(self.config_dir, exist_ok=True)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        reset_registry()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_startup_with_missing_config_directory(self):
        """Test startup behavior when config directory is missing."""
        non_existent_dir = os.path.join(self.temp_dir, "non_existent")
        
        with patch('app.core.service_config.ServiceConfigLoader.load_configuration') as mock_load:
            # Mock configuration loading to fail for missing directory
            mock_load.side_effect = FileNotFoundError("Configuration directory not found")
            
            startup = ApplicationStartup(non_existent_dir)
            
            # Should handle missing config directory gracefully
            with pytest.raises(StartupError):
                startup.run_startup_sequence()
    
    def test_startup_with_corrupted_config_files(self):
        """Test startup behavior with corrupted configuration files."""
        # Create corrupted YAML file
        with open(os.path.join(self.config_dir, "services.yaml"), 'w') as f:
            f.write("invalid: yaml: content: [unclosed")
        
        with patch('app.core.service_config.ServiceConfigLoader.load_configuration') as mock_load:
            # Mock configuration loading to fail for corrupted files
            mock_load.side_effect = yaml.YAMLError("Invalid YAML syntax")
            
            startup = ApplicationStartup(self.config_dir)
            
            # Should handle corrupted config files gracefully
            with pytest.raises(StartupError):
                startup.run_startup_sequence()
    
    def test_startup_with_empty_config_files(self):
        """Test startup behavior with empty configuration files."""
        # Create empty config files
        with open(os.path.join(self.config_dir, "services.yaml"), 'w') as f:
            f.write("")
        
        with open(os.path.join(self.config_dir, "dependencies.yaml"), 'w') as f:
            f.write("")
        
        with patch('importlib.import_module') as mock_import, \
             patch('app.core.service_registration.register_core_services') as mock_register, \
             patch('app.core.service_registration.initialize_core_services') as mock_init:
            
            # Mock dependencies and services
            mock_import.return_value = Mock(__version__='1.0.0')
            mock_register.return_value = ['config', 'logger', 'cache']
            mock_init.return_value = {'config': True, 'logger': True, 'cache': True}
            
            # Mock registry validation
            registry = get_registry()
            registry.validate_dependencies = Mock(return_value=[])
            registry.list_services = Mock(return_value=['config', 'logger', 'cache'])
            registry.health_check = Mock(return_value={'config': True, 'logger': True, 'cache': True})
            
            startup = ApplicationStartup(self.config_dir)
            
            # Should handle empty config files gracefully
            results = startup.run_startup_sequence()
            
            # Should still succeed with minimal configuration
            assert results['startup_successful'] is True
    
    def test_startup_validation_with_circular_service_dependencies(self):
        """Test startup validation when services have circular dependencies."""
        # Create config with circular dependencies
        services_config = {
            'services': {
                'service_a': {
                    'class_path': 'app.tests.fixtures.mock_services.ServiceA',
                    'enabled': True,
                    'singleton': True,
                    'dependencies': ['service_b'],
                    'config': {}
                },
                'service_b': {
                    'class_path': 'app.tests.fixtures.mock_services.ServiceB',
                    'enabled': True,
                    'singleton': True,
                    'dependencies': ['service_a'],
                    'config': {}
                }
            }
        }
        
        with open(os.path.join(self.config_dir, "services.yaml"), 'w') as f:
            yaml.dump(services_config, f)
        
        # Create minimal dependencies config
        dependencies_config = {'dependencies': {'required': [], 'optional': [], 'development': []}}
        with open(os.path.join(self.config_dir, "dependencies.yaml"), 'w') as f:
            yaml.dump(dependencies_config, f)
        
        with patch('importlib.import_module') as mock_import, \
             patch('app.core.service_registration.register_core_services') as mock_register, \
             patch('app.core.service_registration.initialize_core_services') as mock_init:
            
            # Mock dependencies
            mock_import.return_value = Mock(__version__='1.0.0')
            mock_register.return_value = ['config', 'logger', 'cache']
            mock_init.return_value = {'config': True, 'logger': True, 'cache': True}
            
            # Mock registry validation to detect circular dependencies
            registry = get_registry()
            registry.validate_dependencies = Mock(return_value=['Circular dependency detected: service_a -> service_b -> service_a'])
            registry.list_services = Mock(return_value=['config', 'logger', 'cache', 'service_a', 'service_b'])
            registry.health_check = Mock(return_value={'config': True, 'logger': True, 'cache': True})
            
            startup = ApplicationStartup(self.config_dir)
            results = startup.run_startup_sequence()
            
            # Should complete startup but detect registry issues
            assert results['startup_successful'] is True
            
            # Should detect circular dependency in registry validation
            registry_results = results['registry']
            assert registry_results['valid'] is False
            assert len(registry_results['dependency_errors']) > 0
            assert any('Circular dependency detected' in error for error in registry_results['dependency_errors'])


if __name__ == "__main__":
    """Run integration tests when executed directly."""
    pytest.main([__file__, "-v", "--tb=short"])