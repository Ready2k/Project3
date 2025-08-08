"""AWS Bedrock provider implementation."""

import json
from typing import Any, Dict

import boto3

from app.llm.base import LLMProvider


class BedrockProvider(LLMProvider):
    """AWS Bedrock LLM provider implementation."""
    
    def __init__(self, model: str, region: str = "us-east-1"):
        self.model = model
        self.region = region
        self.client = boto3.client("bedrock-runtime", region_name=region)
    
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using AWS Bedrock."""
        try:
            # Format request for Claude models
            if "claude" in self.model.lower():
                body = {
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": kwargs.get("max_tokens", 1000),
                    "temperature": kwargs.get("temperature", 0.7),
                    "anthropic_version": "bedrock-2023-05-31"
                }
            else:
                # Generic format for other models
                body = {
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": kwargs.get("max_tokens", 1000),
                        "temperature": kwargs.get("temperature", 0.7)
                    }
                }
            
            response = self.client.invoke_model(
                modelId=self.model,
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            
            # Parse response based on model type
            if "claude" in self.model.lower():
                return response_body['content'][0]['text']
            else:
                return response_body.get('results', [{}])[0].get('outputText', '')
                
        except Exception as e:
            raise RuntimeError(f"Bedrock generation failed: {e}")
    
    async def test_connection(self) -> bool:
        """Test Bedrock connection."""
        try:
            await self.generate("test", max_tokens=1)
            return True
        except Exception:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Bedrock model information."""
        return {
            "provider": "bedrock",
            "model": self.model,
            "region": self.region
        }