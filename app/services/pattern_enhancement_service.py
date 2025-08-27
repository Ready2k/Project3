"""Service for enhancing existing patterns with detailed technical information and agentic capabilities."""

import json
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from app.utils.logger import app_logger
from app.pattern.enhanced_loader import EnhancedPatternLoader
from app.llm.base import LLMProvider


class PatternEnhancementService:
    """Service for enhancing patterns with rich technical details and agentic capabilities."""
    
    def __init__(self, pattern_loader: EnhancedPatternLoader, llm_provider: LLMProvider):
        self.pattern_loader = pattern_loader
        self.llm_provider = llm_provider
        self.enhancement_template = self._load_enhancement_template()
    
    def _load_enhancement_template(self) -> Dict[str, Any]:
        """Load the enhanced pattern template."""
        template_path = Path(__file__).parent.parent / "pattern" / "enhanced_pattern_template.json"
        try:
            with open(template_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            app_logger.error(f"Failed to load enhancement template: {e}")
            return {}
    
    async def enhance_pattern(self, pattern_id: str, enhancement_type: str = "full") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Enhance an existing pattern with detailed technical information and agentic capabilities.
        
        Args:
            pattern_id: ID of the pattern to enhance
            enhancement_type: Type of enhancement ("technical", "agentic", "full")
            
        Returns:
            Tuple of (success, message, enhanced_pattern)
        """
        try:
            # Load existing pattern
            existing_pattern = self.pattern_loader.get_pattern_by_id(pattern_id)
            if not existing_pattern:
                return False, f"Pattern {pattern_id} not found", None
            
            app_logger.info(f"Enhancing pattern {pattern_id} with {enhancement_type} enhancement")
            
            # Determine enhancement strategy
            if enhancement_type == "technical":
                enhanced_pattern = await self._enhance_technical_details(existing_pattern)
            elif enhancement_type == "agentic":
                enhanced_pattern = await self._enhance_agentic_capabilities(existing_pattern)
            elif enhancement_type == "full":
                enhanced_pattern = await self._enhance_full_pattern(existing_pattern)
            else:
                return False, f"Unknown enhancement type: {enhancement_type}", None
            
            # Keep the same pattern ID but mark as enhanced
            enhanced_pattern["pattern_id"] = pattern_id  # Keep original ID
            enhanced_pattern["enhanced_from_pattern"] = pattern_id
            enhanced_pattern["enhancement_type"] = enhancement_type
            enhanced_pattern["enhanced_by_llm"] = True
            
            # Validate enhanced pattern
            success, message = self.pattern_loader.save_enhanced_pattern(enhanced_pattern)
            
            if success:
                return True, f"Pattern enhanced successfully as {enhanced_pattern['pattern_id']}", enhanced_pattern
            else:
                return False, f"Failed to save enhanced pattern: {message}", None
                
        except Exception as e:
            app_logger.error(f"Error enhancing pattern {pattern_id}: {e}")
            return False, f"Enhancement failed: {e}", None
    
    def _generate_enhanced_pattern_id(self, original_id: str) -> str:
        """Generate a new pattern ID for the enhanced version."""
        if original_id.startswith("PAT-"):
            # Keep the same PAT-XXX ID but enhance in place
            return original_id
        elif original_id.startswith("APAT-"):
            # APAT patterns are already enhanced, keep same ID
            return original_id
        else:
            # Default to original ID
            return original_id
    
    async def _enhance_technical_details(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance pattern with detailed technical implementation information."""
        enhanced_pattern = pattern.copy()
        
        # Create enhancement prompt
        prompt = f"""
        Enhance the following pattern with detailed technical implementation information:
        
        Pattern: {pattern.get('name', 'Unknown')}
        Description: {pattern.get('description', 'No description')}
        Current Tech Stack: {json.dumps(pattern.get('tech_stack', []), indent=2)}
        
        Please provide:
        1. Structured tech stack with categories (agentic_frameworks, core_technologies, data_processing, infrastructure, etc.)
        2. Detailed implementation guidance including architecture decisions, technical challenges, deployment considerations
        3. Comprehensive effort breakdown with phases, deliverables, and dependencies
        4. Performance requirements and security considerations
        5. Testing strategy and validation approaches
        
        Format the response as a JSON object with the enhanced fields. Focus on practical, implementable technical details.
        """
        
        try:
            response = await self.llm_provider.generate_response(prompt)
            enhancement_data = json.loads(response)
            
            # Merge enhancement data with existing pattern
            enhanced_pattern.update(enhancement_data)
            
            # Handle tech stack based on pattern type
            pattern_id = pattern.get("pattern_id", "")
            if "tech_stack" in enhancement_data:
                if pattern_id.startswith("PAT-"):
                    # For PAT-* patterns, flatten tech_stack to maintain traditional schema compatibility
                    tech_stack_data = enhancement_data["tech_stack"]
                    if isinstance(tech_stack_data, dict):
                        # Flatten structured tech stack
                        flattened_stack = []
                        for category, technologies in tech_stack_data.items():
                            if isinstance(technologies, list):
                                flattened_stack.extend(technologies)
                        enhanced_pattern["tech_stack"] = flattened_stack
                    else:
                        enhanced_pattern["tech_stack"] = tech_stack_data
                else:
                    # For APAT-* or EPAT-* patterns, keep structured format
                    enhanced_pattern["tech_stack"] = enhancement_data["tech_stack"]
            
            # Add implementation guidance
            if "implementation_guidance" in enhancement_data:
                enhanced_pattern["implementation_guidance"] = enhancement_data["implementation_guidance"]
            
            # Add detailed effort breakdown
            if "effort_breakdown" in enhancement_data:
                enhanced_pattern["effort_breakdown"] = enhancement_data["effort_breakdown"]
            
            app_logger.info(f"Technical enhancement completed for pattern {pattern.get('pattern_id')}")
            return enhanced_pattern
            
        except Exception as e:
            app_logger.error(f"Failed to enhance technical details: {e}")
            # Return original pattern with basic enhancements
            return self._apply_basic_technical_enhancement(pattern)
    
    async def _enhance_agentic_capabilities(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance pattern with autonomous agent capabilities."""
        enhanced_pattern = pattern.copy()
        
        # Create agentic enhancement prompt
        prompt = f"""
        Enhance the following pattern with autonomous agent capabilities:
        
        Pattern: {pattern.get('name', 'Unknown')}
        Description: {pattern.get('description', 'No description')}
        Domain: {pattern.get('domain', 'Unknown')}
        Complexity: {pattern.get('complexity', 'Medium')}
        
        Please provide:
        1. Autonomy level (0.0-1.0) based on the pattern's automation potential
        2. Reasoning types needed (logical, causal, temporal, spatial, analogical, case_based, probabilistic, strategic)
        3. Decision boundaries: autonomous decisions, escalation triggers, decision authority level
        4. Exception handling strategy: autonomous resolution approaches, reasoning fallbacks, escalation criteria
        5. Learning mechanisms and self-monitoring capabilities
        6. Agent architecture recommendation (single_agent, multi_agent_collaborative, hierarchical_agents, swarm_intelligence)
        7. Coordination requirements if multi-agent
        8. Workflow automation details
        
        Format the response as a JSON object with the agentic enhancement fields.
        """
        
        try:
            response = await self.llm_provider.generate_response(prompt)
            enhancement_data = json.loads(response)
            
            # Merge agentic capabilities
            agentic_fields = [
                "autonomy_level", "reasoning_types", "decision_boundaries", 
                "exception_handling_strategy", "learning_mechanisms", 
                "self_monitoring_capabilities", "agent_architecture", 
                "coordination_requirements", "workflow_automation"
            ]
            
            for field in agentic_fields:
                if field in enhancement_data:
                    enhanced_pattern[field] = enhancement_data[field]
            
            # Update feasibility if autonomy level is high
            if enhanced_pattern.get("autonomy_level", 0) >= 0.9:
                enhanced_pattern["feasibility"] = "Fully Automatable"
            elif enhanced_pattern.get("autonomy_level", 0) >= 0.7:
                enhanced_pattern["feasibility"] = "Partially Automatable"
            
            app_logger.info(f"Agentic enhancement completed for pattern {pattern.get('pattern_id')}")
            return enhanced_pattern
            
        except Exception as e:
            app_logger.error(f"Failed to enhance agentic capabilities: {e}")
            # Return original pattern with basic agentic enhancements
            return self._apply_basic_agentic_enhancement(pattern)
    
    async def _enhance_full_pattern(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Perform full enhancement with both technical details and agentic capabilities."""
        # First enhance technical details
        technically_enhanced = await self._enhance_technical_details(pattern)
        
        # Then enhance with agentic capabilities
        fully_enhanced = await self._enhance_agentic_capabilities(technically_enhanced)
        
        # Add full enhancement metadata
        fully_enhanced["enhancement_type"] = "full"
        fully_enhanced["name"] = f"Enhanced {pattern.get('name', 'Pattern')}"
        
        # Update description to reflect autonomous capabilities
        original_description = pattern.get('description', '')
        fully_enhanced["description"] = f"Fully autonomous AI agent that {original_description.lower()}"
        
        return fully_enhanced
    
    def _apply_basic_technical_enhancement(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Apply basic technical enhancements when LLM enhancement fails."""
        enhanced_pattern = pattern.copy()
        
        # For PAT-* patterns, keep tech_stack as flat array to maintain traditional schema compatibility
        # Only use structured format for APAT-* or EPAT-* patterns
        pattern_id = pattern.get("pattern_id", "")
        tech_stack = pattern.get("tech_stack", [])
        
        if pattern_id.startswith("PAT-"):
            # Keep as flat array for traditional schema compatibility
            if isinstance(tech_stack, list):
                # Add some additional technologies to enhance the stack
                enhanced_tech_stack = tech_stack.copy()
                if "FastAPI" not in enhanced_tech_stack:
                    enhanced_tech_stack.append("FastAPI")
                if "Docker" not in enhanced_tech_stack:
                    enhanced_tech_stack.append("Docker")
                enhanced_pattern["tech_stack"] = enhanced_tech_stack
            else:
                # If it's already structured, flatten it for traditional schema
                flattened_stack = []
                if isinstance(tech_stack, dict):
                    for category, technologies in tech_stack.items():
                        if isinstance(technologies, list):
                            flattened_stack.extend(technologies)
                enhanced_pattern["tech_stack"] = flattened_stack
        else:
            # For APAT-* or EPAT-* patterns, use structured format
            if isinstance(tech_stack, list):
                enhanced_pattern["tech_stack"] = {
                    "core_technologies": tech_stack[:3] if len(tech_stack) > 3 else tech_stack,
                    "data_processing": [t for t in tech_stack if any(keyword in t.lower() for keyword in ["ml", "ai", "data", "analytics"])],
                    "infrastructure": [t for t in tech_stack if any(keyword in t.lower() for keyword in ["aws", "azure", "gcp", "docker", "kubernetes"])],
                    "integration_apis": [t for t in tech_stack if "api" in t.lower()]
                }
        
        # Add basic implementation guidance
        enhanced_pattern["implementation_guidance"] = {
            "architecture_decisions": [
                "Use microservices architecture for scalability",
                "Implement event-driven patterns for loose coupling",
                "Apply cloud-native design principles"
            ],
            "technical_challenges": [
                "Ensuring system scalability and performance",
                "Managing data consistency across services",
                "Implementing robust error handling and recovery"
            ]
        }
        
        return enhanced_pattern
    
    def _apply_basic_agentic_enhancement(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Apply basic agentic enhancements when LLM enhancement fails."""
        enhanced_pattern = pattern.copy()
        
        # Determine autonomy level based on feasibility
        feasibility = pattern.get("feasibility", "Partially Automatable")
        if feasibility == "Automatable" or feasibility == "Fully Automatable":
            enhanced_pattern["autonomy_level"] = 0.85
        else:
            enhanced_pattern["autonomy_level"] = 0.65
        
        # Add basic reasoning types
        enhanced_pattern["reasoning_types"] = ["logical", "causal", "probabilistic"]
        
        # Add basic decision boundaries
        enhanced_pattern["decision_boundaries"] = {
            "autonomous_decisions": [
                "Process routine tasks within defined parameters",
                "Apply business rules and validation logic",
                "Generate reports and notifications"
            ],
            "escalation_triggers": [
                "Exceptions outside normal parameters",
                "High-value or high-risk decisions",
                "User requests for human review"
            ],
            "decision_authority_level": "medium"
        }
        
        # Add basic agent architecture
        enhanced_pattern["agent_architecture"] = "single_agent"
        
        return enhanced_pattern
    
    async def batch_enhance_patterns(self, pattern_ids: List[str], enhancement_type: str = "full") -> Dict[str, Any]:
        """Enhance multiple patterns in batch."""
        results = {
            "successful": [],
            "failed": [],
            "total": len(pattern_ids)
        }
        
        for pattern_id in pattern_ids:
            success, message, enhanced_pattern = await self.enhance_pattern(pattern_id, enhancement_type)
            
            if success:
                results["successful"].append({
                    "original_id": pattern_id,
                    "enhanced_id": enhanced_pattern["pattern_id"] if enhanced_pattern else None,
                    "message": message
                })
            else:
                results["failed"].append({
                    "pattern_id": pattern_id,
                    "error": message
                })
        
        app_logger.info(f"Batch enhancement completed: {len(results['successful'])} successful, {len(results['failed'])} failed")
        return results
    
    def get_enhancement_candidates(self) -> List[Dict[str, Any]]:
        """Get patterns that are good candidates for enhancement."""
        patterns = self.pattern_loader.load_patterns()
        candidates = []
        
        for pattern in patterns:
            # Skip already enhanced patterns
            if pattern.get("pattern_id", "").startswith("EPAT-"):
                continue
            
            # Check if pattern would benefit from enhancement
            capabilities = pattern.get("_capabilities", {})
            
            # Candidates: traditional patterns without agentic features or detailed tech stack
            if (not capabilities.get("has_agentic_features", False) or 
                not capabilities.get("has_detailed_tech_stack", False) or
                not capabilities.get("has_implementation_guidance", False)):
                
                candidates.append({
                    "pattern_id": pattern.get("pattern_id"),
                    "name": pattern.get("name"),
                    "complexity": pattern.get("complexity"),
                    "missing_capabilities": [k for k, v in capabilities.items() if not v],
                    "enhancement_potential": self._calculate_enhancement_potential(pattern)
                })
        
        # Sort by enhancement potential
        candidates.sort(key=lambda x: x["enhancement_potential"], reverse=True)
        return candidates
    
    def _calculate_enhancement_potential(self, pattern: Dict[str, Any]) -> float:
        """Calculate the potential benefit of enhancing a pattern."""
        score = 0.0
        
        # Higher complexity patterns benefit more from detailed guidance
        complexity_map = {"Low": 0.2, "Medium": 0.5, "High": 0.8, "Very High": 1.0}
        score += complexity_map.get(pattern.get("complexity", "Medium"), 0.5)
        
        # Patterns with automation potential benefit from agentic enhancement
        feasibility = pattern.get("feasibility", "")
        if "Automatable" in feasibility:
            score += 0.3
        
        # Patterns with simple tech stacks benefit from detailed technical guidance
        tech_stack = pattern.get("tech_stack", [])
        if isinstance(tech_stack, list) and len(tech_stack) < 5:
            score += 0.2
        
        # Patterns without implementation guidance benefit significantly
        if not pattern.get("implementation_guidance"):
            score += 0.3
        
        return min(score, 1.0)