"""Catalog validation and consistency checking mechanisms."""

from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re

from .models import TechEntry, EcosystemType, MaturityLevel, ReviewStatus, ValidationResult
from app.utils.imports import require_service


@dataclass
class ConsistencyCheck:
    """Result of a consistency check."""
    check_name: str
    passed: bool
    message: str
    severity: str  # "error", "warning", "info"
    affected_technologies: List[str] = field(default_factory=list)


@dataclass
class CatalogHealth:
    """Overall catalog health assessment."""
    overall_score: float  # 0.0-1.0
    total_checks: int
    passed_checks: int
    failed_checks: int
    warnings: int
    errors: int
    recommendations: List[str] = field(default_factory=list)


class CatalogValidator:
    """Comprehensive catalog validation and consistency checking."""
    
    def __init__(self):
        self.logger = require_service('logger', context='CatalogValidator')
        
        # Validation rules configuration
        self.min_description_length = 10
        self.max_description_length = 500
        self.required_fields = ["name", "category", "description"]
        self.valid_categories = {
            "agentic", "ai", "automation", "cloud", "communication", 
            "data", "databases", "frameworks", "infrastructure", 
            "integration", "languages", "monitoring", "processing",
            "reasoning", "scheduling", "search", "security", 
            "storage", "testing", "validation"
        }
        
        # Ecosystem consistency rules
        self.ecosystem_indicators = {
            EcosystemType.AWS: ["aws", "amazon"],
            EcosystemType.AZURE: ["azure", "microsoft"],
            EcosystemType.GCP: ["gcp", "google cloud", "google"],
        }
    
    def validate_technology_entry(self, tech_entry: TechEntry) -> ValidationResult:
        """Comprehensive validation of a single technology entry."""
        errors = []
        warnings = []
        suggestions = []
        
        # Required field validation
        for field in self.required_fields:
            value = getattr(tech_entry, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                errors.append(f"Required field '{field}' is missing or empty")
        
        # Name validation
        if tech_entry.name:
            if len(tech_entry.name) < 2:
                errors.append("Technology name is too short (minimum 2 characters)")
            elif len(tech_entry.name) > 100:
                warnings.append("Technology name is very long (over 100 characters)")
            
            # Check for invalid characters
            if re.search(r'[<>"\']', tech_entry.name):
                errors.append("Technology name contains invalid characters")
        
        # Description validation
        if tech_entry.description:
            desc_len = len(tech_entry.description.strip())
            if desc_len < self.min_description_length:
                warnings.append(f"Description is too short (minimum {self.min_description_length} characters)")
            elif desc_len > self.max_description_length:
                warnings.append(f"Description is too long (maximum {self.max_description_length} characters)")
        
        # Category validation
        if tech_entry.category and tech_entry.category not in self.valid_categories:
            errors.append(f"Invalid category '{tech_entry.category}'. Valid categories: {', '.join(sorted(self.valid_categories))}")
        
        # Ecosystem consistency validation
        ecosystem_warnings = self._validate_ecosystem_consistency(tech_entry)
        warnings.extend(ecosystem_warnings)
        
        # Alias validation
        alias_issues = self._validate_aliases(tech_entry)
        warnings.extend(alias_issues)
        
        # Integration validation
        integration_suggestions = self._validate_integrations(tech_entry)
        suggestions.extend(integration_suggestions)
        
        # Confidence score validation
        if not (0.0 <= tech_entry.confidence_score <= 1.0):
            errors.append("Confidence score must be between 0.0 and 1.0")
        
        # Auto-generated entry validation
        if tech_entry.auto_generated:
            auto_gen_issues = self._validate_auto_generated_entry(tech_entry)
            warnings.extend(auto_gen_issues)
        
        # Review status validation
        review_issues = self._validate_review_status(tech_entry)
        warnings.extend(review_issues)
        
        # Completeness suggestions
        completeness_suggestions = self._suggest_completeness_improvements(tech_entry)
        suggestions.extend(completeness_suggestions)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _validate_ecosystem_consistency(self, tech_entry: TechEntry) -> List[str]:
        """Validate ecosystem consistency with technology name and metadata."""
        warnings = []
        
        if not tech_entry.ecosystem:
            return warnings
        
        tech_name_lower = tech_entry.name.lower()
        expected_indicators = self.ecosystem_indicators.get(tech_entry.ecosystem, [])
        
        # Check if name contains ecosystem indicators
        has_indicator = any(indicator in tech_name_lower for indicator in expected_indicators)
        
        if not has_indicator:
            warnings.append(
                f"Technology '{tech_entry.name}' is marked as {tech_entry.ecosystem.value} "
                f"but name doesn't contain expected indicators: {', '.join(expected_indicators)}"
            )
        
        # Check for conflicting ecosystem indicators
        for ecosystem, indicators in self.ecosystem_indicators.items():
            if ecosystem != tech_entry.ecosystem:
                if any(indicator in tech_name_lower for indicator in indicators):
                    warnings.append(
                        f"Technology name contains {ecosystem.value} indicators "
                        f"but is marked as {tech_entry.ecosystem.value}"
                    )
        
        return warnings
    
    def _validate_aliases(self, tech_entry: TechEntry) -> List[str]:
        """Validate technology aliases."""
        warnings = []
        
        # Check for duplicate aliases
        seen_aliases = set()
        for alias in tech_entry.aliases:
            alias_lower = alias.lower()
            if alias_lower in seen_aliases:
                warnings.append(f"Duplicate alias found: {alias}")
            seen_aliases.add(alias_lower)
            
            # Check if alias is same as name
            if alias_lower == tech_entry.name.lower():
                warnings.append(f"Alias '{alias}' is the same as technology name")
        
        # Check alias quality
        for alias in tech_entry.aliases:
            if len(alias) < 2:
                warnings.append(f"Alias '{alias}' is too short")
            elif re.search(r'[<>"\']', alias):
                warnings.append(f"Alias '{alias}' contains invalid characters")
        
        return warnings
    
    def _validate_integrations(self, tech_entry: TechEntry) -> List[str]:
        """Validate integration information."""
        suggestions = []
        
        # Check for common integration patterns
        tech_name_lower = tech_entry.name.lower()
        
        # Suggest common integrations based on technology type
        if tech_entry.category == "frameworks" and "python" not in [i.lower() for i in tech_entry.integrates_with]:
            if any(indicator in tech_name_lower for indicator in ["fastapi", "django", "flask"]):
                suggestions.append("Consider adding 'python' to integrations")
        
        if tech_entry.category == "cloud" and not tech_entry.integrates_with:
            suggestions.append("Cloud technologies typically integrate with multiple services")
        
        if tech_entry.category == "agentic" and "openai" not in [i.lower() for i in tech_entry.integrates_with]:
            suggestions.append("Consider adding LLM providers to integrations")
        
        return suggestions
    
    def _validate_auto_generated_entry(self, tech_entry: TechEntry) -> List[str]:
        """Validate auto-generated entries."""
        warnings = []
        
        if tech_entry.confidence_score < 0.5:
            warnings.append("Low confidence auto-generated entry needs manual review")
        
        if not tech_entry.source_context:
            warnings.append("Auto-generated entry missing source context")
        
        if tech_entry.review_status == ReviewStatus.PENDING and tech_entry.added_date:
            days_pending = (datetime.now() - tech_entry.added_date).days
            if days_pending > 7:
                warnings.append(f"Entry has been pending review for {days_pending} days")
        
        return warnings
    
    def _validate_review_status(self, tech_entry: TechEntry) -> List[str]:
        """Validate review status consistency."""
        warnings = []
        
        if tech_entry.pending_review and tech_entry.review_status == ReviewStatus.APPROVED:
            warnings.append("Entry marked as pending review but status is approved")
        
        if not tech_entry.pending_review and tech_entry.review_status == ReviewStatus.PENDING:
            warnings.append("Entry not marked as pending review but status is pending")
        
        if tech_entry.review_status == ReviewStatus.REJECTED and tech_entry.confidence_score > 0.8:
            warnings.append("Rejected entry has high confidence score")
        
        return warnings
    
    def _suggest_completeness_improvements(self, tech_entry: TechEntry) -> List[str]:
        """Suggest improvements for entry completeness."""
        suggestions = []
        
        if not tech_entry.integrates_with:
            suggestions.append("Add integration information to improve usefulness")
        
        if not tech_entry.alternatives:
            suggestions.append("Add alternative technologies for better recommendations")
        
        if not tech_entry.use_cases:
            suggestions.append("Add use cases to help with technology selection")
        
        if not tech_entry.tags:
            suggestions.append("Add tags to improve searchability")
        
        if tech_entry.license == "unknown":
            suggestions.append("Specify license information for compliance")
        
        if tech_entry.maturity == MaturityLevel.STABLE and not tech_entry.integrates_with:
            suggestions.append("Stable technologies should have integration information")
        
        return suggestions
    
    def validate_catalog_consistency(self, technologies: Dict[str, TechEntry]) -> List[ConsistencyCheck]:
        """Perform comprehensive catalog consistency checks."""
        checks = []
        
        # Check for duplicate names
        checks.extend(self._check_duplicate_names(technologies))
        
        # Check integration references
        checks.extend(self._check_integration_references(technologies))
        
        # Check alternative references
        checks.extend(self._check_alternative_references(technologies))
        
        # Check ecosystem consistency
        checks.extend(self._check_ecosystem_distribution(technologies))
        
        # Check category distribution
        checks.extend(self._check_category_distribution(technologies))
        
        # Check review queue health
        checks.extend(self._check_review_queue_health(technologies))
        
        # Check auto-generated entry quality
        checks.extend(self._check_auto_generated_quality(technologies))
        
        return checks
    
    def _check_duplicate_names(self, technologies: Dict[str, TechEntry]) -> List[ConsistencyCheck]:
        """Check for duplicate technology names and aliases."""
        checks = []
        name_to_techs = {}
        
        # Collect all names and aliases
        for tech_id, tech in technologies.items():
            all_names = [tech.name, tech.canonical_name] + tech.aliases
            for name in all_names:
                name_lower = name.lower().strip()
                if name_lower:
                    if name_lower not in name_to_techs:
                        name_to_techs[name_lower] = []
                    name_to_techs[name_lower].append((tech_id, tech.name))
        
        # Find duplicates
        duplicates = {name: techs for name, techs in name_to_techs.items() if len(techs) > 1}
        
        if duplicates:
            for name, techs in duplicates.items():
                tech_names = [f"{tech_name} ({tech_id})" for tech_id, tech_name in techs]
                checks.append(ConsistencyCheck(
                    check_name="duplicate_names",
                    passed=False,
                    message=f"Duplicate name/alias '{name}' found in: {', '.join(tech_names)}",
                    severity="error",
                    affected_technologies=[tech_id for tech_id, _ in techs]
                ))
        else:
            checks.append(ConsistencyCheck(
                check_name="duplicate_names",
                passed=True,
                message="No duplicate names or aliases found",
                severity="info"
            ))
        
        return checks
    
    def _check_integration_references(self, technologies: Dict[str, TechEntry]) -> List[ConsistencyCheck]:
        """Check that integration references point to existing technologies."""
        checks = []
        all_tech_names = {tech.name.lower() for tech in technologies.values()}
        broken_refs = []
        
        for tech_id, tech in technologies.items():
            for integration in tech.integrates_with:
                if integration.lower() not in all_tech_names:
                    broken_refs.append(f"{tech.name} -> {integration}")
        
        if broken_refs:
            checks.append(ConsistencyCheck(
                check_name="integration_references",
                passed=False,
                message=f"Broken integration references: {', '.join(broken_refs[:5])}{'...' if len(broken_refs) > 5 else ''}",
                severity="warning"
            ))
        else:
            checks.append(ConsistencyCheck(
                check_name="integration_references",
                passed=True,
                message="All integration references are valid",
                severity="info"
            ))
        
        return checks
    
    def _check_alternative_references(self, technologies: Dict[str, TechEntry]) -> List[ConsistencyCheck]:
        """Check that alternative references point to existing technologies."""
        checks = []
        all_tech_names = {tech.name.lower() for tech in technologies.values()}
        broken_refs = []
        
        for tech_id, tech in technologies.items():
            for alternative in tech.alternatives:
                if alternative.lower() not in all_tech_names:
                    broken_refs.append(f"{tech.name} -> {alternative}")
        
        if broken_refs:
            checks.append(ConsistencyCheck(
                check_name="alternative_references",
                passed=False,
                message=f"Broken alternative references: {', '.join(broken_refs[:5])}{'...' if len(broken_refs) > 5 else ''}",
                severity="warning"
            ))
        else:
            checks.append(ConsistencyCheck(
                check_name="alternative_references",
                passed=True,
                message="All alternative references are valid",
                severity="info"
            ))
        
        return checks
    
    def _check_ecosystem_distribution(self, technologies: Dict[str, TechEntry]) -> List[ConsistencyCheck]:
        """Check ecosystem distribution and consistency."""
        checks = []
        ecosystem_counts = {}
        
        for tech in technologies.values():
            if tech.ecosystem:
                ecosystem_counts[tech.ecosystem.value] = ecosystem_counts.get(tech.ecosystem.value, 0) + 1
        
        total_with_ecosystem = sum(ecosystem_counts.values())
        total_techs = len(technologies)
        
        if total_with_ecosystem < total_techs * 0.5:
            checks.append(ConsistencyCheck(
                check_name="ecosystem_coverage",
                passed=False,
                message=f"Only {total_with_ecosystem}/{total_techs} technologies have ecosystem information",
                severity="warning"
            ))
        else:
            checks.append(ConsistencyCheck(
                check_name="ecosystem_coverage",
                passed=True,
                message=f"Good ecosystem coverage: {total_with_ecosystem}/{total_techs} technologies",
                severity="info"
            ))
        
        return checks
    
    def _check_category_distribution(self, technologies: Dict[str, TechEntry]) -> List[ConsistencyCheck]:
        """Check category distribution for balance."""
        checks = []
        category_counts = {}
        
        for tech in technologies.values():
            category_counts[tech.category] = category_counts.get(tech.category, 0) + 1
        
        # Check for categories with too many or too few technologies
        total_techs = len(technologies)
        imbalanced_categories = []
        
        for category, count in category_counts.items():
            percentage = (count / total_techs) * 100
            if percentage > 30:  # More than 30% in one category
                imbalanced_categories.append(f"{category} ({count} techs, {percentage:.1f}%)")
        
        if imbalanced_categories:
            checks.append(ConsistencyCheck(
                check_name="category_balance",
                passed=False,
                message=f"Imbalanced categories: {', '.join(imbalanced_categories)}",
                severity="warning"
            ))
        else:
            checks.append(ConsistencyCheck(
                check_name="category_balance",
                passed=True,
                message="Categories are well balanced",
                severity="info"
            ))
        
        return checks
    
    def _check_review_queue_health(self, technologies: Dict[str, TechEntry]) -> List[ConsistencyCheck]:
        """Check review queue health and aging."""
        checks = []
        pending_count = 0
        old_pending = []
        
        for tech in technologies.values():
            if tech.pending_review or tech.review_status == ReviewStatus.PENDING:
                pending_count += 1
                
                if tech.added_date:
                    days_pending = (datetime.now() - tech.added_date).days
                    if days_pending > 14:  # More than 2 weeks
                        old_pending.append(f"{tech.name} ({days_pending} days)")
        
        if pending_count > 10:
            checks.append(ConsistencyCheck(
                check_name="review_queue_size",
                passed=False,
                message=f"Large review queue: {pending_count} technologies pending",
                severity="warning"
            ))
        else:
            checks.append(ConsistencyCheck(
                check_name="review_queue_size",
                passed=True,
                message=f"Manageable review queue: {pending_count} technologies pending",
                severity="info"
            ))
        
        if old_pending:
            checks.append(ConsistencyCheck(
                check_name="review_queue_aging",
                passed=False,
                message=f"Old pending reviews: {', '.join(old_pending[:3])}{'...' if len(old_pending) > 3 else ''}",
                severity="warning"
            ))
        
        return checks
    
    def _check_auto_generated_quality(self, technologies: Dict[str, TechEntry]) -> List[ConsistencyCheck]:
        """Check quality of auto-generated entries."""
        checks = []
        auto_gen_count = 0
        low_confidence = []
        
        for tech in technologies.values():
            if tech.auto_generated:
                auto_gen_count += 1
                if tech.confidence_score < 0.6:
                    low_confidence.append(f"{tech.name} ({tech.confidence_score:.2f})")
        
        if low_confidence:
            checks.append(ConsistencyCheck(
                check_name="auto_generated_quality",
                passed=False,
                message=f"Low confidence auto-generated entries: {', '.join(low_confidence[:3])}{'...' if len(low_confidence) > 3 else ''}",
                severity="warning"
            ))
        elif auto_gen_count > 0:
            checks.append(ConsistencyCheck(
                check_name="auto_generated_quality",
                passed=True,
                message=f"Good quality auto-generated entries: {auto_gen_count} total",
                severity="info"
            ))
        
        return checks
    
    def assess_catalog_health(self, technologies: Dict[str, TechEntry]) -> CatalogHealth:
        """Assess overall catalog health."""
        # Run all consistency checks
        checks = self.validate_catalog_consistency(technologies)
        
        # Count results
        total_checks = len(checks)
        passed_checks = sum(1 for check in checks if check.passed)
        failed_checks = total_checks - passed_checks
        
        errors = sum(1 for check in checks if check.severity == "error")
        warnings = sum(1 for check in checks if check.severity == "warning")
        
        # Calculate overall score
        if total_checks == 0:
            overall_score = 1.0
        else:
            # Weight errors more heavily than warnings
            error_penalty = errors * 0.3
            warning_penalty = warnings * 0.1
            max_penalty = total_checks * 0.3
            
            penalty = min(error_penalty + warning_penalty, max_penalty)
            overall_score = max(0.0, 1.0 - (penalty / max_penalty) if max_penalty > 0 else 1.0)
        
        # Generate recommendations
        recommendations = []
        if errors > 0:
            recommendations.append(f"Fix {errors} critical errors to improve catalog reliability")
        if warnings > 5:
            recommendations.append(f"Address {warnings} warnings to improve catalog quality")
        if failed_checks > total_checks * 0.3:
            recommendations.append("Consider reviewing catalog maintenance procedures")
        
        # Add specific recommendations based on checks
        for check in checks:
            if not check.passed and check.severity == "error":
                recommendations.append(f"Priority: {check.message}")
        
        return CatalogHealth(
            overall_score=overall_score,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warnings=warnings,
            errors=errors,
            recommendations=recommendations[:10]  # Limit to top 10
        )