"""LLM-based embedding generation for environments without Hugging Face access."""

import hashlib
import json
from typing import List

from app.llm.base import EmbeddingProvider, LLMProvider
from app.utils.logger import app_logger


class LLMEmbedder(EmbeddingProvider):
    """LLM-based embedding provider using existing LLM APIs."""

    def __init__(self, llm_provider: LLMProvider, cache_embeddings: bool = True):
        """Initialize with an LLM provider.

        Args:
            llm_provider: LLM provider to use for embedding generation
            cache_embeddings: Whether to cache embeddings to avoid repeated API calls
        """
        self.llm_provider = llm_provider
        self.cache_embeddings = cache_embeddings
        self._embedding_cache = {}
        self._dimension = 1536  # Standard embedding dimension

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return hashlib.md5(text.encode()).hexdigest()

    async def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text using LLM.

        Args:
            text: Input text to embed

        Returns:
            List of float values representing the embedding
        """
        if not text:
            text = ""

        # Check cache first
        if self.cache_embeddings:
            cache_key = self._get_cache_key(text)
            if cache_key in self._embedding_cache:
                return self._embedding_cache[cache_key]

        # Create embedding using LLM
        prompt = f"""Convert the following text into a numerical vector representation suitable for similarity search.
Generate exactly {self._dimension} floating point numbers between -1 and 1 that capture the semantic meaning.
Return only a JSON array of numbers, no other text.

Text: {text}"""

        try:
            response = await self.llm_provider.generate(
                prompt, purpose="embedding_generation"
            )

            # Parse the JSON response
            embedding = json.loads(response.strip())

            # Validate the embedding
            if not isinstance(embedding, list) or len(embedding) != self._dimension:
                app_logger.warning(
                    f"Invalid embedding format, using fallback for text: {text[:50]}..."
                )
                embedding = self._generate_fallback_embedding(text)

            # Ensure all values are floats
            embedding = [float(x) for x in embedding]

            # Cache the result
            if self.cache_embeddings:
                self._embedding_cache[cache_key] = embedding

            return embedding

        except Exception as e:
            app_logger.error(f"LLM embedding generation failed: {e}")
            return self._generate_fallback_embedding(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of input texts to embed

        Returns:
            List of embeddings, one for each input text
        """
        if not texts:
            return []

        embeddings = []
        for text in texts:
            embedding = await self.embed(text)
            embeddings.append(embedding)

        return embeddings

    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """Generate a simple hash-based embedding as fallback.

        Args:
            text: Input text

        Returns:
            Deterministic embedding based on text hash
        """
        # Create a deterministic embedding based on text hash
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()

        # Convert bytes to floats between -1 and 1
        embedding = []
        for i in range(0, min(len(hash_bytes), self._dimension // 8)):
            # Take 8 bytes at a time and convert to float
            byte_chunk = hash_bytes[i : i + 8]
            if len(byte_chunk) == 8:
                # Convert 8 bytes to int, then normalize to [-1, 1]
                int_val = int.from_bytes(byte_chunk, byteorder="big", signed=True)
                float_val = int_val / (2**63 - 1)  # Normalize to [-1, 1]
                embedding.append(float_val)

        # Pad with zeros if needed
        while len(embedding) < self._dimension:
            embedding.append(0.0)

        return embedding[: self._dimension]

    def get_dimension(self) -> int:
        """Get the embedding dimension."""
        return self._dimension
