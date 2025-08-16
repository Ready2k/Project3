"""Dynamic model discovery for LLM providers."""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

import httpx
import openai
import anthropic
import boto3
from botocore.exceptions import ClientError

from app.utils.logger import app_logger


@dataclass
class ModelInfo:
    """Information about an available model."""
    id: str
    name: str
    provider: str
    description: Optional[str] = None
    context_length: Optional[int] = None
    input_cost_per_token: Optional[float] = None
    output_cost_per_token: Optional[float] = None
    supports_streaming: bool = True
    capabilities: List[str] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []


class ModelDiscoveryService:
    """Service for discovering available models from LLM providers."""
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = timedelta(hours=1)  # Cache for 1 hour
    
    def _is_cache_valid(self, provider: str) -> bool:
        """Check if cached models are still valid."""
        if provider not in self.cache:
            return False
        
        cached_at = self.cache[provider].get('cached_at')
        if not cached_at:
            return False
        
        return datetime.now() - cached_at < self.cache_ttl
    
    async def discover_openai_models(self, api_key: str) -> List[ModelInfo]:
        """Discover available OpenAI models."""
        try:
            client = openai.OpenAI(api_key=api_key)
            models_response = client.models.list()
            
            models = []
            # Filter for chat completion models
            chat_models = [
                model for model in models_response.data 
                if any(prefix in model.id for prefix in ['gpt-', 'o1-'])
            ]
            
            # Sort by model ID for consistent ordering
            chat_models.sort(key=lambda x: x.id)
            
            for model in chat_models:
                # Determine context length and capabilities based on model name
                context_length = self._get_openai_context_length(model.id)
                capabilities = self._get_openai_capabilities(model.id)
                
                model_info = ModelInfo(
                    id=model.id,
                    name=model.id,
                    provider="openai",
                    description=f"OpenAI {model.id}",
                    context_length=context_length,
                    capabilities=capabilities
                )
                models.append(model_info)
            
            app_logger.info(f"Discovered {len(models)} OpenAI models")
            return models
            
        except Exception as e:
            app_logger.error(f"Failed to discover OpenAI models: {e}")
            return self._get_fallback_openai_models()
    
    async def discover_claude_models(self, api_key: str) -> List[ModelInfo]:
        """Discover available Claude models."""
        try:
            # Claude doesn't have a models endpoint, so we use known models
            # But we can test connection to validate the API key
            client = anthropic.Anthropic(api_key=api_key)
            
            # Test connection with a minimal request
            try:
                await asyncio.to_thread(
                    client.messages.create,
                    model="claude-3-haiku-20240307",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=1
                )
                connection_valid = True
            except Exception:
                connection_valid = False
            
            if not connection_valid:
                app_logger.warning("Claude API key validation failed")
                return []
            
            models = [
                ModelInfo(
                    id="claude-3-5-sonnet-20241022",
                    name="Claude 3.5 Sonnet",
                    provider="claude",
                    description="Most intelligent model, best for complex tasks",
                    context_length=200000,
                    capabilities=["text", "vision", "code", "analysis"]
                ),
                ModelInfo(
                    id="claude-3-5-haiku-20241022",
                    name="Claude 3.5 Haiku",
                    provider="claude",
                    description="Fastest model, best for simple tasks",
                    context_length=200000,
                    capabilities=["text", "code", "fast"]
                ),
                ModelInfo(
                    id="claude-3-opus-20240229",
                    name="Claude 3 Opus",
                    provider="claude",
                    description="Most powerful model for highly complex tasks",
                    context_length=200000,
                    capabilities=["text", "vision", "code", "analysis", "reasoning"]
                ),
                ModelInfo(
                    id="claude-3-sonnet-20240229",
                    name="Claude 3 Sonnet",
                    provider="claude",
                    description="Balanced model for most tasks",
                    context_length=200000,
                    capabilities=["text", "vision", "code"]
                ),
                ModelInfo(
                    id="claude-3-haiku-20240307",
                    name="Claude 3 Haiku",
                    provider="claude",
                    description="Fast and efficient for simple tasks",
                    context_length=200000,
                    capabilities=["text", "code", "fast"]
                )
            ]
            
            app_logger.info(f"Discovered {len(models)} Claude models")
            return models
            
        except Exception as e:
            app_logger.error(f"Failed to discover Claude models: {e}")
            return []
    
    async def discover_bedrock_models(self, region: str = "us-east-1") -> List[ModelInfo]:
        """Discover available AWS Bedrock models."""
        try:
            client = boto3.client("bedrock", region_name=region)
            
            # List foundation models
            response = await asyncio.to_thread(
                client.list_foundation_models,
                byOutputModality="TEXT"
            )
            
            models = []
            for model in response.get('modelSummaries', []):
                model_id = model.get('modelId', '')
                model_name = model.get('modelName', model_id)
                
                # Filter for text generation models
                if 'TEXT' in model.get('outputModalities', []):
                    capabilities = []
                    if 'claude' in model_id.lower():
                        capabilities = ["text", "code", "analysis"]
                    elif 'titan' in model_id.lower():
                        capabilities = ["text", "embeddings"]
                    elif 'llama' in model_id.lower():
                        capabilities = ["text", "code", "chat"]
                    
                    model_info = ModelInfo(
                        id=model_id,
                        name=model_name,
                        provider="bedrock",
                        description=f"AWS Bedrock {model_name}",
                        capabilities=capabilities
                    )
                    models.append(model_info)
            
            app_logger.info(f"Discovered {len(models)} Bedrock models")
            return models
            
        except ClientError as e:
            app_logger.error(f"AWS Bedrock access error: {e}")
            return []
        except Exception as e:
            app_logger.error(f"Failed to discover Bedrock models: {e}")
            return []
    
    async def discover_internal_models(self, endpoint_url: str, api_key: Optional[str] = None) -> List[ModelInfo]:
        """Discover available models from internal HTTP provider."""
        try:
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Try common endpoints for model listing
                endpoints_to_try = [
                    f"{endpoint_url}/models",
                    f"{endpoint_url}/v1/models",
                    f"{endpoint_url}/api/models"
                ]
                
                for endpoint in endpoints_to_try:
                    try:
                        response = await client.get(endpoint, headers=headers)
                        if response.status_code == 200:
                            data = response.json()
                            
                            models = []
                            # Handle different response formats
                            model_list = data.get('data', data.get('models', []))
                            
                            for model in model_list:
                                if isinstance(model, dict):
                                    model_id = model.get('id', model.get('name', 'unknown'))
                                    model_name = model.get('name', model_id)
                                else:
                                    model_id = model_name = str(model)
                                
                                model_info = ModelInfo(
                                    id=model_id,
                                    name=model_name,
                                    provider="internal",
                                    description=f"Internal model {model_name}",
                                    capabilities=["text", "custom"]
                                )
                                models.append(model_info)
                            
                            app_logger.info(f"Discovered {len(models)} internal models from {endpoint}")
                            return models
                    
                    except Exception:
                        continue
                
                # If no models endpoint found, return a default model
                app_logger.warning("No models endpoint found, using default internal model")
                return [
                    ModelInfo(
                        id="default",
                        name="Default Internal Model",
                        provider="internal",
                        description="Default internal model",
                        capabilities=["text", "custom"]
                    )
                ]
                
        except Exception as e:
            app_logger.error(f"Failed to discover internal models: {e}")
            return []
    
    async def get_available_models(self, provider: str, **kwargs) -> List[ModelInfo]:
        """Get available models for a specific provider."""
        cache_key = f"{provider}_{hash(str(sorted(kwargs.items())))}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['models']
        
        models = []
        
        try:
            if provider == "openai":
                api_key = kwargs.get('api_key')
                if api_key:
                    models = await self.discover_openai_models(api_key)
            
            elif provider == "claude":
                api_key = kwargs.get('api_key')
                if api_key:
                    models = await self.discover_claude_models(api_key)
            
            elif provider == "bedrock":
                region = kwargs.get('region', 'us-east-1')
                models = await self.discover_bedrock_models(region)
            
            elif provider == "internal":
                endpoint_url = kwargs.get('endpoint_url')
                api_key = kwargs.get('api_key')
                if endpoint_url:
                    models = await self.discover_internal_models(endpoint_url, api_key)
            
            # Cache the results
            self.cache[cache_key] = {
                'models': models,
                'cached_at': datetime.now()
            }
            
        except Exception as e:
            app_logger.error(f"Failed to get models for provider {provider}: {e}")
            models = []
        
        return models
    
    def _get_openai_context_length(self, model_id: str) -> Optional[int]:
        """Get context length for OpenAI models."""
        context_lengths = {
            'gpt-4o': 128000,
            'gpt-4o-mini': 128000,
            'gpt-4-turbo': 128000,
            'gpt-4': 8192,
            'gpt-3.5-turbo': 16385,
            'o1-preview': 128000,
            'o1-mini': 128000
        }
        
        for model_prefix, length in context_lengths.items():
            if model_id.startswith(model_prefix):
                return length
        
        return None
    
    def _get_openai_capabilities(self, model_id: str) -> List[str]:
        """Get capabilities for OpenAI models."""
        if model_id.startswith('gpt-4o'):
            return ["text", "vision", "code", "analysis", "multimodal"]
        elif model_id.startswith('gpt-4'):
            return ["text", "code", "analysis", "reasoning"]
        elif model_id.startswith('gpt-3.5'):
            return ["text", "code", "chat"]
        elif model_id.startswith('o1'):
            return ["text", "reasoning", "complex-analysis"]
        else:
            return ["text"]
    
    def _get_fallback_openai_models(self) -> List[ModelInfo]:
        """Get fallback OpenAI models when API discovery fails."""
        return [
            ModelInfo(
                id="gpt-4o",
                name="GPT-4o",
                provider="openai",
                description="Most advanced multimodal model",
                context_length=128000,
                capabilities=["text", "vision", "code", "analysis", "multimodal"]
            ),
            ModelInfo(
                id="gpt-4o-mini",
                name="GPT-4o Mini",
                provider="openai",
                description="Efficient multimodal model",
                context_length=128000,
                capabilities=["text", "vision", "code", "fast"]
            ),
            ModelInfo(
                id="gpt-4-turbo",
                name="GPT-4 Turbo",
                provider="openai",
                description="Advanced reasoning model",
                context_length=128000,
                capabilities=["text", "code", "analysis"]
            ),
            ModelInfo(
                id="gpt-3.5-turbo",
                name="GPT-3.5 Turbo",
                provider="openai",
                description="Fast and efficient model",
                context_length=16385,
                capabilities=["text", "code", "chat"]
            )
        ]
    
    def clear_cache(self, provider: Optional[str] = None):
        """Clear model cache for a specific provider or all providers."""
        if provider:
            keys_to_remove = [key for key in self.cache.keys() if key.startswith(provider)]
            for key in keys_to_remove:
                del self.cache[key]
        else:
            self.cache.clear()


# Global instance
model_discovery = ModelDiscoveryService()