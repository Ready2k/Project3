"""Provider configuration component for LLM provider setup."""

import asyncio
from typing import Dict, List, Optional, Any

import streamlit as st
import httpx

from app.ui.components.base import BaseComponent

# Import logger for error handling
from app.utils.logger import app_logger

# API configuration
API_BASE_URL = "http://localhost:8000"


class ProviderConfigComponent(BaseComponent):
    """Component for LLM provider configuration."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.provider_options = ["openai", "claude", "bedrock", "internal", "fake"]
    
    def render(self, **kwargs) -> Any:
        """Render the provider configuration component."""
        # Initialize provider config if not present
        if 'provider_config' not in st.session_state:
            st.session_state.provider_config = {
                'provider': 'openai',
                'model': 'gpt-4o',
                'api_key': '',
                'endpoint_url': '',
                'region': 'us-east-1'
            }
        
        st.sidebar.header("🔧 Provider Configuration")
        
        # Provider selection
        current_provider = st.sidebar.selectbox(
            "LLM Provider",
            self.provider_options,
            index=self._get_provider_index(),
            key="provider_select"
        )
        
        # Update provider in session state
        if current_provider != st.session_state.provider_config['provider']:
            st.session_state.provider_config['provider'] = current_provider
        
        # Provider-specific configuration
        if current_provider == "openai":
            self._render_openai_config()
        elif current_provider == "claude":
            self._render_claude_config()
        elif current_provider == "bedrock":
            self._render_bedrock_config()
        elif current_provider == "internal":
            self._render_internal_config()
        elif current_provider == "fake":
            self._render_fake_config()
        
        # Model discovery and validation
        self._render_model_discovery(current_provider)
        
        # Configuration validation
        self._render_config_validation()
        
        # Debug options
        self._render_debug_options()
    
    def _get_provider_index(self) -> int:
        """Get the current provider index."""
        current_provider = st.session_state.provider_config.get('provider', 'openai')
        try:
            return self.provider_options.index(current_provider)
        except ValueError:
            return 0
    
    def _render_openai_config(self):
        """Render OpenAI provider configuration."""
        st.sidebar.subheader("OpenAI Configuration")
        
        api_key = st.sidebar.text_input(
            "OpenAI API Key",
            value=st.session_state.provider_config.get('api_key', ''),
            type="password",
            help="Your OpenAI API key",
            key="openai_api_key"
        )
        
        # Check if we have discovered models
        discovered_models = st.session_state.get('discovered_models_openai', [])
        
        if discovered_models:
            # Use discovered models with info buttons
            model_options = [model.get('id', 'unknown') for model in discovered_models]
            current_model = st.session_state.provider_config.get('model', 'gpt-4o')
            current_index = 0
            if current_model in model_options:
                current_index = model_options.index(current_model)
            
            # Model selection with info button
            col1, col2 = st.sidebar.columns([3, 1])
            with col1:
                model = st.selectbox(
                    "Model",
                    model_options,
                    index=current_index,
                    key="openai_model",
                    help="Select from discovered models or use 'Discover Models' to refresh"
                )
            with col2:
                if st.button("ℹ️", key="openai_model_info", help="Model Information"):
                    st.session_state['show_model_info_openai'] = model
            
            # Show model information if requested
            self._render_model_info('openai', discovered_models, model)
            
        else:
            # Use default models
            model = st.sidebar.selectbox(
                "Model",
                ["gpt-4o", "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                index=0,
                key="openai_model",
                help="Default models - use 'Discover Models' to see all available models"
            )
        
        # Update session state
        st.session_state.provider_config.update({
            'api_key': api_key,
            'model': model,
            'endpoint_url': '',
            'region': ''
        })
    
    def _render_claude_config(self):
        """Render Claude provider configuration."""
        st.sidebar.subheader("Claude Configuration")
        
        api_key = st.sidebar.text_input(
            "Anthropic API Key",
            value=st.session_state.provider_config.get('api_key', ''),
            type="password",
            help="Your Anthropic API key",
            key="claude_api_key"
        )
        
        # Check if we have discovered models
        discovered_models = st.session_state.get('discovered_models_claude', [])
        
        if discovered_models:
            # Use discovered models with info buttons
            model_options = [model.get('id', 'unknown') for model in discovered_models]
            current_model = st.session_state.provider_config.get('model', 'claude-3-5-sonnet-20241022')
            current_index = 0
            if current_model in model_options:
                current_index = model_options.index(current_model)
            
            # Model selection with info button
            col1, col2 = st.sidebar.columns([3, 1])
            with col1:
                model = st.selectbox(
                    "Model",
                    model_options,
                    index=current_index,
                    key="claude_model",
                    help="Select from discovered models or use 'Discover Models' to refresh"
                )
            with col2:
                if st.button("ℹ️", key="claude_model_info", help="Model Information"):
                    st.session_state['show_model_info_claude'] = model
            
            # Show model information if requested
            self._render_model_info('claude', discovered_models, model)
            
        else:
            # Use default models
            model = st.sidebar.selectbox(
                "Model",
                ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
                index=0,
                key="claude_model",
                help="Default models - use 'Discover Models' to see all available models"
            )
        
        # Update session state
        st.session_state.provider_config.update({
            'api_key': api_key,
            'model': model,
            'endpoint_url': '',
            'region': ''
        })
    
    def _render_bedrock_config(self):
        """Render AWS Bedrock provider configuration."""
        st.sidebar.subheader("AWS Bedrock Configuration")
        
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            aws_access_key = st.text_input(
                "AWS Access Key",
                value=st.session_state.provider_config.get('aws_access_key_id', ''),
                type="password",
                help="Your AWS Access Key ID",
                key="bedrock_access_key"
            )
        
        with col2:
            aws_secret_key = st.text_input(
                "AWS Secret Key",
                value=st.session_state.provider_config.get('aws_secret_access_key', ''),
                type="password",
                help="Your AWS Secret Access Key",
                key="bedrock_secret_key"
            )
        
        region = st.sidebar.selectbox(
            "AWS Region",
            ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"],
            index=0,
            key="bedrock_region"
        )
        
        # Check if we have discovered models
        discovered_models = st.session_state.get('discovered_models_bedrock', [])
        
        if discovered_models:
            # Use discovered models with info buttons
            model_options = [model.get('id', 'unknown') for model in discovered_models]
            current_model = st.session_state.provider_config.get('model', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
            current_index = 0
            if current_model in model_options:
                current_index = model_options.index(current_model)
            
            # Model selection with info button
            col1, col2 = st.sidebar.columns([3, 1])
            with col1:
                model = st.selectbox(
                    "Model",
                    model_options,
                    index=current_index,
                    key="bedrock_model",
                    help="Select from discovered models or use 'Discover Models' to refresh"
                )
            with col2:
                if st.button("ℹ️", key="bedrock_model_info", help="Model Information"):
                    st.session_state['show_model_info_bedrock'] = model
            
            # Show model information if requested
            self._render_model_info('bedrock', discovered_models, model)
            
        else:
            # Use default models
            model = st.sidebar.selectbox(
                "Model",
                ["anthropic.claude-3-5-sonnet-20241022-v2:0", "anthropic.claude-3-opus-20240229-v1:0", "anthropic.claude-3-sonnet-20240229-v1:0"],
                index=0,
                key="bedrock_model",
                help="Default models - use 'Discover Models' to see all available models"
            )
        
        # Update session state
        st.session_state.provider_config.update({
            'aws_access_key_id': aws_access_key,
            'aws_secret_access_key': aws_secret_key,
            'region': region,
            'model': model,
            'api_key': '',
            'endpoint_url': ''
        })
    
    def _render_internal_config(self):
        """Render internal HTTP provider configuration."""
        st.sidebar.subheader("Internal HTTP Configuration")
        
        endpoint_url = st.sidebar.text_input(
            "Endpoint URL",
            value=st.session_state.provider_config.get('endpoint_url', ''),
            placeholder="http://your-internal-llm:8080/v1/chat/completions",
            help="Your internal LLM endpoint URL",
            key="internal_endpoint"
        )
        
        api_key = st.sidebar.text_input(
            "API Key (Optional)",
            value=st.session_state.provider_config.get('api_key', ''),
            type="password",
            help="API key if required by your internal service",
            key="internal_api_key"
        )
        
        # Check if we have discovered models
        discovered_models = st.session_state.get('discovered_models_internal', [])
        
        if discovered_models:
            # Use discovered models with info buttons
            model_options = [model.get('id', 'unknown') for model in discovered_models]
            current_model = st.session_state.provider_config.get('model', 'internal-model')
            current_index = 0
            if current_model in model_options:
                current_index = model_options.index(current_model)
            
            # Model selection with info button
            col1, col2 = st.sidebar.columns([3, 1])
            with col1:
                model = st.selectbox(
                    "Model",
                    model_options,
                    index=current_index,
                    key="internal_model_select",
                    help="Select from discovered models or use 'Discover Models' to refresh"
                )
            with col2:
                if st.button("ℹ️", key="internal_model_info", help="Model Information"):
                    st.session_state['show_model_info_internal'] = model
            
            # Show model information if requested
            self._render_model_info('internal', discovered_models, model)
            
        else:
            # Use text input for manual entry
            model = st.sidebar.text_input(
                "Model Name",
                value=st.session_state.provider_config.get('model', 'internal-model'),
                placeholder="internal-model",
                help="Model name to use with your internal service - use 'Discover Models' to auto-detect",
                key="internal_model"
            )
        
        # Update session state
        st.session_state.provider_config.update({
            'endpoint_url': endpoint_url,
            'api_key': api_key,
            'model': model,
            'region': ''
        })
    
    def _render_fake_config(self):
        """Render fake provider configuration for testing."""
        st.sidebar.subheader("Fake Provider (Testing)")
        
        st.sidebar.info("🧪 This provider returns mock responses for testing purposes.")
        
        response_type = st.sidebar.selectbox(
            "Response Type",
            ["success", "error", "timeout"],
            index=0,
            help="Type of response to simulate",
            key="fake_response_type"
        )
        
        delay = st.sidebar.slider(
            "Response Delay (seconds)",
            min_value=0,
            max_value=10,
            value=1,
            help="Simulated response delay",
            key="fake_delay"
        )
        
        # Model selection for fake provider
        fake_models = ["fake-success", "fake-error", "fake-timeout"]
        selected_fake_model = st.sidebar.selectbox(
            "Fake Model",
            fake_models,
            index=fake_models.index(f'fake-{response_type}') if f'fake-{response_type}' in fake_models else 0,
            key="fake_model_select",
            help="Select the type of fake response to simulate"
        )
        
        # Update session state
        st.session_state.provider_config.update({
            'model': selected_fake_model,
            'api_key': 'fake-key',
            'endpoint_url': '',
            'region': '',
            'response_type': response_type,
            'delay': delay
        })
    
    def _render_model_discovery(self, provider: str):
        """Render model discovery section."""
        st.sidebar.divider()
        
        # Model discovery section
        col1, col2 = st.sidebar.columns([2, 1])
        
        with col1:
            if provider != "fake":
                if st.button("🔍 Discover Models", key=f"discover_{provider}"):
                    self._discover_models(provider)
            else:
                if st.button("🔍 Test Discovery", key=f"discover_{provider}"):
                    self._discover_models(provider)
        
        with col2:
            # Clear discovered models button
            if st.session_state.get(f'discovered_models_{provider}'):
                if st.button("🗑️", key=f"clear_{provider}", help="Clear discovered models"):
                    if f'discovered_models_{provider}' in st.session_state:
                        del st.session_state[f'discovered_models_{provider}']
                    if f'show_model_info_{provider}' in st.session_state:
                        del st.session_state[f'show_model_info_{provider}']
                    st.rerun()
        
        # Show discovered models count and status
        discovered_models = st.session_state.get(f'discovered_models_{provider}', [])
        if discovered_models:
            st.sidebar.success(f"✅ {len(discovered_models)} models discovered")
        elif provider != "fake":
            st.sidebar.info("💡 Use 'Discover Models' to see all available models")
        
        # Show fake provider info
        if provider == "fake":
            st.sidebar.info("🧪 **Fake Provider Models:**")
            st.sidebar.write("• fake-success - Returns success responses")
            st.sidebar.write("• fake-error - Returns error responses") 
            st.sidebar.write("• fake-timeout - Simulates timeout responses")
        
        # Show model comparison if we have discovered models
        if discovered_models and len(discovered_models) > 1:
            if st.sidebar.button("🔍 Compare Models", key=f"compare_{provider}"):
                st.session_state[f'show_model_comparison_{provider}'] = True
            
            # Show model comparison if requested
            if st.session_state.get(f'show_model_comparison_{provider}'):
                self._render_model_comparison(provider, discovered_models)
    

    
    def _render_config_validation(self):
        """Render configuration validation section."""
        st.sidebar.divider()
        
        if st.sidebar.button("✅ Test Configuration", key="test_config"):
            self._test_configuration()
        
        # Show current configuration status
        if self._is_config_valid():
            st.sidebar.success("✅ Configuration Valid")
        else:
            st.sidebar.warning("⚠️ Configuration Incomplete")
    
    def _discover_models(self, provider: str):
        """Discover available models for the provider."""
        try:
            with st.sidebar:
                with st.spinner(f"Discovering {provider} models..."):
                    # Build request data based on provider configuration
                    request_data = {
                        'provider': provider
                    }
                    
                    # Add provider-specific configuration
                    config = st.session_state.provider_config
                    
                    if provider == "openai":
                        api_key = config.get('api_key', '')
                        if not api_key:
                            st.sidebar.error("❌ API key required for OpenAI model discovery")
                            return
                        request_data['api_key'] = api_key
                    
                    elif provider == "claude":
                        api_key = config.get('api_key', '')
                        if not api_key:
                            st.sidebar.error("❌ API key required for Claude model discovery")
                            return
                        request_data['api_key'] = api_key
                    
                    elif provider == "bedrock":
                        region = config.get('region', 'us-east-1')
                        aws_access_key_id = config.get('aws_access_key_id', '')
                        aws_secret_access_key = config.get('aws_secret_access_key', '')
                        
                        if not aws_access_key_id or not aws_secret_access_key:
                            st.sidebar.error("❌ AWS credentials required for Bedrock model discovery")
                            return
                        
                        request_data.update({
                            'region': region,
                            'aws_access_key_id': aws_access_key_id,
                            'aws_secret_access_key': aws_secret_access_key
                        })
                    
                    elif provider == "internal":
                        endpoint_url = config.get('endpoint_url', '')
                        if not endpoint_url:
                            st.sidebar.error("❌ Endpoint URL required for internal provider model discovery")
                            return
                        
                        request_data.update({
                            'endpoint_url': endpoint_url,
                            'api_key': config.get('api_key', '')
                        })
                    
                    elif provider == "fake":
                        # Fake provider doesn't need additional configuration
                        pass
                    
                    response = asyncio.run(self._make_api_request(
                        "POST",
                        "/providers/models",
                        request_data
                    ))
                    
                    if response.get('ok'):
                        models = response.get('models', [])
                        
                        if models:
                            st.sidebar.success(f"✅ Found {len(models)} models")
                            
                            # Store discovered models in session state
                            st.session_state[f'discovered_models_{provider}'] = models
                            
                            # Trigger a rerun to update the model dropdown in the provider config
                            st.rerun()
                        else:
                            st.sidebar.warning("No models found")
                    else:
                        error_msg = response.get('message', 'Unknown error')
                        st.sidebar.error(f"❌ Model discovery failed: {error_msg}")
                        
        except Exception as e:
            error_msg = str(e)
            st.sidebar.error(f"Model discovery failed: {error_msg}")
            app_logger.error(f"Model discovery failed for {provider}: {error_msg}")
            
            # Provide helpful debugging information
            if "Connection" in error_msg or "timeout" in error_msg.lower():
                st.sidebar.info("💡 Check that the API server is running on http://localhost:8000")
            elif "API key" in error_msg:
                st.sidebar.info("💡 Make sure to enter a valid API key for the selected provider")
            elif "credentials" in error_msg.lower():
                st.sidebar.info("💡 Check your AWS credentials and permissions")
            
            # Show debug info if available
            with st.sidebar.expander("🔍 Debug Information"):
                st.write(f"**Provider:** {provider}")
                st.write(f"**Request Data:** {request_data if 'request_data' in locals() else 'Not available'}")
                st.write(f"**Error Type:** {type(e).__name__}")
                st.write(f"**Error Details:** {error_msg}")
    
    def _test_configuration(self):
        """Test the current provider configuration."""
        try:
            with st.sidebar:
                with st.spinner("Testing configuration..."):
                    # Extract provider config for API call
                    provider_config = st.session_state.provider_config
                    
                    # Build complete request data
                    request_data = {
                        'provider': provider_config.get('provider', 'openai'),
                        'model': provider_config.get('model', 'gpt-4o')
                    }
                    
                    # Add provider-specific fields
                    if provider_config.get('api_key'):
                        request_data['api_key'] = provider_config['api_key']
                    if provider_config.get('endpoint_url'):
                        request_data['endpoint_url'] = provider_config['endpoint_url']
                    if provider_config.get('region'):
                        request_data['region'] = provider_config['region']
                    if provider_config.get('aws_access_key_id'):
                        request_data['aws_access_key_id'] = provider_config['aws_access_key_id']
                    if provider_config.get('aws_secret_access_key'):
                        request_data['aws_secret_access_key'] = provider_config['aws_secret_access_key']
                    
                    response = asyncio.run(self._make_api_request(
                        "POST",
                        "/providers/test",
                        request_data
                    ))
                    
                    if response.get('ok'):
                        st.sidebar.success("✅ Configuration test passed!")
                        st.sidebar.info(f"✨ {response.get('message', 'Connection successful')}")
                        
                        # Show test details if available
                        test_info = response.get('info', {})
                        if test_info:
                            with st.sidebar.expander("Test Details"):
                                st.write(f"**Response Time:** {test_info.get('response_time', 'N/A')}ms")
                                st.write(f"**Model:** {test_info.get('model', 'N/A')}")
                                st.write(f"**Status:** {test_info.get('status', 'N/A')}")
                    else:
                        error_msg = response.get('message', 'Unknown error')
                        st.sidebar.error(f"❌ Configuration test failed: {error_msg}")
                        
        except Exception as e:
            error_msg = str(e)
            st.sidebar.error(f"❌ Configuration test failed: {error_msg}")
            app_logger.error(f"Configuration test failed: {error_msg}")
            
            # Show debug info if available
            if hasattr(e, '__cause__') and e.__cause__:
                app_logger.error(f"Underlying error: {e.__cause__}")
            
            # Provide helpful guidance
            if "Connection" in error_msg or "timeout" in error_msg.lower():
                st.sidebar.info("💡 Check that the API server is running on http://localhost:8000")
            elif "API key" in error_msg:
                st.sidebar.info("💡 Make sure to enter a valid API key for the selected provider")
    
    def _is_config_valid(self) -> bool:
        """Check if the current configuration is valid."""
        config = st.session_state.provider_config
        provider = config.get('provider', '')
        
        if provider == "openai":
            return bool(config.get('api_key') and config.get('model'))
        elif provider == "claude":
            return bool(config.get('api_key') and config.get('model'))
        elif provider == "bedrock":
            return bool(
                config.get('aws_access_key_id') and 
                config.get('aws_secret_access_key') and 
                config.get('region') and 
                config.get('model')
            )
        elif provider == "internal":
            return bool(config.get('endpoint_url') and config.get('model'))
        elif provider == "fake":
            return True
        
        return False
    
    async def _make_api_request(self, method: str, endpoint: str, data: Optional[Dict] = None, timeout: float = 30.0) -> Dict:
        """Make async API request to FastAPI backend."""
        url = f"{API_BASE_URL}{endpoint}"
        
        try:
            app_logger.debug(f"Making {method} request to {url} with data: {data}")
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url)
                elif method.upper() == "POST":
                    response = await client.post(url, json=data)
                elif method.upper() == "PUT":
                    response = await client.put(url, json=data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                app_logger.debug(f"Response status: {response.status_code}")
                
                if response.status_code != 200:
                    error_text = response.text
                    app_logger.error(f"API request failed: {response.status_code} - {error_text}")
                    return {
                        'ok': False,
                        'message': f"API request failed: {response.status_code}",
                        'details': error_text
                    }
                
                result = response.json()
                app_logger.debug(f"API response: {result}")
                return result
                
        except httpx.TimeoutException:
            app_logger.error(f"API request timeout for {method} {url}")
            return {
                'ok': False,
                'message': "Request timeout - check if API server is running",
                'details': f"Timeout after {timeout}s"
            }
        except httpx.ConnectError:
            app_logger.error(f"API connection error for {method} {url}")
            return {
                'ok': False,
                'message': "Connection failed - check if API server is running on http://localhost:8000",
                'details': "Connection refused"
            }
        except Exception as e:
            app_logger.error(f"API request error for {method} {url}: {e}")
            return {
                'ok': False,
                'message': f"Request failed: {str(e)}",
                'details': str(e)
            }
    
    def _render_model_info(self, provider: str, discovered_models: List[Dict], selected_model: str):
        """Render detailed model information."""
        if st.session_state.get(f'show_model_info_{provider}') == selected_model:
            # Find the model info
            model_info = None
            for model in discovered_models:
                if model.get('id') == selected_model:
                    model_info = model
                    break
            
            if model_info:
                with st.sidebar.expander("📊 Model Details", expanded=True):
                    st.write(f"**Model ID:** {model_info.get('id', 'N/A')}")
                    st.write(f"**Name:** {model_info.get('name', 'N/A')}")
                    st.write(f"**Description:** {model_info.get('description', 'No description available')}")
                    
                    context_length = model_info.get('context_length')
                    if context_length:
                        if isinstance(context_length, (int, float)):
                            st.write(f"**Context Length:** {context_length:,} tokens")
                        else:
                            st.write(f"**Context Length:** {context_length}")
                    
                    capabilities = model_info.get('capabilities', [])
                    if capabilities:
                        st.write("**Capabilities:**")
                        for capability in capabilities:
                            st.write(f"  • {capability.title()}")
                    
                    # Additional model metadata
                    if model_info.get('created'):
                        st.write(f"**Created:** {model_info['created']}")
                    
                    if model_info.get('owned_by'):
                        st.write(f"**Owned By:** {model_info['owned_by']}")
                    
                    # Close button
                    if st.button("❌ Close", key=f"close_info_{selected_model}_{provider}"):
                        if f'show_model_info_{provider}' in st.session_state:
                            del st.session_state[f'show_model_info_{provider}']
                        st.rerun()
    
    def _render_model_comparison(self, provider: str, discovered_models: List[Dict]):
        """Render model comparison interface."""
        with st.sidebar.expander("🔍 Model Comparison", expanded=True):
            st.write("**Available Models:**")
            
            for i, model in enumerate(discovered_models[:5]):  # Show first 5 models
                model_id = model.get('id', 'unknown')
                model_name = model.get('name', model_id)
                context_length = model.get('context_length')
                capabilities = model.get('capabilities', [])
                description = model.get('description', 'No description')
                
                st.write(f"**{i+1}. {model_name}**")
                if description and description != 'No description':
                    st.write(f"   {description[:100]}{'...' if len(description) > 100 else ''}")
                
                if context_length:
                    if isinstance(context_length, (int, float)):
                        st.write(f"   📏 Context: {context_length:,} tokens")
                    else:
                        st.write(f"   📏 Context: {context_length}")
                
                if capabilities:
                    caps_str = ', '.join(capabilities[:3])
                    if len(capabilities) > 3:
                        caps_str += f" (+{len(capabilities)-3} more)"
                    st.write(f"   🔧 Capabilities: {caps_str}")
                
                st.write("---")
            
            if len(discovered_models) > 5:
                st.write(f"*... and {len(discovered_models) - 5} more models*")
            
            # Close comparison button
            if st.button("❌ Close Comparison", key=f"close_comparison_{provider}"):
                if f'show_model_comparison_{provider}' in st.session_state:
                    del st.session_state[f'show_model_comparison_{provider}']
                st.rerun()
    
    def _render_debug_options(self):
        """Render debug options section."""
        st.sidebar.divider()
        
        with st.sidebar.expander("🔧 Provider Debug"):
            # Show current configuration
            if st.checkbox("Show Configuration", key="show_config_debug"):
                st.json(st.session_state.provider_config)
            
            # Show discovered models
            current_provider = st.session_state.provider_config.get('provider', 'openai')
            discovered_models = st.session_state.get(f'discovered_models_{current_provider}', [])
            
            if discovered_models and st.checkbox("Show Discovered Models", key="show_models_debug"):
                st.json(discovered_models)
            
            # Clear provider session state
            if st.button("🗑️ Clear Provider Data", key="clear_provider_debug"):
                # Clear provider config
                if 'provider_config' in st.session_state:
                    del st.session_state['provider_config']
                
                # Clear discovered models for all providers
                for provider in self.provider_options:
                    if f'discovered_models_{provider}' in st.session_state:
                        del st.session_state[f'discovered_models_{provider}']
                    if f'show_model_info_{provider}' in st.session_state:
                        del st.session_state[f'show_model_info_{provider}']
                    if f'show_model_comparison_{provider}' in st.session_state:
                        del st.session_state[f'show_model_comparison_{provider}']
                
                st.success("✅ Provider data cleared!")
                st.rerun()
            
            st.info("💡 For system-wide debug options, see System Config → Logging tab")