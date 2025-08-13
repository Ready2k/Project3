"""Intelligent tech stack generation service using LLM analysis."""

from typing import Dict, List, Any, Optional, Set
import json
from pathlib import Path

from app.pattern.matcher import MatchResult
from app.llm.base import LLMProvider
from app.utils.logger import app_logger
from app.utils.audit import log_llm_call
from datetime import datetime


class TechStackGenerator:
    """Service for generating intelligent, context-aware technology stacks."""
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """Initialize tech stack generator.
        
        Args:
            llm_provider: LLM provider for intelligent analysis
        """
        self.llm_provider = llm_provider
        
        # Load available technologies from patterns
        self.available_technologies = self._load_available_technologies()
        
    def _load_available_technologies(self) -> Dict[str, Set[str]]:
        """Load all available technologies from existing patterns.
        
        Returns:
            Dictionary mapping categories to sets of technologies
        """
        technologies = {
            "languages": set(),
            "frameworks": set(), 
            "databases": set(),
            "tools": set(),
            "services": set(),
            "libraries": set()
        }
        
        # Load from pattern library
        pattern_dir = Path("data/patterns")
        if pattern_dir.exists():
            for pattern_file in pattern_dir.glob("*.json"):
                try:
                    with open(pattern_file, 'r') as f:
                        pattern = json.load(f)
                    
                    tech_stack = pattern.get("tech_stack", [])
                    for tech in tech_stack:
                        # Categorize technologies
                        self._categorize_technology(tech, technologies)
                        
                except Exception as e:
                    app_logger.warning(f"Failed to load pattern {pattern_file}: {e}")
        
        app_logger.info(f"Loaded {sum(len(techs) for techs in technologies.values())} available technologies")
        return technologies
    
    def _categorize_technology(self, tech: str, technologies: Dict[str, Set[str]]) -> None:
        """Categorize a technology into the appropriate category.
        
        Args:
            tech: Technology name
            technologies: Dictionary to update with categorized tech
        """
        tech_lower = tech.lower()
        
        # Languages
        if tech_lower in ["python", "javascript", "java", "go", "rust", "typescript", "c#", "php", "node.js"]:
            technologies["languages"].add(tech)
        # Frameworks & Web
        elif tech_lower in ["fastapi", "django", "flask", "express", "react", "vue", "angular", "spring", "streamlit"]:
            technologies["frameworks"].add(tech)
        # Databases & Storage
        elif tech_lower in ["postgresql", "mysql", "mongodb", "redis", "elasticsearch", "sqlite", "sqlalchemy"]:
            technologies["databases"].add(tech)
        # Cloud & Infrastructure
        elif tech_lower in ["aws", "azure", "gcp", "docker", "kubernetes", "lambda", "heroku", "vercel"]:
            technologies["services"].add(tech)
        # Communication & Integration
        elif any(keyword in tech_lower for keyword in ["api", "webhook", "oauth", "jwt", "twilio", "smtp", "http"]):
            technologies["libraries"].add(tech)
        # Testing & Development
        elif tech_lower in ["pytest", "jest", "mocha", "selenium", "cypress", "postman"]:
            technologies["tools"].add(tech)
        # Data Processing & ML
        elif tech_lower in ["pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "jupyter"]:
            technologies["libraries"].add(tech)
        # Monitoring & Logging
        elif tech_lower in ["prometheus", "grafana", "elk", "datadog", "sentry", "loguru"]:
            technologies["tools"].add(tech)
        # Message Queues & Processing
        elif tech_lower in ["celery", "rabbitmq", "kafka", "sqs", "redis"]:
            technologies["services"].add(tech)
        # Default fallback
        else:
            if any(keyword in tech_lower for keyword in ["lib", "sdk"]):
                technologies["libraries"].add(tech)
            else:
                technologies["tools"].add(tech)
    
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
                    requirements, pattern_technologies, banned_tools, required_integrations
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
                                     required_integrations: List[str]) -> Optional[List[str]]:
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

**Constraints:**
- Banned tools: {list(banned_tools) if banned_tools else 'None'}
- Required integrations: {required_integrations if required_integrations else 'None'}

**Instructions:**
1. Analyze the requirements carefully
2. Select the most appropriate technologies that directly address the needs
3. Avoid banned technologies
4. Prefer technologies from similar patterns when suitable
5. Only suggest technologies that are necessary and justified
6. Provide 5-12 technologies maximum

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
        
        for category, techs in self.available_technologies.items():
            if techs:
                tech_list = ", ".join(sorted(list(techs))[:10])  # Limit to 10 per category
                if len(techs) > 10:
                    tech_list += f" (and {len(techs) - 10} others)"
                summary_parts.append(f"- {category.title()}: {tech_list}")
        
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
        domain = requirements.get("domain", "").lower()
        description = requirements.get("description", "").lower()
        
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
            if tech not in seen and not any(banned.lower() in tech.lower() for banned in banned_tools):
                validated_tech_stack.append(tech)
                seen.add(tech)
        
        return validated_tech_stack[:10]  # Limit to 10 technologies
    
    def categorize_tech_stack_with_descriptions(self, tech_stack: List[str]) -> Dict[str, Dict[str, Any]]:
        """Categorize tech stack with descriptions and explanations.
        
        Args:
            tech_stack: List of technologies
            
        Returns:
            Dictionary with categorized technologies and descriptions
        """
        categories = {
            "Programming Languages": {
                "description": "Core programming languages used for development",
                "technologies": [],
                "keywords": ["python", "javascript", "java", "go", "rust", "typescript", "c#", "php", "node.js"]
            },
            "Web Frameworks & APIs": {
                "description": "Frameworks for building web applications and APIs",
                "technologies": [],
                "keywords": ["fastapi", "django", "flask", "express", "react", "vue", "angular", "spring", "streamlit"]
            },
            "Databases & Storage": {
                "description": "Data storage and database management systems",
                "technologies": [],
                "keywords": ["postgresql", "mysql", "mongodb", "redis", "elasticsearch", "sqlite", "sqlalchemy"]
            },
            "Cloud & Infrastructure": {
                "description": "Cloud services and infrastructure management",
                "technologies": [],
                "keywords": ["aws", "azure", "gcp", "docker", "kubernetes", "lambda", "heroku", "vercel"]
            },
            "Communication & Integration": {
                "description": "APIs, messaging, and third-party integrations",
                "technologies": [],
                "keywords": ["api", "webhook", "oauth", "jwt", "twilio", "smtp", "http", "rest", "graphql"]
            },
            "Testing & Development Tools": {
                "description": "Testing frameworks and development utilities",
                "technologies": [],
                "keywords": ["pytest", "jest", "mocha", "selenium", "cypress", "postman", "git", "github"]
            },
            "Data Processing & Analytics": {
                "description": "Data processing, machine learning, and analytics tools",
                "technologies": [],
                "keywords": ["pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "jupyter", "matplotlib"]
            },
            "Monitoring & Operations": {
                "description": "System monitoring, logging, and operational tools",
                "technologies": [],
                "keywords": ["prometheus", "grafana", "elk", "datadog", "sentry", "loguru", "nginx"]
            },
            "Message Queues & Processing": {
                "description": "Asynchronous processing and message handling",
                "technologies": [],
                "keywords": ["celery", "rabbitmq", "kafka", "sqs", "redis", "worker", "queue"]
            }
        }
        
        # Categorize each technology
        uncategorized = []
        
        for tech in tech_stack:
            tech_lower = tech.lower()
            found_category = False
            
            for category_name, category_info in categories.items():
                if any(keyword in tech_lower for keyword in category_info["keywords"]):
                    category_info["technologies"].append(tech)
                    found_category = True
                    break
            
            if not found_category:
                uncategorized.append(tech)
        
        # Add uncategorized technologies
        if uncategorized:
            categories["Other Technologies"] = {
                "description": "Additional specialized tools and technologies",
                "technologies": uncategorized,
                "keywords": []
            }
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v["technologies"]}
    
    def get_technology_description(self, tech: str) -> str:
        """Get a brief description of what a technology does.
        
        Args:
            tech: Technology name
            
        Returns:
            Brief description of the technology
        """
        descriptions = {
            "python": "High-level programming language for automation and data processing",
            "fastapi": "Modern, fast web framework for building APIs with Python",
            "postgresql": "Advanced open-source relational database system",
            "redis": "In-memory data structure store for caching and messaging",
            "docker": "Containerization platform for application deployment",
            "celery": "Distributed task queue for asynchronous processing",
            "twilio": "Cloud communications platform for SMS, voice, and messaging",
            "oauth 2.0": "Industry-standard protocol for authorization",
            "pytest": "Testing framework for Python applications",
            "jupyter": "Interactive computing environment for data analysis",
            "aws": "Amazon Web Services cloud computing platform",
            "kubernetes": "Container orchestration platform for scalable deployments",
            "mongodb": "NoSQL document database for flexible data storage",
            "react": "JavaScript library for building user interfaces",
            "nginx": "Web server and reverse proxy for high-performance applications"
        }
        
        tech_lower = tech.lower()
        return descriptions.get(tech_lower, f"Technology component: {tech}")