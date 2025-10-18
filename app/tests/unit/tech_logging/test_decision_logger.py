"""Unit tests for DecisionLogger."""

import pytest
from unittest.mock import Mock

from app.services.tech_logging.decision_logger import (
    DecisionLogger,
    DecisionCriteria,
    OptionEvaluation,
    DecisionResult,
)
from app.services.tech_logging.tech_stack_logger import TechStackLogger, LogCategory


class TestDecisionLogger:
    """Test cases for DecisionLogger."""

    @pytest.fixture
    def mock_tech_logger(self):
        """Mock TechStackLogger for testing."""
        return Mock(spec=TechStackLogger)

    @pytest.fixture
    def decision_logger(self, mock_tech_logger):
        """Create DecisionLogger instance for testing."""
        return DecisionLogger(mock_tech_logger)

    def test_start_decision(self, decision_logger, mock_tech_logger):
        """Test starting a decision process."""
        decision_id = "test_decision_123"

        context = decision_logger.start_decision(
            decision_id=decision_id,
            decision_type="technology_selection",
            component="TechStackGenerator",
            operation="select_technologies",
            input_data={"requirements": "test requirements"},
            constraints={"banned_tools": ["tool1"]},
            available_options=["option1", "option2", "option3"],
        )

        assert context.decision_id == decision_id
        assert context.decision_type == "technology_selection"
        assert context.component == "TechStackGenerator"
        assert context.operation == "select_technologies"
        assert context.input_data["requirements"] == "test requirements"
        assert context.constraints["banned_tools"] == ["tool1"]
        assert context.available_options == ["option1", "option2", "option3"]

        # Verify logging call
        mock_tech_logger.log_info.assert_called_once()
        call_args = mock_tech_logger.log_info.call_args
        assert call_args[0][0] == LogCategory.DECISION_MAKING
        assert call_args[0][1] == "TechStackGenerator"
        assert call_args[0][2] == "select_technologies"
        assert "Started decision process" in call_args[0][3]

    def test_add_decision_criteria(self, decision_logger, mock_tech_logger):
        """Test adding decision criteria."""
        decision_id = "test_decision_123"

        # Start decision first
        decision_logger.start_decision(
            decision_id=decision_id,
            decision_type="technology_selection",
            component="TechStackGenerator",
            operation="select_technologies",
            input_data={},
        )

        # Add criteria
        criteria = [
            DecisionCriteria(
                criterion_name="performance",
                weight=0.4,
                description="Performance requirements",
                evaluation_method="benchmark_scores",
            ),
            DecisionCriteria(
                criterion_name="cost",
                weight=0.3,
                description="Cost considerations",
                evaluation_method="pricing_analysis",
            ),
        ]

        decision_logger.add_decision_criteria(decision_id, criteria)

        # Verify criteria were stored
        decision_data = decision_logger._active_decisions[decision_id]
        assert len(decision_data["criteria"]) == 2
        assert decision_data["criteria"][0].criterion_name == "performance"
        assert decision_data["criteria"][1].criterion_name == "cost"

        # Verify logging call
        assert mock_tech_logger.log_debug.called

    def test_log_option_evaluation(self, decision_logger, mock_tech_logger):
        """Test logging option evaluation."""
        decision_id = "test_decision_123"

        # Start decision first
        decision_logger.start_decision(
            decision_id=decision_id,
            decision_type="technology_selection",
            component="TechStackGenerator",
            operation="select_technologies",
            input_data={},
        )

        # Log option evaluation
        evaluation = OptionEvaluation(
            option_name="FastAPI",
            scores={"performance": 0.9, "cost": 0.8, "ease_of_use": 0.85},
            total_score=0.85,
            confidence=0.9,
            reasoning="FastAPI provides excellent performance with good cost-effectiveness",
            pros=["High performance", "Good documentation", "Type safety"],
            cons=["Newer framework", "Smaller ecosystem"],
        )

        decision_logger.log_option_evaluation(decision_id, evaluation)

        # Verify evaluation was stored
        decision_data = decision_logger._active_decisions[decision_id]
        assert len(decision_data["evaluations"]) == 1
        assert decision_data["evaluations"][0].option_name == "FastAPI"
        assert decision_data["evaluations"][0].total_score == 0.85

        # Verify logging call
        mock_tech_logger.log_debug.assert_called()
        call_args = mock_tech_logger.log_debug.call_args
        assert call_args[1]["confidence_score"] == 0.9

    def test_complete_decision(self, decision_logger, mock_tech_logger):
        """Test completing a decision process."""
        decision_id = "test_decision_123"

        # Start decision
        decision_logger.start_decision(
            decision_id=decision_id,
            decision_type="technology_selection",
            component="TechStackGenerator",
            operation="select_technologies",
            input_data={"requirements": "API framework"},
        )

        # Add some evaluations
        evaluation = OptionEvaluation(
            option_name="FastAPI",
            scores={"performance": 0.9},
            total_score=0.9,
            confidence=0.85,
            reasoning="Best option",
            pros=["Fast"],
            cons=["New"],
        )
        decision_logger.log_option_evaluation(decision_id, evaluation)

        # Complete decision
        result = DecisionResult(
            selected_option="FastAPI",
            confidence_score=0.85,
            reasoning="FastAPI selected for its performance and modern features",
            alternatives_considered=["Django", "Flask"],
            decision_factors={"performance_weight": 0.4, "cost_weight": 0.3},
        )

        trace = decision_logger.complete_decision(decision_id, result)

        # Verify trace structure
        assert trace.context.decision_id == decision_id
        assert trace.result.selected_option == "FastAPI"
        assert trace.result.confidence_score == 0.85
        assert len(trace.evaluations) == 1
        assert trace.duration_ms > 0

        # Verify decision was removed from active decisions
        assert decision_id not in decision_logger._active_decisions

        # Verify logging call
        mock_tech_logger.log_info.assert_called()

    def test_log_technology_selection(self, decision_logger, mock_tech_logger):
        """Test logging technology selection decision."""
        decision_logger.log_technology_selection(
            component="TechStackGenerator",
            operation="generate_tech_stack",
            selected_technologies=["FastAPI", "PostgreSQL", "Redis"],
            explicit_technologies=["FastAPI", "PostgreSQL"],
            contextual_technologies=["Redis", "Docker"],
            rejected_technologies=["Django", "MySQL"],
            selection_reasoning={
                "FastAPI": "High performance and modern features",
                "PostgreSQL": "Robust relational database",
                "Redis": "Fast caching solution",
            },
            confidence_scores={"FastAPI": 0.9, "PostgreSQL": 0.85, "Redis": 0.8},
        )

        # Verify logging call
        mock_tech_logger.log_info.assert_called_once()
        call_args = mock_tech_logger.log_info.call_args

        assert call_args[0][0] == LogCategory.DECISION_MAKING
        assert call_args[0][1] == "TechStackGenerator"
        assert "Technology selection completed" in call_args[0][3]

        context = call_args[0][4]
        assert context["selected_technologies"] == ["FastAPI", "PostgreSQL", "Redis"]
        assert context["selection_stats"]["total_selected"] == 3
        assert context["selection_stats"]["explicit_selected"] == 2

    def test_log_conflict_resolution(self, decision_logger, mock_tech_logger):
        """Test logging conflict resolution."""
        decision_logger.log_conflict_resolution(
            component="TechStackGenerator",
            operation="resolve_conflicts",
            conflict_type="ecosystem_mismatch",
            conflicting_technologies=["AWS S3", "Azure Blob Storage"],
            resolution_strategy="prefer_explicit_mention",
            resolved_selection="AWS S3",
            resolution_reasoning="AWS S3 was explicitly mentioned in requirements",
            confidence_score=0.9,
        )

        # Verify logging call
        mock_tech_logger.log_info.assert_called_once()
        call_args = mock_tech_logger.log_info.call_args

        assert call_args[0][0] == LogCategory.DECISION_MAKING
        assert "Conflict resolved" in call_args[0][3]
        assert call_args[1]["confidence_score"] == 0.9

        context = call_args[0][4]
        assert context["conflict_type"] == "ecosystem_mismatch"
        assert context["resolved_selection"] == "AWS S3"

    def test_log_catalog_decision(self, decision_logger, mock_tech_logger):
        """Test logging catalog management decision."""
        decision_logger.log_catalog_decision(
            component="CatalogManager",
            operation="evaluate_technology",
            technology_name="NewFramework",
            decision_type="auto_add",
            reasoning="Technology mentioned frequently and has good metadata",
            metadata={"source": "llm_suggestion", "frequency": 5},
            confidence_score=0.75,
        )

        # Verify logging call
        mock_tech_logger.log_info.assert_called_once()
        call_args = mock_tech_logger.log_info.call_args

        assert call_args[0][0] == LogCategory.CATALOG_LOOKUP
        assert "Catalog decision" in call_args[0][3]
        assert call_args[1]["confidence_score"] == 0.75

        context = call_args[0][4]
        assert context["technology_name"] == "NewFramework"
        assert context["decision_type"] == "auto_add"

    def test_log_validation_decision(self, decision_logger, mock_tech_logger):
        """Test logging validation decision."""
        decision_logger.log_validation_decision(
            component="CompatibilityValidator",
            operation="validate_stack",
            validation_type="ecosystem_consistency",
            technologies=["AWS S3", "AWS Lambda", "AWS RDS"],
            validation_result=True,
            issues_found=[],
            resolution_actions=[],
            confidence_score=0.95,
        )

        # Verify logging call
        mock_tech_logger.log_info.assert_called_once()
        call_args = mock_tech_logger.log_info.call_args

        assert call_args[0][0] == LogCategory.VALIDATION
        assert "Validation ecosystem_consistency: PASSED" in call_args[0][3]
        assert call_args[1]["confidence_score"] == 0.95

        context = call_args[0][4]
        assert context["validation_result"] is True
        assert context["issue_count"] == 0

    def test_get_decision_summary(self, decision_logger, mock_tech_logger):
        """Test getting decision summary."""
        # Mock log entries
        mock_entries = [
            Mock(
                context={"decision_type": "technology_selection"},
                confidence_score=0.8,
                component="TechStackGenerator",
            ),
            Mock(
                context={"decision_type": "conflict_resolution"},
                confidence_score=0.9,
                component="TechStackGenerator",
            ),
            Mock(
                context={"decision_type": "technology_selection"},
                confidence_score=0.7,
                component="TechStackGenerator",
            ),
        ]

        mock_tech_logger.get_log_entries.return_value = mock_entries

        summary = decision_logger.get_decision_summary(component="TechStackGenerator")

        assert summary["total_decisions"] == 3
        assert summary["average_confidence"] == 0.8  # (0.8 + 0.9 + 0.7) / 3
        assert summary["decision_types"]["technology_selection"] == 2
        assert summary["decision_types"]["conflict_resolution"] == 1
        assert "TechStackGenerator" in summary["components"]

    def test_invalid_decision_id(self, decision_logger):
        """Test handling of invalid decision ID."""
        with pytest.raises(ValueError, match="No active decision found"):
            decision_logger.add_decision_criteria(
                "invalid_id", [DecisionCriteria("test", 1.0, "test", "test")]
            )

        with pytest.raises(ValueError, match="No active decision found"):
            decision_logger.log_option_evaluation(
                "invalid_id", OptionEvaluation("test", {}, 0.5, 0.5, "test", [], [])
            )

        with pytest.raises(ValueError, match="No active decision found"):
            decision_logger.complete_decision(
                "invalid_id", DecisionResult("test", 0.5, "test", [], {})
            )
