"""Technology compatibility validation system with comprehensive validation rules."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime
from collections import Counter, defaultdict

from .models import (
    CompatibilityResult, TechnologyConflict, EcosystemConsistencyResult,
    ValidationReport, ConflictType, ConflictSeverity, CompatibilityMatrix
)
from ..catalog.models import TechEntry, EcosystemType
from ..catalog.intelligent_manager import IntelligentCatalogManager
from app.utils.imports import require_service


class TechnologyCompatibilityValidator:
    """
    Comprehensive technology compatibility validator with ecosystem consistency checking,
    conflict detection, and resolution logic using context priority.
    """
    
    def __init__(self, catalog_manager: Optional[IntelligentCatalogManager] = None):
        """
        Initialize the compatibility validator.
        
        Args:
            catalog_manager: Optional catalog manager instance
        """
        self.catalog_manager = catalog_manager or IntelligentCatalogManager()
        self.logger = require_service('logger', context='TechnologyCompatibilityValidator')
        
        # Load compatibility matrices and rules
        self.compatibility_matrices: Dict[Tuple[str, str], CompatibilityMatrix] = {}
        self.ecosystem_rules: Dict[str, Dict[str, Any]] = {}
        self.conflict_rules: List[Dict[str, Any]] = []
        
        self._load_compatibility_data()
        self._initialize_default_rules()
    
    def _load_compatibility_data(self) -> None:
        """Load compatibility matrices and rules from configuration files."""
        try:
            # Try to load existing compatibility data
            compat_path = Path("Project3/data/compatibility_matrices.json")
            if compat_path.exists():
                with open(compat_path, 'r') as f:
                    data = json.load(f)
                    self._load_compatibility_matrices(data.get("matrices", {}))
                    self.ecosystem_rules = data.get("ecosystem_rules", {})
                    self.conflict_rules = data.get("conflict_rules", [])
            else:
                self.logger.info("No existing compatibility data found, using defaults")
        except Exception as e:
            self.logger.error(f"Failed to load compatibility data: {e}")
    
    def _load_compatibility_matrices(self, matrices_data: Dict[str, Any]) -> None:
        """Load compatibility matrices from data."""
        for key, matrix_data in matrices_data.items():
            tech1, tech2 = key.split("|")
            last_updated = None
            if matrix_data.get("last_updated"):
                last_updated = datetime.fromisoformat(matrix_data["last_updated"])
            
            matrix = CompatibilityMatrix(
                tech1=tech1,
                tech2=tech2,
                compatibility_score=matrix_data["compatibility_score"],
                notes=matrix_data.get("notes"),
                last_updated=last_updated
            )
            self.compatibility_matrices[(tech1, tech2)] = matrix
    
    def _initialize_default_rules(self) -> None:
        """Initialize default compatibility rules."""
        if not self.ecosystem_rules:
            self.ecosystem_rules = {
                "aws": {
                    "preferred_technologies": ["aws", "amazon", "s3", "lambda", "dynamodb", "rds"],
                    "incompatible_with": ["azure", "gcp", "google cloud"],
                    "tolerance_threshold": 0.8  # 80% should be from same ecosystem
                },
                "azure": {
                    "preferred_technologies": ["azure", "microsoft", "cosmos", "functions"],
                    "incompatible_with": ["aws", "gcp", "google cloud"],
                    "tolerance_threshold": 0.8
                },
                "gcp": {
                    "preferred_technologies": ["gcp", "google", "bigquery", "cloud functions"],
                    "incompatible_with": ["aws", "azure"],
                    "tolerance_threshold": 0.8
                }
            }
        
        if not self.conflict_rules:
            self.conflict_rules = [
                {
                    "name": "cloud_provider_conflict",
                    "type": ConflictType.ECOSYSTEM_MISMATCH.value,
                    "severity": ConflictSeverity.HIGH.value,
                    "patterns": [
                        {"tech1_contains": ["aws"], "tech2_contains": ["azure"]},
                        {"tech1_contains": ["aws"], "tech2_contains": ["gcp"]},
                        {"tech1_contains": ["azure"], "tech2_contains": ["gcp"]}
                    ],
                    "description": "Multiple cloud providers detected",
                    "resolution": "Choose a single cloud provider for consistency"
                },
                {
                    "name": "database_conflict",
                    "type": ConflictType.ARCHITECTURE_MISMATCH.value,
                    "severity": ConflictSeverity.MEDIUM.value,
                    "patterns": [
                        {"tech1_contains": ["mysql"], "tech2_contains": ["postgresql"]},
                        {"tech1_contains": ["mongodb"], "tech2_contains": ["sql"]}
                    ],
                    "description": "Multiple database systems detected",
                    "resolution": "Consider using a single primary database"
                },
                {
                    "name": "license_conflict",
                    "type": ConflictType.LICENSE_INCOMPATIBILITY.value,
                    "severity": ConflictSeverity.HIGH.value,
                    "patterns": [
                        {"tech1_license": "GPL", "tech2_license": "proprietary"},
                        {"tech1_license": "AGPL", "tech2_license": "commercial"}
                    ],
                    "description": "License incompatibility detected",
                    "resolution": "Review license compatibility requirements"
                }
            ]
    
    def validate_tech_stack(self, 
                          tech_stack: List[str], 
                          context_priority: Optional[Dict[str, float]] = None) -> ValidationReport:
        """
        Validate entire tech stack for compatibility with comprehensive reporting.
        
        Args:
            tech_stack: List of technology names to validate
            context_priority: Optional priority scores for technologies (0.0-1.0)
        
        Returns:
            Comprehensive validation report with explanations and alternatives
        """
        self.logger.info(f"Validating tech stack with {len(tech_stack)} technologies")
        
        context_priority = context_priority or {}
        validation_timestamp = datetime.now()
        
        # Get technology entries from catalog
        tech_entries = self._resolve_technologies(tech_stack)
        
        # Perform compatibility validation
        compatibility_result = self._validate_compatibility(tech_entries, context_priority)
        
        # Generate explanations
        inclusion_explanations = self._generate_inclusion_explanations(
            compatibility_result.validated_technologies, tech_entries, context_priority
        )
        exclusion_explanations = self._generate_exclusion_explanations(
            compatibility_result.removed_technologies, compatibility_result.conflicts
        )
        alternative_suggestions = self._generate_alternative_suggestions(
            compatibility_result.removed_technologies, tech_entries
        )
        
        # Create comprehensive report
        report = ValidationReport(
            original_tech_stack=tech_stack.copy(),
            validated_tech_stack=compatibility_result.validated_technologies,
            compatibility_result=compatibility_result,
            validation_timestamp=validation_timestamp,
            context_priority=context_priority,
            inclusion_explanations=inclusion_explanations,
            exclusion_explanations=exclusion_explanations,
            alternative_suggestions=alternative_suggestions
        )
        
        self.logger.info(f"Validation complete: {len(report.validated_tech_stack)}/{len(tech_stack)} technologies validated")
        return report
    
    def _resolve_technologies(self, tech_stack: List[str]) -> Dict[str, Optional[TechEntry]]:
        """Resolve technology names to catalog entries."""
        tech_entries = {}
        
        for tech_name in tech_stack:
            # Try exact lookup first
            match_result = self.catalog_manager.lookup_technology(tech_name, fuzzy_threshold=0.8)
            
            if match_result:
                tech_entries[tech_name] = match_result.tech_entry
                self.logger.debug(f"Resolved {tech_name} -> {match_result.tech_entry.canonical_name}")
            else:
                tech_entries[tech_name] = None
                self.logger.warning(f"Could not resolve technology: {tech_name}")
        
        return tech_entries
    
    def _validate_compatibility(self, 
                              tech_entries: Dict[str, Optional[TechEntry]], 
                              context_priority: Dict[str, float]) -> CompatibilityResult:
        """Perform comprehensive compatibility validation."""
        
        # Check ecosystem consistency
        ecosystem_result = self.check_ecosystem_consistency(list(tech_entries.keys()), tech_entries)
        
        # Detect conflicts
        conflicts = self._detect_conflicts(tech_entries)
        
        # Resolve conflicts using context priority
        validated_technologies, removed_technologies = self._resolve_conflicts(
            list(tech_entries.keys()), conflicts, context_priority
        )
        
        # Calculate overall compatibility score
        overall_score = self._calculate_compatibility_score(
            validated_technologies, conflicts, ecosystem_result
        )
        
        # Generate suggestions
        suggestions = self._generate_suggestions(
            validated_technologies, removed_technologies, conflicts, ecosystem_result
        )
        
        return CompatibilityResult(
            is_compatible=overall_score >= 0.7 and not any(c.severity == ConflictSeverity.CRITICAL for c in conflicts),
            overall_score=overall_score,
            conflicts=conflicts,
            ecosystem_result=ecosystem_result,
            validated_technologies=validated_technologies,
            removed_technologies=removed_technologies,
            suggestions=suggestions
        )
    
    def check_ecosystem_consistency(self, 
                                  tech_stack: List[str], 
                                  tech_entries: Optional[Dict[str, Optional[TechEntry]]] = None) -> EcosystemConsistencyResult:
        """
        Check if technologies belong to consistent ecosystems (AWS, Azure, GCP alignment).
        
        Args:
            tech_stack: List of technology names
            tech_entries: Optional pre-resolved technology entries
        
        Returns:
            Ecosystem consistency analysis result
        """
        if tech_entries is None:
            tech_entries = self._resolve_technologies(tech_stack)
        
        ecosystem_counts = Counter()
        ecosystem_technologies = defaultdict(list)
        mixed_ecosystem_technologies = []
        
        # Analyze ecosystem distribution
        for tech_name, tech_entry in tech_entries.items():
            if tech_entry and tech_entry.ecosystem:
                ecosystem = tech_entry.ecosystem.value
                ecosystem_counts[ecosystem] += 1
                ecosystem_technologies[ecosystem].append(tech_name)
            else:
                # Try to infer ecosystem from name
                inferred_ecosystem = self._infer_ecosystem_from_name(tech_name)
                if inferred_ecosystem:
                    ecosystem_counts[inferred_ecosystem] += 1
                    ecosystem_technologies[inferred_ecosystem].append(tech_name)
        
        # Determine primary ecosystem
        primary_ecosystem = None
        primary_ecosystem_name = None
        if ecosystem_counts:
            primary_ecosystem_name = ecosystem_counts.most_common(1)[0][0]
            try:
                primary_ecosystem = EcosystemType(primary_ecosystem_name)
            except ValueError:
                primary_ecosystem = None
        
        # Check for mixed ecosystems
        cloud_ecosystems = {"aws", "azure", "gcp"}
        cloud_ecosystem_count = sum(1 for eco in ecosystem_counts.keys() if eco in cloud_ecosystems)
        
        is_consistent = True
        recommendations = []
        
        if cloud_ecosystem_count > 1:
            is_consistent = False
            # Find technologies from non-primary ecosystems
            for ecosystem, technologies in ecosystem_technologies.items():
                if ecosystem != primary_ecosystem_name and ecosystem in cloud_ecosystems:
                    mixed_ecosystem_technologies.extend(technologies)
            
            recommendations.append(f"Multiple cloud ecosystems detected. Consider standardizing on {primary_ecosystem_name}")
            recommendations.append("Review mixed-ecosystem technologies for potential alternatives")
        
        # Check ecosystem rules
        if primary_ecosystem_name and primary_ecosystem_name in self.ecosystem_rules:
            rules = self.ecosystem_rules[primary_ecosystem_name]
            threshold = rules.get("tolerance_threshold", 0.8)
            
            primary_count = ecosystem_counts.get(primary_ecosystem_name, 0)
            total_count = sum(ecosystem_counts.values())
            
            if total_count > 0 and (primary_count / total_count) < threshold:
                is_consistent = False
                recommendations.append(f"Less than {threshold*100}% of technologies are from {primary_ecosystem_name} ecosystem")
        
        return EcosystemConsistencyResult(
            is_consistent=is_consistent,
            primary_ecosystem=primary_ecosystem,
            ecosystem_distribution=dict(ecosystem_counts),
            mixed_ecosystem_technologies=mixed_ecosystem_technologies,
            recommendations=recommendations
        )
    
    def _infer_ecosystem_from_name(self, tech_name: str) -> Optional[str]:
        """Infer ecosystem from technology name."""
        tech_name_lower = tech_name.lower()
        
        if any(keyword in tech_name_lower for keyword in ["aws", "amazon"]):
            return "aws"
        elif any(keyword in tech_name_lower for keyword in ["azure", "microsoft"]):
            return "azure"
        elif any(keyword in tech_name_lower for keyword in ["gcp", "google"]):
            return "gcp"
        else:
            return "open_source"  # Default assumption
    
    def _detect_conflicts(self, tech_entries: Dict[str, Optional[TechEntry]]) -> List[TechnologyConflict]:
        """Detect conflicts between technologies using predefined rules."""
        conflicts = []
        tech_names = list(tech_entries.keys())
        
        # Check pairwise conflicts using rules
        for i, tech1 in enumerate(tech_names):
            for tech2 in tech_names[i+1:]:
                tech1_entry = tech_entries.get(tech1)
                tech2_entry = tech_entries.get(tech2)
                
                # Apply conflict detection rules
                for rule in self.conflict_rules:
                    conflict = self._apply_conflict_rule(tech1, tech2, tech1_entry, tech2_entry, rule)
                    if conflict:
                        conflicts.append(conflict)
        
        # Check compatibility matrices
        matrix_conflicts = self._check_compatibility_matrices(tech_names)
        conflicts.extend(matrix_conflicts)
        
        return conflicts
    
    def _apply_conflict_rule(self, 
                           tech1: str, 
                           tech2: str, 
                           tech1_entry: Optional[TechEntry], 
                           tech2_entry: Optional[TechEntry], 
                           rule: Dict[str, Any]) -> Optional[TechnologyConflict]:
        """Apply a single conflict detection rule."""
        
        for pattern in rule.get("patterns", []):
            if self._matches_conflict_pattern(tech1, tech2, tech1_entry, tech2_entry, pattern):
                return TechnologyConflict(
                    tech1=tech1,
                    tech2=tech2,
                    conflict_type=ConflictType(rule["type"]),
                    severity=ConflictSeverity(rule["severity"]),
                    description=rule["description"],
                    explanation=f"Conflict detected between {tech1} and {tech2}: {rule['description']}",
                    suggested_resolution=rule.get("resolution"),
                    alternatives=[]  # Will be populated later
                )
        
        return None
    
    def _matches_conflict_pattern(self, 
                                tech1: str, 
                                tech2: str, 
                                tech1_entry: Optional[TechEntry], 
                                tech2_entry: Optional[TechEntry], 
                                pattern: Dict[str, Any]) -> bool:
        """Check if technologies match a conflict pattern."""
        
        # Check name-based patterns
        if "tech1_contains" in pattern and "tech2_contains" in pattern:
            tech1_lower = tech1.lower()
            tech2_lower = tech2.lower()
            
            tech1_matches = any(keyword in tech1_lower for keyword in pattern["tech1_contains"])
            tech2_matches = any(keyword in tech2_lower for keyword in pattern["tech2_contains"])
            
            if tech1_matches and tech2_matches:
                return True
        
        # Check license-based patterns
        if "tech1_license" in pattern and "tech2_license" in pattern:
            tech1_license = tech1_entry.license if tech1_entry else "unknown"
            tech2_license = tech2_entry.license if tech2_entry else "unknown"
            
            if (tech1_license.lower() == pattern["tech1_license"].lower() and 
                tech2_license.lower() == pattern["tech2_license"].lower()):
                return True
        
        return False
    
    def _check_compatibility_matrices(self, tech_names: List[str]) -> List[TechnologyConflict]:
        """Check compatibility using stored matrices."""
        conflicts = []
        
        for i, tech1 in enumerate(tech_names):
            for tech2 in tech_names[i+1:]:
                # Check both directions
                matrix = (self.compatibility_matrices.get((tech1, tech2)) or 
                         self.compatibility_matrices.get((tech2, tech1)))
                
                if matrix and not matrix.is_compatible():
                    severity = ConflictSeverity.HIGH if matrix.compatibility_score < 0.3 else ConflictSeverity.MEDIUM
                    
                    conflicts.append(TechnologyConflict(
                        tech1=tech1,
                        tech2=tech2,
                        conflict_type=ConflictType.INTEGRATION_CONFLICT,
                        severity=severity,
                        description=f"Low compatibility score: {matrix.compatibility_score:.2f}",
                        explanation=matrix.notes or f"Technologies {tech1} and {tech2} have low compatibility",
                        suggested_resolution="Consider alternative technologies or additional integration layers"
                    ))
        
        return conflicts
    
    def _resolve_conflicts(self, 
                         tech_stack: List[str], 
                         conflicts: List[TechnologyConflict], 
                         context_priority: Dict[str, float]) -> Tuple[List[str], List[str]]:
        """
        Resolve conflicts using context priority.
        
        Args:
            tech_stack: Original technology stack
            conflicts: Detected conflicts
            context_priority: Priority scores for technologies
        
        Returns:
            Tuple of (validated_technologies, removed_technologies)
        """
        validated_technologies = tech_stack.copy()
        removed_technologies = []
        
        # Group conflicts by severity
        critical_conflicts = [c for c in conflicts if c.severity == ConflictSeverity.CRITICAL]
        high_conflicts = [c for c in conflicts if c.severity == ConflictSeverity.HIGH]
        
        # Resolve critical conflicts first
        for conflict in critical_conflicts:
            tech_to_remove = self._choose_technology_to_remove(conflict, context_priority)
            if tech_to_remove in validated_technologies:
                validated_technologies.remove(tech_to_remove)
                removed_technologies.append(tech_to_remove)
                self.logger.info(f"Removed {tech_to_remove} due to critical conflict with {conflict.tech1 if tech_to_remove == conflict.tech2 else conflict.tech2}")
        
        # Resolve high severity conflicts
        for conflict in high_conflicts:
            # Only resolve if both technologies are still in the stack
            if conflict.tech1 in validated_technologies and conflict.tech2 in validated_technologies:
                tech_to_remove = self._choose_technology_to_remove(conflict, context_priority)
                if tech_to_remove in validated_technologies:
                    validated_technologies.remove(tech_to_remove)
                    removed_technologies.append(tech_to_remove)
                    self.logger.info(f"Removed {tech_to_remove} due to high severity conflict")
        
        return validated_technologies, removed_technologies
    
    def _choose_technology_to_remove(self, 
                                   conflict: TechnologyConflict, 
                                   context_priority: Dict[str, float]) -> str:
        """Choose which technology to remove based on context priority."""
        
        tech1_priority = context_priority.get(conflict.tech1, 0.5)  # Default medium priority
        tech2_priority = context_priority.get(conflict.tech2, 0.5)
        
        # Remove the technology with lower priority
        if tech1_priority < tech2_priority:
            return conflict.tech1
        elif tech2_priority < tech1_priority:
            return conflict.tech2
        else:
            # If priorities are equal, use additional criteria
            # Prefer more established technologies (higher maturity)
            tech1_entry = self.catalog_manager.get_technology_by_id(conflict.tech1)
            tech2_entry = self.catalog_manager.get_technology_by_id(conflict.tech2)
            
            if tech1_entry and tech2_entry:
                # Prefer mature over experimental
                maturity_order = {"deprecated": 0, "experimental": 1, "beta": 2, "stable": 3, "mature": 4}
                tech1_maturity = maturity_order.get(tech1_entry.maturity.value, 2)
                tech2_maturity = maturity_order.get(tech2_entry.maturity.value, 2)
                
                if tech1_maturity < tech2_maturity:
                    return conflict.tech1
                elif tech2_maturity < tech1_maturity:
                    return conflict.tech2
            
            # Default: remove the first technology (arbitrary but consistent)
            return conflict.tech1
    
    def _calculate_compatibility_score(self, 
                                     validated_technologies: List[str], 
                                     conflicts: List[TechnologyConflict], 
                                     ecosystem_result: EcosystemConsistencyResult) -> float:
        """Calculate overall compatibility score."""
        
        base_score = 1.0
        
        # Deduct for conflicts
        for conflict in conflicts:
            if conflict.severity == ConflictSeverity.CRITICAL:
                base_score -= 0.3
            elif conflict.severity == ConflictSeverity.HIGH:
                base_score -= 0.2
            elif conflict.severity == ConflictSeverity.MEDIUM:
                base_score -= 0.1
            elif conflict.severity == ConflictSeverity.LOW:
                base_score -= 0.05
        
        # Deduct for ecosystem inconsistency
        if not ecosystem_result.is_consistent:
            base_score -= 0.2
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, base_score))
    
    def _generate_suggestions(self, 
                            validated_technologies: List[str], 
                            removed_technologies: List[str], 
                            conflicts: List[TechnologyConflict], 
                            ecosystem_result: EcosystemConsistencyResult) -> List[str]:
        """Generate suggestions for improving the tech stack."""
        suggestions = []
        
        if removed_technologies:
            suggestions.append(f"Removed {len(removed_technologies)} technologies due to conflicts")
        
        if not ecosystem_result.is_consistent:
            suggestions.extend(ecosystem_result.recommendations)
        
        if conflicts:
            high_severity_count = len([c for c in conflicts if c.severity in [ConflictSeverity.CRITICAL, ConflictSeverity.HIGH]])
            if high_severity_count > 0:
                suggestions.append(f"Resolved {high_severity_count} high-severity conflicts")
        
        if len(validated_technologies) < 3:
            suggestions.append("Consider adding more technologies to create a comprehensive stack")
        
        return suggestions
    
    def _generate_inclusion_explanations(self, 
                                       validated_technologies: List[str], 
                                       tech_entries: Dict[str, Optional[TechEntry]], 
                                       context_priority: Dict[str, float]) -> Dict[str, str]:
        """Generate explanations for why technologies were included."""
        explanations = {}
        
        for tech in validated_technologies:
            priority = context_priority.get(tech, 0.5)
            tech_entry = tech_entries.get(tech)
            
            if priority >= 0.8:
                explanations[tech] = f"High priority technology (score: {priority:.2f}) - explicitly mentioned in requirements"
            elif priority >= 0.6:
                explanations[tech] = f"Medium priority technology (score: {priority:.2f}) - inferred from context"
            elif tech_entry and tech_entry.ecosystem:
                explanations[tech] = f"Included for ecosystem consistency ({tech_entry.ecosystem.value})"
            else:
                explanations[tech] = "Included - no conflicts detected"
        
        return explanations
    
    def _generate_exclusion_explanations(self, 
                                       removed_technologies: List[str], 
                                       conflicts: List[TechnologyConflict]) -> Dict[str, str]:
        """Generate explanations for why technologies were excluded."""
        explanations = {}
        
        # Map technologies to their conflicts
        tech_conflicts = defaultdict(list)
        for conflict in conflicts:
            tech_conflicts[conflict.tech1].append(conflict)
            tech_conflicts[conflict.tech2].append(conflict)
        
        for tech in removed_technologies:
            tech_conflict_list = tech_conflicts.get(tech, [])
            if tech_conflict_list:
                # Find the highest severity conflict
                highest_severity_conflict = max(tech_conflict_list, key=lambda c: c.severity.value)
                other_tech = highest_severity_conflict.tech2 if highest_severity_conflict.tech1 == tech else highest_severity_conflict.tech1
                explanations[tech] = f"Removed due to {highest_severity_conflict.severity.value} conflict with {other_tech}: {highest_severity_conflict.description}"
            else:
                explanations[tech] = "Removed due to validation rules"
        
        return explanations
    
    def _generate_alternative_suggestions(self, 
                                        removed_technologies: List[str], 
                                        tech_entries: Dict[str, Optional[TechEntry]]) -> Dict[str, List[str]]:
        """Generate alternative technology suggestions for removed technologies."""
        alternatives = {}
        
        for tech in removed_technologies:
            tech_entry = tech_entries.get(tech)
            if tech_entry and tech_entry.alternatives:
                alternatives[tech] = tech_entry.alternatives[:3]  # Limit to top 3 alternatives
            else:
                # Try to suggest alternatives based on category
                alternatives[tech] = self._suggest_alternatives_by_category(tech, tech_entry)
        
        return alternatives
    
    def _suggest_alternatives_by_category(self, 
                                        tech_name: str, 
                                        tech_entry: Optional[TechEntry]) -> List[str]:
        """Suggest alternatives based on technology category."""
        if not tech_entry:
            return []
        
        # Get technologies from the same category
        category_technologies = self.catalog_manager.get_technologies_by_category(tech_entry.category)
        
        # Filter out the current technology and return up to 3 alternatives
        alternatives = [t.name for t in category_technologies if t.name != tech_name][:3]
        
        return alternatives
    
    def add_compatibility_rule(self, 
                             tech1: str, 
                             tech2: str, 
                             compatibility_score: float, 
                             notes: Optional[str] = None) -> None:
        """Add or update a compatibility rule between two technologies."""
        
        matrix = CompatibilityMatrix(
            tech1=tech1,
            tech2=tech2,
            compatibility_score=compatibility_score,
            notes=notes,
            last_updated=datetime.now()
        )
        
        self.compatibility_matrices[(tech1, tech2)] = matrix
        self.logger.info(f"Added compatibility rule: {tech1} <-> {tech2} (score: {compatibility_score})")
    
    def save_compatibility_data(self) -> None:
        """Save compatibility matrices and rules to file."""
        try:
            data = {
                "matrices": {},
                "ecosystem_rules": self.ecosystem_rules,
                "conflict_rules": self.conflict_rules,
                "last_updated": datetime.now().isoformat()
            }
            
            # Convert matrices to serializable format
            for (tech1, tech2), matrix in self.compatibility_matrices.items():
                key = f"{tech1}|{tech2}"
                data["matrices"][key] = {
                    "compatibility_score": matrix.compatibility_score,
                    "notes": matrix.notes,
                    "last_updated": matrix.last_updated.isoformat() if matrix.last_updated else None
                }
            
            # Save to file
            compat_path = Path("Project3/data/compatibility_matrices.json")
            compat_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(compat_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Saved compatibility data with {len(self.compatibility_matrices)} matrices")
            
        except Exception as e:
            self.logger.error(f"Failed to save compatibility data: {e}")
            raise