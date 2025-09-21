"""Tests for prompt effectiveness and LLM response quality."""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any

from app.services.context_aware_prompt_generator import ContextAwareLLMPromptGenerator
from app.services.requirement_parsing.base import TechContext, DomainContext
from app.llm.base import LLMProvider


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing prompt effectiveness."""
    
    def __init__(self, response_template: Dict[str, Any] = None):
        self.response_template = response_template or {
            "tech_stack": [
                {
                    "name": "FastAPI",
                    "reason": "Explicitly mentioned in requirements for high-performance API development",
                    "confidence": 0.95,
                    "priority_level": "explicit",
                    "addresses_requirements": ["api_framework", "performance"]
                },
                {
                    "name": "PostgreSQL", 
                    "reason": "Reliable relational database for data storage needs",
                    "confidence": 0.9,
                    "priority_level": "contextual",
                    "addresses_requirements": ["data_storage", "reliability"]
                }
            ],
            "overall_reasoning": "Selected technologies prioritize explicit requirements while ensuring ecosystem compatibility",
            "ecosystem_consistency": "Mixed open-source stack with proven integration patterns",
            "alternatives_considered": [
                {
                    "technology": "Django",
                    "reason_not_selected": "Listed as banned technology in constraints"
                }
            ],
            "integration_notes": "FastAPI and PostgreSQL integrate well through SQLAlchemy ORM",
            "confidence_assessment": {
                "overall_confidence": 0.92,
                "risk_factors": ["learning_curve", "deployment_complexity"],
                "validation_notes": "All explicit technologies included as required"
            }
        }
        self.call_count = 0
        self.last_prompt = None
    
    async def generate(self, prompt: str, purpose: str = None) -> Dict[str, Any]:
        """Generate mock response based on prompt analysis."""
        self.call_count += 1
        self.last_prompt = prompt
        
        # Analyze prompt to provide contextual response
        response = self.response_template.copy()
        
        # Adjust response based on prompt content
        if "AWS" in prompt or "aws" in prompt:
            response["tech_stack"].append({
                "name": "AWS Lambda",
                "reason": "AWS ecosystem preference detected in requirements",
                "confidence": 0.88,
                "priority_level": "contextual",
                "addresses_requirements": ["serverless", "scalability"]
            })
            response["ecosystem_consistency"] = "AWS-focused stack for cloud-native deployment"
        
        if "banned" in prompt.lower() and "django" in prompt.lower():
            # Ensure banned technologies are not included
            response["tech_stack"] = [
                tech for tech in response["tech_stack"] 
                if tech["name"].lower() != "django"
            ]
        
        if "MUST INCLUDE" in prompt:
            # Boost confidence for explicit technologies
            for tech in response["tech_stack"]:
                if tech["priority_level"] == "explicit":
                    tech["confidence"] = min(tech["confidence"] * 1.1, 1.0)
        
        return response
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {"model": "mock", "provider": "test"}
    
    async def test_connection(self) -> bool:
        """Test connection."""
        return True


class TestPromptEffectiveness:
    """Test cases for prompt effectiveness and quality."""
    
    @pytest.fixture
    def mock_catalog_manager(self):
        """Create mock catalog manager."""
        mock_manager = Mock()
        mock_manager.technologies = {}
        return mock_manager
    
    @pytest.fixture
    def prompt_generator(self, mock_catalog_manager):
        """Create prompt generator with mocked dependencies."""
        with patch('app.services.context_aware_prompt_generator.require_service') as mock_require:
            mock_logger = Mock()
            mock_require.return_value = mock_logger
            
            return ContextAwareLLMPromptGenerator(catalog_manager=mock_catalog_manager)
    
    @pytest.fixture
    def sample_tech_context(self):
        """Create sample technology context for testing."""
        return TechContext(
            explicit_technologies={'FastAPI': 0.95, 'PostgreSQL': 0.9},
            contextual_technologies={'Redis': 0.8, 'Docker': 0.7},
            domain_context=DomainContext(
                primary_domain='web_api',
                sub_domains=['automation'],
                complexity_indicators=['high_throughput']
            ),
            ecosystem_preference='aws',
            integration_requirements=['database', 'cache'],
            banned_tools={'Django', 'MySQL'},
            priority_weights={'FastAPI': 1.0, 'PostgreSQL': 1.0}
        )
    
    def test_prompt_includes_explicit_technologies_prominently(self, prompt_generator, sample_tech_context):
        """Test that explicit technologies are prominently featured in prompts."""
        requirements = {'description': 'Build API with FastAPI and PostgreSQL'}
        
        prompt = prompt_generator.generate_context_aware_prompt(
            sample_tech_context, requirements, None
        )
        
        # Explicit technologies should be in dedicated section
        assert 'EXPLICIT TECHNOLOGIES' in prompt
        assert 'MUST INCLUDE' in prompt
        
        # Should mention specific technologies
        assert 'FastAPI' in prompt
        assert 'PostgreSQL' in prompt
        
        # Should include confidence scores
        assert '0.95' in prompt  # FastAPI confidence
        assert '0.9' in prompt   # PostgreSQL confidence
        
        # Explicit section should come before contextual
        explicit_pos = prompt.find('EXPLICIT TECHNOLOGIES')
        contextual_pos = prompt.find('CONTEXTUAL TECHNOLOGIES')
        assert explicit_pos < contextual_pos
    
    def test_prompt_enforces_banned_technologies(self, prompt_generator, sample_tech_context):
        """Test that banned technologies are clearly specified and enforced."""
        requirements = {'description': 'Build web application'}
        
        prompt = prompt_generator.generate_context_aware_prompt(
            sample_tech_context, requirements, None
        )
        
        # Should have constraints section
        assert 'CONSTRAINTS' in prompt
        assert 'Banned Technologies' in prompt
        
        # Should list banned technologies
        assert 'Django' in prompt
        assert 'MySQL' in prompt
        
        # Should have enforcement instructions
        assert 'NEVER recommend' in prompt or 'STRICTLY AVOID' in prompt or 'banned' in prompt.lower()
    
    def test_prompt_prioritizes_ecosystem_consistency(self, prompt_generator, sample_tech_context):
        """Test that ecosystem preference is reflected in prompt structure."""
        requirements = {'description': 'Deploy on AWS cloud'}
        
        prompt = prompt_generator.generate_context_aware_prompt(
            sample_tech_context, requirements, None
        )
        
        # Should mention ecosystem preference
        assert 'aws' in prompt.lower() or 'AWS' in prompt
        
        # Should have ecosystem-specific instructions
        assert 'ecosystem' in prompt.lower()
        
        # Should prefer AWS technologies when available
        aws_mentions = prompt.lower().count('aws')
        assert aws_mentions >= 2  # Should appear multiple times
    
    def test_prompt_includes_reasoning_requirements(self, prompt_generator, sample_tech_context):
        """Test that prompt requires detailed reasoning from LLM."""
        requirements = {'description': 'Build complex system'}
        
        prompt = prompt_generator.generate_context_aware_prompt(
            sample_tech_context, requirements, None
        )
        
        # Should have reasoning requirements section
        assert 'REASONING REQUIREMENTS' in prompt
        
        # Should specify what reasoning is needed
        assert 'reasoning' in prompt.lower()
        assert 'explanation' in prompt.lower() or 'justify' in prompt.lower()
        
        # Should require confidence levels
        assert 'confidence' in prompt.lower()
        
        # Should ask for alternatives consideration
        assert 'alternatives' in prompt.lower()
    
    def test_prompt_specifies_json_response_format(self, prompt_generator, sample_tech_context):
        """Test that prompt clearly specifies expected JSON response format."""
        requirements = {'description': 'Build application'}
        
        prompt = prompt_generator.generate_context_aware_prompt(
            sample_tech_context, requirements, None
        )
        
        # Should specify JSON format
        assert 'JSON' in prompt
        
        # Should show expected structure
        assert 'tech_stack' in prompt
        assert 'overall_reasoning' in prompt
        assert 'confidence_assessment' in prompt
        
        # Should have proper JSON syntax examples
        assert '{' in prompt and '}' in prompt
        assert '"name":' in prompt or '"tech_stack":' in prompt
    
    @pytest.mark.asyncio
    async def test_prompt_effectiveness_with_mock_llm(self, prompt_generator, sample_tech_context):
        """Test prompt effectiveness by analyzing LLM responses."""
        requirements = {
            'description': 'Build high-performance API using FastAPI with PostgreSQL database',
            'domain': 'web_api'
        }
        
        # Generate prompt
        prompt = prompt_generator.generate_context_aware_prompt(
            sample_tech_context, requirements, None
        )
        
        # Test with mock LLM
        mock_llm = MockLLMProvider()
        response = await mock_llm.generate(prompt, purpose="tech_stack_generation")
        
        # Validate response structure
        assert isinstance(response, dict)
        assert 'tech_stack' in response
        assert 'overall_reasoning' in response
        assert 'confidence_assessment' in response
        
        # Check that explicit technologies are included
        tech_names = [tech['name'] for tech in response['tech_stack']]
        assert 'FastAPI' in tech_names
        assert 'PostgreSQL' in tech_names
        
        # Check that banned technologies are not included
        assert 'Django' not in tech_names
        assert 'MySQL' not in tech_names
        
        # Validate reasoning quality
        for tech in response['tech_stack']:
            assert 'reason' in tech
            assert len(tech['reason']) > 10  # Should have substantial reasoning
            assert 'confidence' in tech
            assert 0.0 <= tech['confidence'] <= 1.0
    
    def test_prompt_validation_catches_issues(self, prompt_generator):
        """Test that prompt validation catches common issues."""
        # Create incomplete prompt
        incomplete_prompt = "Select some technologies for this project."
        
        from app.services.context_aware_prompt_generator import PromptContext
        
        prompt_context = PromptContext(
            explicit_technologies={'FastAPI': 0.95},
            contextual_technologies={},
            ecosystem_preference=None,
            domain_context='web_api',
            integration_requirements=[],
            banned_tools={'Django'},
            required_integrations=[],
            catalog_technologies={},
            priority_instructions=[],
            selection_rules=[]
        )
        
        validation_result = prompt_generator.validate_prompt(incomplete_prompt, prompt_context)
        
        # Should detect issues
        assert not validation_result.is_valid
        assert len(validation_result.issues) > 0
        assert validation_result.effectiveness_score < 0.5
        
        # Should identify specific problems
        issue_text = ' '.join(validation_result.issues).lower()
        assert 'explicit' in issue_text or 'missing' in issue_text
    
    def test_prompt_optimization_improves_effectiveness(self, prompt_generator, sample_tech_context):
        """Test that prompt optimization improves effectiveness scores."""
        requirements = {'description': 'Build system'}
        
        # Generate base prompt
        base_prompt = prompt_generator.generate_context_aware_prompt(
            sample_tech_context, requirements, None
        )
        
        # Optimize for different models
        gpt_prompt = prompt_generator.optimize_prompt_for_model(base_prompt, 'gpt-4')
        claude_prompt = prompt_generator.optimize_prompt_for_model(base_prompt, 'claude-3')
        
        # Optimized prompts should be different
        assert gpt_prompt != base_prompt
        assert claude_prompt != base_prompt
        assert gpt_prompt != claude_prompt
        
        # GPT optimization should add emphasis
        assert '**' in gpt_prompt  # Should have bold formatting
        
        # Claude optimization should add conversational elements
        assert 'expertise' in claude_prompt.lower()
    
    def test_prompt_variations_provide_different_approaches(self, prompt_generator, sample_tech_context):
        """Test that prompt variations provide meaningfully different approaches."""
        requirements = {'description': 'Build scalable application'}
        
        variations = prompt_generator.generate_prompt_variations(
            sample_tech_context, requirements, None, num_variations=3
        )
        
        assert len(variations) == 3
        
        # Should be different from each other
        for i in range(len(variations)):
            for j in range(i + 1, len(variations)):
                assert variations[i] != variations[j]
        
        # All should contain core requirements
        for variation in variations:
            assert 'FastAPI' in variation  # Explicit technology
            assert 'CONSTRAINTS' in variation  # Should have constraints
            assert 'JSON' in variation  # Should specify format
    
    @pytest.mark.asyncio
    async def test_prompt_handles_edge_cases(self, prompt_generator):
        """Test prompt generation with edge cases."""
        # Test with minimal context
        minimal_context = TechContext(
            explicit_technologies={},
            contextual_technologies={},
            domain_context=DomainContext(primary_domain='general'),
            ecosystem_preference=None,
            integration_requirements=[],
            banned_tools=set(),
            priority_weights={}
        )
        
        minimal_requirements = {'description': 'Build something'}
        
        prompt = prompt_generator.generate_context_aware_prompt(
            minimal_context, minimal_requirements, None
        )
        
        # Should still generate valid prompt
        assert isinstance(prompt, str)
        assert len(prompt) > 200
        assert 'JSON' in prompt
        
        # Test with maximum context
        maximal_context = TechContext(
            explicit_technologies={f'Tech{i}': 0.9 for i in range(10)},
            contextual_technologies={f'Context{i}': 0.7 for i in range(10)},
            domain_context=DomainContext(
                primary_domain='ml_ai',
                sub_domains=['data_processing', 'web_api'],
                complexity_indicators=['high_volume', 'real_time', 'distributed']
            ),
            ecosystem_preference='aws',
            integration_requirements=['database', 'cache', 'queue', 'monitoring'],
            banned_tools={f'Banned{i}' for i in range(5)},
            priority_weights={f'Tech{i}': 1.0 for i in range(10)}
        )
        
        maximal_requirements = {
            'description': 'Build complex distributed ML system with real-time processing',
            'domain': 'ml_ai',
            'volume': {'requests_per_second': 10000},
            'integrations': ['database', 'ml_pipeline', 'monitoring'],
            'compliance': ['GDPR', 'SOC2'],
            'sla': {'availability': '99.99%'}
        }
        
        maximal_prompt = prompt_generator.generate_context_aware_prompt(
            maximal_context, maximal_requirements, None
        )
        
        # Should handle complex context without breaking
        assert isinstance(maximal_prompt, str)
        assert len(maximal_prompt) > 1000
        assert 'Tech0' in maximal_prompt  # Should include explicit techs
        assert 'Banned0' in maximal_prompt  # Should include banned techs
    
    def test_prompt_effectiveness_metrics(self, prompt_generator, sample_tech_context):
        """Test calculation of prompt effectiveness metrics."""
        requirements = {'description': 'Build API with FastAPI'}
        
        prompt = prompt_generator.generate_context_aware_prompt(
            sample_tech_context, requirements, None
        )
        
        # Build prompt context for validation
        prompt_context = prompt_generator._build_prompt_context(
            sample_tech_context, requirements, None
        )
        
        validation_result = prompt_generator.validate_prompt(prompt, prompt_context)
        
        # Should have high effectiveness score for well-formed prompt
        assert validation_result.effectiveness_score > 0.8
        
        # Should be valid
        assert validation_result.is_valid
        
        # Should have minimal issues
        assert len(validation_result.issues) <= 1  # Allow for minor issues
    
    def test_prompt_consistency_across_similar_contexts(self, prompt_generator):
        """Test that similar contexts produce consistent prompt structures."""
        base_context = TechContext(
            explicit_technologies={'FastAPI': 0.95},
            contextual_technologies={'PostgreSQL': 0.8},
            domain_context=DomainContext(primary_domain='web_api'),
            ecosystem_preference='aws',
            integration_requirements=['database'],
            banned_tools={'Django'},
            priority_weights={'FastAPI': 1.0}
        )
        
        # Create slightly different context
        similar_context = TechContext(
            explicit_technologies={'FastAPI': 0.93},  # Slightly different confidence
            contextual_technologies={'PostgreSQL': 0.82},  # Slightly different confidence
            domain_context=DomainContext(primary_domain='web_api'),
            ecosystem_preference='aws',
            integration_requirements=['database'],
            banned_tools={'Django'},
            priority_weights={'FastAPI': 1.0}
        )
        
        requirements = {'description': 'Build REST API'}
        
        prompt1 = prompt_generator.generate_context_aware_prompt(base_context, requirements, None)
        prompt2 = prompt_generator.generate_context_aware_prompt(similar_context, requirements, None)
        
        # Should have similar structure (same sections)
        sections = ['EXPLICIT TECHNOLOGIES', 'CONTEXTUAL TECHNOLOGIES', 'CONSTRAINTS', 'SELECTION RULES']
        for section in sections:
            assert (section in prompt1) == (section in prompt2)
        
        # Should mention same key technologies
        assert ('FastAPI' in prompt1) == ('FastAPI' in prompt2)
        assert ('PostgreSQL' in prompt1) == ('PostgreSQL' in prompt2)
        assert ('Django' in prompt1) == ('Django' in prompt2)


class TestLLMResponseQuality:
    """Test cases for evaluating LLM response quality with generated prompts."""
    
    @pytest.fixture
    def response_evaluator(self):
        """Create response quality evaluator."""
        return LLMResponseQualityEvaluator()
    
    @pytest.mark.asyncio
    async def test_response_includes_explicit_technologies(self, response_evaluator):
        """Test that LLM responses include explicit technologies."""
        mock_llm = MockLLMProvider()
        
        # Simulate prompt with explicit technologies
        prompt = """
        EXPLICIT TECHNOLOGIES (PRIORITY 1.0 - MUST INCLUDE):
        • FastAPI (confidence: 0.95) - MUST INCLUDE
        • PostgreSQL (confidence: 0.9) - MUST INCLUDE
        
        Respond with JSON containing tech_stack array.
        """
        
        response = await mock_llm.generate(prompt)
        
        # Evaluate response quality
        quality_score = response_evaluator.evaluate_explicit_technology_inclusion(
            response, ['FastAPI', 'PostgreSQL']
        )
        
        assert quality_score > 0.8  # Should include most explicit technologies
    
    @pytest.mark.asyncio
    async def test_response_avoids_banned_technologies(self, response_evaluator):
        """Test that LLM responses avoid banned technologies."""
        mock_llm = MockLLMProvider()
        
        prompt = """
        CONSTRAINTS:
        • Banned Technologies: Django, MySQL
        
        STRICTLY AVOID these banned technologies under all circumstances.
        
        Respond with JSON containing tech_stack array.
        """
        
        response = await mock_llm.generate(prompt)
        
        # Evaluate response quality
        quality_score = response_evaluator.evaluate_banned_technology_avoidance(
            response, ['Django', 'MySQL']
        )
        
        assert quality_score == 1.0  # Should completely avoid banned technologies
    
    @pytest.mark.asyncio
    async def test_response_provides_adequate_reasoning(self, response_evaluator):
        """Test that LLM responses provide adequate reasoning."""
        mock_llm = MockLLMProvider()
        
        prompt = """
        REASONING REQUIREMENTS:
        You MUST provide detailed reasoning for each technology selection including:
        1. Why this technology was chosen over alternatives
        2. How it addresses specific requirements
        
        Respond with JSON containing tech_stack with reason fields.
        """
        
        response = await mock_llm.generate(prompt)
        
        # Evaluate reasoning quality
        quality_score = response_evaluator.evaluate_reasoning_quality(response)
        
        assert quality_score > 0.7  # Should provide good reasoning


class LLMResponseQualityEvaluator:
    """Evaluator for LLM response quality metrics."""
    
    def evaluate_explicit_technology_inclusion(self, 
                                            response: Dict[str, Any], 
                                            explicit_technologies: List[str]) -> float:
        """Evaluate how well response includes explicit technologies."""
        if 'tech_stack' not in response:
            return 0.0
        
        tech_names = [tech.get('name', '') for tech in response['tech_stack']]
        
        included_count = sum(1 for tech in explicit_technologies if tech in tech_names)
        total_count = len(explicit_technologies)
        
        return included_count / total_count if total_count > 0 else 1.0
    
    def evaluate_banned_technology_avoidance(self, 
                                           response: Dict[str, Any], 
                                           banned_technologies: List[str]) -> float:
        """Evaluate how well response avoids banned technologies."""
        if 'tech_stack' not in response:
            return 1.0  # No technologies = no banned technologies
        
        tech_names = [tech.get('name', '') for tech in response['tech_stack']]
        
        banned_count = sum(1 for tech in banned_technologies if tech in tech_names)
        
        return 0.0 if banned_count > 0 else 1.0
    
    def evaluate_reasoning_quality(self, response: Dict[str, Any]) -> float:
        """Evaluate quality of reasoning provided in response."""
        if 'tech_stack' not in response:
            return 0.0
        
        total_score = 0.0
        tech_count = len(response['tech_stack'])
        
        if tech_count == 0:
            return 0.0
        
        for tech in response['tech_stack']:
            reason = tech.get('reason', '')
            
            # Score based on reason length and content
            if len(reason) < 10:
                score = 0.0
            elif len(reason) < 30:
                score = 0.3
            elif len(reason) < 60:
                score = 0.6
            else:
                score = 0.8
            
            # Bonus for mentioning requirements or alternatives
            if 'requirement' in reason.lower():
                score += 0.1
            if 'alternative' in reason.lower():
                score += 0.1
            
            total_score += min(score, 1.0)
        
        return total_score / tech_count