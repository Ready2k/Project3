"""Unit tests for enhanced LLM confidence extraction and validation."""

import pytest
import math
from unittest.mock import Mock, patch

from app.services.recommendation import RecommendationService
from app.pattern.matcher import MatchResult


class TestConfidenceExtraction:
    """Test cases for enhanced confidence extraction functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = RecommendationService()
        self.mock_match = MatchResult(
            pattern_id="TEST-001",
            pattern_name="Test Pattern",
            feasibility="Automatable",
            tech_stack=["Python", "FastAPI"],
            confidence=0.8,
            tag_score=0.9,
            vector_score=0.7,
            blended_score=0.8,
            rationale="Test pattern match"
        )
    
    def test_extract_llm_confidence_numeric_values(self):
        """Test extraction of numeric confidence values."""
        # Test valid float
        requirements = {"llm_analysis_confidence_level": 0.85}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.85
        
        # Test valid int
        requirements = {"llm_analysis_confidence_level": 1}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 1.0
        
        # Test zero
        requirements = {"llm_analysis_confidence_level": 0}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.0
    
    def test_extract_llm_confidence_string_values(self):
        """Test extraction from string values."""
        # Test string float
        requirements = {"llm_analysis_confidence_level": "0.75"}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.75
        
        # Test percentage string
        requirements = {"llm_analysis_confidence_level": "85%"}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.85
        
        # Test percentage over 100 (should be converted)
        requirements = {"llm_analysis_confidence_level": "150%"}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 1.0  # Clamped to max
        
        # Test text with confidence
        requirements = {"llm_analysis_confidence_level": "confidence: 0.92"}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.92
    
    def test_extract_llm_confidence_json_string(self):
        """Test extraction from JSON string values."""
        # Test JSON string
        requirements = {"llm_analysis_confidence_level": '{"confidence": 0.88}'}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.88
        
        # Test malformed JSON
        requirements = {"llm_analysis_confidence_level": '{"confidence": 0.88'}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.88  # Should extract number anyway
    
    def test_extract_llm_confidence_dict_values(self):
        """Test extraction from dictionary values."""
        # Test dict with confidence key
        requirements = {"llm_analysis_confidence_level": {"confidence": 0.91}}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.91
        
        # Test dict with score key
        requirements = {"llm_analysis_confidence_level": {"score": 0.77}}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.77
        
        # Test dict without confidence keys
        requirements = {"llm_analysis_confidence_level": {"other": 0.77}}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence is None
    
    def test_extract_llm_confidence_list_values(self):
        """Test extraction from list values."""
        # Test list with valid first element
        requirements = {"llm_analysis_confidence_level": [0.83, 0.92]}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.83
        
        # Test empty list
        requirements = {"llm_analysis_confidence_level": []}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence is None
    
    def test_extract_llm_confidence_invalid_values(self):
        """Test handling of invalid confidence values."""
        # Test boolean (should be rejected)
        requirements = {"llm_analysis_confidence_level": True}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence is None
        
        # Test None
        requirements = {"llm_analysis_confidence_level": None}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence is None
        
        # Test empty string
        requirements = {"llm_analysis_confidence_level": ""}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence is None
        
        # Test invalid string
        requirements = {"llm_analysis_confidence_level": "not a number"}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence is None
    
    def test_extract_llm_confidence_range_validation(self):
        """Test confidence range validation and clamping."""
        # Test negative value (should be clamped to 0)
        requirements = {"llm_analysis_confidence_level": -0.5}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.0
        
        # Test value over 1 (should be clamped to 1)
        requirements = {"llm_analysis_confidence_level": 1.5}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 1.0
        
        # Test NaN (should be rejected)
        requirements = {"llm_analysis_confidence_level": float('nan')}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence is None
        
        # Test infinity (should be rejected)
        requirements = {"llm_analysis_confidence_level": float('inf')}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence is None
    
    def test_extract_llm_confidence_multiple_sources(self):
        """Test extraction from multiple potential sources."""
        # Test fallback to alternative keys
        requirements = {"confidence_level": 0.79}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.79
        
        # Test priority order (first found wins)
        requirements = {
            "llm_analysis_confidence_level": 0.85,
            "confidence_level": 0.75,
            "confidence": 0.65
        }
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.85
    
    def test_extract_confidence_from_raw_response(self):
        """Test extraction from raw LLM response."""
        # Test JSON in response
        requirements = {
            "llm_analysis_raw_response": '{"analysis": "good", "confidence": 0.87, "other": "data"}'
        }
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.87
        
        # Test text pattern in response
        requirements = {
            "llm_analysis_raw_response": "The analysis shows confidence: 0.93 in this assessment."
        }
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.93
        
        # Test percentage pattern in response
        requirements = {
            "llm_analysis_raw_response": "I am 89% confident in this recommendation."
        }
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.89
    
    def test_calculate_confidence_with_llm_value(self):
        """Test full confidence calculation with LLM value."""
        requirements = {
            "llm_analysis_confidence_level": 0.92,
            "description": "Test requirement"
        }
        
        confidence = self.service._calculate_confidence(
            self.mock_match, requirements, "Automatable"
        )
        
        # Should use LLM confidence directly
        assert confidence == 0.92
    
    def test_calculate_confidence_fallback_to_pattern(self):
        """Test confidence calculation fallback to pattern-based when LLM unavailable."""
        requirements = {
            "description": "Test requirement",
            "domain": "test",
            "workflow_steps": ["step1", "step2"]
        }
        
        confidence = self.service._calculate_confidence(
            self.mock_match, requirements, "Automatable"
        )
        
        # Should use pattern-based calculation
        assert 0.0 <= confidence <= 1.0
        assert confidence != 0.92  # Should not be the LLM value
    
    def test_calculate_confidence_with_invalid_llm_fallback(self):
        """Test confidence calculation with invalid LLM value falls back to pattern."""
        requirements = {
            "llm_analysis_confidence_level": "invalid",
            "description": "Test requirement"
        }
        
        confidence = self.service._calculate_confidence(
            self.mock_match, requirements, "Automatable"
        )
        
        # Should fallback to pattern-based calculation
        assert 0.0 <= confidence <= 1.0
    
    @patch('app.services.recommendation.app_logger')
    def test_confidence_extraction_logging(self, mock_logger):
        """Test that confidence extraction includes proper logging."""
        requirements = {"llm_analysis_confidence_level": 0.85}
        
        confidence = self.service._extract_llm_confidence(requirements)
        
        # Verify logging calls were made
        assert mock_logger.info.called
        assert mock_logger.debug.called
        
        # Check that confidence value and source are logged
        log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        assert any("0.85" in call for call in log_calls)
        assert any("llm_analysis_confidence_level" in call for call in log_calls)
    
    @patch('app.services.recommendation.app_logger')
    def test_confidence_validation_error_logging(self, mock_logger):
        """Test that validation errors are properly logged."""
        requirements = {"llm_analysis_confidence_level": True}  # Invalid boolean
        
        confidence = self.service._extract_llm_confidence(requirements)
        
        # Should return None and log warning
        assert confidence is None
        assert mock_logger.warning.called
        
        # Check warning message content
        warning_calls = [call.args[0] for call in mock_logger.warning.call_args_list]
        assert any("is boolean" in call for call in warning_calls)
    
    def test_edge_cases_and_robustness(self):
        """Test edge cases and robustness of confidence extraction."""
        # Test very small positive number
        requirements = {"llm_analysis_confidence_level": 1e-10}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 1e-10
        
        # Test very close to 1
        requirements = {"llm_analysis_confidence_level": 0.9999999}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.9999999
        
        # Test scientific notation string
        requirements = {"llm_analysis_confidence_level": "8.5e-1"}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.85
        
        # Test nested dict structure
        requirements = {"llm_analysis_confidence_level": {"result": {"confidence": 0.76}}}
        confidence = self.service._extract_llm_confidence(requirements)
        # Should not find nested confidence (current implementation only looks one level deep)
        assert confidence is None
    
    def test_malformed_json_edge_cases(self):
        """Test various malformed JSON scenarios."""
        # Test JSON with trailing comma
        requirements = {"llm_analysis_confidence_level": '{"confidence": 0.88,}'}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.88  # Should extract number despite malformed JSON
        
        # Test JSON with single quotes (invalid JSON)
        requirements = {"llm_analysis_confidence_level": "{'confidence': 0.77}"}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.77  # Should extract number from text
        
        # Test JSON with unquoted keys
        requirements = {"llm_analysis_confidence_level": "{confidence: 0.66}"}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.66  # Should extract number from text
        
        # Test completely broken JSON with confidence
        requirements = {"llm_analysis_confidence_level": "broken{json confidence: 0.55 more}text"}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.55
    
    def test_percentage_variations(self):
        """Test various percentage format variations."""
        # Test percentage with decimal
        requirements = {"llm_analysis_confidence_level": "87.5%"}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.875
        
        # Test percentage over 100 (should be clamped)
        requirements = {"llm_analysis_confidence_level": "120%"}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 1.0
        
        # Test percentage with spaces
        requirements = {"llm_analysis_confidence_level": "85 %"}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.85
        
        # Test multiple percentages (should take first)
        requirements = {"llm_analysis_confidence_level": "85% confident, 90% sure"}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.85
    
    def test_text_pattern_variations(self):
        """Test various text patterns for confidence extraction."""
        # Test "confidence is" pattern
        requirements = {"llm_analysis_confidence_level": "confidence is 0.82"}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.82
        
        # Test "score:" pattern
        requirements = {"llm_analysis_confidence_level": "score: 0.91"}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.91
        
        # Test "X% confident" pattern
        requirements = {"llm_analysis_confidence_level": "I am 78% confident"}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.78
        
        # Test mixed case
        requirements = {"llm_analysis_confidence_level": "CONFIDENCE: 0.93"}
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.93
    
    def test_complex_llm_response_patterns(self):
        """Test complex LLM response patterns."""
        # Test response with single JSON containing confidence
        requirements = {
            "llm_analysis_raw_response": '''
            Analysis result: {"confidence": 0.87, "feasibility": "high"}
            '''
        }
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.87
        
        # Test response with confidence in text and JSON (JSON should win)
        requirements = {
            "llm_analysis_raw_response": '''
            I am 75% confident in this analysis.
            {"analysis": "detailed", "confidence": 0.92}
            '''
        }
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.92
        
        # Test response with only text patterns
        requirements = {
            "llm_analysis_raw_response": '''
            Based on the analysis, confidence: 0.84
            in this recommendation. The feasibility is high.
            '''
        }
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.84
        
        # Test response where JSON has no confidence, falls back to text
        requirements = {
            "llm_analysis_raw_response": '''
            Analysis: {"result": "good", "status": "complete"}
            I am 78% confident in this assessment.
            '''
        }
        confidence = self.service._extract_llm_confidence(requirements)
        assert confidence == 0.78
    
    def test_confidence_display_formatting(self):
        """Test confidence display formatting for UI."""
        # Test various confidence values and their expected display format
        test_cases = [
            (0.0, "0%"),
            (0.1, "10%"),
            (0.5, "50%"),
            (0.85, "85%"),
            (0.8567, "86%"),  # Should round to nearest percent
            (1.0, "100%"),
            (0.999, "100%"),  # Should round up
            (0.001, "0%"),    # Should round down
        ]
        
        for confidence_value, expected_display in test_cases:
            # Test the formatting used in the UI (:.0%)
            formatted = f"{confidence_value:.0%}"
            assert formatted == expected_display, f"Confidence {confidence_value} should format as {expected_display}, got {formatted}"
    
    def test_pattern_based_confidence_fallback_scenarios(self):
        """Test pattern-based confidence calculation in various scenarios."""
        # Test with high-quality match and complete requirements
        complete_requirements = {
            "description": "Detailed requirement description",
            "domain": "test_domain",
            "workflow_steps": ["step1", "step2", "step3"],
            "integrations": ["api1", "api2"],
            "data_sensitivity": "medium",
            "volume": {"daily": 1000},
            "sla": {"response_time_ms": 2000}
        }
        
        high_quality_match = MatchResult(
            pattern_id="HIGH-001",
            pattern_name="High Quality Pattern",
            feasibility="Automatable",
            tech_stack=["Python", "FastAPI"],
            confidence=0.9,
            tag_score=0.95,
            vector_score=0.85,
            blended_score=0.9,
            rationale="High quality match"
        )
        
        confidence = self.service._calculate_confidence(
            high_quality_match, complete_requirements, "Automatable"
        )
        
        # Should be high confidence due to good match and complete requirements
        assert confidence > 0.7
        assert confidence <= 1.0
        
        # Test with low-quality match and incomplete requirements
        incomplete_requirements = {"description": "Basic description"}
        
        low_quality_match = MatchResult(
            pattern_id="LOW-001",
            pattern_name="Low Quality Pattern",
            feasibility="Not Automatable",
            tech_stack=[],
            confidence=0.3,
            tag_score=0.2,
            vector_score=0.1,
            blended_score=0.15,
            rationale="Low quality match"
        )
        
        confidence = self.service._calculate_confidence(
            low_quality_match, incomplete_requirements, "Not Automatable"
        )
        
        # Should be low confidence due to poor match and incomplete requirements
        assert confidence < 0.5
        assert confidence >= 0.0
    
    def test_confidence_source_tracking(self):
        """Test that confidence source is properly tracked and logged."""
        # Test LLM source - need to test the full _calculate_confidence method
        requirements_with_llm = {"llm_analysis_confidence_level": 0.85}
        
        with patch('app.services.recommendation.app_logger') as mock_logger:
            confidence = self.service._calculate_confidence(
                self.mock_match, requirements_with_llm, "Automatable"
            )
            
            # Verify LLM source is logged
            log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
            assert any("(source: LLM)" in call for call in log_calls)
        
        # Test pattern-based source
        requirements_without_llm = {"description": "Test requirement"}
        
        with patch('app.services.recommendation.app_logger') as mock_logger:
            confidence = self.service._calculate_confidence(
                self.mock_match, requirements_without_llm, "Automatable"
            )
            
            # Verify pattern-based source is logged
            log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
            assert any("(source: pattern-based)" in call for call in log_calls)
    
    def test_confidence_validation_comprehensive(self):
        """Test comprehensive confidence validation scenarios."""
        # Test boundary values
        boundary_tests = [
            (0.0, 0.0),      # Minimum valid
            (1.0, 1.0),      # Maximum valid
            (-0.1, 0.0),     # Below minimum (should clamp)
            (1.1, 1.0),      # Above maximum (should clamp)
            (-999, 0.0),     # Far below minimum
            (999, 1.0),      # Far above maximum
        ]
        
        for input_value, expected_output in boundary_tests:
            requirements = {"llm_analysis_confidence_level": input_value}
            confidence = self.service._extract_llm_confidence(requirements)
            assert confidence == expected_output, f"Input {input_value} should produce {expected_output}, got {confidence}"
        
        # Test invalid values that should return None
        invalid_tests = [
            float('nan'),
            float('inf'),
            float('-inf'),
        ]
        
        for invalid_value in invalid_tests:
            requirements = {"llm_analysis_confidence_level": invalid_value}
            confidence = self.service._extract_llm_confidence(requirements)
            assert confidence is None, f"Invalid value {invalid_value} should return None, got {confidence}"