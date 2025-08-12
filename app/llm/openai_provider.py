"""OpenAI provider implementation."""

from typing import Any, Dict

import openai

from app.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        self.client = openai.OpenAI(api_key=api_key)
    
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            
            # Store token usage for audit logging
            if hasattr(response, 'usage') and response.usage:
                self.last_tokens_used = response.usage.total_tokens
            else:
                self.last_tokens_used = None
                
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI generation failed: {e}")
    
    async def test_connection(self) -> bool:
        """Test OpenAI API connection."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return len(response.choices) > 0
        except Exception:
            return False
    
    async def test_connection_detailed(self) -> tuple[bool, str]:
        """Test OpenAI API connection with detailed error message."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
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