"""Enhanced OpenAI provider with GPT-5 optimizations."""

from typing import Any, Dict

from app.llm.openai_provider import OpenAIProvider
from app.utils.logger import app_logger


class GPT5EnhancedProvider(OpenAIProvider):
    """OpenAI provider with GPT-5 specific optimizations and error handling."""

    def __init__(self, api_key: str, model: str = "gpt-5"):
        super().__init__(api_key, model)

        # GPT-5 specific configurations
        self.is_gpt5_family = model.startswith("gpt-5") or model.startswith("o1")
        self.default_max_tokens = 2000 if self.is_gpt5_family else 1000
        self.max_retry_tokens = 4000
        self.max_retries = 2

    def _get_optimal_token_limit(
        self, prompt: str, requested_tokens: int = None
    ) -> int:
        """Calculate optimal token limit for GPT-5."""

        # Estimate prompt tokens (rough approximation: 1 token ≈ 0.75 words)
        prompt_tokens = len(prompt.split()) * 1.3

        # Use requested tokens or default
        response_tokens = requested_tokens or self.default_max_tokens

        # For GPT-5, ensure we have enough headroom
        if self.is_gpt5_family:
            # GPT-5 has different context limits, be more conservative
            total_tokens = prompt_tokens + response_tokens

            # If total is too high, reduce response tokens
            max_context = 8000  # Conservative limit for GPT-5
            if total_tokens > max_context:
                response_tokens = max(500, max_context - prompt_tokens)
                app_logger.info(
                    f"Adjusted token limit for GPT-5: {response_tokens} (prompt: {prompt_tokens:.0f})"
                )

        return int(response_tokens)

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate with GPT-5 optimizations and retry logic."""

        # Optimize token limit for GPT-5
        if "max_tokens" in kwargs and self.is_gpt5_family:
            optimal_tokens = self._get_optimal_token_limit(prompt, kwargs["max_tokens"])
            kwargs["max_tokens"] = optimal_tokens
        elif self.is_gpt5_family and "max_tokens" not in kwargs:
            # Set default for GPT-5
            kwargs["max_tokens"] = self.default_max_tokens

        # Use enhanced generation with retry logic
        return await self._generate_with_retry(prompt, **kwargs)

    async def _generate_with_retry(self, prompt: str, **kwargs: Any) -> str:
        """Generate with automatic retry on truncation."""

        retry_count = 0
        last_error = None

        while retry_count <= self.max_retries:
            try:
                # Prepare kwargs with correct token parameter
                prepared_kwargs = self._prepare_kwargs(kwargs)

                app_logger.debug(
                    f"GPT-5 generation attempt {retry_count + 1}: {prepared_kwargs}"
                )

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    **prepared_kwargs,
                )

                # Store token usage for audit logging
                if hasattr(response, "usage") and response.usage:
                    self.last_tokens_used = response.usage.total_tokens
                    app_logger.debug(
                        f"GPT-5 token usage: {response.usage.total_tokens}"
                    )
                else:
                    self.last_tokens_used = None

                content = response.choices[0].message.content

                # Check if response was truncated
                if self._is_response_truncated(content, response):
                    raise Exception("Response was truncated due to token limit")

                app_logger.info(
                    f"GPT-5 generation successful on attempt {retry_count + 1}"
                )
                return content

            except Exception as e:
                last_error = e
                error_str = str(e)

                # Check if this is a truncation-related error
                if self._is_truncation_error(error_str):
                    retry_count += 1
                    if retry_count <= self.max_retries:
                        # Increase token limit for retry
                        current_tokens = kwargs.get(
                            "max_tokens", self.default_max_tokens
                        )
                        new_tokens = min(
                            int(current_tokens * 1.5), self.max_retry_tokens
                        )

                        app_logger.warning(
                            f"GPT-5 response truncated, retrying with {new_tokens} tokens (attempt {retry_count + 1})"
                        )
                        kwargs["max_tokens"] = new_tokens
                        continue
                    else:
                        # Max retries reached
                        app_logger.error(
                            f"GPT-5 response truncation after {self.max_retries} retries"
                        )
                        raise RuntimeError(
                            f"GPT-5 response consistently truncated after {self.max_retries} retries. Try using a shorter prompt or higher token limits."
                        )

                # For non-truncation errors, raise immediately
                app_logger.error(f"GPT-5 generation failed: {error_str}")
                raise RuntimeError(f"GPT-5 generation failed: {e}")

        # Should never reach here, but just in case
        raise RuntimeError(f"GPT-5 generation failed after retries: {last_error}")

    def _is_truncation_error(self, error_str: str) -> bool:
        """Check if error indicates response truncation."""
        error_lower = error_str.lower()

        truncation_indicators = [
            "max_tokens",
            "max_completion_tokens",
            "model output limit",
            "finish_reason",
            "length",
            "truncated",
            "could not finish",
            "output limit",
        ]

        return any(indicator in error_lower for indicator in truncation_indicators)

    def _is_response_truncated(self, content: str, response) -> bool:
        """Check if response appears to be truncated."""

        # Check finish reason from API response
        if hasattr(response, "choices") and response.choices:
            choice = response.choices[0]
            finish_reason = getattr(choice, "finish_reason", None)
            if finish_reason == "length":
                app_logger.warning("GPT-5 response truncated (finish_reason: length)")
                return True

        # Heuristic check: if content ends abruptly
        if content and len(content) > 100:
            content_stripped = content.rstrip()

            # Check if ends mid-sentence (doesn't end with proper punctuation)
            if not content_stripped.endswith(
                (".", "!", "?", '"', "'", ")", "]", "}", "`")
            ):
                # Additional check: if it ends with incomplete words or fragments
                last_words = content_stripped.split()[-3:] if content_stripped else []
                if last_words:
                    last_word = last_words[-1]
                    # Check for incomplete words (very short or unusual endings)
                    if len(last_word) < 2 or last_word.endswith((",", ";", ":")):
                        app_logger.warning(
                            "GPT-5 response appears truncated (heuristic check)"
                        )
                        return True

        return False

    async def test_connection_detailed(self) -> tuple[bool, str]:
        """Test connection with GPT-5 specific handling."""
        try:
            # Use appropriate parameter based on model
            token_param = self._get_token_parameter()

            # Use minimal tokens for connection test
            test_kwargs = {token_param: 10}

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                **test_kwargs,
            )

            if len(response.choices) > 0:
                app_logger.info("GPT-5 connection test successful")
                return True, ""
            else:
                return False, "No response choices returned"

        except Exception as e:
            error_str = str(e)

            # Provide specific error messages for common GPT-5 issues
            if "max_tokens" in error_str and "max_completion_tokens" in error_str:
                return (
                    False,
                    f"Parameter error (our fix should handle this): {error_str}",
                )
            elif "not found" in error_str.lower():
                return (
                    False,
                    f"Model '{self.model}' not found. GPT-5 may not be available in your account yet.",
                )
            elif "rate limit" in error_str.lower():
                return False, f"Rate limit exceeded: {error_str}"
            elif "authentication" in error_str.lower():
                return False, f"Authentication failed - check your API key: {error_str}"
            else:
                return False, f"Connection failed: {error_str}"

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information with GPT-5 specific details."""
        info = super().get_model_info()
        info.update(
            {
                "is_gpt5_family": self.is_gpt5_family,
                "default_max_tokens": self.default_max_tokens,
                "max_retry_tokens": self.max_retry_tokens,
                "enhanced_error_handling": True,
            }
        )
        return info
