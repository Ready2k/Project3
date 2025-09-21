"""Integration test for enhanced TechStackGenerator end-to-end workflow."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.tech_stack_generator import TechStackGenerator
from app.llm.base import LLMProvider


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self, response=None):
        self.response = response or {
            "tech_stack": [
                {"name": "FastAPI", "reason": "Explicit mention in requirements", "confidence": 1.0},
                {"name": "PostgreSQL", "reason": "Database requirement", "confidence": 0.9},
                {"name": "Redis", "reason": "Caching needs", "confidence": 0.8},
                {"name": "Docker", "reason": "Containerization", "confidence": 0.7}
            ]
        }
    
    async def generate(self, prompt: str, purpose: str = None):
        return self.response
    
    @property
    def model(self) -> str:
        return "mock-model"
    
    def get_model_info(self):
        return {"name": "mock-model", "provider": "mock"}
    
    async def test_connection(self) -> bool:
        return True


async def test_enhanced_workflow_with_explicit_technologies():
    """Test the complete enhanced workflow with explicit technologies."""
    print("Testing enhanced workflow with explicit technologies...")
    
    # Mock all service dependencies to avoid initialization issues
    with patch('app.utils.imports.require_service') as mock_require_service:
        mock_logger = Mock()
        mock_require_service.return_value = mock_logger
        
        # Create generator with mock LLM
        generator = TechStackGenerator(
            llm_provider=MockLLMProvider(),
            auto_update_catalog=True
        )
        
        # Test requirements with explicit technologies
        requirements = {
            "description": "Build a REST API using FastAPI with PostgreSQL database, Redis for caching, and Docker for deployment",
            "domain": "web_api",
            "integrations": ["database", "cache", "containerization"],
            "constraints": {
                "banned_tools": ["MongoDB", "MySQL"],
                "required_integrations": ["database"]
            }
        }
        
        # Mock pattern matches (empty for this test)
        matches = []
        
        # Execute the enhanced generation
        result = await generator.generate_tech_stack(
            matches=matches,
            requirements=requirements,
            constraints=requirements.get("constraints")
        )
        
        print(f"Generated tech stack: {result}")
        
        # Verify results
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Should include explicit technologies
        explicit_techs = {"FastAPI", "PostgreSQL", "Redis", "Docker"}
        included_explicit = set(result) & explicit_techs
        
        print(f"Explicit technologies found: {included_explicit}")
        print(f"Inclusion rate: {len(included_explicit) / len(explicit_techs):.2%}")
        
        # Should have good inclusion rate for explicit technologies
        assert len(included_explicit) >= 3, f"Should include at least 3 explicit technologies, got {len(included_explicit)}"
        
        # Should not include banned technologies
        banned_techs = {"MongoDB", "MySQL"}
        included_banned = set(result) & banned_techs
        assert len(included_banned) == 0, f"Should not include banned technologies: {included_banned}"
        
        # Verify metrics were updated
        metrics = generator.get_generation_metrics()
        assert metrics['total_generations'] > 0
        
        print("✓ Enhanced workflow with explicit technologies test passed!")


async def test_enhanced_workflow_fallback_to_rule_based():
    """Test fallback to enhanced rule-based generation when LLM fails."""
    print("Testing enhanced workflow fallback to rule-based generation...")
    
    with patch('app.utils.imports.require_service') as mock_require_service:
        mock_logger = Mock()
        mock_require_service.return_value = mock_logger
        
        # Create generator with failing LLM
        class FailingLLMProvider(LLMProvider):
            async def generate(self, prompt: str, purpose: str = None):
                raise Exception("LLM service unavailable")
            
            @property
            def model(self) -> str:
                return "failing-model"
            
            def get_model_info(self):
                return {"name": "failing-model", "provider": "mock"}
            
            async def test_connection(self) -> bool:
                return False
        
        generator = TechStackGenerator(
            llm_provider=FailingLLMProvider(),
            auto_update_catalog=True
        )
        
        requirements = {
            "description": "Build web application with database and caching",
            "domain": "web_api"
        }
        
        matches = []
        
        # Should fall back to enhanced rule-based generation
        result = await generator.generate_tech_stack(
            matches=matches,
            requirements=requirements
        )
        
        print(f"Fallback generated tech stack: {result}")
        
        # Should still return a valid tech stack
        assert isinstance(result, list)
        assert len(result) > 0
        
        print("✓ Enhanced workflow fallback test passed!")


async def test_enhanced_workflow_with_constraints():
    """Test enhanced workflow with various constraints."""
    print("Testing enhanced workflow with constraints...")
    
    with patch('app.utils.imports.require_service') as mock_require_service:
        mock_logger = Mock()
        mock_require_service.return_value = mock_logger
        
        # Mock LLM that tries to include banned technologies
        mock_llm = MockLLMProvider({
            "tech_stack": [
                {"name": "FastAPI", "reason": "API framework"},
                {"name": "MongoDB", "reason": "Database"},  # This is banned
                {"name": "MySQL", "reason": "Alternative DB"},  # This is also banned
                {"name": "Redis", "reason": "Caching"}
            ]
        })
        
        generator = TechStackGenerator(
            llm_provider=mock_llm,
            auto_update_catalog=True
        )
        
        requirements = {
            "description": "Build API with FastAPI and database storage",
            "domain": "web_api",
            "constraints": {
                "banned_tools": ["MongoDB", "MySQL"],
                "required_integrations": ["database"]
            }
        }
        
        matches = []
        
        result = await generator.generate_tech_stack(
            matches=matches,
            requirements=requirements,
            constraints=requirements["constraints"]
        )
        
        print(f"Constrained tech stack: {result}")
        
        # Should not include banned technologies
        banned_techs = {"MongoDB", "MySQL"}
        included_banned = set(result) & banned_techs
        assert len(included_banned) == 0, f"Should not include banned technologies: {included_banned}"
        
        # Should include allowed technologies
        assert "FastAPI" in result
        assert "Redis" in result
        
        print("✓ Enhanced workflow with constraints test passed!")


async def test_ecosystem_consistency():
    """Test ecosystem consistency in technology selection."""
    print("Testing ecosystem consistency...")
    
    with patch('app.utils.imports.require_service') as mock_require_service:
        mock_logger = Mock()
        mock_require_service.return_value = mock_logger
        
        generator = TechStackGenerator(
            llm_provider=MockLLMProvider({
                "tech_stack": [
                    {"name": "AWS Lambda", "reason": "Serverless compute"},
                    {"name": "Amazon S3", "reason": "Storage"},
                    {"name": "Amazon DynamoDB", "reason": "Database"},
                    {"name": "Amazon CloudWatch", "reason": "Monitoring"}
                ]
            }),
            auto_update_catalog=True
        )
        
        requirements = {
            "description": "Build serverless application using AWS Lambda and S3 storage",
            "domain": "serverless",
            "cloud_provider": "aws"
        }
        
        matches = []
        
        result = await generator.generate_tech_stack(
            matches=matches,
            requirements=requirements
        )
        
        print(f"AWS ecosystem tech stack: {result}")
        
        # Should prefer AWS technologies when AWS is mentioned
        aws_techs = {"AWS Lambda", "Amazon S3", "Amazon DynamoDB", "Amazon CloudWatch", "AWS API Gateway"}
        aws_count = len(set(result) & aws_techs)
        
        print(f"AWS technologies included: {aws_count}")
        
        # Should have some AWS technologies when AWS ecosystem is indicated
        assert aws_count > 0, "Should include AWS technologies when AWS ecosystem is indicated"
        
        print("✓ Ecosystem consistency test passed!")


async def main():
    """Run all integration tests."""
    print("Running enhanced TechStackGenerator integration tests...\n")
    
    try:
        await test_enhanced_workflow_with_explicit_technologies()
        print()
        
        await test_enhanced_workflow_fallback_to_rule_based()
        print()
        
        await test_enhanced_workflow_with_constraints()
        print()
        
        await test_ecosystem_consistency()
        print()
        
        print("🎉 All integration tests passed!")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)