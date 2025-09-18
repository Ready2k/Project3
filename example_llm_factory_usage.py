#!/usr/bin/env python3
"""
Example: Using LLM Provider Factory in Application Code

This example shows how to integrate the LLM provider factory into your application
to replace fallback import patterns with proper service-based dependency management.
"""

import asyncio
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.utils.imports import require_service, optional_service
from app.core.service_registration import register_core_services


class AnalysisService:
    """
    Example service that uses LLM providers through the factory.
    
    This demonstrates how to replace fallback imports with service registry patterns.
    """
    
    def __init__(self):
        """Initialize the analysis service."""
        # Get LLM factory from service registry
        self.llm_factory = require_service("llm_provider_factory")
        self.llm_factory.initialize()
        
        # Cache for LLM provider instance
        self._llm_provider = None
    
    async def get_llm_provider(self):
        """Get an LLM provider instance with fallback handling."""
        if self._llm_provider is None:
            # Try to create provider with automatic fallback
            result = self.llm_factory.create_provider_with_fallback()
            
            if result.is_success():
                self._llm_provider = result.value
                print(f"✅ Using LLM provider: {self._llm_provider.get_model_info()['provider']}")
            else:
                raise RuntimeError(f"No LLM providers available: {result.error}")
        
        return self._llm_provider
    
    async def analyze_text(self, text: str) -> dict:
        """
        Analyze text using LLM provider.
        
        Args:
            text: Text to analyze
            
        Returns:
            Analysis results dictionary
        """
        try:
            provider = await self.get_llm_provider()
            
            # Create analysis prompt
            prompt = f"""
            Please analyze the following text and provide:
            1. A brief summary
            2. Key themes or topics
            3. Sentiment (positive, negative, neutral)
            
            Text: {text}
            
            Please format your response as a structured analysis.
            """
            
            # Generate analysis
            response = await provider.generate(prompt, max_tokens=500)
            
            return {
                "success": True,
                "analysis": response,
                "provider": provider.get_model_info()["provider"],
                "model": provider.get_model_info().get("model", "unknown")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "analysis": None
            }
    
    async def check_provider_health(self) -> dict:
        """Check the health of available LLM providers."""
        status = self.llm_factory.get_provider_status()
        available_providers = self.llm_factory.get_available_providers()
        
        health_results = {}
        for provider_name in available_providers:
            test_result = await self.llm_factory.test_provider(provider_name)
            health_results[provider_name] = {
                "available": True,
                "healthy": test_result.is_success(),
                "error": test_result.error if test_result.is_error() else None
            }
        
        return {
            "total_providers": len(status),
            "available_providers": len(available_providers),
            "provider_health": health_results
        }


class PatternMatchingService:
    """
    Example service showing optional LLM usage.
    
    This service can work without LLM providers but uses them for enhanced functionality.
    """
    
    def __init__(self):
        """Initialize the pattern matching service."""
        # Use optional service - won't fail if not available
        self.llm_factory = optional_service("llm_provider_factory")
        
        if self.llm_factory:
            self.llm_factory.initialize()
            print("✅ LLM factory available - enhanced pattern matching enabled")
        else:
            print("⚠️  LLM factory not available - using basic pattern matching")
    
    async def match_patterns(self, text: str, patterns: list) -> dict:
        """
        Match patterns in text with optional LLM enhancement.
        
        Args:
            text: Text to analyze
            patterns: List of patterns to match
            
        Returns:
            Pattern matching results
        """
        # Basic pattern matching (always available)
        basic_matches = []
        for pattern in patterns:
            if pattern.lower() in text.lower():
                basic_matches.append({
                    "pattern": pattern,
                    "found": True,
                    "method": "basic_string_match"
                })
        
        result = {
            "basic_matches": basic_matches,
            "enhanced_matches": None,
            "llm_available": self.llm_factory is not None
        }
        
        # Enhanced matching with LLM (if available)
        if self.llm_factory:
            try:
                provider_result = self.llm_factory.create_provider_with_fallback()
                if provider_result.is_success():
                    provider = provider_result.value
                    
                    prompt = f"""
                    Analyze the following text for semantic matches to these patterns:
                    Patterns: {', '.join(patterns)}
                    
                    Text: {text}
                    
                    For each pattern, indicate if it's semantically present (not just exact string match).
                    Respond with a simple list format.
                    """
                    
                    response = await provider.generate(prompt, max_tokens=200)
                    result["enhanced_matches"] = response
                    result["enhancement_provider"] = provider.get_model_info()["provider"]
                    
            except Exception as e:
                result["enhancement_error"] = str(e)
        
        return result


async def demonstrate_service_usage():
    """Demonstrate how services use the LLM factory."""
    print("🚀 LLM Factory Usage in Application Services")
    
    # Set up services
    register_core_services()
    
    print("\n=== Analysis Service Example ===")
    
    # Create analysis service
    analysis_service = AnalysisService()
    
    # Check provider health
    health_status = await analysis_service.check_provider_health()
    print(f"Provider health: {health_status['available_providers']}/{health_status['total_providers']} providers available")
    
    # Analyze some text
    sample_text = """
    Artificial Intelligence is transforming the way we work and live. 
    Machine learning algorithms can now process vast amounts of data 
    to identify patterns and make predictions. This technology has 
    applications in healthcare, finance, transportation, and many other fields.
    The future looks bright for AI development.
    """
    
    analysis_result = await analysis_service.analyze_text(sample_text)
    
    if analysis_result["success"]:
        print(f"✅ Analysis completed using {analysis_result['provider']} ({analysis_result['model']})")
        print(f"Analysis: {analysis_result['analysis'][:200]}...")
    else:
        print(f"❌ Analysis failed: {analysis_result['error']}")
    
    print("\n=== Pattern Matching Service Example ===")
    
    # Create pattern matching service
    pattern_service = PatternMatchingService()
    
    # Test pattern matching
    patterns = ["artificial intelligence", "machine learning", "data processing", "healthcare"]
    
    pattern_results = await pattern_service.match_patterns(sample_text, patterns)
    
    print(f"Basic matches found: {len(pattern_results['basic_matches'])}")
    for match in pattern_results['basic_matches']:
        print(f"  - {match['pattern']}: {match['found']}")
    
    if pattern_results['enhanced_matches']:
        print(f"Enhanced analysis: {pattern_results['enhanced_matches'][:150]}...")
    
    print("\n=== Error Handling Example ===")
    
    # Demonstrate error handling when no providers are available
    try:
        # This would fail if no providers were available
        provider_result = require_service("llm_provider_factory").create_provider("nonexistent")
        if provider_result.is_error():
            print(f"✅ Proper error handling: {provider_result.error}")
    except Exception as e:
        print(f"✅ Exception handling: {e}")


def show_migration_example():
    """Show how to migrate from fallback imports to service registry."""
    print("\n=== Migration Example: Before and After ===")
    
    print("\n--- BEFORE (Problematic fallback imports) ---")
    print("""
    # Old problematic pattern:
    try:
        import openai
        llm_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        llm_available = True
    except ImportError:
        try:
            import anthropic
            llm_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            llm_available = True
        except ImportError:
            llm_client = None
            llm_available = False
    
    # Usage with unclear error handling:
    if llm_available and llm_client:
        response = llm_client.generate("Hello")  # Different APIs!
    else:
        response = "LLM not available"
    """)
    
    print("\n--- AFTER (Service registry pattern) ---")
    print("""
    # New service-based pattern:
    from app.utils.imports import require_service
    
    # Get factory from service registry
    llm_factory = require_service("llm_provider_factory")
    
    # Create provider with automatic fallback
    result = llm_factory.create_provider_with_fallback("openai")
    
    if result.is_success():
        provider = result.value
        response = await provider.generate("Hello")  # Consistent API!
    else:
        response = f"LLM not available: {result.error}"
    """)
    
    print("\n✅ Benefits of the new approach:")
    print("  - Consistent API across all providers")
    print("  - Explicit error handling with clear messages")
    print("  - Automatic fallback to available providers")
    print("  - Easy testing with mock providers")
    print("  - Centralized configuration")
    print("  - Health monitoring and status reporting")


if __name__ == "__main__":
    try:
        # Run the demonstration
        asyncio.run(demonstrate_service_usage())
        
        # Show migration example
        show_migration_example()
        
        print("\n🎉 Example completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)