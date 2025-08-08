"""Claude Direct provider implementation."""

from typing import Any, Dict

import anthropic

from app.llm.base import LLMProvider


class ClaudeProvider(LLMProvider):
    """Claude Direct API provider implementation."""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)
    
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using Claude Direct API."""
        try:
            response = self.client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get("max_tokens", 1000),
                temperature=kwargs.get("temperature", 0.7)
            )
            return response.content[0].text
        except Exception as e:
            raise RuntimeError(f"Claude generation failed: {e}")
    
    async def test_connection(self) -> bool:
        """Test Claude API connection."""
        try:
            response = self.client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return len(response.content) > 0
        except Exception:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Claude model information."""
        return {
            "provider": "claude",
            "model": self.model,
            "api_key_set": bool(self.api_key)
        }