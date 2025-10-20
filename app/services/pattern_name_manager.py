"""Pattern name management service to prevent duplicate names and ensure uniqueness."""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from app.utils.imports import require_service


class PatternNameManager:
    """Service to manage pattern names and prevent duplicates."""
    
    def __init__(self, pattern_library_path: Path):
        """Initialize the pattern name manager.
        
        Args:
            pattern_library_path: Path to pattern library directory
        """
        self.pattern_library_path = pattern_library_path
        self.logger = require_service("logger", context="PatternNameManager")
        self._existing_names_cache: Optional[Set[str]] = None
    
    def get_existing_pattern_names(self) -> Set[str]:
        """Get all existing pattern names from the library.
        
        Returns:
            Set of existing pattern names
        """
        if self._existing_names_cache is not None:
            return self._existing_names_cache
            
        existing_names = set()
        
        try:
            # Read from pattern files
            for pattern_file in self.pattern_library_path.glob("*.json"):
                try:
                    with open(pattern_file, 'r', encoding='utf-8') as f:
                        pattern = json.load(f)
                        name = pattern.get('name', '').strip()
                        if name:
                            existing_names.add(name.lower())  # Store lowercase for comparison
                except Exception as e:
                    self.logger.warning(f"Error reading pattern file {pattern_file}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error scanning pattern library: {e}")
            
        self._existing_names_cache = existing_names
        self.logger.info(f"Loaded {len(existing_names)} existing pattern names")
        return existing_names
    
    def is_name_unique(self, proposed_name: str) -> bool:
        """Check if a proposed pattern name is unique.
        
        Args:
            proposed_name: The proposed pattern name
            
        Returns:
            True if the name is unique, False otherwise
        """
        if not proposed_name or not proposed_name.strip():
            return False
            
        existing_names = self.get_existing_pattern_names()
        return proposed_name.lower().strip() not in existing_names
    
    def generate_unique_name(self, base_name: str, requirements: Dict[str, Any], 
                           pattern_analysis: Dict[str, Any]) -> str:
        """Generate a unique pattern name based on requirements and analysis.
        
        Args:
            base_name: Base name to start with
            requirements: User requirements
            pattern_analysis: Pattern analysis results
            
        Returns:
            Unique pattern name
        """
        if self.is_name_unique(base_name):
            return base_name
            
        # Try to make it more specific based on content
        enhanced_name = self._enhance_name_with_context(base_name, requirements, pattern_analysis)
        if self.is_name_unique(enhanced_name):
            return enhanced_name
            
        # Add version numbers if still not unique
        for version in range(2, 100):  # Try v2 through v99
            versioned_name = f"{enhanced_name} (v{version})"
            if self.is_name_unique(versioned_name):
                return versioned_name
                
        # Fallback: add unique identifier
        import uuid
        unique_suffix = str(uuid.uuid4())[:8].upper()
        return f"{enhanced_name} ({unique_suffix})"
    
    def _enhance_name_with_context(self, base_name: str, requirements: Dict[str, Any], 
                                 pattern_analysis: Dict[str, Any]) -> str:
        """Enhance a base name with contextual information to make it more unique.
        
        Args:
            base_name: Base pattern name
            requirements: User requirements
            pattern_analysis: Pattern analysis results
            
        Returns:
            Enhanced pattern name
        """
        description = requirements.get('description', '').lower()
        domain = requirements.get('domain', '')
        
        # Extract key characteristics
        agent_count = self._extract_agent_count(description, pattern_analysis)
        use_case = self._extract_use_case(description, requirements)
        architecture = self._extract_architecture_type(pattern_analysis)
        
        # Build enhanced name
        enhanced_parts = []
        
        # Add agent count for multi-agent systems
        if agent_count and 'multi-agent' in base_name.lower():
            enhanced_parts.append(f"{agent_count}-Agent")
        elif architecture and architecture != 'general':
            enhanced_parts.append(architecture)
            
        # Add use case specificity
        if use_case and use_case != 'general':
            enhanced_parts.append(use_case)
        elif domain and domain not in ['general', 'None', 'none', '']:
            enhanced_parts.append(domain.replace('_', ' ').title())
            
        # Add system type
        if 'system' not in base_name.lower():
            enhanced_parts.append('System')
            
        if enhanced_parts:
            return ' '.join(enhanced_parts)
        else:
            return base_name
    
    def _extract_agent_count(self, description: str, pattern_analysis: Dict[str, Any]) -> Optional[str]:
        """Extract agent count from description or analysis."""
        # Look for explicit agent count mentions
        agent_match = re.search(r'(\d+)\s+(?:specialized\s+)?agents?', description)
        if agent_match:
            return agent_match.group(1)
            
        # Check pattern analysis for agent-related info
        pattern_types = pattern_analysis.get('pattern_types', [])
        if 'multi_agent_system' in pattern_types:
            # Default to common counts if not specified
            if 'complex' in description:
                return '5'
            else:
                return '4'
                
        return None
    
    def _extract_use_case(self, description: str, requirements: Dict[str, Any]) -> str:
        """Extract the main use case from description."""
        use_case_patterns = {
            'Investment Portfolio': ['investment', 'portfolio', 'rebalancing', 'trading', 'financial'],
            'Customer Support': ['customer support', 'customer service', 'crm', 'inquiries', 'helpdesk'],
            'Data Processing': ['data processing', 'analytics', 'etl', 'data pipeline', 'transform'],
            'Document Processing': ['document', 'pdf', 'file processing', 'extract', 'parse'],
            'Workflow Automation': ['workflow', 'process automation', 'business process'],
            'Monitoring': ['monitoring', 'alerting', 'observability', 'metrics', 'watch'],
            'API Integration': ['api', 'integration', 'connect', 'sync', 'webhook'],
            'Content Management': ['content', 'cms', 'publishing', 'media'],
            'Communication': ['email', 'messaging', 'notification', 'chat', 'sms'],
            'E-commerce': ['order', 'payment', 'shopping', 'product', 'inventory'],
            'HR Management': ['employee', 'hr', 'payroll', 'recruitment', 'onboarding'],
            'Project Management': ['project', 'task', 'milestone', 'planning', 'tracking']
        }
        
        for use_case, keywords in use_case_patterns.items():
            if any(keyword in description for keyword in keywords):
                return use_case
                
        return 'general'
    
    def _extract_architecture_type(self, pattern_analysis: Dict[str, Any]) -> str:
        """Extract architecture type from pattern analysis."""
        pattern_types = pattern_analysis.get('pattern_types', [])
        
        if 'multi_agent_system' in pattern_types or 'hierarchical_agents' in pattern_types:
            return 'Multi-Agent'
        elif 'agentic_reasoning' in pattern_types:
            return 'Agentic Reasoning'
        elif 'workflow_automation' in pattern_types:
            return 'Workflow Automation'
        elif 'api_integration' in pattern_types:
            return 'API Integration'
        elif 'ml_processing' in pattern_types:
            return 'ML Processing'
        else:
            return 'Autonomous'
    
    def invalidate_cache(self):
        """Invalidate the existing names cache to force reload."""
        self._existing_names_cache = None
        self.logger.debug("Pattern names cache invalidated")
    
    def validate_and_suggest_name(self, proposed_name: str, requirements: Dict[str, Any], 
                                pattern_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a proposed name and suggest alternatives if needed.
        
        Args:
            proposed_name: The proposed pattern name
            requirements: User requirements
            pattern_analysis: Pattern analysis results
            
        Returns:
            Dictionary with validation results and suggestions
        """
        result = {
            'is_valid': True,
            'is_unique': True,
            'suggested_name': proposed_name,
            'issues': [],
            'suggestions': []
        }
        
        # Check if name is empty or too generic
        if not proposed_name or not proposed_name.strip():
            result['is_valid'] = False
            result['issues'].append('Pattern name cannot be empty')
            
        if proposed_name.strip().lower() in ['pattern', 'automation', 'system']:
            result['is_valid'] = False
            result['issues'].append('Pattern name is too generic')
            
        # Check uniqueness
        if not self.is_name_unique(proposed_name):
            result['is_unique'] = False
            result['issues'].append(f'Pattern name "{proposed_name}" already exists')
            
        # Generate suggestions if there are issues
        if not result['is_valid'] or not result['is_unique']:
            result['suggested_name'] = self.generate_unique_name(
                proposed_name if proposed_name else 'Automation Pattern',
                requirements,
                pattern_analysis
            )
            result['suggestions'].append(f'Suggested alternative: "{result["suggested_name"]}"')
            
        return result