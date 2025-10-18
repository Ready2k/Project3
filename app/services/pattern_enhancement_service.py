"""Service for enhancing existing patterns with detailed technical information and agentic capabilities."""

import json
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

from app.utils.imports import require_service
from app.pattern.enhanced_loader import EnhancedPatternLoader
from app.llm.base import LLMProvider

# Import enhanced catalog capabilities
from app.services.catalog.intelligent_manager import IntelligentCatalogManager
from app.services.catalog.validator import CatalogValidator
from app.services.requirement_parsing.enhanced_parser import EnhancedRequirementParser
from app.services.requirement_parsing.context_extractor import (
    TechnologyContextExtractor,
)


class PatternEnhancementService:
    """Service for enhancing patterns with rich technical details and agentic capabilities."""

    def __init__(
        self, pattern_loader: EnhancedPatternLoader, llm_provider: LLMProvider
    ):
        self.pattern_loader = pattern_loader
        self.llm_provider = llm_provider

        # Get logger from service registry
        self.logger = require_service("logger", context="PatternEnhancementService")

        # Initialize enhanced catalog capabilities
        self.catalog_manager = IntelligentCatalogManager()
        self.catalog_validator = CatalogValidator()
        self.enhanced_parser = EnhancedRequirementParser()
        self.context_extractor = TechnologyContextExtractor()

        self.enhancement_template = self._load_enhancement_template()

    def _load_enhancement_template(self) -> Dict[str, Any]:
        """Load the enhanced pattern template."""
        template_path = (
            Path(__file__).parent.parent / "pattern" / "enhanced_pattern_template.json"
        )
        try:
            with open(template_path, "r") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load enhancement template: {e}")
            return {}

    async def enhance_pattern(
        self, pattern_id: str, enhancement_type: str = "full"
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Enhance an existing pattern with detailed technical information and agentic capabilities.

        Args:
            pattern_id: ID of the pattern to enhance
            enhancement_type: Type of enhancement ("technical", "agentic", "full")

        Returns:
            Tuple of (success, message, enhanced_pattern)
        """
        try:
            # Load existing pattern
            existing_pattern = self.pattern_loader.get_pattern_by_id(pattern_id)
            if not existing_pattern:
                return False, f"Pattern {pattern_id} not found", None

            self.logger.info(
                f"Enhancing pattern {pattern_id} with {enhancement_type} enhancement"
            )

            # Determine enhancement strategy
            if enhancement_type == "technical":
                enhanced_pattern = await self._enhance_technical_details(
                    existing_pattern
                )
            elif enhancement_type == "agentic":
                enhanced_pattern = await self._enhance_agentic_capabilities(
                    existing_pattern
                )
            elif enhancement_type == "full":
                enhanced_pattern = await self._enhance_full_pattern(existing_pattern)
            else:
                return False, f"Unknown enhancement type: {enhancement_type}", None

            # Keep the same pattern ID but mark as enhanced
            enhanced_pattern["pattern_id"] = pattern_id  # Keep original ID
            enhanced_pattern["enhanced_from_pattern"] = pattern_id
            enhanced_pattern["enhancement_type"] = enhancement_type
            enhanced_pattern["enhanced_by_llm"] = True

            # Validate enhanced pattern
            success, message = self.pattern_loader.save_enhanced_pattern(
                enhanced_pattern
            )

            if success:
                return (
                    True,
                    f"Pattern enhanced successfully as {enhanced_pattern['pattern_id']}",
                    enhanced_pattern,
                )
            else:
                return False, f"Failed to save enhanced pattern: {message}", None

        except Exception as e:
            self.logger.error(f"Error enhancing pattern {pattern_id}: {e}")
            return False, f"Enhancement failed: {e}", None

    def _generate_enhanced_pattern_id(self, original_id: str) -> str:
        """Generate a new pattern ID for the enhanced version."""
        if original_id.startswith("PAT-"):
            # Keep the same PAT-XXX ID but enhance in place
            return original_id
        elif original_id.startswith("APAT-"):
            # APAT patterns are already enhanced, keep same ID
            return original_id
        else:
            # Default to original ID
            return original_id

    async def _enhance_technical_details(
        self, pattern: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance pattern with detailed technical implementation information using catalog intelligence."""
        enhanced_pattern = pattern.copy()

        # Extract technology context from pattern description and requirements
        pattern_requirements = {
            "description": pattern.get("description", ""),
            "domain": pattern.get("domain", ""),
            "constraints": pattern.get("constraints", {}),
            "tech_stack": pattern.get("tech_stack", []),
        }

        # Use enhanced parsing to understand technology context
        parsed_requirements = self.enhanced_parser.parse_requirements(
            pattern_requirements
        )
        tech_context = self.context_extractor.build_context(parsed_requirements)

        # Get catalog recommendations for missing technologies
        current_tech_stack = pattern.get("tech_stack", [])
        if isinstance(current_tech_stack, list):
            current_tech_list = current_tech_stack
        elif isinstance(current_tech_stack, dict):
            current_tech_list = []
            for category, techs in current_tech_stack.items():
                if isinstance(techs, list):
                    current_tech_list.extend(techs)
        else:
            current_tech_list = []

        # Get catalog suggestions for enhancement
        catalog_suggestions = self._get_catalog_enhancement_suggestions(
            current_tech_list, tech_context, pattern.get("domain", "")
        )

        # Create enhancement prompt with catalog intelligence
        prompt = f"""
        Enhance the following pattern with detailed technical implementation information:
        
        Pattern: {pattern.get('name', 'Unknown')}
        Description: {pattern.get('description', 'No description')}
        Domain: {pattern.get('domain', 'general')}
        Current Tech Stack: {json.dumps(current_tech_list, indent=2)}
        
        CATALOG INTELLIGENCE:
        - Explicit Technologies Mentioned: {list(tech_context.explicit_technologies.keys())}
        - Contextual Technologies: {list(tech_context.contextual_technologies.keys())}
        - Catalog Suggestions: {catalog_suggestions}
        - Domain Context: {tech_context.domain_context}
        
        IMPORTANT: Respond with ONLY a valid JSON object. Do not include any explanatory text before or after the JSON.
        
        Required JSON structure:
        {{
            "tech_stack": ["Technology1", "Technology2", "..."],
            "implementation_guidance": {{
                "overview": "Brief overview",
                "prerequisites": ["Prerequisite1", "Prerequisite2"],
                "steps": ["Step1", "Step2", "Step3"],
                "best_practices": ["Practice1", "Practice2"]
            }},
            "effort_breakdown": {{
                "total_effort": "X weeks",
                "phases": {{
                    "planning": "X weeks",
                    "development": "X weeks",
                    "testing": "X weeks"
                }}
            }},
            "catalog_metadata": {{
                "enhanced_technologies": ["Tech1", "Tech2"],
                "missing_technologies": ["MissingTech1"],
                "ecosystem_consistency": "aws|azure|gcp|mixed"
            }}
        }}
        
        INSTRUCTIONS:
        1. Include ALL explicit technologies mentioned in the pattern
        2. Add catalog-suggested technologies that improve the stack
        3. Ensure ecosystem consistency (prefer AWS, Azure, or GCP alignment)
        4. Focus on practical, implementable technical details
        5. Mark any technologies not in catalog as missing_technologies
        """

        try:
            response = await self.llm_provider.generate(
                prompt, purpose="pattern_enhancement"
            )

            # Clean and extract JSON from response
            enhancement_data = self._extract_json_from_response(response)
            if not enhancement_data:
                self.logger.warning(
                    "No valid JSON found in LLM response for technical enhancement"
                )
                return self._apply_basic_technical_enhancement(pattern)

            # Merge enhancement data with existing pattern
            enhanced_pattern.update(enhancement_data)

            # Handle tech stack based on pattern type
            pattern_id = pattern.get("pattern_id", "")
            if "tech_stack" in enhancement_data:
                if pattern_id.startswith("PAT-"):
                    # For PAT-* patterns, flatten tech_stack to maintain traditional schema compatibility
                    tech_stack_data = enhancement_data["tech_stack"]
                    if isinstance(tech_stack_data, dict):
                        # Flatten structured tech stack
                        flattened_stack = []
                        for category, technologies in tech_stack_data.items():
                            if isinstance(technologies, list):
                                flattened_stack.extend(technologies)
                        enhanced_pattern["tech_stack"] = flattened_stack
                    else:
                        enhanced_pattern["tech_stack"] = tech_stack_data
                else:
                    # For APAT-* or EPAT-* patterns, keep structured format
                    enhanced_pattern["tech_stack"] = enhancement_data["tech_stack"]

            # Add implementation guidance
            if "implementation_guidance" in enhancement_data:
                enhanced_pattern["implementation_guidance"] = enhancement_data[
                    "implementation_guidance"
                ]

            # Add detailed effort breakdown
            if "effort_breakdown" in enhancement_data:
                enhanced_pattern["effort_breakdown"] = enhancement_data[
                    "effort_breakdown"
                ]

            self.logger.info(
                f"Technical enhancement completed for pattern {pattern.get('pattern_id')}"
            )
            return enhanced_pattern

        except Exception as e:
            self.logger.error(f"Failed to enhance technical details: {e}")
            # Return original pattern with basic enhancements
            return self._apply_basic_technical_enhancement(pattern)

    async def _enhance_agentic_capabilities(
        self, pattern: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance pattern with autonomous agent capabilities."""
        enhanced_pattern = pattern.copy()

        # Create agentic enhancement prompt
        prompt = f"""
        Enhance the following pattern with autonomous agent capabilities:
        
        Pattern: {pattern.get('name', 'Unknown')}
        Description: {pattern.get('description', 'No description')}
        Domain: {pattern.get('domain', 'Unknown')}
        Complexity: {pattern.get('complexity', 'Medium')}
        
        IMPORTANT: Respond with ONLY a valid JSON object. Do not include any explanatory text before or after the JSON.
        
        Required JSON structure:
        {{
            "autonomy_level": "medium",
            "reasoning_types": ["logical_reasoning", "pattern_matching"],
            "decision_boundaries": ["Boundary1", "Boundary2"],
            "self_monitoring": ["Capability1", "Capability2"],
            "learning_mechanisms": ["Mechanism1", "Mechanism2"],
            "agent_architecture": "single_agent"
        }}
        
        Choose autonomy_level from: low, medium, high, very_high
        Choose reasoning_types from: logical_reasoning, causal_reasoning, temporal_reasoning, spatial_reasoning, analogical_reasoning, case_based_reasoning, probabilistic_reasoning, strategic_reasoning, pattern_matching
        Choose agent_architecture from: single_agent, multi_agent_collaborative, hierarchical_agents, swarm_intelligence
        """

        try:
            response = await self.llm_provider.generate(
                prompt, purpose="pattern_enhancement"
            )

            # Clean and extract JSON from response
            enhancement_data = self._extract_json_from_response(response)
            if not enhancement_data:
                self.logger.warning(
                    "No valid JSON found in LLM response for agentic enhancement"
                )
                return self._apply_basic_agentic_enhancement(pattern)

            # Merge agentic capabilities
            agentic_fields = [
                "autonomy_level",
                "reasoning_types",
                "decision_boundaries",
                "exception_handling_strategy",
                "learning_mechanisms",
                "self_monitoring_capabilities",
                "agent_architecture",
                "coordination_requirements",
                "workflow_automation",
            ]

            for field in agentic_fields:
                if field in enhancement_data:
                    enhanced_pattern[field] = enhancement_data[field]

            # Update feasibility if autonomy level is high
            if enhanced_pattern.get("autonomy_level", 0) >= 0.9:
                enhanced_pattern["feasibility"] = "Fully Automatable"
            elif enhanced_pattern.get("autonomy_level", 0) >= 0.7:
                enhanced_pattern["feasibility"] = "Partially Automatable"

            self.logger.info(
                f"Agentic enhancement completed for pattern {pattern.get('pattern_id')}"
            )
            return enhanced_pattern

        except Exception as e:
            self.logger.error(f"Failed to enhance agentic capabilities: {e}")
            # Return original pattern with basic agentic enhancements
            return self._apply_basic_agentic_enhancement(pattern)

    async def _enhance_full_pattern(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Perform full enhancement with both technical details and agentic capabilities."""
        # First enhance technical details
        technically_enhanced = await self._enhance_technical_details(pattern)

        # Then enhance with agentic capabilities
        fully_enhanced = await self._enhance_agentic_capabilities(technically_enhanced)

        # Add full enhancement metadata
        fully_enhanced["enhancement_type"] = "full"
        fully_enhanced["name"] = f"Enhanced {pattern.get('name', 'Pattern')}"

        # Update description to reflect autonomous capabilities
        original_description = pattern.get("description", "")
        fully_enhanced["description"] = (
            f"Fully autonomous AI agent that {original_description.lower()}"
        )

        return fully_enhanced

    def _apply_basic_technical_enhancement(
        self, pattern: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply basic technical enhancements when LLM enhancement fails."""
        enhanced_pattern = pattern.copy()

        # For PAT-* patterns, keep tech_stack as flat array to maintain traditional schema compatibility
        # Only use structured format for APAT-* or EPAT-* patterns
        pattern_id = pattern.get("pattern_id", "")
        tech_stack = pattern.get("tech_stack", [])

        if pattern_id.startswith("PAT-"):
            # Keep as flat array for traditional schema compatibility
            if isinstance(tech_stack, list):
                # Add some additional technologies to enhance the stack
                enhanced_tech_stack = tech_stack.copy()
                if "FastAPI" not in enhanced_tech_stack:
                    enhanced_tech_stack.append("FastAPI")
                if "Docker" not in enhanced_tech_stack:
                    enhanced_tech_stack.append("Docker")
                enhanced_pattern["tech_stack"] = enhanced_tech_stack
            else:
                # If it's already structured, flatten it for traditional schema
                flattened_stack = []
                if isinstance(tech_stack, dict):
                    for category, technologies in tech_stack.items():
                        if isinstance(technologies, list):
                            flattened_stack.extend(technologies)
                enhanced_pattern["tech_stack"] = flattened_stack
        else:
            # For APAT-* or EPAT-* patterns, use structured format
            if isinstance(tech_stack, list):
                enhanced_pattern["tech_stack"] = {
                    "core_technologies": (
                        tech_stack[:3] if len(tech_stack) > 3 else tech_stack
                    ),
                    "data_processing": [
                        t
                        for t in tech_stack
                        if any(
                            keyword in t.lower()
                            for keyword in ["ml", "ai", "data", "analytics"]
                        )
                    ],
                    "infrastructure": [
                        t
                        for t in tech_stack
                        if any(
                            keyword in t.lower()
                            for keyword in [
                                "aws",
                                "azure",
                                "gcp",
                                "docker",
                                "kubernetes",
                            ]
                        )
                    ],
                    "integration_apis": [t for t in tech_stack if "api" in t.lower()],
                }

        # Add basic implementation guidance
        enhanced_pattern["implementation_guidance"] = {
            "architecture_decisions": [
                "Use microservices architecture for scalability",
                "Implement event-driven patterns for loose coupling",
                "Apply cloud-native design principles",
            ],
            "technical_challenges": [
                "Ensuring system scalability and performance",
                "Managing data consistency across services",
                "Implementing robust error handling and recovery",
            ],
        }

        return enhanced_pattern

    def _apply_basic_agentic_enhancement(
        self, pattern: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply basic agentic enhancements when LLM enhancement fails."""
        enhanced_pattern = pattern.copy()

        # Determine autonomy level based on feasibility
        feasibility = pattern.get("feasibility", "Partially Automatable")
        if feasibility == "Automatable" or feasibility == "Fully Automatable":
            enhanced_pattern["autonomy_level"] = 0.85
        else:
            enhanced_pattern["autonomy_level"] = 0.65

        # Add basic reasoning types
        enhanced_pattern["reasoning_types"] = ["logical", "causal", "probabilistic"]

        # Add basic decision boundaries
        enhanced_pattern["decision_boundaries"] = {
            "autonomous_decisions": [
                "Process routine tasks within defined parameters",
                "Apply business rules and validation logic",
                "Generate reports and notifications",
            ],
            "escalation_triggers": [
                "Exceptions outside normal parameters",
                "High-value or high-risk decisions",
                "User requests for human review",
            ],
            "decision_authority_level": "medium",
        }

        # Add basic agent architecture
        enhanced_pattern["agent_architecture"] = "single_agent"

        return enhanced_pattern

    async def batch_enhance_patterns(
        self, pattern_ids: List[str], enhancement_type: str = "full"
    ) -> Dict[str, Any]:
        """Enhance multiple patterns in batch."""
        results = {"successful": [], "failed": [], "total": len(pattern_ids)}

        for pattern_id in pattern_ids:
            success, message, enhanced_pattern = await self.enhance_pattern(
                pattern_id, enhancement_type
            )

            if success:
                results["successful"].append(
                    {
                        "original_id": pattern_id,
                        "enhanced_id": (
                            enhanced_pattern["pattern_id"] if enhanced_pattern else None
                        ),
                        "message": message,
                    }
                )
            else:
                results["failed"].append({"pattern_id": pattern_id, "error": message})

        self.logger.info(
            f"Batch enhancement completed: {len(results['successful'])} successful, {len(results['failed'])} failed"
        )
        return results

    def get_enhancement_candidates(self) -> List[Dict[str, Any]]:
        """Get patterns that are good candidates for enhancement."""
        patterns = self.pattern_loader.load_patterns()
        candidates = []

        for pattern in patterns:
            # Skip already enhanced patterns
            if pattern.get("pattern_id", "").startswith("EPAT-"):
                continue

            # Check if pattern would benefit from enhancement
            capabilities = pattern.get("_capabilities", {})

            # Candidates: traditional patterns without agentic features or detailed tech stack
            if (
                not capabilities.get("has_agentic_features", False)
                or not capabilities.get("has_detailed_tech_stack", False)
                or not capabilities.get("has_implementation_guidance", False)
            ):

                candidates.append(
                    {
                        "pattern_id": pattern.get("pattern_id"),
                        "name": pattern.get("name"),
                        "complexity": pattern.get("complexity"),
                        "missing_capabilities": [
                            k for k, v in capabilities.items() if not v
                        ],
                        "enhancement_potential": self._calculate_enhancement_potential(
                            pattern
                        ),
                    }
                )

        # Sort by enhancement potential
        candidates.sort(key=lambda x: x["enhancement_potential"], reverse=True)
        return candidates

    def _calculate_enhancement_potential(self, pattern: Dict[str, Any]) -> float:
        """Calculate the potential benefit of enhancing a pattern."""
        score = 0.0

        # Higher complexity patterns benefit more from detailed guidance
        complexity_map = {"Low": 0.2, "Medium": 0.5, "High": 0.8, "Very High": 1.0}
        score += complexity_map.get(pattern.get("complexity", "Medium"), 0.5)

        # Patterns with automation potential benefit from agentic enhancement
        feasibility = pattern.get("feasibility", "")
        if "Automatable" in feasibility:
            score += 0.3

        # Patterns with simple tech stacks benefit from detailed technical guidance
        tech_stack = pattern.get("tech_stack", [])
        if isinstance(tech_stack, list) and len(tech_stack) < 5:
            score += 0.2

        # Patterns without implementation guidance benefit significantly
        if not pattern.get("implementation_guidance"):
            score += 0.3

        return min(score, 1.0)

    def _extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response, handling various formats."""
        if not response or not response.strip():
            return None

        import re

        try:
            # First try to parse the entire response as JSON
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass

        # Try to find JSON block in markdown code blocks
        json_patterns = [
            r"```json\s*(\{.*?\})\s*```",
            r"```\s*(\{.*?\})\s*```",
            r"(\{.*?\})",
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match.strip())
                except json.JSONDecodeError:
                    continue

        self.logger.warning(
            f"Could not extract valid JSON from response: {response[:200]}..."
        )
        return None

    def _apply_basic_technical_enhancement(
        self, pattern: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply basic technical enhancements when LLM enhancement fails."""
        enhanced_pattern = pattern.copy()

        # Add basic implementation guidance if missing
        if not enhanced_pattern.get("implementation_guidance"):
            enhanced_pattern["implementation_guidance"] = {
                "overview": f"Implementation guidance for {pattern.get('name', 'this pattern')}",
                "prerequisites": [
                    "Review requirements",
                    "Set up development environment",
                ],
                "steps": [
                    "Plan the implementation approach",
                    "Set up the technical infrastructure",
                    "Implement core functionality",
                    "Test and validate the solution",
                ],
                "best_practices": [
                    "Follow coding standards",
                    "Implement proper error handling",
                    "Add comprehensive logging",
                ],
            }

        # Add basic effort breakdown if missing
        if not enhanced_pattern.get("effort_breakdown"):
            enhanced_pattern["effort_breakdown"] = {
                "total_effort": "4-6 weeks",
                "phases": {
                    "planning": "1 week",
                    "development": "3-4 weeks",
                    "testing": "1 week",
                },
            }

        self.logger.info(
            f"Applied basic technical enhancement to pattern {pattern.get('pattern_id')}"
        )
        return enhanced_pattern

    def _apply_basic_agentic_enhancement(
        self, pattern: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply basic agentic enhancements when LLM enhancement fails."""
        enhanced_pattern = pattern.copy()

        # Add basic agentic capabilities
        enhanced_pattern["autonomy_level"] = "medium"
        enhanced_pattern["reasoning_types"] = ["logical_reasoning", "pattern_matching"]
        enhanced_pattern["decision_boundaries"] = [
            "Standard operational parameters",
            "Predefined business rules",
        ]
        enhanced_pattern["self_monitoring"] = [
            "Performance tracking",
            "Error detection",
        ]
        enhanced_pattern["learning_mechanisms"] = [
            "Pattern recognition",
            "Feedback incorporation",
        ]
        enhanced_pattern["agent_architecture"] = "single_agent"

        self.logger.info(
            f"Applied basic agentic enhancement to pattern {pattern.get('pattern_id')}"
        )
        return enhanced_pattern

    def _get_catalog_enhancement_suggestions(
        self, current_tech_stack: List[str], tech_context: Any, domain: str
    ) -> Dict[str, Any]:
        """Get catalog-based suggestions for enhancing the technology stack.

        Args:
            current_tech_stack: Current technologies in the pattern
            tech_context: Technology context from enhanced parsing
            domain: Pattern domain

        Returns:
            Dictionary of enhancement suggestions
        """
        try:
            suggestions = {
                "missing_from_catalog": [],
                "recommended_additions": [],
                "ecosystem_alignment": "mixed",
                "integration_opportunities": [],
            }

            # Check which technologies are missing from catalog
            for tech in current_tech_stack:
                if not self.catalog_manager.lookup_technology(tech):
                    suggestions["missing_from_catalog"].append(tech)
                    # Auto-add to catalog for future use
                    self.catalog_manager.auto_add_technology(
                        tech, {"source": "pattern_enhancement", "domain": domain}
                    )

            # Get recommendations based on domain and context
            if hasattr(tech_context, "domain_context"):

                # Suggest domain-specific technologies
                if domain in ["legal", "compliance"]:
                    suggestions["recommended_additions"].extend(
                        ["Microsoft Presidio", "spaCy", "FAISS"]
                    )
                elif domain in ["customer_support", "communication"]:
                    suggestions["recommended_additions"].extend(
                        ["Twilio", "Slack API", "Azure Cognitive Services"]
                    )
                elif domain in ["data_processing", "analytics"]:
                    suggestions["recommended_additions"].extend(
                        ["Apache Spark", "Elasticsearch", "PostgreSQL"]
                    )

            # Determine ecosystem alignment
            cloud_techs = [
                tech
                for tech in current_tech_stack
                if any(cloud in tech.lower() for cloud in ["aws", "azure", "gcp"])
            ]
            if cloud_techs:
                if any("aws" in tech.lower() for tech in cloud_techs):
                    suggestions["ecosystem_alignment"] = "aws"
                elif any("azure" in tech.lower() for tech in cloud_techs):
                    suggestions["ecosystem_alignment"] = "azure"
                elif any("gcp" in tech.lower() for tech in cloud_techs):
                    suggestions["ecosystem_alignment"] = "gcp"

            # Suggest integration opportunities
            if (
                "FastAPI" in current_tech_stack
                and "PostgreSQL" not in current_tech_stack
            ):
                suggestions["integration_opportunities"].append(
                    "PostgreSQL for data persistence"
                )
            if "Docker" not in current_tech_stack:
                suggestions["integration_opportunities"].append(
                    "Docker for containerization"
                )

            return suggestions

        except Exception as e:
            self.logger.error(f"Error getting catalog enhancement suggestions: {e}")
            return {
                "missing_from_catalog": [],
                "recommended_additions": [],
                "ecosystem_alignment": "mixed",
                "integration_opportunities": [],
            }

    def update_existing_patterns_with_enhanced_metadata(self) -> Dict[str, Any]:
        """Update existing patterns to use improved technology metadata.

        Returns:
            Dictionary with update results
        """
        try:
            patterns = self.pattern_loader.load_patterns()
            results = {
                "updated": [],
                "failed": [],
                "skipped": [],
                "total": len(patterns),
            }

            for pattern in patterns:
                pattern_id = pattern.get("pattern_id", "")

                # Skip already enhanced patterns
                if pattern.get("enhanced_by_llm") and pattern.get("catalog_metadata"):
                    results["skipped"].append(
                        {
                            "pattern_id": pattern_id,
                            "reason": "Already has enhanced metadata",
                        }
                    )
                    continue

                try:
                    # Extract current tech stack
                    current_tech_stack = pattern.get("tech_stack", [])
                    if isinstance(current_tech_stack, dict):
                        # Flatten structured tech stack for analysis
                        tech_list = []
                        for category, techs in current_tech_stack.items():
                            if isinstance(techs, list):
                                tech_list.extend(techs)
                        current_tech_stack = tech_list

                    # Parse pattern requirements for context
                    pattern_requirements = {
                        "description": pattern.get("description", ""),
                        "domain": pattern.get("domain", ""),
                        "constraints": pattern.get("constraints", {}),
                        "tech_stack": current_tech_stack,
                    }

                    parsed_requirements = self.enhanced_parser.parse_requirements(
                        pattern_requirements
                    )
                    tech_context = self.context_extractor.build_context(
                        parsed_requirements
                    )

                    # Get catalog enhancement suggestions
                    catalog_suggestions = self._get_catalog_enhancement_suggestions(
                        current_tech_stack, tech_context, pattern.get("domain", "")
                    )

                    # Update pattern with enhanced metadata
                    updated_pattern = pattern.copy()
                    updated_pattern["catalog_metadata"] = {
                        "last_updated": datetime.now().isoformat(),
                        "enhanced_by_catalog": True,
                        "missing_from_catalog": catalog_suggestions[
                            "missing_from_catalog"
                        ],
                        "ecosystem_alignment": catalog_suggestions[
                            "ecosystem_alignment"
                        ],
                        "integration_opportunities": catalog_suggestions[
                            "integration_opportunities"
                        ],
                        "explicit_technologies": list(
                            tech_context.explicit_technologies.keys()
                        ),
                        "contextual_technologies": list(
                            tech_context.contextual_technologies.keys()
                        ),
                    }

                    # Add technology confidence scores
                    if tech_context.explicit_technologies:
                        updated_pattern["technology_confidence"] = (
                            tech_context.explicit_technologies
                        )

                    # Save updated pattern
                    success, message = self.pattern_loader.save_enhanced_pattern(
                        updated_pattern
                    )

                    if success:
                        results["updated"].append(
                            {
                                "pattern_id": pattern_id,
                                "enhancements": list(catalog_suggestions.keys()),
                            }
                        )
                        self.logger.info(
                            f"Updated pattern {pattern_id} with enhanced metadata"
                        )
                    else:
                        results["failed"].append(
                            {"pattern_id": pattern_id, "error": message}
                        )

                except Exception as e:
                    results["failed"].append(
                        {"pattern_id": pattern_id, "error": str(e)}
                    )
                    self.logger.error(f"Failed to update pattern {pattern_id}: {e}")

            self.logger.info(
                f"Pattern metadata update completed: {len(results['updated'])} updated, "
                f"{len(results['failed'])} failed, {len(results['skipped'])} skipped"
            )

            return results

        except Exception as e:
            self.logger.error(f"Error updating existing patterns: {e}")
            return {
                "updated": [],
                "failed": [],
                "skipped": [],
                "total": 0,
                "error": str(e),
            }
