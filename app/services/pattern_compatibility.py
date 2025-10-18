"""Backward compatibility layer for existing patterns with enhanced system."""

import json
from typing import Dict, Any, List, Tuple
from pathlib import Path
from datetime import datetime

from app.utils.imports import require_service


class PatternCompatibilityLayer:
    """Ensures backward compatibility between old and new pattern formats."""

    def __init__(self):
        """Initialize compatibility layer."""
        try:
            self.logger = require_service("logger", context="PatternCompatibilityLayer")
        except Exception:
            import logging

            self.logger = logging.getLogger("PatternCompatibilityLayer")

    def normalize_pattern_format(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize pattern to work with enhanced system.

        Args:
            pattern: Pattern in any format (old or new)

        Returns:
            Pattern normalized for enhanced system compatibility
        """
        try:
            normalized = pattern.copy()

            # Ensure required fields exist
            normalized = self._ensure_required_fields(normalized)

            # Normalize tech stack format
            normalized = self._normalize_tech_stack(normalized)

            # Normalize constraints format
            normalized = self._normalize_constraints(normalized)

            # Add compatibility metadata
            normalized = self._add_compatibility_metadata(normalized)

            # Validate normalized pattern
            validation_result = self._validate_normalized_pattern(normalized)
            if not validation_result["valid"]:
                self.logger.warning(
                    f"Pattern {pattern.get('pattern_id')} normalization has issues: {validation_result['warnings']}"
                )

            return normalized

        except Exception as e:
            self.logger.error(
                f"Failed to normalize pattern {pattern.get('pattern_id', 'unknown')}: {e}"
            )
            # Return original pattern if normalization fails
            return pattern

    def _ensure_required_fields(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all required fields exist with default values.

        Args:
            pattern: Pattern to process

        Returns:
            Pattern with required fields
        """
        required_defaults = {
            "pattern_id": f"PAT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "name": "Unnamed Pattern",
            "description": "No description provided",
            "feasibility": "Automatable",
            "pattern_type": ["general_automation"],
            "input_requirements": ["User input"],
            "tech_stack": [],
            "related_patterns": [],
            "confidence_score": 0.7,
            "constraints": {"banned_tools": [], "required_integrations": []},
            "domain": "general",
            "complexity": "Medium",
            "estimated_effort": "2-4 weeks",
            "auto_generated": False,
        }

        for field, default_value in required_defaults.items():
            if field not in pattern:
                pattern[field] = default_value
                self.logger.debug(f"Added missing field '{field}' with default value")

        return pattern

    def _normalize_tech_stack(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize tech stack format for compatibility.

        Args:
            pattern: Pattern to process

        Returns:
            Pattern with normalized tech stack
        """
        tech_stack = pattern.get("tech_stack", [])
        pattern_id = pattern.get("pattern_id", "")

        # Handle different tech stack formats
        if isinstance(tech_stack, dict):
            # Structured format - decide whether to keep or flatten
            if pattern_id.startswith("APAT-") or pattern_id.startswith("EPAT-"):
                # Keep structured format for agentic patterns
                pattern["tech_stack"] = tech_stack
            else:
                # Flatten for traditional patterns (PAT-*)
                flattened = []
                for category, technologies in tech_stack.items():
                    if isinstance(technologies, list):
                        flattened.extend(technologies)
                    elif isinstance(technologies, str):
                        flattened.append(technologies)
                pattern["tech_stack"] = flattened
                self.logger.debug(
                    f"Flattened structured tech stack for pattern {pattern_id}"
                )

        elif isinstance(tech_stack, list):
            # List format - decide whether to structure or keep flat
            if pattern_id.startswith("APAT-") and len(tech_stack) > 5:
                # Structure for complex agentic patterns
                structured = self._structure_tech_stack(tech_stack)
                pattern["tech_stack"] = structured
                self.logger.debug(
                    f"Structured flat tech stack for pattern {pattern_id}"
                )
            else:
                # Keep flat for traditional patterns
                pattern["tech_stack"] = tech_stack

        elif isinstance(tech_stack, str):
            # Single technology as string
            pattern["tech_stack"] = [tech_stack]
            self.logger.debug(
                f"Converted string tech stack to list for pattern {pattern_id}"
            )

        else:
            # Invalid format
            pattern["tech_stack"] = []
            self.logger.warning(
                f"Invalid tech stack format for pattern {pattern_id}, reset to empty list"
            )

        return pattern

    def _structure_tech_stack(self, tech_list: List[str]) -> Dict[str, List[str]]:
        """Structure a flat tech stack list into categories.

        Args:
            tech_list: Flat list of technologies

        Returns:
            Structured tech stack dictionary
        """
        structured = {
            "core_technologies": [],
            "data_processing": [],
            "infrastructure": [],
            "integration_apis": [],
            "other": [],
        }

        # Categorization rules
        categorization_rules = {
            "core_technologies": [
                "fastapi",
                "django",
                "flask",
                "express",
                "spring",
                "nodejs",
                "python",
                "java",
                "javascript",
                "typescript",
            ],
            "data_processing": [
                "postgresql",
                "mysql",
                "mongodb",
                "redis",
                "elasticsearch",
                "apache spark",
                "pandas",
                "numpy",
                "scikit-learn",
                "tensorflow",
                "pytorch",
                "huggingface",
                "spacy",
                "nltk",
            ],
            "infrastructure": [
                "docker",
                "kubernetes",
                "aws",
                "azure",
                "gcp",
                "nginx",
                "apache",
                "jenkins",
                "github actions",
                "terraform",
                "ansible",
            ],
            "integration_apis": [
                "rest api",
                "graphql",
                "grpc",
                "webhook",
                "kafka",
                "rabbitmq",
                "twilio",
                "slack api",
                "jira api",
                "stripe api",
            ],
        }

        for tech in tech_list:
            tech_lower = tech.lower()
            categorized = False

            for category, keywords in categorization_rules.items():
                if any(keyword in tech_lower for keyword in keywords):
                    structured[category].append(tech)
                    categorized = True
                    break

            if not categorized:
                structured["other"].append(tech)

        # Remove empty categories
        return {k: v for k, v in structured.items() if v}

    def _normalize_constraints(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize constraints format.

        Args:
            pattern: Pattern to process

        Returns:
            Pattern with normalized constraints
        """
        constraints = pattern.get("constraints", {})

        # Ensure constraints is a dictionary
        if not isinstance(constraints, dict):
            constraints = {}

        # Ensure required constraint fields
        constraint_defaults = {
            "banned_tools": [],
            "required_integrations": [],
            "compliance_requirements": [],
            "data_sensitivity": "",
            "budget_constraints": "",
            "deployment_preference": "",
        }

        for field, default_value in constraint_defaults.items():
            if field not in constraints:
                constraints[field] = default_value

        # Normalize list fields
        list_fields = [
            "banned_tools",
            "required_integrations",
            "compliance_requirements",
        ]
        for field in list_fields:
            if isinstance(constraints[field], str):
                # Convert string to list
                constraints[field] = [constraints[field]] if constraints[field] else []
            elif not isinstance(constraints[field], list):
                constraints[field] = []

        pattern["constraints"] = constraints
        return pattern

    def _add_compatibility_metadata(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Add compatibility metadata to pattern.

        Args:
            pattern: Pattern to process

        Returns:
            Pattern with compatibility metadata
        """
        # Add compatibility tracking
        if "_compatibility" not in pattern:
            pattern["_compatibility"] = {
                "normalized_at": datetime.now().isoformat(),
                "original_format_detected": self._detect_original_format(pattern),
                "normalization_applied": True,
                "backward_compatible": True,
            }

        # Add capabilities metadata for enhancement detection
        if "_capabilities" not in pattern:
            pattern["_capabilities"] = self._assess_pattern_capabilities(pattern)

        return pattern

    def _detect_original_format(self, pattern: Dict[str, Any]) -> str:
        """Detect the original format of the pattern.

        Args:
            pattern: Pattern to analyze

        Returns:
            Detected format identifier
        """
        pattern_id = pattern.get("pattern_id", "")

        # Check for enhanced fields
        enhanced_fields = [
            "autonomy_level",
            "reasoning_types",
            "decision_boundaries",
            "implementation_guidance",
            "catalog_metadata",
        ]

        has_enhanced_fields = any(field in pattern for field in enhanced_fields)

        if pattern_id.startswith("APAT-"):
            return "agentic_enhanced" if has_enhanced_fields else "agentic_basic"
        elif pattern_id.startswith("EPAT-"):
            return "enhanced_pattern"
        elif pattern_id.startswith("PAT-"):
            return (
                "traditional_enhanced" if has_enhanced_fields else "traditional_basic"
            )
        elif pattern_id.startswith("TRAD-AUTO-"):
            return "traditional_automation"
        else:
            return "unknown_format"

    def _assess_pattern_capabilities(self, pattern: Dict[str, Any]) -> Dict[str, bool]:
        """Assess what capabilities a pattern has.

        Args:
            pattern: Pattern to assess

        Returns:
            Dictionary of capability flags
        """
        capabilities = {
            "has_agentic_features": False,
            "has_detailed_tech_stack": False,
            "has_implementation_guidance": False,
            "has_catalog_metadata": False,
            "has_enhanced_constraints": False,
            "has_reasoning_capabilities": False,
        }

        # Check for agentic features
        agentic_fields = [
            "autonomy_level",
            "reasoning_types",
            "decision_boundaries",
            "agent_architecture",
        ]
        capabilities["has_agentic_features"] = any(
            field in pattern for field in agentic_fields
        )

        # Check for detailed tech stack
        tech_stack = pattern.get("tech_stack", [])
        if isinstance(tech_stack, dict):
            capabilities["has_detailed_tech_stack"] = len(tech_stack) > 1
        elif isinstance(tech_stack, list):
            capabilities["has_detailed_tech_stack"] = len(tech_stack) > 3

        # Check for implementation guidance
        capabilities["has_implementation_guidance"] = (
            "implementation_guidance" in pattern
        )

        # Check for catalog metadata
        capabilities["has_catalog_metadata"] = "catalog_metadata" in pattern

        # Check for enhanced constraints
        constraints = pattern.get("constraints", {})
        enhanced_constraint_fields = [
            "compliance_requirements",
            "data_sensitivity",
            "deployment_preference",
        ]
        capabilities["has_enhanced_constraints"] = any(
            field in constraints for field in enhanced_constraint_fields
        )

        # Check for reasoning capabilities
        reasoning_fields = [
            "reasoning_types",
            "decision_boundaries",
            "learning_mechanisms",
        ]
        capabilities["has_reasoning_capabilities"] = any(
            field in pattern for field in reasoning_fields
        )

        return capabilities

    def _validate_normalized_pattern(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Validate normalized pattern for common issues.

        Args:
            pattern: Normalized pattern to validate

        Returns:
            Validation result dictionary
        """
        validation_result = {"valid": True, "warnings": [], "errors": []}

        # Check required fields
        required_fields = [
            "pattern_id",
            "name",
            "description",
            "feasibility",
            "tech_stack",
        ]
        for field in required_fields:
            if field not in pattern or not pattern[field]:
                validation_result["errors"].append(f"Missing required field: {field}")
                validation_result["valid"] = False

        # Check tech stack
        tech_stack = pattern.get("tech_stack", [])
        if isinstance(tech_stack, list) and len(tech_stack) == 0:
            validation_result["warnings"].append("Empty tech stack")
        elif isinstance(tech_stack, dict) and not any(tech_stack.values()):
            validation_result["warnings"].append("Empty structured tech stack")

        # Check feasibility values
        valid_feasibility = [
            "Automatable",
            "Partially Automatable",
            "Not Automatable",
            "Fully Automatable",
        ]
        if pattern.get("feasibility") not in valid_feasibility:
            validation_result["warnings"].append(
                f"Invalid feasibility value: {pattern.get('feasibility')}"
            )

        # Check confidence score
        confidence = pattern.get("confidence_score", 0)
        if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
            validation_result["warnings"].append(
                f"Invalid confidence score: {confidence}"
            )

        return validation_result

    def convert_legacy_patterns_batch(self, pattern_directory: Path) -> Dict[str, Any]:
        """Convert multiple legacy patterns to enhanced format.

        Args:
            pattern_directory: Directory containing pattern files

        Returns:
            Conversion results dictionary
        """
        results = {"converted": [], "failed": [], "skipped": [], "total": 0}

        try:
            pattern_files = list(pattern_directory.glob("*.json"))
            results["total"] = len(pattern_files)

            for pattern_file in pattern_files:
                try:
                    # Load pattern
                    with open(pattern_file, "r") as f:
                        pattern = json.load(f)

                    pattern_id = pattern.get("pattern_id", pattern_file.stem)

                    # Check if already enhanced
                    if pattern.get("_compatibility", {}).get("normalization_applied"):
                        results["skipped"].append(
                            {"pattern_id": pattern_id, "reason": "Already normalized"}
                        )
                        continue

                    # Normalize pattern
                    normalized_pattern = self.normalize_pattern_format(pattern)

                    # Save normalized pattern
                    with open(pattern_file, "w") as f:
                        json.dump(normalized_pattern, f, indent=2, ensure_ascii=False)

                    results["converted"].append(
                        {
                            "pattern_id": pattern_id,
                            "original_format": normalized_pattern.get(
                                "_compatibility", {}
                            ).get("original_format_detected"),
                            "capabilities_added": list(
                                normalized_pattern.get("_capabilities", {}).keys()
                            ),
                        }
                    )

                    self.logger.info(
                        f"Converted pattern {pattern_id} to enhanced format"
                    )

                except Exception as e:
                    results["failed"].append(
                        {"pattern_file": str(pattern_file), "error": str(e)}
                    )
                    self.logger.error(f"Failed to convert pattern {pattern_file}: {e}")

            self.logger.info(
                f"Batch conversion completed: {len(results['converted'])} converted, "
                f"{len(results['failed'])} failed, {len(results['skipped'])} skipped"
            )

            return results

        except Exception as e:
            self.logger.error(f"Batch conversion failed: {e}")
            return {
                "converted": [],
                "failed": [],
                "skipped": [],
                "total": 0,
                "error": str(e),
            }

    def is_pattern_compatible(self, pattern: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Check if pattern is compatible with enhanced system.

        Args:
            pattern: Pattern to check

        Returns:
            Tuple of (is_compatible, list_of_issues)
        """
        issues = []

        # Check required fields
        required_fields = [
            "pattern_id",
            "name",
            "description",
            "feasibility",
            "tech_stack",
        ]
        for field in required_fields:
            if field not in pattern:
                issues.append(f"Missing required field: {field}")

        # Check tech stack format
        tech_stack = pattern.get("tech_stack")
        if tech_stack is not None and not isinstance(tech_stack, (list, dict)):
            issues.append("Invalid tech_stack format (must be list or dict)")

        # Check constraints format
        constraints = pattern.get("constraints")
        if constraints is not None and not isinstance(constraints, dict):
            issues.append("Invalid constraints format (must be dict)")

        # Check pattern_type format
        pattern_type = pattern.get("pattern_type")
        if pattern_type is not None and not isinstance(pattern_type, list):
            issues.append("Invalid pattern_type format (must be list)")

        is_compatible = len(issues) == 0
        return is_compatible, issues

    def get_compatibility_report(self, pattern_directory: Path) -> Dict[str, Any]:
        """Generate compatibility report for all patterns in directory.

        Args:
            pattern_directory: Directory containing pattern files

        Returns:
            Compatibility report dictionary
        """
        report = {
            "total_patterns": 0,
            "compatible": [],
            "incompatible": [],
            "needs_normalization": [],
            "summary": {},
        }

        try:
            pattern_files = list(pattern_directory.glob("*.json"))
            report["total_patterns"] = len(pattern_files)

            for pattern_file in pattern_files:
                try:
                    with open(pattern_file, "r") as f:
                        pattern = json.load(f)

                    pattern_id = pattern.get("pattern_id", pattern_file.stem)
                    is_compatible, issues = self.is_pattern_compatible(pattern)

                    if is_compatible:
                        # Check if needs normalization
                        if not pattern.get("_compatibility", {}).get(
                            "normalization_applied"
                        ):
                            report["needs_normalization"].append(
                                {
                                    "pattern_id": pattern_id,
                                    "format": self._detect_original_format(pattern),
                                }
                            )
                        else:
                            report["compatible"].append(
                                {
                                    "pattern_id": pattern_id,
                                    "format": pattern.get("_compatibility", {}).get(
                                        "original_format_detected"
                                    ),
                                }
                            )
                    else:
                        report["incompatible"].append(
                            {"pattern_id": pattern_id, "issues": issues}
                        )

                except Exception as e:
                    report["incompatible"].append(
                        {
                            "pattern_file": str(pattern_file),
                            "issues": [f"Failed to load: {e}"],
                        }
                    )

            # Generate summary
            report["summary"] = {
                "compatible_count": len(report["compatible"]),
                "incompatible_count": len(report["incompatible"]),
                "needs_normalization_count": len(report["needs_normalization"]),
                "compatibility_rate": len(report["compatible"])
                / max(report["total_patterns"], 1)
                * 100,
            }

            return report

        except Exception as e:
            self.logger.error(f"Failed to generate compatibility report: {e}")
            return {
                "total_patterns": 0,
                "compatible": [],
                "incompatible": [],
                "needs_normalization": [],
                "summary": {},
                "error": str(e),
            }
