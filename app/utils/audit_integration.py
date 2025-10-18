"""Integration utilities for audit logging with LLM providers."""

import time
from functools import wraps
from typing import Any, Callable

from .audit import log_llm_call


def audit_llm_call(session_id: str):
    """Decorator to automatically audit LLM provider calls."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args, **kwargs) -> Any:
            start_time = time.time()

            try:
                # Call the original method
                result = await func(self, *args, **kwargs)

                # Calculate latency
                latency_ms = int((time.time() - start_time) * 1000)

                # Extract token count if available in result
                tokens = None
                if hasattr(result, "usage") and hasattr(result.usage, "total_tokens"):
                    tokens = result.usage.total_tokens

                # Get provider info
                provider_info = self.get_model_info()

                # Log the call
                await log_llm_call(
                    session_id=session_id,
                    provider=provider_info.get("provider", "unknown"),
                    model=provider_info.get("model", "unknown"),
                    latency_ms=latency_ms,
                    tokens=tokens,
                )

                return result

            except Exception as e:
                # Still log failed calls
                latency_ms = int((time.time() - start_time) * 1000)
                provider_info = self.get_model_info()

                await log_llm_call(
                    session_id=session_id,
                    provider=provider_info.get("provider", "unknown"),
                    model=provider_info.get("model", "unknown"),
                    latency_ms=latency_ms,
                    tokens=None,
                )

                raise e

        return wrapper

    return decorator


class AuditedLLMProvider:
    """Wrapper class to add audit logging to any LLM provider."""

    def __init__(self, provider, session_id: str):
        self.provider = provider
        self.session_id = session_id

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text with audit logging."""
        start_time = time.time()

        # Extract purpose for audit logging (don't pass to provider)
        purpose = kwargs.pop("purpose", "general")

        try:
            result = await self.provider.generate(prompt, **kwargs)
            latency_ms = int((time.time() - start_time) * 1000)

            # Extract actual token count if available
            tokens = getattr(self.provider, "last_tokens_used", None) or kwargs.get(
                "max_tokens"
            )

            provider_info = self.provider.get_model_info()

            await log_llm_call(
                session_id=self.session_id,
                provider=provider_info.get("provider", "unknown"),
                model=provider_info.get("model", "unknown"),
                latency_ms=latency_ms,
                tokens=tokens,
                prompt=prompt,
                response=result,
                purpose=purpose,
            )

            return result

        except Exception as e:
            # Log failed calls too
            latency_ms = int((time.time() - start_time) * 1000)
            provider_info = self.provider.get_model_info()

            await log_llm_call(
                session_id=self.session_id,
                provider=provider_info.get("provider", "unknown"),
                model=provider_info.get("model", "unknown"),
                latency_ms=latency_ms,
                tokens=None,
                prompt=prompt,
                response="",  # Empty response for failed calls
                purpose=purpose,
            )

            raise e

    async def test_connection(self) -> bool:
        """Test connection without audit logging."""
        return await self.provider.test_connection()

    async def test_connection_detailed(self) -> tuple[bool, str]:
        """Test connection with detailed error message."""
        if hasattr(self.provider, "test_connection_detailed"):
            return await self.provider.test_connection_detailed()
        else:
            success = await self.provider.test_connection()
            return success, "" if success else "Connection test failed"

    def get_model_info(self) -> dict[str, Any]:
        """Get model information from wrapped provider."""
        return self.provider.get_model_info()


def create_audited_provider(provider, session_id: str):
    """Factory function to create an audited version of any LLM provider."""
    return AuditedLLMProvider(provider, session_id)
