"""AWS Bedrock provider implementation."""

import json
import boto3
from typing import Any, Dict, List, Optional
from botocore.exceptions import ClientError

from app.llm.base import LLMProvider
from app.llm.model_discovery import model_discovery
from app.utils.logger import app_logger


class BedrockProvider(LLMProvider):
    """AWS Bedrock LLM provider implementation."""
    
    def __init__(self, model: str, region: str = "us-east-1", 
                 aws_access_key_id: Optional[str] = None, 
                 aws_secret_access_key: Optional[str] = None, 
                 aws_session_token: Optional[str] = None,
                 bedrock_api_key: Optional[str] = None):
        self.model = model
        self.region = region
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_session_token = aws_session_token
        self.bedrock_api_key = bedrock_api_key
        
        # Create boto3 client with appropriate authentication
        self.client = self._create_bedrock_client()
    
    def _create_bedrock_client(self):
        """Create Bedrock client with appropriate authentication method."""
        client_kwargs = {"region_name": self.region}
        
        if self.bedrock_api_key:
            # Use Bedrock API key authentication
            # Note: This is a placeholder for when AWS implements API key auth for Bedrock
            # For now, we'll still use AWS credentials but store the API key for future use
            app_logger.info("Bedrock API key provided - storing for future use")
            
        if self.aws_access_key_id and self.aws_secret_access_key:
            client_kwargs.update({
                "aws_access_key_id": self.aws_access_key_id,
                "aws_secret_access_key": self.aws_secret_access_key
            })
            if self.aws_session_token:
                client_kwargs["aws_session_token"] = self.aws_session_token
            app_logger.info(f"Using explicit AWS credentials for Bedrock in {self.region}")
        else:
            app_logger.info(f"Using default AWS credentials for Bedrock in {self.region}")
        
        return boto3.client("bedrock-runtime", **client_kwargs)
    
    async def generate_short_term_credentials(self) -> Dict[str, str]:
        """Generate short-term AWS credentials using STS."""
        try:
            # Create STS client with current credentials
            sts_client_kwargs = {"region_name": self.region}
            if self.aws_access_key_id and self.aws_secret_access_key:
                sts_client_kwargs.update({
                    "aws_access_key_id": self.aws_access_key_id,
                    "aws_secret_access_key": self.aws_secret_access_key
                })
                if self.aws_session_token:
                    sts_client_kwargs["aws_session_token"] = self.aws_session_token
            
            sts_client = boto3.client("sts", **sts_client_kwargs)
            
            # Get session token (valid for 1 hour by default)
            response = sts_client.get_session_token(DurationSeconds=3600)
            
            credentials = response['Credentials']
            return {
                'aws_access_key_id': credentials['AccessKeyId'],
                'aws_secret_access_key': credentials['SecretAccessKey'],
                'aws_session_token': credentials['SessionToken'],
                'expiration': credentials['Expiration'].isoformat()
            }
        except ClientError as e:
            app_logger.error(f"Failed to generate short-term credentials: {e}")
            raise RuntimeError(f"Failed to generate short-term credentials: {e}")
        except Exception as e:
            app_logger.error(f"Unexpected error generating credentials: {e}")
            raise RuntimeError(f"Unexpected error generating credentials: {e}")
    
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
            "region": self.region,
            "auth_method": "api_key" if self.bedrock_api_key else "aws_credentials"
        }
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available Bedrock models."""
        models = await model_discovery.get_available_models(
            "bedrock", 
            region=self.region,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            aws_session_token=self.aws_session_token,
            bedrock_api_key=self.bedrock_api_key
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