"""Provider configuration UI component."""

from typing import Dict, Any, Tuple
import streamlit as st
import asyncio
from app.ui.api_client import api_client


class ProviderConfigComponent:
    """Handles LLM provider configuration UI."""

    def __init__(self) -> None:
        self.providers = {
            "fake": {
                "name": "Fake (Testing)",
                "models": ["fake-model"],
                "requires_api_key": False,
                "description": "For testing and development",
            },
            "openai": {
                "name": "OpenAI",
                "models": ["gpt-4o", "gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
                "requires_api_key": True,
                "description": "OpenAI GPT models",
            },
            "claude": {
                "name": "Anthropic Claude",
                "models": ["claude-3-sonnet", "claude-3-haiku", "claude-3-opus"],
                "requires_api_key": True,
                "description": "Anthropic Claude models",
            },
            "bedrock": {
                "name": "AWS Bedrock",
                "models": ["claude-3-sonnet", "claude-3-haiku"],
                "requires_api_key": False,
                "description": "AWS Bedrock hosted models",
            },
        }

    def render_provider_selection(self) -> Dict[str, Any]:
        """Render provider selection UI and return configuration."""
        st.subheader("🔧 LLM Provider Configuration")

        # Provider selection
        provider_keys = list(self.providers.keys())
        provider = st.selectbox(
            "LLM Provider",
            provider_keys,
            format_func=lambda x: self.providers[x]["name"],
            help="Select the LLM provider to use for analysis",
        )

        provider_info = self.providers[provider]
        st.info(f"ℹ️ {provider_info['description']}")

        # Model selection
        models = provider_info["models"]
        model = st.selectbox(
            "Model",
            models,
            help=f"Select the model to use with {provider_info['name']}",
        )

        # Configuration based on provider
        config = {"provider": provider, "model": model}

        if provider == "openai":
            config.update(self._render_openai_config())
        elif provider == "claude":
            config.update(self._render_claude_config())
        elif provider == "bedrock":
            config.update(self._render_bedrock_config())
        elif provider == "fake":
            config.update(self._render_fake_config())

        return config

    def _render_openai_config(self) -> Dict[str, Any]:
        """Render OpenAI-specific configuration."""
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Your OpenAI API key (starts with sk-)",
        )

        with st.expander("🔧 Advanced OpenAI Settings"):
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=0.3,
                step=0.1,
                help="Controls randomness in responses",
            )

            max_tokens = st.number_input(
                "Max Tokens",
                min_value=100,
                max_value=4000,
                value=1000,
                step=100,
                help="Maximum tokens in response",
            )

        return {
            "api_key": api_key,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    def _render_claude_config(self) -> Dict[str, Any]:
        """Render Claude-specific configuration."""
        api_key = st.text_input(
            "Anthropic API Key", type="password", help="Your Anthropic API key"
        )

        with st.expander("🔧 Advanced Claude Settings"):
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.1,
                help="Controls randomness in responses",
            )

            max_tokens = st.number_input(
                "Max Tokens",
                min_value=100,
                max_value=4000,
                value=1000,
                step=100,
                help="Maximum tokens in response",
            )

        return {
            "api_key": api_key,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    def _render_bedrock_config(self) -> Dict[str, Any]:
        """Render Bedrock-specific configuration."""
        st.write("**AWS Bedrock Configuration**")

        auth_method = st.radio(
            "Authentication Method",
            ["AWS Credentials", "Bedrock API Key"],
            help="Choose how to authenticate with AWS Bedrock",
        )

        config = {}

        if auth_method == "AWS Credentials":
            col1, col2 = st.columns(2)

            with col1:
                aws_access_key_id = st.text_input(
                    "AWS Access Key ID", type="password", help="Your AWS access key ID"
                )

                region = st.selectbox(
                    "AWS Region",
                    ["us-east-1", "us-west-2", "eu-west-1", "eu-west-2"],
                    index=0,
                    help="AWS region for Bedrock",
                )

            with col2:
                aws_secret_access_key = st.text_input(
                    "AWS Secret Access Key",
                    type="password",
                    help="Your AWS secret access key",
                )

                aws_session_token = st.text_input(
                    "AWS Session Token (Optional)",
                    type="password",
                    help="Optional session token for temporary credentials",
                )

            config.update(
                {
                    "aws_access_key_id": aws_access_key_id,
                    "aws_secret_access_key": aws_secret_access_key,
                    "aws_session_token": aws_session_token,
                    "region": region,
                }
            )

        else:  # Bedrock API Key
            bedrock_api_key = st.text_input(
                "Bedrock API Key", type="password", help="Your Bedrock API key"
            )

            region = st.selectbox(
                "AWS Region",
                ["us-east-1", "us-west-2", "eu-west-1", "eu-west-2"],
                index=0,
                help="AWS region for Bedrock",
            )

            config.update({"bedrock_api_key": bedrock_api_key, "region": region})

        return config

    def _render_fake_config(self) -> Dict[str, Any]:
        """Render fake provider configuration."""
        st.info(
            "🧪 **Fake Provider**: No configuration needed. This provider returns mock responses for testing."
        )

        with st.expander("🔧 Fake Provider Settings"):
            seed = st.number_input(
                "Random Seed",
                min_value=0,
                max_value=1000,
                value=42,
                help="Seed for reproducible fake responses",
            )

            response_delay = st.slider(
                "Response Delay (seconds)",
                min_value=0.0,
                max_value=5.0,
                value=1.0,
                step=0.5,
                help="Simulate API response delay",
            )

        return {"seed": seed, "response_delay": response_delay}

    def render_connection_test(
        self, config: Dict[str, Any], api_integration: Any
    ) -> bool:
        """Render connection test UI."""
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔗 Test Connection", type="secondary"):
                if config["provider"] != "fake" and config.get("api_key"):
                    return api_integration.test_provider_connection_with_ui_feedback(
                        config
                    )
                elif config["provider"] == "fake":
                    st.success("✅ Fake provider connection successful!")
                    return True
                else:
                    st.warning("⚠️ Please enter API key to test connection")
                    return False

        with col2:
            if st.button("🔍 Discover Models", type="secondary"):
                return self._discover_models(config)

        return False

    def _discover_models(self, config: Dict[str, Any]) -> bool:
        """Discover available models for the provider."""
        provider = config.get("provider")

        if provider == "fake":
            st.info("🧪 Fake provider has predefined models")
            return True

        if not config.get("api_key") and provider in ["openai", "claude"]:
            st.warning("⚠️ Please enter API key to discover models")
            return False

        with st.spinner("🔍 Discovering models..."):
            try:
                # Use asyncio to run the async function
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                result = loop.run_until_complete(api_client.discover_models(config))

                loop.close()

                if result and result.get("ok"):
                    models = result.get("models", [])
                    st.success(f"✅ Discovered {len(models)} models!")

                    # Display discovered models
                    with st.expander("📋 Available Models"):
                        for model in models:
                            st.write(f"**{model.get('name', model.get('id'))}**")
                            if model.get("description"):
                                st.caption(model["description"])
                            if model.get("context_length"):
                                st.caption(
                                    f"Context length: {model['context_length']:,} tokens"
                                )

                    return True
                else:
                    error_msg = (
                        result.get("message", "Unknown error")
                        if result
                        else "Failed to discover models"
                    )
                    st.error(f"❌ {error_msg}")
                    return False

            except Exception as e:
                st.error(f"❌ Error discovering models: {str(e)}")
                return False

    def get_provider_status_info(self, provider: str) -> Dict[str, Any]:
        """Get status information for a provider."""
        provider_info = self.providers.get(provider, {})

        status_info = {
            "name": provider_info.get("name", provider),
            "description": provider_info.get("description", ""),
            "requires_api_key": provider_info.get("requires_api_key", True),
            "models": provider_info.get("models", []),
            "status": "available",  # Could be enhanced with actual status checking
        }

        return status_info

    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate provider configuration."""
        provider = config.get("provider")

        if not provider:
            return False, "Provider not specified"

        if provider not in self.providers:
            return False, f"Unknown provider: {provider}"

        provider_info = self.providers[provider]

        # Check API key requirement
        if provider_info["requires_api_key"] and not config.get("api_key"):
            return False, f"{provider_info['name']} requires an API key"

        # Check model
        model = config.get("model")
        if model and model not in provider_info["models"]:
            return False, f"Model '{model}' not available for {provider_info['name']}"

        # Provider-specific validation
        if provider == "bedrock":
            if not config.get("bedrock_api_key") and not (
                config.get("aws_access_key_id") and config.get("aws_secret_access_key")
            ):
                return False, "Bedrock requires either API key or AWS credentials"

        return True, "Configuration valid"
