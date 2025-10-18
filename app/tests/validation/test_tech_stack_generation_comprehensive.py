"""
Comprehensive validation and testing framework for tech stack generation.

This module provides end-to-end testing for the tech stack generation system,
including regression tests for the AWS Connect bug case and performance benchmarks.
"""

import pytest
import time
import json
from unittest.mock import Mock

from app.services.tech_stack_generator import TechStackGenerator
from app.services.requirement_parsing.enhanced_parser import EnhancedRequirementParser
from app.services.requirement_parsing.context_extractor import (
    TechnologyContextExtractor,
)
from app.services.catalog.intelligent_manager import IntelligentCatalogManager
from app.services.validation.compatibility_validator import (
    TechnologyCompatibilityValidator,
)
from app.services.context_aware_prompt_generator import ContextAwarePromptGenerator
from app.services.requirement_parsing.context_prioritizer import (
    RequirementContextPrioritizer,
)
from app.services.ecosystem.intelligence import EcosystemIntelligence


class TestTechStackGenerationComprehensive:
    """Comprehensive test suite for tech stack generation scenarios."""

    @pytest.fixture
    def tech_stack_generator(self):
        """Create a fully configured tech stack generator."""
        generator = TechStackGenerator()
        # Mock the LLM provider to avoid external API calls
        generator.llm_provider = Mock()
        return generator

    @pytest.fixture
    def requirement_parser(self):
        """Create enhanced requirement parser."""
        return EnhancedRequirementParser()

    @pytest.fixture
    def context_extractor(self):
        """Create technology context extractor."""
        return TechnologyContextExtractor()

    @pytest.fixture
    def catalog_manager(self):
        """Create intelligent catalog manager."""
        return IntelligentCatalogManager()

    @pytest.fixture
    def compatibility_validator(self):
        """Create technology compatibility validator."""
        return TechnologyCompatibilityValidator()

    @pytest.fixture
    def prompt_generator(self):
        """Create context-aware prompt generator."""
        return ContextAwarePromptGenerator()

    @pytest.fixture
    def context_prioritizer(self):
        """Create requirement context prioritizer."""
        return RequirementContextPrioritizer()

    @pytest.fixture
    def ecosystem_intelligence(self):
        """Create ecosystem intelligence service."""
        return EcosystemIntelligence()

    # AWS Connect Bug Regression Tests

    def test_aws_connect_bug_regression(self, tech_stack_generator, requirement_parser):
        """
        Regression test for the original AWS Connect bug.

        This test ensures that when requirements explicitly mention AWS services,
        they are properly extracted and prioritized in the tech stack generation.
        """
        # Original bug case: AWS Connect mentioned but not included in tech stack
        requirements = {
            "description": """
            Build a customer service automation system that integrates with Amazon Connect
            for call routing and AWS Comprehend for sentiment analysis. The system should
            handle customer inquiries and route them based on sentiment and intent.
            Use AWS S3 for storing call recordings and DynamoDB for customer data.
            """,
            "domain": "customer_service",
            "integrations": ["Amazon Connect", "AWS Comprehend", "AWS S3", "DynamoDB"],
            "cloud_provider": "AWS",
        }

        # Parse requirements
        parsed = requirement_parser.parse_requirements(requirements)

        # Verify explicit technologies are extracted
        explicit_techs = [tech.name for tech in parsed.explicit_technologies]
        assert "Amazon Connect" in explicit_techs
        assert "AWS Comprehend" in explicit_techs
        assert "AWS S3" in explicit_techs
        assert "DynamoDB" in explicit_techs

        # Mock LLM response that should include explicit technologies
        mock_response = {
            "tech_stack": [
                "Amazon Connect",
                "AWS Comprehend",
                "AWS S3",
                "DynamoDB",
                "AWS Lambda",
                "Python",
                "FastAPI",
            ],
            "reasoning": {
                "Amazon Connect": "Explicitly mentioned for call routing",
                "AWS Comprehend": "Explicitly mentioned for sentiment analysis",
                "AWS S3": "Explicitly mentioned for call recordings storage",
                "DynamoDB": "Explicitly mentioned for customer data",
            },
        }

        tech_stack_generator.llm_provider.generate_response = Mock(
            return_value=json.dumps(mock_response)
        )

        # Generate tech stack
        result = tech_stack_generator.generate_tech_stack(requirements)

        # Verify all explicit AWS technologies are included
        generated_stack = result.get("tech_stack", [])
        assert "Amazon Connect" in generated_stack
        assert "AWS Comprehend" in generated_stack
        assert "AWS S3" in generated_stack
        assert "DynamoDB" in generated_stack

        # Verify at least 70% of explicit technologies are included
        explicit_count = len(explicit_techs)
        included_count = sum(1 for tech in explicit_techs if tech in generated_stack)
        inclusion_rate = included_count / explicit_count if explicit_count > 0 else 0
        assert (
            inclusion_rate >= 0.7
        ), f"Only {inclusion_rate:.2%} of explicit technologies included"

    def test_multi_cloud_context_prioritization(
        self, tech_stack_generator, requirement_parser
    ):
        """Test that cloud-specific context is properly prioritized."""
        requirements = {
            "description": """
            Create a data processing pipeline using Azure Data Factory for ETL,
            Azure Cosmos DB for storage, and Azure Functions for serverless processing.
            Integrate with Microsoft Graph API for Office 365 data.
            """,
            "domain": "data_processing",
            "cloud_provider": "Azure",
            "integrations": [
                "Azure Data Factory",
                "Azure Cosmos DB",
                "Azure Functions",
                "Microsoft Graph API",
            ],
        }

        parsed = requirement_parser.parse_requirements(requirements)

        # Verify Azure ecosystem is detected
        assert parsed.context_clues.cloud_provider == "Azure"

        # Verify explicit Azure technologies are extracted
        explicit_techs = [tech.name for tech in parsed.explicit_technologies]
        assert "Azure Data Factory" in explicit_techs
        assert "Azure Cosmos DB" in explicit_techs
        assert "Azure Functions" in explicit_techs
        assert "Microsoft Graph API" in explicit_techs

    def test_generic_pattern_override(self, tech_stack_generator, requirement_parser):
        """Test that explicit technologies override generic pattern recommendations."""
        requirements = {
            "description": """
            Build a multi-agent system for automated trading using AWS Bedrock for AI models,
            Amazon SQS for message queuing, and AWS Lambda for agent execution.
            The system should use specific AWS services, not generic alternatives.
            """,
            "domain": "multi_agent",
            "pattern_indicators": ["multi-agent", "automated"],
            "explicit_technologies": ["AWS Bedrock", "Amazon SQS", "AWS Lambda"],
            "cloud_provider": "AWS",
        }

        parsed = requirement_parser.parse_requirements(requirements)

        # Verify explicit technologies have higher priority than pattern-based ones
        explicit_techs = {
            tech.name: tech.confidence for tech in parsed.explicit_technologies
        }

        # All explicit technologies should have confidence >= 0.9
        for tech_name, confidence in explicit_techs.items():
            assert confidence >= 0.9, f"{tech_name} has low confidence: {confidence}"

        # Verify AWS ecosystem consistency
        aws_techs = [
            tech for tech in explicit_techs.keys() if tech.startswith(("AWS", "Amazon"))
        ]
        assert len(aws_techs) >= 3, "Should detect multiple AWS technologies"

    # End-to-End Test Scenarios

    @pytest.mark.asyncio
    async def test_end_to_end_data_processing_scenario(self, tech_stack_generator):
        """Complete end-to-end test for data processing scenario."""
        requirements = {
            "description": """
            Automate daily processing of customer data from CSV files stored in AWS S3.
            Use AWS Glue for ETL, Amazon RDS for storage, and AWS Lambda for triggers.
            Generate reports using Amazon QuickSight and send notifications via Amazon SES.
            """,
            "domain": "data_processing",
            "frequency": "daily",
            "data_volume": {"daily": 100000},
            "cloud_provider": "AWS",
            "explicit_technologies": [
                "AWS S3",
                "AWS Glue",
                "Amazon RDS",
                "AWS Lambda",
                "Amazon QuickSight",
                "Amazon SES",
            ],
        }

        # Mock successful LLM response
        mock_response = {
            "tech_stack": [
                "AWS S3",
                "AWS Glue",
                "Amazon RDS",
                "AWS Lambda",
                "Amazon QuickSight",
                "Amazon SES",
                "Python",
                "Pandas",
            ],
            "reasoning": {
                "AWS S3": "Explicitly mentioned for CSV storage",
                "AWS Glue": "Explicitly mentioned for ETL processing",
                "Amazon RDS": "Explicitly mentioned for data storage",
                "AWS Lambda": "Explicitly mentioned for triggers",
                "Amazon QuickSight": "Explicitly mentioned for reporting",
                "Amazon SES": "Explicitly mentioned for notifications",
            },
            "ecosystem_consistency": "AWS",
            "confidence_score": 0.95,
        }

        tech_stack_generator.llm_provider.generate_response = Mock(
            return_value=json.dumps(mock_response)
        )

        # Generate tech stack
        result = tech_stack_generator.generate_tech_stack(requirements)

        # Verify all explicit technologies are included
        generated_stack = result.get("tech_stack", [])
        explicit_techs = requirements["explicit_technologies"]

        for tech in explicit_techs:
            assert tech in generated_stack, f"Missing explicit technology: {tech}"

        # Verify ecosystem consistency
        aws_techs = [
            tech for tech in generated_stack if tech.startswith(("AWS", "Amazon"))
        ]
        assert len(aws_techs) >= 6, "Should include all AWS technologies"

        # Verify confidence score
        confidence = result.get("confidence_score", 0)
        assert confidence >= 0.9, f"Low confidence score: {confidence}"

    @pytest.mark.asyncio
    async def test_end_to_end_api_integration_scenario(self, tech_stack_generator):
        """Complete end-to-end test for API integration scenario."""
        requirements = {
            "description": """
            Integrate with Stripe payment API and Salesforce CRM API.
            Use FastAPI for the backend, Redis for caching, and PostgreSQL for data storage.
            Deploy on Google Cloud Platform using Cloud Run and Cloud SQL.
            """,
            "domain": "api_integration",
            "integrations": ["Stripe API", "Salesforce API"],
            "explicit_technologies": [
                "FastAPI",
                "Redis",
                "PostgreSQL",
                "Google Cloud Run",
                "Google Cloud SQL",
            ],
            "cloud_provider": "GCP",
        }

        mock_response = {
            "tech_stack": [
                "FastAPI",
                "Redis",
                "PostgreSQL",
                "Google Cloud Run",
                "Google Cloud SQL",
                "Stripe API",
                "Salesforce API",
                "Python",
            ],
            "reasoning": {
                "FastAPI": "Explicitly mentioned for backend API",
                "Redis": "Explicitly mentioned for caching",
                "PostgreSQL": "Explicitly mentioned for data storage",
                "Google Cloud Run": "Explicitly mentioned for deployment",
                "Google Cloud SQL": "Explicitly mentioned for managed database",
            },
            "ecosystem_consistency": "GCP",
            "confidence_score": 0.88,
        }

        tech_stack_generator.llm_provider.generate_response = Mock(
            return_value=json.dumps(mock_response)
        )

        result = tech_stack_generator.generate_tech_stack(requirements)

        # Verify explicit technologies
        generated_stack = result.get("tech_stack", [])
        explicit_techs = requirements["explicit_technologies"]

        inclusion_count = sum(1 for tech in explicit_techs if tech in generated_stack)
        inclusion_rate = inclusion_count / len(explicit_techs)
        assert inclusion_rate >= 0.7, f"Low inclusion rate: {inclusion_rate:.2%}"

        # Verify GCP ecosystem consistency
        gcp_techs = [
            tech for tech in generated_stack if "Google Cloud" in tech or "GCP" in tech
        ]
        assert len(gcp_techs) >= 2, "Should include GCP technologies"

    # Performance Benchmarks

    @pytest.mark.performance
    def test_large_requirement_processing_performance(self, tech_stack_generator):
        """Benchmark performance for large requirement processing."""
        # Create a large, complex requirement
        large_requirements = {
            "description": " ".join(
                [
                    "Build a comprehensive enterprise system with microservices architecture.",
                    "Use AWS EKS for container orchestration, Amazon RDS for databases,",
                    "AWS Lambda for serverless functions, Amazon S3 for storage,",
                    "Amazon CloudFront for CDN, AWS API Gateway for API management,",
                    "Amazon ElastiCache for caching, Amazon SQS for messaging,",
                    "AWS Cognito for authentication, Amazon CloudWatch for monitoring,",
                    "AWS X-Ray for tracing, Amazon Kinesis for streaming data,",
                    "AWS Glue for ETL, Amazon Redshift for data warehousing,",
                    "Amazon QuickSight for analytics, AWS Step Functions for workflows.",
                ]
            ),
            "domain": "enterprise_system",
            "explicit_technologies": [
                "AWS EKS",
                "Amazon RDS",
                "AWS Lambda",
                "Amazon S3",
                "Amazon CloudFront",
                "AWS API Gateway",
                "Amazon ElastiCache",
                "Amazon SQS",
                "AWS Cognito",
                "Amazon CloudWatch",
                "AWS X-Ray",
                "Amazon Kinesis",
                "AWS Glue",
                "Amazon Redshift",
                "Amazon QuickSight",
                "AWS Step Functions",
            ],
            "integrations": ["microservices", "databases", "apis", "monitoring"],
            "complexity": "high",
            "scale": "enterprise",
        }

        # Mock response with all technologies
        mock_response = {
            "tech_stack": large_requirements["explicit_technologies"]
            + ["Python", "Docker", "Kubernetes"],
            "reasoning": {
                tech: f"Explicitly mentioned for {tech}"
                for tech in large_requirements["explicit_technologies"]
            },
            "ecosystem_consistency": "AWS",
            "confidence_score": 0.92,
        }

        tech_stack_generator.llm_provider.generate_response = Mock(
            return_value=json.dumps(mock_response)
        )

        # Measure processing time
        start_time = time.time()
        result = tech_stack_generator.generate_tech_stack(large_requirements)
        processing_time = time.time() - start_time

        # Performance assertions
        assert (
            processing_time < 5.0
        ), f"Processing took too long: {processing_time:.2f}s"
        assert result is not None, "Should return a result"
        assert (
            len(result.get("tech_stack", [])) >= 15
        ), "Should handle large tech stacks"

        # Verify all explicit technologies are processed
        generated_stack = result.get("tech_stack", [])
        explicit_count = len(large_requirements["explicit_technologies"])
        included_count = sum(
            1
            for tech in large_requirements["explicit_technologies"]
            if tech in generated_stack
        )
        inclusion_rate = included_count / explicit_count
        assert (
            inclusion_rate >= 0.8
        ), f"Low inclusion rate for large requirements: {inclusion_rate:.2%}"

    @pytest.mark.performance
    def test_concurrent_processing_performance(self, tech_stack_generator):
        """Test performance under concurrent processing load."""
        import concurrent.futures

        # Create multiple different requirements
        requirements_list = [
            {
                "description": f"Build system {i} with AWS services",
                "explicit_technologies": ["AWS Lambda", "Amazon S3", "Amazon RDS"],
                "domain": f"system_{i}",
            }
            for i in range(10)
        ]

        # Mock responses
        def mock_generate_response(prompt):
            return json.dumps(
                {
                    "tech_stack": ["AWS Lambda", "Amazon S3", "Amazon RDS", "Python"],
                    "reasoning": {"AWS Lambda": "Serverless functions"},
                    "confidence_score": 0.85,
                }
            )

        tech_stack_generator.llm_provider.generate_response = Mock(
            side_effect=mock_generate_response
        )

        # Process concurrently
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(tech_stack_generator.generate_tech_stack, req)
                for req in requirements_list
            ]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        processing_time = time.time() - start_time

        # Performance assertions
        assert (
            processing_time < 10.0
        ), f"Concurrent processing took too long: {processing_time:.2f}s"
        assert len(results) == 10, "Should process all requests"

        # Verify all results are valid
        for result in results:
            assert result is not None, "All results should be valid"
            assert "tech_stack" in result, "All results should have tech_stack"

    # Accuracy Metrics and Validation

    def test_accuracy_metrics_collection(self, tech_stack_generator):
        """Test collection and validation of accuracy metrics."""
        test_cases = [
            {
                "requirements": {
                    "description": "Use AWS S3 and Lambda for file processing",
                    "explicit_technologies": ["AWS S3", "AWS Lambda"],
                },
                "expected_inclusions": ["AWS S3", "AWS Lambda"],
                "expected_exclusions": ["Azure Blob Storage", "Google Cloud Functions"],
            },
            {
                "requirements": {
                    "description": "Build with React and Node.js for web application",
                    "explicit_technologies": ["React", "Node.js"],
                },
                "expected_inclusions": ["React", "Node.js"],
                "expected_exclusions": ["Vue.js", "Django"],
            },
            {
                "requirements": {
                    "description": "Use PostgreSQL and Redis for data layer",
                    "explicit_technologies": ["PostgreSQL", "Redis"],
                },
                "expected_inclusions": ["PostgreSQL", "Redis"],
                "expected_exclusions": ["MySQL", "MongoDB"],
            },
        ]

        accuracy_metrics = {
            "total_cases": 0,
            "correct_inclusions": 0,
            "incorrect_inclusions": 0,
            "correct_exclusions": 0,
            "incorrect_exclusions": 0,
        }

        for case in test_cases:
            # Mock appropriate response
            mock_response = {
                "tech_stack": case["expected_inclusions"] + ["Python", "Docker"],
                "reasoning": {
                    tech: "Explicitly mentioned" for tech in case["expected_inclusions"]
                },
                "confidence_score": 0.9,
            }

            tech_stack_generator.llm_provider.generate_response = Mock(
                return_value=json.dumps(mock_response)
            )

            result = tech_stack_generator.generate_tech_stack(case["requirements"])
            generated_stack = result.get("tech_stack", [])

            accuracy_metrics["total_cases"] += 1

            # Check inclusions
            for tech in case["expected_inclusions"]:
                if tech in generated_stack:
                    accuracy_metrics["correct_inclusions"] += 1
                else:
                    accuracy_metrics["incorrect_inclusions"] += 1

            # Check exclusions
            for tech in case["expected_exclusions"]:
                if tech not in generated_stack:
                    accuracy_metrics["correct_exclusions"] += 1
                else:
                    accuracy_metrics["incorrect_exclusions"] += 1

        # Calculate accuracy rates
        total_inclusions = (
            accuracy_metrics["correct_inclusions"]
            + accuracy_metrics["incorrect_inclusions"]
        )
        total_exclusions = (
            accuracy_metrics["correct_exclusions"]
            + accuracy_metrics["incorrect_exclusions"]
        )

        inclusion_accuracy = (
            accuracy_metrics["correct_inclusions"] / total_inclusions
            if total_inclusions > 0
            else 0
        )
        exclusion_accuracy = (
            accuracy_metrics["correct_exclusions"] / total_exclusions
            if total_exclusions > 0
            else 0
        )

        # Accuracy assertions
        assert (
            inclusion_accuracy >= 0.9
        ), f"Low inclusion accuracy: {inclusion_accuracy:.2%}"
        assert (
            exclusion_accuracy >= 0.9
        ), f"Low exclusion accuracy: {exclusion_accuracy:.2%}"

        # Overall accuracy should be high
        overall_accuracy = (
            accuracy_metrics["correct_inclusions"]
            + accuracy_metrics["correct_exclusions"]
        ) / (total_inclusions + total_exclusions)
        assert overall_accuracy >= 0.9, f"Low overall accuracy: {overall_accuracy:.2%}"

    # Test Data Sets for Various Contexts

    @pytest.fixture
    def technology_context_test_data(self):
        """Test data sets for various technology contexts and domains."""
        return {
            "aws_ecosystem": {
                "requirements": {
                    "description": "Build serverless application with AWS Lambda, API Gateway, and DynamoDB",
                    "explicit_technologies": [
                        "AWS Lambda",
                        "AWS API Gateway",
                        "DynamoDB",
                    ],
                    "cloud_provider": "AWS",
                },
                "expected_ecosystem": "AWS",
                "expected_confidence": 0.9,
            },
            "azure_ecosystem": {
                "requirements": {
                    "description": "Deploy using Azure Functions, Azure SQL, and Azure Storage",
                    "explicit_technologies": [
                        "Azure Functions",
                        "Azure SQL",
                        "Azure Storage",
                    ],
                    "cloud_provider": "Azure",
                },
                "expected_ecosystem": "Azure",
                "expected_confidence": 0.9,
            },
            "gcp_ecosystem": {
                "requirements": {
                    "description": "Use Google Cloud Run, Cloud SQL, and Cloud Storage",
                    "explicit_technologies": [
                        "Google Cloud Run",
                        "Google Cloud SQL",
                        "Google Cloud Storage",
                    ],
                    "cloud_provider": "GCP",
                },
                "expected_ecosystem": "GCP",
                "expected_confidence": 0.9,
            },
            "open_source_stack": {
                "requirements": {
                    "description": "Build with PostgreSQL, Redis, FastAPI, and React",
                    "explicit_technologies": [
                        "PostgreSQL",
                        "Redis",
                        "FastAPI",
                        "React",
                    ],
                    "ecosystem": "open_source",
                },
                "expected_ecosystem": "open_source",
                "expected_confidence": 0.85,
            },
            "mixed_ecosystem": {
                "requirements": {
                    "description": "Use AWS S3 for storage but PostgreSQL for database and React for frontend",
                    "explicit_technologies": ["AWS S3", "PostgreSQL", "React"],
                    "mixed": True,
                },
                "expected_ecosystem": "mixed",
                "expected_confidence": 0.7,
            },
        }

    def test_various_technology_contexts(
        self, tech_stack_generator, technology_context_test_data
    ):
        """Test tech stack generation across various technology contexts."""
        for context_name, test_data in technology_context_test_data.items():
            requirements = test_data["requirements"]

            # Mock appropriate response based on context
            mock_response = {
                "tech_stack": requirements["explicit_technologies"] + ["Python"],
                "reasoning": {
                    tech: "Explicitly mentioned"
                    for tech in requirements["explicit_technologies"]
                },
                "ecosystem_consistency": test_data["expected_ecosystem"],
                "confidence_score": test_data["expected_confidence"],
            }

            tech_stack_generator.llm_provider.generate_response = Mock(
                return_value=json.dumps(mock_response)
            )

            result = tech_stack_generator.generate_tech_stack(requirements)

            # Verify context-specific expectations
            generated_stack = result.get("tech_stack", [])

            # All explicit technologies should be included
            for tech in requirements["explicit_technologies"]:
                assert (
                    tech in generated_stack
                ), f"Missing {tech} in {context_name} context"

            # Confidence should meet expectations
            confidence = result.get("confidence_score", 0)
            expected_confidence = test_data["expected_confidence"]
            assert (
                confidence >= expected_confidence * 0.9
            ), f"Low confidence in {context_name}: {confidence}"

    # Catalog Consistency and Completeness Tests

    def test_catalog_consistency_validation(self, catalog_manager):
        """Test automated catalog consistency checking."""
        # Test data with potential inconsistencies
        test_catalog_entries = [
            {
                "name": "AWS Lambda",
                "category": "serverless",
                "ecosystem": "AWS",
                "integrates_with": ["AWS API Gateway", "Amazon S3", "DynamoDB"],
                "aliases": ["Lambda"],
            },
            {
                "name": "AWS API Gateway",
                "category": "api_management",
                "ecosystem": "AWS",
                "integrates_with": ["AWS Lambda", "Amazon Cognito"],
                "aliases": ["API Gateway"],
            },
            {
                "name": "DynamoDB",
                "category": "database",
                "ecosystem": "AWS",
                "integrates_with": ["AWS Lambda", "AWS API Gateway"],
                "aliases": ["Amazon DynamoDB"],
            },
        ]

        # Mock catalog with test entries
        catalog_manager.catalog_entries = {
            entry["name"]: entry for entry in test_catalog_entries
        }

        # Run consistency validation
        validation_result = catalog_manager.validate_catalog_consistency()

        # Should pass basic consistency checks
        assert validation_result.is_valid, "Catalog should be consistent"
        assert (
            len(validation_result.errors) == 0
        ), f"Unexpected errors: {validation_result.errors}"

        # Test with inconsistent data
        inconsistent_entry = {
            "name": "Inconsistent Service",
            "category": "unknown",
            "ecosystem": "AWS",
            "integrates_with": ["NonExistent Service"],  # This should cause an error
            "aliases": [],
        }

        catalog_manager.catalog_entries["Inconsistent Service"] = inconsistent_entry

        validation_result = catalog_manager.validate_catalog_consistency()
        assert not validation_result.is_valid, "Should detect inconsistency"
        assert len(validation_result.errors) > 0, "Should report errors"

    def test_catalog_completeness_validation(self, catalog_manager):
        """Test catalog completeness for common technology stacks."""
        # Common technology combinations that should be in catalog
        common_stacks = [
            ["Python", "FastAPI", "PostgreSQL", "Redis"],
            ["Node.js", "Express", "MongoDB", "React"],
            ["Java", "Spring Boot", "MySQL", "Angular"],
            ["AWS Lambda", "AWS API Gateway", "DynamoDB"],
            ["Azure Functions", "Azure SQL", "Azure Storage"],
            ["Google Cloud Run", "Cloud SQL", "Cloud Storage"],
        ]

        completeness_results = []

        for stack in common_stacks:
            missing_technologies = []
            for tech in stack:
                if not catalog_manager.lookup_technology(tech):
                    missing_technologies.append(tech)

            completeness_rate = (len(stack) - len(missing_technologies)) / len(stack)
            completeness_results.append(
                {
                    "stack": stack,
                    "completeness_rate": completeness_rate,
                    "missing": missing_technologies,
                }
            )

        # Overall completeness should be high
        overall_completeness = sum(
            result["completeness_rate"] for result in completeness_results
        ) / len(completeness_results)
        assert (
            overall_completeness >= 0.8
        ), f"Low catalog completeness: {overall_completeness:.2%}"

        # Report missing technologies for improvement
        all_missing = set()
        for result in completeness_results:
            all_missing.update(result["missing"])

        if all_missing:
            print(f"Missing technologies in catalog: {sorted(all_missing)}")

    # Integration with Existing System Tests

    def test_integration_with_pattern_creation(self, tech_stack_generator):
        """Test integration with existing pattern creation workflow."""
        # Simulate pattern creation requirements
        pattern_requirements = {
            "description": "Create agentic pattern for automated code review using GitHub API and OpenAI",
            "pattern_type": "agentic",
            "autonomy_level": 0.95,
            "explicit_technologies": ["GitHub API", "OpenAI API", "Python", "FastAPI"],
            "domain": "code_review",
        }

        mock_response = {
            "tech_stack": [
                "GitHub API",
                "OpenAI API",
                "Python",
                "FastAPI",
                "Redis",
                "PostgreSQL",
            ],
            "reasoning": {
                "GitHub API": "Explicitly mentioned for repository access",
                "OpenAI API": "Explicitly mentioned for AI analysis",
                "Python": "Explicitly mentioned as primary language",
                "FastAPI": "Explicitly mentioned for API framework",
            },
            "agentic_suitability": 0.95,
            "confidence_score": 0.92,
        }

        tech_stack_generator.llm_provider.generate_response = Mock(
            return_value=json.dumps(mock_response)
        )

        result = tech_stack_generator.generate_tech_stack(pattern_requirements)

        # Verify integration-specific requirements
        assert (
            result.get("agentic_suitability", 0) >= 0.9
        ), "Should support high autonomy"
        assert "GitHub API" in result.get("tech_stack", []), "Should include GitHub API"
        assert "OpenAI API" in result.get("tech_stack", []), "Should include OpenAI API"

        # Verify pattern-specific metadata
        confidence = result.get("confidence_score", 0)
        assert (
            confidence >= 0.9
        ), f"Should have high confidence for agentic patterns: {confidence}"

    def test_backward_compatibility(self, tech_stack_generator):
        """Test backward compatibility with existing system interfaces."""
        # Test with old-style requirements format
        legacy_requirements = {
            "description": "Build web application with database",
            "tech_preferences": ["Python", "PostgreSQL"],  # Old format
            "deployment": "cloud",
        }

        # Should still work with legacy format
        mock_response = {
            "tech_stack": ["Python", "PostgreSQL", "FastAPI", "Docker"],
            "reasoning": {"Python": "Preferred technology"},
            "confidence_score": 0.8,
        }

        tech_stack_generator.llm_provider.generate_response = Mock(
            return_value=json.dumps(mock_response)
        )

        result = tech_stack_generator.generate_tech_stack(legacy_requirements)

        # Should handle legacy format gracefully
        assert result is not None, "Should handle legacy requirements"
        assert "tech_stack" in result, "Should return tech stack"
        assert "Python" in result.get("tech_stack", []), "Should respect preferences"


class TestTechStackGenerationMetrics:
    """Test suite for collecting and validating tech stack generation metrics."""

    def test_explicit_technology_inclusion_rate(self, tech_stack_generator):
        """Test and measure explicit technology inclusion rates."""
        test_cases = [
            {
                "name": "AWS Services",
                "requirements": {
                    "description": "Use AWS Lambda, S3, and RDS for backend",
                    "explicit_technologies": ["AWS Lambda", "Amazon S3", "Amazon RDS"],
                },
                "expected_inclusions": ["AWS Lambda", "Amazon S3", "Amazon RDS"],
            },
            {
                "name": "Web Stack",
                "requirements": {
                    "description": "Build with React, Node.js, and MongoDB",
                    "explicit_technologies": ["React", "Node.js", "MongoDB"],
                },
                "expected_inclusions": ["React", "Node.js", "MongoDB"],
            },
            {
                "name": "Data Stack",
                "requirements": {
                    "description": "Process data with Python, Pandas, and PostgreSQL",
                    "explicit_technologies": ["Python", "Pandas", "PostgreSQL"],
                },
                "expected_inclusions": ["Python", "Pandas", "PostgreSQL"],
            },
        ]

        inclusion_rates = []

        for case in test_cases:
            mock_response = {
                "tech_stack": case["expected_inclusions"] + ["Docker", "Kubernetes"],
                "reasoning": {
                    tech: "Explicitly mentioned" for tech in case["expected_inclusions"]
                },
                "confidence_score": 0.9,
            }

            tech_stack_generator.llm_provider.generate_response = Mock(
                return_value=json.dumps(mock_response)
            )

            result = tech_stack_generator.generate_tech_stack(case["requirements"])
            generated_stack = result.get("tech_stack", [])

            # Calculate inclusion rate
            expected = case["expected_inclusions"]
            included = sum(1 for tech in expected if tech in generated_stack)
            inclusion_rate = included / len(expected) if expected else 0

            inclusion_rates.append(
                {
                    "case": case["name"],
                    "rate": inclusion_rate,
                    "expected": len(expected),
                    "included": included,
                }
            )

        # Overall inclusion rate should be high
        overall_rate = sum(rate["rate"] for rate in inclusion_rates) / len(
            inclusion_rates
        )
        assert overall_rate >= 0.9, f"Low overall inclusion rate: {overall_rate:.2%}"

        # Individual cases should also be high
        for rate_info in inclusion_rates:
            assert (
                rate_info["rate"] >= 0.8
            ), f"Low inclusion rate for {rate_info['case']}: {rate_info['rate']:.2%}"

    def test_ecosystem_consistency_metrics(self, tech_stack_generator):
        """Test and measure ecosystem consistency in generated tech stacks."""
        ecosystem_test_cases = [
            {
                "name": "Pure AWS",
                "requirements": {
                    "description": "AWS-only solution with Lambda, S3, RDS, and API Gateway",
                    "explicit_technologies": [
                        "AWS Lambda",
                        "Amazon S3",
                        "Amazon RDS",
                        "AWS API Gateway",
                    ],
                    "cloud_provider": "AWS",
                },
                "expected_ecosystem": "AWS",
            },
            {
                "name": "Pure Azure",
                "requirements": {
                    "description": "Azure solution with Functions, Storage, and SQL",
                    "explicit_technologies": [
                        "Azure Functions",
                        "Azure Storage",
                        "Azure SQL",
                    ],
                    "cloud_provider": "Azure",
                },
                "expected_ecosystem": "Azure",
            },
            {
                "name": "Open Source",
                "requirements": {
                    "description": "Open source stack with PostgreSQL, Redis, and FastAPI",
                    "explicit_technologies": ["PostgreSQL", "Redis", "FastAPI"],
                    "ecosystem": "open_source",
                },
                "expected_ecosystem": "open_source",
            },
        ]

        consistency_scores = []

        for case in ecosystem_test_cases:
            mock_response = {
                "tech_stack": case["requirements"]["explicit_technologies"]
                + ["Python", "Docker"],
                "ecosystem_consistency": case["expected_ecosystem"],
                "confidence_score": 0.9,
            }

            tech_stack_generator.llm_provider.generate_response = Mock(
                return_value=json.dumps(mock_response)
            )

            result = tech_stack_generator.generate_tech_stack(case["requirements"])

            # Check ecosystem consistency
            ecosystem = result.get("ecosystem_consistency", "")
            expected_ecosystem = case["expected_ecosystem"]

            consistency_score = 1.0 if ecosystem == expected_ecosystem else 0.0
            consistency_scores.append(
                {
                    "case": case["name"],
                    "score": consistency_score,
                    "expected": expected_ecosystem,
                    "actual": ecosystem,
                }
            )

        # Overall consistency should be high
        overall_consistency = sum(score["score"] for score in consistency_scores) / len(
            consistency_scores
        )
        assert (
            overall_consistency >= 0.8
        ), f"Low ecosystem consistency: {overall_consistency:.2%}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
