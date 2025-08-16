"""Internal HTTP provider implementation."""

from typing import Any, Dict, List

import httpx

from app.llm.base import LLMProvider
from app.llm.model_discovery import model_discovery


class InternalProvider(LLMProvider):
    """Internal HTTP API provider implementation."""
    
    def __init__(self, endpoint_url: str, model: str, api_key: str = None):
        self.endpoint_url = endpoint_url
        self.model = model
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using internal HTTP API."""
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                **kwargs
            }
            
            response = await self.client.post(
                self.endpoint_url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("text", result.get("response", ""))
            
        except Exception as e:
            raise RuntimeError(f"Internal provider generation failed: {e}")
    
    async def test_connection(self) -> bool:
        """Test internal API connection."""
        try:
            await self.generate("test", max_tokens=1)
            return True
        except Exception:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get internal provider model information."""
        return {
            "provider": "internal",
            "model": self.model,
            "endpoint_url": self.endpoint_url,
            "api_key_set": bool(self.api_key)
        }
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available internal models."""
        models = await model_discovery.get_available_models(
            "internal", 
            endpoint_url=self.endpoint_url, 
            api_key=self.api_key
        )
        return [
            {
                "id": model.id,
                "name": model.name,
                "description": model.description,
                "capabilities": model.capabilities
            }
            for model in models
        ]