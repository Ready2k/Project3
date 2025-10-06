"""Pattern enhancement service for converting traditional automation to agentic solutions."""

import json
from typing import Dict, List, Any
from pathlib import Path

from app.llm.base import LLMProvider


class PatternAgenticEnhancer:
    """Service for enhancing patterns with agentic capabilities."""
    
    def __init__(self, llm_provider: LLMProvider, pattern_library_path: Path):
        self.llm_provider = llm_provider
        self.pattern_library_path = pattern_library_path
        self.agentic_frameworks = [
            "LangChain", "AutoGPT", "CrewAI", "Microsoft Semantic Kernel",
            "OpenAI Assistants API", "Anthropic Claude Computer Use"
        ]
        self.reasoning_engines = [
            "Neo4j", "Prolog", "CLIPS", "Drools", "Apache Jena", "Stardog"
        ]
    
    async def enhance_for_autonomy(self, 
                                 pattern: Dict[str, Any], 
                                 requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance a pattern to maximize autonomous capabilities."""
        
        self.logger.info(f"Enhancing pattern {pattern.get('pattern_id')} for autonomy")
        
        # Analyze current autonomy level
        current_autonomy = self._assess_current_autonomy(pattern)
        
        # Generate agentic enhancements
        enhancements = await self._generate_agentic_enhancements(pattern, requirements)
        
        # Apply enhancements to create agentic pattern
        enhanced_pattern = self._apply_enhancements(pattern, enhancements)
        
        # Validate enhanced pattern meets autonomy standards
        enhanced_pattern = self._ensure_autonomy_standards(enhanced_pattern)
        
        self.logger.info(f"Enhanced pattern autonomy from {current_autonomy:.2f} to {enhanced_pattern.get('autonomy_level', 0):.2f}")
        
        return enhanced_pattern
    
    def _assess_current_autonomy(self, pattern: Dict[str, Any]) -> float:
        """Assess the current autonomy level of a pattern."""
        
        # Check for human-in-the-loop indicators
        human_indicators = [
            "human_in_loop", "manual_review", "human_approval", 
            "escalation", "human_oversight"
        ]
        
        pattern_types = pattern.get("pattern_type", [])
        description = pattern.get("description", "").lower()
        
        # Penalty for human dependency
        human_penalty = 0
        for indicator in human_indicators:
            if indicator in pattern_types or indicator in description:
                human_penalty += 0.2
        
        # Base autonomy from feasibility
        feasibility = pattern.get("feasibility", "Not Automatable")
        if feasibility == "Automatable" or feasibility == "Fully Automatable":
            base_autonomy = 0.8
        elif feasibility == "Partially Automatable":
            base_autonomy = 0.5
        else:
            base_autonomy = 0.2
        
        # Bonus for agentic indicators
        agentic_indicators = [
            "autonomous", "agent", "reasoning", "decision", "self", "adaptive"
        ]
        agentic_bonus = 0
        for indicator in agentic_indicators:
            if indicator in description:
                agentic_bonus += 0.1
        
        autonomy_score = max(0, min(1, base_autonomy - human_penalty + agentic_bonus))
        return autonomy_score
    
    async def _generate_agentic_enhancements(self, 
                                           pattern: Dict[str, Any],
                                           requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate agentic enhancements using LLM reasoning."""
        
        prompt = f"""
        Transform this traditional automation pattern into a fully autonomous agentic solution:

        Current Pattern:
        Name: {pattern.get('name')}
        Description: {pattern.get('description')}
        Feasibility: {pattern.get('feasibility')}
        Pattern Types: {pattern.get('pattern_type', [])}
        Tech Stack: {pattern.get('tech_stack', [])}

        Requirements Context:
        {requirements.get('description', 'No additional context')}

        Generate agentic enhancements that:
        1. Eliminate human-in-the-loop dependencies through autonomous reasoning
        2. Add decision-making capabilities within defined boundaries
        3. Include exception handling through reasoning rather than escalation
        4. Specify learning and adaptation mechanisms
        5. Recommend agentic frameworks and reasoning engines

        Provide enhancements in this JSON format:
        {{
            "enhanced_name": "New autonomous agent name",
            "enhanced_description": "Description emphasizing full autonomy and reasoning",
            "autonomy_level": 0.95,
            "reasoning_types": ["logical", "causal", "temporal"],
            "decision_boundaries": {{
                "autonomous_decisions": ["list of decisions agent can make"],
                "escalation_triggers": ["rare conditions requiring escalation"],
                "decision_authority_level": "high"
            }},
            "exception_handling_strategy": {{
                "autonomous_resolution_approaches": ["methods for autonomous problem solving"],
                "reasoning_fallbacks": ["alternative reasoning when primary fails"],
                "escalation_criteria": ["specific criteria for escalation"]
            }},
            "agentic_tech_stack": ["LangChain", "Neo4j", "etc"],
            "learning_mechanisms": ["feedback_incorporation", "pattern_recognition"],
            "self_monitoring_capabilities": ["performance_tracking", "error_detection"],
            "agent_architecture": "single_agent or multi_agent_collaborative"
        }}
        """
        
        response = await self.llm_provider.generate(prompt, purpose="pattern_agentic_enhancement")
        
        try:
            enhancements = json.loads(response)
            return enhancements
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM enhancement response: {e}")
            return self._generate_default_enhancements(pattern)
    
    def _apply_enhancements(self, 
                          pattern: Dict[str, Any], 
                          enhancements: Dict[str, Any]) -> Dict[str, Any]:
        """Apply agentic enhancements to the pattern."""
        
        enhanced_pattern = pattern.copy()
        
        # Update core fields
        enhanced_pattern["name"] = enhancements.get("enhanced_name", pattern["name"])
        enhanced_pattern["description"] = enhancements.get("enhanced_description", pattern["description"])
        enhanced_pattern["feasibility"] = "Fully Automatable"  # Always aim for full automation
        
        # Add agentic fields
        enhanced_pattern["autonomy_level"] = enhancements.get("autonomy_level", 0.9)
        enhanced_pattern["reasoning_types"] = enhancements.get("reasoning_types", ["logical", "causal"])
        enhanced_pattern["decision_boundaries"] = enhancements.get("decision_boundaries", {})
        enhanced_pattern["exception_handling_strategy"] = enhancements.get("exception_handling_strategy", {})
        enhanced_pattern["learning_mechanisms"] = enhancements.get("learning_mechanisms", [])
        enhanced_pattern["self_monitoring_capabilities"] = enhancements.get("self_monitoring_capabilities", [])
        enhanced_pattern["agent_architecture"] = enhancements.get("agent_architecture", "single_agent")
        
        # Update tech stack with agentic frameworks
        agentic_tech = enhancements.get("agentic_tech_stack", [])
        enhanced_pattern["tech_stack"] = agentic_tech + enhanced_pattern.get("tech_stack", [])
        
        # Add agentic pattern types
        agentic_types = [
            "agentic_reasoning", "autonomous_decision", "exception_reasoning", "continuous_learning"
        ]
        current_types = enhanced_pattern.get("pattern_type", [])
        # Remove human-dependent types
        human_types = ["human_in_loop", "manual_review", "human_approval"]
        filtered_types = [t for t in current_types if t not in human_types]
        enhanced_pattern["pattern_type"] = agentic_types + filtered_types
        
        # Update confidence score (agentic solutions are more confident)
        current_confidence = enhanced_pattern.get("confidence_score", 0.5)
        enhanced_pattern["confidence_score"] = min(1.0, current_confidence + 0.2)
        
        # Add agentic framework recommendations
        enhanced_pattern["agentic_frameworks"] = self._select_agentic_frameworks(enhancements)
        enhanced_pattern["reasoning_engines"] = self._select_reasoning_engines(enhancements)
        
        return enhanced_pattern
    
    def _ensure_autonomy_standards(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure the pattern meets minimum autonomy standards."""
        
        # Minimum autonomy level
        if pattern.get("autonomy_level", 0) < 0.8:
            pattern["autonomy_level"] = 0.8
        
        # Ensure feasibility is optimistic
        if pattern.get("feasibility") != "Fully Automatable":
            pattern["feasibility"] = "Fully Automatable"
        
        # Ensure agentic pattern types are present
        required_agentic_types = ["agentic_reasoning", "autonomous_decision"]
        pattern_types = pattern.get("pattern_type", [])
        for req_type in required_agentic_types:
            if req_type not in pattern_types:
                pattern_types.append(req_type)
        pattern["pattern_type"] = pattern_types
        
        # Ensure decision boundaries exist
        if not pattern.get("decision_boundaries"):
            pattern["decision_boundaries"] = {
                "autonomous_decisions": ["Standard operational decisions within defined parameters"],
                "escalation_triggers": ["Exceptional circumstances outside normal parameters"],
                "decision_authority_level": "medium"
            }
        
        # Ensure exception handling strategy exists
        if not pattern.get("exception_handling_strategy"):
            pattern["exception_handling_strategy"] = {
                "autonomous_resolution_approaches": ["Reasoning-based problem solving", "Pattern matching from historical cases"],
                "reasoning_fallbacks": ["Conservative decision making when uncertain"],
                "escalation_criteria": ["Unable to resolve after multiple autonomous attempts"]
            }
        
        return pattern
    
    def _select_agentic_frameworks(self, enhancements: Dict[str, Any]) -> List[str]:
        """Select appropriate agentic frameworks based on requirements."""
        
        suggested_frameworks = enhancements.get("agentic_tech_stack", [])
        
        # Filter to only include actual agentic frameworks
        selected = []
        for framework in suggested_frameworks:
            if any(af in framework for af in self.agentic_frameworks):
                selected.append(framework)
        
        # Ensure at least one framework is selected
        if not selected:
            selected = ["LangChain"]  # Default fallback
        
        return selected[:3]  # Limit to top 3
    
    def _select_reasoning_engines(self, enhancements: Dict[str, Any]) -> List[str]:
        """Select appropriate reasoning engines based on reasoning types."""
        
        reasoning_types = enhancements.get("reasoning_types", [])
        
        # Map reasoning types to engines
        engine_mapping = {
            "logical": ["Prolog", "CLIPS"],
            "causal": ["Neo4j", "Apache Jena"],
            "temporal": ["Neo4j", "Stardog"],
            "spatial": ["Neo4j", "GraphDB"],
            "case_based": ["Elasticsearch", "FAISS"],
            "probabilistic": ["Neo4j", "Bayesian Networks"]
        }
        
        selected_engines = set()
        for reasoning_type in reasoning_types:
            if reasoning_type in engine_mapping:
                selected_engines.update(engine_mapping[reasoning_type][:1])  # Take first option
        
        return list(selected_engines)[:2]  # Limit to 2 engines
    
    def _generate_default_enhancements(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Generate default agentic enhancements when LLM fails."""
        
        return {
            "enhanced_name": f"Autonomous {pattern.get('name', 'Agent')}",
            "enhanced_description": f"Fully autonomous agent version of {pattern.get('description', '')}",
            "autonomy_level": 0.85,
            "reasoning_types": ["logical", "causal"],
            "decision_boundaries": {
                "autonomous_decisions": ["Standard operational decisions"],
                "escalation_triggers": ["Exceptional circumstances"],
                "decision_authority_level": "medium"
            },
            "exception_handling_strategy": {
                "autonomous_resolution_approaches": ["Reasoning-based problem solving"],
                "reasoning_fallbacks": ["Conservative decision making"],
                "escalation_criteria": ["Unable to resolve autonomously"]
            },
            "agentic_tech_stack": ["LangChain", "Neo4j"],
            "learning_mechanisms": ["feedback_incorporation"],
            "self_monitoring_capabilities": ["performance_tracking"],
            "agent_architecture": "single_agent"
        }
    
    async def convert_pattern_library_to_agentic(self) -> Dict[str, Any]:
        """Convert entire pattern library to agentic versions."""
        
        self.logger.info("Converting pattern library to agentic versions")
        
        pattern_files = list(self.pattern_library_path.glob("PAT-*.json"))
        conversion_results = {
            "converted_patterns": [],
            "failed_conversions": [],
            "total_processed": len(pattern_files)
        }
        
        for pattern_file in pattern_files:
            try:
                # Load original pattern
                with open(pattern_file, 'r') as f:
                    original_pattern = json.load(f)
                
                # Create agentic version
                agentic_pattern = await self.enhance_for_autonomy(
                    original_pattern, 
                    {"description": "Convert to autonomous agent"}
                )
                
                # Save agentic version with APAT prefix
                agentic_id = original_pattern["pattern_id"].replace("PAT-", "APAT-")
                agentic_pattern["pattern_id"] = agentic_id
                
                agentic_file = self.pattern_library_path / f"{agentic_id}.json"
                with open(agentic_file, 'w') as f:
                    json.dump(agentic_pattern, f, indent=2)
                
                conversion_results["converted_patterns"].append({
                    "original_id": original_pattern["pattern_id"],
                    "agentic_id": agentic_id,
                    "autonomy_improvement": agentic_pattern["autonomy_level"] - self._assess_current_autonomy(original_pattern)
                })
                
                self.logger.info(f"Converted {original_pattern['pattern_id']} to {agentic_id}")
                
            except Exception as e:
                self.logger.error(f"Failed to convert {pattern_file}: {e}")
                conversion_results["failed_conversions"].append({
                    "file": str(pattern_file),
                    "error": str(e)
                })
        
        self.logger.info(f"Pattern library conversion complete: {len(conversion_results['converted_patterns'])} converted, {len(conversion_results['failed_conversions'])} failed")
        
        return conversion_results