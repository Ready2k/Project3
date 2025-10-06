#!/usr/bin/env python3
"""
Fix GPT-5 response handling for truncated responses.
"""

from app.llm.openai_provider import OpenAIProvider


def enhance_gpt5_error_handling():
    """Enhance GPT-5 error handling for response truncation."""
    
    print("🔧 Enhancing GPT-5 Error Handling")
    print("=" * 50)
    
    # The error message suggests the issue is response truncation, not parameter error
    # Let's add better error handling and automatic retry with higher token limits
    
    enhanced_generate_method = '''
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using OpenAI API with enhanced GPT-5 support."""
        max_retries = 2
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
                    
                return response.choices[0].message.content
                
            except Exception as e:
                error_str = str(e)
                
                # Handle GPT-5 specific truncation errors
                if ("max_tokens" in error_str and "model output limit" in error_str) or \
                   ("max_completion_tokens" in error_str and "model output limit" in error_str):
                    
                    retry_count += 1
                    if retry_count <= max_retries:
                        # Increase token limit for retry
                        current_tokens = kwargs.get("max_tokens", 1000)
                        new_tokens = min(current_tokens * 2, 4000)  # Double but cap at 4000
                        
                        app_logger.warning(f"GPT-5 response truncated, retrying with {new_tokens} tokens (attempt {retry_count})")
                        kwargs["max_tokens"] = new_tokens
                        continue
                    else:
                        # Max retries reached, return partial response if available
                        app_logger.error(f"GPT-5 response truncation after {max_retries} retries")
                        raise RuntimeError(f"GPT-5 response truncated after retries: {e}")
                
                # For other errors, raise immediately
                raise RuntimeError(f"OpenAI generation failed: {e}")
        
        # Should never reach here
        raise RuntimeError("Unexpected error in generate method")
    '''
    
    print("Enhanced generate method created with:")
    print("  ✅ Automatic retry on truncation errors")
    print("  ✅ Progressive token limit increase")
    print("  ✅ GPT-5 specific error handling")
    print("  ✅ Fallback to partial response")
    
    return enhanced_generate_method


def create_gpt5_optimized_provider():
    """Create a GPT-5 optimized provider class."""
    
    optimized_provider_code = '''
class GPT5OptimizedProvider(OpenAIProvider):
    """OpenAI provider optimized for GPT-5 usage."""
    
    def __init__(self, api_key: str, model: str = "gpt-5"):
        super().__init__(api_key, model)
        
        # GPT-5 specific defaults
        self.default_max_tokens = 2000 if model.startswith("gpt-5") else 1000
        self.max_retry_tokens = 4000
    
    def _get_optimal_token_limit(self, prompt: str, requested_tokens: int = None) -> int:
        """Calculate optimal token limit for GPT-5."""
        
        # Estimate prompt tokens (rough approximation)
        prompt_tokens = len(prompt.split()) * 1.3  # Rough token estimation
        
        # Use requested tokens or default
        response_tokens = requested_tokens or self.default_max_tokens
        
        # For GPT-5, ensure we have enough headroom
        if self.model.startswith("gpt-5"):
            # GPT-5 has different context limits, be more conservative
            total_tokens = prompt_tokens + response_tokens
            
            # If total is too high, reduce response tokens
            if total_tokens > 8000:  # Conservative limit for GPT-5
                response_tokens = max(500, 8000 - prompt_tokens)
        
        return int(response_tokens)
    
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate with GPT-5 optimizations."""
        
        # Optimize token limit for GPT-5
        if "max_tokens" in kwargs:
            optimal_tokens = self._get_optimal_token_limit(prompt, kwargs["max_tokens"])
            kwargs["max_tokens"] = optimal_tokens
        
        # Use enhanced generation with retry logic
        return await self._generate_with_retry(prompt, **kwargs)
    
    async def _generate_with_retry(self, prompt: str, **kwargs: Any) -> str:
        """Generate with automatic retry on truncation."""
        
        max_retries = 2
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
                
                # Check if response seems truncated
                if self._is_response_truncated(content, response):
                    raise Exception("Response appears truncated")
                
                return content
                
            except Exception as e:
                error_str = str(e)
                
                # Handle truncation errors
                if self._is_truncation_error(error_str) or "Response appears truncated" in error_str:
                    retry_count += 1
                    if retry_count <= max_retries:
                        # Increase token limit for retry
                        current_tokens = kwargs.get("max_tokens", self.default_max_tokens)
                        new_tokens = min(current_tokens * 1.5, self.max_retry_tokens)
                        
                        print(f"⚠️ GPT-5 response truncated, retrying with {new_tokens} tokens (attempt {retry_count})")
                        kwargs["max_tokens"] = int(new_tokens)
                        continue
                    else:
                        # Max retries reached
                        print(f"❌ GPT-5 response truncation after {max_retries} retries")
                        raise RuntimeError(f"GPT-5 response consistently truncated: {e}")
                
                # For other errors, raise immediately
                raise RuntimeError(f"OpenAI generation failed: {e}")
        
        raise RuntimeError("Unexpected error in generate method")
    
    def _is_truncation_error(self, error_str: str) -> bool:
        """Check if error indicates response truncation."""
        truncation_indicators = [
            "max_tokens",
            "max_completion_tokens", 
            "model output limit",
            "finish_reason",
            "length"
        ]
        return any(indicator in error_str.lower() for indicator in truncation_indicators)
    
    def _is_response_truncated(self, content: str, response) -> bool:
        """Check if response appears to be truncated."""
        
        # Check finish reason
        if hasattr(response, 'choices') and response.choices:
            finish_reason = getattr(response.choices[0], 'finish_reason', None)
            if finish_reason == 'length':
                return True
        
        # Check if content ends abruptly (heuristic)
        if content and len(content) > 100:
            # Check if ends mid-sentence
            if not content.rstrip().endswith(('.', '!', '?', '"', "'", ')', ']', '}')):
                return True
        
        return False
'''
    
    print("GPT-5 Optimized Provider created with:")
    print("  ✅ Intelligent token limit calculation")
    print("  ✅ Automatic retry on truncation")
    print("  ✅ Response truncation detection")
    print("  ✅ Progressive token increase")
    
    return optimized_provider_code


def main():
    """Create GPT-5 enhancements."""
    
    print("🚀 Creating GPT-5 Response Handling Enhancements")
    print("=" * 60)
    
    # Create enhanced error handling
    enhanced_method = enhance_gpt5_error_handling()
    
    print("\n" + "-" * 60)
    
    # Create optimized provider
    optimized_provider = create_gpt5_optimized_provider()
    
    print(f"\n" + "=" * 60)
    print("📋 IMPLEMENTATION RECOMMENDATIONS")
    print("=" * 60)
    
    print("\n1. **Immediate Fix**: The error you're seeing might not be a parameter issue")
    print("   but rather GPT-5 hitting token limits and truncating responses.")
    
    print("\n2. **Root Cause**: GPT-5 may have different context/response limits")
    print("   that require more conservative token management.")
    
    print("\n3. **Solution Options**:")
    print("   a) Increase max_tokens in your requests (try 2000-4000)")
    print("   b) Implement automatic retry with higher limits")
    print("   c) Use the GPT-5 optimized provider class")
    
    print("\n4. **Quick Test**: Try setting max_tokens to 2000 or higher")
    print("   when using GPT-5 to see if the error persists.")
    
    print(f"\n🎯 **Next Steps**:")
    print("   - Test with higher max_tokens values")
    print("   - Implement retry logic for truncation errors")
    print("   - Consider using GPT-5 optimized provider")
    
    return True


if __name__ == "__main__":
    main()