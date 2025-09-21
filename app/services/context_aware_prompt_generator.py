"""Context-aware LLM prompt generator for tech stack generation."""

import json
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime

from app.services.requirement_parsing.base import TechContext, ParsedRequirements
from app.services.catalog.intelligent_manager import IntelligentCatalogManager
from app.services.catalog.models import TechEntry, EcosystemType
from app.utils.imports import require_service


@dataclass
class PromptContext:
    """Context information for prompt generation."""
    explicit_technologies: Dict[str, float]  # tech_name -> confidence
    contextual_technologies: Dict[str, float]
    ecosystem_preference: Optional[str]
    domain_context: str
    integration_requirements: List[str]
    banned_tools: Set[str]
    required_integrations: List[str]
    catalog_technologies: Dict[str, List[TechEntry]]  # category -> technologies
    priority_instructions: List[str]
    selection_rules: List[str]


@dataclass
class PromptValidationResult:
    """Result of prompt validation."""
    is_valid: bool
    issues: List[str]
    suggestions: List[str]
    effectiveness_score: float


class ContextAwareLLMPromptGenerator:
    """Context-aware LLM prompt generator with technology prioritization."""
    
    def __init__(self, catalog_manager: Optional[IntelligentCatalogManager] = None):
        """Initialize the prompt generator.
        
        Args:
            catalog_manager: Technology catalog manager
        """
        self.catalog_manager = catalog_manager or IntelligentCatalogManager()
        
        # Get logger from service registry
        self.logger = require_service('logger', context='ContextAwareLLMPromptGenerator')
        
        # Initialize prompt templates and rules
        self._init_prompt_templates()
        self._init_selection_rules()
        self._init_priority_instructions()
    
    def _init_prompt_templates(self) -> None:
        """Initialize prompt templates for different scenarios."""
        self.base_template = """You are a senior software architect specializing in technology stack selection for automation and AI systems.

Your task is to recommend the most appropriate technology stack based on user requirements, with STRICT PRIORITY given to explicitly mentioned technologies.

**CRITICAL PRIORITY RULES:**
{priority_instructions}

**EXPLICIT TECHNOLOGIES (PRIORITY 1.0 - MUST INCLUDE):**
{explicit_technologies_section}

**CONTEXTUAL TECHNOLOGIES (PRIORITY 0.8):**
{contextual_technologies_section}

**AVAILABLE CATALOG TECHNOLOGIES (Organized by Relevance):**
{catalog_technologies_section}

**REQUIREMENTS CONTEXT:**
{requirements_context}

**CONSTRAINTS:**
{constraints_section}

**TECHNOLOGY SELECTION RULES:**
{selection_rules}

**REASONING REQUIREMENTS:**
You MUST provide detailed reasoning for each technology selection including:
1. Why this technology was chosen over alternatives
2. How it addresses specific requirements
3. Integration considerations with other selected technologies
4. Confidence level in the selection (0.0-1.0)

**RESPONSE FORMAT:**
Respond with a JSON object containing:
{{
    "tech_stack": [
        {{
            "name": "Technology Name",
            "reason": "Detailed explanation of selection",
            "confidence": 0.95,
            "priority_level": "explicit|contextual|inferred",
            "addresses_requirements": ["req1", "req2"]
        }}
    ],
    "overall_reasoning": "Brief explanation of the overall stack composition",
    "ecosystem_consistency": "Explanation of ecosystem choices",
    "alternatives_considered": [
        {{
            "technology": "Alternative Name",
            "reason_not_selected": "Why this wasn't chosen"
        }}
    ],
    "integration_notes": "Notes about how technologies integrate together",
    "confidence_assessment": {{
        "overall_confidence": 0.85,
        "risk_factors": ["factor1", "factor2"],
        "validation_notes": "Additional validation considerations"
    }}
}}"""
        
        self.ecosystem_focused_template = """You are a senior software architect with expertise in {ecosystem} ecosystem technologies.

**ECOSYSTEM FOCUS: {ecosystem_name}**
Your primary goal is to recommend technologies that work well within the {ecosystem} ecosystem while respecting explicit technology requirements.

{base_content}

**ECOSYSTEM-SPECIFIC CONSIDERATIONS:**
{ecosystem_considerations}"""
        
        self.domain_focused_template = """You are a senior software architect with expertise in {domain} domain solutions.

**DOMAIN FOCUS: {domain_name}**
Your primary goal is to recommend technologies optimized for {domain} use cases while respecting explicit technology requirements.

{base_content}

**DOMAIN-SPECIFIC CONSIDERATIONS:**
{domain_considerations}"""
    
    def _init_selection_rules(self) -> None:
        """Initialize technology selection rules."""
        self.base_selection_rules = [
            "1. MANDATORY: Include ALL explicit technologies that exist in the catalog",
            "2. For missing explicit technologies, use closest alternatives and flag for catalog addition",
            "3. Prioritize technologies from the same ecosystem when ecosystem preference is detected",
            "4. Ensure compatibility between selected technologies",
            "5. Respect all banned technologies and constraints",
            "6. Include required integrations in the stack",
            "7. Prefer mature, well-supported technologies for production use",
            "8. Consider performance, scalability, and maintainability",
            "9. Limit total technologies to 8-15 for focused, practical stacks",
            "10. Provide alternatives for high-risk or experimental technologies"
        ]
        
        self.ecosystem_selection_rules = {
            'aws': [
                "Prefer AWS-native services when available",
                "Use AWS SDK and tools for integration",
                "Consider AWS Lambda for serverless needs",
                "Use AWS managed services to reduce operational overhead"
            ],
            'azure': [
                "Prefer Azure-native services when available", 
                "Use Azure SDK and tools for integration",
                "Consider Azure Functions for serverless needs",
                "Leverage Azure Active Directory for authentication"
            ],
            'gcp': [
                "Prefer Google Cloud-native services when available",
                "Use Google Cloud SDK and tools for integration", 
                "Consider Google Cloud Functions for serverless needs",
                "Leverage Google Cloud's ML and data analytics strengths"
            ],
            'open_source': [
                "Prioritize open-source alternatives",
                "Ensure license compatibility",
                "Consider community support and maintenance",
                "Evaluate long-term sustainability"
            ]
        }
        
        self.domain_selection_rules = {
            'data_processing': [
                "Prioritize technologies optimized for data throughput",
                "Consider data format compatibility (JSON, CSV, Parquet, etc.)",
                "Include appropriate data storage solutions",
                "Ensure scalability for large datasets"
            ],
            'web_api': [
                "Prioritize technologies optimized for API performance",
                "Include proper authentication and authorization",
                "Consider API documentation and testing tools",
                "Ensure proper error handling and monitoring"
            ],
            'ml_ai': [
                "Prioritize technologies with strong ML/AI ecosystem support",
                "Include model serving and deployment capabilities",
                "Consider data preprocessing and feature engineering tools",
                "Ensure GPU/compute optimization where needed"
            ],
            'automation': [
                "Prioritize technologies for workflow orchestration",
                "Include monitoring and alerting capabilities",
                "Consider error handling and retry mechanisms",
                "Ensure scalability and reliability"
            ]
        }
    
    def _init_priority_instructions(self) -> None:
        """Initialize priority instructions for different scenarios."""
        self.base_priority_instructions = [
            "EXPLICIT TECHNOLOGIES have absolute priority - they MUST be included if they exist in the catalog",
            "If an explicit technology is missing from catalog, find the closest alternative and flag for addition",
            "CONTEXTUAL TECHNOLOGIES should be strongly considered but can be replaced if better alternatives exist",
            "CATALOG TECHNOLOGIES are organized by relevance - prefer those listed first in each category",
            "When choosing between similar technologies, prefer those with higher confidence scores",
            "Maintain ecosystem consistency when possible - don't mix AWS and Azure services unnecessarily"
        ]
        
        self.ecosystem_priority_instructions = {
            'aws': [
                "AWS technologies have elevated priority when ecosystem preference is AWS",
                "Prefer AWS managed services over self-hosted alternatives",
                "Use AWS SDK and integration tools for seamless connectivity"
            ],
            'azure': [
                "Azure technologies have elevated priority when ecosystem preference is Azure", 
                "Prefer Azure managed services over self-hosted alternatives",
                "Use Azure SDK and integration tools for seamless connectivity"
            ],
            'gcp': [
                "Google Cloud technologies have elevated priority when ecosystem preference is GCP",
                "Prefer Google Cloud managed services over self-hosted alternatives", 
                "Use Google Cloud SDK and integration tools for seamless connectivity"
            ]
        }
    
    def generate_context_aware_prompt(self, 
                                    tech_context: TechContext,
                                    requirements: Dict[str, Any],
                                    constraints: Optional[Dict[str, Any]] = None) -> str:
        """Generate context-aware prompt for LLM tech stack generation.
        
        Args:
            tech_context: Technology context from requirement parsing
            requirements: Original user requirements
            constraints: Additional constraints
            
        Returns:
            Generated prompt string
        """
        self.logger.info("Generating context-aware LLM prompt")
        
        # Build prompt context
        prompt_context = self._build_prompt_context(tech_context, requirements, constraints)
        
        # Select appropriate template
        template_type = self._select_template(prompt_context)
        
        # Generate sections
        sections = self._generate_prompt_sections(prompt_context)
        
        # Fill template based on type
        if template_type == "ecosystem_focused":
            # Fill ecosystem template
            sections["base_content"] = self.base_template.format(**sections)
            prompt = self.ecosystem_focused_template.format(**sections)
        elif template_type == "domain_focused":
            # Fill domain template
            sections["base_content"] = self.base_template.format(**sections)
            prompt = self.domain_focused_template.format(**sections)
        else:
            # Use base template
            prompt = self.base_template.format(**sections)
        
        # Validate prompt
        validation_result = self.validate_prompt(prompt, prompt_context)
        if not validation_result.is_valid:
            self.logger.warning(f"Generated prompt has issues: {validation_result.issues}")
            # Apply fixes if possible
            prompt = self._apply_prompt_fixes(prompt, validation_result)
        
        self.logger.info(f"Generated prompt with effectiveness score: {validation_result.effectiveness_score:.2f}")
        return prompt
    
    def _build_prompt_context(self, 
                            tech_context: TechContext,
                            requirements: Dict[str, Any],
                            constraints: Optional[Dict[str, Any]] = None) -> PromptContext:
        """Build comprehensive prompt context.
        
        Args:
            tech_context: Technology context
            requirements: User requirements
            constraints: Additional constraints
            
        Returns:
            PromptContext object
        """
        # Organize catalog technologies by relevance
        catalog_technologies = self._organize_catalog_by_relevance(tech_context)
        
        # Build priority instructions
        priority_instructions = self._build_priority_instructions(tech_context)
        
        # Build selection rules
        selection_rules = self._build_selection_rules(tech_context)
        
        # Extract constraints
        banned_tools = set(tech_context.banned_tools)
        if constraints:
            banned_tools.update(constraints.get("banned_tools", []))
        
        required_integrations = list(tech_context.integration_requirements)
        if constraints:
            required_integrations.extend(constraints.get("required_integrations", []))
        
        return PromptContext(
            explicit_technologies=tech_context.explicit_technologies,
            contextual_technologies=tech_context.contextual_technologies,
            ecosystem_preference=tech_context.ecosystem_preference,
            domain_context=tech_context.domain_context.primary_domain or "general",
            integration_requirements=tech_context.integration_requirements,
            banned_tools=banned_tools,
            required_integrations=required_integrations,
            catalog_technologies=catalog_technologies,
            priority_instructions=priority_instructions,
            selection_rules=selection_rules
        )
    
    def _organize_catalog_by_relevance(self, tech_context: TechContext) -> Dict[str, List[TechEntry]]:
        """Organize catalog technologies by relevance to context.
        
        Args:
            tech_context: Technology context
            
        Returns:
            Dictionary mapping categories to ordered lists of technologies
        """
        organized_catalog = {}
        
        # Get all technologies from catalog
        all_technologies = list(self.catalog_manager.technologies.values())
        
        # Group by category
        by_category = {}
        for tech in all_technologies:
            if tech.category not in by_category:
                by_category[tech.category] = []
            by_category[tech.category].append(tech)
        
        # Sort each category by relevance
        for category, techs in by_category.items():
            # Calculate relevance scores
            scored_techs = []
            for tech in techs:
                score = self._calculate_technology_relevance(tech, tech_context)
                scored_techs.append((tech, score))
            
            # Sort by score (descending) and take top technologies
            scored_techs.sort(key=lambda x: x[1], reverse=True)
            organized_catalog[category] = [tech for tech, score in scored_techs[:10]]  # Limit per category
        
        return organized_catalog
    
    def _calculate_technology_relevance(self, tech: TechEntry, tech_context: TechContext) -> float:
        """Calculate relevance score for a technology given the context.
        
        Args:
            tech: Technology entry
            tech_context: Technology context
            
        Returns:
            Relevance score (0.0-1.0)
        """
        score = 0.0
        
        # Explicit mention boost
        if tech.canonical_name in tech_context.explicit_technologies:
            score += 1.0
        
        # Contextual mention boost
        if tech.canonical_name in tech_context.contextual_technologies:
            score += 0.8
        
        # Ecosystem alignment boost
        if (tech_context.ecosystem_preference and 
            tech.ecosystem and 
            tech.ecosystem.value == tech_context.ecosystem_preference):
            score += 0.6
        
        # Domain alignment boost
        if tech_context.domain_context.primary_domain:
            domain_keywords = {
                'data_processing': ['data', 'processing', 'analytics', 'etl'],
                'web_api': ['api', 'web', 'http', 'rest', 'graphql'],
                'ml_ai': ['ai', 'ml', 'machine learning', 'neural', 'model'],
                'automation': ['automation', 'workflow', 'orchestration', 'scheduler']
            }
            
            domain = tech_context.domain_context.primary_domain
            if domain in domain_keywords:
                tech_text = f"{tech.name} {tech.description} {' '.join(tech.tags)}".lower()
                keyword_matches = sum(1 for keyword in domain_keywords[domain] if keyword in tech_text)
                score += keyword_matches * 0.2
        
        # Integration requirement boost
        for integration in tech_context.integration_requirements:
            if integration.lower() in tech.canonical_name.lower():
                score += 0.4
            if any(integration.lower() in use_case.lower() for use_case in tech.use_cases):
                score += 0.3
        
        # Maturity and confidence boost
        if tech.maturity.value == 'stable':
            score += 0.2
        elif tech.maturity.value == 'mature':
            score += 0.3
        
        if tech.confidence_score:
            score += tech.confidence_score * 0.1
        
        # Penalty for banned technologies
        for banned in tech_context.banned_tools:
            if banned.lower() in tech.canonical_name.lower():
                score = 0.0
                break
        
        return min(score, 1.0)
    
    def _select_template(self, prompt_context: PromptContext) -> str:
        """Select appropriate prompt template based on context.
        
        Args:
            prompt_context: Prompt context
            
        Returns:
            Selected template string
        """
        # Use ecosystem-focused template if strong ecosystem preference
        if prompt_context.ecosystem_preference:
            ecosystem_techs = len([
                tech for techs in prompt_context.catalog_technologies.values()
                for tech in techs
                if tech.ecosystem and tech.ecosystem.value == prompt_context.ecosystem_preference
            ])
            
            if ecosystem_techs > 5:  # Significant ecosystem presence
                return "ecosystem_focused"
        
        # Use domain-focused template if specific domain
        if prompt_context.domain_context != "general":
            return "domain_focused"
        
        # Default to base template
        return "base"
    
    def _generate_prompt_sections(self, prompt_context: PromptContext) -> Dict[str, str]:
        """Generate all sections for the prompt.
        
        Args:
            prompt_context: Prompt context
            
        Returns:
            Dictionary of section content
        """
        sections = {}
        
        # Priority instructions
        sections["priority_instructions"] = self._format_priority_instructions(prompt_context.priority_instructions)
        
        # Explicit technologies section
        sections["explicit_technologies_section"] = self._format_explicit_technologies(prompt_context.explicit_technologies)
        
        # Contextual technologies section
        sections["contextual_technologies_section"] = self._format_contextual_technologies(prompt_context.contextual_technologies)
        
        # Catalog technologies section
        sections["catalog_technologies_section"] = self._format_catalog_technologies(prompt_context.catalog_technologies)
        
        # Requirements context
        sections["requirements_context"] = self._format_requirements_context(prompt_context)
        
        # Constraints section
        sections["constraints_section"] = self._format_constraints(prompt_context)
        
        # Selection rules
        sections["selection_rules"] = self._format_selection_rules(prompt_context.selection_rules)
        
        # Ecosystem-specific sections (if applicable)
        if prompt_context.ecosystem_preference:
            sections["ecosystem_name"] = prompt_context.ecosystem_preference.upper()
            sections["ecosystem"] = prompt_context.ecosystem_preference
            sections["ecosystem_considerations"] = self._format_ecosystem_considerations(prompt_context.ecosystem_preference)
        
        # Domain-specific sections (if applicable)
        if prompt_context.domain_context != "general":
            sections["domain_name"] = prompt_context.domain_context.title()
            sections["domain"] = prompt_context.domain_context
            sections["domain_considerations"] = self._format_domain_considerations(prompt_context.domain_context)
        
        # Base content for specialized templates (will be filled later)
        sections["base_content"] = ""
        
        return sections
    
    def _build_priority_instructions(self, tech_context: TechContext) -> List[str]:
        """Build priority instructions based on context.
        
        Args:
            tech_context: Technology context
            
        Returns:
            List of priority instructions
        """
        instructions = self.base_priority_instructions.copy()
        
        # Add ecosystem-specific instructions
        if tech_context.ecosystem_preference and tech_context.ecosystem_preference in self.ecosystem_priority_instructions:
            instructions.extend(self.ecosystem_priority_instructions[tech_context.ecosystem_preference])
        
        # Add context-specific instructions
        if len(tech_context.explicit_technologies) > 0:
            instructions.append(f"You have {len(tech_context.explicit_technologies)} explicit technology requirements that are NON-NEGOTIABLE")
        
        if tech_context.banned_tools:
            instructions.append(f"STRICTLY AVOID these {len(tech_context.banned_tools)} banned technologies under all circumstances")
        
        return instructions
    
    def _build_selection_rules(self, tech_context: TechContext) -> List[str]:
        """Build selection rules based on context.
        
        Args:
            tech_context: Technology context
            
        Returns:
            List of selection rules
        """
        rules = self.base_selection_rules.copy()
        
        # Add ecosystem-specific rules
        if tech_context.ecosystem_preference and tech_context.ecosystem_preference in self.ecosystem_selection_rules:
            ecosystem_rules = self.ecosystem_selection_rules[tech_context.ecosystem_preference]
            rules.extend([f"ECOSYSTEM: {rule}" for rule in ecosystem_rules])
        
        # Add domain-specific rules
        if (tech_context.domain_context.primary_domain and 
            tech_context.domain_context.primary_domain in self.domain_selection_rules):
            domain_rules = self.domain_selection_rules[tech_context.domain_context.primary_domain]
            rules.extend([f"DOMAIN: {rule}" for rule in domain_rules])
        
        return rules
    
    def _format_priority_instructions(self, instructions: List[str]) -> str:
        """Format priority instructions for prompt."""
        return "\n".join(f"• {instruction}" for instruction in instructions)
    
    def _format_explicit_technologies(self, explicit_techs: Dict[str, float]) -> str:
        """Format explicit technologies section."""
        if not explicit_techs:
            return "None specified - use contextual and catalog technologies"
        
        lines = []
        for tech, confidence in sorted(explicit_techs.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"• {tech} (confidence: {confidence:.2f}) - MUST INCLUDE")
        
        return "\n".join(lines)
    
    def _format_contextual_technologies(self, contextual_techs: Dict[str, float]) -> str:
        """Format contextual technologies section."""
        if not contextual_techs:
            return "None inferred from context"
        
        lines = []
        for tech, confidence in sorted(contextual_techs.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"• {tech} (confidence: {confidence:.2f}) - STRONGLY CONSIDER")
        
        return "\n".join(lines)
    
    def _format_catalog_technologies(self, catalog_techs: Dict[str, List[TechEntry]]) -> str:
        """Format catalog technologies section."""
        lines = []
        
        # Sort categories by relevance (categories with more relevant techs first)
        sorted_categories = sorted(
            catalog_techs.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        for category, techs in sorted_categories[:8]:  # Limit categories
            if not techs:
                continue
                
            lines.append(f"\n**{category.title()}:**")
            for tech in techs[:8]:  # Limit techs per category
                ecosystem_info = f" [{tech.ecosystem.value}]" if tech.ecosystem else ""
                maturity_info = f" ({tech.maturity.value})" if tech.maturity else ""
                lines.append(f"  • {tech.canonical_name}{ecosystem_info}{maturity_info} - {tech.description}")
        
        return "\n".join(lines) if lines else "No relevant catalog technologies found"
    
    def _format_requirements_context(self, prompt_context: PromptContext) -> str:
        """Format requirements context section."""
        lines = [
            f"• Domain: {prompt_context.domain_context}",
            f"• Ecosystem Preference: {prompt_context.ecosystem_preference or 'None'}",
            f"• Integration Requirements: {', '.join(prompt_context.integration_requirements) or 'None'}",
            f"• Required Integrations: {', '.join(prompt_context.required_integrations) or 'None'}"
        ]
        return "\n".join(lines)
    
    def _format_constraints(self, prompt_context: PromptContext) -> str:
        """Format constraints section."""
        lines = []
        
        if prompt_context.banned_tools:
            banned_list = ', '.join(sorted(prompt_context.banned_tools))
            lines.append(f"• Banned Technologies: {banned_list}")
        else:
            lines.append("• Banned Technologies: None")
        
        if prompt_context.required_integrations:
            required_list = ', '.join(prompt_context.required_integrations)
            lines.append(f"• Required Integrations: {required_list}")
        else:
            lines.append("• Required Integrations: None")
        
        return "\n".join(lines)
    
    def _format_selection_rules(self, rules: List[str]) -> str:
        """Format selection rules section."""
        return "\n".join(rules)
    
    def _format_ecosystem_considerations(self, ecosystem: str) -> str:
        """Format ecosystem-specific considerations."""
        considerations = {
            'aws': [
                "Leverage AWS managed services to reduce operational overhead",
                "Use AWS SDK for seamless integration between services",
                "Consider AWS Lambda for serverless compute needs",
                "Use AWS CloudFormation or CDK for infrastructure as code",
                "Implement proper IAM roles and policies for security"
            ],
            'azure': [
                "Leverage Azure managed services to reduce operational overhead",
                "Use Azure SDK for seamless integration between services", 
                "Consider Azure Functions for serverless compute needs",
                "Use Azure Resource Manager templates for infrastructure as code",
                "Implement Azure Active Directory for authentication and authorization"
            ],
            'gcp': [
                "Leverage Google Cloud managed services to reduce operational overhead",
                "Use Google Cloud SDK for seamless integration between services",
                "Consider Google Cloud Functions for serverless compute needs", 
                "Use Google Cloud Deployment Manager for infrastructure as code",
                "Leverage Google Cloud's strengths in ML and data analytics"
            ]
        }
        
        ecosystem_considerations = considerations.get(ecosystem, [])
        return "\n".join(f"• {consideration}" for consideration in ecosystem_considerations)
    
    def _format_domain_considerations(self, domain: str) -> str:
        """Format domain-specific considerations."""
        considerations = {
            'data_processing': [
                "Prioritize technologies optimized for data throughput and processing",
                "Consider data format compatibility and transformation capabilities",
                "Include appropriate data storage and retrieval solutions",
                "Ensure scalability for large datasets and high-volume processing",
                "Include monitoring and observability for data pipelines"
            ],
            'web_api': [
                "Prioritize technologies optimized for API performance and scalability",
                "Include proper authentication, authorization, and security measures",
                "Consider API documentation, testing, and monitoring tools",
                "Ensure proper error handling, logging, and debugging capabilities",
                "Include load balancing and caching solutions for high availability"
            ],
            'ml_ai': [
                "Prioritize technologies with strong ML/AI ecosystem support",
                "Include model training, serving, and deployment capabilities",
                "Consider data preprocessing, feature engineering, and model management tools",
                "Ensure GPU/compute optimization and resource management",
                "Include experiment tracking and model versioning solutions"
            ],
            'automation': [
                "Prioritize technologies for workflow orchestration and task scheduling",
                "Include comprehensive monitoring, alerting, and observability",
                "Consider error handling, retry mechanisms, and fault tolerance",
                "Ensure scalability, reliability, and high availability",
                "Include configuration management and deployment automation"
            ]
        }
        
        domain_considerations = considerations.get(domain, [])
        return "\n".join(f"• {consideration}" for consideration in domain_considerations)
    
    def validate_prompt(self, prompt: str, prompt_context: PromptContext) -> PromptValidationResult:
        """Validate generated prompt for effectiveness and completeness.
        
        Args:
            prompt: Generated prompt
            prompt_context: Prompt context used for generation
            
        Returns:
            PromptValidationResult
        """
        issues = []
        suggestions = []
        effectiveness_score = 1.0
        
        # Check for required sections
        required_sections = [
            "EXPLICIT TECHNOLOGIES",
            "CONTEXTUAL TECHNOLOGIES", 
            "AVAILABLE CATALOG TECHNOLOGIES",
            "CONSTRAINTS",
            "TECHNOLOGY SELECTION RULES",
            "REASONING REQUIREMENTS"
        ]
        
        for section in required_sections:
            if section not in prompt:
                issues.append(f"Missing required section: {section}")
                effectiveness_score -= 0.1
        
        # Check explicit technologies are properly highlighted
        if prompt_context.explicit_technologies:
            for tech in prompt_context.explicit_technologies:
                if tech not in prompt:
                    issues.append(f"Explicit technology '{tech}' not mentioned in prompt")
                    effectiveness_score -= 0.15
        
        # Check banned technologies are mentioned
        if prompt_context.banned_tools:
            banned_mentioned = any(banned in prompt for banned in prompt_context.banned_tools)
            if not banned_mentioned:
                issues.append("Banned technologies not clearly specified in prompt")
                effectiveness_score -= 0.1
        
        # Check prompt length (should be comprehensive but not overwhelming)
        if len(prompt) < 1000:
            suggestions.append("Prompt might be too short for comprehensive guidance")
            effectiveness_score -= 0.05
        elif len(prompt) > 8000:
            suggestions.append("Prompt might be too long and could overwhelm the LLM")
            effectiveness_score -= 0.05
        
        # Check for clear JSON response format
        if "JSON" not in prompt or "{" not in prompt:
            issues.append("JSON response format not clearly specified")
            effectiveness_score -= 0.1
        
        # Check for reasoning requirements
        if "reasoning" not in prompt.lower() and "explanation" not in prompt.lower():
            issues.append("Reasoning requirements not clearly specified")
            effectiveness_score -= 0.1
        
        # Ensure effectiveness score is within bounds
        effectiveness_score = max(0.0, min(1.0, effectiveness_score))
        
        return PromptValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            suggestions=suggestions,
            effectiveness_score=effectiveness_score
        )
    
    def _apply_prompt_fixes(self, prompt: str, validation_result: PromptValidationResult) -> str:
        """Apply fixes to improve prompt based on validation results.
        
        Args:
            prompt: Original prompt
            validation_result: Validation result with issues
            
        Returns:
            Fixed prompt
        """
        fixed_prompt = prompt
        
        # Add missing JSON format specification if needed
        if "JSON response format not clearly specified" in validation_result.issues:
            json_format = '''
**RESPONSE FORMAT:**
Respond with a valid JSON object containing:
{
    "tech_stack": [...],
    "overall_reasoning": "...",
    "confidence_assessment": {...}
}'''
            if "RESPONSE FORMAT" not in fixed_prompt:
                fixed_prompt += json_format
        
        # Add reasoning requirements if missing
        if "Reasoning requirements not clearly specified" in validation_result.issues:
            reasoning_req = '''
**REASONING REQUIREMENTS:**
You MUST provide detailed reasoning for each technology selection including:
1. Why this technology was chosen over alternatives
2. How it addresses specific requirements
3. Integration considerations with other selected technologies'''
            if "REASONING REQUIREMENTS" not in fixed_prompt:
                fixed_prompt += reasoning_req
        
        return fixed_prompt
    
    def optimize_prompt_for_model(self, prompt: str, model_type: str) -> str:
        """Optimize prompt for specific LLM model characteristics.
        
        Args:
            prompt: Base prompt
            model_type: Type of LLM model (e.g., 'gpt-4', 'claude', 'bedrock')
            
        Returns:
            Optimized prompt
        """
        if model_type.startswith('gpt'):
            # GPT models respond well to structured instructions and examples
            return self._optimize_for_gpt(prompt)
        elif model_type.startswith('claude'):
            # Claude models prefer conversational tone and clear reasoning
            return self._optimize_for_claude(prompt)
        elif model_type.startswith('bedrock'):
            # Bedrock models vary, use conservative optimization
            return self._optimize_for_bedrock(prompt)
        else:
            return prompt
    
    def _optimize_for_gpt(self, prompt: str) -> str:
        """Optimize prompt for GPT models."""
        # GPT models respond well to numbered lists and clear structure
        optimized = prompt.replace("•", "1.")  # Convert bullets to numbers where appropriate
        
        # Add emphasis for critical instructions
        optimized = optimized.replace("MUST INCLUDE", "**MUST INCLUDE**")
        optimized = optimized.replace("CRITICAL:", "**CRITICAL:**")
        
        return optimized
    
    def _optimize_for_claude(self, prompt: str) -> str:
        """Optimize prompt for Claude models."""
        # Claude prefers conversational tone
        conversational_intro = """I need your expertise as a senior software architect to help select the most appropriate technology stack. Please carefully consider the following requirements and constraints:

"""
        return conversational_intro + prompt
    
    def _optimize_for_bedrock(self, prompt: str) -> str:
        """Optimize prompt for Bedrock models."""
        # Use conservative optimization for Bedrock
        return prompt
    
    def generate_prompt_variations(self, 
                                 tech_context: TechContext,
                                 requirements: Dict[str, Any],
                                 constraints: Optional[Dict[str, Any]] = None,
                                 num_variations: int = 3) -> List[str]:
        """Generate multiple prompt variations for A/B testing.
        
        Args:
            tech_context: Technology context
            requirements: User requirements
            constraints: Additional constraints
            num_variations: Number of variations to generate
            
        Returns:
            List of prompt variations
        """
        variations = []
        
        # Base prompt
        base_prompt = self.generate_context_aware_prompt(tech_context, requirements, constraints)
        variations.append(base_prompt)
        
        if num_variations > 1:
            # Variation with different emphasis
            from copy import deepcopy
            emphasis_context = deepcopy(tech_context)
            # Boost explicit technology confidence
            boosted_explicit = {
                tech: min(conf * 1.2, 1.0) 
                for tech, conf in tech_context.explicit_technologies.items()
            }
            emphasis_context.explicit_technologies = boosted_explicit
            
            emphasis_prompt = self.generate_context_aware_prompt(emphasis_context, requirements, constraints)
            variations.append(emphasis_prompt)
        
        if num_variations > 2:
            # Variation with ecosystem focus
            if tech_context.ecosystem_preference:
                ecosystem_prompt = base_prompt.replace(
                    "You are a senior software architect",
                    f"You are a senior software architect specializing in {tech_context.ecosystem_preference} ecosystem"
                )
                variations.append(ecosystem_prompt)
            else:
                # Variation with domain focus
                domain_prompt = base_prompt.replace(
                    "You are a senior software architect",
                    f"You are a senior software architect specializing in {tech_context.domain_context.primary_domain or 'automation'} solutions"
                )
                variations.append(domain_prompt)
        
        return variations[:num_variations]