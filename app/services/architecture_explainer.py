"""LLM-driven architecture explanation service."""

import json
from typing import Dict, List, Any, Optional

from app.llm.base import LLMProvider
from app.utils.logger import app_logger
from app.utils.audit import log_llm_call


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
                                 session_id: str = "unknown") -> str:
        """Generate LLM-driven explanation of how the tech stack works together.
        
        Args:
            tech_stack: List of technologies in the stack
            requirements: User requirements for context
            session_id: Session ID for tracking
            
        Returns:
            Architecture explanation string
        """
        if not self.llm_provider or not tech_stack:
            return self._generate_fallback_explanation(tech_stack, requirements)
        
        try:
            explanation = await self._generate_llm_explanation(tech_stack, requirements, session_id)
            if explanation:
                return explanation
        except Exception as e:
            app_logger.error(f"Failed to generate LLM architecture explanation: {e}")
        
        # Fallback to rule-based explanation
        return self._generate_fallback_explanation(tech_stack, requirements)
    
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
        # Prepare context for LLM
        prompt = {
            "system": """You are a senior software architect with expertise in system design and technology integration. 
Your task is to explain how a technology stack works together to solve a specific automation requirement.

Focus on:
1. How the technologies complement each other
2. The data flow and system architecture
3. Why this combination is effective for the requirements
4. How the components interact and communicate

Keep the explanation clear, practical, and focused on the specific use case.
Avoid generic descriptions - be specific about how these technologies address the actual requirements.""",
            
            "user": f"""
**Requirements:**
- Description: {requirements.get('description', 'Not specified')}
- Domain: {requirements.get('domain', 'Not specified')}
- Volume: {requirements.get('volume', {})}
- Integrations: {requirements.get('integrations', [])}
- Data sensitivity: {requirements.get('data_sensitivity', 'Not specified')}
- Compliance: {requirements.get('compliance', [])}

**Technology Stack:**
{', '.join(tech_stack)}

**Instructions:**
Explain how these technologies work together to address the specific requirements above. 
Focus on:
1. The overall system architecture and data flow
2. How each technology contributes to solving the problem
3. Why this combination is well-suited for the requirements
4. How the components communicate and integrate

Provide a clear, practical explanation in 2-3 paragraphs. Be specific to this use case, not generic.
"""
        }
        
        try:
            # Track timing for audit
            from datetime import datetime
            start_time = datetime.now()
            
            response = await self.llm_provider.generate(prompt)
            
            # Calculate latency
            end_time = datetime.now()
            latency_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Log the LLM call with response
            await log_llm_call(
                session_id=session_id,
                provider=self.llm_provider.__class__.__name__,
                model=getattr(self.llm_provider, 'model', 'unknown'),
                latency_ms=latency_ms,
                prompt=str(prompt),
                response=str(response)
            )
            
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