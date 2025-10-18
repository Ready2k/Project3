"""Base interfaces for LLM and embedding providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text from the given prompt.

        Args:
            prompt: The input prompt
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text response
        """
        raise NotImplementedError("Subclasses must implement generate")

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if the provider connection is working.

        Returns:
            True if connection is successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement test_connection")

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model and provider.

        Returns:
            Dictionary with provider and model information
        """
        raise NotImplementedError("Subclasses must implement get_model_info")

    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models for this provider.

        Returns:
            List of model information dictionaries
        """
        # Default implementation returns empty list
        # Subclasses can override to provide dynamic model discovery
        return []


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for the given text.

        Args:
            text: Input text to embed

        Returns:
            List of float values representing the embedding
        """
        raise NotImplementedError("Subclasses must implement embed")

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of input texts to embed

        Returns:
            List of embeddings, one for each input text
        """
        raise NotImplementedError("Subclasses must implement embed_batch")
