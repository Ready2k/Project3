"""
Unit tests for the User Education and Guidance System.

Tests comprehensive user guidance generation, educational content delivery,
and appeal mechanism functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.security.user_education import (
    UserEducationSystem, UserGuidanceMessage, GuidanceType, AppealRequest
)
from app.security.attack_patterns import (
    SecurityDecision, SecurityAction, AttackPattern, AttackSeverity
)


class TestUserEducationSystem:
    """Test the UserEducationSystem class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.education_system = UserEducationSystem()
    
    def test_initialization(self):
        """Test UserEducationSystem initialization."""
        assert self.education_system is not None
        assert len(self.education_system.guidance_templates) > 0
        assert len(self.education_system.acceptable_examples) > 0
        assert len(self.education_system.educational_content) > 0
        assert isinstance(self.education_system.appeal_requests, dict)
    
    def test_guidance_templates_structure(self):
        """Test that guidance templates have required structure."""
        for category, template in self.education_system.guidance_templates.items():
            assert "title" in template
            assert "explanation" in template
            assert "guidance" in template
            assert "examples" in template
            assert isinstance(template["examples"], list)
            assert len(template["examples"]) > 0
    
    def test_acceptable_examples_structure(self):
        """Test that acceptable examples have proper structure."""
        expected_categories = [
            "process_automation", "data_processing", 
            "communication_automation", "decision_support"
        ]
        
        for category in expected_categories:
            assert category in self.education_system.acceptable_examples
            examples = self.education_system.acceptable_examples[category]
            assert isinstance(examples, list)
            assert len(examples) > 0
            
            # Check that examples are properly formatted
            for example in examples:
                assert isinstance(example, str)
                assert len(example) > 10  # Reasonable length
    
    def test_educational_content_completeness(self):
        """Test that educational content covers all required topics."""
        expected_topics = [
            "system_purpose", "how_to_use", "what_system_provides",
            "what_system_cannot_do", "security_measures"
        ]
        
        for topic in expected_topics:
            assert topic in self.education_system.educational_content
            content = self.education_system.educational_content[topic]
            assert isinstance(content, str)
            assert len(content) > 50  # Substantial content
    
    def test_determine_primary_attack_category(self):
        """Test attack category determination logic."""
        # Test prompt injection patterns
        injection_patterns = [
            AttackPattern(
                id="PAT-014", category="C", name="Ignore Instructions",
                description="Test", pattern_regex="", semantic_indicators=[],
                severity=AttackSeverity.HIGH, response_action=SecurityAction.BLOCK,
                examples=[], false_positive_indicators=[]
            )
        ]
        
        category = self.education_system._determine_primary_attack_category(injection_patterns)
        assert category == "prompt_injection"
        
        # Test out of scope patterns
        scope_patterns = [
            AttackPattern(
                id="PAT-009", category="B", name="Text Summarization",
                description="Test", pattern_regex="", semantic_indicators=[],
                severity=AttackSeverity.MEDIUM, response_action=SecurityAction.BLOCK,
                examples=[], false_positive_indicators=[]
            )
        ]
        
        category = self.education_system._determine_primary_attack_category(scope_patterns)
        assert category == "out_of_scope"
        
        # Test data extraction patterns
        data_patterns = [
            AttackPattern(
                id="PAT-026", category="F", name="Environment Variables",
                description="Test", pattern_regex="", semantic_indicators=[],
                severity=AttackSeverity.HIGH, response_action=SecurityAction.BLOCK,
                examples=[], false_positive_indicators=[]
            )
        ]
        
        category = self.education_system._determine_primary_attack_category(data_patterns)
        assert category == "data_extraction"
        
        # Test empty patterns
        category = self.education_system._determine_primary_attack_category([])
        assert category == "general"
    
    def test_generate_block_guidance(self):
        """Test block guidance generation."""
        # Create test security decision
        attack_patterns = [
            AttackPattern(
                id="PAT-014", category="C", name="Ignore Instructions",
                description="Test injection", pattern_regex="", semantic_indicators=[],
                severity=AttackSeverity.HIGH, response_action=SecurityAction.BLOCK,
                examples=[], false_positive_indicators=[]
            )
        ]
        
        decision = SecurityDecision(
            action=SecurityAction.BLOCK,
            confidence=0.9,
            detected_attacks=attack_patterns,
            user_message="",
            technical_details=""
        )
        
        guidance = self.education_system.generate_user_guidance(decision, "test_session")
        
        assert guidance.message_type == GuidanceType.BLOCK_MESSAGE
        assert guidance.title == "Prompt Injection Detected"
        assert len(guidance.content) > 100  # Substantial content
        assert len(guidance.action_items) > 0
        assert guidance.appeal_info is not None
        assert "test_session" in guidance.appeal_info
    
    def test_generate_flag_guidance(self):
        """Test flag guidance generation."""
        attack_patterns = [
            AttackPattern(
                id="PAT-018", category="D", name="Base64 Payload",
                description="Test obfuscation", pattern_regex="", semantic_indicators=[],
                severity=AttackSeverity.MEDIUM, response_action=SecurityAction.FLAG,
                examples=[], false_positive_indicators=[]
            )
        ]
        
        decision = SecurityDecision(
            action=SecurityAction.FLAG,
            confidence=0.7,
            detected_attacks=attack_patterns,
            sanitized_input="cleaned input",
            user_message="",
            technical_details=""
        )
        
        guidance = self.education_system.generate_user_guidance(decision, "test_session")
        
        assert guidance.message_type == GuidanceType.FLAG_MESSAGE
        assert guidance.title == "Request Flagged for Review"
        assert "sanitized" in guidance.content.lower() or "cleaned" in guidance.content.lower()
        assert len(guidance.action_items) > 0
        assert guidance.appeal_info is not None
    
    def test_generate_pass_guidance(self):
        """Test guidance for passed requests."""
        decision = SecurityDecision(
            action=SecurityAction.PASS,
            confidence=0.1,
            detected_attacks=[],
            user_message="",
            technical_details=""
        )
        
        guidance = self.education_system.generate_user_guidance(decision, "test_session")
        
        assert guidance.message_type == GuidanceType.EDUCATIONAL
        assert guidance.title == "Request Processed Successfully"
    
    def test_get_educational_content(self):
        """Test educational content retrieval."""
        # Test getting all content
        all_content = self.education_system.get_educational_content("all")
        assert len(all_content) > 0
        assert "system_purpose" in all_content
        
        # Test getting specific topic
        purpose_content = self.education_system.get_educational_content("system_purpose")
        assert "system_purpose" in purpose_content
        assert len(purpose_content) == 1
        
        # Test non-existent topic
        empty_content = self.education_system.get_educational_content("nonexistent")
        assert "nonexistent" in empty_content
        assert empty_content["nonexistent"] == ""
    
    def test_get_acceptable_examples(self):
        """Test acceptable examples retrieval."""
        # Test getting all examples
        all_examples = self.education_system.get_acceptable_examples("all")
        assert len(all_examples) > 0
        assert "process_automation" in all_examples
        
        # Test getting specific category
        process_examples = self.education_system.get_acceptable_examples("process_automation")
        assert "process_automation" in process_examples
        assert len(process_examples) == 1
        assert len(process_examples["process_automation"]) > 0
        
        # Test non-existent category
        empty_examples = self.education_system.get_acceptable_examples("nonexistent")
        assert "nonexistent" in empty_examples
        assert empty_examples["nonexistent"] == []
    
    def test_submit_appeal(self):
        """Test appeal submission."""
        appeal_id = self.education_system.submit_appeal(
            request_id="req_123",
            original_input="Test input",
            user_explanation="This was legitimate",
            business_justification="We need to automate our process",
            contact_info="user@example.com"
        )
        
        assert appeal_id.startswith("appeal_req_123_")
        assert appeal_id in self.education_system.appeal_requests
        
        appeal = self.education_system.appeal_requests[appeal_id]
        assert appeal.request_id == "req_123"
        assert appeal.original_input == "Test input"
        assert appeal.user_explanation == "This was legitimate"
        assert appeal.business_justification == "We need to automate our process"
        assert appeal.contact_info == "user@example.com"
        assert appeal.status == "pending"
        assert isinstance(appeal.timestamp, datetime)
    
    def test_get_appeal_status(self):
        """Test appeal status retrieval."""
        # Submit an appeal first
        appeal_id = self.education_system.submit_appeal(
            "req_123", "Test input", "Explanation", "Justification", "contact@example.com"
        )
        
        # Test getting existing appeal status
        status = self.education_system.get_appeal_status(appeal_id)
        assert status is not None
        assert status["appeal_id"] == appeal_id
        assert status["status"] == "pending"
        assert status["request_id"] == "req_123"
        assert "submitted" in status
        
        # Test getting non-existent appeal status
        status = self.education_system.get_appeal_status("nonexistent")
        assert status is None
    
    def test_process_appeal(self):
        """Test appeal processing."""
        # Submit an appeal first
        appeal_id = self.education_system.submit_appeal(
            "req_123", "Test input", "Explanation", "Justification", "contact@example.com"
        )
        
        # Test valid decision
        result = self.education_system.process_appeal(appeal_id, "approved", "Looks legitimate")
        assert result is True
        assert self.education_system.appeal_requests[appeal_id].status == "approved"
        
        # Test invalid decision
        result = self.education_system.process_appeal(appeal_id, "invalid_status")
        assert result is False
        
        # Test non-existent appeal
        result = self.education_system.process_appeal("nonexistent", "approved")
        assert result is False
    
    def test_get_pending_appeals(self):
        """Test pending appeals retrieval."""
        # Submit multiple appeals
        appeal_id1 = self.education_system.submit_appeal(
            "req_1", "Input 1", "Explanation 1", "Justification 1", "user1@example.com"
        )
        appeal_id2 = self.education_system.submit_appeal(
            "req_2", "Input 2", "Explanation 2", "Justification 2", "user2@example.com"
        )
        
        # Process one appeal
        self.education_system.process_appeal(appeal_id1, "approved")
        
        # Get pending appeals
        pending = self.education_system.get_pending_appeals()
        
        assert len(pending) == 1
        assert pending[0]["appeal_id"] == appeal_id2
        assert pending[0]["request_id"] == "req_2"
        assert "submitted" in pending[0]
        assert "user_explanation" in pending[0]
        assert "business_justification" in pending[0]
        assert "contact_info" in pending[0]
        assert "original_input" in pending[0]
    
    def test_generate_system_documentation(self):
        """Test system documentation generation."""
        doc = self.education_system.generate_system_documentation()
        
        assert isinstance(doc, str)
        assert len(doc) > 1000  # Substantial documentation
        assert "# Business Automation Feasibility Assessment System" in doc
        assert "## System Purpose" in doc
        assert "## How to Use This System" in doc
        assert "## Examples of Acceptable Requests" in doc
        assert "## Appeal Process" in doc
        
        # Check that examples are included
        for examples in self.education_system.acceptable_examples.values():
            for example in examples[:2]:  # Check first few examples
                assert example in doc
    
    def test_get_guidance_statistics(self):
        """Test guidance statistics retrieval."""
        stats = self.education_system.get_guidance_statistics()
        
        assert "guidance_templates" in stats
        assert "acceptable_examples" in stats
        assert "educational_topics" in stats
        assert "pending_appeals" in stats
        assert "total_appeals" in stats
        
        assert stats["guidance_templates"] > 0
        assert stats["acceptable_examples"] > 0
        assert stats["educational_topics"] > 0
        assert stats["pending_appeals"] >= 0
        assert stats["total_appeals"] >= 0
    
    def test_guidance_message_structure(self):
        """Test UserGuidanceMessage structure and validation."""
        message = UserGuidanceMessage(
            message_type=GuidanceType.BLOCK_MESSAGE,
            title="Test Title",
            content="Test content",
            examples=["Example 1", "Example 2"],
            action_items=["Action 1", "Action 2"],
            appeal_info="Appeal information"
        )
        
        assert message.message_type == GuidanceType.BLOCK_MESSAGE
        assert message.title == "Test Title"
        assert message.content == "Test content"
        assert len(message.examples) == 2
        assert len(message.action_items) == 2
        assert message.appeal_info == "Appeal information"
    
    def test_appeal_request_structure(self):
        """Test AppealRequest structure and validation."""
        timestamp = datetime.now()
        appeal = AppealRequest(
            request_id="req_123",
            original_input="Test input",
            user_explanation="Test explanation",
            business_justification="Test justification",
            contact_info="test@example.com",
            timestamp=timestamp,
            status="pending"
        )
        
        assert appeal.request_id == "req_123"
        assert appeal.original_input == "Test input"
        assert appeal.user_explanation == "Test explanation"
        assert appeal.business_justification == "Test justification"
        assert appeal.contact_info == "test@example.com"
        assert appeal.timestamp == timestamp
        assert appeal.status == "pending"
    
    def test_category_specific_guidance(self):
        """Test that different attack categories generate appropriate guidance."""
        categories_to_test = [
            ("prompt_injection", "C"),
            ("out_of_scope", "B"),
            ("data_extraction", "F"),
            ("system_manipulation", "K"),
            ("tool_abuse", "E")
        ]
        
        for expected_category, pattern_category in categories_to_test:
            attack_pattern = AttackPattern(
                id=f"PAT-TEST", category=pattern_category, name="Test Pattern",
                description="Test", pattern_regex="", semantic_indicators=[],
                severity=AttackSeverity.HIGH, response_action=SecurityAction.BLOCK,
                examples=[], false_positive_indicators=[]
            )
            
            decision = SecurityDecision(
                action=SecurityAction.BLOCK,
                confidence=0.9,
                detected_attacks=[attack_pattern],
                user_message="",
                technical_details=""
            )
            
            guidance = self.education_system.generate_user_guidance(decision, "test_session")
            
            # Check that the guidance is appropriate for the category
            template = self.education_system.guidance_templates.get(expected_category)
            if template:
                assert guidance.title == template["title"]
                assert template["explanation"] in guidance.content
    
    def test_obfuscation_detection_in_guidance(self):
        """Test that obfuscation patterns are properly categorized."""
        obfuscation_patterns = [
            AttackPattern(
                id="PAT-018", category="D", name="Base64 Payload Detection",
                description="base64 encoded content", pattern_regex="", semantic_indicators=[],
                severity=AttackSeverity.MEDIUM, response_action=SecurityAction.FLAG,
                examples=[], false_positive_indicators=[]
            )
        ]
        
        category = self.education_system._determine_primary_attack_category(obfuscation_patterns)
        assert category == "obfuscation"
        
        decision = SecurityDecision(
            action=SecurityAction.BLOCK,
            confidence=0.8,
            detected_attacks=obfuscation_patterns,
            user_message="",
            technical_details=""
        )
        
        guidance = self.education_system.generate_user_guidance(decision, "test_session")
        assert guidance.title == "Obfuscated Content Detected"
    
    def test_multilingual_attack_guidance(self):
        """Test multilingual attack guidance generation."""
        multilingual_patterns = [
            AttackPattern(
                id="PAT-035", category="I", name="Non-English Malicious Instructions",
                description="multilingual attack", pattern_regex="", semantic_indicators=[],
                severity=AttackSeverity.MEDIUM, response_action=SecurityAction.BLOCK,
                examples=[], false_positive_indicators=[]
            )
        ]
        
        decision = SecurityDecision(
            action=SecurityAction.BLOCK,
            confidence=0.8,
            detected_attacks=multilingual_patterns,
            user_message="",
            technical_details=""
        )
        
        guidance = self.education_system.generate_user_guidance(decision, "test_session")
        assert guidance.title == "Multilingual Security Issue Detected"
        assert "multilingual business requirements" in guidance.content
    
    def test_long_input_truncation_in_appeals(self):
        """Test that long inputs are properly truncated in appeal listings."""
        long_input = "A" * 300  # 300 character input
        
        appeal_id = self.education_system.submit_appeal(
            "req_123", long_input, "Explanation", "Justification", "contact@example.com"
        )
        
        pending = self.education_system.get_pending_appeals()
        assert len(pending) == 1
        
        # Check that input is truncated
        original_input = pending[0]["original_input"]
        assert len(original_input) <= 203  # 200 + "..."
        assert original_input.endswith("...")
    
    def test_guidance_with_sanitized_input(self):
        """Test guidance generation when sanitized input is available."""
        decision = SecurityDecision(
            action=SecurityAction.FLAG,
            confidence=0.6,
            detected_attacks=[],
            sanitized_input="This is the cleaned version",
            user_message="",
            technical_details=""
        )
        
        guidance = self.education_system.generate_user_guidance(decision, "test_session")
        
        assert "sanitized" in guidance.content.lower() or "cleaned" in guidance.content.lower()
        assert guidance.message_type == GuidanceType.FLAG_MESSAGE
    
    def test_guidance_without_sanitized_input(self):
        """Test guidance generation when no sanitized input is available."""
        decision = SecurityDecision(
            action=SecurityAction.FLAG,
            confidence=0.6,
            detected_attacks=[],
            sanitized_input=None,
            user_message="",
            technical_details=""
        )
        
        guidance = self.education_system.generate_user_guidance(decision, "test_session")
        
        assert "review your request" in guidance.content.lower()
        assert guidance.message_type == GuidanceType.FLAG_MESSAGE


class TestUserGuidanceIntegration:
    """Test integration between UserEducationSystem and other components."""
    
    def test_guidance_message_formatting(self):
        """Test that guidance messages can be properly formatted."""
        guidance = UserGuidanceMessage(
            message_type=GuidanceType.BLOCK_MESSAGE,
            title="Test Block",
            content="This is test content with multiple lines.\n\nSecond paragraph.",
            examples=["Example 1", "Example 2"],
            action_items=["Do this", "Do that"],
            appeal_info="Contact support with ID: test_123"
        )
        
        # Test that all components are present
        assert guidance.title == "Test Block"
        assert "multiple lines" in guidance.content
        assert "Second paragraph" in guidance.content
        assert len(guidance.examples) == 2
        assert len(guidance.action_items) == 2
        assert "test_123" in guidance.appeal_info
    
    def test_educational_content_completeness(self):
        """Test that educational content covers all necessary aspects."""
        education_system = UserEducationSystem()
        
        # Test system documentation completeness
        doc = education_system.generate_system_documentation()
        
        required_sections = [
            "System Purpose", "How to Use", "What This System Provides",
            "What This System Cannot Do", "Security Measures", "Examples",
            "Getting Help", "Appeal Process"
        ]
        
        for section in required_sections:
            assert section in doc
        
        # Test that examples are comprehensive
        all_examples = education_system.get_acceptable_examples("all")
        total_examples = sum(len(examples) for examples in all_examples.values())
        assert total_examples >= 20  # Should have substantial examples
    
    def test_appeal_workflow(self):
        """Test complete appeal workflow."""
        education_system = UserEducationSystem()
        
        # Step 1: Submit appeal
        appeal_id = education_system.submit_appeal(
            "req_123", "Original input", "User explanation", 
            "Business justification", "user@example.com"
        )
        
        # Step 2: Check it appears in pending
        pending = education_system.get_pending_appeals()
        assert len(pending) == 1
        assert pending[0]["appeal_id"] == appeal_id
        
        # Step 3: Process appeal
        result = education_system.process_appeal(appeal_id, "approved", "Looks good")
        assert result is True
        
        # Step 4: Check it's no longer pending
        pending = education_system.get_pending_appeals()
        assert len(pending) == 0
        
        # Step 5: Check status
        status = education_system.get_appeal_status(appeal_id)
        assert status["status"] == "approved"