import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from app.config.settings import ConfigurationManager, AppConfig, Environment, LogLevel
from app.utils.redact import PIIRedactor


class TestConfigurationManager:
    def test_default_config(self):
        """Test that default configuration is loaded correctly."""
        config = AppConfig()
        assert config.environment == Environment.DEVELOPMENT
        assert config.log_level == LogLevel.INFO
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.database.host == "localhost"
        assert config.database.port == 5432
        assert config.cache.type == "diskcache"
        assert config.ui.page_title == "Automated AI Assessment"

    def test_env_override(self):
        """Test that environment variables override defaults."""
        with patch.dict(os.environ, {
            'AAA_ENVIRONMENT': 'production',
            'AAA_LOG_LEVEL': 'ERROR',
            'AAA_PORT': '9000',
            'AAA_DATABASE__HOST': 'db.example.com'
        }):
            manager = ConfigurationManager()
            result = manager.load_config()
            assert result.is_success
            
            config = result.value
            assert config.environment == Environment.PRODUCTION
            assert config.log_level == LogLevel.ERROR
            assert config.port == 9000
            assert config.database.host == "db.example.com"

    def test_yaml_config_loading(self):
        """Test loading configuration from YAML file."""
        config_data = {
            'environment': 'testing',
            'debug': True,
            'database': {
                'host': 'test-db',
                'port': 5433
            },
            'llm_providers': [
                {
                    'name': 'test_provider',
                    'model': 'test-model',
                    'timeout': 10
                }
            ]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            base_config_path = config_dir / "base.yaml"
            
            with open(base_config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            manager = ConfigurationManager(config_dir)
            result = manager.load_config()
            assert result.is_success
            
            config = result.value
            assert config.environment == Environment.TESTING
            assert config.debug is True
            assert config.database.host == "test-db"
            assert config.database.port == 5433
            assert len(config.llm_providers) == 1
            assert config.llm_providers[0].name == "test_provider"

    def test_env_precedence_over_yaml(self):
        """Test that environment variables take precedence over YAML."""
        config_data = {
            'environment': 'development',
            'port': 8000,
            'database': {'host': 'yaml-db'}
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            base_config_path = config_dir / "base.yaml"
            
            with open(base_config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            with patch.dict(os.environ, {
                'AAA_ENVIRONMENT': 'production',
                'AAA_DATABASE__HOST': 'env-db'
            }):
                manager = ConfigurationManager(config_dir)
                result = manager.load_config()
                assert result.is_success
                
                config = result.value
                assert config.environment == Environment.PRODUCTION  # env wins
                assert config.port == 8000  # yaml value
                assert config.database.host == "env-db"  # env wins

    def test_hierarchical_config_loading(self):
        """Test hierarchical configuration loading (base + environment)."""
        base_config = {
            'debug': False,
            'port': 8000,
            'database': {'host': 'base-db', 'port': 5432}
        }
        
        env_config = {
            'debug': True,
            'database': {'host': 'env-db'}  # port should remain from base
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            
            with open(config_dir / "base.yaml", 'w') as f:
                yaml.dump(base_config, f)
            
            with open(config_dir / "testing.yaml", 'w') as f:
                yaml.dump(env_config, f)
            
            manager = ConfigurationManager(config_dir)
            result = manager.load_config("testing")
            assert result.is_success
            
            config = result.value
            assert config.debug is True  # from env config
            assert config.port == 8000  # from base config
            assert config.database.host == "env-db"  # from env config
            assert config.database.port == 5432  # from base config


class TestPIIRedactor:
    def test_redact_email(self):
        """Test email redaction."""
        redactor = PIIRedactor()
        text = "Contact john.doe@example.com for details"
        result = redactor.redact(text)
        assert "[REDACTED_EMAIL]" in result
        assert "john.doe@example.com" not in result

    def test_redact_phone(self):
        """Test phone number redaction."""
        redactor = PIIRedactor()
        text = "Call me at 555-123-4567"
        result = redactor.redact(text)
        assert "[REDACTED_PHONE]" in result
        assert "555-123-4567" not in result

    def test_redact_api_key(self):
        """Test API key redaction."""
        redactor = PIIRedactor()
        text = "API key: sk-1234567890abcdef1234567890abcdef"
        result = redactor.redact(text)
        assert "[REDACTED_API_KEY]" in result
        assert "sk-1234567890abcdef1234567890abcdef" not in result

    def test_redact_multiple_patterns(self):
        """Test redacting multiple PII patterns in one text."""
        redactor = PIIRedactor()
        text = "Email: user@test.com, Phone: 555-123-4567, Key: abcd1234567890abcdef1234567890ab"
        result = redactor.redact(text)
        assert "[REDACTED_EMAIL]" in result
        assert "[REDACTED_PHONE]" in result
        assert "[REDACTED_API_KEY]" in result
        assert "user@test.com" not in result
        assert "555-123-4567" not in result

    def test_no_redaction_needed(self):
        """Test text with no PII remains unchanged."""
        redactor = PIIRedactor()
        text = "This is a normal sentence with no sensitive data."
        result = redactor.redact(text)
        assert result == text