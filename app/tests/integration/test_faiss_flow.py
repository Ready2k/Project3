import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.embeddings.engine import SentenceTransformerEmbedder
from app.embeddings.index import FAISSIndex
from app.llm.fakes import FakeEmbedder


class TestSentenceTransformerEmbedder:
    """Test sentence transformer embedding generation."""
    
    @pytest.fixture
    def embedder(self):
        # Use a small model for testing
        return SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
    
    @pytest.mark.asyncio
    async def test_embed_single_text(self, embedder):
        """Test embedding a single text."""
        text = "This is a test sentence for embedding."
        embedding = await embedder.embed(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384  # all-MiniLM-L6-v2 dimension
        assert all(isinstance(x, float) for x in embedding)
    
    @pytest.mark.asyncio
    async def test_embed_batch(self, embedder):
        """Test embedding multiple texts."""
        texts = [
            "First test sentence.",
            "Second test sentence.",
            "Third test sentence."
        ]
        embeddings = await embedder.embed_batch(texts)
        
        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)
        assert all(isinstance(x, float) for emb in embeddings for x in emb)
    
    @pytest.mark.asyncio
    async def test_embed_empty_text(self, embedder):
        """Test embedding empty text."""
        embedding = await embedder.embed("")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384
    
    @pytest.mark.asyncio
    async def test_embed_consistency(self, embedder):
        """Test that same text produces same embedding."""
        text = "Consistent test text"
        
        embedding1 = await embedder.embed(text)
        embedding2 = await embedder.embed(text)
        
        # Should be identical (or very close due to floating point)
        assert len(embedding1) == len(embedding2)
        for i in range(len(embedding1)):
            assert abs(embedding1[i] - embedding2[i]) < 1e-6


class TestFAISSIndex:
    """Test FAISS index operations."""
    
    @pytest.fixture
    def fake_embedder(self):
        return FakeEmbedder(dimension=384, seed=42)
    
    @pytest.fixture
    def temp_index_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir) / "test_index.faiss"
    
    @pytest.mark.asyncio
    async def test_build_index_from_texts(self, fake_embedder, temp_index_path):
        """Test building FAISS index from text documents."""
        texts = [
            "Document about web scraping automation",
            "API integration workflow documentation",
            "Document processing pipeline guide",
            "Machine learning model deployment",
            "Database optimization techniques"
        ]
        
        faiss_index = FAISSIndex(embedder=fake_embedder, index_path=temp_index_path)
        await faiss_index.build_from_texts(texts)
        
        assert faiss_index.index is not None
        assert faiss_index.index.ntotal == 5
        assert len(faiss_index.text_mapping) == 5
    
    @pytest.mark.asyncio
    async def test_search_similar_texts(self, fake_embedder, temp_index_path):
        """Test searching for similar texts in the index."""
        texts = [
            "Web scraping with Python and BeautifulSoup",
            "API integration using REST and GraphQL",
            "Document processing with OCR technology",
            "Machine learning model training",
            "Database query optimization"
        ]
        
        faiss_index = FAISSIndex(embedder=fake_embedder, index_path=temp_index_path)
        await faiss_index.build_from_texts(texts)
        
        # Search for similar text
        query = "Python web scraping automation"
        results = await faiss_index.search(query, top_k=3)
        
        assert len(results) <= 3
        assert all('text' in result for result in results)
        assert all('score' in result for result in results)
        assert all('index' in result for result in results)
        
        # Scores should be in descending order
        scores = [result['score'] for result in results]
        assert scores == sorted(scores, reverse=True)
    
    @pytest.mark.asyncio
    async def test_search_empty_index(self, fake_embedder, temp_index_path):
        """Test searching in an empty index."""
        faiss_index = FAISSIndex(embedder=fake_embedder, index_path=temp_index_path)
        
        results = await faiss_index.search("test query", top_k=5)
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_save_and_load_index(self, fake_embedder, temp_index_path):
        """Test saving and loading FAISS index."""
        texts = [
            "First document for testing",
            "Second document for testing",
            "Third document for testing"
        ]
        
        # Build and save index
        faiss_index = FAISSIndex(embedder=fake_embedder, index_path=temp_index_path)
        await faiss_index.build_from_texts(texts)
        faiss_index.save()
        
        # Load index in new instance
        new_faiss_index = FAISSIndex(embedder=fake_embedder, index_path=temp_index_path)
        new_faiss_index.load()
        
        assert new_faiss_index.index is not None
        assert new_faiss_index.index.ntotal == 3
        assert len(new_faiss_index.text_mapping) == 3
        
        # Test search works after loading
        results = await new_faiss_index.search("testing document", top_k=2)
        assert len(results) <= 2
    
    @pytest.mark.asyncio
    async def test_add_documents_to_existing_index(self, fake_embedder, temp_index_path):
        """Test adding documents to an existing index."""
        initial_texts = [
            "Initial document one",
            "Initial document two"
        ]
        
        faiss_index = FAISSIndex(embedder=fake_embedder, index_path=temp_index_path)
        await faiss_index.build_from_texts(initial_texts)
        
        assert faiss_index.index.ntotal == 2
        
        # Add more documents
        additional_texts = [
            "Additional document one",
            "Additional document two"
        ]
        
        await faiss_index.add_texts(additional_texts)
        
        assert faiss_index.index.ntotal == 4
        assert len(faiss_index.text_mapping) == 4
    
    @pytest.mark.asyncio
    async def test_search_with_different_top_k(self, fake_embedder, temp_index_path):
        """Test search with different top_k values."""
        texts = [f"Document number {i}" for i in range(10)]
        
        faiss_index = FAISSIndex(embedder=fake_embedder, index_path=temp_index_path)
        await faiss_index.build_from_texts(texts)
        
        # Test different top_k values
        for k in [1, 3, 5, 10, 15]:
            results = await faiss_index.search("document", top_k=k)
            expected_count = min(k, 10)  # Can't return more than available
            assert len(results) == expected_count


class TestEmbeddingIntegration:
    """Test integration between embeddings and FAISS."""
    
    @pytest.mark.asyncio
    async def test_pattern_embedding_and_search(self):
        """Test embedding patterns and searching for similar ones."""
        # Mock pattern descriptions
        pattern_descriptions = [
            "Automated web scraping with rate limiting and error handling",
            "API integration workflow with authentication and retry logic",
            "Document processing pipeline with OCR and text extraction",
            "Machine learning model deployment with monitoring",
            "Database migration and optimization automation"
        ]
        
        fake_embedder = FakeEmbedder(dimension=384, seed=42)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir) / "patterns.faiss"
            faiss_index = FAISSIndex(embedder=fake_embedder, index_path=index_path)
            
            # Build index from pattern descriptions
            await faiss_index.build_from_texts(pattern_descriptions)
            
            # Search for similar patterns
            query = "web scraping automation with error handling"
            results = await faiss_index.search(query, top_k=3)
            
            assert len(results) == 3
            
            # The first result should be the web scraping pattern
            # (deterministic due to fake embedder)
            first_result = results[0]
            assert 'text' in first_result
            assert 'score' in first_result
            assert isinstance(first_result['score'], float)
    
    @pytest.mark.asyncio
    async def test_requirement_to_pattern_matching(self):
        """Test matching user requirements to patterns."""
        # Simulate pattern library
        patterns = [
            {
                "pattern_id": "PAT-001",
                "description": "Web scraping automation with Python and BeautifulSoup"
            },
            {
                "pattern_id": "PAT-002", 
                "description": "REST API integration with authentication and rate limiting"
            },
            {
                "pattern_id": "PAT-003",
                "description": "Document processing with OCR and text extraction"
            }
        ]
        
        pattern_descriptions = [p["description"] for p in patterns]
        fake_embedder = FakeEmbedder(dimension=384, seed=42)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir) / "requirements.faiss"
            faiss_index = FAISSIndex(embedder=fake_embedder, index_path=index_path)
            
            await faiss_index.build_from_texts(pattern_descriptions)
            
            # User requirement
            user_requirement = "I need to extract data from websites automatically"
            
            results = await faiss_index.search(user_requirement, top_k=2)
            
            assert len(results) == 2
            
            # Map results back to patterns
            matched_patterns = []
            for result in results:
                pattern_index = result['index']
                matched_pattern = patterns[pattern_index]
                matched_patterns.append({
                    **matched_pattern,
                    'similarity_score': result['score']
                })
            
            assert len(matched_patterns) == 2
            assert all('pattern_id' in p for p in matched_patterns)
            assert all('similarity_score' in p for p in matched_patterns)