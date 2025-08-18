"""Unit tests for enhanced JiraConfig with Data Center support."""

import pytest
from pydantic import ValidationError

from app.config import JiraConfig, JiraAuthType, JiraDeploymentType


class TestJiraAuthType:
    """Test JiraAuthType enum."""
    
    def test_auth_type_values(self):
        """Test that all expected auth types are available."""
        assert JiraAuthType.API_TOKEN == "api_token"
        assert JiraAuthType.PERSONAL_ACCESS_TOKEN == "pat"
        assert JiraAuthType.SSO == "sso"
        assert JiraAuthType.BASIC == "basic"
    
    def test_auth_type_enum_membership(self):
        """Test enum membership."""
        assert JiraAuthType.API_TOKEN in JiraAuthType
        assert JiraAuthType.PERSONAL_ACCESS_TOKEN in JiraAuthType
        assert JiraAuthType.SSO in JiraAuthType
        assert JiraAuthType.BASIC in JiraAuthType
        
        # Test string values can be used to create enum instances
        assert JiraAuthType("api_token") == JiraAuthType.API_TOKEN
        assert JiraAuthType("pat") == JiraAuthType.PERSONAL_ACCESS_TOKEN
        assert JiraAuthType("sso") == JiraAuthType.SSO
        assert JiraAuthType("basic") == JiraAuthType.BASIC


class TestJiraDeploymentType:
    """Test JiraDeploymentType enum."""
    
    def test_deployment_type_values(self):
        """Test that all expected deployment types are available."""
        assert JiraDeploymentType.CLOUD == "cloud"
        assert JiraDeploymentType.DATA_CENTER == "data_center"
        assert JiraDeploymentType.SERVER == "server"
    
    def test_deployment_type_enum_membership(self):
        """Test enum membership."""
        assert JiraDeploymentType.CLOUD in JiraDeploymentType
        assert JiraDeploymentType.DATA_CENTER in JiraDeploymentType
        assert JiraDeploymentType.SERVER in JiraDeploymentType
        
        # Test string values can be used to create enum instances
        assert JiraDeploymentType("cloud") == JiraDeploymentType.CLOUD
        assert JiraDeploymentType("data_center") == JiraDeploymentType.DATA_CENTER
        assert JiraDeploymentType("server") == JiraDeploymentType.SERVER


class TestJiraConfig:
    """Test JiraConfig model."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = JiraConfig()
        
        assert config.base_url is None
        assert config.deployment_type is None
        assert config.auth_type == JiraAuthType.API_TOKEN
        assert config.email is None
        assert config.api_token is None
        assert config.username is None
        assert config.password is None
        assert config.personal_access_token is None
        assert config.verify_ssl is True
        assert config.ca_cert_path is None
        assert config.proxy_url is None
        assert config.timeout == 30
        assert config.use_sso is False
        assert config.sso_session_cookie is None
        assert config.context_path is None
        assert config.custom_port is None
    
    def test_cloud_api_token_config(self):
        """Test valid Cloud configuration with API token."""
        config = JiraConfig(
            base_url="https://company.atlassian.net",
            deployment_type=JiraDeploymentType.CLOUD,
            auth_type=JiraAuthType.API_TOKEN,
            email="user@company.com",
            api_token="token123"
        )
        
        assert config.base_url == "https://company.atlassian.net"
        assert config.deployment_type == JiraDeploymentType.CLOUD
        assert config.auth_type == JiraAuthType.API_TOKEN
        assert config.email == "user@company.com"
        assert config.api_token == "token123"
        assert config.is_cloud_deployment() is True
        assert config.is_data_center_deployment() is False
    
    def test_data_center_pat_config(self):
        """Test valid Data Center configuration with PAT."""
        config = JiraConfig(
            base_url="https://jira.company.com",
            deployment_type=JiraDeploymentType.DATA_CENTER,
            auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
            personal_access_token="pat_token123",
            context_path="/jira",
            custom_port=8080
        )
        
        assert config.base_url == "https://jira.company.com"
        assert config.deployment_type == JiraDeploymentType.DATA_CENTER
        assert config.auth_type == JiraAuthType.PERSONAL_ACCESS_TOKEN
        assert config.personal_access_token == "pat_token123"
        assert config.context_path == "/jira"
        assert config.custom_port == 8080
        assert config.is_data_center_deployment() is True
        assert config.is_cloud_deployment() is False
    
    def test_data_center_sso_config(self):
        """Test valid Data Center configuration with SSO."""
        config = JiraConfig(
            base_url="https://jira.company.com",
            deployment_type=JiraDeploymentType.DATA_CENTER,
            auth_type=JiraAuthType.SSO,
            use_sso=True,
            sso_session_cookie="JSESSIONID=abc123",
            verify_ssl=False,
            ca_cert_path="/path/to/ca.crt"
        )
        
        assert config.auth_type == JiraAuthType.SSO
        assert config.use_sso is True
        assert config.sso_session_cookie == "JSESSIONID=abc123"
        assert config.verify_ssl is False
        assert config.ca_cert_path == "/path/to/ca.crt"
    
    def test_data_center_basic_auth_config(self):
        """Test valid Data Center configuration with basic auth."""
        config = JiraConfig(
            base_url="https://jira.company.com",
            deployment_type=JiraDeploymentType.DATA_CENTER,
            auth_type=JiraAuthType.BASIC,
            username="jdoe",
            password="password123",
            proxy_url="http://proxy.company.com:8080"
        )
        
        assert config.auth_type == JiraAuthType.BASIC
        assert config.username == "jdoe"
        assert config.password == "password123"
        assert config.proxy_url == "http://proxy.company.com:8080"
    
    def test_base_url_validation(self):
        """Test base URL validation."""
        # Valid URLs
        config1 = JiraConfig(base_url="https://jira.company.com")
        assert config1.base_url == "https://jira.company.com"
        
        config2 = JiraConfig(base_url="http://localhost:8080/")
        assert config2.base_url == "http://localhost:8080"
        
        # Invalid URLs
        with pytest.raises(ValidationError) as exc_info:
            JiraConfig(base_url="jira.company.com")
        assert "Base URL must start with http:// or https://" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            JiraConfig(base_url="ftp://jira.company.com")
        assert "Base URL must start with http:// or https://" in str(exc_info.value)
    
    def test_custom_port_validation(self):
        """Test custom port validation."""
        # Valid ports
        config1 = JiraConfig(custom_port=8080)
        assert config1.custom_port == 8080
        
        config2 = JiraConfig(custom_port=443)
        assert config2.custom_port == 443
        
        # Invalid ports
        with pytest.raises(ValidationError) as exc_info:
            JiraConfig(custom_port=0)
        assert "Custom port must be between 1 and 65535" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            JiraConfig(custom_port=65536)
        assert "Custom port must be between 1 and 65535" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            JiraConfig(custom_port=-1)
        assert "Custom port must be between 1 and 65535" in str(exc_info.value)
    
    def test_timeout_validation(self):
        """Test timeout validation."""
        # Valid timeout
        config = JiraConfig(timeout=60)
        assert config.timeout == 60
        
        # Invalid timeout
        with pytest.raises(ValidationError) as exc_info:
            JiraConfig(timeout=0)
        assert "Timeout must be at least 1 second" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            JiraConfig(timeout=-5)
        assert "Timeout must be at least 1 second" in str(exc_info.value)
    
    def test_validate_auth_config_api_token(self):
        """Test authentication validation for API token."""
        # Valid API token config
        config = JiraConfig(
            auth_type=JiraAuthType.API_TOKEN,
            email="user@company.com",
            api_token="token123"
        )
        errors = config.validate_auth_config()
        assert errors == []
        
        # Missing email
        config = JiraConfig(
            auth_type=JiraAuthType.API_TOKEN,
            api_token="token123"
        )
        errors = config.validate_auth_config()
        assert "Email is required for API token authentication" in errors
        
        # Missing API token
        config = JiraConfig(
            auth_type=JiraAuthType.API_TOKEN,
            email="user@company.com"
        )
        errors = config.validate_auth_config()
        assert "API token is required for API token authentication" in errors
        
        # Missing both
        config = JiraConfig(auth_type=JiraAuthType.API_TOKEN)
        errors = config.validate_auth_config()
        assert len(errors) == 2
        assert "Email is required for API token authentication" in errors
        assert "API token is required for API token authentication" in errors
    
    def test_validate_auth_config_pat(self):
        """Test authentication validation for Personal Access Token."""
        # Valid PAT config
        config = JiraConfig(
            auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
            personal_access_token="pat_token123"
        )
        errors = config.validate_auth_config()
        assert errors == []
        
        # Missing PAT
        config = JiraConfig(auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN)
        errors = config.validate_auth_config()
        assert "Personal access token is required for PAT authentication" in errors
    
    def test_validate_auth_config_basic(self):
        """Test authentication validation for basic auth."""
        # Valid basic auth config
        config = JiraConfig(
            auth_type=JiraAuthType.BASIC,
            username="jdoe",
            password="password123"
        )
        errors = config.validate_auth_config()
        assert errors == []
        
        # Missing username
        config = JiraConfig(
            auth_type=JiraAuthType.BASIC,
            password="password123"
        )
        errors = config.validate_auth_config()
        assert "Username is required for basic authentication" in errors
        
        # Missing password
        config = JiraConfig(
            auth_type=JiraAuthType.BASIC,
            username="jdoe"
        )
        errors = config.validate_auth_config()
        assert "Password is required for basic authentication" in errors
        
        # Missing both
        config = JiraConfig(auth_type=JiraAuthType.BASIC)
        errors = config.validate_auth_config()
        assert len(errors) == 2
        assert "Username is required for basic authentication" in errors
        assert "Password is required for basic authentication" in errors
    
    def test_validate_auth_config_sso(self):
        """Test authentication validation for SSO."""
        # Valid SSO config
        config = JiraConfig(
            auth_type=JiraAuthType.SSO,
            use_sso=True
        )
        errors = config.validate_auth_config()
        assert errors == []
        
        # SSO not enabled
        config = JiraConfig(auth_type=JiraAuthType.SSO)
        errors = config.validate_auth_config()
        assert "SSO must be enabled for SSO authentication" in errors
    
    def test_get_normalized_base_url(self):
        """Test normalized base URL generation."""
        # Base URL only
        config = JiraConfig(base_url="https://jira.company.com")
        assert config.get_normalized_base_url() == "https://jira.company.com"
        
        # With custom port
        config = JiraConfig(
            base_url="https://jira.company.com",
            custom_port=8080
        )
        assert config.get_normalized_base_url() == "https://jira.company.com:8080"
        
        # With context path
        config = JiraConfig(
            base_url="https://jira.company.com",
            context_path="/jira"
        )
        assert config.get_normalized_base_url() == "https://jira.company.com/jira"
        
        # With both custom port and context path
        config = JiraConfig(
            base_url="https://jira.company.com",
            custom_port=8080,
            context_path="/jira"
        )
        assert config.get_normalized_base_url() == "https://jira.company.com:8080/jira"
        
        # Context path with leading/trailing slashes
        config = JiraConfig(
            base_url="https://jira.company.com",
            context_path="/jira/"
        )
        assert config.get_normalized_base_url() == "https://jira.company.com/jira"
        
        # URL already has port (should not add custom port)
        config = JiraConfig(
            base_url="https://jira.company.com:9090",
            custom_port=8080
        )
        assert config.get_normalized_base_url() == "https://jira.company.com:9090"
        
        # No base URL
        config = JiraConfig()
        assert config.get_normalized_base_url() is None
    
    def test_deployment_type_helpers(self):
        """Test deployment type helper methods."""
        # Cloud deployment
        config = JiraConfig(deployment_type=JiraDeploymentType.CLOUD)
        assert config.is_cloud_deployment() is True
        assert config.is_data_center_deployment() is False
        
        # Data Center deployment
        config = JiraConfig(deployment_type=JiraDeploymentType.DATA_CENTER)
        assert config.is_cloud_deployment() is False
        assert config.is_data_center_deployment() is True
        
        # Server deployment
        config = JiraConfig(deployment_type=JiraDeploymentType.SERVER)
        assert config.is_cloud_deployment() is False
        assert config.is_data_center_deployment() is False
        
        # No deployment type
        config = JiraConfig()
        assert config.is_cloud_deployment() is False
        assert config.is_data_center_deployment() is False
    
    def test_backward_compatibility(self):
        """Test that existing configurations still work."""
        # Legacy configuration (Cloud with API token)
        config = JiraConfig(
            base_url="https://company.atlassian.net",
            email="user@company.com",
            api_token="token123"
        )
        
        # Should work with defaults
        assert config.auth_type == JiraAuthType.API_TOKEN
        assert config.deployment_type is None
        assert config.verify_ssl is True
        assert config.timeout == 30
        
        # Should validate successfully
        errors = config.validate_auth_config()
        assert errors == []
    
    def test_network_configuration(self):
        """Test network-related configuration options."""
        config = JiraConfig(
            base_url="https://jira.company.com",
            verify_ssl=False,
            ca_cert_path="/etc/ssl/certs/ca.crt",
            proxy_url="http://proxy.company.com:8080",
            timeout=60
        )
        
        assert config.verify_ssl is False
        assert config.ca_cert_path == "/etc/ssl/certs/ca.crt"
        assert config.proxy_url == "http://proxy.company.com:8080"
        assert config.timeout == 60
    
    def test_enterprise_configuration_example(self):
        """Test a complete enterprise Data Center configuration."""
        config = JiraConfig(
            base_url="https://jira.enterprise.com",
            deployment_type=JiraDeploymentType.DATA_CENTER,
            auth_type=JiraAuthType.SSO,
            use_sso=True,
            sso_session_cookie="JSESSIONID=enterprise_session_123",
            verify_ssl=True,
            ca_cert_path="/etc/ssl/certs/enterprise-ca.crt",
            proxy_url="http://proxy.enterprise.com:8080",
            timeout=45,
            context_path="/jira",
            custom_port=8443
        )
        
        # Validate all fields
        assert config.is_data_center_deployment() is True
        assert config.auth_type == JiraAuthType.SSO
        assert config.use_sso is True
        assert config.verify_ssl is True
        assert config.ca_cert_path == "/etc/ssl/certs/enterprise-ca.crt"
        assert config.proxy_url == "http://proxy.enterprise.com:8080"
        assert config.timeout == 45
        assert config.context_path == "/jira"
        assert config.custom_port == 8443
        
        # Validate authentication
        errors = config.validate_auth_config()
        assert errors == []
        
        # Test normalized URL
        normalized_url = config.get_normalized_base_url()
        assert normalized_url == "https://jira.enterprise.com:8443/jira"