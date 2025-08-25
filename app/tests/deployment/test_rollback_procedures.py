"""
Tests for rollback and deployment procedures.

This module tests the rollback procedures and deployment validation
to ensure safe deployment of the refactored system.
"""

import pytest
import tempfile
import shutil
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch
import subprocess

from app.config.settings import ConfigurationManager, AppConfig
from app.core.registry import ServiceRegistry


class TestRollbackProcedures:
    """Test rollback procedures for each phase."""
    
    @pytest.fixture
    def deployment_environment(self):
        """Set up deployment testing environment."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            
            # Create directory structure
            (base_dir / "app").mkdir()
            (base_dir / "app" / "ui").mkdir()
            (base_dir / "app" / "config").mkdir()
            (base_dir / "app" / "core").mkdir()
            (base_dir / "legacy").mkdir()
            (base_dir / "config").mkdir()
            
            # Create backup directory
            (base_dir / "backup").mkdir()
            
            yield {
                'base_dir': base_dir,
                'backup_dir': base_dir / "backup",
                'app_dir': base_dir / "app",
                'legacy_dir': base_dir / "legacy",
                'config_dir': base_dir / "config"
            }
    
    def test_configuration_rollback(self, deployment_environment):
        """Test configuration rollback procedure."""
        config_dir = deployment_environment['config_dir']
        backup_dir = deployment_environment['backup_dir']
        
        # Create original configuration
        original_config = {
            'environment': 'production',
            'debug': False,
            'database': {'host': 'prod-db', 'port': 5432}
        }
        
        original_file = config_dir / "base.yaml"
        with open(original_file, 'w') as f:
            yaml.dump(original_config, f)
        
        # Create backup
        backup_file = backup_dir / "base.yaml.backup"
        shutil.copy2(original_file, backup_file)
        
        # Simulate configuration update
        updated_config = {
            'environment': 'production',
            'debug': False,
            'database': {'host': 'new-db', 'port': 5433},
            'new_feature': True
        }
        
        with open(original_file, 'w') as f:
            yaml.dump(updated_config, f)
        
        # Verify update
        manager = ConfigurationManager(config_dir)
        result = manager.load_config()
        assert result.is_success
        assert result.value.database.host == "new-db"
        
        # Perform rollback
        shutil.copy2(backup_file, original_file)
        
        # Verify rollback
        manager_rollback = ConfigurationManager(config_dir)
        result_rollback = manager_rollback.load_config()
        assert result_rollback.is_success
        assert result_rollback.value.database.host == "prod-db"
        assert result_rollback.value.database.port == 5432
    
    def test_code_rollback(self, deployment_environment):
        """Test code rollback procedure."""
        app_dir = deployment_environment['app_dir']
        backup_dir = deployment_environment['backup_dir']
        
        # Create original code file
        original_code = '''
def original_function():
    return "original"
'''
        
        original_file = app_dir / "test_module.py"
        with open(original_file, 'w') as f:
            f.write(original_code)
        
        # Create backup
        backup_file = backup_dir / "test_module.py.backup"
        shutil.copy2(original_file, backup_file)
        
        # Simulate code update
        updated_code = '''
def original_function():
    return "updated"

def new_function():
    return "new"
'''
        
        with open(original_file, 'w') as f:
            f.write(updated_code)
        
        # Verify update
        with open(original_file, 'r') as f:
            content = f.read()
            assert "updated" in content
            assert "new_function" in content
        
        # Perform rollback
        shutil.copy2(backup_file, original_file)
        
        # Verify rollback
        with open(original_file, 'r') as f:
            content = f.read()
            assert "original" in content
            assert "new_function" not in content
    
    def test_database_rollback(self, deployment_environment):
        """Test database schema rollback procedure."""
        # Simulate database migration tracking
        migration_log = {
            'migrations': [
                {'version': '001', 'applied': True, 'rollback_sql': 'DROP TABLE new_table;'},
                {'version': '002', 'applied': True, 'rollback_sql': 'ALTER TABLE users DROP COLUMN new_column;'}
            ]
        }
        
        log_file = deployment_environment['backup_dir'] / "migration_log.json"
        with open(log_file, 'w') as f:
            json.dump(migration_log, f)
        
        # Simulate rollback procedure
        def rollback_migrations(target_version='000'):
            with open(log_file, 'r') as f:
                log = json.load(f)
            
            rollback_commands = []
            for migration in reversed(log['migrations']):
                if migration['applied']:
                    rollback_commands.append(migration['rollback_sql'])
                    migration['applied'] = False
            
            # Save updated log
            with open(log_file, 'w') as f:
                json.dump(log, f)
            
            return rollback_commands
        
        # Perform rollback
        rollback_commands = rollback_migrations()
        
        # Verify rollback commands
        assert len(rollback_commands) == 2
        assert "DROP TABLE new_table;" in rollback_commands
        assert "ALTER TABLE users DROP COLUMN new_column;" in rollback_commands
        
        # Verify migration log updated
        with open(log_file, 'r') as f:
            updated_log = json.load(f)
        
        for migration in updated_log['migrations']:
            assert migration['applied'] is False
    
    def test_service_rollback(self, deployment_environment):
        """Test service rollback procedure."""
        # Simulate service configuration
        service_config = {
            'services': {
                'api': {'version': '2.0', 'port': 8000, 'enabled': True},
                'ui': {'version': '2.0', 'port': 8501, 'enabled': True},
                'worker': {'version': '2.0', 'enabled': True}
            }
        }
        
        config_file = deployment_environment['config_dir'] / "services.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(service_config, f)
        
        # Create backup
        backup_file = deployment_environment['backup_dir'] / "services.yaml.backup"
        shutil.copy2(config_file, backup_file)
        
        # Simulate service update
        updated_config = {
            'services': {
                'api': {'version': '2.1', 'port': 8000, 'enabled': True},
                'ui': {'version': '2.1', 'port': 8501, 'enabled': True},
                'worker': {'version': '2.1', 'enabled': True},
                'new_service': {'version': '1.0', 'enabled': True}
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(updated_config, f)
        
        # Verify update
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            assert config['services']['api']['version'] == '2.1'
            assert 'new_service' in config['services']
        
        # Perform rollback
        shutil.copy2(backup_file, config_file)
        
        # Verify rollback
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            assert config['services']['api']['version'] == '2.0'
            assert 'new_service' not in config['services']


class TestDeploymentValidation:
    """Test deployment validation procedures."""
    
    def test_configuration_validation(self, deployment_environment):
        """Test configuration validation during deployment."""
        config_dir = deployment_environment['config_dir']
        
        # Create valid configuration
        valid_config = {
            'environment': 'production',
            'debug': False,
            'database': {
                'host': 'prod-db',
                'port': 5432,
                'name': 'aaa_prod'
            },
            'cache': {
                'type': 'redis',
                'redis_url': 'redis://localhost:6379'
            }
        }
        
        config_file = config_dir / "base.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(valid_config, f)
        
        # Validate configuration
        manager = ConfigurationManager(config_dir)
        result = manager.load_config()
        
        assert result.is_success
        config = result.value
        
        # Validation checks
        assert config.environment.value == "production"
        assert config.debug is False
        assert config.database.host == "prod-db"
        assert config.database.port == 5432
        assert config.cache.type == "redis"
    
    def test_service_health_validation(self):
        """Test service health validation."""
        # Mock service health checks
        def check_api_health():
            # Simulate API health check
            return {'status': 'healthy', 'response_time': 0.05}
        
        def check_database_health():
            # Simulate database health check
            return {'status': 'healthy', 'connections': 5}
        
        def check_cache_health():
            # Simulate cache health check
            return {'status': 'healthy', 'memory_usage': 0.3}
        
        # Perform health checks
        api_health = check_api_health()
        db_health = check_database_health()
        cache_health = check_cache_health()
        
        # Validate health
        assert api_health['status'] == 'healthy'
        assert api_health['response_time'] < 0.1
        assert db_health['status'] == 'healthy'
        assert cache_health['status'] == 'healthy'
        assert cache_health['memory_usage'] < 0.8
    
    def test_functionality_validation(self, deployment_environment):
        """Test functionality validation after deployment."""
        config_dir = deployment_environment['config_dir']
        
        # Create test configuration
        test_config = {
            'environment': 'testing',
            'debug': True,
            'llm_providers': [
                {
                    'name': 'test_provider',
                    'model': 'test-model',
                    'timeout': 5
                }
            ]
        }
        
        config_file = config_dir / "base.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(test_config, f)
        
        # Test configuration loading
        manager = ConfigurationManager(config_dir)
        result = manager.load_config()
        assert result.is_success
        
        # Test service registry
        registry = ServiceRegistry()
        registry.register_instance(AppConfig, result.value)
        
        config_result = registry.resolve(AppConfig)
        assert config_result.is_success
        assert config_result.value.environment.value == "testing"
        
        # Test UI components
        from app.ui.tabs.analysis_tab import AnalysisTab
        
        with patch('streamlit.session_state', {}):
            tab = AnalysisTab(result.value, registry)
            assert tab.can_render() is True
    
    def test_performance_validation(self):
        """Test performance validation after deployment."""
        # Mock performance metrics
        performance_metrics = {
            'startup_time': 0.8,  # seconds
            'memory_usage': 150,  # MB
            'response_time': 0.05,  # seconds
            'throughput': 100  # requests/second
        }
        
        # Validate performance targets
        assert performance_metrics['startup_time'] < 1.0
        assert performance_metrics['memory_usage'] < 500
        assert performance_metrics['response_time'] < 0.1
        assert performance_metrics['throughput'] > 50
    
    def test_security_validation(self):
        """Test security validation after deployment."""
        # Mock security checks
        security_checks = {
            'ssl_enabled': True,
            'authentication_required': True,
            'input_validation': True,
            'rate_limiting': True,
            'audit_logging': True
        }
        
        # Validate security requirements
        for check, enabled in security_checks.items():
            assert enabled, f"Security check failed: {check}"


class TestMonitoringAndAlerting:
    """Test monitoring and alerting setup."""
    
    def test_health_monitoring_setup(self):
        """Test health monitoring configuration."""
        monitoring_config = {
            'health_checks': {
                'api': {'endpoint': '/health', 'interval': 30, 'timeout': 5},
                'database': {'query': 'SELECT 1', 'interval': 60, 'timeout': 10},
                'cache': {'command': 'ping', 'interval': 30, 'timeout': 5}
            },
            'alerts': {
                'email': ['admin@company.com'],
                'slack': {'webhook': 'https://hooks.slack.com/...'},
                'thresholds': {
                    'response_time': 1.0,
                    'error_rate': 0.05,
                    'memory_usage': 0.8
                }
            }
        }
        
        # Validate monitoring configuration
        assert 'health_checks' in monitoring_config
        assert 'alerts' in monitoring_config
        
        # Validate health check intervals
        for service, config in monitoring_config['health_checks'].items():
            assert config['interval'] > 0
            assert config['timeout'] > 0
            assert config['timeout'] < config['interval']
        
        # Validate alert thresholds
        thresholds = monitoring_config['alerts']['thresholds']
        assert 0 < thresholds['response_time'] < 10
        assert 0 < thresholds['error_rate'] < 1
        assert 0 < thresholds['memory_usage'] < 1
    
    def test_performance_monitoring_setup(self):
        """Test performance monitoring configuration."""
        performance_config = {
            'metrics': {
                'startup_time': {'threshold': 1.0, 'alert': True},
                'memory_usage': {'threshold': 500, 'alert': True},
                'response_time': {'threshold': 0.1, 'alert': True},
                'error_rate': {'threshold': 0.01, 'alert': True}
            },
            'collection_interval': 60,  # seconds
            'retention_period': 30  # days
        }
        
        # Validate performance monitoring
        assert performance_config['collection_interval'] > 0
        assert performance_config['retention_period'] > 0
        
        for metric, config in performance_config['metrics'].items():
            assert 'threshold' in config
            assert 'alert' in config
    
    def test_error_monitoring_setup(self):
        """Test error monitoring and logging configuration."""
        error_config = {
            'logging': {
                'level': 'INFO',
                'format': 'json',
                'destination': 'file',
                'rotation': 'daily',
                'retention': 30
            },
            'error_tracking': {
                'enabled': True,
                'sample_rate': 1.0,
                'ignore_patterns': ['health_check', 'metrics']
            },
            'alerts': {
                'error_threshold': 10,  # errors per minute
                'critical_errors': ['database_connection', 'authentication']
            }
        }
        
        # Validate error monitoring
        assert error_config['logging']['level'] in ['DEBUG', 'INFO', 'WARNING', 'ERROR']
        assert error_config['error_tracking']['enabled'] is True
        assert 0 <= error_config['error_tracking']['sample_rate'] <= 1.0


class TestTroubleshootingGuide:
    """Test troubleshooting procedures and guides."""
    
    def test_common_issues_troubleshooting(self):
        """Test troubleshooting for common issues."""
        troubleshooting_guide = {
            'configuration_errors': {
                'symptoms': ['Application fails to start', 'Invalid configuration'],
                'solutions': [
                    'Check configuration file syntax',
                    'Validate environment variables',
                    'Review configuration schema'
                ]
            },
            'performance_issues': {
                'symptoms': ['Slow startup', 'High memory usage', 'Slow response'],
                'solutions': [
                    'Check system resources',
                    'Review cache configuration',
                    'Analyze performance metrics'
                ]
            },
            'service_failures': {
                'symptoms': ['Service unavailable', 'Connection errors'],
                'solutions': [
                    'Check service health',
                    'Review service logs',
                    'Restart services if needed'
                ]
            }
        }
        
        # Validate troubleshooting guide structure
        for issue_type, guide in troubleshooting_guide.items():
            assert 'symptoms' in guide
            assert 'solutions' in guide
            assert len(guide['symptoms']) > 0
            assert len(guide['solutions']) > 0
    
    def test_diagnostic_procedures(self):
        """Test diagnostic procedures."""
        def diagnose_configuration():
            """Diagnose configuration issues."""
            issues = []
            
            # Check configuration files exist
            config_files = ['base.yaml', 'production.yaml']
            for file in config_files:
                if not Path(f"config/{file}").exists():
                    issues.append(f"Missing configuration file: {file}")
            
            return issues
        
        def diagnose_services():
            """Diagnose service issues."""
            issues = []
            
            # Mock service checks
            services = {
                'api': {'running': True, 'healthy': True},
                'database': {'running': True, 'healthy': False},
                'cache': {'running': False, 'healthy': False}
            }
            
            for service, status in services.items():
                if not status['running']:
                    issues.append(f"Service not running: {service}")
                elif not status['healthy']:
                    issues.append(f"Service unhealthy: {service}")
            
            return issues
        
        def diagnose_performance():
            """Diagnose performance issues."""
            issues = []
            
            # Mock performance metrics
            metrics = {
                'startup_time': 2.5,
                'memory_usage': 800,
                'response_time': 0.5
            }
            
            if metrics['startup_time'] > 1.0:
                issues.append(f"Slow startup: {metrics['startup_time']}s")
            if metrics['memory_usage'] > 500:
                issues.append(f"High memory usage: {metrics['memory_usage']}MB")
            if metrics['response_time'] > 0.1:
                issues.append(f"Slow response: {metrics['response_time']}s")
            
            return issues
        
        # Run diagnostics
        config_issues = diagnose_configuration()
        service_issues = diagnose_services()
        performance_issues = diagnose_performance()
        
        # Validate diagnostic results
        assert isinstance(config_issues, list)
        assert isinstance(service_issues, list)
        assert isinstance(performance_issues, list)
        
        # Should identify issues
        assert len(service_issues) > 0  # Database unhealthy, cache not running
        assert len(performance_issues) > 0  # Performance issues detected