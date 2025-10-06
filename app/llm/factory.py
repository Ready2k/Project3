"""
LLM Provider Factory

This module provides a factory for creating LLM provider instances with:
- Provider availability checking
- Graceful fallback when providers are unavailable
- Configuration-based provider selection
- Service registry integration
"""

from typing import Any, Dict, List, Optional
import os
import logging
from enum import Enum
from dataclasses import dataclass

from app.llm.base import LLMProvider
from app.core.service import ConfigurableService
from app.core.types import Result, Success, Error
from app.utils.imports import ImportManager


class ProviderType(Enum):
    """Supported LLM provider types."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CLAUDE = "claude"  # Alias for anthropic
    BEDROCK = "bedrock"
    FAKE = "fake"  # For testing


@dataclass
class ProviderInfo:
    """Information about an LLM provider."""
    name: str
    provider_type: ProviderType
    class_path: str
    import_name: str
    required_env_vars: List[str]
    optional_env_vars: List[str]
    dependencies: List[str]
    is_available: bool = False
    error_message: Optional[str] = None


class LLMProviderFactory(ConfigurableService):
    """
    Factory for creating LLM provider instances.
    
    Handles provider availability checking, graceful fallback,
    and configuration-based provider selection.
    """
    
    def __init__(self, config: Dict[str, Any], logger: Optional[Any] = None):
        """
        Initialize the LLM provider factory.
        
        Args:
            config: Factory configuration
            logger: Logger instance (optional)
        """
        super().__init__(config, "llm_provider_factory")
        self._logger = logger or logging.getLogger(__name__)
        self._import_manager = ImportManager()
        self._providers: Dict[str, ProviderInfo] = {}
        self._provider_instances: Dict[str, LLMProvider] = {}
        self._availability_checked = False
        
        # Initialize provider definitions
        self._initialize_provider_definitions()
    
    def _do_initialize(self) -> None:
        """Initialize the factory and check provider availability."""
        self._logger.info("Initializing LLM Provider Factory")
        
        # Check availability of all providers
        self._check_provider_availability()
        
        # Log available providers
        available_providers = [name for name, info in self._providers.items() if info.is_available]
        self._logger.info(f"Available LLM providers: {available_providers}")
        
        if not available_providers:
            self._logger.warning("No LLM providers are available")
    
    def _do_shutdown(self) -> None:
        """Shutdown the factory and clean up provider instances."""
        self._logger.info("Shutting down LLM Provider Factory")
        
        # Shutdown any provider instances that support it
        for provider_name, provider in self._provider_instances.items():
            try:
                if hasattr(provider, 'shutdown'):
                    provider.shutdown()
                    self._logger.debug(f"Shutdown provider: {provider_name}")
            except Exception as e:
                self._logger.error(f"Error shutting down provider {provider_name}: {e}")
        
        self._provider_instances.clear()
    
    def _do_health_check(self) -> bool:
        """Check if at least one provider is available."""
        if not self._availability_checked:
            self._check_provider_availability()
        
        available_count = sum(1 for info in self._providers.values() if info.is_available)
        return available_count > 0
    
    def _initialize_provider_definitions(self) -> None:
        """Initialize the definitions of all supported providers."""
        self._providers = {
            "openai": ProviderInfo(
                name="openai",
                provider_type=ProviderType.OPENAI,
                class_path="app.llm.openai_provider.OpenAIProvider",
                import_name="openai",
                required_env_vars=["OPENAI_API_KEY"],
                optional_env_vars=["OPENAI_ORG_ID", "OPENAI_BASE_URL"],
                dependencies=["openai"]
            ),
            "anthropic": ProviderInfo(
                name="anthropic",
                provider_type=ProviderType.ANTHROPIC,
                class_path="app.llm.claude_provider.ClaudeProvider",
                import_name="anthropic",
                required_env_vars=["ANTHROPIC_API_KEY"],
                optional_env_vars=["ANTHROPIC_BASE_URL"],
                dependencies=["anthropic"]
            ),
            "claude": ProviderInfo(  # Alias for anthropic
                name="claude",
                provider_type=ProviderType.CLAUDE,
                class_path="app.llm.claude_provider.ClaudeProvider",
                import_name="anthropic",
                required_env_vars=["ANTHROPIC_API_KEY"],
                optional_env_vars=["ANTHROPIC_BASE_URL"],
                dependencies=["anthropic"]
            ),
            "bedrock": ProviderInfo(
                name="bedrock",
                provider_type=ProviderType.BEDROCK,
                class_path="app.llm.bedrock_provider.BedrockProvider",
                import_name="boto3",
                required_env_vars=[],  # Can use IAM roles or explicit credentials
                optional_env_vars=[
                    "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN",
                    "AWS_REGION", "BEDROCK_API_KEY"
                ],
                dependencies=["boto3"]
            ),
            "fake": ProviderInfo(
                name="fake",
                provider_type=ProviderType.FAKE,
                class_path="app.llm.fakes.FakeLLMProvider",
                import_name="",  # No import required
                required_env_vars=[],
                optional_env_vars=[],
                dependencies=[]
            )
        }
    
    def _check_provider_availability(self) -> None:
        """Check availability of all providers."""
        self._logger.debug("Checking LLM provider availability")
        
        for provider_name, provider_info in self._providers.items():
            try:
                # Check if required dependencies are available
                if provider_info.dependencies:
                    for dep in provider_info.dependencies:
                        if not self._import_manager.safe_import(dep):
                            provider_info.is_available = False
                            provider_info.error_message = f"Missing dependency: {dep}"
                            continue
                
                # Check environment variables for non-fake providers
                if provider_info.provider_type != ProviderType.FAKE:
                    missing_env_vars = []
                    for env_var in provider_info.required_env_vars:
                        if not os.getenv(env_var):
                            missing_env_vars.append(env_var)
                    
                    if missing_env_vars:
                        provider_info.is_available = False
                        provider_info.error_message = f"Missing environment variables: {missing_env_vars}"
                        continue
                
                # If we get here, provider is available
                provider_info.is_available = True
                provider_info.error_message = None
                self._logger.debug(f"Provider {provider_name} is available")
                
            except Exception as e:
                provider_info.is_available = False
                provider_info.error_message = f"Availability check failed: {e}"
                self._logger.debug(f"Provider {provider_name} is not available: {e}")
        
        self._availability_checked = True
    
    def get_available_providers(self) -> List[str]:
        """
        Get list of available provider names.
        
        Returns:
            List of available provider names
        """
        if not self._availability_checked:
            self._check_provider_availability()
        
        return [name for name, info in self._providers.items() if info.is_available]
    
    def is_provider_available(self, provider_name: str) -> bool:
        """
        Check if a specific provider is available.
        
        Args:
            provider_name: Name of the provider to check
            
        Returns:
            True if provider is available, False otherwise
        """
        if not self._availability_checked:
            self._check_provider_availability()
        
        provider_info = self._providers.get(provider_name)
        return provider_info.is_available if provider_info else False
    
    def get_provider_info(self, provider_name: str) -> Optional[ProviderInfo]:
        """
        Get information about a provider.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            ProviderInfo if provider exists, None otherwise
        """
        return self._providers.get(provider_name)
    
    def create_provider(self, provider_name: Optional[str] = None, **kwargs) -> Result[LLMProvider, str]:
        """
        Create an LLM provider instance.
        
        Args:
            provider_name: Name of the provider to create (uses default if None)
            **kwargs: Additional configuration for the provider
            
        Returns:
            Result containing LLMProvider instance or error message
        """
        # Determine which provider to use
        target_provider = self._determine_provider(provider_name)
        if not target_provider:
            return Error("No available LLM providers found")
        
        # Check if we already have an instance (for singleton behavior)
        cache_key = f"{target_provider}_{hash(frozenset(kwargs.items()))}"
        if cache_key in self._provider_instances:
            return Success(self._provider_instances[cache_key])
        
        # Create new provider instance
        try:
            provider_instance = self._create_provider_instance(target_provider, **kwargs)
            
            # Cache the instance
            self._provider_instances[cache_key] = provider_instance
            
            self._logger.info(f"Created LLM provider: {target_provider}")
            return Success(provider_instance)
            
        except Exception as e:
            error_msg = f"Failed to create provider {target_provider}: {e}"
            self._logger.error(error_msg)
            return Error(error_msg)
    
    def create_provider_with_fallback(self, preferred_provider: Optional[str] = None, **kwargs) -> Result[LLMProvider, str]:
        """
        Create an LLM provider with automatic fallback to available providers.
        
        Args:
            preferred_provider: Preferred provider name
            **kwargs: Additional configuration for the provider
            
        Returns:
            Result containing LLMProvider instance or error message
        """
        # Try preferred provider first
        if preferred_provider:
            result = self.create_provider(preferred_provider, **kwargs)
            if result.is_success():
                return result
            self._logger.warning(f"Preferred provider {preferred_provider} failed, trying fallbacks")
        
        # Try fallback providers
        fallback_providers = self.get_config("fallback_providers", ["anthropic", "openai", "bedrock"])
        for fallback_provider in fallback_providers:
            if fallback_provider != preferred_provider:  # Skip if already tried
                result = self.create_provider(fallback_provider, **kwargs)
                if result.is_success():
                    self._logger.info(f"Using fallback provider: {fallback_provider}")
                    return result
        
        # If all else fails, try fake provider for testing
        if self.is_provider_available("fake"):
            self._logger.warning("All real providers failed, using fake provider")
            return self.create_provider("fake", **kwargs)
        
        return Error("No LLM providers available, including fallbacks")
    
    def _determine_provider(self, provider_name: Optional[str]) -> Optional[str]:
        """
        Determine which provider to use based on configuration and availability.
        
        Args:
            provider_name: Requested provider name
            
        Returns:
            Provider name to use, or None if none available
        """
        if not self._availability_checked:
            self._check_provider_availability()
        
        # If specific provider requested, check if available
        if provider_name:
            if self.is_provider_available(provider_name):
                return provider_name
            else:
                self._logger.warning(f"Requested provider {provider_name} is not available")
                return None
        
        # Use default provider from configuration
        default_provider = self.get_config("default_provider", "openai")
        if self.is_provider_available(default_provider):
            return default_provider
        
        # Fall back to any available provider
        available_providers = self.get_available_providers()
        if available_providers:
            # Prefer real providers over fake
            real_providers = [p for p in available_providers if p != "fake"]
            if real_providers:
                return real_providers[0]
            else:
                return available_providers[0]
        
        return None
    
    def _create_provider_instance(self, provider_name: str, **kwargs) -> LLMProvider:
        """
        Create an instance of the specified provider.
        
        Args:
            provider_name: Name of the provider to create
            **kwargs: Additional configuration for the provider
            
        Returns:
            LLMProvider instance
            
        Raises:
            Exception: If provider creation fails
        """
        provider_info = self._providers.get(provider_name)
        if not provider_info:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        if not provider_info.is_available:
            raise RuntimeError(f"Provider {provider_name} is not available: {provider_info.error_message}")
        
        # Import the provider class
        module_path, class_name = provider_info.class_path.rsplit(".", 1)
        provider_module = self._import_manager.safe_import(module_path)
        if not provider_module:
            raise ImportError(f"Could not import provider module: {module_path}")
        
        provider_class = getattr(provider_module, class_name)
        if not provider_class:
            raise ImportError(f"Could not find provider class: {class_name}")
        
        # Prepare provider configuration
        provider_config = self._prepare_provider_config(provider_name, **kwargs)
        
        # Create provider instance
        try:
            if provider_name == "openai":
                api_key = provider_config.get("api_key", os.getenv("OPENAI_API_KEY"))
                model = provider_config.get("model", "gpt-4o")
                
                # Use enhanced provider for GPT-5 and o1 models
                if model.startswith("gpt-5") or model.startswith("o1"):
                    from app.llm.gpt5_enhanced_provider import GPT5EnhancedProvider
                    self._logger.info(f"Using GPT-5 enhanced provider for model: {model}")
                    return GPT5EnhancedProvider(api_key=api_key, model=model)
                else:
                    return provider_class(api_key=api_key, model=model)
            elif provider_name in ["anthropic", "claude"]:
                return provider_class(
                    api_key=provider_config.get("api_key", os.getenv("ANTHROPIC_API_KEY")),
                    model=provider_config.get("model", "claude-3-5-sonnet-20241022")
                )
            elif provider_name == "bedrock":
                return provider_class(
                    model=provider_config.get("model", "anthropic.claude-3-sonnet-20240229-v1:0"),
                    region=provider_config.get("region", os.getenv("AWS_REGION", "us-east-1")),
                    aws_access_key_id=provider_config.get("aws_access_key_id", os.getenv("AWS_ACCESS_KEY_ID")),
                    aws_secret_access_key=provider_config.get("aws_secret_access_key", os.getenv("AWS_SECRET_ACCESS_KEY")),
                    aws_session_token=provider_config.get("aws_session_token", os.getenv("AWS_SESSION_TOKEN")),
                    bedrock_api_key=provider_config.get("bedrock_api_key", os.getenv("BEDROCK_API_KEY"))
                )
            elif provider_name == "fake":
                return provider_class(**provider_config)
            else:
                # Generic instantiation
                return provider_class(**provider_config)
                
        except Exception as e:
            raise RuntimeError(f"Failed to instantiate provider {provider_name}: {e}") from e
    
    def _prepare_provider_config(self, provider_name: str, **kwargs) -> Dict[str, Any]:
        """
        Prepare configuration for a provider instance.
        
        Args:
            provider_name: Name of the provider
            **kwargs: Additional configuration
            
        Returns:
            Configuration dictionary for the provider
        """
        # Start with factory configuration
        config = self.config.copy()
        
        # Add provider-specific configuration
        provider_config_key = f"{provider_name}_config"
        if provider_config_key in config:
            config.update(config[provider_config_key])
        
        # Override with any provided kwargs
        config.update(kwargs)
        
        # Add common configuration
        config.setdefault("timeout_seconds", self.get_config("timeout_seconds", 30))
        config.setdefault("max_retries", self.get_config("max_retries", 3))
        config.setdefault("retry_delay_seconds", self.get_config("retry_delay_seconds", 1.0))
        
        return config
    
    async def test_provider(self, provider_name: str) -> Result[bool, str]:
        """
        Test a provider's connection and functionality.
        
        Args:
            provider_name: Name of the provider to test
            
        Returns:
            Result indicating success or failure with error message
        """
        try:
            result = self.create_provider(provider_name)
            if result.is_error():
                return Error(f"Failed to create provider: {result.error}")
            
            provider = result.value
            
            # Test the connection
            is_connected = await provider.test_connection()
            if is_connected:
                return Success(True)
            else:
                return Error("Provider connection test failed")
                
        except Exception as e:
            return Error(f"Provider test failed: {e}")
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status information for all providers.
        
        Returns:
            Dictionary mapping provider names to their status information
        """
        if not self._availability_checked:
            self._check_provider_availability()
        
        status = {}
        for provider_name, provider_info in self._providers.items():
            status[provider_name] = {
                "available": provider_info.is_available,
                "error_message": provider_info.error_message,
                "provider_type": provider_info.provider_type.value,
                "required_env_vars": provider_info.required_env_vars,
                "dependencies": provider_info.dependencies,
                "has_instance": any(provider_name in key for key in self._provider_instances.keys())
            }
        
        return status
    
    @property
    def dependencies(self) -> List[str]:
        """Factory dependencies."""
        return ["config", "logger"]