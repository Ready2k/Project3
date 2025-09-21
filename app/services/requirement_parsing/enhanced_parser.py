"""Enhanced requirement parser implementation with NER and pattern matching."""

import re
from typing import Dict, List, Any, Optional, Set
from dataclasses import replace

from .base import (
    RequirementParser, ParsedRequirements, ExplicitTech, ContextClues,
    RequirementConstraints, DomainContext, ExtractionMethod, ConfidenceLevel
)
from .tech_extractor import TechnologyExtractor
from app.utils.imports import require_service


class EnhancedRequirementParser(RequirementParser):
    """Enhanced requirement parser with NER and pattern matching capabilities."""
    
    def __init__(self, tech_extractor: Optional[TechnologyExtractor] = None):
        """Initialize enhanced requirement parser.
        
        Args:
            tech_extractor: Technology extractor instance
        """
        self.tech_extractor = tech_extractor or TechnologyExtractor()
        try:
            self.logger = require_service('logger', context='EnhancedRequirementParser')
        except Exception:
            # Fallback to basic logging for testing
            import logging
            self.logger = logging.getLogger('EnhancedRequirementParser')
        
        # Initialize pattern matchers
        self._init_patterns()
    
    def _init_patterns(self) -> None:
        """Initialize regex patterns for context extraction."""
        # Cloud provider patterns
        self.cloud_patterns = {
            'aws': re.compile(r'\b(?:aws|amazon\s+web\s+services|amazon\s+\w+)\b', re.IGNORECASE),
            'azure': re.compile(r'\b(?:azure|microsoft\s+azure|microsoft\s+\w+)\b', re.IGNORECASE),
            'gcp': re.compile(r'\b(?:gcp|google\s+cloud|google\s+\w+)\b', re.IGNORECASE)
        }
        
        # Domain patterns
        self.domain_patterns = {
            'data_processing': re.compile(r'\b(?:data\s+processing|etl|data\s+pipeline|analytics)\b', re.IGNORECASE),
            'web_api': re.compile(r'\b(?:api|rest|web\s+service|endpoint|microservice)\b', re.IGNORECASE),
            'automation': re.compile(r'\b(?:automat|workflow|orchestrat|schedul)\b', re.IGNORECASE),
            'ml_ai': re.compile(r'\b(?:machine\s+learning|ai|artificial\s+intelligence|model|training)\b', re.IGNORECASE),
            'monitoring': re.compile(r'\b(?:monitoring|observ|metric|alert|dashboard)\b', re.IGNORECASE),
            'security': re.compile(r'\b(?:security|auth|encrypt|secure|compliance)\b', re.IGNORECASE)
        }
        
        # Integration patterns
        self.integration_patterns = {
            'database': re.compile(r'\b(?:database|db|sql|nosql|storage|persist)\b', re.IGNORECASE),
            'messaging': re.compile(r'\b(?:queue|message|event|stream|kafka|rabbitmq)\b', re.IGNORECASE),
            'cache': re.compile(r'\b(?:cache|redis|memcache|session)\b', re.IGNORECASE),
            'file_storage': re.compile(r'\b(?:file|storage|s3|blob|object\s+storage)\b', re.IGNORECASE),
            'notification': re.compile(r'\b(?:notification|email|sms|alert|webhook)\b', re.IGNORECASE)
        }
        
        # Programming language patterns
        self.language_patterns = {
            'python': re.compile(r'\b(?:python|py|django|flask|fastapi|pandas|numpy)\b', re.IGNORECASE),
            'javascript': re.compile(r'\b(?:javascript|js|node|react|vue|angular|npm)\b', re.IGNORECASE),
            'java': re.compile(r'\b(?:java|spring|maven|gradle|jvm)\b', re.IGNORECASE),
            'csharp': re.compile(r'\b(?:c#|csharp|\.net|dotnet|asp\.net)\b', re.IGNORECASE),
            'go': re.compile(r'\b(?:golang|go\s+lang)\b', re.IGNORECASE)
        }
        
        # Deployment patterns
        self.deployment_patterns = {
            'containerized': re.compile(r'\b(?:docker|container|kubernetes|k8s|pod)\b', re.IGNORECASE),
            'serverless': re.compile(r'\b(?:serverless|lambda|function|faas)\b', re.IGNORECASE),
            'cloud_native': re.compile(r'\b(?:cloud\s+native|microservice|service\s+mesh)\b', re.IGNORECASE),
            'on_premises': re.compile(r'\b(?:on\s+premises|on-premises|self\s+hosted)\b', re.IGNORECASE)
        }
        
        # Constraint patterns
        self.constraint_patterns = {
            'banned_tools': re.compile(r'\b(?:banned|prohibited|not\s+allowed|cannot\s+use|avoid)\s+([^.]+)', re.IGNORECASE),
            'required_tools': re.compile(r'\b(?:must\s+use|required|mandatory|need\s+to\s+use)\s+([^.]+)', re.IGNORECASE),
            'compliance': re.compile(r'\b(?:compliance|gdpr|hipaa|sox|pci|regulation)\b', re.IGNORECASE),
            'budget': re.compile(r'\b(?:budget|cost|price|expensive|cheap|free|open\s+source)\b', re.IGNORECASE)
        }
    
    def parse_requirements(self, requirements: Dict[str, Any]) -> ParsedRequirements:
        """Parse requirements to extract technology context and constraints.
        
        Args:
            requirements: Raw requirements dictionary
            
        Returns:
            ParsedRequirements object with extracted information
        """
        self.logger.info("Starting enhanced requirement parsing")
        
        # Extract text content from requirements
        text_content = self._extract_text_content(requirements)
        
        # Extract explicit technologies
        explicit_techs = self.extract_explicit_technologies(text_content)
        
        # Identify context clues
        context_clues = self.identify_context_clues(text_content)
        
        # Extract constraints
        constraints = self.extract_constraints(requirements)
        
        # Build domain context
        domain_context = self._build_domain_context(text_content, context_clues)
        
        # Create parsed requirements
        parsed_req = ParsedRequirements(
            explicit_technologies=explicit_techs,
            context_clues=context_clues,
            constraints=constraints,
            domain_context=domain_context,
            raw_text=text_content,
            extraction_metadata={
                'total_explicit_techs': len(explicit_techs),
                'high_confidence_techs': len([t for t in explicit_techs if t.confidence >= 0.8]),
                'context_clue_count': len(context_clues.domains) + len(context_clues.cloud_providers)
            }
        )
        
        # Calculate overall confidence
        parsed_req.confidence_score = self.calculate_confidence(parsed_req)
        
        self.logger.info(f"Parsed requirements with {len(explicit_techs)} explicit technologies, "
                        f"confidence: {parsed_req.confidence_score:.2f}")
        
        return parsed_req
    
    def extract_explicit_technologies(self, text: str) -> List[ExplicitTech]:
        """Extract explicitly mentioned technologies from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of explicitly mentioned technologies with confidence scores
        """
        if not text:
            return []
        
        # Use technology extractor for comprehensive extraction
        extracted_techs = self.tech_extractor.extract_technologies(text)
        
        # Additional pattern-based extraction for common technology mentions
        additional_techs = self._extract_pattern_based_technologies(text)
        
        # Combine and deduplicate
        all_techs = extracted_techs + additional_techs
        deduplicated = self._deduplicate_technologies(all_techs)
        
        self.logger.debug(f"Extracted {len(deduplicated)} explicit technologies")
        return deduplicated
    
    def identify_context_clues(self, text: str) -> ContextClues:
        """Identify context clues from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            ContextClues object with identified patterns
        """
        if not text:
            return ContextClues()
        
        # Extract cloud providers
        cloud_providers = []
        for provider, pattern in self.cloud_patterns.items():
            if pattern.search(text):
                cloud_providers.append(provider)
        
        # Extract domains
        domains = []
        for domain, pattern in self.domain_patterns.items():
            if pattern.search(text):
                domains.append(domain)
        
        # Extract integration patterns
        integration_patterns = []
        for integration, pattern in self.integration_patterns.items():
            if pattern.search(text):
                integration_patterns.append(integration)
        
        # Extract programming languages
        programming_languages = []
        for lang, pattern in self.language_patterns.items():
            if pattern.search(text):
                programming_languages.append(lang)
        
        # Extract deployment preferences
        deployment_preferences = []
        for deployment, pattern in self.deployment_patterns.items():
            if pattern.search(text):
                deployment_preferences.append(deployment)
        
        # Extract data patterns
        data_patterns = self._extract_data_patterns(text)
        
        # Extract technology categories
        technology_categories = self._extract_technology_categories(text)
        
        context_clues = ContextClues(
            cloud_providers=cloud_providers,
            domains=domains,
            integration_patterns=integration_patterns,
            programming_languages=programming_languages,
            deployment_preferences=deployment_preferences,
            data_patterns=data_patterns,
            technology_categories=technology_categories
        )
        
        self.logger.debug(f"Identified context clues: {len(cloud_providers)} cloud providers, "
                         f"{len(domains)} domains, {len(integration_patterns)} integration patterns")
        
        return context_clues
    
    def extract_constraints(self, requirements: Dict[str, Any]) -> RequirementConstraints:
        """Extract constraints from requirements.
        
        Args:
            requirements: Requirements dictionary
            
        Returns:
            RequirementConstraints object
        """
        constraints = RequirementConstraints()
        
        # Extract from explicit constraints field
        if 'constraints' in requirements:
            constraint_data = requirements['constraints']
            if isinstance(constraint_data, dict):
                constraints.banned_tools.update(constraint_data.get('banned_tools', []))
                constraints.required_integrations.extend(constraint_data.get('required_integrations', []))
                constraints.compliance_requirements.extend(constraint_data.get('compliance_requirements', []))
                constraints.data_sensitivity = constraint_data.get('data_sensitivity')
                constraints.budget_constraints = constraint_data.get('budget_constraints')
                constraints.deployment_preference = constraint_data.get('deployment_preference')
                constraints.performance_requirements.update(constraint_data.get('performance_requirements', {}))
        
        # Extract from text content using patterns
        text_content = self._extract_text_content(requirements)
        if text_content:
            self._extract_text_constraints(text_content, constraints)
        
        self.logger.debug(f"Extracted constraints: {len(constraints.banned_tools)} banned tools, "
                         f"{len(constraints.required_integrations)} required integrations")
        
        return constraints
    
    def calculate_confidence(self, parsed_req: ParsedRequirements) -> float:
        """Calculate overall confidence score for parsed requirements.
        
        Args:
            parsed_req: Parsed requirements
            
        Returns:
            Overall confidence score (0.0 to 1.0)
        """
        if not parsed_req.explicit_technologies and not parsed_req.context_clues.domains:
            return 0.0
        
        # Calculate technology confidence
        tech_confidence = 0.0
        if parsed_req.explicit_technologies:
            tech_confidence = sum(tech.confidence for tech in parsed_req.explicit_technologies) / len(parsed_req.explicit_technologies)
        
        # Calculate context confidence
        context_confidence = 0.0
        context_indicators = (
            len(parsed_req.context_clues.cloud_providers) * 0.3 +
            len(parsed_req.context_clues.domains) * 0.2 +
            len(parsed_req.context_clues.integration_patterns) * 0.1 +
            len(parsed_req.context_clues.programming_languages) * 0.1
        )
        context_confidence = min(context_indicators, 1.0)
        
        # Calculate constraint confidence
        constraint_confidence = 0.0
        if parsed_req.constraints.banned_tools or parsed_req.constraints.required_integrations:
            constraint_confidence = 0.2
        
        # Weighted average - give more weight to explicit technologies
        if parsed_req.explicit_technologies:
            # High weight to explicit technologies when they exist
            overall_confidence = (
                tech_confidence * 0.8 +
                context_confidence * 0.15 +
                constraint_confidence * 0.05
            )
        else:
            # Fall back to context-based confidence when no explicit technologies
            overall_confidence = (
                context_confidence * 0.8 +
                constraint_confidence * 0.2
            )
        
        return min(overall_confidence, 1.0)
    
    def _extract_text_content(self, requirements: Dict[str, Any]) -> str:
        """Extract all text content from requirements dictionary.
        
        Args:
            requirements: Requirements dictionary
            
        Returns:
            Combined text content
        """
        text_parts = []
        
        # Common text fields
        text_fields = ['description', 'details', 'requirements', 'notes', 'summary']
        
        for field in text_fields:
            if field in requirements and isinstance(requirements[field], str):
                text_parts.append(requirements[field])
        
        # Handle nested structures
        for key, value in requirements.items():
            if isinstance(value, str) and key not in text_fields:
                text_parts.append(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        text_parts.append(item)
        
        return ' '.join(text_parts)
    
    def _extract_pattern_based_technologies(self, text: str) -> List[ExplicitTech]:
        """Extract technologies using pattern matching.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of extracted technologies
        """
        technologies = []
        
        # Common technology patterns
        tech_patterns = {
            'fastapi': re.compile(r'\bfastapi\b', re.IGNORECASE),
            'django': re.compile(r'\bdjango\b', re.IGNORECASE),
            'flask': re.compile(r'\bflask\b', re.IGNORECASE),
            'react': re.compile(r'\breact\b', re.IGNORECASE),
            'vue': re.compile(r'\bvue(?:\.js)?\b', re.IGNORECASE),
            'angular': re.compile(r'\bangular\b', re.IGNORECASE),
            'docker': re.compile(r'\bdocker\b', re.IGNORECASE),
            'kubernetes': re.compile(r'\b(?:kubernetes|k8s)\b', re.IGNORECASE),
            'redis': re.compile(r'\bredis\b', re.IGNORECASE),
            'postgresql': re.compile(r'\b(?:postgresql|postgres)\b', re.IGNORECASE),
            'mysql': re.compile(r'\bmysql\b', re.IGNORECASE),
            'mongodb': re.compile(r'\bmongodb\b', re.IGNORECASE)
        }
        
        for tech_name, pattern in tech_patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                # Resolve to canonical name
                canonical_name = tech_name.title()  # Proper case
                tech = ExplicitTech(
                    name=canonical_name,
                    canonical_name=canonical_name,
                    confidence=0.9,  # High confidence for exact matches
                    extraction_method=ExtractionMethod.PATTERN_MATCHING,
                    source_text=match.group(),
                    position=match.start(),
                    context=text[max(0, match.start()-50):match.end()+50]
                )
                technologies.append(tech)
        
        return technologies
    
    def _deduplicate_technologies(self, technologies: List[ExplicitTech]) -> List[ExplicitTech]:
        """Remove duplicate technologies, keeping the highest confidence version.
        
        Args:
            technologies: List of technologies to deduplicate
            
        Returns:
            Deduplicated list of technologies
        """
        tech_map = {}
        
        for tech in technologies:
            # Use canonical name for deduplication, fallback to normalized name
            canonical = tech.canonical_name or tech.name
            key = canonical.lower().strip()
            
            if key not in tech_map or tech.confidence > tech_map[key].confidence:
                tech_map[key] = tech
        
        return list(tech_map.values())
    
    def _build_domain_context(self, text: str, context_clues: ContextClues) -> DomainContext:
        """Build domain context from text and context clues.
        
        Args:
            text: Text content
            context_clues: Extracted context clues
            
        Returns:
            DomainContext object
        """
        # Determine primary domain
        primary_domain = None
        if context_clues.domains:
            # Use the first domain as primary (could be enhanced with scoring)
            primary_domain = context_clues.domains[0]
        
        # Extract use case patterns
        use_case_patterns = []
        use_case_keywords = ['automation', 'integration', 'processing', 'analysis', 'monitoring']
        for keyword in use_case_keywords:
            if keyword in text.lower():
                use_case_patterns.append(keyword)
        
        # Extract complexity indicators
        complexity_indicators = []
        complexity_keywords = ['scalable', 'high-performance', 'distributed', 'real-time', 'enterprise']
        for keyword in complexity_keywords:
            if keyword in text.lower():
                complexity_indicators.append(keyword)
        
        return DomainContext(
            primary_domain=primary_domain,
            sub_domains=context_clues.domains[1:] if len(context_clues.domains) > 1 else [],
            use_case_patterns=use_case_patterns,
            complexity_indicators=complexity_indicators
        )
    
    def _extract_data_patterns(self, text: str) -> List[str]:
        """Extract data-related patterns from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of data patterns
        """
        data_patterns = []
        
        patterns = {
            'structured_data': re.compile(r'\b(?:structured\s+data|relational|sql|table)\b', re.IGNORECASE),
            'unstructured_data': re.compile(r'\b(?:unstructured|document|json|xml)\b', re.IGNORECASE),
            'time_series': re.compile(r'\b(?:time\s+series|temporal|metrics|logs)\b', re.IGNORECASE),
            'big_data': re.compile(r'\b(?:big\s+data|large\s+scale|petabyte|terabyte)\b', re.IGNORECASE),
            'real_time': re.compile(r'\b(?:real\s+time|streaming|live|instant)\b', re.IGNORECASE)
        }
        
        for pattern_name, pattern in patterns.items():
            if pattern.search(text):
                data_patterns.append(pattern_name)
        
        return data_patterns
    
    def _extract_technology_categories(self, text: str) -> List[str]:
        """Extract technology categories from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of technology categories
        """
        categories = []
        
        category_patterns = {
            'web_framework': re.compile(r'\b(?:web\s+framework|api\s+framework|rest\s+framework)\b', re.IGNORECASE),
            'database': re.compile(r'\b(?:database|db|storage|persistence)\b', re.IGNORECASE),
            'message_queue': re.compile(r'\b(?:message\s+queue|messaging|queue|broker)\b', re.IGNORECASE),
            'cache': re.compile(r'\b(?:cache|caching|memory\s+store)\b', re.IGNORECASE),
            'monitoring': re.compile(r'\b(?:monitoring|observability|metrics|logging)\b', re.IGNORECASE),
            'container': re.compile(r'\b(?:container|containerization|orchestration)\b', re.IGNORECASE)
        }
        
        for category_name, pattern in category_patterns.items():
            if pattern.search(text):
                categories.append(category_name)
        
        return categories
    
    def _extract_text_constraints(self, text: str, constraints: RequirementConstraints) -> None:
        """Extract constraints from text using pattern matching.
        
        Args:
            text: Text to analyze
            constraints: Constraints object to update
        """
        # Extract banned tools
        banned_matches = self.constraint_patterns['banned_tools'].finditer(text)
        for match in banned_matches:
            tools_text = match.group(1).strip()
            # Simple extraction - could be enhanced with NER
            tools = [tool.strip() for tool in tools_text.split(',')]
            constraints.banned_tools.update(tools)
        
        # Extract required tools
        required_matches = self.constraint_patterns['required_tools'].finditer(text)
        for match in required_matches:
            tools_text = match.group(1).strip()
            tools = [tool.strip() for tool in tools_text.split(',')]
            constraints.required_integrations.extend(tools)
        
        # Extract compliance requirements
        if self.constraint_patterns['compliance'].search(text):
            compliance_keywords = ['gdpr', 'hipaa', 'sox', 'pci']
            for keyword in compliance_keywords:
                if keyword in text.lower():
                    constraints.compliance_requirements.append(keyword.upper())
        
        # Extract budget constraints
        if self.constraint_patterns['budget'].search(text):
            if 'open source' in text.lower() or 'free' in text.lower():
                constraints.budget_constraints = 'low'
            elif 'expensive' in text.lower() or 'cost' in text.lower():
                constraints.budget_constraints = 'medium'