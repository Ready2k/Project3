"""FAISS index wrapper for vector similarity search."""

import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

import faiss
import numpy as np

from app.llm.base import EmbeddingProvider
from app.utils.logger import app_logger


class FAISSIndex:
    """FAISS-based vector similarity search index."""
    
    def __init__(self, embedder: EmbeddingProvider, index_path: Optional[Path] = None):
        """Initialize FAISS index.
        
        Args:
            embedder: Embedding provider for generating vectors
            index_path: Path to save/load the index
        """
        self.embedder = embedder
        self.index_path = index_path
        self.index: Optional[faiss.Index] = None
        self.text_mapping: List[str] = []  # Maps index positions to original texts
        self.dimension: Optional[int] = None
    
    async def build_from_texts(self, texts: List[str]) -> None:
        """Build FAISS index from a list of texts.
        
        Args:
            texts: List of texts to index
        """
        if not texts:
            app_logger.warning("No texts provided to build index")
            return
        
        app_logger.info(f"Building FAISS index from {len(texts)} texts")
        
        # Generate embeddings for all texts
        embeddings = await self.embedder.embed_batch(texts)
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings, dtype=np.float32)
        self.dimension = embeddings_array.shape[1]
        
        # Create FAISS index (using L2 distance)
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Add embeddings to index
        self.index.add(embeddings_array)
        
        # Store text mapping
        self.text_mapping = texts.copy()
        
        app_logger.info(f"Built FAISS index with {self.index.ntotal} vectors, dimension {self.dimension}")
    
    async def add_texts(self, texts: List[str]) -> None:
        """Add more texts to an existing index.
        
        Args:
            texts: List of texts to add
        """
        if not texts:
            return
        
        if self.index is None:
            await self.build_from_texts(texts)
            return
        
        app_logger.info(f"Adding {len(texts)} texts to existing index")
        
        # Generate embeddings for new texts
        embeddings = await self.embedder.embed_batch(texts)
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # Add to index
        self.index.add(embeddings_array)
        
        # Update text mapping
        self.text_mapping.extend(texts)
        
        app_logger.info(f"Index now contains {self.index.ntotal} vectors")
    
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar texts in the index.
        
        Args:
            query: Query text to search for
            top_k: Number of top results to return
            
        Returns:
            List of search results with text, score, and index
        """
        if self.index is None or self.index.ntotal == 0:
            app_logger.warning("Index is empty, returning no results")
            return []
        
        # Generate embedding for query
        query_embedding = await self.embedder.embed(query)
        query_array = np.array([query_embedding], dtype=np.float32)
        
        # Search in index
        actual_k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(query_array, actual_k)
        
        # Convert results
        results = []
        for i in range(actual_k):
            distance = float(distances[0][i])
            index = int(indices[0][i])
            
            # Convert L2 distance to similarity score (higher is better)
            # Using negative exponential to convert distance to similarity
            similarity_score = float(np.exp(-distance))
            
            results.append({
                'text': self.text_mapping[index],
                'score': similarity_score,
                'index': index,
                'distance': distance
            })
        
        app_logger.debug(f"Found {len(results)} results for query")
        return results
    
    def save(self) -> None:
        """Save the index and text mapping to disk."""
        if self.index_path is None:
            raise ValueError("No index path specified for saving")
        
        if self.index is None:
            raise ValueError("No index to save")
        
        # Create directory if it doesn't exist
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(self.index_path))
        
        # Save text mapping
        mapping_path = self.index_path.with_suffix('.mapping.pkl')
        with open(mapping_path, 'wb') as f:
            pickle.dump({
                'text_mapping': self.text_mapping,
                'dimension': self.dimension
            }, f)
        
        app_logger.info(f"Saved FAISS index to {self.index_path}")
    
    def load(self) -> None:
        """Load the index and text mapping from disk."""
        if self.index_path is None:
            raise ValueError("No index path specified for loading")
        
        if not self.index_path.exists():
            raise FileNotFoundError(f"Index file not found: {self.index_path}")
        
        # Load FAISS index
        self.index = faiss.read_index(str(self.index_path))
        
        # Load text mapping
        mapping_path = self.index_path.with_suffix('.mapping.pkl')
        if mapping_path.exists():
            with open(mapping_path, 'rb') as f:
                data = pickle.load(f)
                self.text_mapping = data['text_mapping']
                self.dimension = data['dimension']
        else:
            app_logger.warning("Text mapping file not found, creating empty mapping")
            self.text_mapping = []
            self.dimension = self.index.d
        
        app_logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors from {self.index_path}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        if self.index is None:
            return {'total_vectors': 0, 'dimension': 0}
        
        return {
            'total_vectors': self.index.ntotal,
            'dimension': self.dimension or self.index.d,
            'text_count': len(self.text_mapping)
        }