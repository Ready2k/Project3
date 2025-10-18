"""AWS Bedrock provider implementation."""

import json
import boto3
import httpx
from typing import Any, Dict, List, Optional
from botocore.exceptions import ClientError

from app.llm.base import LLMProvider
from app.llm.model_discovery import model_discovery
from app.utils.logger import app_logger


class BedrockProvider(LLMProvider):
    """AWS Bedrock LLM provider implementation."""

    def __init__(
        self,
        model: str,
        region: str = "us-east-1",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        bedrock_api_key: Optional[str] = None,
    ):
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
        if self.bedrock_api_key:
            # For Bedrock API keys, we don't use boto3 client
            # Instead, we'll use HTTP requests directly
            app_logger.info(f"Using Bedrock API key authentication for {self.region}")
            return None

        # Use AWS credentials with boto3
        client_kwargs = {"region_name": self.region}
        if self.aws_access_key_id and self.aws_secret_access_key:
            client_kwargs.update(
                {
                    "aws_access_key_id": self.aws_access_key_id,
                    "aws_secret_access_key": self.aws_secret_access_key,
                }
            )
            if self.aws_session_token:
                client_kwargs["aws_session_token"] = self.aws_session_token
            app_logger.info(
                f"Using explicit AWS credentials for Bedrock in {self.region}"
            )
        else:
            app_logger.info(
                f"Using default AWS credentials for Bedrock in {self.region}"
            )

        return boto3.client("bedrock-runtime", **client_kwargs)

    async def generate_short_term_credentials(self) -> Dict[str, str]:
        """Generate short-term AWS credentials using STS."""
        try:
            # Create STS client with current credentials
            sts_client_kwargs = {"region_name": self.region}
            if self.aws_access_key_id and self.aws_secret_access_key:
                sts_client_kwargs.update(
                    {
                        "aws_access_key_id": self.aws_access_key_id,
                        "aws_secret_access_key": self.aws_secret_access_key,
                    }
                )
                if self.aws_session_token:
                    sts_client_kwargs["aws_session_token"] = self.aws_session_token

            sts_client = boto3.client("sts", **sts_client_kwargs)

            # Get session token (valid for 1 hour by default)
            response = sts_client.get_session_token(DurationSeconds=3600)

            credentials = response["Credentials"]
            return {
                "aws_access_key_id": credentials["AccessKeyId"],
                "aws_secret_access_key": credentials["SecretAccessKey"],
                "aws_session_token": credentials["SessionToken"],
                "expiration": credentials["Expiration"].isoformat(),
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
            if self.bedrock_api_key:
                return await self._generate_with_api_key(prompt, **kwargs)
            else:
                return await self._generate_with_boto3(prompt, **kwargs)
        except Exception as e:
            raise RuntimeError(f"Bedrock generation failed: {e}")

    async def _generate_with_api_key(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using Bedrock API key."""
        # Format request for Claude models
        if "claude" in self.model.lower():
            body = {
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": kwargs.get("max_tokens", 1000),
                "temperature": kwargs.get("temperature", 0.7),
                "anthropic_version": "bedrock-2023-05-31",
            }
        else:
            # Generic format for other models
            body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": kwargs.get("max_tokens", 1000),
                    "temperature": kwargs.get("temperature", 0.7),
                },
            }

        # Use HTTP request with API key
        url = f"https://bedrock-runtime.{self.region}.amazonaws.com/model/{self.model}/invoke"
        headers = {
            "Authorization": f"Bearer {self.bedrock_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=body, headers=headers)
            response.raise_for_status()
            response_body = response.json()

        # Parse response based on model type
        if "claude" in self.model.lower():
            return response_body["content"][0]["text"]
        else:
            return response_body.get("results", [{}])[0].get("outputText", "")

    async def _generate_with_boto3(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using boto3 client with AWS credentials."""
        # Format request for Claude models
        if "claude" in self.model.lower():
            body = {
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": kwargs.get("max_tokens", 1000),
                "temperature": kwargs.get("temperature", 0.7),
                "anthropic_version": "bedrock-2023-05-31",
            }
        else:
            # Generic format for other models
            body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": kwargs.get("max_tokens", 1000),
                    "temperature": kwargs.get("temperature", 0.7),
                },
            }

        response = self.client.invoke_model(modelId=self.model, body=json.dumps(body))

        response_body = json.loads(response["body"].read())

        # Parse response based on model type
        if "claude" in self.model.lower():
            return response_body["content"][0]["text"]
        else:
            return response_body.get("results", [{}])[0].get("outputText", "")

    async def test_connection(self) -> bool:
        """Test Bedrock connection."""
        try:
            if self.bedrock_api_key:
                return await self._test_connection_with_api_key()
            else:
                return await self._test_connection_with_boto3()
        except Exception as e:
            app_logger.error(f"Bedrock connection test failed: {e}")
            return False

    async def _test_connection_with_api_key(self) -> bool:
        """Test connection using Bedrock API key."""
        try:
            # Test with a minimal request
            await self.generate("test", max_tokens=1)
            return True
        except Exception as e:
            app_logger.error(f"API key connection test failed: {e}")
            return False

    async def _test_connection_with_boto3(self) -> bool:
        """Test connection using boto3 client."""
        try:
            await self.generate("test", max_tokens=1)
            return True
        except Exception as e:
            app_logger.error(f"AWS credentials connection test failed: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """Get Bedrock model information."""
        return {
            "provider": "bedrock",
            "model": self.model,
            "region": self.region,
            "auth_method": "api_key" if self.bedrock_api_key else "aws_credentials",
        }

    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available Bedrock models."""
        models = await model_discovery.get_available_models(
            "bedrock",
            region=self.region,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            aws_session_token=self.aws_session_token,
            bedrock_api_key=self.bedrock_api_key,
        )
        return [
            {
                "id": model.id,
                "name": model.name,
                "description": model.description,
                "capabilities": model.capabilities,
            }
            for model in models
        ]
