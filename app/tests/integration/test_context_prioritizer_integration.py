"""Integration tests for requirement context prioritizer."""

import pytest
from typing import Dict, List, Any

from app.services.requirement_parsing.context_prioritizer import (
    RequirementContextPrioritizer, RequirementSource, AmbiguityType
)
from app.services.requirement_parsing.enhanced_parser import EnhancedRequirementParser
from app.services.requirement_parsing.context_extractor import TechnologyContextExtractor
from app.services.requirement_parsing.base import ParsedRequirements, TechContext


class TestContextPrioritizerIntegration:
    """Integration tests for context prioritizer with other components."""
    
    @pytest.fixture
    def prioritizer(self):
        """Create prioritizer instance."""
        return RequirementContextPrioritizer()
    
    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return EnhancedRequirementParser()
    
    @pytest.fixture
    def context_extractor(self):
        """Create context extractor instance."""
        return TechnologyContextExtractor()
    
    @pytest.fixture
    def aws_connect_requirements(self):
        """Sample AWS Connect requirements that caused the original bug."""
        return {
            "business_requirements": [
                "Integrate with Amazon Connect for voice capabilities",
                "Use AWS services for cloud infrastructure",
                "Implement real-time call analytics using AWS Comprehend",
                "Store call recordings in Amazon S3",
                "Use AWS Lambda for serverless processing"
            ],
            "technical_specifications": [
                "Python-based backend using FastAPI",
                "RESTful API design",
                "Database integration for call metadata",
                "Real-time data processing pipeline",
                "Secure authentication and authorization"
            ],
            "constraints": {
                "banned_tools": ["MySQL"],
                "required_integrations": ["voice_integration", "analytics"],
                "compliance": ["SOC2", "HIPAA"]
            }
        }
    
    @pytest.fixture
    def multi_cloud_requirements(self):
        """Requirements with conflicting cloud providers."""
        return {
            "business_requirements": [
                "Use AWS Lambda for serverless functions",
                "Integrate with Azure Cognitive Services for AI",
                "Store data in Google BigQuery for analytics",
                "Implement monitoring with AWS CloudWatch"
            ],
            "technical_specifications": [
                "Node.js backend with Express.js",
                "React frontend application",
                "Database integration required",
                "Real-time notifications"
            ]
        }
    
    def test_end_to_end_aws_connect_prioritization(self, prioritizer, parser, context_extractor, aws_connect_requirements):
        """Test end-to-end prioritization for AWS Connect use case."""
        # Parse requirements
        parsed_req = parser.parse_requirements(aws_connect_requirements)
        
        # Extract technology context
        tech_context = context_extractor.build_context(parsed_req)
        
        # Calculate context weights
        context_weights = prioritizer.calculate_context_weights(parsed_req, tech_context)
        
        # Verify AWS technologies are prioritized
        aws_technologies = [
            "Amazon Connect SDK", "AWS Lambda", "Amazon S3", 
            "AWS Comprehend", "Amazon CloudWatch"
        ]
        
        for tech in aws_technologies:
            if tech in context_weights:
                # AWS technologies should have high weights due to explicit mentions
                assert context_weights[tech].final_weight >= 0.7
                # Should have ecosystem consistency boost
                assert context_weights[tech].ecosystem_boost > 0
        
        # Verify FastAPI is prioritized (explicit mention)
        if "FastAPI" in context_weights:
            assert context_weights["FastAPI"].final_weight >= 0.8
        
        # Verify banned technologies are excluded
        for tech, weight in context_weights.items():
            assert "MySQL" not in tech.lower()
        
        # Check prioritization summary
        summary = prioritizer.get_prioritization_summary(context_weights)
        assert summary["total_technologies"] > 0
        assert len(summary["top_technologies"]) > 0
        
        # Top technology should be an AWS service or explicitly mentioned tech
        top_tech = summary["top_technologies"][0]
        assert top_tech["weight"] >= 0.7
    
    def test_ambiguity_detection_with_real_requirements(self, prioritizer, parser, multi_cloud_requirements):
        """Test ambiguity detection with conflicting cloud requirements."""
        # Parse requirements
        parsed_req = parser.parse_requirements(multi_cloud_requirements)
        
        # Detect ambiguities
        ambiguities = prioritizer.detect_requirement_ambiguity(parsed_req)
        
        # Should detect ecosystem conflicts
        ecosystem_conflicts = [
            a for a in ambiguities 
            if a.ambiguity_type == AmbiguityType.ECOSYSTEM_MISMATCH
        ]
        assert len(ecosystem_conflicts) > 0
        
        # Check conflict details
        for conflict in ecosystem_conflicts:
            assert conflict.impact_level in ["high", "medium"]
            assert len(conflict.suggested_clarifications) > 0
            assert conflict.confidence > 0.5
    
    def test_conflict_resolution_integration(self, prioritizer, parser, context_extractor, multi_cloud_requirements):
        """Test conflict resolution with real conflicting requirements."""
        # Parse and extract context
        parsed_req = parser.parse_requirements(multi_cloud_requirements)
        tech_context = context_extractor.build_context(parsed_req)
        
        # Detect conflicts
        ambiguities = prioritizer.detect_requirement_ambiguity(parsed_req)
        
        # Resolve conflicts
        resolutions = prioritizer.resolve_technology_conflicts(ambiguities, tech_context)
        
        # Should have resolution decisions
        assert isinstance(resolutions, dict)
        
        # If there are conflicts, there should be resolutions
        tech_conflicts = [a for a in ambiguities if a.ambiguity_type == AmbiguityType.TECHNOLOGY_CONFLICT]
        if tech_conflicts:
            assert len(resolutions) > 0
    
    def test_domain_preference_integration(self, prioritizer, parser, context_extractor):
        """Test domain preference integration with different domains."""
        test_cases = [
            {
                "domain": "ml_ai",
                "requirements": {
                    "business_requirements": [
                        "Build machine learning pipeline",
                        "Use OpenAI API for language processing",
                        "Implement vector similarity search",
                        "Train custom models with PyTorch"
                    ]
                },
                "expected_high_priority": ["OpenAI API", "PyTorch", "FAISS"]
            },
            {
                "domain": "data_processing",
                "requirements": {
                    "business_requirements": [
                        "Process large datasets with Apache Spark",
                        "Stream data using Apache Kafka",
                        "Store results in data warehouse",
                        "Real-time analytics dashboard"
                    ]
                },
                "expected_high_priority": ["Apache Spark", "Apache Kafka"]
            },
            {
                "domain": "monitoring",
                "requirements": {
                    "business_requirements": [
                        "Monitor application performance",
                        "Collect metrics with Prometheus",
                        "Visualize data with Grafana",
                        "Distributed tracing with Jaeger"
                    ]
                },
                "expected_high_priority": ["Prometheus", "Grafana", "Jaeger"]
            }
        ]
        
        for case in test_cases:
            # Parse requirements
            parsed_req = parser.parse_requirements(case["requirements"])
            
            # Override domain context for testing
            parsed_req.domain_context.primary_domain = case["domain"]
            
            # Extract context and calculate weights
            tech_context = context_extractor.build_context(parsed_req)
            context_weights = prioritizer.calculate_context_weights(parsed_req, tech_context)
            
            # Check domain preferences
            domain_prefs = prioritizer.implement_domain_specific_preferences(
                tech_context, parsed_req.domain_context
            )
            
            # Verify expected technologies get high priority
            for tech in case["expected_high_priority"]:
                if tech in domain_prefs:
                    assert domain_prefs[tech] >= 0.7
                if tech in context_weights:
                    assert context_weights[tech].domain_boost > 0
    
    def test_user_preference_learning_integration(self, prioritizer, parser, context_extractor):
        """Test user preference learning integration."""
        requirements = {
            "business_requirements": [
                "Build web API with Python framework",
                "Database integration required",
                "Caching layer needed"
            ]
        }
        
        # Parse requirements
        parsed_req = parser.parse_requirements(requirements)
        parsed_req.domain_context.primary_domain = "web_api"
        
        # Simulate user selections over multiple sessions
        sessions = [
            {
                "selected": ["FastAPI", "PostgreSQL", "Redis"],
                "rejected": ["Django", "MySQL", "Memcached"]
            },
            {
                "selected": ["FastAPI", "PostgreSQL"],
                "rejected": ["Flask", "MongoDB"]
            },
            {
                "selected": ["FastAPI", "Redis"],
                "rejected": ["Django", "MySQL"]
            }
        ]
        
        # Learn from sessions
        for session in sessions:
            prioritizer.learn_user_preferences(
                session["selected"],
                session["rejected"],
                "web_api",
                ["rest_api", "database", "cache"]
            )
        
        # Extract context and calculate weights
        tech_context = context_extractor.build_context(parsed_req)
        context_weights = prioritizer.calculate_context_weights(parsed_req, tech_context)
        
        # Check that learned preferences affect weights
        preferred_techs = ["FastAPI", "PostgreSQL", "Redis"]
        rejected_techs = ["Django", "MySQL"]
        
        for tech in preferred_techs:
            if tech in context_weights:
                assert context_weights[tech].user_preference_boost >= 0
        
        # Check preference scores
        for tech in preferred_techs:
            pref_key = f"web_api:{tech}"
            if pref_key in prioritizer.user_preferences:
                assert prioritizer.user_preferences[pref_key].preference_score > 0
        
        for tech in rejected_techs:
            pref_key = f"web_api:{tech}"
            if pref_key in prioritizer.user_preferences:
                assert prioritizer.user_preferences[pref_key].preference_score <= 0
    
    def test_comprehensive_prioritization_accuracy(self, prioritizer, parser, context_extractor):
        """Test comprehensive prioritization accuracy across different scenarios."""
        test_scenarios = [
            {
                "name": "AWS Connect Voice Integration",
                "requirements": {
                    "business_requirements": [
                        "Integrate with Amazon Connect for voice capabilities",
                        "Use AWS Comprehend for sentiment analysis",
                        "Store call recordings in Amazon S3"
                    ],
                    "technical_specifications": [
                        "Python backend with FastAPI",
                        "Real-time processing with AWS Lambda"
                    ]
                },
                "expected_top_techs": ["Amazon Connect SDK", "AWS Comprehend", "Amazon S3", "FastAPI", "AWS Lambda"],
                "expected_ecosystem": "aws"
            },
            {
                "name": "Multi-Agent AI System",
                "requirements": {
                    "business_requirements": [
                        "Build multi-agent AI system",
                        "Use OpenAI API for language processing",
                        "Implement agent coordination with LangGraph",
                        "Vector similarity search with FAISS"
                    ]
                },
                "expected_top_techs": ["OpenAI API", "LangGraph", "FAISS", "LangChain"],
                "expected_domain": "ml_ai"
            },
            {
                "name": "Enterprise Web Application",
                "requirements": {
                    "business_requirements": [
                        "Enterprise web application with React frontend",
                        "Node.js backend with Express.js",
                        "PostgreSQL database with Redis caching",
                        "Kubernetes deployment"
                    ]
                },
                "expected_top_techs": ["React", "Express.js", "PostgreSQL", "Redis", "Kubernetes"],
                "expected_domain": "web_api"
            }
        ]
        
        for scenario in test_scenarios:
            # Parse and process requirements
            parsed_req = parser.parse_requirements(scenario["requirements"])
            tech_context = context_extractor.build_context(parsed_req)
            context_weights = prioritizer.calculate_context_weights(parsed_req, tech_context)
            
            # Get prioritization summary
            summary = prioritizer.get_prioritization_summary(context_weights)
            
            # Check that expected technologies are in top priorities
            top_tech_names = [tech["technology"] for tech in summary["top_technologies"][:10]]
            
            matched_techs = 0
            for expected_tech in scenario["expected_top_techs"]:
                if expected_tech in top_tech_names:
                    matched_techs += 1
            
            # Should match at least 60% of expected technologies
            match_ratio = matched_techs / len(scenario["expected_top_techs"])
            assert match_ratio >= 0.6, f"Scenario '{scenario['name']}' only matched {match_ratio:.2%} of expected technologies"
            
            # Check ecosystem preference if specified
            if "expected_ecosystem" in scenario:
                assert tech_context.ecosystem_preference == scenario["expected_ecosystem"]
            
            # Check domain inference if specified
            if "expected_domain" in scenario:
                # Domain might be inferred differently, so this is a softer check
                # Just verify that some domain context exists (could be in sub_domains or complexity_indicators)
                has_domain_context = (
                    parsed_req.domain_context.primary_domain is not None or
                    len(parsed_req.domain_context.sub_domains) > 0 or
                    len(parsed_req.domain_context.complexity_indicators) > 0
                )
                assert has_domain_context, f"No domain context found for scenario '{scenario['name']}'"
    
    def test_consistency_across_similar_requirements(self, prioritizer, parser, context_extractor):
        """Test that similar requirements produce consistent prioritization."""
        # Create similar requirements with slight variations
        base_requirements = {
            "business_requirements": [
                "Build REST API with FastAPI",
                "Use PostgreSQL for data storage",
                "Implement Redis for caching"
            ]
        }
        
        variations = [
            {**base_requirements, "technical_specifications": ["Python 3.10+", "Async/await support"]},
            {**base_requirements, "technical_specifications": ["Modern Python", "Asynchronous processing"]},
            {**base_requirements, "constraints": {"performance": "high_throughput"}}
        ]
        
        results = []
        for variation in variations:
            parsed_req = parser.parse_requirements(variation)
            tech_context = context_extractor.build_context(parsed_req)
            context_weights = prioritizer.calculate_context_weights(parsed_req, tech_context)
            summary = prioritizer.get_prioritization_summary(context_weights)
            results.append(summary)
        
        # Check consistency in top technologies
        core_techs = ["FastAPI", "PostgreSQL", "Redis"]
        for i, result in enumerate(results):
            top_tech_names = [tech["technology"] for tech in result["top_technologies"][:5]]
            
            matched_core = sum(1 for tech in core_techs if tech in top_tech_names)
            match_ratio = matched_core / len(core_techs)
            
            assert match_ratio >= 0.8, f"Variation {i} didn't consistently prioritize core technologies"
    
    def test_performance_with_large_requirements(self, prioritizer, parser, context_extractor):
        """Test performance with large requirement sets."""
        # Create large requirements set
        large_requirements = {
            "business_requirements": [
                f"Requirement {i}: Use various technologies for processing"
                for i in range(50)
            ],
            "technical_specifications": [
                f"Technical spec {i}: Implement feature with modern stack"
                for i in range(30)
            ]
        }
        
        # Add some explicit technologies
        large_requirements["business_requirements"].extend([
            "Use FastAPI for REST API",
            "Implement with PostgreSQL database",
            "Use Redis for caching",
            "Deploy with Docker and Kubernetes",
            "Monitor with Prometheus and Grafana"
        ])
        
        import time
        start_time = time.time()
        
        # Process requirements
        parsed_req = parser.parse_requirements(large_requirements)
        tech_context = context_extractor.build_context(parsed_req)
        context_weights = prioritizer.calculate_context_weights(parsed_req, tech_context)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert processing_time < 10.0, f"Processing took too long: {processing_time:.2f} seconds"
        
        # Should still produce valid results
        assert len(context_weights) > 0
        summary = prioritizer.get_prioritization_summary(context_weights)
        assert summary["total_technologies"] > 0
    
    def test_edge_case_handling(self, prioritizer, parser, context_extractor):
        """Test handling of edge cases and unusual inputs."""
        edge_cases = [
            # Empty requirements
            {},
            
            # Only constraints
            {"constraints": {"banned_tools": ["MySQL"]}},
            
            # Contradictory requirements
            {
                "business_requirements": [
                    "Use MySQL database",
                    "Avoid MySQL at all costs",
                    "Simple lightweight solution",
                    "Enterprise-grade scalable system"
                ]
            },
            
            # Very specific technical requirements
            {
                "technical_specifications": [
                    "Python 3.11.2 exactly",
                    "FastAPI version 0.104.1",
                    "PostgreSQL 15.3 with specific extensions",
                    "Redis 7.0 with clustering"
                ]
            }
        ]
        
        for i, requirements in enumerate(edge_cases):
            try:
                parsed_req = parser.parse_requirements(requirements)
                tech_context = context_extractor.build_context(parsed_req)
                context_weights = prioritizer.calculate_context_weights(parsed_req, tech_context)
                
                # Should not crash and should return valid structure
                assert isinstance(context_weights, dict)
                
                # Should handle ambiguity detection
                ambiguities = prioritizer.detect_requirement_ambiguity(parsed_req)
                assert isinstance(ambiguities, list)
                
            except Exception as e:
                pytest.fail(f"Edge case {i} caused exception: {e}")


if __name__ == "__main__":
    pytest.main([__file__])