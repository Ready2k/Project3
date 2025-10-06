"""OpenAI provider implementation."""

from typing import Any, Dict, List

import openai

from app.llm.base import LLMProvider
from app.llm.model_discovery import model_discovery


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        self.client = openai.OpenAI(api_key=api_key)
    
    def _get_token_parameter(self) -> str:
        """Get the appropriate token parameter based on model version."""
        # GPT-5 and newer models use max_completion_tokens
        if self.model.startswith("gpt-5") or self.model.startswith("o1"):
            return "max_completion_tokens"
        # Older models use max_tokens
        return "max_tokens"
    
    def _prepare_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare kwargs with correct token parameter."""
        prepared_kwargs = kwargs.copy()
        
        # Handle token parameter conversion
        if "max_tokens" in prepared_kwargs:
            token_param = self._get_token_parameter()
            if token_param == "max_completion_tokens":
                # Convert max_tokens to max_completion_tokens for newer models
                prepared_kwargs["max_completion_tokens"] = prepared_kwargs.pop("max_tokens")
        
        return prepared_kwargs
    

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using OpenAI API with GPT-5 hotfix."""
        # HOTFIX_APPLIED - Aggressive GPT-5 error handling
        
        # For GPT-5, use much higher token limits by default
        if self.model.startswith("gpt-5") or self.model.startswith("o1"):
            if "max_tokens" not in kwargs:
                kwargs["max_tokens"] = 3000  # Much higher default
            elif kwargs["max_tokens"] < 2000:
                kwargs["max_tokens"] = max(kwargs["max_tokens"] * 2, 2000)  # At least double
        
        max_retries = 3
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # Prepare kwargs with correct token parameter
                prepared_kwargs = self._prepare_kwargs(kwargs)
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    **prepared_kwargs
                )
                
                # Store token usage for audit logging
                if hasattr(response, 'usage') and response.usage:
                    self.last_tokens_used = response.usage.total_tokens
                else:
                    self.last_tokens_used = None
                
                content = response.choices[0].message.content
                
                # Check if response was truncated
                if hasattr(response, 'choices') and response.choices:
                    finish_reason = getattr(response.choices[0], 'finish_reason', None)
                    if finish_reason == 'length':
                        raise Exception("Response truncated due to token limit")
                
                return content
                
            except Exception as e:
                error_str = str(e)
                
                # Handle truncation errors aggressively
                if any(indicator in error_str.lower() for indicator in [
                    "max_tokens", "max_completion_tokens", "model output limit", 
                    "finish_reason", "length", "truncated", "could not finish"
                ]):
                    retry_count += 1
                    if retry_count <= max_retries:
                        # Aggressively increase token limit
                        current_tokens = kwargs.get("max_tokens", 1000)
                        new_tokens = min(current_tokens * 2, 8000)  # Double up to 8000
                        
                        print(f"⚠️ GPT-5 truncation detected, retrying with {new_tokens} tokens (attempt {retry_count})")
                        kwargs["max_tokens"] = new_tokens
                        continue
                    else:
                        # Final attempt with maximum tokens
                        print(f"❌ GPT-5 truncation after {max_retries} retries, trying maximum tokens...")
                        kwargs["max_tokens"] = 8000
                        try:
                            prepared_kwargs = self._prepare_kwargs(kwargs)
                            response = self.client.chat.completions.create(
                                model=self.model,
                                messages=[{"role": "user", "content": prompt}],
                                **prepared_kwargs
                            )
                            return response.choices[0].message.content
                        except:
                            pass
                        
                        raise RuntimeError(f"GPT-5 response consistently truncated. Try using a shorter prompt or breaking it into smaller parts. Original error: {e}")
                
                # For non-truncation errors, raise immediately
                raise RuntimeError(f"OpenAI generation failed: {e}")
        
        raise RuntimeError("Unexpected error in generate method")

    async def test_connection(self) -> bool:
        """Test OpenAI API connection."""
        try:
            # Use appropriate parameter based on model
            token_param = self._get_token_parameter()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                **{token_param: 1}
            )
            return len(response.choices) > 0
        except Exception:
            return False
    
    async def test_connection_detailed(self) -> tuple[bool, str]:
        """Test OpenAI API connection with detailed error message."""
        try:
            # Use appropriate parameter based on model
            token_param = self._get_token_parameter()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                **{token_param: 1}
            )
            return len(response.choices) > 0, ""
        except openai.AuthenticationError as e:
            return False, f"Authentication failed - check your API key: {str(e)}"
        except openai.NotFoundError as e:
            return False, f"Model '{self.model}' not found: {str(e)}"
        except openai.RateLimitError as e:
            return False, f"Rate limit exceeded: {str(e)}"
        except openai.APIConnectionError as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get OpenAI model information."""
        return {
            "provider": "openai",
            "model": self.model,
            "api_key_set": bool(self.api_key)
        }
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available OpenAI models."""
        models = await model_discovery.get_available_models("openai", api_key=self.api_key)
        return [
            {
                "id": model.id,
                "name": model.name,
                "description": model.description,
                "context_length": model.context_length,
                "capabilities": model.capabilities
            }
            for model in models
        ]