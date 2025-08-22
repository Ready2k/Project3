"""Hash-based embedding generation for offline environments."""

import hashlib
import re
from typing import List, Set

from app.llm.base import EmbeddingProvider
from app.utils.logger import app_logger


class HashEmbedder(EmbeddingProvider):
    """Simple hash-based embedding provider for offline use."""
    
    def __init__(self, dimension: int = 384):
        """Initialize hash-based embedder.
        
        Args:
            dimension: Embedding dimension (should be multiple of 32 for efficiency)
        """
        self.dimension = dimension
        
    def _extract_features(self, text: str) -> Set[str]:
        """Extract features from text for embedding generation."""
        if not text:
            return set()
        
        text = text.lower()
        features = set()
        
        # Word-level features
        words = re.findall(r'\b\w+\b', text)
        features.update(words)
        
        # Bigram features
        for i in range(len(words) - 1):
            bigram = f"{words[i]}_{words[i+1]}"
            features.add(bigram)
        
        # Character-level features (for handling typos)
        for word in words:
            if len(word) >= 3:
                for i in range(len(word) - 2):
                    trigram = word[i:i+3]
                    features.add(f"char_{trigram}")
        
        return features
    
    def _hash_feature(self, feature: str, dimension: int) -> int:
        """Hash a feature to a dimension index."""
        hash_obj = hashlib.md5(feature.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        return hash_int % dimension
    
    async def embed(self, text: str) -> List[float]:
        """Generate hash-based embedding for text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of float values representing the embedding
        """
        if not text:
            return [0.0] * self.dimension
        
        # Initialize embedding vector
        embedding = [0.0] * self.dimension
        
        # Extract features
        features = self._extract_features(text)
        
        if not features:
            return embedding
        
        # Hash each feature to embedding dimensions
        for feature in features:
            # Use multiple hash functions for better distribution
            for salt in ['a', 'b', 'c']:
                salted_feature = f"{salt}_{feature}"
                dim_index = self._hash_feature(salted_feature, self.dimension)
                
                # Use signed hash for positive/negative values
                sign_hash = self._hash_feature(f"sign_{salted_feature}", 2)
                sign = 1.0 if sign_hash == 0 else -1.0
                
                embedding[dim_index] += sign * (1.0 / len(features))
        
        # Normalize the embedding
        magnitude = sum(x * x for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]
        
        return embedding
    
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
    
    def get_dimension(self) -> int:
        """Get the embedding dimension."""
        return self.dimension