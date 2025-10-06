"""Integration tests for context-aware prompt generator."""

import pytest
import json
from unittest.mock import Mock, patch

from app.services.context_aware_prompt_generator import ContextAwareLLMPromptGenerator
from app.services.requirement_parsing.enhanced_parser import EnhancedRequirementParser
from app.services.requirement_parsing.context_extractor import TechnologyContextExtractor
from app.services.catalog.intelligent_manager import IntelligentCatalogManager
from app.services.requirement_parsing.base import RequirementConstraints


@pytest.mark.integration
class TestPromptGeneratorIntegration:
    """Integration tests for prompt generator with real components."""
    
    @pytest.fixture
    def temp_catalog_path(self, tmp_path):
        """Create temporary catalog file for testing."""
        catalog_path = tmp_path / "test_technologies.json"
        
        # Create minimal catalog for testing
        catalog_data = {
            "metadata": {
                "version": "test",
                "total_technologies": 3
            },
            "technologies": {
                "fastapi": {
                    "id": "fastapi",
                    "name": "FastAPI",
                    "canonical_name": "FastAPI",
                    "category": "frameworks",
                    "description": "Modern, fast web framework for building APIs with Python",
                    "aliases": ["fast-api", "fast_api"],
                    "ecosystem": "open_source",
                    "integrates_with": ["python", "pydantic", "uvicorn"],
                    "alternatives": ["django", "flask"],
                    "tags": ["python", "api", "async", "web"],
                    "use_cases": ["rest_api", "microservices", "web_backend"],
                    "license": "MIT",
                    "maturity": "stable",
                    "confidence_score": 0.9,
                    "auto_generated": False,
                    "pending_review": False
                },
                "aws_lambda": {
                    "id": "aws_lambda",
                    "name": "AWS Lambda",
                    "canonical_name": "AWS Lambda",
                    "category": "serverless",
                    "description": "Serverless compute service by Amazon Web Services",
                    "aliases": ["lambda", "amazon lambda"],
                    "ecosystem": "aws",
                    "integrates_with": ["aws_api_gateway", "aws_s3", "aws_dynamodb"],
                    "alternatives": ["azure_functions", "google_cloud_functions"],
                    "tags": ["serverless", "compute", "aws"],
                    "use_cases": ["serverless_api", "event_processing", "microservices"],
                    "license": "Commercial",
                    "maturity": "mature",
                    "confidence_score": 0.95,
                    "auto_generated": False,
                    "pending_review": False
                },
                "postgresql": {
                    "id": "postgresql",
                    "name": "PostgreSQL",
                    "canonical_name": "PostgreSQL",
                    "category": "databases",
                    "description": "Advanced open source relational database",
                    "aliases": ["postgres", "pg"],
                    "ecosystem": "open_source",
                    "integrates_with": ["python", "sqlalchemy", "django"],
                    "alternatives": ["mysql", "sqlite"],
                    "tags": ["database", "sql", "relational"],
                    "use_cases": ["data_storage", "analytics", "web_backend"],
                    "license": "PostgreSQL License",
                    "maturity": "mature",
                    "confidence_score": 0.9,
                    "auto_generated": False,
                    "pending_review": False
                }
            },
            "categories": {
                "frameworks": {
                    "name": "Frameworks",
                    "description": "Web and application frameworks",
                    "technologies": ["fastapi"]
                },
                "serverless": {
                    "name": "Serverless",
                    "description": "Serverless computing platforms",
                    "technologies": ["aws_lambda"]
                },
                "databases": {
                    "name": "Databases",
                    "description": "Database systems and storage",
                    "technologies": ["postgresql"]
                }
            }
        }
        
        with open(catalog_path, 'w') as f:
            json.dump(catalog_data, f, indent=2)
        
        return catalog_path
    
    @pytest.fixture
    def catalog_manager(self, temp_catalog_path):
        """Create catalog manager with test catalog."""
        with patch('app.services.catalog.intelligent_manager.require_service') as mock_require:
            mock_logger = Mock()
            mock_require.return_value = mock_logger
            
            return IntelligentCatalogManager(catalog_path=temp_catalog_path)
    
    @pytest.fixture
    def requirement_parser(self):
        """Create requirement parser."""
        with patch('app.services.requirement_parsing.enhanced_parser.require_service') as mock_require:
            mock_logger = Mock()
            mock_require.return_value = mock_logger
            
            return EnhancedRequirementParser()
    
    @pytest.fixture
    def context_extractor(self):
        """Create context extractor."""
        with patch('app.services.requirement_parsing.context_extractor.require_service') as mock_require:
            mock_logger = Mock()
            mock_require.return_value = mock_logger
            
            return TechnologyContextExtractor()
    
    @pytest.fixture
    def prompt_generator(self, catalog_manager):
        """Create prompt generator with real catalog."""
        with patch('app.services.context_aware_prompt_generator.require_service') as mock_require:
            mock_logger = Mock()
            mock_require.return_value = mock_logger
            
            return ContextAwareLLMPromptGenerator(catalog_manager=catalog_manager)
    
    def test_full_workflow_with_explicit_technologies(self, 
                                                    requirement_parser, 
                                                    context_extractor, 
                                                    prompt_generator):
        """Test complete workflow with explicit technology mentions."""
        # Sample requirements with explicit technologies
        requirements = {
            'description': 'Build a REST API using FastAPI and AWS Lambda for serverless deployment. Store data in PostgreSQL.',
            'domain': 'web_api',
            'volume': {'requests_per_second': 500},
            'integrations': ['database', 'serverless'],
            'data_sensitivity': 'internal',
            'compliance': [],
            'sla': {'availability': '99.5%'}
        }
        
        RequirementConstraints(
            banned_tools={'Django', 'MySQL'},
            required_integrations=['database'],
            compliance_requirements=[],
            data_sensitivity='internal'
        )
        
        # Parse requirements
        parsed_requirements = requirement_parser.parse_requirements(requirements)
        
        # Extract technology context
        tech_context = context_extractor.build_context(parsed_requirements)
        
        # Generate prompt
        prompt = prompt_generator.generate_context_aware_prompt(
            tech_context, requirements, {'banned_tools': ['Django', 'MySQL']}
        )
        
        # Validate prompt content
        assert isinstance(prompt, str)
        assert len(prompt) > 1000  # Should be comprehensive
        
        # Check explicit technologies are prominently featured
        assert 'FastAPI' in prompt
        assert 'AWS Lambda' in prompt
        assert 'PostgreSQL' in prompt
        
        # Check priority sections exist
        assert 'EXPLICIT TECHNOLOGIES' in prompt
        assert 'MUST INCLUDE' in prompt
        
        # Check banned technologies are mentioned
        assert 'Django' in prompt
        assert 'MySQL' in prompt
        
        # Check ecosystem preference is detected and used
        assert 'aws' in prompt.lower() or 'AWS' in prompt
        
        # Check JSON response format is specified
        assert 'JSON' in prompt
        assert 'tech_stack' in prompt
        assert 'reasoning' in prompt.lower()
    
    def test_workflow_with_contextual_technologies_only(self, 
                                                      requirement_parser, 
                                                      context_extractor, 
                                                      prompt_generator):
        """Test workflow with only contextual technology inferences."""
        # Requirements without explicit technology names
        requirements = {
            'description': 'Build a web application for data processing with real-time analytics and user authentication.',
            'domain': 'data_processing',
            'volume': {'data_points_per_hour': 10000},
            'integrations': ['database', 'authentication', 'analytics'],
            'data_sensitivity': 'confidential',
            'compliance': ['GDPR'],
            'sla': {'availability': '99.9%', 'response_time': '200ms'}
        }
        
        RequirementConstraints(
            banned_tools=set(),
            required_integrations=['database', 'authentication'],
            compliance_requirements=['GDPR'],
            data_sensitivity='confidential'
        )
        
        # Parse requirements
        parsed_requirements = requirement_parser.parse_requirements(requirements)
        
        # Extract technology context
        tech_context = context_extractor.build_context(parsed_requirements)
        
        # Generate prompt
        prompt = prompt_generator.generate_context_aware_prompt(
            tech_context, requirements, None
        )
        
        # Validate prompt content
        assert isinstance(prompt, str)
        assert len(prompt) > 800
        
        # Should focus on contextual technologies
        assert 'CONTEXTUAL TECHNOLOGIES' in prompt
        assert 'STRONGLY CONSIDER' in prompt
        
        # Should include domain-specific considerations
        assert 'data' in prompt.lower()
        assert 'processing' in prompt.lower()
        
        # Should include compliance considerations
        assert 'GDPR' in prompt or 'confidential' in prompt.lower()
    
    def test_workflow_with_ecosystem_preference(self, 
                                              requirement_parser, 
                                              context_extractor, 
                                              prompt_generator):
        """Test workflow with strong ecosystem preference."""
        # Requirements with AWS ecosystem indicators
        requirements = {
            'description': 'Deploy microservices on AWS using Lambda functions, API Gateway, and DynamoDB for a serverless architecture.',
            'domain': 'microservices',
            'volume': {'requests_per_second': 1000},
            'integrations': ['serverless', 'database', 'api_gateway'],
            'data_sensitivity': 'internal',
            'compliance': [],
            'sla': {'availability': '99.9%'}
        }
        
        RequirementConstraints(
            banned_tools=set(),
            required_integrations=['serverless'],
            compliance_requirements=[],
            data_sensitivity='internal'
        )
        
        # Parse requirements
        parsed_requirements = requirement_parser.parse_requirements(requirements)
        
        # Extract technology context
        tech_context = context_extractor.build_context(parsed_requirements)
        
        # Generate prompt
        prompt = prompt_generator.generate_context_aware_prompt(
            tech_context, requirements, None
        )
        
        # Should detect AWS ecosystem preference
        assert tech_context.ecosystem_preference == 'aws'
        
        # Prompt should reflect AWS focus
        assert 'AWS' in prompt or 'aws' in prompt.lower()
        assert 'Lambda' in prompt
        
        # Should use ecosystem-focused template or considerations
        assert 'ecosystem' in prompt.lower()
    
    def test_prompt_validation_with_real_content(self, prompt_generator):
        """Test prompt validation with realistic prompt content."""
        # Create a realistic tech context
        from app.services.requirement_parsing.base import TechContext, DomainContext
        
        tech_context = TechContext(
            explicit_technologies={'FastAPI': 0.95, 'PostgreSQL': 0.9},
            contextual_technologies={'Redis': 0.8, 'Docker': 0.7},
            domain_context=DomainContext(
                primary_domain='web_api',
                sub_domains=[],
                complexity_indicators=['high_throughput']
            ),
            ecosystem_preference='aws',
            integration_requirements=['database', 'cache'],
            banned_tools={'Django'},
            priority_weights={'FastAPI': 1.0, 'PostgreSQL': 1.0}
        )
        
        requirements = {
            'description': 'Build high-performance API',
            'domain': 'web_api'
        }
        
        # Generate prompt
        prompt = prompt_generator.generate_context_aware_prompt(
            tech_context, requirements, None
        )
        
        # Validate the generated prompt
        prompt_context = prompt_generator._build_prompt_context(
            tech_context, requirements, None
        )
        
        validation_result = prompt_generator.validate_prompt(prompt, prompt_context)
        
        # Should be valid and effective
        assert validation_result.is_valid
        assert validation_result.effectiveness_score > 0.7
        assert len(validation_result.issues) == 0
    
    def test_catalog_organization_with_real_data(self, prompt_generator):
        """Test catalog organization with real catalog data."""
        from app.services.requirement_parsing.base import TechContext, DomainContext
        
        tech_context = TechContext(
            explicit_technologies={'FastAPI': 0.95},
            contextual_technologies={},
            domain_context=DomainContext(
                primary_domain='web_api',
                sub_domains=[],
                complexity_indicators=[]
            ),
            ecosystem_preference=None,
            integration_requirements=[],
            banned_tools=set(),
            priority_weights={}
        )
        
        # Organize catalog by relevance
        organized_catalog = prompt_generator._organize_catalog_by_relevance(tech_context)
        
        # Should have categories
        assert len(organized_catalog) > 0
        
        # FastAPI should be highly ranked in frameworks category
        if 'frameworks' in organized_catalog:
            frameworks = organized_catalog['frameworks']
            assert len(frameworks) > 0
            
            # FastAPI should be first due to explicit mention
            fastapi_found = any(tech.canonical_name == 'FastAPI' for tech in frameworks)
            assert fastapi_found
    
    def test_prompt_variations_generation(self, 
                                        requirement_parser, 
                                        context_extractor, 
                                        prompt_generator):
        """Test generating multiple prompt variations."""
        requirements = {
            'description': 'Build API with FastAPI and PostgreSQL',
            'domain': 'web_api'
        }
        
        RequirementConstraints(
            banned_tools=set(),
            required_integrations=[],
            compliance_requirements=[],
            data_sensitivity='internal'
        )
        
        # Parse requirements and extract context
        parsed_requirements = requirement_parser.parse_requirements(requirements)
        tech_context = context_extractor.build_context(parsed_requirements)
        
        # Generate variations
        variations = prompt_generator.generate_prompt_variations(
            tech_context, requirements, None, num_variations=3
        )
        
        assert len(variations) == 3
        
        # All should be valid prompts
        for variation in variations:
            assert isinstance(variation, str)
            assert len(variation) > 500
            assert 'FastAPI' in variation
        
        # Should be different from each other
        assert variations[0] != variations[1]
        assert variations[1] != variations[2]
    
    def test_model_specific_optimization(self, prompt_generator):
        """Test model-specific prompt optimization."""
        base_prompt = """
        CRITICAL: This is important
        • Bullet point 1
        • Bullet point 2
        MUST INCLUDE: Required technology
        """
        
        # Test different model optimizations
        gpt_optimized = prompt_generator.optimize_prompt_for_model(base_prompt, 'gpt-4')
        claude_optimized = prompt_generator.optimize_prompt_for_model(base_prompt, 'claude-3')
        bedrock_optimized = prompt_generator.optimize_prompt_for_model(base_prompt, 'bedrock-titan')
        
        # GPT should have enhanced formatting
        assert '**CRITICAL:**' in gpt_optimized
        assert '**MUST INCLUDE**' in gpt_optimized
        
        # Claude should have conversational intro
        assert 'I need your expertise' in claude_optimized
        
        # Bedrock should be unchanged (conservative)
        assert bedrock_optimized == base_prompt
    
    def test_error_handling_with_missing_catalog(self, tmp_path):
        """Test error handling when catalog is missing or corrupted."""
        # Test with non-existent catalog path
        missing_catalog_path = tmp_path / "missing_catalog.json"
        
        with patch('app.services.context_aware_prompt_generator.require_service') as mock_require:
            mock_logger = Mock()
            mock_require.return_value = mock_logger
            
            # Should handle missing catalog gracefully
            catalog_manager = IntelligentCatalogManager(catalog_path=missing_catalog_path)
            prompt_generator = ContextAwareLLMPromptGenerator(catalog_manager=catalog_manager)
            
            # Should still be able to generate prompts
            from app.services.requirement_parsing.base import TechContext, DomainContext
            
            tech_context = TechContext(
                explicit_technologies={'FastAPI': 0.95},
                contextual_technologies={},
                domain_context=DomainContext(primary_domain='web_api'),
                ecosystem_preference=None,
                integration_requirements=[],
                banned_tools=set(),
                priority_weights={}
            )
            
            prompt = prompt_generator.generate_context_aware_prompt(
                tech_context, {'description': 'Test'}, None
            )
            
            assert isinstance(prompt, str)
            assert len(prompt) > 100  # Should still generate something meaningful
    
    def test_performance_with_large_catalog(self, prompt_generator):
        """Test performance with a larger catalog."""
        # This test would be more meaningful with a real large catalog
        # For now, just ensure the current implementation doesn't break
        
        from app.services.requirement_parsing.base import TechContext, DomainContext
        
        tech_context = TechContext(
            explicit_technologies={'FastAPI': 0.95, 'PostgreSQL': 0.9},
            contextual_technologies={'Redis': 0.8, 'Docker': 0.7, 'Nginx': 0.6},
            domain_context=DomainContext(primary_domain='web_api'),
            ecosystem_preference='aws',
            integration_requirements=['database', 'cache', 'proxy'],
            banned_tools={'Django', 'MySQL'},
            priority_weights={}
        )
        
        requirements = {
            'description': 'Complex application with multiple integrations',
            'domain': 'web_api'
        }
        
        import time
        start_time = time.time()
        
        prompt = prompt_generator.generate_context_aware_prompt(
            tech_context, requirements, None
        )
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert generation_time < 5.0  # 5 seconds should be more than enough
        assert isinstance(prompt, str)
        assert len(prompt) > 1000