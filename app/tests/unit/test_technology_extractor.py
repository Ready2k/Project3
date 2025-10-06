"""Unit tests for enhanced technology extractor."""

import pytest
from unittest.mock import Mock, patch

from app.services.requirement_parsing.tech_extractor import TechnologyExtractor, TechnologyAlias, NEREntity, IntegrationPattern
from app.services.requirement_parsing.base import ExplicitTech, ExtractionMethod


class TestTechnologyExtractor:
    """Test cases for TechnologyExtractor."""
    
    @pytest.fixture
    def mock_logger(self):
        """Mock logger fixture."""
        return Mock()
    
    @pytest.fixture
    def extractor(self):
        """Technology extractor fixture."""
        with patch('app.services.requirement_parsing.tech_extractor.require_service') as mock_require:
            mock_require.return_value = Mock()
            return TechnologyExtractor()
    
    def test_initialization(self, extractor):
        """Test extractor initialization."""
        assert extractor.technology_aliases is not None
        assert len(extractor.technology_aliases) > 0
        assert 'fastapi' in extractor.technology_aliases
        assert 'connect sdk' in extractor.technology_aliases
    
    def test_resolve_aliases_exact_match(self, extractor):
        """Test alias resolution with exact matches."""
        # Test exact matches
        assert extractor.resolve_aliases('fastapi') == 'FastAPI'
        assert extractor.resolve_aliases('connect sdk') == 'Amazon Connect SDK'
        assert extractor.resolve_aliases('s3') == 'Amazon S3'
        assert extractor.resolve_aliases('postgres') == 'PostgreSQL'
    
    def test_resolve_aliases_case_insensitive(self, extractor):
        """Test case-insensitive alias resolution."""
        assert extractor.resolve_aliases('FASTAPI') == 'FastAPI'
        assert extractor.resolve_aliases('FastAPI') == 'FastAPI'
        assert extractor.resolve_aliases('S3') == 'Amazon S3'
    
    def test_resolve_aliases_partial_match(self, extractor):
        """Test partial alias matching."""
        # Should find partial matches
        result = extractor.resolve_aliases('connect')
        assert result == 'Amazon Connect'  # Should match the alias
    
    def test_resolve_aliases_no_match(self, extractor):
        """Test alias resolution with no matches."""
        assert extractor.resolve_aliases('nonexistent_tech') is None
        assert extractor.resolve_aliases('') is None
    
    def test_calculate_extraction_confidence_explicit(self, extractor):
        """Test confidence calculation for explicit mentions."""
        confidence = extractor.calculate_extraction_confidence(
            'FastAPI', ExtractionMethod.EXPLICIT_MENTION, 'Use FastAPI for the API'
        )
        assert confidence == 1.0
    
    def test_calculate_extraction_confidence_alias(self, extractor):
        """Test confidence calculation for alias resolution."""
        confidence = extractor.calculate_extraction_confidence(
            'fastapi', ExtractionMethod.ALIAS_RESOLUTION, 'Use fastapi for the API'
        )
        assert confidence >= 0.9  # Should be high confidence for known alias
    
    def test_calculate_extraction_confidence_pattern(self, extractor):
        """Test confidence calculation for pattern matching."""
        confidence = extractor.calculate_extraction_confidence(
            'SomeFramework', ExtractionMethod.PATTERN_MATCHING, 'Use SomeFramework API'
        )
        assert 0.6 <= confidence <= 0.8  # Should be medium confidence
    
    def test_calculate_extraction_confidence_ambiguous(self, extractor):
        """Test confidence calculation for ambiguous terms."""
        confidence = extractor.calculate_extraction_confidence(
            'lambda', ExtractionMethod.PATTERN_MATCHING, 'Use lambda functions'
        )
        # Should be reduced due to ambiguity
        assert confidence < 0.7
    
    def test_calculate_extraction_confidence_with_context(self, extractor):
        """Test confidence boost with relevant context."""
        confidence = extractor.calculate_extraction_confidence(
            'SomeAPI', ExtractionMethod.PATTERN_MATCHING, 'Build a REST API using SomeAPI'
        )
        # Should get context boost for API-related context
        assert confidence > 0.7
    
    def test_extract_technologies_comprehensive(self, extractor):
        """Test comprehensive technology extraction."""
        text = "Build a web API using FastAPI, connect to PostgreSQL database, and deploy with Docker"
        
        result = extractor.extract_technologies(text)
        
        # Should extract multiple technologies
        assert len(result) >= 3
        
        tech_names = [tech.canonical_name or tech.name for tech in result]
        assert 'FastAPI' in tech_names
        assert 'PostgreSQL' in tech_names
        assert 'Docker' in tech_names
    
    def test_extract_by_aliases(self, extractor):
        """Test extraction using alias matching."""
        text = "Use fastapi for the API and connect to postgres database"
        
        result = extractor._extract_by_aliases(text)
        
        # Should find aliases
        tech_names = [tech.canonical_name for tech in result]
        assert 'FastAPI' in tech_names
        assert 'PostgreSQL' in tech_names
        
        # Check extraction metadata
        for tech in result:
            assert tech.extraction_method == ExtractionMethod.ALIAS_RESOLUTION
            assert tech.confidence > 0.0
            assert tech.source_text
            assert tech.context
    
    def test_extract_by_aliases_context_required(self, extractor):
        """Test alias extraction with context requirements."""
        # Test lambda without AWS context - should not match
        text = "Use lambda functions in Python"
        result = extractor._extract_by_aliases(text)
        lambda_techs = [tech for tech in result if 'lambda' in tech.name.lower()]
        # Should not extract AWS Lambda without AWS context
        assert len(lambda_techs) == 0
        
        # Test lambda with AWS context - should match
        text = "Use AWS lambda functions for serverless"
        result = extractor._extract_by_aliases(text)
        lambda_techs = [tech for tech in result if 'lambda' in tech.canonical_name.lower()]
        assert len(lambda_techs) > 0
    
    def test_extract_by_patterns(self, extractor):
        """Test extraction using pattern matching."""
        text = "Integrate with Amazon S3 and use Google Cloud Functions"
        
        result = extractor._extract_by_patterns(text)
        
        # Should extract cloud services
        assert len(result) >= 2
        
        # Check that patterns captured the services
        tech_names = [tech.canonical_name for tech in result]
        # Note: Exact matches depend on pattern implementation
        assert any('S3' in name or 'Amazon' in name for name in tech_names)
    
    def test_extract_by_ner_simplified(self, extractor):
        """Test simplified NER extraction."""
        text = "Use FastAPI and PostgreSQL for the backend"
        
        result = extractor._extract_by_ner(text)
        
        # Should extract capitalized technology names
        tech_names = [tech.canonical_name for tech in result]
        assert 'FastAPI' in tech_names
        assert 'PostgreSQL' in tech_names
        
        # Check extraction metadata
        for tech in result:
            assert tech.extraction_method == ExtractionMethod.NER_EXTRACTION
    
    def test_extract_integration_technologies(self, extractor):
        """Test integration pattern-based extraction."""
        text = "Build a REST API with GraphQL support and message queue integration"
        
        result = extractor._extract_integration_technologies(text)
        
        # Should infer technologies from integration patterns
        assert len(result) > 0
        
        tech_names = [tech.canonical_name for tech in result]
        # Should suggest technologies for REST API, GraphQL, and message queues
        assert any('API' in name or 'FastAPI' in name or 'Express' in name for name in tech_names)
        
        # Check extraction metadata
        for tech in result:
            assert tech.extraction_method == ExtractionMethod.INTEGRATION_PATTERN
    
    def test_has_relevant_context_lambda(self, extractor):
        """Test context relevance checking for lambda."""
        # AWS context should be relevant
        aws_context = "Deploy using AWS lambda functions for serverless processing"
        assert extractor._has_relevant_context('lambda', aws_context)
        
        # Generic context should not be relevant
        generic_context = "Use lambda functions in Python code"
        assert not extractor._has_relevant_context('lambda', generic_context)
    
    def test_has_relevant_context_connect(self, extractor):
        """Test context relevance checking for connect."""
        # AWS Connect context should be relevant
        connect_context = "Integrate with Amazon Connect for call center operations"
        assert extractor._has_relevant_context('connect', connect_context)
        
        # Generic connect context should not be relevant
        generic_context = "Connect to the database server"
        assert not extractor._has_relevant_context('connect', generic_context)
    
    def test_deduplicate_and_enhance(self, extractor):
        """Test deduplication and enhancement."""
        technologies = [
            ExplicitTech(
                name='FastAPI', canonical_name='FastAPI', confidence=0.9,
                extraction_method=ExtractionMethod.EXPLICIT_MENTION,
                aliases=['fastapi']
            ),
            ExplicitTech(
                name='FastAPI', canonical_name='FastAPI', confidence=0.7,
                extraction_method=ExtractionMethod.ALIAS_RESOLUTION,
                aliases=['fast-api']
            ),
            ExplicitTech(
                name='PostgreSQL', canonical_name='PostgreSQL', confidence=0.8,
                extraction_method=ExtractionMethod.PATTERN_MATCHING,
                aliases=['postgres']
            )
        ]
        
        text = "Use FastAPI and PostgreSQL"
        result = extractor._deduplicate_and_enhance(technologies, text)
        
        # Should have 2 unique technologies
        assert len(result) == 2
        
        # Should keep highest confidence version
        fastapi_tech = next(tech for tech in result if tech.canonical_name == 'FastAPI')
        assert fastapi_tech.confidence == 0.9
        
        # Should merge aliases
        assert 'fastapi' in fastapi_tech.aliases
        assert 'fast-api' in fastapi_tech.aliases
    
    def test_aws_services_extraction(self, extractor):
        """Test extraction of AWS services."""
        text = "Use Amazon Connect SDK, AWS Comprehend, and S3 for storage"
        
        result = extractor.extract_technologies(text)
        
        tech_names = [tech.canonical_name or tech.name for tech in result]
        assert 'Amazon Connect SDK' in tech_names
        assert 'AWS Comprehend' in tech_names
        assert 'Amazon S3' in tech_names
    
    def test_azure_services_extraction(self, extractor):
        """Test extraction of Azure services."""
        text = "Deploy using Azure Functions and Azure Cosmos DB"
        
        result = extractor.extract_technologies(text)
        
        tech_names = [tech.canonical_name or tech.name for tech in result]
        assert any('Azure Functions' in name for name in tech_names)
        assert any('Cosmos DB' in name for name in tech_names)
    
    def test_programming_languages_extraction(self, extractor):
        """Test extraction of programming languages."""
        text = "Implement in Python using JavaScript for frontend"
        
        result = extractor.extract_technologies(text)
        
        tech_names = [tech.canonical_name or tech.name for tech in result]
        assert 'Python' in tech_names
        assert 'JavaScript' in tech_names
    
    def test_database_extraction(self, extractor):
        """Test extraction of database technologies."""
        text = "Store data in PostgreSQL and cache with Redis"
        
        result = extractor.extract_technologies(text)
        
        tech_names = [tech.canonical_name or tech.name for tech in result]
        assert 'PostgreSQL' in tech_names
        assert 'Redis' in tech_names
    
    def test_container_technologies_extraction(self, extractor):
        """Test extraction of container technologies."""
        text = "Containerize with Docker and orchestrate using Kubernetes"
        
        result = extractor.extract_technologies(text)
        
        tech_names = [tech.canonical_name or tech.name for tech in result]
        assert 'Docker' in tech_names
        assert 'Kubernetes' in tech_names
    
    def test_empty_text_handling(self, extractor):
        """Test handling of empty text."""
        result = extractor.extract_technologies("")
        assert len(result) == 0
        
        result = extractor.extract_technologies(None)
        assert len(result) == 0
    
    def test_confidence_scoring_consistency(self, extractor):
        """Test that confidence scores are consistent and within bounds."""
        text = "Use FastAPI, Django, and some unknown framework"
        
        result = extractor.extract_technologies(text)
        
        for tech in result:
            # All confidence scores should be between 0 and 1
            assert 0.0 <= tech.confidence <= 1.0
            
            # Known technologies should have higher confidence
            if tech.canonical_name in ['FastAPI', 'Django']:
                assert tech.confidence >= 0.7
    
    @pytest.mark.parametrize("text,expected_tech", [
        ("Use fastapi for API", "FastAPI"),
        ("Connect to postgres database", "PostgreSQL"),
        ("Deploy with docker containers", "Docker"),
        ("Cache with redis", "Redis"),
        ("Use react for frontend", "React")
    ])
    def test_alias_resolution_parametrized(self, extractor, text, expected_tech):
        """Test alias resolution with various inputs."""
        result = extractor.extract_technologies(text)
        tech_names = [tech.canonical_name or tech.name for tech in result]
        assert expected_tech in tech_names
    
    def test_technology_alias_dataclass(self):
        """Test TechnologyAlias dataclass."""
        alias = TechnologyAlias('fastapi', 'FastAPI', 0.9, False, 'backend', 'open_source')
        
        assert alias.alias == 'fastapi'
        assert alias.canonical_name == 'FastAPI'
        assert alias.confidence == 0.9
        assert alias.context_required is False
        assert alias.category == 'backend'
        assert alias.ecosystem == 'open_source'
        
        # Test default values
        alias_default = TechnologyAlias('test', 'Test')
        assert alias_default.confidence == 1.0
        assert alias_default.context_required is False
        assert alias_default.category is None
        assert alias_default.ecosystem is None
    
    def test_ner_entity_dataclass(self):
        """Test NEREntity dataclass."""
        entity = NEREntity('FastAPI', 'TECH_NAME', 0, 7, 0.9)
        
        assert entity.text == 'FastAPI'
        assert entity.label == 'TECH_NAME'
        assert entity.start == 0
        assert entity.end == 7
        assert entity.confidence == 0.9
    
    def test_integration_pattern_dataclass(self):
        """Test IntegrationPattern dataclass."""
        pattern = IntegrationPattern(
            pattern=r'\brest\s+api\b',
            technologies=['FastAPI', 'Express.js'],
            confidence_multiplier=0.8,
            context_boost={'python': 1.2}
        )
        
        assert pattern.pattern == r'\brest\s+api\b'
        assert pattern.technologies == ['FastAPI', 'Express.js']
        assert pattern.confidence_multiplier == 0.8
        assert pattern.context_boost == {'python': 1.2}
    
    def test_enhanced_alias_resolution(self, extractor):
        """Test enhanced alias resolution with abbreviations."""
        # Test abbreviations
        assert extractor.resolve_aliases('js') == 'JavaScript'
        assert extractor.resolve_aliases('ts') == 'TypeScript'
        assert extractor.resolve_aliases('py') == 'Python'
        assert extractor.resolve_aliases('k8s') == 'Kubernetes'
        
        # Test case insensitive
        assert extractor.resolve_aliases('JS') == 'JavaScript'
        assert extractor.resolve_aliases('K8S') == 'Kubernetes'
    
    def test_abbreviation_resolution(self, extractor):
        """Test abbreviation resolution method."""
        # Programming languages
        assert extractor._resolve_abbreviations('js') == 'JavaScript'
        assert extractor._resolve_abbreviations('py') == 'Python'
        assert extractor._resolve_abbreviations('ts') == 'TypeScript'
        
        # Cloud services
        assert extractor._resolve_abbreviations('aws') == 'Amazon Web Services'
        assert extractor._resolve_abbreviations('gcp') == 'Google Cloud Platform'
        
        # Container technologies
        assert extractor._resolve_abbreviations('k8s') == 'Kubernetes'
        
        # AI/ML abbreviations
        assert extractor._resolve_abbreviations('ml') == 'Machine Learning'
        assert extractor._resolve_abbreviations('ai') == 'Artificial Intelligence'
        
        # Unknown abbreviations
        assert extractor._resolve_abbreviations('xyz') is None
    
    def test_fuzzy_matching(self, extractor):
        """Test fuzzy matching for technology names."""
        # Test similarity calculation
        assert extractor._calculate_similarity('fastapi', 'fastapi') == 1.0
        assert extractor._calculate_similarity('fastapi', 'fast-api') > 0.6  # Adjusted expectation
        assert extractor._calculate_similarity('postgres', 'postgresql') > 0.6  # Adjusted expectation
        assert extractor._calculate_similarity('react', 'angular') < 0.5
    
    def test_enhanced_ner_extraction(self, extractor):
        """Test enhanced NER extraction with multiple entity types."""
        text = "Use FastAPI with PostgreSQL and deploy on AWS Lambda"
        
        result = extractor._extract_by_ner(text)
        
        # Should extract capitalized technology names
        tech_names = [tech.canonical_name or tech.name for tech in result]
        assert 'FastAPI' in tech_names
        assert 'PostgreSQL' in tech_names
        assert 'AWS Lambda' in tech_names or 'AWS' in tech_names
    
    def test_is_common_word(self, extractor):
        """Test common word detection."""
        # Common words should be filtered out
        assert extractor._is_common_word('the') is True
        assert extractor._is_common_word('and') is True
        assert extractor._is_common_word('use') is True
        
        # Technology names should not be filtered
        assert extractor._is_common_word('FastAPI') is False
        assert extractor._is_common_word('PostgreSQL') is False
        assert extractor._is_common_word('Docker') is False
    
    def test_looks_like_technology(self, extractor):
        """Test technology name detection."""
        # Should recognize technology patterns
        assert extractor._looks_like_technology('FastAPI', 'TECH_NAME') is True
        assert extractor._looks_like_technology('React.js', 'TECH_NAME') is True
        assert extractor._looks_like_technology('PostgreSQL', 'TECH_NAME') is True
        assert extractor._looks_like_technology('Node-Express', 'TECH_NAME') is True
        
        # Should not recognize common words
        assert extractor._looks_like_technology('The', 'TECH_NAME') is False
        assert extractor._looks_like_technology('System', 'TECH_NAME') is False
    
    def test_enhanced_integration_patterns(self, extractor):
        """Test enhanced integration pattern extraction."""
        text = "Build a REST API with GraphQL support and implement microservices architecture"
        
        result = extractor._extract_integration_technologies(text)
        
        # Should extract technologies for multiple patterns
        tech_names = [tech.canonical_name for tech in result]
        
        # REST API pattern
        assert any('FastAPI' in name or 'Express' in name or 'Spring' in name for name in tech_names)
        
        # GraphQL pattern
        assert any('GraphQL' in name or 'Apollo' in name for name in tech_names)
        
        # Microservices pattern
        assert any('Kubernetes' in name or 'Docker' in name for name in tech_names)
    
    def test_context_confidence_boosts(self, extractor):
        """Test context-based confidence boosts."""
        tech = 'FastAPI'
        context = 'build a python web api using fastapi framework'
        
        boosts = extractor._calculate_context_confidence_boosts(tech, context)
        
        # Should get boosts for relevant context
        assert len(boosts) > 0
        assert sum(boosts) > 0
    
    def test_ecosystem_consistency_boost(self, extractor):
        """Test ecosystem consistency boost."""
        # Python ecosystem
        boost = extractor._calculate_ecosystem_consistency_boost(
            'FastAPI', 
            'python django flask fastapi web development'
        )
        assert boost > 0
        
        # AWS ecosystem
        boost = extractor._calculate_ecosystem_consistency_boost(
            'AWS Lambda', 
            'amazon s3 dynamodb lambda serverless'
        )
        assert boost > 0
        
        # No ecosystem match
        boost = extractor._calculate_ecosystem_consistency_boost(
            'FastAPI', 
            'java spring boot hibernate'
        )
        assert boost == 0
    
    def test_frequency_boost(self, extractor):
        """Test frequency-based confidence boost."""
        # Single mention
        boost = extractor._calculate_frequency_boost('FastAPI', 'use fastapi once')
        assert boost == 0
        
        # Multiple mentions
        boost = extractor._calculate_frequency_boost('FastAPI', 'use fastapi and fastapi framework')
        assert boost > 0
    
    def test_enhanced_confidence_calculation(self, extractor):
        """Test enhanced confidence calculation with all factors."""
        # High confidence case: explicit mention with context
        confidence = extractor.calculate_extraction_confidence(
            'FastAPI', 
            ExtractionMethod.EXPLICIT_MENTION, 
            'Build a Python REST API using FastAPI framework'
        )
        assert confidence >= 0.9
        
        # Medium confidence case: pattern matching with some context
        confidence = extractor.calculate_extraction_confidence(
            'SomeAPI', 
            ExtractionMethod.PATTERN_MATCHING, 
            'Use SomeAPI for web development'
        )
        assert 0.5 <= confidence <= 0.8
        
        # Low confidence case: ambiguous term without context
        confidence = extractor.calculate_extraction_confidence(
            'lambda', 
            ExtractionMethod.PATTERN_MATCHING, 
            'Use lambda in the code'
        )
        assert confidence < 0.6
    
    def test_comprehensive_extraction_aws_services(self, extractor):
        """Test comprehensive extraction of AWS services."""
        text = """
        Build a serverless application using AWS Lambda functions, 
        store data in Amazon S3 and DynamoDB, process text with 
        AWS Comprehend, and integrate with Amazon Connect SDK for 
        customer service automation.
        """
        
        result = extractor.extract_technologies(text)
        tech_names = [tech.canonical_name or tech.name for tech in result]
        
        # Should extract AWS services
        assert 'AWS Lambda' in tech_names
        assert 'Amazon S3' in tech_names
        assert 'Amazon DynamoDB' in tech_names
        assert 'AWS Comprehend' in tech_names
        assert 'Amazon Connect SDK' in tech_names
    
    def test_comprehensive_extraction_web_stack(self, extractor):
        """Test comprehensive extraction of web development stack."""
        text = """
        Create a modern web application using React.js for the frontend,
        FastAPI for the backend API, PostgreSQL for data storage,
        Redis for caching, and deploy using Docker containers on Kubernetes.
        """
        
        result = extractor.extract_technologies(text)
        tech_names = [tech.canonical_name or tech.name for tech in result]
        
        # Should extract web stack technologies
        assert 'React' in tech_names
        assert 'FastAPI' in tech_names
        assert 'PostgreSQL' in tech_names
        assert 'Redis' in tech_names
        assert 'Docker' in tech_names
        assert 'Kubernetes' in tech_names
    
    def test_implicit_technology_references(self, extractor):
        """Test extraction of implicit technology references."""
        text = "Use Connect SDK for call center integration and Comprehend for sentiment analysis"
        
        result = extractor.extract_technologies(text)
        tech_names = [tech.canonical_name or tech.name for tech in result]
        
        # Should resolve implicit references
        assert 'Amazon Connect SDK' in tech_names
        assert 'AWS Comprehend' in tech_names
    
    def test_integration_pattern_inference(self, extractor):
        """Test integration pattern inference."""
        text = "Implement REST API endpoints with GraphQL queries and WebSocket connections"
        
        result = extractor.extract_technologies(text)
        tech_names = [tech.canonical_name for tech in result]
        
        # Should infer technologies from patterns
        rest_api_techs = ['FastAPI', 'Express.js', 'Spring Boot', 'Django REST Framework']
        graphql_techs = ['GraphQL', 'Apollo Server']
        websocket_techs = ['Socket.IO', 'WebSocket API']
        
        assert any(tech in tech_names for tech in rest_api_techs)
        assert any(tech in tech_names for tech in graphql_techs)
        assert any(tech in tech_names for tech in websocket_techs)
    
    def test_edge_cases_and_error_handling(self, extractor):
        """Test edge cases and error handling."""
        # Empty text
        result = extractor.extract_technologies("")
        assert len(result) == 0
        
        # None input
        result = extractor.extract_technologies(None)
        assert len(result) == 0
        
        # Very short text
        result = extractor.extract_technologies("a")
        assert len(result) == 0
        
        # Text with only common words
        result = extractor.extract_technologies("the quick brown fox")
        assert len(result) == 0
        
        # Text with special characters
        result = extractor.extract_technologies("Use FastAPI!!! @#$%^&*()")
        tech_names = [tech.canonical_name or tech.name for tech in result]
        assert 'FastAPI' in tech_names
    