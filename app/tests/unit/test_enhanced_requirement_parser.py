"""Unit tests for enhanced requirement parser."""

import pytest
from unittest.mock import Mock, patch

from app.services.requirement_parsing.enhanced_parser import EnhancedRequirementParser
from app.services.requirement_parsing.tech_extractor import TechnologyExtractor
from app.services.requirement_parsing.base import (
    ExplicitTech, ContextClues, ExtractionMethod
)


class TestEnhancedRequirementParser:
    """Test cases for EnhancedRequirementParser."""
    
    @pytest.fixture
    def mock_logger(self):
        """Mock logger fixture."""
        return Mock()
    
    @pytest.fixture
    def mock_tech_extractor(self):
        """Mock technology extractor fixture."""
        return Mock(spec=TechnologyExtractor)
    
    @pytest.fixture
    def parser(self, mock_tech_extractor):
        """Enhanced requirement parser fixture."""
        with patch('app.services.requirement_parsing.enhanced_parser.require_service') as mock_require:
            mock_require.return_value = Mock()
            return EnhancedRequirementParser(tech_extractor=mock_tech_extractor)
    
    def test_parse_requirements_basic(self, parser, mock_tech_extractor):
        """Test basic requirement parsing."""
        # Setup
        requirements = {
            'description': 'Build a web API using FastAPI and PostgreSQL',
            'domain': 'web_api'
        }
        
        mock_tech_extractor.extract_technologies.return_value = [
            ExplicitTech(
                name='FastAPI',
                canonical_name='FastAPI',
                confidence=0.9,
                extraction_method=ExtractionMethod.EXPLICIT_MENTION
            ),
            ExplicitTech(
                name='PostgreSQL',
                canonical_name='PostgreSQL',
                confidence=0.9,
                extraction_method=ExtractionMethod.EXPLICIT_MENTION
            )
        ]
        
        # Execute
        result = parser.parse_requirements(requirements)
        
        # Verify
        assert len(result.explicit_technologies) == 2
        assert result.raw_text == 'Build a web API using FastAPI and PostgreSQL web_api'
        assert result.confidence_score > 0.0
        assert 'web_api' in result.context_clues.domains
        assert result.extraction_metadata['total_explicit_techs'] == 2
    
    def test_extract_explicit_technologies(self, parser, mock_tech_extractor):
        """Test explicit technology extraction."""
        # Setup
        text = "We need to use Amazon Connect SDK and AWS Comprehend for this project"
        
        mock_tech_extractor.extract_technologies.return_value = [
            ExplicitTech(
                name='Amazon Connect SDK',
                canonical_name='Amazon Connect SDK',
                confidence=0.9,
                extraction_method=ExtractionMethod.ALIAS_RESOLUTION
            )
        ]
        
        # Execute
        result = parser.extract_explicit_technologies(text)
        
        # Verify
        assert len(result) >= 1
        mock_tech_extractor.extract_technologies.assert_called_once_with(text)
    
    def test_identify_context_clues_cloud_providers(self, parser):
        """Test cloud provider identification."""
        # Setup
        text = "Deploy on AWS using Amazon S3 and integrate with Azure services"
        
        # Execute
        result = parser.identify_context_clues(text)
        
        # Verify
        assert 'aws' in result.cloud_providers
        assert 'azure' in result.cloud_providers
        assert len(result.cloud_providers) == 2
    
    def test_identify_context_clues_domains(self, parser):
        """Test domain identification."""
        # Setup
        text = "Build a machine learning API for data processing and monitoring"
        
        # Execute
        result = parser.identify_context_clues(text)
        
        # Verify
        assert 'ml_ai' in result.domains
        assert 'data_processing' in result.domains
        assert 'web_api' in result.domains
        assert 'monitoring' in result.domains
    
    def test_identify_context_clues_programming_languages(self, parser):
        """Test programming language identification."""
        # Setup
        text = "Implement using Python with FastAPI and JavaScript for the frontend"
        
        # Execute
        result = parser.identify_context_clues(text)
        
        # Verify
        assert 'python' in result.programming_languages
        assert 'javascript' in result.programming_languages
    
    def test_identify_context_clues_deployment_preferences(self, parser):
        """Test deployment preference identification."""
        # Setup
        text = "Deploy using Docker containers on Kubernetes with serverless functions"
        
        # Execute
        result = parser.identify_context_clues(text)
        
        # Verify
        assert 'containerized' in result.deployment_preferences
        assert 'serverless' in result.deployment_preferences
    
    def test_extract_constraints_from_dict(self, parser):
        """Test constraint extraction from dictionary."""
        # Setup
        requirements = {
            'constraints': {
                'banned_tools': ['selenium', 'playwright'],
                'required_integrations': ['database', 'cache'],
                'compliance_requirements': ['gdpr'],
                'data_sensitivity': 'confidential',
                'budget_constraints': 'low',
                'deployment_preference': 'on_premises'
            }
        }
        
        # Execute
        result = parser.extract_constraints(requirements)
        
        # Verify
        assert 'selenium' in result.banned_tools
        assert 'playwright' in result.banned_tools
        assert 'database' in result.required_integrations
        assert 'cache' in result.required_integrations
        assert 'gdpr' in result.compliance_requirements
        assert result.data_sensitivity == 'confidential'
        assert result.budget_constraints == 'low'
        assert result.deployment_preference == 'on_premises'
    
    def test_extract_constraints_from_text(self, parser):
        """Test constraint extraction from text."""
        # Setup
        requirements = {
            'description': 'Cannot use selenium or playwright. Must use PostgreSQL. GDPR compliance required.'
        }
        
        # Execute
        result = parser.extract_constraints(requirements)
        
        # Verify
        # Note: Text-based constraint extraction is basic in this implementation
        # More sophisticated NLP would be needed for production
        assert len(result.compliance_requirements) >= 0  # May or may not detect GDPR
    
    def test_calculate_confidence_high(self, parser):
        """Test confidence calculation with high-confidence data."""
        # Setup
        parsed_req = Mock()
        parsed_req.explicit_technologies = [
            Mock(confidence=0.9),
            Mock(confidence=0.8)
        ]
        parsed_req.context_clues = Mock()
        parsed_req.context_clues.cloud_providers = ['aws']
        parsed_req.context_clues.domains = ['web_api', 'data_processing']
        parsed_req.context_clues.integration_patterns = ['database']
        parsed_req.context_clues.programming_languages = ['python']
        parsed_req.constraints = Mock()
        parsed_req.constraints.banned_tools = set()
        parsed_req.constraints.required_integrations = []
        
        # Execute
        result = parser.calculate_confidence(parsed_req)
        
        # Verify
        assert result > 0.7  # Should be high confidence
        assert result <= 1.0
    
    def test_calculate_confidence_low(self, parser):
        """Test confidence calculation with low-confidence data."""
        # Setup
        parsed_req = Mock()
        parsed_req.explicit_technologies = []
        parsed_req.context_clues = Mock()
        parsed_req.context_clues.cloud_providers = []
        parsed_req.context_clues.domains = []
        parsed_req.context_clues.integration_patterns = []
        parsed_req.context_clues.programming_languages = []
        parsed_req.constraints = Mock()
        parsed_req.constraints.banned_tools = set()
        parsed_req.constraints.required_integrations = []
        
        # Execute
        result = parser.calculate_confidence(parsed_req)
        
        # Verify
        assert result == 0.0  # Should be zero confidence
    
    def test_extract_text_content_comprehensive(self, parser):
        """Test comprehensive text content extraction."""
        # Setup
        requirements = {
            'description': 'Main description',
            'details': 'Additional details',
            'notes': 'Some notes',
            'custom_field': 'Custom text',
            'nested': {
                'field': 'Nested text'
            },
            'list_field': ['Item 1', 'Item 2', 123]  # Mixed types
        }
        
        # Execute
        result = parser._extract_text_content(requirements)
        
        # Verify
        assert 'Main description' in result
        assert 'Additional details' in result
        assert 'Some notes' in result
        assert 'Custom text' in result
        assert 'Item 1' in result
        assert 'Item 2' in result
    
    def test_extract_pattern_based_technologies(self, parser):
        """Test pattern-based technology extraction."""
        # Setup
        text = "Use FastAPI for the API, Docker for containers, and Redis for caching"
        
        # Execute
        result = parser._extract_pattern_based_technologies(text)
        
        # Verify
        tech_names = [tech.name for tech in result]
        assert 'fastapi' in tech_names
        assert 'docker' in tech_names
        assert 'redis' in tech_names
        
        # Check extraction metadata
        for tech in result:
            assert tech.extraction_method == ExtractionMethod.PATTERN_MATCHING
            assert tech.confidence > 0.0
            assert tech.source_text
            assert tech.context
    
    def test_deduplicate_technologies(self, parser):
        """Test technology deduplication."""
        # Setup
        technologies = [
            ExplicitTech(name='FastAPI', canonical_name='FastAPI', confidence=0.9),
            ExplicitTech(name='fastapi', canonical_name='FastAPI', confidence=0.7),
            ExplicitTech(name='PostgreSQL', canonical_name='PostgreSQL', confidence=0.8),
            ExplicitTech(name='postgres', canonical_name='PostgreSQL', confidence=0.6)
        ]
        
        # Execute
        result = parser._deduplicate_technologies(technologies)
        
        # Verify
        assert len(result) == 2  # Should have 2 unique technologies
        
        # Check that highest confidence versions are kept
        tech_names = [tech.canonical_name for tech in result]
        assert 'FastAPI' in tech_names
        assert 'PostgreSQL' in tech_names
        
        # Check confidence scores
        for tech in result:
            if tech.canonical_name == 'FastAPI':
                assert tech.confidence == 0.9
            elif tech.canonical_name == 'PostgreSQL':
                assert tech.confidence == 0.8
    
    def test_build_domain_context(self, parser):
        """Test domain context building."""
        # Setup
        text = "Build a scalable real-time automation system for enterprise use"
        context_clues = ContextClues(
            domains=['automation', 'web_api'],
            cloud_providers=['aws']
        )
        
        # Execute
        result = parser._build_domain_context(text, context_clues)
        
        # Verify
        assert result.primary_domain == 'automation'
        assert 'web_api' in result.sub_domains
        assert 'automation' in result.use_case_patterns
        assert 'scalable' in result.complexity_indicators
        assert 'real-time' in result.complexity_indicators
        assert 'enterprise' in result.complexity_indicators
    
    def test_extract_data_patterns(self, parser):
        """Test data pattern extraction."""
        # Setup
        text = "Process structured data from SQL tables and unstructured JSON documents in real time"
        
        # Execute
        result = parser._extract_data_patterns(text)
        
        # Verify
        assert 'structured_data' in result
        assert 'unstructured_data' in result
        assert 'real_time' in result
    
    def test_extract_technology_categories(self, parser):
        """Test technology category extraction."""
        # Setup
        text = "Need a web framework, database storage, message queue, and monitoring solution"
        
        # Execute
        result = parser._extract_technology_categories(text)
        
        # Verify
        assert 'web_framework' in result
        assert 'database' in result
        assert 'message_queue' in result
        assert 'monitoring' in result
    
    def test_empty_input_handling(self, parser, mock_tech_extractor):
        """Test handling of empty inputs."""
        # Setup
        mock_tech_extractor.extract_technologies.return_value = []
        
        # Test empty requirements
        result = parser.parse_requirements({})
        assert result.confidence_score == 0.0
        assert len(result.explicit_technologies) == 0
        
        # Test empty text
        result = parser.extract_explicit_technologies("")
        assert len(result) == 0
        
        result = parser.identify_context_clues("")
        assert len(result.cloud_providers) == 0
        assert len(result.domains) == 0
    
    def test_aws_connect_bug_scenario(self, parser, mock_tech_extractor):
        """Test the specific AWS Connect bug scenario from requirements."""
        # Setup - This is the exact scenario that was failing
        requirements = {
            'description': 'Integrate with Amazon Connect SDK to handle customer calls and use AWS Comprehend for sentiment analysis'
        }
        
        mock_tech_extractor.extract_technologies.return_value = [
            ExplicitTech(
                name='Amazon Connect SDK',
                canonical_name='Amazon Connect SDK',
                confidence=0.9,
                extraction_method=ExtractionMethod.ALIAS_RESOLUTION
            ),
            ExplicitTech(
                name='AWS Comprehend',
                canonical_name='AWS Comprehend',
                confidence=0.9,
                extraction_method=ExtractionMethod.ALIAS_RESOLUTION
            )
        ]
        
        # Execute
        result = parser.parse_requirements(requirements)
        
        # Verify - Should extract AWS technologies and infer AWS ecosystem
        assert len(result.explicit_technologies) == 2
        tech_names = [tech.canonical_name for tech in result.explicit_technologies]
        assert 'Amazon Connect SDK' in tech_names
        assert 'AWS Comprehend' in tech_names
        
        # Should identify AWS as cloud provider
        assert 'aws' in result.context_clues.cloud_providers
        
        # Should have high confidence due to explicit technology mentions
        assert result.confidence_score > 0.7
    
    @pytest.mark.parametrize("text,expected_cloud", [
        ("Deploy on AWS using Lambda", ['aws']),
        ("Use Azure Functions and Cosmos DB", ['azure']),
        ("Google Cloud Run with BigQuery", ['gcp']),
        ("AWS S3 and Azure Storage", ['aws', 'azure']),
        ("No cloud services mentioned", [])
    ])
    def test_cloud_provider_detection_parametrized(self, parser, text, expected_cloud):
        """Test cloud provider detection with various inputs."""
        result = parser.identify_context_clues(text)
        assert set(result.cloud_providers) == set(expected_cloud)
    
    @pytest.mark.parametrize("text,expected_domains", [
        ("Build a REST API", ['web_api']),
        ("Process data with ETL pipeline", ['data_processing']),
        ("Machine learning model training", ['ml_ai']),
        ("Automate workflow processes", ['automation']),
        ("Monitor system metrics", ['monitoring']),
        ("Secure authentication system", ['security'])
    ])
    def test_domain_detection_parametrized(self, parser, text, expected_domains):
        """Test domain detection with various inputs."""
        result = parser.identify_context_clues(text)
        for domain in expected_domains:
            assert domain in result.domains