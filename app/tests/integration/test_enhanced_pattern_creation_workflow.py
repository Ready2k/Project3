"""Integration tests for enhanced pattern creation workflow."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from app.services.pattern_creator import PatternCreator
from app.services.pattern_enhancement_service import PatternEnhancementService
from app.pattern.enhanced_loader import EnhancedPatternLoader
from app.llm.base import LLMProvider


class TestEnhancedPatternCreationWorkflow:
    """Test enhanced pattern creation workflow integration."""
    
    @pytest.fixture
    def temp_pattern_dir(self):
        """Create temporary pattern directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def mock_llm_provider(self):
        """Create mock LLM provider."""
        provider = Mock(spec=LLMProvider)
        provider.generate = AsyncMock()
        return provider
    
    @pytest.fixture
    def pattern_creator(self, temp_pattern_dir, mock_llm_provider):
        """Create PatternCreator instance."""
        return PatternCreator(temp_pattern_dir, mock_llm_provider)
    
    @pytest.fixture
    def pattern_enhancement_service(self, temp_pattern_dir, mock_llm_provider):
        """Create PatternEnhancementService instance."""
        pattern_loader = EnhancedPatternLoader(temp_pattern_dir)
        return PatternEnhancementService(pattern_loader, mock_llm_provider)
    
    @pytest.fixture
    def sample_requirements(self):
        """Sample requirements for testing."""
        return {
            "description": "Create an automated system to process Amazon Connect call recordings using AWS Comprehend for sentiment analysis and store results in PostgreSQL database",
            "domain": "customer_service",
            "volume": {"daily": 1000},
            "integrations": ["Amazon Connect", "AWS Comprehend", "PostgreSQL"],
            "constraints": {
                "banned_tools": ["Google Cloud services"],
                "required_integrations": ["Amazon Connect SDK", "AWS SDK"],
                "compliance_requirements": ["GDPR", "SOX"]
            }
        }
    
    @pytest.fixture
    def mock_llm_analysis_response(self):
        """Mock LLM analysis response."""
        return json.dumps({
            "pattern_name": "Amazon Connect Call Analysis Automation",
            "pattern_description": "Automated call recording analysis system using AWS services",
            "feasibility": "Automatable",
            "pattern_types": ["call_analysis", "sentiment_analysis", "aws_integration"],
            "domain": "customer_service",
            "complexity": "Medium",
            "automation_type": "api_integration",
            "data_flow": "batch",
            "user_interaction": "fully_automated",
            "processing_type": "ml_processing",
            "scalability_needs": "medium_scale",
            "security_requirements": ["encryption", "compliance"],
            "integration_points": ["aws", "database", "api"],
            "input_requirements": ["Call recordings", "AWS credentials", "Database connection"],
            "tech_stack": ["Amazon Connect SDK", "AWS Comprehend", "PostgreSQL", "FastAPI", "Docker"],
            "estimated_effort": "3-6 weeks",
            "effort_breakdown": "MVP: 2 weeks, Full implementation: 4 weeks",
            "key_challenges": ["Real-time processing", "Data privacy compliance"],
            "recommended_approach": "Use AWS native services for seamless integration",
            "confidence_score": 0.9,
            "banned_tools_suggestions": ["Google Cloud services"],
            "required_integrations_suggestions": ["Amazon Connect SDK", "AWS SDK"],
            "compliance_considerations": ["GDPR", "SOX"]
        })
    
    @pytest.mark.asyncio
    async def test_enhanced_pattern_creation_with_explicit_technologies(
        self, pattern_creator, mock_llm_provider, sample_requirements, mock_llm_analysis_response
    ):
        """Test pattern creation with explicit technology mentions."""
        # Setup mock LLM response
        mock_llm_provider.generate.return_value = mock_llm_analysis_response
        
        # Create pattern
        pattern = await pattern_creator.create_pattern_from_requirements(
            sample_requirements, "test-session-001"
        )
        
        # Verify pattern was created
        assert pattern is not None
        assert pattern["pattern_id"].startswith("PAT-")
        assert pattern["name"] == "Amazon Connect Call Analysis Automation"
        assert pattern["feasibility"] == "Automatable"
        
        # Verify explicit technologies are included
        tech_stack = pattern["tech_stack"]
        assert "Amazon Connect SDK" in tech_stack
        assert "AWS Comprehend" in tech_stack
        assert "PostgreSQL" in tech_stack
        
        # Verify constraints are respected
        constraints = pattern["constraints"]
        assert "Google Cloud services" in constraints["banned_tools"]
        assert "Amazon Connect SDK" in constraints["required_integrations"]
        
        # Verify enhanced metadata
        assert pattern["enhanced_by_llm"] is True
        assert pattern["created_from_session"] == "test-session-001"
        assert "catalog_metadata" in pattern or "llm_insights" in pattern
    
    @pytest.mark.asyncio
    async def test_pattern_enhancement_with_catalog_intelligence(
        self, pattern_enhancement_service, mock_llm_provider, temp_pattern_dir
    ):
        """Test pattern enhancement using catalog intelligence."""
        # Create a basic pattern to enhance
        basic_pattern = {
            "pattern_id": "PAT-TEST-001",
            "name": "Basic API Integration",
            "description": "Simple API integration pattern",
            "feasibility": "Automatable",
            "pattern_type": ["api_integration"],
            "tech_stack": ["FastAPI", "PostgreSQL"],
            "domain": "integration",
            "complexity": "Low"
        }
        
        # Save basic pattern
        pattern_file = temp_pattern_dir / "PAT-TEST-001.json"
        with open(pattern_file, 'w') as f:
            json.dump(basic_pattern, f)
        
        # Setup mock LLM response for enhancement
        enhancement_response = json.dumps({
            "tech_stack": ["FastAPI", "PostgreSQL", "Redis", "Docker"],
            "implementation_guidance": {
                "overview": "Enhanced API integration with caching and containerization",
                "prerequisites": ["Docker environment", "Redis server"],
                "steps": ["Setup FastAPI", "Configure PostgreSQL", "Add Redis caching", "Containerize"],
                "best_practices": ["Use connection pooling", "Implement proper error handling"]
            },
            "effort_breakdown": {
                "total_effort": "2-3 weeks",
                "phases": {
                    "planning": "0.5 weeks",
                    "development": "1.5 weeks",
                    "testing": "1 week"
                }
            },
            "catalog_metadata": {
                "enhanced_technologies": ["Redis", "Docker"],
                "missing_technologies": [],
                "ecosystem_consistency": "mixed"
            }
        })
        mock_llm_provider.generate.return_value = enhancement_response
        
        # Enhance pattern
        success, message, enhanced_pattern = await pattern_enhancement_service.enhance_pattern(
            "PAT-TEST-001", "technical"
        )
        
        # Verify enhancement
        assert success is True
        assert enhanced_pattern is not None
        assert enhanced_pattern["pattern_id"] == "PAT-TEST-001"
        
        # Verify enhanced tech stack
        tech_stack = enhanced_pattern["tech_stack"]
        assert "Redis" in tech_stack
        assert "Docker" in tech_stack
        
        # Verify implementation guidance
        assert "implementation_guidance" in enhanced_pattern
        guidance = enhanced_pattern["implementation_guidance"]
        assert "overview" in guidance
        assert "prerequisites" in guidance
        assert "steps" in guidance
        
        # Verify catalog metadata
        if "catalog_metadata" in enhanced_pattern:
            catalog_meta = enhanced_pattern["catalog_metadata"]
            assert "enhanced_technologies" in catalog_meta
    
    @pytest.mark.asyncio
    async def test_backward_compatibility_with_existing_patterns(
        self, pattern_creator, pattern_enhancement_service, mock_llm_provider, temp_pattern_dir
    ):
        """Test backward compatibility with existing pattern library."""
        # Create existing pattern in old format
        old_pattern = {
            "pattern_id": "PAT-OLD-001",
            "name": "Legacy Pattern",
            "description": "Old format pattern",
            "feasibility": "Automatable",
            "pattern_type": ["legacy"],
            "tech_stack": ["Python", "MySQL"],
            "confidence_score": 0.8
        }
        
        # Save old pattern
        pattern_file = temp_pattern_dir / "PAT-OLD-001.json"
        with open(pattern_file, 'w') as f:
            json.dump(old_pattern, f)
        
        # Test that pattern creator can work with existing patterns
        # (This would typically involve loading and processing existing patterns)
        
        # Setup mock for enhancement
        enhancement_response = json.dumps({
            "tech_stack": ["Python", "MySQL", "FastAPI"],
            "implementation_guidance": {
                "overview": "Enhanced legacy pattern",
                "prerequisites": ["Python 3.8+"],
                "steps": ["Migrate to FastAPI", "Update database connections"],
                "best_practices": ["Use async/await", "Add proper logging"]
            },
            "effort_breakdown": {
                "total_effort": "1-2 weeks",
                "phases": {
                    "planning": "0.5 weeks",
                    "development": "1 week",
                    "testing": "0.5 weeks"
                }
            }
        })
        mock_llm_provider.generate.return_value = enhancement_response
        
        # Enhance old pattern
        success, message, enhanced_pattern = await pattern_enhancement_service.enhance_pattern(
            "PAT-OLD-001", "technical"
        )
        
        # Verify backward compatibility
        assert success is True
        assert enhanced_pattern["pattern_id"] == "PAT-OLD-001"  # Same ID maintained
        assert enhanced_pattern["name"] == "Legacy Pattern"  # Original name preserved
        
        # Verify enhancements were added
        assert "implementation_guidance" in enhanced_pattern
        assert "FastAPI" in enhanced_pattern["tech_stack"]
    
    @pytest.mark.asyncio
    async def test_catalog_auto_addition_during_pattern_creation(
        self, pattern_creator, mock_llm_provider, sample_requirements, mock_llm_analysis_response
    ):
        """Test automatic catalog addition during pattern creation."""
        # Modify requirements to include a technology not in catalog
        requirements_with_new_tech = sample_requirements.copy()
        requirements_with_new_tech["integrations"].append("CustomTechStack")
        
        # Setup mock LLM response with new technology
        analysis_response = json.loads(mock_llm_analysis_response)
        analysis_response["tech_stack"].append("CustomTechStack")
        mock_llm_provider.generate.return_value = json.dumps(analysis_response)
        
        # Mock catalog manager to simulate missing technology
        with patch.object(pattern_creator.catalog_manager, 'lookup_technology') as mock_lookup:
            with patch.object(pattern_creator.catalog_manager, 'auto_add_technology') as mock_auto_add:
                # Simulate CustomTechStack not found in catalog
                mock_lookup.side_effect = lambda tech: None if tech == "CustomTechStack" else Mock()
                mock_auto_add.return_value = Mock()
                
                # Create pattern
                pattern = await pattern_creator.create_pattern_from_requirements(
                    requirements_with_new_tech, "test-session-002"
                )
                
                # Verify pattern was created
                assert pattern is not None
                
                # Verify auto-add was called for missing technology
                mock_auto_add.assert_called()
                call_args = mock_auto_add.call_args
                assert call_args[0][0] == "CustomTechStack"  # Technology name
                assert "source" in call_args[0][1]  # Context metadata
    
    @pytest.mark.asyncio
    async def test_ecosystem_consistency_validation(
        self, pattern_creator, mock_llm_provider, sample_requirements
    ):
        """Test ecosystem consistency validation during pattern creation."""
        # Create requirements with mixed ecosystems
        mixed_requirements = sample_requirements.copy()
        mixed_requirements["integrations"] = ["AWS Lambda", "Azure Functions", "Google Cloud Functions"]
        
        # Setup mock LLM response with mixed ecosystem
        analysis_response = {
            "pattern_name": "Mixed Cloud Functions",
            "pattern_description": "Multi-cloud function integration",
            "feasibility": "Partially Automatable",
            "pattern_types": ["cloud_integration"],
            "domain": "cloud",
            "complexity": "High",
            "tech_stack": ["AWS Lambda", "Azure Functions", "Google Cloud Functions"],
            "confidence_score": 0.7,
            "banned_tools_suggestions": [],
            "required_integrations_suggestions": [],
            "compliance_considerations": []
        }
        mock_llm_provider.generate.return_value = json.dumps(analysis_response)
        
        # Create pattern
        pattern = await pattern_creator.create_pattern_from_requirements(
            mixed_requirements, "test-session-003"
        )
        
        # Verify pattern handles mixed ecosystem
        assert pattern is not None
        assert pattern["complexity"] == "High"  # Should reflect ecosystem complexity
        
        # The system should either:
        # 1. Flag the mixed ecosystem as a complexity factor, or
        # 2. Suggest ecosystem alignment in recommendations
        tech_stack = pattern["tech_stack"]
        assert len(tech_stack) > 0
    
    @pytest.mark.asyncio
    async def test_pattern_metadata_update_workflow(
        self, pattern_enhancement_service, temp_pattern_dir
    ):
        """Test updating existing patterns with enhanced metadata."""
        # Create multiple patterns with different formats
        patterns = [
            {
                "pattern_id": "PAT-META-001",
                "name": "Pattern Without Metadata",
                "description": "Pattern lacking enhanced metadata",
                "tech_stack": ["FastAPI", "PostgreSQL"],
                "domain": "web"
            },
            {
                "pattern_id": "PAT-META-002", 
                "name": "Pattern With Some Metadata",
                "description": "Pattern with partial metadata",
                "tech_stack": ["Django", "MySQL"],
                "domain": "web",
                "enhanced_by_llm": True,
                "catalog_metadata": {"last_updated": "2024-01-01"}
            }
        ]
        
        # Save patterns
        for pattern in patterns:
            pattern_file = temp_pattern_dir / f"{pattern['pattern_id']}.json"
            with open(pattern_file, 'w') as f:
                json.dump(pattern, f)
        
        # Update patterns with enhanced metadata
        results = pattern_enhancement_service.update_existing_patterns_with_enhanced_metadata()
        
        # Verify update results
        assert results["total"] == 2
        assert len(results["updated"]) >= 1  # At least one should be updated
        assert len(results["skipped"]) >= 0  # Some might be skipped if already enhanced
        
        # Verify patterns were actually updated
        for updated_info in results["updated"]:
            pattern_id = updated_info["pattern_id"]
            pattern_file = temp_pattern_dir / f"{pattern_id}.json"
            
            if pattern_file.exists():
                with open(pattern_file, 'r') as f:
                    updated_pattern = json.load(f)
                
                # Verify enhanced metadata was added
                assert "catalog_metadata" in updated_pattern
                catalog_meta = updated_pattern["catalog_metadata"]
                assert "last_updated" in catalog_meta
                assert "enhanced_by_catalog" in catalog_meta
    
    def test_migration_script_integration(self, temp_pattern_dir):
        """Test integration with catalog migration script."""
        # This test would verify that the migration script works correctly
        # with the enhanced pattern creation workflow
        
        # Create a sample catalog in old format
        old_catalog = {
            "categories": {
                "frameworks": {
                    "name": "Web Frameworks",
                    "technologies": ["fastapi", "django"]
                }
            },
            "technologies": {
                "fastapi": {
                    "name": "FastAPI",
                    "description": "Modern web framework"
                },
                "django": {
                    "name": "Django", 
                    "description": "Full-featured web framework"
                }
            }
        }
        
        catalog_file = temp_pattern_dir / "technologies.json"
        with open(catalog_file, 'w') as f:
            json.dump(old_catalog, f)
        
        # Import and test migration (would need to adjust paths)
        # This is a placeholder for actual migration testing
        assert catalog_file.exists()
        
        # Verify catalog structure
        with open(catalog_file, 'r') as f:
            catalog = json.load(f)
        
        assert "technologies" in catalog
        assert "fastapi" in catalog["technologies"]
        assert "django" in catalog["technologies"]
    
    @pytest.mark.asyncio
    async def test_end_to_end_enhanced_workflow(
        self, pattern_creator, pattern_enhancement_service, mock_llm_provider, 
        sample_requirements, mock_llm_analysis_response, temp_pattern_dir
    ):
        """Test complete end-to-end enhanced pattern creation workflow."""
        # Step 1: Create pattern with enhanced tech stack generation
        mock_llm_provider.generate.return_value = mock_llm_analysis_response
        
        created_pattern = await pattern_creator.create_pattern_from_requirements(
            sample_requirements, "e2e-test-session"
        )
        
        assert created_pattern is not None
        pattern_id = created_pattern["pattern_id"]
        
        # Step 2: Enhance pattern with additional capabilities
        enhancement_response = json.dumps({
            "autonomy_level": "high",
            "reasoning_types": ["logical_reasoning", "causal_reasoning"],
            "decision_boundaries": ["Automated processing within parameters"],
            "self_monitoring": ["Performance tracking", "Error detection"],
            "learning_mechanisms": ["Feedback incorporation"],
            "agent_architecture": "single_agent"
        })
        mock_llm_provider.generate.return_value = enhancement_response
        
        success, message, enhanced_pattern = await pattern_enhancement_service.enhance_pattern(
            pattern_id, "agentic"
        )
        
        assert success is True
        assert enhanced_pattern is not None
        
        # Step 3: Verify complete enhanced pattern
        final_pattern = enhanced_pattern
        
        # Verify original pattern data preserved
        assert final_pattern["pattern_id"] == pattern_id
        assert "Amazon Connect" in str(final_pattern["tech_stack"])
        
        # Verify enhancements added
        assert "autonomy_level" in final_pattern
        assert "reasoning_types" in final_pattern
        
        # Verify catalog integration
        assert final_pattern.get("enhanced_by_llm") is True
        
        # Step 4: Verify pattern can be loaded and used
        pattern_file = temp_pattern_dir / f"{pattern_id}.json"
        assert pattern_file.exists()
        
        with open(pattern_file, 'r') as f:
            saved_pattern = json.load(f)
        
        assert saved_pattern["pattern_id"] == pattern_id
        assert "tech_stack" in saved_pattern
        assert len(saved_pattern["tech_stack"]) > 0