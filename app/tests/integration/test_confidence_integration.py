"""Integration tests for confidence extraction and display."""

import pytest
from unittest.mock import patch
from app.services.recommendation import RecommendationService
from app.pattern.matcher import MatchResult
from app.state.store import Recommendation


class TestConfidenceIntegration:
    """Integration tests for confidence extraction and display functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = RecommendationService()
        self.mock_match = MatchResult(
            pattern_id="INT-001",
            pattern_name="Integration Test Pattern",
            feasibility="Automatable",
            tech_stack=["Python", "FastAPI"],
            confidence=0.8,
            tag_score=0.9,
            vector_score=0.7,
            blended_score=0.8,
            rationale="Integration test pattern match"
        )
    
    @pytest.mark.asyncio
    async def test_end_to_end_confidence_flow_with_llm(self):
        """Test complete confidence flow from LLM analysis to recommendation."""
        # Mock requirements with LLM confidence
        requirements = {
            "description": "Test automation requirement",
            "llm_analysis_confidence_level": 0.92,
            "llm_analysis_automation_feasibility": "Automatable",
            "domain": "test"
        }
        
        # Generate recommendations
        recommendations = await self.service.generate_recommendations(
            [self.mock_match], requirements, "test_session"
        )
        
        # Verify LLM confidence is used
        assert len(recommendations) == 1
        assert recommendations[0].confidence == 0.92
        assert recommendations[0].feasibility == "Automatable"
    
    @pytest.mark.asyncio
    async def test_end_to_end_confidence_flow_with_pattern_fallback(self):
        """Test complete confidence flow with pattern-based fallback."""
        # Mock requirements without LLM confidence
        requirements = {
            "description": "Test automation requirement",
            "domain": "test",
            "workflow_steps": ["step1", "step2"]
        }
        
        # Generate recommendations
        recommendations = await self.service.generate_recommendations(
            [self.mock_match], requirements, "test_session"
        )
        
        # Verify pattern-based confidence is calculated
        assert len(recommendations) == 1
        assert 0.0 <= recommendations[0].confidence <= 1.0
        assert recommendations[0].confidence != 0.92  # Should not be LLM value
    
    def test_confidence_display_formatting_integration(self):
        """Test confidence display formatting as used in the UI."""
        # Test various confidence values and their UI display
        test_cases = [
            (0.0, "0%"),
            (0.1234, "12%"),
            (0.5, "50%"),
            (0.8567, "86%"),
            (0.999, "100%"),
            (1.0, "100%"),
        ]
        
        for confidence_value, expected_display in test_cases:
            # Create a recommendation with the confidence value
            recommendation = Recommendation(
                pattern_id="TEST-001",
                feasibility="Automatable",
                confidence=confidence_value,
                tech_stack=["Python"],
                reasoning="Test reasoning"
            )
            
            # Test the formatting used in main.py: {confidence:.0%}
            formatted = f"{recommendation.confidence:.0%}"
            assert formatted == expected_display, f"Confidence {confidence_value} should format as {expected_display}, got {formatted}"
    
    @pytest.mark.asyncio
    async def test_confidence_with_various_llm_response_formats(self):
        """Test confidence extraction with various LLM response formats in integration."""
        test_cases = [
            # JSON format
            {
                "llm_analysis_raw_response": '{"confidence": 0.87, "feasibility": "high"}',
                "expected_confidence": 0.87
            },
            # Text format with percentage
            {
                "llm_analysis_raw_response": "I am 78% confident in this analysis.",
                "expected_confidence": 0.78
            },
            # Text format with decimal
            {
                "llm_analysis_raw_response": "Analysis confidence: 0.91",
                "expected_confidence": 0.91
            },
            # Malformed JSON with extractable number (falls back to pattern-based)
            {
                "llm_analysis_raw_response": '{"confidence": 0.85,} confidence: 0.85',
                "expected_confidence": 0.85
            }
        ]
        
        for test_case in test_cases:
            requirements = {
                "description": "Test requirement",
                "llm_analysis_raw_response": test_case["llm_analysis_raw_response"]
            }
            
            recommendations = await self.service.generate_recommendations(
                [self.mock_match], requirements, "test_session"
            )
            
            assert len(recommendations) == 1
            assert recommendations[0].confidence == test_case["expected_confidence"], \
                f"Failed for response: {test_case['llm_analysis_raw_response']}"
    
    @pytest.mark.asyncio
    async def test_confidence_validation_in_integration(self):
        """Test confidence validation in full integration flow."""
        # Test out-of-range values are clamped
        test_cases = [
            {"llm_analysis_confidence_level": -0.5, "expected": 0.0},
            {"llm_analysis_confidence_level": 1.5, "expected": 1.0},
            {"llm_analysis_confidence_level": 0.5, "expected": 0.5},
        ]
        
        for test_case in test_cases:
            requirements = {
                "description": "Test requirement",
                **test_case
            }
            
            recommendations = await self.service.generate_recommendations(
                [self.mock_match], requirements, "test_session"
            )
            
            assert len(recommendations) == 1
            assert recommendations[0].confidence == test_case["expected"]
    
    @pytest.mark.asyncio
    async def test_confidence_with_feasibility_adjustment(self):
        """Test confidence adjustment based on feasibility in integration."""
        # Test that feasibility affects final confidence
        base_requirements = {
            "description": "Test requirement",
            "llm_analysis_confidence_level": 0.9
        }
        
        # Test different feasibility levels
        feasibility_cases = [
            ("Automatable", 0.9),  # Should keep LLM confidence
            ("Partially Automatable", 0.9),  # Should keep LLM confidence
            ("Not Automatable", 0.9),  # Should keep LLM confidence
        ]
        
        for feasibility, expected_confidence in feasibility_cases:
            requirements = {
                **base_requirements,
                "llm_analysis_automation_feasibility": feasibility
            }
            
            recommendations = await self.service.generate_recommendations(
                [self.mock_match], requirements, "test_session"
            )
            
            assert len(recommendations) == 1
            assert recommendations[0].confidence == expected_confidence
            assert recommendations[0].feasibility == feasibility
    
    @pytest.mark.asyncio
    async def test_confidence_logging_integration(self):
        """Test that confidence extraction and calculation includes proper logging."""
        requirements = {
            "description": "Test requirement",
            "llm_analysis_confidence_level": 0.85
        }
        
        with patch('app.services.recommendation.app_logger') as mock_logger:
            await self.service.generate_recommendations(
                [self.mock_match], requirements, "test_session"
            )
            
            # Verify logging occurred
            assert mock_logger.info.called
            
            # Check for confidence-related log messages
            log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
            confidence_logs = [call for call in log_calls if "confidence" in call.lower()]
            assert len(confidence_logs) > 0, "Expected confidence-related log messages"
            
            # Check for source tracking
            source_logs = [call for call in log_calls if "(source:" in call]
            assert len(source_logs) > 0, "Expected source tracking in logs"
    
    @pytest.mark.asyncio
    async def test_confidence_error_handling_integration(self):
        """Test confidence error handling in full integration flow."""
        # Test with invalid confidence that should fallback to pattern-based
        requirements = {
            "description": "Test requirement",
            "llm_analysis_confidence_level": "invalid_value"
        }
        
        recommendations = await self.service.generate_recommendations(
            [self.mock_match], requirements, "test_session"
        )
        
        # Should still generate recommendation with pattern-based confidence
        assert len(recommendations) == 1
        assert 0.0 <= recommendations[0].confidence <= 1.0
        
        # Test with completely missing confidence data
        minimal_requirements = {"description": "Minimal requirement"}
        
        recommendations = await self.service.generate_recommendations(
            [self.mock_match], minimal_requirements, "test_session"
        )
        
        # Should still work with pattern-based confidence
        assert len(recommendations) == 1
        assert 0.0 <= recommendations[0].confidence <= 1.0
    
    def test_confidence_api_serialization(self):
        """Test that confidence values serialize correctly for API responses."""
        # Test various confidence values
        test_confidences = [0.0, 0.1234, 0.5, 0.8567, 0.999, 1.0]
        
        for confidence in test_confidences:
            recommendation = Recommendation(
                pattern_id="API-001",
                feasibility="Automatable",
                confidence=confidence,
                tech_stack=["Python"],
                reasoning="API test"
            )
            
            # Test serialization (as would happen in API)
            serialized = {
                "pattern_id": recommendation.pattern_id,
                "feasibility": recommendation.feasibility,
                "confidence": recommendation.confidence,
                "tech_stack": recommendation.tech_stack,
                "reasoning": recommendation.reasoning
            }
            
            # Verify confidence is preserved correctly
            assert serialized["confidence"] == confidence
            assert isinstance(serialized["confidence"], float)
    
    @pytest.mark.asyncio
    async def test_multiple_recommendations_confidence_sorting(self):
        """Test that multiple recommendations are sorted by confidence correctly."""
        # Create multiple matches with different confidence levels
        matches = [
            MatchResult(
                pattern_id="HIGH-001",
                pattern_name="High Confidence Pattern",
                feasibility="Automatable",
                tech_stack=["Python"],
                confidence=0.9,
                tag_score=0.9,
                vector_score=0.8,
                blended_score=0.85,
                rationale="High confidence match"
            ),
            MatchResult(
                pattern_id="LOW-001",
                pattern_name="Low Confidence Pattern",
                feasibility="Partially Automatable",
                tech_stack=["Java"],
                confidence=0.6,
                tag_score=0.6,
                vector_score=0.5,
                blended_score=0.55,
                rationale="Low confidence match"
            ),
            MatchResult(
                pattern_id="MED-001",
                pattern_name="Medium Confidence Pattern",
                feasibility="Automatable",
                tech_stack=["JavaScript"],
                confidence=0.75,
                tag_score=0.7,
                vector_score=0.7,
                blended_score=0.7,
                rationale="Medium confidence match"
            )
        ]
        
        requirements = {"description": "Multi-pattern test"}
        
        recommendations = await self.service.generate_recommendations(
            matches, requirements, "test_session"
        )
        
        # Verify recommendations are sorted by confidence (descending)
        assert len(recommendations) == 3
        for i in range(len(recommendations) - 1):
            assert recommendations[i].confidence >= recommendations[i + 1].confidence, \
                f"Recommendations not sorted by confidence: {[r.confidence for r in recommendations]}"