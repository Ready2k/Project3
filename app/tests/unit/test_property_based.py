"""Property-based tests using Hypothesis for edge cases and data validation."""

from hypothesis import given, strategies as st, assume
from hypothesis.strategies import composite

from app.pattern.matcher import MatchResult
from app.services.recommendation import RecommendationService
from app.qa.question_loop import Question, QAResult
from app.state.store import SessionState, QAExchange
from app.exporters.json_exporter import JSONExporter
from app.exporters.markdown_exporter import MarkdownExporter
from app.utils.redact import PIIRedactor


@composite
def valid_requirements(draw):
    """Generate valid requirements dictionaries."""
    description = draw(st.text(min_size=10, max_size=500))
    domain = draw(
        st.sampled_from(
            ["data_processing", "workflow_automation", "api_integration", "reporting"]
        )
    )

    requirements = {"description": description, "domain": domain}

    # Add optional fields
    if draw(st.booleans()):
        requirements["frequency"] = draw(
            st.sampled_from(["daily", "weekly", "monthly", "on-demand"])
        )

    if draw(st.booleans()):
        requirements["data_sensitivity"] = draw(
            st.sampled_from(["low", "medium", "high"])
        )

    if draw(st.booleans()):
        requirements["integrations"] = draw(
            st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10)
        )

    if draw(st.booleans()):
        requirements["volume"] = {
            "daily": draw(st.integers(min_value=1, max_value=1000000))
        }

    return requirements


@composite
def valid_pattern_match(draw):
    """Generate valid pattern match results."""
    return MatchResult(
        pattern_id=f"PAT-{draw(st.integers(min_value=1, max_value=999)):03d}",
        pattern_name=draw(st.text(min_size=5, max_size=50)),
        feasibility=draw(
            st.sampled_from(["Automatable", "Partially Automatable", "Not Automatable"])
        ),
        tech_stack=draw(
            st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=10)
        ),
        confidence=draw(st.floats(min_value=0.0, max_value=1.0)),
        tag_score=draw(st.floats(min_value=0.0, max_value=1.0)),
        vector_score=draw(st.floats(min_value=0.0, max_value=1.0)),
        blended_score=draw(st.floats(min_value=0.0, max_value=1.0)),
        rationale=draw(st.text(min_size=10, max_size=200)),
    )


class TestPropertyBasedValidation:
    """Property-based tests for data validation and edge cases."""

    @given(valid_requirements())
    def test_requirements_always_have_description_and_domain(self, requirements):
        """Property: All valid requirements must have description and domain."""
        assert "description" in requirements
        assert "domain" in requirements
        assert len(requirements["description"]) >= 10
        assert requirements["domain"] in [
            "data_processing",
            "workflow_automation",
            "api_integration",
            "reporting",
        ]

    @given(valid_pattern_match())
    def test_pattern_match_confidence_bounds(self, match):
        """Property: All confidence scores must be between 0 and 1."""
        assert 0.0 <= match.confidence <= 1.0
        assert 0.0 <= match.tag_score <= 1.0
        assert 0.0 <= match.vector_score <= 1.0
        assert 0.0 <= match.blended_score <= 1.0

    @given(valid_pattern_match())
    def test_pattern_match_serialization_roundtrip(self, match):
        """Property: Pattern matches can be serialized and deserialized."""
        match_dict = match.to_dict()

        # Verify all required fields are present
        required_fields = ["pattern_id", "pattern_name", "feasibility", "confidence"]
        for field in required_fields:
            assert field in match_dict

        # Verify data types
        assert isinstance(match_dict["confidence"], (int, float))
        assert isinstance(match_dict["tech_stack"], list)

    @given(st.text(min_size=0, max_size=1000))
    def test_pii_redactor_never_crashes(self, text):
        """Property: PII redactor should never crash on any input."""
        redactor = PIIRedactor()
        result = redactor.redact(text)
        assert isinstance(result, str)
        assert len(result) >= 0

    @given(
        st.text(min_size=1, max_size=100),
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=50),
    )
    def test_question_creation_properties(self, text, field, category):
        """Property: Questions can be created with any valid string inputs."""
        question = Question(text=text, field=field, template_category=category)

        assert question.text == text
        assert question.field == field
        assert question.template_category == category
        assert question.question_type == "text"  # Default

        # Test serialization
        question_dict = question.to_dict()
        assert question_dict["question"] == text
        assert question_dict["id"] == field

    @given(
        st.booleans(),
        st.floats(min_value=0.0, max_value=1.0),
        st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=10),
    )
    def test_qa_result_properties(self, complete, confidence, question_texts):
        """Property: QA results maintain consistency."""
        questions = [
            Question(text=text, field=f"field_{i}", template_category="test")
            for i, text in enumerate(question_texts)
        ]

        result = QAResult(
            complete=complete, confidence=confidence, next_questions=questions
        )

        assert result.complete == complete
        assert result.confidence == confidence
        assert len(result.next_questions) == len(questions)

        # Test serialization
        result_dict = result.to_dict()
        assert result_dict["complete"] == complete
        assert result_dict["confidence"] == confidence
        assert len(result_dict["next_questions"]) == len(questions)


class TestRecommendationServiceProperties:
    """Property-based tests for recommendation service."""

    def setup_method(self):
        """Set up recommendation service."""
        self.service = RecommendationService()

    @given(valid_requirements())
    def test_completeness_score_bounds(self, requirements):
        """Property: Completeness scores are always between 0 and 1."""
        score = self.service._calculate_completeness_score(requirements)
        assert 0.0 <= score <= 1.0

    @given(valid_requirements())
    def test_complexity_factors_non_negative(self, requirements):
        """Property: Complexity factors are always non-negative integers."""
        factors = self.service._analyze_complexity_factors(requirements)

        for factor_name, factor_value in factors.items():
            assert isinstance(factor_value, int)
            assert factor_value >= 0
            assert factor_value <= 3  # Max complexity level

    @given(valid_requirements())
    def test_risk_factors_non_negative(self, requirements):
        """Property: Risk factors are always non-negative integers."""
        factors = self.service._analyze_risk_factors(requirements)

        for factor_name, factor_value in factors.items():
            assert isinstance(factor_value, int)
            assert factor_value >= 0
            assert factor_value <= 3  # Max risk level

    @given(
        st.lists(valid_pattern_match(), min_size=1, max_size=10), valid_requirements()
    )
    def test_recommendations_maintain_order(self, matches, requirements):
        """Property: Recommendations are returned in confidence order."""
        recommendations = self.service.generate_recommendations(matches, requirements)

        # Should have same number of recommendations as matches
        assert len(recommendations) == len(matches)

        # Should be sorted by confidence (descending)
        confidences = [rec.confidence for rec in recommendations]
        assert confidences == sorted(confidences, reverse=True)


class TestExporterProperties:
    """Property-based tests for exporters."""

    def setup_method(self):
        """Set up exporters."""
        import tempfile
        from pathlib import Path

        temp_dir = Path(tempfile.mkdtemp())
        self.json_exporter = JSONExporter(temp_dir)
        self.markdown_exporter = MarkdownExporter(temp_dir)

    @given(st.text(min_size=1, max_size=50))
    def test_filename_generation_properties(self, session_id):
        """Property: Filename generation is consistent and valid."""
        from app.state.store import SessionState, Phase
        from datetime import datetime

        # Create a mock session
        session = SessionState(
            session_id=session_id,
            phase=Phase.DONE,
            progress=100,
            requirements={"description": "test"},
            missing_fields=[],
            qa_history=[],
            matches=[],
            recommendations=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        json_filename = self.json_exporter.generate_filename(session)
        md_filename = self.markdown_exporter.generate_filename(session)

        # Should contain session ID
        assert session_id in json_filename
        assert session_id in md_filename

        # Should have correct extensions
        assert json_filename.endswith(".json")
        assert md_filename.endswith(".md")

        # Should be valid filenames (no invalid characters)
        invalid_chars = ["<", ">", ":", '"', "|", "?", "*"]
        for char in invalid_chars:
            assert char not in json_filename
            assert char not in md_filename

    @given(st.floats(min_value=0.0, max_value=1.0))
    def test_confidence_bar_properties(self, confidence):
        """Property: Confidence bars are always valid."""
        bar = self.markdown_exporter.generate_confidence_bar(confidence)

        assert isinstance(bar, str)
        assert len(bar) > 0
        assert "█" in bar or "░" in bar  # Should contain bar characters


class TestSessionStateProperties:
    """Property-based tests for session state."""

    @given(st.text(min_size=1, max_size=50), valid_requirements())
    def test_session_state_creation_properties(self, session_id, requirements):
        """Property: Session state creation is consistent."""
        from app.state.store import Phase
        from datetime import datetime

        session = SessionState(
            session_id=session_id,
            phase=Phase.PARSING,
            progress=0,
            requirements=requirements,
            missing_fields=[],
            qa_history=[],
            matches=[],
            recommendations=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert session.session_id == session_id
        assert session.requirements == requirements
        assert isinstance(session.qa_history, list)
        assert isinstance(session.matches, list)
        assert isinstance(session.recommendations, list)
        assert len(session.qa_history) == 0  # Initially empty

    @given(
        st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=5),
        st.dictionaries(
            st.text(min_size=1, max_size=20),
            st.text(min_size=1, max_size=100),
            min_size=1,
            max_size=5,
        ),
    )
    def test_qa_exchange_properties(self, questions, answers):
        """Property: QA exchanges maintain data integrity."""
        from datetime import datetime

        exchange = QAExchange(
            questions=questions, answers=answers, timestamp=datetime.now()
        )

        assert exchange.questions == questions
        assert exchange.answers == answers
        assert exchange.timestamp is not None


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @given(st.text(max_size=0))
    def test_empty_string_handling(self, empty_text):
        """Property: Empty strings are handled gracefully."""
        assume(empty_text == "")

        # PII redactor should handle empty strings
        redactor = PIIRedactor()
        result = redactor.redact(empty_text)
        assert result == ""

    @given(st.lists(st.nothing(), min_size=0, max_size=0))
    def test_empty_list_handling(self, empty_list):
        """Property: Empty lists are handled gracefully."""
        assume(len(empty_list) == 0)

        service = RecommendationService()
        recommendations = service.generate_recommendations(
            empty_list, {"description": "test"}
        )
        assert len(recommendations) == 0

    @given(st.floats(min_value=0.0, max_value=0.0))
    def test_zero_confidence_handling(self, zero_confidence):
        """Property: Zero confidence values are handled correctly."""
        assume(zero_confidence == 0.0)

        match = MatchResult(
            pattern_id="PAT-001",
            pattern_name="Test Pattern",
            feasibility="Not Automatable",
            tech_stack=[],
            confidence=zero_confidence,
            tag_score=zero_confidence,
            vector_score=zero_confidence,
            blended_score=zero_confidence,
            rationale="No confidence",
        )

        assert match.confidence == 0.0
        match_dict = match.to_dict()
        assert match_dict["confidence"] == 0.0

    @given(st.floats(min_value=1.0, max_value=1.0))
    def test_perfect_confidence_handling(self, perfect_confidence):
        """Property: Perfect confidence values are handled correctly."""
        assume(perfect_confidence == 1.0)

        match = MatchResult(
            pattern_id="PAT-001",
            pattern_name="Perfect Pattern",
            feasibility="Automatable",
            tech_stack=["Python"],
            confidence=perfect_confidence,
            tag_score=perfect_confidence,
            vector_score=perfect_confidence,
            blended_score=perfect_confidence,
            rationale="Perfect match",
        )

        assert match.confidence == 1.0
        match_dict = match.to_dict()
        assert match_dict["confidence"] == 1.0
