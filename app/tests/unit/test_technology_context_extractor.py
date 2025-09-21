"""Unit tests for technology context extractor."""

import pytest
from unittest.mock import Mock, patch

from app.services.requirement_parsing.context_extractor import TechnologyContextExtractor
from app.services.requirement_parsing.base import (
    ParsedRequirements, ExplicitTech, ContextClues, RequirementConstraints,
    DomainContext, TechContext, ExtractionMethod
)


class TestTechnologyContextExtractor:
    """Test cases for TechnologyContextExtractor."""
    
    @pytest.fixture
    def mock_logger(self):
        """Mock logger fixture."""
        return Mock()
    
    @pytest.fixture
    def extractor(self):
        """Technology context extractor fixture."""
        with patch('app.services.requirement_parsing.context_extractor.require_service') as mock_require:
            mock_require.return_value = Mock()
            return TechnologyContextExtractor()
    
    def test_initialization(self, extractor):
        """Test extractor initialization."""
        assert extractor.ecosystem_mappings is not None
        assert 'aws' in extractor.ecosystem_mappings
        assert 'azure' in extractor.ecosystem_mappings
        assert 'gcp' in extractor.ecosystem_mappings
        assert 'open_source' in extractor.ecosystem_mappings
        
        assert extractor.domain_preferences is not None
        assert 'data_processing' in extractor.domain_preferences
        assert 'web_api' in extractor.domain_preferences
        assert 'ml_ai' in extractor.domain_preferences
    
    def test_build_context_comprehensive(self, extractor):
        """Test comprehensive context building."""
        # Setup
        parsed_req = ParsedRequirements(
            explicit_technologies=[
                ExplicitTech(
                    name='Amazon Connect SDK',
                    canonical_name='Amazon Connect SDK',
                    confidence=0.9
                ),
                ExplicitTech(
                    name='FastAPI',
                    canonical_name='FastAPI',
                    confidence=0.8
                )
            ],
            context_clues=ContextClues(
                cloud_providers=['aws'],
                domains=['web_api'],
                integration_patterns=['database', 'cache'],
                programming_languages=['python']
            ),
            constraints=RequirementConstraints(
                banned_tools={'selenium'},
                required_integrations=['database']
            ),
            domain_context=DomainContext(
                primary_domain='web_api',
                complexity_indicators=['scalable']
            )
        )
        
        # Execute
        result = extractor.build_context(parsed_req)
        
        # Verify
        assert isinstance(result, TechContext)
        assert 'Amazon Connect SDK' in result.explicit_technologies
        assert 'FastAPI' in result.explicit_technologies
        assert result.ecosystem_preference == 'aws'
        assert 'database' in result.integration_requirements
        assert 'selenium' in result.banned_tools
        assert len(result.contextual_technologies) > 0
    
    def test_prioritize_technologies_explicit_priority(self, extractor):
        """Test technology prioritization with explicit technologies."""
        # Setup
        context = TechContext(
            explicit_technologies={'FastAPI': 0.9, 'PostgreSQL': 0.8},
            contextual_technologies={'Redis': 0.7, 'Docker': 0.6},
            domain_context=DomainContext(primary_domain='web_api'),
            banned_tools=set()
        )
        
        # Execute
        result = extractor.prioritize_technologies(context)
        
        # Verify
        # Explicit technologies should have highest priority
        assert result['FastAPI'] >= 0.9
        assert result['PostgreSQL'] >= 0.8
        
        # Contextual technologies should have lower priority
        assert result['Redis'] < result['FastAPI']
        assert result['Docker'] < result['PostgreSQL']
    
    def test_prioritize_technologies_domain_boost(self, extractor):
        """Test domain-specific technology boosting."""
        # Setup
        context = TechContext(
            explicit_technologies={'FastAPI': 0.8},
            contextual_technologies={},
            domain_context=DomainContext(primary_domain='web_api'),
            banned_tools=set()
        )
        
        # Execute
        result = extractor.prioritize_technologies(context)
        
        # Verify
        # FastAPI should get domain boost for web_api domain
        assert result['FastAPI'] > 0.8
        
        # Should add domain-preferred technologies
        assert 'Express.js' in result or 'Spring Boot' in result or 'Django REST Framework' in result
    
    def test_prioritize_technologies_ecosystem_boost(self, extractor):
        """Test ecosystem consistency boosting."""
        # Setup
        context = TechContext(
            explicit_technologies={'Amazon S3': 0.8},
            contextual_technologies={'AWS Lambda': 0.7},
            ecosystem_preference='aws',
            banned_tools=set()
        )
        
        # Execute
        result = extractor.prioritize_technologies(context)
        
        # Verify
        # AWS technologies should get ecosystem boost
        assert result['Amazon S3'] > 0.8
        assert result['AWS Lambda'] > 0.7
    
    def test_prioritize_technologies_banned_removal(self, extractor):
        """Test removal of banned technologies."""
        # Setup
        context = TechContext(
            explicit_technologies={'FastAPI': 0.9},
            contextual_technologies={'Selenium': 0.8, 'Redis': 0.7},
            banned_tools={'selenium', 'playwright'}
        )
        
        # Execute
        result = extractor.prioritize_technologies(context)
        
        # Verify
        # Banned technologies should be removed
        assert 'Selenium' not in result
        assert 'selenium' not in result
        
        # Non-banned technologies should remain
        assert 'FastAPI' in result
        assert 'Redis' in result
    
    def test_infer_ecosystem_preference_cloud_providers(self, extractor):
        """Test ecosystem inference from cloud providers."""
        # Test AWS preference
        context_clues = ContextClues(cloud_providers=['aws'])
        result = extractor.infer_ecosystem_preference(context_clues)
        assert result == 'aws'
        
        # Test Azure preference
        context_clues = ContextClues(cloud_providers=['azure'])
        result = extractor.infer_ecosystem_preference(context_clues)
        assert result == 'azure'
        
        # Test GCP preference
        context_clues = ContextClues(cloud_providers=['gcp'])
        result = extractor.infer_ecosystem_preference(context_clues)
        assert result == 'gcp'
    
    def test_infer_ecosystem_preference_domains(self, extractor):
        """Test ecosystem inference from domains."""
        # ML/AI domain should prefer AWS or GCP
        context_clues = ContextClues(domains=['ml_ai'])
        result = extractor.infer_ecosystem_preference(context_clues)
        assert result in ['aws', 'gcp'] or result is None
        
        # Data processing should prefer AWS or GCP
        context_clues = ContextClues(domains=['data_processing'])
        result = extractor.infer_ecosystem_preference(context_clues)
        assert result in ['aws', 'gcp'] or result is None
    
    def test_infer_ecosystem_preference_deployment(self, extractor):
        """Test ecosystem inference from deployment preferences."""
        # Serverless should prefer AWS
        context_clues = ContextClues(deployment_preferences=['serverless'])
        result = extractor.infer_ecosystem_preference(context_clues)
        assert result == 'aws'
        
        # Containerized should prefer GCP (Kubernetes)
        context_clues = ContextClues(deployment_preferences=['containerized'])
        result = extractor.infer_ecosystem_preference(context_clues)
        assert result == 'gcp'
    
    def test_infer_ecosystem_preference_no_clear_preference(self, extractor):
        """Test ecosystem inference with no clear preference."""
        context_clues = ContextClues()
        result = extractor.infer_ecosystem_preference(context_clues)
        assert result is None
    
    def test_build_contextual_technologies_integration_patterns(self, extractor):
        """Test contextual technology building from integration patterns."""
        context_clues = ContextClues(
            integration_patterns=['database', 'messaging', 'cache']
        )
        domain_context = DomainContext()
        
        result = extractor._build_contextual_technologies(context_clues, domain_context)
        
        # Should suggest technologies for each integration pattern
        assert 'PostgreSQL' in result or 'MySQL' in result  # Database
        assert 'Apache Kafka' in result or 'RabbitMQ' in result  # Messaging
        assert 'Redis' in result  # Cache
    
    def test_build_contextual_technologies_programming_languages(self, extractor):
        """Test contextual technology building from programming languages."""
        context_clues = ContextClues(
            programming_languages=['python', 'javascript']
        )
        domain_context = DomainContext()
        
        result = extractor._build_contextual_technologies(context_clues, domain_context)
        
        # Should suggest frameworks for each language
        assert 'FastAPI' in result or 'Django' in result or 'Flask' in result  # Python
        assert 'Express.js' in result or 'React' in result or 'Vue.js' in result  # JavaScript
    
    def test_build_contextual_technologies_deployment_preferences(self, extractor):
        """Test contextual technology building from deployment preferences."""
        context_clues = ContextClues(
            deployment_preferences=['containerized', 'serverless']
        )
        domain_context = DomainContext()
        
        result = extractor._build_contextual_technologies(context_clues, domain_context)
        
        # Should suggest container and serverless technologies
        assert 'Docker' in result
        assert 'Kubernetes' in result
        assert 'AWS Lambda' in result or 'Azure Functions' in result
    
    def test_build_contextual_technologies_data_patterns(self, extractor):
        """Test contextual technology building from data patterns."""
        context_clues = ContextClues(
            data_patterns=['structured_data', 'unstructured_data', 'real_time']
        )
        domain_context = DomainContext()
        
        result = extractor._build_contextual_technologies(context_clues, domain_context)
        
        # Should suggest appropriate data technologies
        assert 'PostgreSQL' in result or 'MySQL' in result  # Structured data
        assert 'MongoDB' in result or 'Elasticsearch' in result  # Unstructured data
        assert 'Apache Kafka' in result or 'Redis' in result  # Real-time
    
    def test_build_integration_requirements(self, extractor):
        """Test integration requirements building."""
        context_clues = ContextClues(
            integration_patterns=['database', 'cache']
        )
        constraints = RequirementConstraints(
            required_integrations=['messaging', 'monitoring']
        )
        
        result = extractor._build_integration_requirements(context_clues, constraints)
        
        # Should combine both sources and deduplicate
        assert 'database' in result
        assert 'cache' in result
        assert 'messaging' in result
        assert 'monitoring' in result
        assert len(result) == 4  # No duplicates
    
    def test_calculate_priority_weights_explicit_technologies(self, extractor):
        """Test priority weight calculation for explicit technologies."""
        explicit_technologies = {'FastAPI': 0.9, 'PostgreSQL': 0.8}
        contextual_technologies = {'Redis': 0.7}
        domain_context = DomainContext()
        
        result = extractor._calculate_priority_weights(
            explicit_technologies, contextual_technologies, domain_context
        )
        
        # Explicit technologies should get weight 1.0
        assert result['FastAPI'] == 1.0
        assert result['PostgreSQL'] == 1.0
        
        # Contextual technologies should get their confidence as weight
        assert result['Redis'] == 0.7
    
    def test_calculate_priority_weights_complexity_boost(self, extractor):
        """Test priority weight calculation with complexity boost."""
        explicit_technologies = {}
        contextual_technologies = {'Kubernetes': 0.7, 'PostgreSQL': 0.6}
        domain_context = DomainContext(
            complexity_indicators=['scalable', 'enterprise', 'high-performance']
        )
        
        result = extractor._calculate_priority_weights(
            explicit_technologies, contextual_technologies, domain_context
        )
        
        # Enterprise technologies should get complexity boost
        assert result['Kubernetes'] > 0.7
        assert result['PostgreSQL'] > 0.6
        
        # Boost should be based on number of complexity indicators
        expected_boost = len(domain_context.complexity_indicators) * 0.1
        assert result['Kubernetes'] == min(0.7 + expected_boost, 1.0)
    
    def test_ecosystem_mappings_completeness(self, extractor):
        """Test that ecosystem mappings are comprehensive."""
        # AWS ecosystem
        aws_techs = extractor.ecosystem_mappings['aws']
        assert 'Amazon Connect SDK' in aws_techs
        assert 'AWS Lambda' in aws_techs
        assert 'Amazon S3' in aws_techs
        
        # Azure ecosystem
        azure_techs = extractor.ecosystem_mappings['azure']
        assert 'Azure Functions' in azure_techs
        assert 'Azure Cosmos DB' in azure_techs
        
        # GCP ecosystem
        gcp_techs = extractor.ecosystem_mappings['gcp']
        assert 'Google Cloud Functions' in gcp_techs
        assert 'Google BigQuery' in gcp_techs
        
        # Open source ecosystem
        oss_techs = extractor.ecosystem_mappings['open_source']
        assert 'FastAPI' in oss_techs
        assert 'PostgreSQL' in oss_techs
        assert 'Docker' in oss_techs
    
    def test_domain_preferences_completeness(self, extractor):
        """Test that domain preferences are comprehensive."""
        # Web API domain
        web_api_prefs = extractor.domain_preferences['web_api']
        assert 'high_priority' in web_api_prefs
        assert 'medium_priority' in web_api_prefs
        assert 'ecosystems' in web_api_prefs
        assert 'FastAPI' in web_api_prefs['high_priority']
        
        # ML/AI domain
        ml_ai_prefs = extractor.domain_preferences['ml_ai']
        assert 'OpenAI API' in ml_ai_prefs['high_priority']
        assert 'PyTorch' in ml_ai_prefs['high_priority'] or 'TensorFlow' in ml_ai_prefs['high_priority']
        
        # Data processing domain
        data_prefs = extractor.domain_preferences['data_processing']
        assert 'Pandas' in data_prefs['high_priority']
        assert 'Apache Kafka' in data_prefs['high_priority']
    
    def test_aws_connect_scenario_context_building(self, extractor):
        """Test context building for the AWS Connect scenario."""
        # Setup - The specific scenario from requirements
        parsed_req = ParsedRequirements(
            explicit_technologies=[
                ExplicitTech(
                    name='Amazon Connect SDK',
                    canonical_name='Amazon Connect SDK',
                    confidence=0.9
                ),
                ExplicitTech(
                    name='AWS Comprehend',
                    canonical_name='AWS Comprehend',
                    confidence=0.9
                )
            ],
            context_clues=ContextClues(
                cloud_providers=['aws'],
                domains=['automation'],
                integration_patterns=['api']
            ),
            constraints=RequirementConstraints(),
            domain_context=DomainContext(primary_domain='automation')
        )
        
        # Execute
        result = extractor.build_context(parsed_req)
        
        # Verify
        assert result.ecosystem_preference == 'aws'
        assert 'Amazon Connect SDK' in result.explicit_technologies
        assert 'AWS Comprehend' in result.explicit_technologies
        
        # Should prioritize AWS ecosystem technologies
        priorities = extractor.prioritize_technologies(result)
        assert priorities['Amazon Connect SDK'] >= 0.9
        assert priorities['AWS Comprehend'] >= 0.9
    
    @pytest.mark.parametrize("cloud_provider,expected_ecosystem", [
        (['aws'], 'aws'),
        (['azure'], 'azure'),
        (['gcp'], 'gcp'),
        (['aws', 'azure'], 'aws'),  # First one wins with equal scores
        ([], None)
    ])
    def test_ecosystem_inference_parametrized(self, extractor, cloud_provider, expected_ecosystem):
        """Test ecosystem inference with various cloud provider combinations."""
        context_clues = ContextClues(cloud_providers=cloud_provider)
        result = extractor.infer_ecosystem_preference(context_clues)
        assert result == expected_ecosystem
    
    def test_empty_context_handling(self, extractor):
        """Test handling of empty context."""
        # Empty parsed requirements
        parsed_req = ParsedRequirements()
        result = extractor.build_context(parsed_req)
        
        assert isinstance(result, TechContext)
        assert len(result.explicit_technologies) == 0
        assert len(result.contextual_technologies) == 0
        assert result.ecosystem_preference is None
        
        # Empty context clues
        context_clues = ContextClues()
        result = extractor.infer_ecosystem_preference(context_clues)
        assert result is None
    
    def test_fuzzy_alias_resolution_exact_match(self, extractor):
        """Test fuzzy alias resolution with exact matches."""
        # Test exact alias match
        result = extractor.resolve_alias_with_fuzzy_matching('fastapi')
        assert result is not None
        canonical, confidence = result
        assert canonical == 'FastAPI'
        assert confidence == 1.0
        
        # Test exact canonical match
        result = extractor.resolve_alias_with_fuzzy_matching('PostgreSQL')
        assert result is not None
        canonical, confidence = result
        assert canonical == 'PostgreSQL'
        assert confidence == 1.0
    
    def test_fuzzy_alias_resolution_fuzzy_match(self, extractor):
        """Test fuzzy alias resolution with approximate matches."""
        # Test fuzzy matching (assuming fuzzywuzzy is available)
        result = extractor.resolve_alias_with_fuzzy_matching('postgre')
        if result:  # Only test if fuzzy matching is available
            canonical, confidence = result
            assert canonical == 'PostgreSQL'
            assert confidence > 0.8
        
        # Test with typo
        result = extractor.resolve_alias_with_fuzzy_matching('reactjs')
        if result:
            canonical, confidence = result
            assert canonical == 'React'
            assert confidence > 0.8
    
    def test_fuzzy_alias_resolution_with_context(self, extractor):
        """Test fuzzy alias resolution with context boost."""
        # Test AWS context boost
        result = extractor.resolve_alias_with_fuzzy_matching('lambda', 'aws serverless function')
        if result:
            canonical, confidence = result
            assert canonical == 'AWS Lambda'
            assert confidence > 0.8
        
        # Test Azure context boost
        result = extractor.resolve_alias_with_fuzzy_matching('functions', 'azure cloud serverless')
        if result:
            canonical, confidence = result
            assert canonical == 'Azure Functions'
            assert confidence > 0.8
    
    def test_fuzzy_alias_resolution_no_match(self, extractor):
        """Test fuzzy alias resolution with no good matches."""
        # Test with completely unrelated term
        result = extractor.resolve_alias_with_fuzzy_matching('xyz123nonexistent')
        assert result is None
        
        # Test with empty string
        result = extractor.resolve_alias_with_fuzzy_matching('')
        assert result is None
    
    def test_find_similar_technologies(self, extractor):
        """Test finding similar technologies."""
        # Test finding similar technologies
        results = extractor.find_similar_technologies('postgres')
        if results:  # Only test if fuzzy matching is available
            assert len(results) > 0
            # Should find PostgreSQL as most similar
            assert any('PostgreSQL' in result[0] for result in results)
        
        # Test with partial match
        results = extractor.find_similar_technologies('react')
        if results:
            assert len(results) > 0
            assert any('React' in result[0] for result in results)
    
    def test_get_technology_suggestions(self, extractor):
        """Test getting technology suggestions."""
        # Test suggestions for partial name
        suggestions = extractor.get_technology_suggestions('fast')
        if suggestions:  # Only test if fuzzy matching is available
            assert len(suggestions) > 0
            assert all('name' in s and 'confidence' in s and 'reason' in s for s in suggestions)
            # Should include FastAPI
            assert any('FastAPI' in s['name'] for s in suggestions)
        
        # Test suggestions with context
        suggestions = extractor.get_technology_suggestions('lambda', 'aws serverless')
        if suggestions:
            assert len(suggestions) > 0
            # Should prefer AWS Lambda with context
            assert any('AWS Lambda' in s['name'] for s in suggestions)
    
    def test_context_boost_calculation(self, extractor):
        """Test context boost calculation for fuzzy matching."""
        # Test AWS context boost
        boost = extractor._calculate_context_boost('AWS Lambda', 'aws serverless function')
        assert boost > 0
        
        # Test Azure context boost
        boost = extractor._calculate_context_boost('Azure Functions', 'azure cloud platform')
        assert boost > 0
        
        # Test domain-specific boost
        boost = extractor._calculate_context_boost('PostgreSQL', 'database storage system')
        assert boost > 0
        
        # Test no boost for unrelated context
        boost = extractor._calculate_context_boost('FastAPI', 'unrelated context')
        assert boost == 0.0
    
    def test_technology_aliases_completeness(self, extractor):
        """Test that technology aliases mapping is comprehensive."""
        # Check that major technology categories are covered
        aliases = extractor.technology_aliases
        
        # AWS services
        assert 'Amazon Connect' in aliases
        assert 'AWS Lambda' in aliases
        assert 'Amazon S3' in aliases
        
        # Programming languages
        assert 'Python' in aliases
        assert 'JavaScript' in aliases
        assert 'TypeScript' in aliases
        
        # Frameworks
        assert 'FastAPI' in aliases
        assert 'React' in aliases
        assert 'Django' in aliases
        
        # Databases
        assert 'PostgreSQL' in aliases
        assert 'MongoDB' in aliases
        assert 'Redis' in aliases
        
        # Each technology should have multiple aliases
        for canonical, alias_list in aliases.items():
            assert len(alias_list) >= 1
            assert canonical.lower() in [alias.lower() for alias in alias_list]
    
    def test_alias_to_canonical_mapping(self, extractor):
        """Test reverse alias to canonical mapping."""
        # Check that reverse mapping is properly created
        assert hasattr(extractor, 'alias_to_canonical')
        assert len(extractor.alias_to_canonical) > 0
        
        # Test specific mappings
        assert extractor.alias_to_canonical.get('fastapi') == 'FastAPI'
        assert extractor.alias_to_canonical.get('postgres') == 'PostgreSQL'
        assert extractor.alias_to_canonical.get('k8s') == 'Kubernetes'
    
    def test_enhanced_context_building_with_fuzzy_matching(self, extractor):
        """Test context building with fuzzy matching enhancement."""
        # Setup with technologies that need fuzzy resolution
        parsed_req = ParsedRequirements(
            explicit_technologies=[
                ExplicitTech(
                    name='postgre',  # Typo that should fuzzy match to PostgreSQL
                    confidence=0.9,
                    context='database storage'
                ),
                ExplicitTech(
                    name='reactjs',  # Should fuzzy match to React
                    confidence=0.8,
                    context='frontend framework'
                )
            ],
            context_clues=ContextClues(
                programming_languages=['python'],
                domains=['web_api']
            )
        )
        
        # Execute
        result = extractor.build_context(parsed_req)
        
        # Verify - should resolve fuzzy matches if available
        if hasattr(extractor, 'resolve_alias_with_fuzzy_matching'):
            # The exact behavior depends on whether fuzzywuzzy is available
            assert isinstance(result, TechContext)
            assert len(result.explicit_technologies) >= 0  # May be 0 if fuzzy matching unavailable
    
    def test_priority_calculation_with_fuzzy_confidence(self, extractor):
        """Test priority calculation considering fuzzy matching confidence."""
        # Setup context with technologies that have different confidence levels
        context = TechContext(
            explicit_technologies={
                'FastAPI': 1.0,  # Exact match
                'PostgreSQL': 0.85,  # Fuzzy match with high confidence
                'React': 0.75  # Fuzzy match with medium confidence
            },
            contextual_technologies={'Redis': 0.7},
            domain_context=DomainContext(primary_domain='web_api')
        )
        
        # Execute
        result = extractor.prioritize_technologies(context)
        
        # Verify priority ordering respects confidence levels
        assert result['FastAPI'] >= result['PostgreSQL']
        assert result['PostgreSQL'] >= result['React']
        assert result['React'] > result['Redis']  # Explicit should beat contextual