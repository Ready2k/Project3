"""Embedding generation using sentence transformers."""

from typing import List

from sentence_transformers import SentenceTransformer

from app.llm.base import EmbeddingProvider


class SentenceTransformerEmbedder(EmbeddingProvider):
    """Sentence transformer-based embedding provider."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize with a sentence transformer model.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of float values representing the embedding
        """
        if not text:
            text = ""  # Handle empty text
        
        # sentence-transformers encode returns numpy array
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embeddings, one for each input text
        """
        if not texts:
            return []
        
        # Handle empty texts
        processed_texts = [text if text else "" for text in texts]
        
        # Batch encoding is more efficient
        embeddings = self.model.encode(processed_texts, convert_to_tensor=False)
        return [embedding.tolist() for embedding in embeddings]
    
    def get_dimension(self) -> int:
        """Get the embedding dimension."""
        return self.model.get_sentence_embedding_dimension()