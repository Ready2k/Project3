"""Intelligent catalog manager with fuzzy matching and auto-addition capabilities."""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime
from difflib import SequenceMatcher
from dataclasses import asdict

from .models import (
    TechEntry, EcosystemType, MaturityLevel, ReviewStatus,
    ValidationResult, FuzzyMatchResult, CatalogStats
)
from app.utils.imports import require_service


class IntelligentCatalogManager:
    """Intelligent technology catalog manager with fuzzy matching and auto-addition."""
    
    def __init__(self, catalog_path: Optional[Path] = None):
        self.catalog_path = catalog_path or Path("Project3/data/technologies.json")
        self.technologies: Dict[str, TechEntry] = {}
        self.name_index: Dict[str, str] = {}  # name/alias -> tech_id mapping
        
        # Get logger from service registry
        self.logger = require_service('logger', context='IntelligentCatalogManager')
        
        self._load_catalog()
        self._build_indexes()
    
    def _load_catalog(self) -> None:
        """Load the technology catalog from file."""
        if not self.catalog_path.exists():
            self.logger.info("Creating new technology catalog")
            self._create_default_catalog()
            return
        
        try:
            with open(self.catalog_path, 'r') as f:
                catalog_data = json.load(f)
            
            # Load existing technologies section if it exists
            if "technologies" in catalog_data:
                for tech_id, tech_data in catalog_data["technologies"].items():
                    try:
                        # Convert old format to new format if needed
                        if "id" not in tech_data:
                            tech_data["id"] = tech_id
                        
                        tech_entry = TechEntry.from_dict(tech_data)
                        self.technologies[tech_id] = tech_entry
                    except Exception as e:
                        self.logger.error(f"Failed to load technology {tech_id}: {e}")
            
            self.logger.info(f"Loaded {len(self.technologies)} technologies from catalog")
            
        except Exception as e:
            self.logger.error(f"Failed to load catalog: {e}")
            self._create_default_catalog()
    
    def _create_default_catalog(self) -> None:
        """Create a default catalog with some basic technologies."""
        default_techs = [
            TechEntry(
                id="fastapi",
                name="FastAPI",
                canonical_name="FastAPI",
                category="frameworks",
                description="Modern, fast web framework for building APIs with Python",
                aliases=["fast-api", "fast_api"],
                ecosystem=EcosystemType.OPEN_SOURCE,
                integrates_with=["python", "pydantic", "uvicorn"],
                alternatives=["django", "flask"],
                tags=["python", "api", "async", "web"],
                use_cases=["rest_api", "microservices", "web_backend"],
                license="MIT",
                maturity=MaturityLevel.STABLE
            ),
            TechEntry(
                id="langchain",
                name="LangChain",
                canonical_name="LangChain",
                category="agentic",
                description="Framework for developing applications powered by language models",
                aliases=["lang-chain", "lang_chain"],
                ecosystem=EcosystemType.OPEN_SOURCE,
                integrates_with=["openai", "python", "faiss"],
                alternatives=["llamaindex", "semantic_kernel"],
                tags=["llm", "ai", "agents", "python"],
                use_cases=["chatbots", "document_qa", "agents"],
                license="MIT",
                maturity=MaturityLevel.STABLE
            ),
            TechEntry(
                id="aws",
                name="AWS",
                canonical_name="Amazon Web Services",
                category="cloud",
                description="Amazon's comprehensive cloud computing platform",
                aliases=["amazon_web_services", "amazon-web-services"],
                ecosystem=EcosystemType.AWS,
                integrates_with=["python", "docker", "terraform"],
                alternatives=["azure", "gcp"],
                tags=["cloud", "infrastructure", "serverless"],
                use_cases=["cloud_hosting", "serverless", "storage"],
                license="Commercial",
                maturity=MaturityLevel.MATURE
            )
        ]
        
        for tech in default_techs:
            self.technologies[tech.id] = tech
        
        self._save_catalog()
    
    def _build_indexes(self) -> None:
        """Build search indexes for fast lookup."""
        self.name_index.clear()
        
        for tech_id, tech in self.technologies.items():
            # Index canonical name
            self.name_index[tech.canonical_name.lower()] = tech_id
            
            # Index display name if different
            if tech.name.lower() != tech.canonical_name.lower():
                self.name_index[tech.name.lower()] = tech_id
            
            # Index aliases
            for alias in tech.aliases:
                self.name_index[alias.lower()] = tech_id
    
    def lookup_technology(self, tech_name: str, fuzzy_threshold: float = 0.8) -> Optional[FuzzyMatchResult]:
        """
        Lookup technology with fuzzy matching.
        
        Args:
            tech_name: Technology name to search for
            fuzzy_threshold: Minimum similarity score for fuzzy matches (0.0-1.0)
        
        Returns:
            FuzzyMatchResult if found, None otherwise
        """
        tech_name_lower = tech_name.lower().strip()
        
        # Exact name match
        if tech_name_lower in self.name_index:
            tech_id = self.name_index[tech_name_lower]
            tech_entry = self.technologies[tech_id]
            return FuzzyMatchResult(
                tech_entry=tech_entry,
                match_score=1.0,
                match_type="exact",
                matched_text=tech_name
            )
        
        # Fuzzy matching
        best_match = None
        best_score = 0.0
        
        for indexed_name, tech_id in self.name_index.items():
            similarity = SequenceMatcher(None, tech_name_lower, indexed_name).ratio()
            
            if similarity > best_score and similarity >= fuzzy_threshold:
                best_score = similarity
                tech_entry = self.technologies[tech_id]
                
                # Determine match type
                match_type = "fuzzy_name"
                if indexed_name in [alias.lower() for alias in tech_entry.aliases]:
                    match_type = "fuzzy_alias"
                
                best_match = FuzzyMatchResult(
                    tech_entry=tech_entry,
                    match_score=similarity,
                    match_type=match_type,
                    matched_text=indexed_name
                )
        
        return best_match
    
    def auto_add_technology(self, 
                          tech_name: str, 
                          context: Dict[str, Any],
                          confidence_score: float = 0.7) -> TechEntry:
        """
        Automatically add a missing technology to the catalog.
        
        Args:
            tech_name: Name of the technology to add
            context: Context information about where/how it was mentioned
            confidence_score: Confidence in the auto-generated entry
        
        Returns:
            The created TechEntry
        """
        # Generate unique ID
        tech_id = self._generate_tech_id(tech_name)
        
        # Extract metadata from context
        category = self._infer_category(tech_name, context)
        ecosystem = self._infer_ecosystem(tech_name, context)
        description = self._generate_description(tech_name, context)
        
        # Create new technology entry
        tech_entry = TechEntry(
            id=tech_id,
            name=tech_name,
            canonical_name=tech_name,
            category=category,
            description=description,
            ecosystem=ecosystem,
            confidence_score=confidence_score,
            auto_generated=True,
            pending_review=True,
            source_context=json.dumps(context),
            review_status=ReviewStatus.PENDING
        )
        
        # Add to catalog
        self.technologies[tech_id] = tech_entry
        self._rebuild_indexes()
        self._save_catalog()
        
        self.logger.info(f"Auto-added technology: {tech_name} (ID: {tech_id})")
        return tech_entry
    
    def _generate_tech_id(self, tech_name: str) -> str:
        """Generate a unique ID for a technology."""
        # Create base ID from name
        base_id = tech_name.lower().replace(" ", "_").replace("-", "_")
        base_id = "".join(c for c in base_id if c.isalnum() or c == "_")
        
        # Ensure uniqueness
        if base_id not in self.technologies:
            return base_id
        
        # Add suffix if needed
        counter = 1
        while f"{base_id}_{counter}" in self.technologies:
            counter += 1
        
        return f"{base_id}_{counter}"
    
    def _infer_category(self, tech_name: str, context: Dict[str, Any]) -> str:
        """Infer technology category from name and context."""
        tech_name_lower = tech_name.lower()
        
        # Category inference rules
        if any(keyword in tech_name_lower for keyword in ["aws", "amazon", "azure", "gcp", "google cloud"]):
            return "cloud"
        elif any(keyword in tech_name_lower for keyword in ["api", "rest", "graphql", "fastapi", "flask", "django"]):
            return "frameworks"
        elif any(keyword in tech_name_lower for keyword in ["langchain", "crew", "autogen", "agent"]):
            return "agentic"
        elif any(keyword in tech_name_lower for keyword in ["postgres", "mysql", "redis", "mongodb"]):
            return "databases"
        elif any(keyword in tech_name_lower for keyword in ["docker", "kubernetes", "terraform"]):
            return "infrastructure"
        elif any(keyword in tech_name_lower for keyword in ["python", "javascript", "java", "go"]):
            return "languages"
        elif any(keyword in tech_name_lower for keyword in ["openai", "claude", "gpt", "llm"]):
            return "ai"
        else:
            # Try to infer from context
            context_text = str(context).lower()
            if "cloud" in context_text:
                return "cloud"
            elif "framework" in context_text:
                return "frameworks"
            elif "database" in context_text:
                return "databases"
            else:
                return "integration"  # Default category
    
    def _infer_ecosystem(self, tech_name: str, context: Dict[str, Any]) -> Optional[EcosystemType]:
        """Infer technology ecosystem from name and context."""
        tech_name_lower = tech_name.lower()
        
        if any(keyword in tech_name_lower for keyword in ["aws", "amazon"]):
            return EcosystemType.AWS
        elif any(keyword in tech_name_lower for keyword in ["azure", "microsoft"]):
            return EcosystemType.AZURE
        elif any(keyword in tech_name_lower for keyword in ["gcp", "google cloud", "google"]):
            return EcosystemType.GCP
        elif any(keyword in tech_name_lower for keyword in ["open source", "mit", "apache"]):
            return EcosystemType.OPEN_SOURCE
        else:
            # Try to infer from context
            context_text = str(context).lower()
            if "aws" in context_text:
                return EcosystemType.AWS
            elif "azure" in context_text:
                return EcosystemType.AZURE
            elif "gcp" in context_text or "google" in context_text:
                return EcosystemType.GCP
            else:
                return None
    
    def _generate_description(self, tech_name: str, context: Dict[str, Any]) -> str:
        """Generate a basic description for auto-added technology."""
        return f"Technology component: {tech_name}"
    
    def validate_catalog_entry(self, tech_entry: TechEntry) -> ValidationResult:
        """Validate a catalog entry for completeness and accuracy."""
        errors = []
        warnings = []
        suggestions = []
        
        # Required field validation
        if not tech_entry.name.strip():
            errors.append("Technology name is required")
        
        if not tech_entry.category.strip():
            errors.append("Category is required")
        
        if not tech_entry.description.strip():
            warnings.append("Description is empty")
        
        # Consistency validation
        if tech_entry.ecosystem == EcosystemType.AWS and not any(
            aws_indicator in tech_entry.name.lower() 
            for aws_indicator in ["aws", "amazon"]
        ):
            warnings.append("Technology marked as AWS ecosystem but name doesn't indicate AWS")
        
        # Completeness validation
        if not tech_entry.integrates_with:
            suggestions.append("Consider adding integration information")
        
        if not tech_entry.alternatives:
            suggestions.append("Consider adding alternative technologies")
        
        if not tech_entry.use_cases:
            suggestions.append("Consider adding use cases")
        
        # Auto-generated entry validation
        if tech_entry.auto_generated and tech_entry.confidence_score < 0.5:
            warnings.append("Low confidence auto-generated entry needs review")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def get_pending_review_queue(self) -> List[TechEntry]:
        """Get all technologies pending review."""
        return [
            tech for tech in self.technologies.values()
            if tech.pending_review or tech.review_status == ReviewStatus.PENDING
        ]
    
    def approve_technology(self, tech_id: str, reviewer: str, notes: Optional[str] = None) -> bool:
        """Approve a technology entry."""
        if tech_id not in self.technologies:
            return False
        
        tech_entry = self.technologies[tech_id]
        tech_entry.approve_review(reviewer, notes)
        self._save_catalog()
        
        self.logger.info(f"Approved technology: {tech_entry.name} by {reviewer}")
        return True
    
    def reject_technology(self, tech_id: str, reviewer: str, notes: str) -> bool:
        """Reject a technology entry."""
        if tech_id not in self.technologies:
            return False
        
        tech_entry = self.technologies[tech_id]
        tech_entry.reject_review(reviewer, notes)
        self._save_catalog()
        
        self.logger.info(f"Rejected technology: {tech_entry.name} by {reviewer}")
        return True
    
    def request_technology_update(self, tech_id: str, reviewer: str, notes: str) -> bool:
        """Request updates to a technology entry."""
        if tech_id not in self.technologies:
            return False
        
        tech_entry = self.technologies[tech_id]
        tech_entry.request_update(reviewer, notes)
        self._save_catalog()
        
        self.logger.info(f"Requested update for technology: {tech_entry.name} by {reviewer}")
        return True
    
    def update_technology(self, tech_id: str, updates: Dict[str, Any]) -> bool:
        """Update a technology entry."""
        if tech_id not in self.technologies:
            return False
        
        tech_entry = self.technologies[tech_id]
        
        # Apply updates
        for field, value in updates.items():
            if hasattr(tech_entry, field):
                setattr(tech_entry, field, value)
        
        tech_entry.last_updated = datetime.now()
        
        # Rebuild indexes if name/aliases changed
        if any(field in updates for field in ["name", "canonical_name", "aliases"]):
            self._rebuild_indexes()
        
        self._save_catalog()
        
        self.logger.info(f"Updated technology: {tech_entry.name}")
        return True
    
    def add_technology_alias(self, tech_id: str, alias: str) -> bool:
        """Add an alias to a technology."""
        if tech_id not in self.technologies:
            return False
        
        tech_entry = self.technologies[tech_id]
        tech_entry.add_alias(alias)
        
        # Update index
        self.name_index[alias.lower()] = tech_id
        
        self._save_catalog()
        return True
    
    def get_catalog_statistics(self) -> CatalogStats:
        """Get comprehensive catalog statistics."""
        stats = CatalogStats(
            total_entries=len(self.technologies),
            pending_review=0,
            auto_generated=0,
            validation_errors=0
        )
        
        for tech in self.technologies.values():
            if tech.pending_review:
                stats.pending_review += 1
            
            if tech.auto_generated:
                stats.auto_generated += 1
            
            if tech.validation_errors:
                stats.validation_errors += 1
            
            # Ecosystem stats
            if tech.ecosystem:
                ecosystem_name = tech.ecosystem.value
                stats.by_ecosystem[ecosystem_name] = stats.by_ecosystem.get(ecosystem_name, 0) + 1
            
            # Category stats
            stats.by_category[tech.category] = stats.by_category.get(tech.category, 0) + 1
            
            # Maturity stats
            maturity_name = tech.maturity.value
            stats.by_maturity[maturity_name] = stats.by_maturity.get(maturity_name, 0) + 1
        
        return stats
    
    def validate_catalog_consistency(self) -> ValidationResult:
        """Validate the entire catalog for consistency."""
        errors = []
        warnings = []
        suggestions = []
        
        # Check for duplicate names/aliases
        seen_names = set()
        for tech in self.technologies.values():
            all_names = [tech.name, tech.canonical_name] + tech.aliases
            for name in all_names:
                name_lower = name.lower()
                if name_lower in seen_names:
                    errors.append(f"Duplicate name/alias found: {name}")
                seen_names.add(name_lower)
        
        # Check integration references
        all_tech_names = {tech.name.lower() for tech in self.technologies.values()}
        for tech in self.technologies.values():
            for integration in tech.integrates_with:
                if integration.lower() not in all_tech_names:
                    warnings.append(f"{tech.name} references unknown integration: {integration}")
            
            for alternative in tech.alternatives:
                if alternative.lower() not in all_tech_names:
                    warnings.append(f"{tech.name} references unknown alternative: {alternative}")
        
        # Check pending reviews
        pending_count = len(self.get_pending_review_queue())
        if pending_count > 0:
            suggestions.append(f"{pending_count} technologies pending review")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _rebuild_indexes(self) -> None:
        """Rebuild all search indexes."""
        self._build_indexes()
    
    def _save_catalog(self) -> None:
        """Save the catalog to file."""
        try:
            # Load existing catalog structure
            catalog_data = {}
            if self.catalog_path.exists() and self.catalog_path.stat().st_size > 0:
                with open(self.catalog_path, 'r') as f:
                    catalog_data = json.load(f)
            
            # Update technologies section
            catalog_data["technologies"] = {}
            for tech_id, tech in self.technologies.items():
                catalog_data["technologies"][tech_id] = tech.to_dict()
            
            # Update metadata
            if "metadata" not in catalog_data:
                catalog_data["metadata"] = {}
            
            catalog_data["metadata"]["total_technologies"] = len(self.technologies)
            catalog_data["metadata"]["last_auto_update"] = datetime.now().isoformat()
            
            # Ensure directory exists
            self.catalog_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to file
            with open(self.catalog_path, 'w') as f:
                json.dump(catalog_data, f, indent=2)
            
            self.logger.debug(f"Saved catalog with {len(self.technologies)} technologies")
            
        except Exception as e:
            self.logger.error(f"Failed to save catalog: {e}")
            raise
    
    def get_technology_by_id(self, tech_id: str) -> Optional[TechEntry]:
        """Get technology by ID."""
        return self.technologies.get(tech_id)
    
    def get_technologies_by_category(self, category: str) -> List[TechEntry]:
        """Get all technologies in a category."""
        return [tech for tech in self.technologies.values() if tech.category == category]
    
    def get_technologies_by_ecosystem(self, ecosystem: EcosystemType) -> List[TechEntry]:
        """Get all technologies in an ecosystem."""
        return [tech for tech in self.technologies.values() if tech.ecosystem == ecosystem]
    
    def search_technologies(self, query: str, limit: int = 10) -> List[FuzzyMatchResult]:
        """Search technologies with fuzzy matching."""
        results = []
        query_lower = query.lower()
        
        for tech in self.technologies.values():
            # Check name matches
            name_score = SequenceMatcher(None, query_lower, tech.name.lower()).ratio()
            if name_score > 0.3:
                results.append(FuzzyMatchResult(
                    tech_entry=tech,
                    match_score=name_score,
                    match_type="name_search",
                    matched_text=tech.name
                ))
            
            # Check alias matches
            for alias in tech.aliases:
                alias_score = SequenceMatcher(None, query_lower, alias.lower()).ratio()
                if alias_score > 0.3:
                    results.append(FuzzyMatchResult(
                        tech_entry=tech,
                        match_score=alias_score,
                        match_type="alias_search",
                        matched_text=alias
                    ))
        
        # Sort by score and return top results
        results.sort(key=lambda x: x.match_score, reverse=True)
        return results[:limit]