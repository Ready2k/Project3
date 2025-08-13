"""LLM-driven architecture explanation service."""

import json
from typing import Dict, List, Any, Optional

from app.llm.base import LLMProvider
from app.utils.logger import app_logger


class ArchitectureExplainer:
    """Service for generating LLM-driven architecture explanations."""
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """Initialize architecture explainer.
        
        Args:
            llm_provider: LLM provider for generating explanations
        """
        self.llm_provider = llm_provider
    
    async def explain_architecture(self, 
                                 tech_stack: List[str],
                                 requirements: Dict[str, Any],
                                 session_id: str = "unknown") -> tuple[List[str], str]:
        """Generate LLM-driven tech stack and explanation based on requirements.
        
        Args:
            tech_stack: Initial tech stack (may be enhanced by LLM)
            requirements: User requirements for context
            session_id: Session ID for tracking
            
        Returns:
            Tuple of (enhanced_tech_stack, architecture_explanation)
        """
        if not self.llm_provider:
            return tech_stack, self._generate_fallback_explanation(tech_stack, requirements)
        
        try:
            # First, generate an appropriate tech stack based on requirements
            enhanced_tech_stack = await self._generate_tech_stack_for_requirements(requirements, session_id)
            
            # Then explain how it works together
            explanation = await self._generate_llm_explanation(enhanced_tech_stack, requirements, session_id)
            if explanation:
                return enhanced_tech_stack, explanation
        except Exception as e:
            app_logger.error(f"Failed to generate LLM architecture explanation: {e}")
        
        # Fallback to rule-based explanation
        return tech_stack, self._generate_fallback_explanation(tech_stack, requirements)
    
    async def _generate_tech_stack_for_requirements(self,
                                                  requirements: Dict[str, Any],
                                                  session_id: str) -> List[str]:
        """Generate appropriate tech stack based on specific requirements.
        
        Args:
            requirements: User requirements
            session_id: Session ID for tracking
            
        Returns:
            List of recommended technologies
        """
        # Create a focused prompt for tech stack generation
        prompt = f"""You are a senior software architect focusing around AI and Agentic systems. Based on the specific requirements below, recommend a focused, practical technology stack.

**Requirements:**
- Description: {requirements.get('description', 'Not specified')}
- Domain: {requirements.get('domain', 'Not specified')}
- Volume/Scale: {requirements.get('volume', 'Not specified')}
- Integrations needed: {requirements.get('integrations', [])}
- Data sensitivity: {requirements.get('data_sensitivity', 'Not specified')}
- Compliance requirements: {requirements.get('compliance', [])}

**Instructions:**
1. Analyze the specific requirements carefully
2. Recommend upto 10 technologies that directly address these needs, you must include all technologies to make it work.
3. Focus on practical, proven technologies BUT you can include new emerging technologies if they are a better fit
4. Consider the domain, scale, performance and integration requirements
5. Include: programming language, framework, database, key libraries/tools

Respond with ONLY a valid JSON object (no markdown, no extra text):
{{
    "tech_stack": ["Technology1", "Technology2", "Technology3", ...],
    "reasoning": "Brief explanation of why these technologies were chosen for these specific requirements"
}}

IMPORTANT: Return only the JSON object, no other text or formatting."""

        try:
            response = await self.llm_provider.generate(prompt, purpose="tech_stack_generation")
            
            # Parse JSON response (handle markdown formatting)
            import json
            import re
            
            try:
                # Clean the response - remove markdown code blocks if present
                cleaned_response = response.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response.replace('```json', '').replace('```', '').strip()
                elif cleaned_response.startswith('```'):
                    cleaned_response = cleaned_response.replace('```', '').strip()
                
                # Try to extract JSON from the response
                json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    result = json.loads(json_str)
                    tech_stack = result.get("tech_stack", [])
                    app_logger.info(f"Generated tech stack ({len(tech_stack)} items): {tech_stack}")
                    return tech_stack
                else:
                    raise json.JSONDecodeError("No JSON object found", cleaned_response, 0)
                    
            except json.JSONDecodeError as e:
                app_logger.warning(f"Failed to parse tech stack JSON: {e}, extracting from text")
                # Fallback: extract technologies from text
                return self._extract_tech_from_text(response)
                
        except Exception as e:
            app_logger.error(f"Failed to generate tech stack: {e}")
            # Return a basic tech stack based on domain
            return self._get_domain_based_tech_stack(requirements)
    
    def _extract_tech_from_text(self, text: str) -> List[str]:
        """Extract technology names from text response."""
        # Simple extraction - look for common tech patterns
        import re
        tech_patterns = [
            r'\b(Python|JavaScript|Java|Go|Rust|TypeScript|C#)\b',
            r'\b(FastAPI|Django|Flask|Express|React|Vue|Angular|Spring)\b',
            r'\b(PostgreSQL|MySQL|MongoDB|Redis|SQLite|Elasticsearch)\b',
            r'\b(Docker|Kubernetes|AWS|Azure|GCP|Nginx|Apache)\b',
            r'\b(Celery|RabbitMQ|Kafka|WebSocket|GraphQL|REST)\b'
        ]
        
        technologies = []
        for pattern in tech_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            technologies.extend(matches)
        
        # Remove duplicates and limit to 8
        return list(dict.fromkeys(technologies))[:8]
    
    def _get_domain_based_tech_stack(self, requirements: Dict[str, Any]) -> List[str]:
        """Get basic tech stack based on domain."""
        domain = requirements.get('domain', '').lower()
        
        if 'data' in domain or 'analytics' in domain:
            return ["Python", "FastAPI", "PostgreSQL", "Pandas", "Redis", "Docker"]
        elif 'web' in domain or 'api' in domain:
            return ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "Nginx"]
        elif 'mobile' in domain:
            return ["Python", "FastAPI", "PostgreSQL", "WebSocket", "Redis", "Mobile SDK"]
        else:
            return ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "Monitoring"]
    
    async def _generate_llm_explanation(self, 
                                      tech_stack: List[str],
                                      requirements: Dict[str, Any],
                                      session_id: str) -> Optional[str]:
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
        tech_stack_str = ', '.join(tech_stack)
        description = requirements.get('description', 'Not specified')
        domain = requirements.get('domain', 'Not specified')
        volume = requirements.get('volume', {})
        integrations = requirements.get('integrations', [])
        data_sensitivity = requirements.get('data_sensitivity', 'Not specified')
        compliance = requirements.get('compliance', [])
        
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

**Technology Stack (use ALL of these technologies in your explanation):**
{tech_stack_str}

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
            app_logger.info(f"Generating explanation for tech stack ({len(tech_stack)} items): {tech_stack}")
            response = await self.llm_provider.generate(prompt, purpose="tech_stack_explanation")
            
            # Clean up the response
            if isinstance(response, str):
                explanation = response.strip()
                app_logger.info(f"Generated LLM architecture explanation ({len(explanation)} chars)")
                return explanation
            elif isinstance(response, dict):
                # Handle structured response
                explanation = response.get("explanation", str(response))
                app_logger.info(f"Generated LLM architecture explanation from dict ({len(explanation)} chars)")
                return explanation
            
            return None
            
        except Exception as e:
            app_logger.error(f"Failed to generate LLM architecture explanation: {e}")
            return None
    
    def _generate_fallback_explanation(self, 
                                     tech_stack: List[str],
                                     requirements: Dict[str, Any]) -> str:
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
            core_tech = list(categories.get("languages", [])) + list(categories.get("frameworks", []))
            explanation_parts.append(f"The system is built using {', '.join(core_tech[:2])} as the core technology stack, providing a robust foundation for automation.")
        
        # Data layer
        if categories.get("databases"):
            db_tech = ', '.join(categories["databases"])
            explanation_parts.append(f"Data persistence is handled by {db_tech}, ensuring reliable storage and fast retrieval of information.")
        
        # Integration layer
        if categories.get("tools"):
            integration_tools = [tool for tool in categories["tools"] if any(keyword in tool.lower() for keyword in ["http", "api", "request", "celery", "queue"])]
            if integration_tools:
                explanation_parts.append(f"System integration and communication is managed through {', '.join(integration_tools[:2])}, enabling seamless data exchange.")
        
        # Infrastructure
        if categories.get("services"):
            infra_tech = ', '.join(categories["services"])
            explanation_parts.append(f"The infrastructure leverages {infra_tech} for scalable deployment and monitoring.")
        
        # Add flow description based on requirements
        domain = requirements.get('domain') or ''
        domain = domain.lower() if domain else ''
        if 'data' in domain:
            explanation_parts.append("The typical workflow involves data ingestion, processing, validation, and storage, with monitoring throughout the pipeline.")
        elif 'api' in domain:
            explanation_parts.append("The system follows an API-first approach, with request handling, business logic processing, and response formatting.")
        else:
            explanation_parts.append("The components work together in a coordinated workflow, with each technology handling its specialized function while maintaining system reliability.")
        
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
            "libraries": []
        }
        
        for tech in tech_stack:
            tech_lower = tech.lower()
            
            # Languages
            if tech_lower in ["python", "javascript", "java", "go", "rust", "typescript", "c#", "php"]:
                categories["languages"].append(tech)
            # Frameworks
            elif tech_lower in ["fastapi", "django", "flask", "express", "react", "vue", "angular", "spring"]:
                categories["frameworks"].append(tech)
            # Databases
            elif tech_lower in ["postgresql", "mysql", "mongodb", "redis", "elasticsearch", "sqlite", "sqlalchemy"]:
                categories["databases"].append(tech)
            # Cloud Services
            elif tech_lower in ["aws", "azure", "gcp", "docker", "kubernetes", "lambda", "prometheus"]:
                categories["services"].append(tech)
            # Tools and Libraries
            else:
                if any(keyword in tech_lower for keyword in ["lib", "sdk", "api"]):
                    categories["libraries"].append(tech)
                else:
                    categories["tools"].append(tech)
        
        return categories