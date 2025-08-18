"""Unit tests for proxy handling."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from app.services.proxy_handler import (
    ProxyHandler, 
    ProxyConfig, 
    ProxyValidationResult,
    ProxyTestResult
)


class TestProxyHandler:
    """Test cases for proxy handling."""
    
    def test_init_no_proxy(self):
        """Test proxy handler initialization without proxy."""
        handler = ProxyHandler()
        
        assert handler.proxy_url is None
        assert handler.proxy_config is None
    
    def test_init_with_proxy(self):
        """Test proxy handler initialization with proxy URL."""
        proxy_url = "http://proxy.example.com:8080"
        handler = ProxyHandler(proxy_url=proxy_url)
        
        assert handler.proxy_url == proxy_url
        assert handler.proxy_config is not None
        assert handler.proxy_config.url == proxy_url
    
    def test_parse_proxy_url_basic(self):
        """Test parsing basic proxy URL."""
        handler = ProxyHandler()
        config = handler._parse_proxy_url("http://proxy.example.com:8080")
        
        assert config is not None
        assert config.url == "http://proxy.example.com:8080"
        assert config.username is None
        assert config.password is None
    
    def test_parse_proxy_url_with_auth(self):
        """Test parsing proxy URL with authentication."""
        handler = ProxyHandler()
        config = handler._parse_proxy_url("http://user:pass@proxy.example.com:8080")
        
        assert config is not None
        assert config.url == "http://proxy.example.com:8080"
        assert config.username == "user"
        assert config.password == "pass"
    
    def test_parse_proxy_url_no_hostname(self):
        """Test parsing proxy URL without hostname."""
        handler = ProxyHandler()
        config = handler._parse_proxy_url("http://:8080")
        
        assert config is None
    
    def test_parse_proxy_url_no_port(self):
        """Test parsing proxy URL without port."""
        handler = ProxyHandler()
        config = handler._parse_proxy_url("http://proxy.example.com")
        
        assert config is None
    
    def test_parse_proxy_url_invalid(self):
        """Test parsing invalid proxy URL."""
        handler = ProxyHandler()
        config = handler._parse_proxy_url("invalid-url")
        
        assert config is None
    
    def test_get_httpx_proxy_config_no_proxy(self):
        """Test httpx proxy configuration without proxy."""
        handler = ProxyHandler()
        config = handler.get_httpx_proxy_config()
        
        assert config is None
    
    def test_get_httpx_proxy_config_basic(self):
        """Test httpx proxy configuration with basic proxy."""
        handler = ProxyHandler("http://proxy.example.com:8080")
        config = handler.get_httpx_proxy_config()
        
        assert config is not None
        assert config["http://"] == "http://proxy.example.com:8080"
        assert config["https://"] == "http://proxy.example.com:8080"
    
    def test_get_httpx_proxy_config_with_auth(self):
        """Test httpx proxy configuration with authentication."""
        handler = ProxyHandler("http://user:pass@proxy.example.com:8080")
        config = handler.get_httpx_proxy_config()
        
        assert config is not None
        assert config["http://"] == "http://user:pass@proxy.example.com:8080"
        assert config["https://"] == "http://user:pass@proxy.example.com:8080"
    
    def test_validate_proxy_config_no_proxy(self):
        """Test proxy configuration validation without proxy."""
        handler = ProxyHandler()
        result = handler.validate_proxy_config()
        
        assert result.is_valid is True
        assert "No proxy configured" in result.error_message
    
    def test_validate_proxy_config_invalid_url(self):
        """Test proxy configuration validation with invalid URL."""
        handler = ProxyHandler("invalid-url")
        result = handler.validate_proxy_config()
        
        assert result.is_valid is False
        assert result.error_type == "invalid_proxy_url"
        assert "Invalid proxy URL format" in result.error_message
    
    def test_validate_proxy_config_invalid_scheme(self):
        """Test proxy configuration validation with invalid scheme."""
        handler = ProxyHandler("ftp://proxy.example.com:8080")
        result = handler.validate_proxy_config()
        
        assert result.is_valid is False
        assert result.error_type == "invalid_proxy_scheme"
        assert "http:// or https://" in result.error_message
    
    def test_validate_proxy_config_invalid_port(self):
        """Test proxy configuration validation with invalid port."""
        # Create handler with manually set invalid proxy config
        handler = ProxyHandler()
        handler.proxy_url = "http://proxy.example.com:99999"
        handler.proxy_config = ProxyConfig(url="http://proxy.example.com:99999")
        
        result = handler.validate_proxy_config()
        assert result.is_valid is False
        assert result.error_type == "invalid_proxy_port"
    
    def test_validate_proxy_config_incomplete_auth(self):
        """Test proxy configuration validation with incomplete authentication."""
        handler = ProxyHandler()
        handler.proxy_url = "http://user@proxy.example.com:8080"
        handler.proxy_config = ProxyConfig(
            url="http://proxy.example.com:8080",
            username="user"
            # password is None
        )
        
        result = handler.validate_proxy_config()
        
        assert result.is_valid is False
        assert result.error_type == "incomplete_proxy_auth"
        assert "password is missing" in result.error_message
    
    def test_validate_proxy_config_valid(self):
        """Test proxy configuration validation with valid configuration."""
        handler = ProxyHandler("http://user:pass@proxy.example.com:8080")
        result = handler.validate_proxy_config()
        
        assert result.is_valid is True
        assert result.proxy_config is not None
    
    @pytest.mark.asyncio
    async def test_test_proxy_connectivity_no_proxy(self):
        """Test proxy connectivity test without proxy."""
        handler = ProxyHandler()
        result = await handler.test_proxy_connectivity()
        
        assert result.success is True
        assert result.proxy_used is False
        assert "No proxy configured" in result.error_message
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_test_proxy_connectivity_success(self, mock_client):
        """Test successful proxy connectivity test."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client.return_value = mock_client_instance
        
        handler = ProxyHandler("http://proxy.example.com:8080")
        result = await handler.test_proxy_connectivity()
        
        assert result.success is True
        assert result.proxy_used is True
        assert result.response_time_ms is not None
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_test_proxy_connectivity_http_error(self, mock_client):
        """Test proxy connectivity test with HTTP error."""
        # Mock HTTP error response
        mock_response = Mock()
        mock_response.status_code = 407  # Proxy Authentication Required
        mock_response.text = "Proxy Authentication Required"
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client.return_value = mock_client_instance
        
        handler = ProxyHandler("http://proxy.example.com:8080")
        result = await handler.test_proxy_connectivity()
        
        assert result.success is False
        assert result.proxy_used is True
        assert result.error_type == "proxy_http_error"
        assert "HTTP 407" in result.error_message
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_test_proxy_connectivity_proxy_error(self, mock_client):
        """Test proxy connectivity test with proxy error."""
        import httpx
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = httpx.ProxyError("Proxy connection failed")
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client.return_value = mock_client_instance
        
        handler = ProxyHandler("http://proxy.example.com:8080")
        result = await handler.test_proxy_connectivity()
        
        assert result.success is False
        assert result.proxy_used is True
        assert result.error_type == "proxy_connection_error"
        assert "Proxy connection error" in result.error_message
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_test_proxy_connectivity_timeout(self, mock_client):
        """Test proxy connectivity test with timeout."""
        import httpx
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = httpx.TimeoutException("Request timeout")
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client.return_value = mock_client_instance
        
        handler = ProxyHandler("http://proxy.example.com:8080")
        result = await handler.test_proxy_connectivity()
        
        assert result.success is False
        assert result.proxy_used is True
        assert result.error_type == "proxy_timeout"
        assert "timeout" in result.error_message.lower()
    
    def test_get_proxy_troubleshooting_steps(self):
        """Test proxy troubleshooting steps for different error types."""
        handler = ProxyHandler()
        
        # Test invalid proxy URL
        steps = handler.get_proxy_troubleshooting_steps("invalid_proxy_url")
        assert any("proxy url format" in step.lower() for step in steps)
        
        # Test proxy connection error
        steps = handler.get_proxy_troubleshooting_steps("proxy_connection_error")
        assert any("proxy server" in step.lower() for step in steps)
        
        # Test proxy timeout
        steps = handler.get_proxy_troubleshooting_steps("proxy_timeout")
        assert any("timeout" in step.lower() for step in steps)
        
        # Test unknown error type
        steps = handler.get_proxy_troubleshooting_steps("unknown_error")
        assert len(steps) > 0
    
    def test_suggest_proxy_config_for_error(self):
        """Test proxy configuration suggestions for different error types."""
        handler = ProxyHandler()
        
        # Test invalid proxy URL
        config = handler.suggest_proxy_config_for_error("invalid_proxy_url")
        assert "proxy_url" in config
        
        # Test incomplete proxy auth
        config = handler.suggest_proxy_config_for_error("incomplete_proxy_auth")
        assert "username:password" in config["proxy_url"]
        
        # Test proxy timeout
        config = handler.suggest_proxy_config_for_error("proxy_timeout")
        assert "timeout" in config
        
        # Test proxy connection error
        config = handler.suggest_proxy_config_for_error("proxy_connection_error")
        assert config["proxy_url"] is None
    
    @patch('os.environ.get')
    def test_detect_system_proxy(self, mock_env_get):
        """Test system proxy detection from environment variables."""
        mock_env_get.side_effect = lambda var: {
            'HTTP_PROXY': 'http://proxy.example.com:8080'
        }.get(var)
        
        proxy_url = ProxyHandler.detect_system_proxy()
        
        assert proxy_url == 'http://proxy.example.com:8080'
    
    @patch('os.environ.get')
    def test_detect_system_proxy_none(self, mock_env_get):
        """Test system proxy detection when no proxy is configured."""
        mock_env_get.return_value = None
        
        proxy_url = ProxyHandler.detect_system_proxy()
        
        assert proxy_url is None
    
    def test_is_url_in_no_proxy(self):
        """Test URL matching against no_proxy list."""
        # Test exact match
        assert ProxyHandler.is_url_in_no_proxy(
            "https://internal.company.com", 
            ["internal.company.com"]
        ) is True
        
        # Test wildcard match
        assert ProxyHandler.is_url_in_no_proxy(
            "https://api.internal.company.com", 
            ["*.company.com"]
        ) is True
        
        # Test suffix match
        assert ProxyHandler.is_url_in_no_proxy(
            "https://api.internal.company.com", 
            [".company.com"]
        ) is True
        
        # Test no match
        assert ProxyHandler.is_url_in_no_proxy(
            "https://external.example.com", 
            ["internal.company.com"]
        ) is False
        
        # Test empty no_proxy list
        assert ProxyHandler.is_url_in_no_proxy(
            "https://example.com", 
            []
        ) is False
    
    def test_should_use_proxy_for_url(self):
        """Test proxy usage decision for URLs."""
        # Test no proxy configured
        handler = ProxyHandler()
        assert handler.should_use_proxy_for_url("https://example.com") is False
        
        # Test proxy configured, no no_proxy list
        handler = ProxyHandler("http://proxy.example.com:8080")
        assert handler.should_use_proxy_for_url("https://example.com") is True
        
        # Test proxy configured with no_proxy list
        handler = ProxyHandler("http://proxy.example.com:8080")
        if handler.proxy_config:
            handler.proxy_config.no_proxy = ["internal.company.com"]
        
        assert handler.should_use_proxy_for_url("https://internal.company.com") is False
        assert handler.should_use_proxy_for_url("https://external.example.com") is True
    
    def test_get_proxy_info(self):
        """Test proxy information retrieval."""
        # Test no proxy
        handler = ProxyHandler()
        info = handler.get_proxy_info()
        
        assert info["proxy_enabled"] is False
        
        # Test proxy with authentication
        handler = ProxyHandler("http://user:pass@proxy.example.com:8080")
        info = handler.get_proxy_info()
        
        assert info["proxy_enabled"] is True
        assert info["proxy_host"] == "proxy.example.com"
        assert info["proxy_port"] == 8080
        assert info["proxy_scheme"] == "http"
        assert info["authentication_enabled"] is True
        assert info["username"] == "user"
        assert info["password_configured"] is True


class TestProxyConfig:
    """Test cases for proxy configuration data class."""
    
    def test_proxy_config_creation(self):
        """Test proxy configuration creation."""
        config = ProxyConfig(
            url="http://proxy.example.com:8080",
            username="user",
            password="pass"
        )
        
        assert config.url == "http://proxy.example.com:8080"
        assert config.username == "user"
        assert config.password == "pass"
        assert config.no_proxy is None


class TestProxyValidationResult:
    """Test cases for proxy validation result model."""
    
    def test_proxy_validation_result_success(self):
        """Test proxy validation result for successful validation."""
        result = ProxyValidationResult(
            is_valid=True,
            proxy_config={"http://": "http://proxy.example.com:8080"}
        )
        
        assert result.is_valid is True
        assert result.proxy_config is not None
        assert result.error_message is None
    
    def test_proxy_validation_result_failure(self):
        """Test proxy validation result for failed validation."""
        result = ProxyValidationResult(
            is_valid=False,
            error_message="Invalid proxy configuration",
            error_type="invalid_proxy_url",
            troubleshooting_steps=["Check proxy URL format"]
        )
        
        assert result.is_valid is False
        assert result.error_message == "Invalid proxy configuration"
        assert result.error_type == "invalid_proxy_url"
        assert len(result.troubleshooting_steps) == 1


class TestProxyTestResult:
    """Test cases for proxy test result model."""
    
    def test_proxy_test_result_success(self):
        """Test proxy test result for successful test."""
        result = ProxyTestResult(
            success=True,
            proxy_used=True,
            response_time_ms=150.5
        )
        
        assert result.success is True
        assert result.proxy_used is True
        assert result.response_time_ms == 150.5
        assert result.error_message is None
    
    def test_proxy_test_result_failure(self):
        """Test proxy test result for failed test."""
        result = ProxyTestResult(
            success=False,
            proxy_used=True,
            error_message="Proxy connection failed",
            error_type="proxy_connection_error",
            troubleshooting_steps=["Check proxy server"]
        )
        
        assert result.success is False
        assert result.proxy_used is True
        assert result.error_message == "Proxy connection failed"
        assert result.error_type == "proxy_connection_error"
        assert len(result.troubleshooting_steps) == 1