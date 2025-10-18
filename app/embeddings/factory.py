"""Factory for creating embedding providers based on configuration."""

from typing import Optional

from app.config import Settings, EmbeddingProvider as EmbeddingProviderEnum
from app.llm.base import EmbeddingProvider, LLMProvider
from app.utils.logger import app_logger


def create_embedding_provider(
    settings: Settings, llm_provider: Optional[LLMProvider] = None
) -> EmbeddingProvider:
    """Create an embedding provider based on configuration.

    Args:
        settings: Application settings
        llm_provider: Optional LLM provider for LLM-based embeddings

    Returns:
        Configured embedding provider
    """
    provider_type = settings.embedding.provider

    try:
        if provider_type == EmbeddingProviderEnum.SENTENCE_TRANSFORMERS:
            return _create_sentence_transformer_provider(settings)
        elif provider_type == EmbeddingProviderEnum.LLM_BASED:
            return _create_llm_provider(settings, llm_provider)
        elif provider_type == EmbeddingProviderEnum.HASH_BASED:
            return _create_hash_provider(settings)
        else:
            app_logger.warning(
                f"Unknown embedding provider: {provider_type}, falling back to hash-based"
            )
            return _create_hash_provider(settings)

    except Exception as e:
        app_logger.error(f"Failed to create {provider_type} embedding provider: {e}")

        # Try fallback provider
        fallback_provider = settings.embedding.fallback_provider
        if fallback_provider and fallback_provider != provider_type:
            app_logger.info(f"Attempting fallback to {fallback_provider}")
            try:
                if fallback_provider == EmbeddingProviderEnum.HASH_BASED:
                    return _create_hash_provider(settings)
                elif (
                    fallback_provider == EmbeddingProviderEnum.LLM_BASED
                    and llm_provider
                ):
                    return _create_llm_provider(settings, llm_provider)
            except Exception as fallback_error:
                app_logger.error(f"Fallback provider also failed: {fallback_error}")

        # Final fallback to hash-based
        app_logger.info("Using hash-based embeddings as final fallback")
        return _create_hash_provider(settings)


def _create_sentence_transformer_provider(settings: Settings) -> EmbeddingProvider:
    """Create sentence transformer embedding provider."""
    try:
        from app.embeddings.engine import SentenceTransformerEmbedder

        return SentenceTransformerEmbedder(model_name=settings.embedding.model_name)
    except ImportError as e:
        raise ImportError(f"sentence-transformers not available: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to initialize sentence transformer model: {e}")


def _create_llm_provider(
    settings: Settings, llm_provider: Optional[LLMProvider]
) -> EmbeddingProvider:
    """Create LLM-based embedding provider."""
    if llm_provider is None:
        raise ValueError("LLM provider is required for LLM-based embeddings")

    from app.embeddings.llm_embedder import LLMEmbedder

    return LLMEmbedder(
        llm_provider=llm_provider, cache_embeddings=settings.embedding.cache_embeddings
    )


def _create_hash_provider(settings: Settings) -> EmbeddingProvider:
    """Create hash-based embedding provider."""
    from app.embeddings.hash_embedder import HashEmbedder

    return HashEmbedder(dimension=settings.embedding.dimension)
