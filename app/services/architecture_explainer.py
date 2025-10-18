"""LLM-driven architecture explanation service."""

from typing import Dict, List, Any, Optional

from app.llm.base import LLMProvider
from app.utils.imports import require_service


class ArchitectureExplainer:
    """Service for generating LLM-driven architecture explanations."""

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """Initialize architecture explainer.

        Args:
            llm_provider: LLM provider for generating explanations
        """
        self.llm_provider = llm_provider

        # Get logger from service registry
        self.logger = require_service("logger", context="ArchitectureExplainer")

        # Initialize tech stack generator for proper constraint handling
        if llm_provider:
            from app.services.tech_stack_generator import TechStackGenerator

            self.tech_stack_generator = TechStackGenerator(llm_provider)
        else:
            self.tech_stack_generator = None

    async def explain_architecture(
        self,
        tech_stack: List[str],
        requirements: Dict[str, Any],
        session_id: str = "unknown",
    ) -> tuple[List[str], str]:
        """Generate LLM-driven tech stack and explanation based on requirements.

        Args:
            tech_stack: Initial tech stack (may be enhanced by LLM)
            requirements: User requirements for context
            session_id: Session ID for tracking

        Returns:
            Tuple of (enhanced_tech_stack, architecture_explanation)
        """
        if not self.llm_provider:
            return tech_stack, self._generate_fallback_explanation(
                tech_stack, requirements
            )

        try:
            # First, generate an appropriate tech stack based on requirements
            enhanced_tech_stack = await self._generate_tech_stack_for_requirements(
                requirements, session_id
            )

            # Then explain how it works together
            explanation = await self._generate_llm_explanation(
                enhanced_tech_stack, requirements, session_id
            )
            if explanation:
                return enhanced_tech_stack, explanation
        except Exception as e:
            self.logger.error(f"Failed to generate LLM architecture explanation: {e}")

        # Fallback to rule-based explanation
        return tech_stack, self._generate_fallback_explanation(tech_stack, requirements)

    async def _generate_tech_stack_for_requirements(
        self, requirements: Dict[str, Any], session_id: str
    ) -> List[str]:
        """Generate appropriate tech stack based on specific requirements using proper TechStackGenerator.

        Args:
            requirements: User requirements
            session_id: Session ID for tracking

        Returns:
            List of recommended technologies
        """
        if not self.tech_stack_generator:
            self.logger.warning("No tech stack generator available, using fallback")
            return self._get_domain_based_tech_stack(requirements)

        try:
            # Create empty matches list since we're generating from requirements
            matches = []

            # Extract constraints from requirements (this is the key fix!)
            constraints = requirements.get("constraints", {})

            self.logger.info(f"Generating tech stack with constraints: {constraints}")

            # Use the proper TechStackGenerator which handles constraints correctly
            tech_stack = await self.tech_stack_generator.generate_tech_stack(
                matches, requirements, constraints
            )

            self.logger.info(
                f"Generated tech stack with {len(tech_stack)} technologies using TechStackGenerator"
            )
            return tech_stack

        except Exception as e:
            self.logger.error(
                f"Failed to generate tech stack using TechStackGenerator: {e}"
            )
            return self._get_domain_based_tech_stack(requirements)

    def _extract_tech_from_text(self, text: str) -> List[str]:
        """Extract technology names from text response."""
        # Simple extraction - look for common tech patterns
        import re

        tech_patterns = [
            r"\b(Python|JavaScript|Java|Go|Rust|TypeScript|C#)\b",
            r"\b(FastAPI|Django|Flask|Express|React|Vue|Angular|Spring)\b",
            r"\b(PostgreSQL|MySQL|MongoDB|Redis|SQLite|Elasticsearch)\b",
            r"\b(Docker|Kubernetes|AWS|Azure|GCP|Nginx|Apache)\b",
            r"\b(Celery|RabbitMQ|Kafka|WebSocket|GraphQL|REST)\b",
        ]

        technologies = []
        for pattern in tech_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            technologies.extend(matches)

        # Remove duplicates and limit to 8
        return list(dict.fromkeys(technologies))[:8]

    def _get_domain_based_tech_stack(self, requirements: Dict[str, Any]) -> List[str]:
        """Get basic tech stack based on domain."""
        domain = str(requirements.get("domain", "")).lower()

        if "data" in domain or "analytics" in domain:
            return ["Python", "FastAPI", "PostgreSQL", "Pandas", "Redis", "Docker"]
        elif "web" in domain or "api" in domain:
            return ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "Nginx"]
        elif "mobile" in domain:
            return [
                "Python",
                "FastAPI",
                "PostgreSQL",
                "WebSocket",
                "Redis",
                "Mobile SDK",
            ]
        else:
            return ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "Monitoring"]

    async def _generate_llm_explanation(
        self, tech_stack: List[str], requirements: Dict[str, Any], session_id: str
    ) -> Optional[str]:
        """Generate architecture explanation using LLM.

        Args:
            tech_stack: List of technologies
            requirements: User requirements
            session_id: Session ID for tracking

        Returns:
            LLM-generated explanation or None if failed
        """
        # Prepare context for LLM as a single string prompt
        # Build the prompt with proper string formatting
        tech_stack_str = ", ".join(tech_stack)
        description = requirements.get("description", "Not specified")
        domain = requirements.get("domain", "Not specified")
        volume = requirements.get("volume", {})
        integrations = requirements.get("integrations", [])

        # Extract constraints from nested structure
        constraints = requirements.get("constraints", {})
        data_sensitivity = constraints.get("data_sensitivity", "Not specified")
        compliance = constraints.get("compliance_requirements", [])
        banned_tools = constraints.get("banned_tools", [])
        required_integrations = constraints.get("required_integrations", [])
        budget_constraints = constraints.get("budget_constraints", "Not specified")
        deployment_preference = constraints.get(
            "deployment_preference", "Not specified"
        )

        prompt = f"""You are a senior software architect with expertise in system design and technology integration. 
Your task is to explain how a technology stack works together to solve a specific automation requirement.

Focus on:
1. How the technologies complement each other
2. The data flow and system architecture
3. Why this combination is effective for the requirements
4. How the components interact and communicate

Keep the explanation clear, practical, and focused on the specific use case.
Avoid generic descriptions - be specific about how these technologies address the actual requirements.

**Requirements:**
- Description: {description}
- Domain: {domain}
- Volume: {volume}
- Integrations: {integrations}
- Data sensitivity: {data_sensitivity}
- Compliance: {compliance}

**IMPORTANT CONSTRAINTS:**
- Banned Technologies: {banned_tools if banned_tools else 'None'}
- Required Integrations: {required_integrations if required_integrations else 'None'}
- Budget Constraints: {budget_constraints}
- Deployment Preference: {deployment_preference}

**Technology Stack (use ALL of these technologies in your explanation):**
{tech_stack_str}

**NOTE:** The recommended technology stack has been selected considering the constraints above. Explain why these specific technologies were chosen given the restrictions and requirements.

**Instructions:**
Explain how these EXACT technologies work together to address the specific requirements above. 
You MUST mention and explain the role of each technology listed above.

Focus on:
1. The overall system architecture and data flow
2. How EACH technology in the stack contributes to solving the problem
3. Why this specific combination is well-suited for the requirements
4. How the components communicate and integrate

Provide a clear, practical explanation in 2-3 paragraphs. Be specific to this use case and mention all technologies by name."""

        try:
            self.logger.info(
                f"Generating explanation for tech stack ({len(tech_stack)} items): {tech_stack}"
            )
            response = await self.llm_provider.generate(
                prompt, purpose="tech_stack_explanation"
            )

            # Clean up the response
            if isinstance(response, str):
                explanation = response.strip()
                self.logger.info(
                    f"Generated LLM architecture explanation ({len(explanation)} chars)"
                )
                return explanation
            elif isinstance(response, dict):
                # Handle structured response
                explanation = response.get("explanation", str(response))
                self.logger.info(
                    f"Generated LLM architecture explanation from dict ({len(explanation)} chars)"
                )
                return explanation

            return None

        except Exception as e:
            self.logger.error(f"Failed to generate LLM architecture explanation: {e}")
            return None

    def _generate_fallback_explanation(
        self, tech_stack: List[str], requirements: Dict[str, Any]
    ) -> str:
        """Generate fallback architecture explanation using rules.

        Args:
            tech_stack: List of technologies
            requirements: User requirements

        Returns:
            Rule-based explanation
        """
        if not tech_stack:
            return "No technology stack specified for this recommendation."

        # Categorize technologies
        categories = self._categorize_technologies(tech_stack)

        explanation_parts = []

        # Core architecture
        if categories.get("languages") or categories.get("frameworks"):
            core_tech = list(categories.get("languages", [])) + list(
                categories.get("frameworks", [])
            )
            explanation_parts.append(
                f"The system is built using {', '.join(core_tech[:2])} as the core technology stack, providing a robust foundation for automation."
            )

        # Data layer
        if categories.get("databases"):
            db_tech = ", ".join(categories["databases"])
            explanation_parts.append(
                f"Data persistence is handled by {db_tech}, ensuring reliable storage and fast retrieval of information."
            )

        # Integration layer
        if categories.get("tools"):
            integration_tools = [
                tool
                for tool in categories["tools"]
                if isinstance(tool, str)
                and any(
                    keyword in tool.lower()
                    for keyword in ["http", "api", "request", "celery", "queue"]
                )
            ]
            if integration_tools:
                explanation_parts.append(
                    f"System integration and communication is managed through {', '.join(integration_tools[:2])}, enabling seamless data exchange."
                )

        # Infrastructure
        if categories.get("services"):
            infra_tech = ", ".join(categories["services"])
            explanation_parts.append(
                f"The infrastructure leverages {infra_tech} for scalable deployment and monitoring."
            )

        # Add flow description based on requirements
        domain = requirements.get("domain") or ""
        domain = domain.lower() if domain else ""
        if "data" in domain:
            explanation_parts.append(
                "The typical workflow involves data ingestion, processing, validation, and storage, with monitoring throughout the pipeline."
            )
        elif "api" in domain:
            explanation_parts.append(
                "The system follows an API-first approach, with request handling, business logic processing, and response formatting."
            )
        else:
            explanation_parts.append(
                "The components work together in a coordinated workflow, with each technology handling its specialized function while maintaining system reliability."
            )

        return " ".join(explanation_parts)

    def _categorize_technologies(self, tech_stack: List[str]) -> Dict[str, List[str]]:
        """Categorize technologies for explanation generation.

        Args:
            tech_stack: List of technologies

        Returns:
            Dictionary of categorized technologies
        """
        categories = {
            "languages": [],
            "frameworks": [],
            "databases": [],
            "tools": [],
            "services": [],
            "libraries": [],
        }

        for tech in tech_stack:
            # Ensure tech is a string (handle cases where it might be a dict)
            if isinstance(tech, dict):
                tech_name = tech.get("name") or tech.get("technology") or str(tech)
                self.logger.warning(
                    f"Tech stack item was dict in architecture explainer, extracted name: {tech_name}"
                )
                tech = tech_name
            elif not isinstance(tech, str):
                tech = str(tech)
                self.logger.warning(
                    f"Tech stack item was {type(tech)} in architecture explainer, converted to string: {tech}"
                )

            tech_lower = tech.lower()

            # Languages
            if tech_lower in [
                "python",
                "javascript",
                "java",
                "go",
                "rust",
                "typescript",
                "c#",
                "php",
            ]:
                categories["languages"].append(tech)
            # Frameworks
            elif tech_lower in [
                "fastapi",
                "django",
                "flask",
                "express",
                "react",
                "vue",
                "angular",
                "spring",
            ]:
                categories["frameworks"].append(tech)
            # Databases
            elif tech_lower in [
                "postgresql",
                "mysql",
                "mongodb",
                "redis",
                "elasticsearch",
                "sqlite",
                "sqlalchemy",
            ]:
                categories["databases"].append(tech)
            # Cloud Services
            elif tech_lower in [
                "aws",
                "azure",
                "gcp",
                "docker",
                "kubernetes",
                "lambda",
                "prometheus",
            ]:
                categories["services"].append(tech)
            # Tools and Libraries
            else:
                if any(keyword in tech_lower for keyword in ["lib", "sdk", "api"]):
                    categories["libraries"].append(tech)
                else:
                    categories["tools"].append(tech)

        return categories
