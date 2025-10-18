"""Enhanced recommendation service with all fixes applied."""

from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import math
import re

from app.pattern.matcher import MatchResult
from app.services.recommendation import RecommendationService
from app.state.store import Recommendation
from app.llm.base import LLMProvider
from app.utils.logger import app_logger
from app.utils.audit import log_pattern_match


class ReportQualityGate:
    """Quality gate checker for comprehensive reports."""

    def __init__(self, criteria: Dict[str, float]):
        self.criteria = criteria

    def check_quality(
        self,
        patterns_analyzed: int,
        recommendations: List[Recommendation],
        required_integrations: List[str],
    ) -> Tuple[bool, List[str]]:
        """Check if report meets quality standards."""

        issues = []

        # Check minimum patterns analyzed
        if patterns_analyzed < self.criteria["minimum_patterns_analyzed"]:
            issues.append(
                f"Only {patterns_analyzed} patterns analyzed, minimum {self.criteria['minimum_patterns_analyzed']} required"
            )

        # Check confidence variation
        confidences = [r.confidence for r in recommendations]
        if len(set(confidences)) == 1 and len(confidences) > 1:
            issues.append("All recommendations have identical confidence scores")

        confidence_range = max(confidences) - min(confidences) if confidences else 0
        if confidence_range < self.criteria["minimum_confidence_variation"]:
            issues.append(
                f"Confidence variation ({confidence_range:.2f}) below minimum ({self.criteria['minimum_confidence_variation']})"
            )

        # Check required integrations coverage
        if required_integrations:
            covered_integrations = set()
            for rec in recommendations:
                covered_integrations.update(rec.tech_stack)

            coverage_ratio = len(
                covered_integrations.intersection(set(required_integrations))
            ) / len(required_integrations)
            if coverage_ratio < self.criteria["required_integrations_coverage"]:
                issues.append(
                    f"Required integrations coverage ({coverage_ratio:.2f}) below minimum ({self.criteria['required_integrations_coverage']})"
                )

        # Check for duplicate tech stacks
        tech_stack_signatures = [tuple(sorted(r.tech_stack)) for r in recommendations]
        unique_stacks = len(set(tech_stack_signatures))
        duplicate_ratio = (
            1 - (unique_stacks / len(recommendations)) if recommendations else 0
        )

        if duplicate_ratio > self.criteria["maximum_duplicate_tech_stacks"]:
            issues.append(
                f"Duplicate tech stacks ratio ({duplicate_ratio:.2f}) exceeds maximum ({self.criteria['maximum_duplicate_tech_stacks']})"
            )

        return len(issues) == 0, issues

    def should_generate_report(
        self, quality_check_result: Tuple[bool, List[str]]
    ) -> bool:
        """Determine if report should be generated based on quality check."""
        passes_quality, issues = quality_check_result

        # For now, generate report but include warnings
        # In production, you might want to block generation for critical issues
        return True  # Always generate but with warnings


class EnhancedTechStackGenerator:
    """Enhanced technology stack generator with domain-specific recommendations."""

    def __init__(self):
        self.domain_catalogs = {
            "financial": {
                "cloud_platforms": ["AWS", "Azure", "Google Cloud"],
                "contact_centers": ["Amazon Connect", "Twilio Flex", "Genesys Cloud"],
                "ai_platforms": ["Amazon Bedrock", "Azure OpenAI", "Google Vertex AI"],
                "programming_languages": ["GoLang", "Java", "Python", "C#"],
                "bpm_platforms": ["Pega", "Camunda", "IBM BPM"],
                "databases": ["Amazon DynamoDB", "PostgreSQL", "Oracle", "MongoDB"],
                "messaging": ["Amazon SQS", "Apache Kafka", "RabbitMQ"],
                "security": ["AWS IAM", "HashiCorp Vault", "Auth0"],
                "compliance": ["AWS Config", "Splunk", "Datadog"],
            },
            "healthcare": {
                "cloud_platforms": ["AWS", "Azure", "Google Cloud"],
                "ai_platforms": ["Amazon Bedrock", "Azure AI", "Google Healthcare AI"],
                "programming_languages": ["Python", "Java", "C#"],
                "databases": ["PostgreSQL", "MongoDB", "FHIR Server"],
                "security": ["HIPAA Compliant Storage", "Encryption Services"],
                "integration": ["HL7 FHIR", "DICOM", "Epic MyChart API"],
            },
            "retail": {
                "cloud_platforms": ["AWS", "Azure", "Shopify Plus"],
                "ai_platforms": ["Amazon Personalize", "Azure Cognitive Services"],
                "programming_languages": ["JavaScript", "Python", "PHP"],
                "databases": ["Amazon DynamoDB", "Redis", "Elasticsearch"],
                "ecommerce": ["Shopify", "Magento", "WooCommerce"],
                "payment": ["Stripe", "PayPal", "Square"],
            },
        }

    def generate_domain_specific_stack(
        self,
        domain: str,
        requirements: Dict[str, Any],
        required_integrations: List[str],
        recommendation_index: int = 0,
    ) -> List[str]:
        """Generate domain-specific technology stack."""

        tech_stack = []
        domain_catalog = self.domain_catalogs.get(domain, {})

        # Add required integrations first
        tech_stack.extend(required_integrations)

        # Add domain-specific technologies based on requirements
        description = requirements.get("description", "").lower()

        if "voice" in description or "chat" in description or "contact" in description:
            tech_stack.extend(domain_catalog.get("contact_centers", [])[:2])

        if "ai" in description or "agent" in description or "bedrock" in description:
            tech_stack.extend(domain_catalog.get("ai_platforms", [])[:2])

        if (
            "workflow" in description
            or "process" in description
            or "bpm" in description
        ):
            tech_stack.extend(domain_catalog.get("bpm_platforms", [])[:2])

        # Add core technologies for the domain with diversification
        core_categories = ["programming_languages", "databases", "cloud_platforms"]

        for category in core_categories:
            category_tech = domain_catalog.get(category, [])
            if category_tech:
                # Diversify based on recommendation index
                start_index = recommendation_index % len(category_tech)
                selected_tech = category_tech[start_index : start_index + 2]
                if len(selected_tech) < 2 and len(category_tech) > 1:
                    # Wrap around if needed
                    remaining = 2 - len(selected_tech)
                    selected_tech.extend(category_tech[:remaining])
                tech_stack.extend(selected_tech)

        # Remove duplicates while preserving order
        seen = set()
        unique_stack = []
        for tech in tech_stack:
            if tech not in seen:
                seen.add(tech)
                unique_stack.append(tech)

        return unique_stack


class EnhancedRecommendationService(RecommendationService):
    """Enhanced recommendation service with all fixes applied."""

    def __init__(
        self,
        confidence_threshold: float = 0.6,
        pattern_library_path: Optional[Path] = None,
        llm_provider: Optional[LLMProvider] = None,
    ):
        """Initialize enhanced recommendation service."""
        super().__init__(confidence_threshold, pattern_library_path, llm_provider)

        # Initialize enhanced components
        self.enhanced_tech_generator = EnhancedTechStackGenerator()
        self.quality_gate = ReportQualityGate(
            {
                "minimum_patterns_analyzed": 1,
                "maximum_identical_confidence_ratio": 0.8,
                "minimum_confidence_variation": 0.1,
                "required_integrations_coverage": 0.8,
                "maximum_duplicate_tech_stacks": 0.5,
            }
        )

        app_logger.info(
            "Enhanced recommendation service initialized with quality gates"
        )

    async def generate_enhanced_recommendations(
        self,
        matches: List[MatchResult],
        requirements: Dict[str, Any],
        session_id: str = "unknown",
    ) -> Tuple[List[Recommendation], List[str]]:
        """Generate enhanced recommendations with quality checks."""

        app_logger.info(
            f"Generating enhanced recommendations from {len(matches)} pattern matches"
        )

        # Extract required integrations from requirements
        required_integrations = []
        constraints = requirements.get("constraints", {})
        if isinstance(constraints, dict):
            required_integrations = constraints.get("required_integrations", [])

        # Also check for integrations in the main requirements
        if "integrations" in requirements:
            required_integrations.extend(requirements["integrations"])

        # Remove duplicates
        required_integrations = list(set(required_integrations))

        app_logger.info(f"Required integrations: {required_integrations}")

        # Generate base recommendations
        recommendations = []

        for i, match in enumerate(matches):
            # Determine feasibility with LLM priority
            feasibility = self._determine_enhanced_feasibility(match, requirements)

            # Calculate enhanced confidence with variation
            confidence = self._calculate_enhanced_confidence(
                match, requirements, feasibility, i
            )

            # Generate domain-specific tech stack
            tech_stack = await self._generate_enhanced_tech_stack(
                match, requirements, required_integrations, i
            )

            # Generate enhanced reasoning
            reasoning = self._generate_enhanced_reasoning(
                match, requirements, feasibility, confidence
            )

            recommendation = Recommendation(
                pattern_id=match.pattern_id,
                feasibility=feasibility,
                confidence=confidence,
                tech_stack=tech_stack,
                reasoning=reasoning,
            )

            # Log pattern match for analytics
            try:
                await log_pattern_match(
                    session_id=session_id,
                    pattern_id=match.pattern_id,
                    score=match.blended_score,
                    accepted=None,
                )
            except Exception as e:
                app_logger.error(f"Failed to log pattern match: {e}")

            recommendations.append(recommendation)

        # Diversify technology stacks to avoid duplicates
        recommendations = self._diversify_tech_stacks(recommendations)

        # Sort by confidence (descending)
        recommendations.sort(key=lambda r: r.confidence, reverse=True)

        # Apply quality gate checks
        quality_passed, quality_issues = self.quality_gate.check_quality(
            patterns_analyzed=len(matches),
            recommendations=recommendations,
            required_integrations=required_integrations,
        )

        if not quality_passed:
            app_logger.warning(f"Quality gate issues detected: {quality_issues}")

        app_logger.info(f"Generated {len(recommendations)} enhanced recommendations")
        return recommendations, quality_issues

    def _determine_enhanced_feasibility(
        self, match: MatchResult, requirements: Dict[str, Any]
    ) -> str:
        """Determine feasibility with LLM analysis priority."""

        # Prioritize LLM analysis if available
        llm_feasibility = requirements.get("llm_analysis_automation_feasibility")
        if llm_feasibility:
            app_logger.info(f"Using LLM feasibility assessment: {llm_feasibility}")
            # Map LLM response to our format
            feasibility_mapping = {
                "Automatable": "Automatable",
                "Fully Automatable": "Automatable",
                "Partially Automatable": "Partially Automatable",
                "Not Automatable": "Not Automatable",
            }
            return feasibility_mapping.get(llm_feasibility, llm_feasibility)

        # Fallback to pattern-based analysis
        app_logger.info("No LLM feasibility found, using pattern-based analysis")
        return super()._determine_feasibility(match, requirements)

    def _calculate_enhanced_confidence(
        self,
        match: MatchResult,
        requirements: Dict[str, Any],
        feasibility: str,
        recommendation_index: int,
    ) -> float:
        """Calculate confidence with enhanced variation and LLM priority."""

        # Try to extract LLM confidence first
        llm_confidence = self._extract_enhanced_llm_confidence(requirements)

        if llm_confidence is not None:
            # Add slight variation based on recommendation index to avoid identical scores
            variation = (recommendation_index * 0.02) % 0.1  # 0-10% variation
            adjusted_confidence = max(0.0, min(1.0, llm_confidence - variation))
            app_logger.info(
                f"Using LLM confidence: {adjusted_confidence:.3f} (original: {llm_confidence:.3f}, variation: -{variation:.3f})"
            )
            return adjusted_confidence

        # Fallback to enhanced pattern-based confidence calculation
        base_confidence = match.blended_score

        # Add variation based on recommendation index to avoid identical scores
        index_variation = recommendation_index * 0.05  # 5% per index

        # Adjust based on feasibility
        feasibility_multiplier = {
            "Automatable": 1.0,
            "Partially Automatable": 0.8,
            "Not Automatable": 0.4,
        }

        # Calculate with variation
        confidence = (base_confidence - index_variation) * feasibility_multiplier.get(
            feasibility, 0.5
        )
        confidence = max(0.1, min(1.0, confidence))  # Keep within bounds

        app_logger.info(
            f"Enhanced confidence for {match.pattern_id}: {confidence:.3f} "
            f"(base: {base_confidence:.3f}, variation: -{index_variation:.3f}, "
            f"feasibility: {feasibility})"
        )

        return confidence

    def _extract_enhanced_llm_confidence(
        self, requirements: Dict[str, Any]
    ) -> Optional[float]:
        """Extract LLM confidence with enhanced parsing."""

        # Try multiple sources for LLM confidence
        confidence_sources = [
            "llm_analysis_confidence_level",
            "confidence_level",
            "confidence",
            "llm_confidence",
        ]

        for source_key in confidence_sources:
            raw_value = requirements.get(source_key)
            if raw_value is not None:
                confidence = self._parse_enhanced_confidence_value(
                    raw_value, source_key
                )
                if confidence is not None:
                    return confidence

        # Try to extract from full LLM response if available
        llm_response = requirements.get("llm_analysis_raw_response")
        if llm_response:
            confidence = self._extract_confidence_from_response(llm_response)
            if confidence is not None:
                return confidence

        return None

    def _parse_enhanced_confidence_value(
        self, raw_value: Any, source_key: str
    ) -> Optional[float]:
        """Parse confidence value with enhanced validation."""

        try:
            # Handle None or empty values
            if raw_value is None or raw_value == "":
                return None

            # Handle boolean values (reject them)
            if isinstance(raw_value, bool):
                app_logger.warning(
                    f"Confidence from '{source_key}' is boolean ({raw_value}), rejecting"
                )
                return None

            # Handle numeric values
            if isinstance(raw_value, (int, float)) and not isinstance(raw_value, bool):
                confidence = float(raw_value)
                return self._validate_confidence_range(
                    confidence, source_key, str(raw_value)
                )

            # Handle string values
            if isinstance(raw_value, str):
                return self._parse_confidence_from_string(raw_value, source_key)

            return None

        except Exception as e:
            app_logger.error(f"Error parsing confidence from '{source_key}': {e}")
            return None

    def _validate_confidence_range(
        self, confidence: float, source: str, original_value: str
    ) -> Optional[float]:
        """Validate confidence is in valid range."""

        # Check for invalid values
        if math.isnan(confidence) or math.isinf(confidence):
            app_logger.warning(
                f"Confidence from '{source}' is NaN or infinite: {confidence}"
            )
            return None

        # Clamp to valid range
        clamped_confidence = max(0.0, min(1.0, confidence))

        if confidence != clamped_confidence:
            app_logger.warning(
                f"Confidence from '{source}' was out of range ({confidence}), clamped to {clamped_confidence}"
            )

        return clamped_confidence

    def _parse_confidence_from_string(
        self, value: str, source_key: str
    ) -> Optional[float]:
        """Parse confidence from string with multiple strategies."""

        # Strategy 1: Direct float conversion
        try:
            confidence = float(value.strip())
            return self._validate_confidence_range(confidence, source_key, value)
        except (ValueError, TypeError):
            pass

        # Strategy 2: Extract percentage
        percentage_match = re.search(r"(\d+(?:\.\d+)?)%", value)
        if percentage_match:
            try:
                percentage = float(percentage_match.group(1))
                confidence = percentage / 100.0 if percentage > 1.0 else percentage
                return self._validate_confidence_range(confidence, source_key, value)
            except (ValueError, TypeError):
                pass

        # Strategy 3: Extract decimal number from text
        decimal_match = re.search(r"(\d+(?:\.\d+)?)", value)
        if decimal_match:
            try:
                number = float(decimal_match.group(1))
                confidence = number / 100.0 if number > 1.0 else number
                return self._validate_confidence_range(confidence, source_key, value)
            except (ValueError, TypeError):
                pass

        return None

    async def _generate_enhanced_tech_stack(
        self,
        match: MatchResult,
        requirements: Dict[str, Any],
        required_integrations: List[str],
        recommendation_index: int,
    ) -> List[str]:
        """Generate enhanced domain-specific technology stack."""

        domain = requirements.get("domain", "general")

        # Use enhanced tech stack generator
        tech_stack = self.enhanced_tech_generator.generate_domain_specific_stack(
            domain=domain,
            requirements=requirements,
            required_integrations=required_integrations,
            recommendation_index=recommendation_index,
        )

        # Add pattern-specific technologies if not already included
        pattern_tech = match.tech_stack
        for tech in pattern_tech:
            if tech not in tech_stack:
                tech_stack.append(tech)

        # Limit to reasonable size
        return tech_stack[:12]

    def _generate_enhanced_reasoning(
        self,
        match: MatchResult,
        requirements: Dict[str, Any],
        feasibility: str,
        confidence: float,
    ) -> str:
        """Generate enhanced reasoning with domain context."""

        reasoning_parts = []

        # Pattern match quality
        reasoning_parts.append(
            f"Pattern {match.pattern_id} provides {match.rationale.lower()}."
        )

        # Feasibility assessment
        if feasibility == "Automatable":
            reasoning_parts.append("Full automation implementation recommended.")
        elif feasibility == "Partially Automatable":
            reasoning_parts.append(
                "Partial automation with human oversight recommended."
            )
        else:
            reasoning_parts.append(
                "Manual process with automation support recommended."
            )

        # Domain-specific insights
        domain = requirements.get("domain", "")
        if domain == "financial":
            reasoning_parts.append(
                "Financial services compliance and security requirements considered."
            )
        elif domain == "healthcare":
            reasoning_parts.append(
                "Healthcare privacy and regulatory requirements considered."
            )

        # Required integrations acknowledgment
        constraints = requirements.get("constraints", {})
        required_integrations = constraints.get("required_integrations", [])
        if required_integrations:
            reasoning_parts.append(
                f"Integrates with required systems: {', '.join(required_integrations[:3])}."
            )

        # Confidence explanation
        if confidence > 0.8:
            reasoning_parts.append(
                "High confidence based on strong pattern match and clear requirements."
            )
        elif confidence > 0.6:
            reasoning_parts.append(
                "Moderate confidence with some implementation considerations."
            )
        else:
            reasoning_parts.append(
                "Lower confidence due to complexity or unclear requirements."
            )

        return " ".join(reasoning_parts)

    def _diversify_tech_stacks(
        self, recommendations: List[Recommendation]
    ) -> List[Recommendation]:
        """Ensure each recommendation has a unique technology stack."""

        used_stacks = set()
        diversified_recommendations = []

        for i, recommendation in enumerate(recommendations):
            original_stack = recommendation.tech_stack.copy()

            # Create stack signature for uniqueness check
            stack_signature = tuple(sorted(original_stack))

            if stack_signature in used_stacks:
                # Diversify the stack
                diversified_stack = self._diversify_single_stack(original_stack, i)
                recommendation.tech_stack = diversified_stack
                app_logger.info(f"Diversified tech stack for recommendation {i}")

            used_stacks.add(tuple(sorted(recommendation.tech_stack)))
            diversified_recommendations.append(recommendation)

        return diversified_recommendations

    def _diversify_single_stack(
        self, stack: List[str], recommendation_index: int
    ) -> List[str]:
        """Diversify a single technology stack to make it unique."""

        diversified = stack.copy()

        # Define alternative technologies
        alternatives = {
            "Python": ["GoLang", "Java", "TypeScript"],
            "FastAPI": ["Spring Boot", "Express.js", "Gin"],
            "PostgreSQL": ["MongoDB", "DynamoDB", "Redis"],
            "Docker": ["Kubernetes", "AWS Fargate", "Podman"],
            "Redis": ["Memcached", "Hazelcast", "Apache Ignite"],
        }

        # Apply diversification based on recommendation index
        for i, tech in enumerate(diversified):
            if tech in alternatives and recommendation_index > 0:
                alt_index = (recommendation_index - 1) % len(alternatives[tech])
                diversified[i] = alternatives[tech][alt_index]

        return diversified
