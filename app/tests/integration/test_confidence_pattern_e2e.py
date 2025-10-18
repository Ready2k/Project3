"""
End-to-end integration tests for confidence extraction and pattern creation fixes.

Tests the complete flow from LLM analysis to confidence display and pattern creation
with real requirements containing new technologies.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from app.services.recommendation import RecommendationService
from app.services.pattern_creator import PatternCreator
from app.llm.fakes import FakeLLM


class TestConfidencePatternE2E:
    """End-to-end tests for confidence extraction and pattern creation integration."""

    @pytest.fixture
    def temp_pattern_dir(self):
        """Create temporary directory for pattern files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def mock_settings(self, temp_pattern_dir):
        """Mock settings with temporary pattern directory."""
        settings = MagicMock()
        settings.pattern_library_path = temp_pattern_dir
        return settings

    @pytest.fixture
    def embedding_engine(self):
        """Create mock embedding engine."""
        engine = MagicMock()
        engine.get_embedding = AsyncMock(return_value=[0.1] * 384)
        engine.search_similar = AsyncMock(return_value=[])
        return engine

    def create_fake_llm_with_response(self, response_data):
        """Create fake LLM with specific response data."""
        response_json = json.dumps(response_data)
        # Create a generic hash that will match most prompts
        generic_hash = "12345678"
        return FakeLLM(responses={generic_hash: response_json}, seed=42)

    @pytest.mark.asyncio
    async def test_confidence_extraction_e2e_flow(
        self, mock_settings, embedding_engine
    ):
        """Test complete confidence extraction flow from LLM to display."""
        # Setup: Configure LLM to return specific confidence
        confidence_response = {
            "confidence": 0.73,
            "feasibility": "Partially Automatable",
            "explanation": "Some aspects can be automated, others require manual intervention.",
            "tech_stack": ["Python", "FastAPI", "Redis"],
        }
        fake_llm_provider = self.create_fake_llm_with_response(confidence_response)
        pattern_creator = PatternCreator(mock_settings, fake_llm_provider)

        recommendation_service = RecommendationService(
            settings=mock_settings,
            llm_provider=fake_llm_provider,
            embedding_engine=embedding_engine,
            pattern_creator=pattern_creator,
        )

        # Test requirements with LLM confidence
        requirements = {
            "description": "Build a customer support chatbot with escalation to human agents",
            "llm_analysis_confidence_level": 0.73,
            "business_domain": "customer_service",
            "complexity": "medium",
        }

        # Execute: Get recommendation
        result = await recommendation_service.get_recommendation(requirements)

        # Verify: Confidence extracted from LLM
        assert result["confidence"] == 0.73
        assert result["confidence_source"] == "llm"
        assert result["feasibility"] == "Partially Automatable"

    @pytest.mark.asyncio
    async def test_confidence_fallback_to_pattern_based(
        self, mock_settings, embedding_engine
    ):
        """Test confidence fallback when LLM confidence is invalid."""
        # Setup: Configure LLM with invalid confidence
        invalid_response = {
            "confidence": "high",  # Invalid string value
            "feasibility": "Automatable",
            "explanation": "This can be automated.",
            "tech_stack": ["React", "Express"],
        }
        fake_llm_provider = self.create_fake_llm_with_response(invalid_response)
        pattern_creator = PatternCreator(mock_settings, fake_llm_provider)

        recommendation_service = RecommendationService(
            settings=mock_settings,
            llm_provider=fake_llm_provider,
            embedding_engine=embedding_engine,
            pattern_creator=pattern_creator,
        )

        # Test requirements without valid LLM confidence
        requirements = {
            "description": "Simple CRUD application for inventory management",
            "business_domain": "inventory",
            "complexity": "low",
        }

        # Execute: Get recommendation
        result = await recommendation_service.get_recommendation(requirements)

        # Verify: Falls back to pattern-based confidence
        assert 0.0 <= result["confidence"] <= 1.0
        assert result["confidence_source"] == "pattern_based"
        assert result["feasibility"] == "Automatable"

    @pytest.mark.asyncio
    async def test_pattern_creation_with_novel_technologies(
        self, mock_settings, embedding_engine
    ):
        """Test pattern creation when requirements contain novel technologies."""
        # Setup: Configure LLM for pattern creation
        pattern_response = {
            "pattern_id": "PAT-NEW-001",
            "name": "Blockchain Supply Chain Tracking",
            "description": "Automated supply chain tracking using blockchain technology",
            "feasibility": "Automatable",
            "confidence": 0.82,
            "tech_stack": ["Ethereum", "Solidity", "Web3.js", "IPFS", "React"],
            "pattern_type": ["blockchain_integration", "supply_chain_automation"],
            "integrations": ["MetaMask", "Infura", "Pinata"],
            "compliance": ["ISO_27001", "GDPR"],
        }
        fake_llm_provider = self.create_fake_llm_with_response(pattern_response)
        pattern_creator = PatternCreator(mock_settings, fake_llm_provider)

        # Create existing pattern with different tech stack
        existing_pattern = {
            "pattern_id": "PAT-001",
            "name": "Traditional Supply Chain Management",
            "description": "Supply chain management using traditional databases",
            "feasibility": "Automatable",
            "tech_stack": ["MySQL", "PHP", "Apache"],
            "pattern_type": ["database_management"],
            "integrations": ["SAP", "Oracle"],
            "compliance": ["SOX"],
        }

        pattern_file = Path(mock_settings.pattern_library_path) / "PAT-001.json"
        with open(pattern_file, "w") as f:
            json.dump(existing_pattern, f)

        recommendation_service = RecommendationService(
            settings=mock_settings,
            llm_provider=fake_llm_provider,
            embedding_engine=embedding_engine,
            pattern_creator=pattern_creator,
        )

        # Test requirements with novel blockchain technologies
        requirements = {
            "description": "Build a blockchain-based supply chain tracking system with smart contracts",
            "business_domain": "supply_chain",
            "complexity": "high",
            "tech_stack": ["Ethereum", "Solidity", "Web3.js", "IPFS"],
            "compliance_requirements": ["GDPR", "ISO_27001"],
        }

        # Execute: Get recommendation (should create new pattern)
        result = await recommendation_service.get_recommendation(requirements)

        # Verify: New pattern created due to novel technologies
        assert result["confidence"] == 0.82
        assert result.get("pattern_created", False) is True
        assert "PAT-NEW-001" in result.get("pattern_id", "")

    @pytest.mark.asyncio
    async def test_regression_existing_functionality(
        self, mock_settings, embedding_engine
    ):
        """Test that existing functionality still works after fixes."""
        # Setup: Standard response format
        standard_response = {
            "feasibility": "Partially Automatable",
            "confidence": 0.65,
            "explanation": "Some manual steps required for compliance verification",
            "tech_stack": ["Java", "Spring", "Oracle", "Apache_Kafka"],
            "automation_percentage": 75,
        }
        fake_llm_provider = self.create_fake_llm_with_response(standard_response)
        pattern_creator = PatternCreator(mock_settings, fake_llm_provider)

        recommendation_service = RecommendationService(
            settings=mock_settings,
            llm_provider=fake_llm_provider,
            embedding_engine=embedding_engine,
            pattern_creator=pattern_creator,
        )

        # Test standard requirements format
        requirements = {
            "description": "Financial reporting system with regulatory compliance",
            "business_domain": "finance",
            "complexity": "high",
            "compliance_requirements": ["SOX", "GDPR"],
        }

        # Execute: Get recommendation
        result = await recommendation_service.get_recommendation(requirements)

        # Verify: All expected fields present
        assert "feasibility" in result
        assert "confidence" in result
        assert "explanation" in result
        assert "tech_stack" in result

        # Verify: Values are correct
        assert result["feasibility"] == "Partially Automatable"
        assert result["confidence"] == 0.65
        assert "Java" in result["tech_stack"]

    @pytest.mark.asyncio
    async def test_confidence_display_formatting(self, mock_settings, embedding_engine):
        """Test that confidence values are properly formatted for display."""
        # Test various confidence values
        test_cases = [
            (0.0, "0.00%"),
            (0.5, "50.00%"),
            (0.8567, "85.67%"),
            (1.0, "100.00%"),
        ]

        for confidence_value, expected_display in test_cases:
            # Setup: Configure specific confidence
            response = {
                "confidence": confidence_value,
                "feasibility": "Automatable",
                "explanation": "Test case",
                "tech_stack": ["Python"],
            }
            fake_llm_provider = self.create_fake_llm_with_response(response)
            pattern_creator = PatternCreator(mock_settings, fake_llm_provider)

            recommendation_service = RecommendationService(
                settings=mock_settings,
                llm_provider=fake_llm_provider,
                embedding_engine=embedding_engine,
                pattern_creator=pattern_creator,
            )

            # Test requirements
            requirements = {
                "description": f"Test case for confidence {confidence_value}",
                "llm_analysis_confidence_level": confidence_value,
            }

            # Execute: Get recommendation
            result = await recommendation_service.get_recommendation(requirements)

            # Verify: Confidence value and formatting
            assert result["confidence"] == confidence_value

            # Test display formatting
            display_confidence = f"{result['confidence']:.2%}"
            assert display_confidence == expected_display

    @pytest.mark.asyncio
    async def test_logging_and_monitoring_integration(
        self, mock_settings, embedding_engine, caplog
    ):
        """Test that logging and monitoring work correctly for both fixes."""
        import logging

        caplog.set_level(logging.INFO)

        # Setup: Configure LLM response
        response = {
            "confidence": 0.91,
            "feasibility": "Automatable",
            "explanation": "Fully automatable with modern tools",
            "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
        }
        fake_llm_provider = self.create_fake_llm_with_response(response)
        pattern_creator = PatternCreator(mock_settings, fake_llm_provider)

        recommendation_service = RecommendationService(
            settings=mock_settings,
            llm_provider=fake_llm_provider,
            embedding_engine=embedding_engine,
            pattern_creator=pattern_creator,
        )

        # Test requirements
        requirements = {
            "description": "API for user management with authentication",
            "llm_analysis_confidence_level": 0.91,
            "business_domain": "user_management",
        }

        # Execute: Get recommendation
        result = await recommendation_service.get_recommendation(requirements)

        # Verify: Proper logging occurred
        log_messages = [record.message for record in caplog.records]

        # Check that some logging occurred (specific messages may vary)
        assert len(log_messages) > 0

        # Verify result structure
        assert "confidence" in result
        assert "confidence_source" in result
        assert "feasibility" in result
        assert result["confidence"] == 0.91
