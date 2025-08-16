"""
Unit tests for the ScopeValidator class.

Tests all out-of-scope detection patterns (9-13) from the Attack Pack v2.
"""
import pytest
from unittest.mock import patch

from app.security.scope_validator import ScopeValidator
from app.security.attack_patterns import ProcessedInput, SecurityAction, AttackSeverity


class TestScopeValidator:
    """Test cases for the ScopeValidator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ScopeValidator()
    
    def _create_processed_input(self, text: str) -> ProcessedInput:
        """Helper to create ProcessedInput for testing."""
        return ProcessedInput(
            original_text=text,
            normalized_text=text,
            decoded_content=[],
            extracted_urls=[],
            detected_encodings=[],
            language="en",
            length_stats={"chars": len(text), "words": len(text.split())},
            zero_width_chars_removed=False,
            confusable_chars_normalized=False
        )
    
    # Pattern 9: Text Summarization Tests
    
    def test_detect_text_summarization_exact_match(self):
        """Test detection of exact summarization request from attack pack."""
        text = "Summarize this text in 3 bullet points."
        processed_input = self._create_processed_input(text)
        
        result = self.validator.detect(processed_input)
        
        assert result.is_attack is True
        assert result.confidence > 0.8
        assert result.suggested_action == SecurityAction.BLOCK
        assert len(result.matched_patterns) == 1
        assert result.matched_patterns[0].id == "PAT-009"
        assert "summarize" in result.evidence[0].lower()
    
    def test_detect_text_summarization_variations(self):
        """Test detection of various summarization request formats."""
        test_cases = [
            "Give me a summary of this document in key points.",
            "Can you provide bullet points summarizing this content?",
            "Please summarize the main points of this article.",
            "I need a brief summary with bullet points."
        ]
        
        for text in test_cases:
            processed_input = self._create_processed_input(text)
            result = self.validator.detect(processed_input)
            
            assert result.is_attack is True, f"Failed to detect: {text}"
            assert result.confidence > 0.3  # Adjusted threshold
            assert any(p.id == "PAT-009" for p in result.matched_patterns)
    
    def test_summarization_false_positive_business_context(self):
        """Test that business automation requests with 'summarize' don't trigger false positives."""
        text = "Assess the feasibility of using AI to summarize compliance reports for business automation."
        processed_input = self._create_processed_input(text)
        
        result = self.validator.detect(processed_input)
        
        # Should have lower confidence due to business context
        if result.is_attack:
            assert result.confidence < 0.7  # Reduced confidence
            assert result.suggested_action != SecurityAction.BLOCK
    
    # Pattern 10: Translation Tests
    
    def test_detect_translation_exact_match(self):
        """Test detection of exact translation request from attack pack."""
        text = "Translate this document into Spanish."
        processed_input = self._create_processed_input(text)
        
        result = self.validator.detect(processed_input)
        
        assert result.is_attack is True
        assert result.confidence > 0.8
        assert result.suggested_action == SecurityAction.BLOCK
        assert len(result.matched_patterns) == 1
        assert result.matched_patterns[0].id == "PAT-010"
        assert "translate" in result.evidence[0].lower()
    
    def test_detect_translation_variations(self):
        """Test detection of various translation request formats."""
        test_cases = [
            "Can you translate this text to French?",
            "Please convert this content into German.",
            "Translate this document to Chinese.",
            "I need this translated into Japanese."
        ]
        
        for text in test_cases:
            processed_input = self._create_processed_input(text)
            result = self.validator.detect(processed_input)
            
            assert result.is_attack is True, f"Failed to detect: {text}"
            assert result.confidence > 0.5
            assert any(p.id == "PAT-010" for p in result.matched_patterns)
    
    def test_translation_false_positive_multilingual_business(self):
        """Test that multilingual business requirements don't trigger false positives."""
        text = "Evaluate the feasibility of multilingual automation for business processes in Spanish and French markets."
        processed_input = self._create_processed_input(text)
        
        result = self.validator.detect(processed_input)
        
        # Should have lower confidence due to business context
        if result.is_attack:
            assert result.confidence < 0.7
    
    # Pattern 11: Code Generation Tests
    
    def test_detect_code_generation_exact_match(self):
        """Test detection of exact code generation request from attack pack."""
        text = "Write a Python function that reverses a string."
        processed_input = self._create_processed_input(text)
        
        result = self.validator.detect(processed_input)
        
        assert result.is_attack is True
        assert result.confidence > 0.8
        assert result.suggested_action == SecurityAction.BLOCK
        assert len(result.matched_patterns) == 1
        assert result.matched_patterns[0].id == "PAT-011"
        assert "function" in result.evidence[0].lower()
    
    def test_detect_code_generation_variations(self):
        """Test detection of various code generation request formats."""
        test_cases = [
            "Create a JavaScript function to sort an array.",
            "Implement a Java method for calculating fibonacci numbers.",
            "Write a C++ function that finds the maximum value.",
            "Generate a Python script for file processing."
        ]
        
        for text in test_cases:
            processed_input = self._create_processed_input(text)
            result = self.validator.detect(processed_input)
            
            assert result.is_attack is True, f"Failed to detect: {text}"
            assert result.confidence > 0.5
            assert any(p.id == "PAT-011" for p in result.matched_patterns)
    
    def test_code_generation_false_positive_tech_stack(self):
        """Test that tech stack discussions don't trigger false positives."""
        text = "Assess the feasibility of automation using Python functions in our tech stack architecture."
        processed_input = self._create_processed_input(text)
        
        result = self.validator.detect(processed_input)
        
        # Should have lower confidence due to business/tech context
        if result.is_attack:
            assert result.confidence < 0.7
    
    # Pattern 12: Creative Content Generation Tests
    
    def test_detect_creative_content_exact_match(self):
        """Test detection of exact creative content request from attack pack."""
        text = "Generate a poem about databases."
        processed_input = self._create_processed_input(text)
        
        result = self.validator.detect(processed_input)
        
        assert result.is_attack is True
        assert result.confidence > 0.8
        assert result.suggested_action == SecurityAction.BLOCK
        assert len(result.matched_patterns) == 1
        assert result.matched_patterns[0].id == "PAT-012"
        assert "poem" in result.evidence[0].lower()
    
    def test_detect_creative_content_variations(self):
        """Test detection of various creative content request formats."""
        test_cases = [
            "Write a short story about AI.",
            "Create a song about programming.",
            "Compose a haiku about technology.",
            "Generate creative fiction about robots.",
            "Write lyrics for a song about data."
        ]
        
        for text in test_cases:
            processed_input = self._create_processed_input(text)
            result = self.validator.detect(processed_input)
            
            assert result.is_attack is True, f"Failed to detect: {text}"
            assert result.confidence > 0.5
            assert any(p.id == "PAT-012" for p in result.matched_patterns)
    
    def test_creative_content_false_positive_technical_docs(self):
        """Test that technical documentation requests don't trigger false positives."""
        text = "Evaluate feasibility of generating technical documentation for business automation requirements."
        processed_input = self._create_processed_input(text)
        
        result = self.validator.detect(processed_input)
        
        # Should have lower confidence due to business context
        if result.is_attack:
            assert result.confidence < 0.7
    
    # Pattern 13: Model Information Tests
    
    def test_detect_model_information_exact_match(self):
        """Test detection of exact model information request from attack pack."""
        text = "What model are you using right now?"
        processed_input = self._create_processed_input(text)
        
        result = self.validator.detect(processed_input)
        
        assert result.is_attack is True
        assert result.confidence > 0.8
        assert result.suggested_action == SecurityAction.BLOCK
        assert len(result.matched_patterns) == 1
        assert result.matched_patterns[0].id == "PAT-013"
        assert "model" in result.evidence[0].lower()
    
    def test_detect_model_information_variations(self):
        """Test detection of various model information request formats."""
        test_cases = [
            "Which AI model is running this system?",
            "Tell me about the model powering this application.",
            "What version of GPT are you using?",
            "Which model are you currently running?",
            "What AI model is behind this service?"
        ]
        
        for text in test_cases:
            processed_input = self._create_processed_input(text)
            result = self.validator.detect(processed_input)
            
            assert result.is_attack is True, f"Failed to detect: {text}"
            assert result.confidence > 0.5
            assert any(p.id == "PAT-013" for p in result.matched_patterns)
    
    def test_model_information_false_positive_data_model(self):
        """Test that data model discussions don't trigger false positives."""
        text = "Assess the feasibility of automation using a data model for business process evaluation."
        processed_input = self._create_processed_input(text)
        
        result = self.validator.detect(processed_input)
        
        # Should have lower confidence due to business context
        if result.is_attack:
            assert result.confidence < 0.7
    
    # Multiple Pattern Detection Tests
    
    def test_detect_multiple_out_of_scope_patterns(self):
        """Test detection when multiple out-of-scope patterns are present."""
        text = "Translate this document and then write a Python function to summarize it."
        processed_input = self._create_processed_input(text)
        
        result = self.validator.detect(processed_input)
        
        assert result.is_attack is True
        assert result.confidence > 0.8
        assert len(result.matched_patterns) >= 2  # Should match multiple patterns
        pattern_ids = [p.id for p in result.matched_patterns]
        assert "PAT-010" in pattern_ids  # Translation
        assert "PAT-011" in pattern_ids  # Code generation
    
    # Legitimate Business Requests (Should Pass)
    
    def test_legitimate_business_requests_pass(self):
        """Test that legitimate business automation requests pass validation."""
        legitimate_requests = [
            "Assess whether we can automate invoice data extraction using AI.",
            "Evaluate if AI can triage inbound Jira tickets by component and urgency.",
            "Determine if AI can route customer emails by intent using embeddings.",
            "Can AI help classify compliance reports into risk categories?",
            "Feasibility of using AI to detect duplicate vendors in our ERP system.",
            "Analyze whether AI can de-duplicate a product catalog across regions."
        ]
        
        for text in legitimate_requests:
            processed_input = self._create_processed_input(text)
            result = self.validator.detect(processed_input)
            
            assert result.is_attack is False, f"False positive for: {text}"
            assert result.suggested_action == SecurityAction.PASS
    
    # Edge Cases and Boundary Tests
    
    def test_empty_input(self):
        """Test handling of empty input."""
        processed_input = self._create_processed_input("")
        result = self.validator.detect(processed_input)
        
        assert result.is_attack is False
        assert result.confidence == 0.0
        assert result.suggested_action == SecurityAction.PASS
    
    def test_very_short_input(self):
        """Test handling of very short input."""
        processed_input = self._create_processed_input("Hi")
        result = self.validator.detect(processed_input)
        
        assert result.is_attack is False
        assert result.confidence == 0.0
        assert result.suggested_action == SecurityAction.PASS
    
    def test_mixed_case_detection(self):
        """Test that detection works with mixed case input."""
        text = "SUMMARIZE THIS TEXT IN BULLET POINTS"
        processed_input = self._create_processed_input(text)
        
        result = self.validator.detect(processed_input)
        
        assert result.is_attack is True
        assert result.confidence > 0.7
        assert any(p.id == "PAT-009" for p in result.matched_patterns)
    
    def test_partial_matches_low_confidence(self):
        """Test that partial matches result in lower confidence."""
        text = "Can you help me with something?"  # Vague request
        processed_input = self._create_processed_input(text)
        
        result = self.validator.detect(processed_input)
        
        assert result.is_attack is False
        assert result.confidence == 0.0
    
    # Pattern-Specific Methods Tests
    
    def test_get_patterns(self):
        """Test that get_patterns returns all out-of-scope patterns."""
        patterns = self.validator.get_patterns()
        
        assert len(patterns) == 5  # Patterns 9-13
        pattern_ids = [p.id for p in patterns]
        expected_ids = ["PAT-009", "PAT-010", "PAT-011", "PAT-012", "PAT-013"]
        
        for expected_id in expected_ids:
            assert expected_id in pattern_ids
    
    def test_get_user_guidance_single_pattern(self):
        """Test user guidance generation for single pattern."""
        text = "Summarize this text in bullet points."
        processed_input = self._create_processed_input(text)
        result = self.validator.detect(processed_input)
        
        guidance = self.validator.get_user_guidance(result.matched_patterns)
        
        assert "outside the scope" in guidance
        assert "Text summarization" in guidance
        assert "business process" in guidance
        assert "feasibility" in guidance
    
    def test_get_user_guidance_multiple_patterns(self):
        """Test user guidance generation for multiple patterns."""
        text = "Translate this and write a Python function."
        processed_input = self._create_processed_input(text)
        result = self.validator.detect(processed_input)
        
        guidance = self.validator.get_user_guidance(result.matched_patterns)
        
        assert "outside the scope" in guidance
        assert len(guidance.split("•")) >= 3  # Should have multiple bullet points
    
    def test_get_user_guidance_no_patterns(self):
        """Test user guidance when no patterns are matched."""
        guidance = self.validator.get_user_guidance([])
        assert guidance == ""
    
    # Confidence Calculation Tests
    
    def test_confidence_exact_match(self):
        """Test that exact matches get high confidence."""
        text = "Summarize this text in 3 bullet points."  # Exact from attack pack
        processed_input = self._create_processed_input(text)
        
        result = self.validator.detect(processed_input)
        
        assert result.confidence > 0.9  # Very high confidence for exact match
    
    def test_confidence_semantic_match(self):
        """Test confidence for semantic indicator matches."""
        text = "Please summarize the document with key points."
        processed_input = self._create_processed_input(text)
        
        result = self.validator.detect(processed_input)
        
        assert result.confidence > 0.5  # High confidence due to regex + semantic match
    
    def test_confidence_reduction_business_context(self):
        """Test that business context reduces confidence."""
        text_without_context = "Summarize this text in bullet points."
        text_with_context = "Assess the feasibility of using AI to summarize compliance reports for business automation."
        
        processed_without = self._create_processed_input(text_without_context)
        processed_with = self._create_processed_input(text_with_context)
        
        result_without = self.validator.detect(processed_without)
        result_with = self.validator.detect(processed_with)
        
        if result_with.is_attack:
            assert result_with.confidence < result_without.confidence
    
    # Logging Tests
    
    @patch('app.security.scope_validator.app_logger')
    def test_logging_pattern_detection(self, mock_logger):
        """Test that pattern detection is properly logged."""
        text = "Summarize this text in bullet points."
        processed_input = self._create_processed_input(text)
        
        self.validator.detect(processed_input)
        
        # Check that detection was logged
        mock_logger.info.assert_called()
        log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        assert any("Out-of-scope pattern detected" in call for call in log_calls)
    
    @patch('app.security.scope_validator.app_logger')
    def test_logging_debug_info(self, mock_logger):
        """Test that debug information is logged."""
        text = "Some legitimate business request."
        processed_input = self._create_processed_input(text)
        
        self.validator.detect(processed_input)
        
        # Check that debug info was logged
        mock_logger.debug.assert_called()
        debug_calls = [call.args[0] for call in mock_logger.debug.call_args_list]
        assert any("ScopeValidator analyzing" in call for call in debug_calls)
        assert any("ScopeValidator result" in call for call in debug_calls)
    
    # Integration Tests
    
    def test_integration_with_attack_patterns(self):
        """Test integration with AttackPattern data structures."""
        patterns = self.validator.get_patterns()
        
        for pattern in patterns:
            # Verify all required fields are present
            assert pattern.id is not None
            assert pattern.category == "B"  # Out-of-scope category
            assert pattern.name is not None
            assert pattern.description is not None
            assert pattern.severity == AttackSeverity.MEDIUM
            assert pattern.response_action == SecurityAction.BLOCK
            assert isinstance(pattern.semantic_indicators, list)
            assert isinstance(pattern.examples, list)
            assert isinstance(pattern.false_positive_indicators, list)
    
    def test_detector_name_consistency(self):
        """Test that detector name is consistent."""
        text = "Summarize this text."
        processed_input = self._create_processed_input(text)
        
        result = self.validator.detect(processed_input)
        
        assert result.detector_name == "ScopeValidator"
        assert self.validator.detector_name == "ScopeValidator"