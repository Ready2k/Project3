import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import yaml

from app.config import Settings, load_settings
from app.utils.redact import PIIRedactor


class TestSettings:
    def test_default_settings(self):
        """Test that default settings are loaded correctly."""
        settings = Settings()
        assert settings.provider == "openai"
        assert settings.model == "gpt-4o"
        assert settings.pattern_library_path == Path("./data/patterns")
        assert settings.export_path == Path("./exports")
        assert settings.timeouts.llm == 20
        assert settings.timeouts.http == 10
        assert settings.logging.level == "INFO"
        assert settings.logging.redact_pii is True

    def test_env_override(self):
        """Test that environment variables override defaults."""
        with patch.dict(os.environ, {
            'PROVIDER': 'bedrock',
            'MODEL': 'claude-3',
            'LOGGING_LEVEL': 'DEBUG'
        }):
            settings = Settings()
            assert settings.provider == "bedrock"
            assert settings.model == "claude-3"
            assert settings.logging.level == "DEBUG"

    def test_yaml_config_loading(self):
        """Test loading configuration from YAML file."""
        config_data = {
            'provider': 'claude',
            'model': 'claude-3-sonnet',
            'constraints': {
                'unavailable_tools': ['selenium', 'playwright']
            },
            'timeouts': {
                'llm': 30,
                'http': 15
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            settings = load_settings(config_path=config_path)
            assert settings.provider == "claude"
            assert settings.model == "claude-3-sonnet"
            assert "selenium" in settings.constraints.unavailable_tools
            assert settings.timeouts.llm == 30
        finally:
            os.unlink(config_path)

    def test_env_precedence_over_yaml(self):
        """Test that environment variables take precedence over YAML."""
        config_data = {'provider': 'claude', 'model': 'claude-3'}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            with patch.dict(os.environ, {'PROVIDER': 'openai'}):
                settings = load_settings(config_path=config_path)
                assert settings.provider == "openai"  # env wins
                assert settings.model == "claude-3"   # yaml value
        finally:
            os.unlink(config_path)


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