"""Tests for context-aware LLM prompt generator."""

import pytest
from unittest.mock import Mock, patch

from app.services.context_aware_prompt_generator import (
    ContextAwareLLMPromptGenerator,
    PromptContext,
    PromptValidationResult,
)
from app.services.requirement_parsing.base import TechContext, DomainContext
from app.services.catalog.models import TechEntry, EcosystemType, MaturityLevel


class TestContextAwareLLMPromptGenerator:
    """Test cases for ContextAwareLLMPromptGenerator."""

    @pytest.fixture
    def mock_catalog_manager(self):
        """Create mock catalog manager."""
        mock_manager = Mock()

        # Create sample technologies
        sample_techs = {
            "fastapi": TechEntry(
                id="fastapi",
                name="FastAPI",
                canonical_name="FastAPI",
                category="frameworks",
                description="Modern, fast web framework for building APIs with Python",
                aliases=["fast-api", "fast_api"],
                ecosystem=EcosystemType.OPEN_SOURCE,
                integrates_with=["python", "pydantic", "uvicorn"],
                alternatives=["django", "flask"],
                tags=["python", "api", "async", "web"],
                use_cases=["rest_api", "microservices", "web_backend"],
                license="MIT",
                maturity=MaturityLevel.STABLE,
            ),
            "aws_lambda": TechEntry(
                id="aws_lambda",
                name="AWS Lambda",
                canonical_name="AWS Lambda",
                category="serverless",
                description="Serverless compute service by Amazon Web Services",
                aliases=["lambda", "amazon lambda"],
                ecosystem=EcosystemType.AWS,
                integrates_with=["aws_api_gateway", "aws_s3", "aws_dynamodb"],
                alternatives=["azure_functions", "google_cloud_functions"],
                tags=["serverless", "compute", "aws"],
                use_cases=["serverless_api", "event_processing", "microservices"],
                license="Commercial",
                maturity=MaturityLevel.MATURE,
            ),
            "langchain": TechEntry(
                id="langchain",
                name="LangChain",
                canonical_name="LangChain",
                category="agentic",
                description="Framework for developing applications powered by language models",
                aliases=["lang-chain", "lang_chain"],
                ecosystem=EcosystemType.OPEN_SOURCE,
                integrates_with=["openai", "python", "faiss"],
                alternatives=["llamaindex", "semantic_kernel"],
                tags=["llm", "ai", "agents", "python"],
                use_cases=["chatbots", "document_qa", "agents"],
                license="MIT",
                maturity=MaturityLevel.STABLE,
            ),
        }

        mock_manager.technologies = sample_techs
        return mock_manager

    @pytest.fixture
    def sample_tech_context(self):
        """Create sample technology context."""
        return TechContext(
            explicit_technologies={"FastAPI": 0.95, "AWS Lambda": 0.9},
            contextual_technologies={"PostgreSQL": 0.8, "Redis": 0.7},
            domain_context=DomainContext(
                primary_domain="web_api",
                sub_domains=["automation"],
                complexity_indicators=["high_throughput", "real_time"],
            ),
            ecosystem_preference="aws",
            integration_requirements=["database", "cache"],
            banned_tools={"Django", "MySQL"},
            priority_weights={"FastAPI": 1.0, "AWS Lambda": 1.0, "PostgreSQL": 0.8},
        )

    @pytest.fixture
    def sample_requirements(self):
        """Create sample requirements."""
        return {
            "description": "Build a high-performance API for real-time data processing",
            "domain": "web_api",
            "volume": {"requests_per_second": 1000},
            "integrations": ["database", "cache"],
            "data_sensitivity": "internal",
            "compliance": ["SOC2"],
            "sla": {"availability": "99.9%", "response_time": "100ms"},
        }

    @pytest.fixture
    def prompt_generator(self, mock_catalog_manager):
        """Create prompt generator with mocked dependencies."""
        with patch(
            "app.services.context_aware_prompt_generator.require_service"
        ) as mock_require:
            mock_logger = Mock()
            mock_require.return_value = mock_logger

            generator = ContextAwareLLMPromptGenerator(
                catalog_manager=mock_catalog_manager
            )
            return generator

    def test_initialization(self, prompt_generator):
        """Test prompt generator initialization."""
        assert prompt_generator is not None
        assert prompt_generator.catalog_manager is not None
        assert hasattr(prompt_generator, "base_template")
        assert hasattr(prompt_generator, "base_selection_rules")
        assert hasattr(prompt_generator, "base_priority_instructions")

    def test_build_prompt_context(
        self, prompt_generator, sample_tech_context, sample_requirements
    ):
        """Test building prompt context from tech context and requirements."""
        prompt_context = prompt_generator._build_prompt_context(
            sample_tech_context, sample_requirements, None
        )

        assert isinstance(prompt_context, PromptContext)
        assert (
            prompt_context.explicit_technologies
            == sample_tech_context.explicit_technologies
        )
        assert (
            prompt_context.contextual_technologies
            == sample_tech_context.contextual_technologies
        )
        assert prompt_context.ecosystem_preference == "aws"
        assert prompt_context.domain_context == "web_api"
        assert "Django" in prompt_context.banned_tools
        assert "MySQL" in prompt_context.banned_tools

    def test_organize_catalog_by_relevance(self, prompt_generator, sample_tech_context):
        """Test organizing catalog technologies by relevance."""
        organized_catalog = prompt_generator._organize_catalog_by_relevance(
            sample_tech_context
        )

        assert isinstance(organized_catalog, dict)

        # Check that technologies are grouped by category
        for category, techs in organized_catalog.items():
            assert isinstance(techs, list)
            for tech in techs:
                assert isinstance(tech, TechEntry)
                assert tech.category == category

    def test_calculate_technology_relevance(
        self, prompt_generator, sample_tech_context
    ):
        """Test technology relevance calculation."""
        # Test explicit technology (should get high score)
        fastapi_tech = TechEntry(
            id="fastapi",
            name="FastAPI",
            canonical_name="FastAPI",
            category="frameworks",
            description="Modern, fast web framework",
            ecosystem=EcosystemType.OPEN_SOURCE,
            maturity=MaturityLevel.STABLE,
            confidence_score=0.9,
        )

        score = prompt_generator._calculate_technology_relevance(
            fastapi_tech, sample_tech_context
        )
        assert score > 0.8  # Should be high due to explicit mention

        # Test AWS technology with AWS ecosystem preference
        aws_tech = TechEntry(
            id="aws_lambda",
            name="AWS Lambda",
            canonical_name="AWS Lambda",
            category="serverless",
            description="Serverless compute service",
            ecosystem=EcosystemType.AWS,
            maturity=MaturityLevel.MATURE,
            confidence_score=0.8,
        )

        score = prompt_generator._calculate_technology_relevance(
            aws_tech, sample_tech_context
        )
        assert score > 0.5  # Should get ecosystem boost

        # Test banned technology (should get zero score)
        banned_tech = TechEntry(
            id="django",
            name="Django",
            canonical_name="Django",
            category="frameworks",
            description="Python web framework",
            ecosystem=EcosystemType.OPEN_SOURCE,
            maturity=MaturityLevel.MATURE,
        )

        score = prompt_generator._calculate_technology_relevance(
            banned_tech, sample_tech_context
        )
        assert score == 0.0  # Should be zero due to ban

    def test_select_template(self, prompt_generator):
        """Test template selection based on context."""
        # Test base template selection
        base_context = PromptContext(
            explicit_technologies={},
            contextual_technologies={},
            ecosystem_preference=None,
            domain_context="general",
            integration_requirements=[],
            banned_tools=set(),
            required_integrations=[],
            catalog_technologies={},
            priority_instructions=[],
            selection_rules=[],
        )

        template = prompt_generator._select_template(base_context)
        assert template == "base"

        # Test ecosystem template selection
        ecosystem_context = PromptContext(
            explicit_technologies={},
            contextual_technologies={},
            ecosystem_preference="aws",
            domain_context="general",
            integration_requirements=[],
            banned_tools=set(),
            required_integrations=[],
            catalog_technologies={
                "serverless": [Mock(ecosystem=EcosystemType.AWS) for _ in range(6)]
            },
            priority_instructions=[],
            selection_rules=[],
        )

        template = prompt_generator._select_template(ecosystem_context)
        assert template == "ecosystem_focused"

        # Test domain template selection
        domain_context = PromptContext(
            explicit_technologies={},
            contextual_technologies={},
            ecosystem_preference=None,
            domain_context="web_api",
            integration_requirements=[],
            banned_tools=set(),
            required_integrations=[],
            catalog_technologies={},
            priority_instructions=[],
            selection_rules=[],
        )

        template = prompt_generator._select_template(domain_context)
        assert template == "domain_focused"

    def test_generate_context_aware_prompt(
        self, prompt_generator, sample_tech_context, sample_requirements
    ):
        """Test generating context-aware prompt."""
        prompt = prompt_generator.generate_context_aware_prompt(
            sample_tech_context, sample_requirements, None
        )

        assert isinstance(prompt, str)
        assert len(prompt) > 500  # Should be substantial

        # Check for required sections
        assert "EXPLICIT TECHNOLOGIES" in prompt
        assert "CONTEXTUAL TECHNOLOGIES" in prompt
        assert "AVAILABLE CATALOG TECHNOLOGIES" in prompt
        assert "CONSTRAINTS" in prompt
        assert "TECHNOLOGY SELECTION RULES" in prompt

        # Check explicit technologies are mentioned
        assert "FastAPI" in prompt
        assert "AWS Lambda" in prompt

        # Check banned technologies are mentioned
        assert "Django" in prompt or "MySQL" in prompt

        # Check ecosystem preference is reflected
        assert "aws" in prompt.lower() or "AWS" in prompt

    def test_format_explicit_technologies(self, prompt_generator):
        """Test formatting explicit technologies section."""
        explicit_techs = {"FastAPI": 0.95, "AWS Lambda": 0.9, "PostgreSQL": 0.8}

        formatted = prompt_generator._format_explicit_technologies(explicit_techs)

        assert "FastAPI" in formatted
        assert "AWS Lambda" in formatted
        assert "PostgreSQL" in formatted
        assert "MUST INCLUDE" in formatted
        assert "0.95" in formatted  # Confidence scores should be included

        # Test empty case
        empty_formatted = prompt_generator._format_explicit_technologies({})
        assert "None specified" in empty_formatted

    def test_format_contextual_technologies(self, prompt_generator):
        """Test formatting contextual technologies section."""
        contextual_techs = {"Redis": 0.8, "Docker": 0.7}

        formatted = prompt_generator._format_contextual_technologies(contextual_techs)

        assert "Redis" in formatted
        assert "Docker" in formatted
        assert "STRONGLY CONSIDER" in formatted
        assert "0.8" in formatted

        # Test empty case
        empty_formatted = prompt_generator._format_contextual_technologies({})
        assert "None inferred" in empty_formatted

    def test_format_catalog_technologies(self, prompt_generator, mock_catalog_manager):
        """Test formatting catalog technologies section."""
        catalog_techs = {
            "frameworks": [mock_catalog_manager.technologies["fastapi"]],
            "serverless": [mock_catalog_manager.technologies["aws_lambda"]],
        }

        formatted = prompt_generator._format_catalog_technologies(catalog_techs)

        assert "Frameworks:" in formatted
        assert "Serverless:" in formatted
        assert "FastAPI" in formatted
        assert "AWS Lambda" in formatted

        # Test empty case
        empty_formatted = prompt_generator._format_catalog_technologies({})
        assert "No relevant catalog technologies" in empty_formatted

    def test_build_priority_instructions(self, prompt_generator, sample_tech_context):
        """Test building priority instructions."""
        instructions = prompt_generator._build_priority_instructions(
            sample_tech_context
        )

        assert isinstance(instructions, list)
        assert len(instructions) > 0

        # Should include base instructions
        assert any(
            "EXPLICIT TECHNOLOGIES have absolute priority" in inst
            for inst in instructions
        )

        # Should include ecosystem-specific instructions for AWS
        assert any("AWS" in inst for inst in instructions)

        # Should include context-specific instructions
        assert any("explicit technology requirements" in inst for inst in instructions)
        assert any("banned technologies" in inst for inst in instructions)

    def test_build_selection_rules(self, prompt_generator, sample_tech_context):
        """Test building selection rules."""
        rules = prompt_generator._build_selection_rules(sample_tech_context)

        assert isinstance(rules, list)
        assert len(rules) > 0

        # Should include base rules
        assert any("Include ALL explicit technologies" in rule for rule in rules)

        # Should include ecosystem-specific rules
        assert any("ECOSYSTEM:" in rule for rule in rules)

        # Should include domain-specific rules
        assert any("DOMAIN:" in rule for rule in rules)

    def test_validate_prompt(self, prompt_generator):
        """Test prompt validation."""
        # Test valid prompt
        valid_prompt = """
        EXPLICIT TECHNOLOGIES (PRIORITY 1.0 - MUST INCLUDE):
        • FastAPI (confidence: 0.95) - MUST INCLUDE
        
        CONTEXTUAL TECHNOLOGIES (PRIORITY 0.8):
        • PostgreSQL (confidence: 0.8) - STRONGLY CONSIDER
        
        AVAILABLE CATALOG TECHNOLOGIES (Organized by Relevance):
        **Frameworks:**
          • FastAPI [open_source] (stable) - Modern, fast web framework
        
        CONSTRAINTS:
        • Banned Technologies: Django, MySQL
        
        TECHNOLOGY SELECTION RULES:
        1. Include ALL explicit technologies that exist in the catalog
        
        REASONING REQUIREMENTS:
        You MUST provide detailed reasoning for each technology selection
        
        Respond with a JSON object containing:
        {
            "tech_stack": [...],
            "overall_reasoning": "..."
        }
        """

        prompt_context = PromptContext(
            explicit_technologies={"FastAPI": 0.95},
            contextual_technologies={"PostgreSQL": 0.8},
            ecosystem_preference="aws",
            domain_context="web_api",
            integration_requirements=[],
            banned_tools={"Django", "MySQL"},
            required_integrations=[],
            catalog_technologies={},
            priority_instructions=[],
            selection_rules=[],
        )

        result = prompt_generator.validate_prompt(valid_prompt, prompt_context)

        assert isinstance(result, PromptValidationResult)
        assert result.is_valid
        assert result.effectiveness_score > 0.8

        # Test invalid prompt (missing sections)
        invalid_prompt = "This is a very short and incomplete prompt."

        invalid_result = prompt_generator.validate_prompt(
            invalid_prompt, prompt_context
        )

        assert not invalid_result.is_valid
        assert len(invalid_result.issues) > 0
        assert invalid_result.effectiveness_score < 0.5

    def test_apply_prompt_fixes(self, prompt_generator):
        """Test applying fixes to improve prompt."""
        # Create validation result with issues
        validation_result = PromptValidationResult(
            is_valid=False,
            issues=[
                "JSON response format not clearly specified",
                "Reasoning requirements not clearly specified",
            ],
            suggestions=[],
            effectiveness_score=0.6,
        )

        original_prompt = "This is an incomplete prompt."
        fixed_prompt = prompt_generator._apply_prompt_fixes(
            original_prompt, validation_result
        )

        assert len(fixed_prompt) > len(original_prompt)
        assert "RESPONSE FORMAT" in fixed_prompt or "JSON" in fixed_prompt
        assert (
            "REASONING REQUIREMENTS" in fixed_prompt
            or "reasoning" in fixed_prompt.lower()
        )

    def test_optimize_prompt_for_model(self, prompt_generator):
        """Test optimizing prompt for specific models."""
        base_prompt = """
        • This is a bullet point
        CRITICAL: This is critical
        MUST INCLUDE: This must be included
        """

        # Test GPT optimization
        gpt_prompt = prompt_generator.optimize_prompt_for_model(base_prompt, "gpt-4")
        assert "**MUST INCLUDE**" in gpt_prompt
        assert "**CRITICAL:**" in gpt_prompt

        # Test Claude optimization
        claude_prompt = prompt_generator.optimize_prompt_for_model(
            base_prompt, "claude-3"
        )
        assert "I need your expertise" in claude_prompt

        # Test Bedrock optimization (should be unchanged)
        bedrock_prompt = prompt_generator.optimize_prompt_for_model(
            base_prompt, "bedrock-titan"
        )
        assert bedrock_prompt == base_prompt

    def test_generate_prompt_variations(
        self, prompt_generator, sample_tech_context, sample_requirements
    ):
        """Test generating multiple prompt variations."""
        variations = prompt_generator.generate_prompt_variations(
            sample_tech_context, sample_requirements, None, num_variations=3
        )

        assert isinstance(variations, list)
        assert len(variations) == 3

        # All variations should be strings
        for variation in variations:
            assert isinstance(variation, str)
            assert len(variation) > 500

        # Variations should be different
        assert variations[0] != variations[1]
        assert variations[1] != variations[2]

    def test_format_constraints(self, prompt_generator):
        """Test formatting constraints section."""
        prompt_context = PromptContext(
            explicit_technologies={},
            contextual_technologies={},
            ecosystem_preference=None,
            domain_context="general",
            integration_requirements=[],
            banned_tools={"Django", "MySQL"},
            required_integrations=["database", "cache"],
            catalog_technologies={},
            priority_instructions=[],
            selection_rules=[],
        )

        formatted = prompt_generator._format_constraints(prompt_context)

        assert "Django" in formatted
        assert "MySQL" in formatted
        assert "database" in formatted
        assert "cache" in formatted

        # Test empty constraints
        empty_context = PromptContext(
            explicit_technologies={},
            contextual_technologies={},
            ecosystem_preference=None,
            domain_context="general",
            integration_requirements=[],
            banned_tools=set(),
            required_integrations=[],
            catalog_technologies={},
            priority_instructions=[],
            selection_rules=[],
        )

        empty_formatted = prompt_generator._format_constraints(empty_context)
        assert "None" in empty_formatted

    def test_format_ecosystem_considerations(self, prompt_generator):
        """Test formatting ecosystem-specific considerations."""
        aws_considerations = prompt_generator._format_ecosystem_considerations("aws")
        assert "AWS managed services" in aws_considerations
        assert "AWS SDK" in aws_considerations
        assert "AWS Lambda" in aws_considerations

        azure_considerations = prompt_generator._format_ecosystem_considerations(
            "azure"
        )
        assert "Azure managed services" in azure_considerations
        assert "Azure SDK" in azure_considerations
        assert "Azure Functions" in azure_considerations

        gcp_considerations = prompt_generator._format_ecosystem_considerations("gcp")
        assert "Google Cloud managed services" in gcp_considerations
        assert "Google Cloud SDK" in gcp_considerations
        assert "Google Cloud Functions" in gcp_considerations

    def test_format_domain_considerations(self, prompt_generator):
        """Test formatting domain-specific considerations."""
        data_considerations = prompt_generator._format_domain_considerations(
            "data_processing"
        )
        assert "data throughput" in data_considerations
        assert "scalability" in data_considerations

        api_considerations = prompt_generator._format_domain_considerations("web_api")
        assert "API performance" in api_considerations
        assert "authentication" in api_considerations

        ml_considerations = prompt_generator._format_domain_considerations("ml_ai")
        assert "ML/AI ecosystem" in ml_considerations
        assert "serving" in ml_considerations

        automation_considerations = prompt_generator._format_domain_considerations(
            "automation"
        )
        assert "workflow orchestration" in automation_considerations
        assert "monitoring" in automation_considerations


class TestPromptContextDataclass:
    """Test cases for PromptContext dataclass."""

    def test_prompt_context_creation(self):
        """Test creating PromptContext instance."""
        context = PromptContext(
            explicit_technologies={"FastAPI": 0.95},
            contextual_technologies={"PostgreSQL": 0.8},
            ecosystem_preference="aws",
            domain_context="web_api",
            integration_requirements=["database"],
            banned_tools={"Django"},
            required_integrations=["cache"],
            catalog_technologies={},
            priority_instructions=["Test instruction"],
            selection_rules=["Test rule"],
        )

        assert context.explicit_technologies == {"FastAPI": 0.95}
        assert context.contextual_technologies == {"PostgreSQL": 0.8}
        assert context.ecosystem_preference == "aws"
        assert context.domain_context == "web_api"
        assert context.integration_requirements == ["database"]
        assert context.banned_tools == {"Django"}
        assert context.required_integrations == ["cache"]
        assert context.priority_instructions == ["Test instruction"]
        assert context.selection_rules == ["Test rule"]


class TestPromptValidationResultDataclass:
    """Test cases for PromptValidationResult dataclass."""

    def test_prompt_validation_result_creation(self):
        """Test creating PromptValidationResult instance."""
        result = PromptValidationResult(
            is_valid=True,
            issues=["Issue 1"],
            suggestions=["Suggestion 1"],
            effectiveness_score=0.85,
        )

        assert result.is_valid is True
        assert result.issues == ["Issue 1"]
        assert result.suggestions == ["Suggestion 1"]
        assert result.effectiveness_score == 0.85


@pytest.mark.integration
class TestPromptGeneratorIntegration:
    """Integration tests for prompt generator with real catalog."""

    def test_end_to_end_prompt_generation(self):
        """Test complete prompt generation workflow."""
        # This would test with a real catalog manager
        # Skip for now as it requires actual catalog file
        pass
