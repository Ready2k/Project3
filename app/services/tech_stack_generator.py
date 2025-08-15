"""Intelligent tech stack generation service using LLM analysis."""

from typing import Dict, List, Any, Optional, Set
import json
from pathlib import Path

from app.pattern.matcher import MatchResult
from app.llm.base import LLMProvider
from app.utils.logger import app_logger
from app.utils.audit import log_llm_call
from datetime import datetime
import shutil


class TechStackGenerator:
    """Service for generating intelligent, context-aware technology stacks."""
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None, auto_update_catalog: bool = True):
        """Initialize tech stack generator.
        
        Args:
            llm_provider: LLM provider for intelligent analysis
            auto_update_catalog: Whether to automatically update catalog with new technologies
        """
        self.llm_provider = llm_provider
        self.auto_update_catalog = auto_update_catalog
        
        # Load technology catalog
        self.technology_catalog = self._load_technology_catalog()
        self.available_technologies = self._build_category_index()
        
    def _load_technology_catalog(self) -> Dict[str, Any]:
        """Load technology catalog from JSON file.
        
        Returns:
            Technology catalog dictionary
        """
        catalog_path = Path("data/technologies.json")
        
        if not catalog_path.exists():
            app_logger.warning("Technology catalog not found, falling back to pattern extraction")
            return self._fallback_to_pattern_extraction()
        
        try:
            with open(catalog_path, 'r') as f:
                catalog = json.load(f)
            
            tech_count = len(catalog.get("technologies", {}))
            app_logger.info(f"Loaded {tech_count} available technologies from catalog")
            return catalog
            
        except Exception as e:
            app_logger.error(f"Failed to load technology catalog: {e}")
            return self._fallback_to_pattern_extraction()
    
    def _build_category_index(self) -> Dict[str, Set[str]]:
        """Build category index from technology catalog.
        
        Returns:
            Dictionary mapping categories to sets of technology IDs
        """
        categories = {}
        
        # Initialize categories from catalog
        for category_id, category_info in self.technology_catalog.get("categories", {}).items():
            categories[category_id] = set(category_info.get("technologies", []))
        
        return categories
    
    def _fallback_to_pattern_extraction(self) -> Dict[str, Any]:
        """Fallback method to extract technologies from patterns if catalog is missing.
        
        Returns:
            Basic catalog structure from pattern extraction
        """
        technologies = {}
        
        # Load from pattern library
        pattern_dir = Path("data/patterns")
        if pattern_dir.exists():
            for pattern_file in pattern_dir.glob("*.json"):
                try:
                    with open(pattern_file, 'r') as f:
                        pattern = json.load(f)
                    
                    tech_stack = pattern.get("tech_stack", [])
                    for tech in tech_stack:
                        tech_id = tech.lower().replace(" ", "_").replace("/", "_")
                        technologies[tech_id] = {
                            "name": tech,
                            "category": "tools",  # Default category
                            "description": f"Technology component: {tech}",
                            "tags": [],
                            "maturity": "unknown",
                            "license": "unknown"
                        }
                        
                except Exception as e:
                    app_logger.warning(f"Failed to load pattern {pattern_file}: {e}")
        
        app_logger.info(f"Extracted {len(technologies)} technologies from patterns")
        
        return {
            "metadata": {"version": "fallback", "total_technologies": len(technologies)},
            "technologies": technologies,
            "categories": {"tools": {"name": "Tools", "technologies": list(technologies.keys())}}
        }
    
    def get_technology_info(self, tech_id: str) -> Dict[str, Any]:
        """Get detailed information about a technology.
        
        Args:
            tech_id: Technology identifier
            
        Returns:
            Technology information dictionary
        """
        return self.technology_catalog.get("technologies", {}).get(tech_id, {
            "name": tech_id,
            "category": "unknown",
            "description": f"Technology: {tech_id}",
            "tags": [],
            "maturity": "unknown",
            "license": "unknown"
        })
    
    def find_technology_by_name(self, name: str) -> Optional[str]:
        """Find technology ID by name (case-insensitive).
        
        Args:
            name: Technology name to search for
            
        Returns:
            Technology ID if found, None otherwise
        """
        name_lower = name.lower()
        
        for tech_id, tech_info in self.technology_catalog.get("technologies", {}).items():
            if tech_info.get("name", "").lower() == name_lower:
                return tech_id
            
            # Also check if the name contains the tech name
            if name_lower in tech_info.get("name", "").lower() or tech_info.get("name", "").lower() in name_lower:
                return tech_id
        
        return None
    
    async def generate_tech_stack(self, 
                                matches: List[MatchResult], 
                                requirements: Dict[str, Any],
                                constraints: Optional[Dict[str, Any]] = None) -> List[str]:
        """Generate intelligent tech stack based on requirements and constraints.
        
        Args:
            matches: Pattern matching results
            requirements: User requirements
            constraints: Constraints including banned tools
            
        Returns:
            List of recommended technologies
        """
        app_logger.info("Generating intelligent tech stack")
        
        # Extract constraint information
        banned_tools = set()
        required_integrations = []
        
        if constraints:
            banned_tools.update(constraints.get("banned_tools", []))
            required_integrations.extend(constraints.get("required_integrations", []))
        
        # Add banned tools from patterns
        for match in matches:
            if hasattr(match, 'constraints') and match.constraints:
                banned_tools.update(match.constraints.get("banned_tools", []))
        
        # Get available technologies from patterns
        pattern_technologies = self._extract_pattern_technologies(matches)
        
        # Use LLM for intelligent analysis if available
        if self.llm_provider:
            try:
                llm_tech_stack = await self._generate_llm_tech_stack(
                    requirements, pattern_technologies, banned_tools, required_integrations, constraints
                )
                if llm_tech_stack:
                    app_logger.info(f"Generated LLM-based tech stack with {len(llm_tech_stack)} technologies")
                    return llm_tech_stack
            except Exception as e:
                app_logger.error(f"LLM tech stack generation failed: {e}")
        
        # Fallback to rule-based generation
        app_logger.info("Using rule-based tech stack generation")
        return self._generate_rule_based_tech_stack(
            matches, requirements, pattern_technologies, banned_tools, required_integrations
        )
    
    def _extract_pattern_technologies(self, matches: List[MatchResult]) -> Dict[str, List[str]]:
        """Extract technologies from matched patterns.
        
        Args:
            matches: Pattern matching results
            
        Returns:
            Dictionary with pattern technologies organized by confidence
        """
        high_confidence = []  # > 0.8
        medium_confidence = []  # 0.5 - 0.8
        low_confidence = []  # < 0.5
        
        for match in matches:
            tech_stack = match.tech_stack or []
            
            if match.blended_score > 0.8:
                high_confidence.extend(tech_stack)
            elif match.blended_score > 0.5:
                medium_confidence.extend(tech_stack)
            else:
                low_confidence.extend(tech_stack)
        
        return {
            "high_confidence": list(set(high_confidence)),
            "medium_confidence": list(set(medium_confidence)),
            "low_confidence": list(set(low_confidence))
        }
    
    async def _generate_llm_tech_stack(self, 
                                     requirements: Dict[str, Any],
                                     pattern_technologies: Dict[str, List[str]],
                                     banned_tools: Set[str],
                                     required_integrations: List[str],
                                     constraints: Optional[Dict[str, Any]] = None) -> Optional[List[str]]:
        """Generate tech stack using LLM analysis.
        
        Args:
            requirements: User requirements
            pattern_technologies: Technologies from matched patterns
            banned_tools: Tools that cannot be used
            required_integrations: Required integration types
            
        Returns:
            LLM-generated tech stack or None if failed
        """
        # Prepare context for LLM
        available_tech_summary = self._summarize_available_technologies()
        pattern_tech_summary = self._summarize_pattern_technologies(pattern_technologies)
        
        prompt = {
            "system": """You are a senior software architect specializing in automation and AI systems. 
Your task is to recommend the most appropriate technology stack for a given automation requirement.

Consider:
1. The specific requirements and constraints
2. Technologies used in similar patterns (if any)
3. Available technologies in the organization
4. Banned/prohibited technologies
5. Required integrations
6. Performance, scalability, and maintainability

Provide a focused, practical tech stack - avoid generic or unnecessary technologies.
Focus on technologies that directly address the requirements.""",
            
            "user": f"""
**Requirements:**
- Description: {requirements.get('description', 'Not specified')}
- Domain: {requirements.get('domain', 'Not specified')}
- Volume: {requirements.get('volume', {})}
- Integrations needed: {requirements.get('integrations', [])}
- Data sensitivity: {requirements.get('data_sensitivity', 'Not specified')}
- Compliance: {requirements.get('compliance', [])}
- SLA requirements: {requirements.get('sla', {})}

**Available Technologies from Similar Patterns:**
{pattern_tech_summary}

**Available Technologies in Organization:**
{available_tech_summary}

**CRITICAL CONSTRAINTS (MUST BE ENFORCED):**
- Banned/Prohibited Technologies: {list(banned_tools) if banned_tools else 'None'}
- Required Integrations: {required_integrations if required_integrations else 'None'}
- Compliance Requirements: {constraints.get('compliance_requirements', []) if constraints else 'None'}
- Data Sensitivity Level: {constraints.get('data_sensitivity', 'Not specified') if constraints else 'Not specified'}
- Budget Constraints: {constraints.get('budget_constraints', 'Not specified') if constraints else 'Not specified'}
- Deployment Preference: {constraints.get('deployment_preference', 'Not specified') if constraints else 'Not specified'}

**CRITICAL INSTRUCTIONS:**
1. Analyze the requirements carefully
2. **NEVER recommend any technology listed in "Banned/Prohibited Technologies"**
3. **MUST include all "Required Integrations" in your recommendations**
4. Consider compliance requirements when selecting technologies
5. Respect data sensitivity level and deployment preferences
6. Consider budget constraints (prefer open source if specified)
7. Select technologies that directly address the needs
8. Prefer technologies from similar patterns when suitable
9. Only suggest technologies that are necessary and justified
10. Provide 5-12 technologies maximum

**CONSTRAINT ENFORCEMENT:**
- If a technology is banned, find suitable alternatives
- If budget is "Low (Open source preferred)", prioritize open source solutions
- If deployment is "On-premises only", avoid cloud-only services
- If data sensitivity is "Confidential" or "Restricted", prioritize secure, enterprise-grade solutions

Respond with a JSON object containing:
{{
    "tech_stack": ["Technology1", "Technology2", ...],
    "reasoning": "Brief explanation of why these technologies were chosen",
    "alternatives": ["Alt1", "Alt2", ...] // Optional alternatives if primary choices aren't available
}}
"""
        }
        
        try:
            # Log the LLM call for audit trail
            start_time = datetime.now()
            
            # Note: We'll log after the call to get latency
            
            response = await self.llm_provider.generate(prompt, purpose="tech_stack_generation")
            
            # Calculate latency
            end_time = datetime.now()
            latency_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Parse JSON response
            if isinstance(response, dict):
                # Response is already a dict (from fake provider)
                result = response
                response_str = json.dumps(result)
            elif isinstance(response, str):
                # Try to extract JSON from string response
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    response_str = json_match.group()
                    result = json.loads(response_str)
                else:
                    result = {"error": "Could not parse JSON from response"}
                    response_str = response
            else:
                # Fallback for unexpected response types
                app_logger.warning(f"Unexpected response type: {type(response)}")
                return None
            
            tech_stack = result.get("tech_stack", [])
            reasoning = result.get("reasoning", "")
            
            # Log the successful response
            await log_llm_call(
                session_id="tech_stack_generation",
                provider=self.llm_provider.__class__.__name__,
                model=getattr(self.llm_provider, 'model', 'unknown'),
                latency_ms=latency_ms,
                prompt=str(prompt),
                response=response_str
            )
            
            # Update catalog with new technologies before validation (if enabled)
            if self.auto_update_catalog:
                await self._update_catalog_with_new_technologies(tech_stack)
            
            # Validate and filter tech stack
            validated_tech_stack = self._validate_tech_stack(tech_stack, banned_tools)
            
            app_logger.info(f"LLM tech stack reasoning: {reasoning}")
            return validated_tech_stack
            
        except Exception as e:
            app_logger.error(f"Failed to parse LLM tech stack response: {e}")
            return None
    
    def _summarize_available_technologies(self) -> str:
        """Summarize available technologies for LLM context.
        
        Returns:
            Formatted summary of available technologies
        """
        summary_parts = []
        
        categories = self.technology_catalog.get("categories", {})
        technologies = self.technology_catalog.get("technologies", {})
        
        for category_id, category_info in categories.items():
            category_name = category_info.get("name", category_id.title())
            tech_ids = category_info.get("technologies", [])
            
            if tech_ids:
                # Get actual technology names
                tech_names = []
                for tech_id in tech_ids[:10]:  # Limit to 10 per category
                    tech_info = technologies.get(tech_id, {})
                    tech_names.append(tech_info.get("name", tech_id))
                
                tech_list = ", ".join(tech_names)
                if len(tech_ids) > 10:
                    tech_list += f" (and {len(tech_ids) - 10} others)"
                
                summary_parts.append(f"- {category_name}: {tech_list}")
        
        return "\n".join(summary_parts) if summary_parts else "No specific technologies catalogued"
    
    def _summarize_pattern_technologies(self, pattern_technologies: Dict[str, List[str]]) -> str:
        """Summarize pattern technologies for LLM context.
        
        Args:
            pattern_technologies: Technologies organized by confidence
            
        Returns:
            Formatted summary
        """
        summary_parts = []
        
        if pattern_technologies.get("high_confidence"):
            summary_parts.append(f"- High confidence matches: {', '.join(pattern_technologies['high_confidence'])}")
        
        if pattern_technologies.get("medium_confidence"):
            summary_parts.append(f"- Medium confidence matches: {', '.join(pattern_technologies['medium_confidence'])}")
        
        if pattern_technologies.get("low_confidence"):
            summary_parts.append(f"- Low confidence matches: {', '.join(pattern_technologies['low_confidence'])}")
        
        return "\n".join(summary_parts) if summary_parts else "No similar patterns found"
    
    def _validate_tech_stack(self, tech_stack: List[str], banned_tools: Set[str]) -> List[str]:
        """Validate and filter tech stack against constraints.
        
        Args:
            tech_stack: Proposed tech stack
            banned_tools: Tools that cannot be used
            
        Returns:
            Validated tech stack
        """
        validated = []
        
        for tech in tech_stack:
            # Ensure tech is a string (handle cases where LLM returns dicts)
            if isinstance(tech, dict):
                # If it's a dict, try to extract the name
                tech_name = tech.get('name') or tech.get('technology') or str(tech)
                app_logger.warning(f"Tech stack item was dict, extracted name: {tech_name}")
                tech = tech_name
            elif not isinstance(tech, str):
                # Convert to string if it's not already
                tech = str(tech)
                app_logger.warning(f"Tech stack item was {type(tech)}, converted to string: {tech}")
            
            # Check if technology is banned
            if any(banned.lower() in tech.lower() for banned in banned_tools):
                app_logger.warning(f"Skipping banned technology: {tech}")
                continue
            
            validated.append(tech)
        
        return validated
    
    def _generate_rule_based_tech_stack(self, 
                                      matches: List[MatchResult],
                                      requirements: Dict[str, Any],
                                      pattern_technologies: Dict[str, List[str]],
                                      banned_tools: Set[str],
                                      required_integrations: List[str]) -> List[str]:
        """Generate tech stack using rule-based approach as fallback.
        
        Args:
            matches: Pattern matching results
            requirements: User requirements
            pattern_technologies: Technologies from patterns
            banned_tools: Banned technologies
            required_integrations: Required integrations
            
        Returns:
            Rule-based tech stack
        """
        tech_stack = []
        
        # Start with high-confidence pattern technologies
        tech_stack.extend(pattern_technologies.get("high_confidence", []))
        
        # Add medium-confidence if we don't have enough
        if len(tech_stack) < 3:
            tech_stack.extend(pattern_technologies.get("medium_confidence", []))
        
        # Add requirement-specific technologies
        domain = str(requirements.get("domain", "")).lower()
        description = str(requirements.get("description", "")).lower()
        
        # Domain-specific additions
        if "data" in domain or "processing" in description:
            tech_stack.extend(["pandas", "numpy"])
        
        if "api" in domain or "integration" in description:
            tech_stack.extend(["FastAPI", "httpx"])
        
        if "web" in domain or "scraping" in description:
            tech_stack.extend(["requests", "BeautifulSoup"])
        
        # Integration-specific additions
        for integration in required_integrations:
            if "database" in integration.lower():
                tech_stack.append("SQLAlchemy")
            elif "queue" in integration.lower():
                tech_stack.append("Celery")
            elif "monitoring" in integration.lower():
                tech_stack.append("Prometheus")
        
        # Remove banned technologies and duplicates
        validated_tech_stack = []
        seen = set()
        
        for tech in tech_stack:
            # Ensure tech is a string (handle cases where it might be a dict)
            if isinstance(tech, dict):
                tech_name = tech.get('name') or tech.get('technology') or str(tech)
                app_logger.warning(f"Tech stack item was dict, extracted name: {tech_name}")
                tech = tech_name
            elif not isinstance(tech, str):
                tech = str(tech)
                app_logger.warning(f"Tech stack item was {type(tech)}, converted to string: {tech}")
            
            if tech not in seen and not any(banned.lower() in tech.lower() for banned in banned_tools):
                validated_tech_stack.append(tech)
                seen.add(tech)
        
        return validated_tech_stack[:10]  # Limit to 10 technologies
    
    def categorize_tech_stack_with_descriptions(self, tech_stack: List[str]) -> Dict[str, Dict[str, Any]]:
        """Categorize tech stack with descriptions and explanations using catalog.
        
        Args:
            tech_stack: List of technology names
            
        Returns:
            Dictionary with categorized technologies and descriptions
        """
        result_categories = {}
        uncategorized = []
        
        catalog_categories = self.technology_catalog.get("categories", {})
        catalog_technologies = self.technology_catalog.get("technologies", {})
        
        # Process each technology in the stack
        for tech_name in tech_stack:
            # Ensure tech_name is a string (handle cases where it might be a dict)
            if isinstance(tech_name, dict):
                tech_name = tech_name.get('name') or tech_name.get('technology') or str(tech_name)
                app_logger.warning(f"Tech stack item was dict in categorization, extracted name: {tech_name}")
            elif not isinstance(tech_name, str):
                tech_name = str(tech_name)
                app_logger.warning(f"Tech stack item was {type(tech_name)} in categorization, converted to string: {tech_name}")
            
            # Find the technology in catalog
            tech_id = self.find_technology_by_name(tech_name)
            
            if tech_id and tech_id in catalog_technologies:
                tech_info = catalog_technologies[tech_id]
                category_id = tech_info.get("category", "unknown")
                
                # Find the category info
                category_info = None
                for cat_id, cat_data in catalog_categories.items():
                    if cat_id == category_id or tech_id in cat_data.get("technologies", []):
                        category_info = cat_data
                        break
                
                if category_info:
                    category_name = category_info.get("name", category_id.title())
                    category_desc = category_info.get("description", f"{category_name} technologies")
                    
                    if category_name not in result_categories:
                        result_categories[category_name] = {
                            "description": category_desc,
                            "technologies": []
                        }
                    
                    # Add technology with its description
                    tech_entry = {
                        "name": tech_info.get("name", tech_name),
                        "description": tech_info.get("description", f"Technology: {tech_name}"),
                        "tags": tech_info.get("tags", []),
                        "maturity": tech_info.get("maturity", "unknown")
                    }
                    result_categories[category_name]["technologies"].append(tech_entry)
                else:
                    uncategorized.append(tech_name)
            else:
                uncategorized.append(tech_name)
        
        # Add uncategorized technologies
        if uncategorized:
            result_categories["Other Technologies"] = {
                "description": "Additional specialized tools and technologies",
                "technologies": [
                    {
                        "name": tech,
                        "description": f"Technology component: {tech}",
                        "tags": [],
                        "maturity": "unknown"
                    } for tech in uncategorized
                ]
            }
        
        return result_categories
    
    def get_technology_description(self, tech: str) -> str:
        """Get a brief description of what a technology does.
        
        Args:
            tech: Technology name
            
        Returns:
            Brief description of the technology
        """
        tech_id = self.find_technology_by_name(tech)
        
        if tech_id:
            tech_info = self.get_technology_info(tech_id)
            return tech_info.get("description", f"Technology component: {tech}")
        
        return f"Technology component: {tech}"
    
    async def _update_catalog_with_new_technologies(self, tech_stack: List[str]) -> None:
        """Update technology catalog with new technologies from LLM suggestions.
        
        Args:
            tech_stack: List of technology names from LLM
        """
        new_technologies = []
        catalog_updated = False
        
        for tech_name in tech_stack:
            # Check if technology already exists in catalog
            tech_id = self.find_technology_by_name(tech_name)
            
            if not tech_id:
                # This is a new technology, add it to catalog
                new_tech_id = self._generate_tech_id(tech_name)
                new_tech_info = self._infer_technology_info(tech_name)
                
                # Add to in-memory catalog
                self.technology_catalog.setdefault("technologies", {})[new_tech_id] = new_tech_info
                
                # Add to appropriate category
                category_id = new_tech_info.get("category", "integration")
                self.technology_catalog.setdefault("categories", {}).setdefault(category_id, {
                    "name": category_id.replace("_", " ").title(),
                    "description": f"{category_id.replace('_', ' ').title()} technologies",
                    "technologies": []
                })
                
                if new_tech_id not in self.technology_catalog["categories"][category_id]["technologies"]:
                    self.technology_catalog["categories"][category_id]["technologies"].append(new_tech_id)
                
                new_technologies.append(tech_name)
                catalog_updated = True
                
                app_logger.info(f"Added new technology to catalog: {tech_name} -> {new_tech_id}")
        
        # Save updated catalog to file if changes were made
        if catalog_updated:
            await self._save_catalog_to_file()
            
            # Update metadata
            total_techs = len(self.technology_catalog.get("technologies", {}))
            self.technology_catalog.setdefault("metadata", {}).update({
                "total_technologies": total_techs,
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "last_auto_update": datetime.now().isoformat()
            })
            
            app_logger.info(f"Catalog updated with {len(new_technologies)} new technologies: {', '.join(new_technologies)}")
    
    def _generate_tech_id(self, tech_name: str) -> str:
        """Generate a consistent technology ID from name.
        
        Args:
            tech_name: Technology name
            
        Returns:
            Technology ID (lowercase, underscores)
        """
        # Clean and normalize the name
        tech_id = tech_name.lower()
        tech_id = tech_id.replace(" ", "_")
        tech_id = tech_id.replace("/", "_")
        tech_id = tech_id.replace("-", "_")
        tech_id = tech_id.replace(".", "_")
        tech_id = tech_id.replace("(", "").replace(")", "")
        
        # Remove common suffixes/prefixes
        tech_id = tech_id.replace("_api", "").replace("api_", "")
        tech_id = tech_id.replace("_service", "").replace("service_", "")
        
        # Handle duplicates by checking existing IDs
        base_id = tech_id
        counter = 1
        while tech_id in self.technology_catalog.get("technologies", {}):
            tech_id = f"{base_id}_{counter}"
            counter += 1
        
        return tech_id
    
    def _infer_technology_info(self, tech_name: str) -> Dict[str, Any]:
        """Infer technology information from name using heuristics.
        
        Args:
            tech_name: Technology name
            
        Returns:
            Technology information dictionary
        """
        tech_lower = tech_name.lower()
        
        # Infer category based on name patterns
        category = "integration"  # Default
        tags = []
        
        if any(keyword in tech_lower for keyword in ["python", "java", "javascript", "node", "go", "rust", "c#"]):
            category = "languages"
            tags = ["programming", "language"]
        elif any(keyword in tech_lower for keyword in ["api", "rest", "graphql", "webhook"]):
            category = "integration"
            tags = ["api", "integration"]
        elif any(keyword in tech_lower for keyword in ["database", "db", "sql", "mongo", "redis", "elastic"]):
            category = "databases"
            tags = ["database", "storage"]
        elif any(keyword in tech_lower for keyword in ["aws", "azure", "gcp", "cloud", "lambda", "function"]):
            category = "cloud"
            tags = ["cloud", "infrastructure"]
        elif any(keyword in tech_lower for keyword in ["docker", "kubernetes", "k8s", "container"]):
            category = "infrastructure"
            tags = ["containers", "devops"]
        elif any(keyword in tech_lower for keyword in ["kafka", "rabbitmq", "queue", "celery"]):
            category = "processing"
            tags = ["messaging", "queue"]
        elif any(keyword in tech_lower for keyword in ["ai", "ml", "nlp", "gpt", "claude", "openai"]):
            category = "ai"
            tags = ["ai", "ml", "nlp"]
        elif any(keyword in tech_lower for keyword in ["auth", "oauth", "jwt", "security"]):
            category = "security"
            tags = ["security", "authentication"]
        elif any(keyword in tech_lower for keyword in ["test", "pytest", "jest", "selenium"]):
            category = "testing"
            tags = ["testing", "qa"]
        elif any(keyword in tech_lower for keyword in ["framework", "django", "flask", "express", "spring"]):
            category = "frameworks"
            tags = ["framework", "web"]
        
        return {
            "name": tech_name,
            "category": category,
            "description": f"Technology component: {tech_name}",
            "tags": tags,
            "maturity": "unknown",
            "license": "unknown",
            "alternatives": [],
            "integrates_with": [],
            "use_cases": [],
            "auto_generated": True,
            "added_date": datetime.now().strftime("%Y-%m-%d")
        }
    
    async def _save_catalog_to_file(self) -> None:
        """Save the updated catalog back to the JSON file.
        
        This method handles file I/O safely with backup and error handling.
        """
        catalog_path = Path("data/technologies.json")
        backup_path = Path("data/technologies.json.backup")
        
        try:
            # Create backup of existing catalog
            if catalog_path.exists():
                import shutil
                shutil.copy2(catalog_path, backup_path)
            
            # Write updated catalog
            with open(catalog_path, 'w') as f:
                json.dump(self.technology_catalog, f, indent=2, sort_keys=True)
            
            app_logger.info(f"Technology catalog saved to {catalog_path}")
            
        except Exception as e:
            app_logger.error(f"Failed to save technology catalog: {e}")
            
            # Restore from backup if write failed
            if backup_path.exists():
                try:
                    import shutil
                    shutil.copy2(backup_path, catalog_path)
                    app_logger.info("Restored catalog from backup after write failure")
                except Exception as restore_error:
                    app_logger.error(f"Failed to restore catalog from backup: {restore_error}")
    
    async def add_technology_to_catalog(self, tech_name: str, tech_info: Optional[Dict[str, Any]] = None) -> str:
        """Manually add a technology to the catalog.
        
        Args:
            tech_name: Technology name
            tech_info: Optional technology information (will be inferred if not provided)
            
        Returns:
            Technology ID that was created
        """
        # Check if already exists
        existing_id = self.find_technology_by_name(tech_name)
        if existing_id:
            app_logger.info(f"Technology {tech_name} already exists as {existing_id}")
            return existing_id
        
        # Generate new technology entry
        tech_id = self._generate_tech_id(tech_name)
        
        if tech_info is None:
            tech_info = self._infer_technology_info(tech_name)
        else:
            # Ensure required fields are present
            tech_info.setdefault("name", tech_name)
            tech_info.setdefault("category", "integration")
            tech_info.setdefault("description", f"Technology component: {tech_name}")
            tech_info.setdefault("tags", [])
            tech_info.setdefault("maturity", "unknown")
            tech_info.setdefault("license", "unknown")
            tech_info.setdefault("added_date", datetime.now().strftime("%Y-%m-%d"))
        
        # Add to catalog
        self.technology_catalog.setdefault("technologies", {})[tech_id] = tech_info
        
        # Add to category
        category_id = tech_info.get("category", "integration")
        self.technology_catalog.setdefault("categories", {}).setdefault(category_id, {
            "name": category_id.replace("_", " ").title(),
            "description": f"{category_id.replace('_', ' ').title()} technologies",
            "technologies": []
        })
        
        if tech_id not in self.technology_catalog["categories"][category_id]["technologies"]:
            self.technology_catalog["categories"][category_id]["technologies"].append(tech_id)
        
        # Save to file
        await self._save_catalog_to_file()
        
        app_logger.info(f"Manually added technology: {tech_name} -> {tech_id}")
        return tech_id