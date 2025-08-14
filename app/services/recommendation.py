"""Recommendation generation service."""

from typing import Dict, List, Any, Tuple, Optional
import math
from pathlib import Path

from app.pattern.matcher import MatchResult
from app.state.store import Recommendation
from app.services.pattern_creator import PatternCreator
from app.services.tech_stack_generator import TechStackGenerator
from app.llm.base import LLMProvider
from app.utils.logger import app_logger


class RecommendationService:
    """Service for generating automation recommendations."""
    
    def __init__(self, 
                 confidence_threshold: float = 0.6,
                 pattern_library_path: Optional[Path] = None,
                 llm_provider: Optional[LLMProvider] = None):
        """Initialize recommendation service.
        
        Args:
            confidence_threshold: Minimum confidence for positive recommendations
            pattern_library_path: Path to pattern library for creating new patterns
            llm_provider: LLM provider for pattern creation and tech stack generation
        """
        self.confidence_threshold = confidence_threshold
        self.pattern_creator = None
        self.tech_stack_generator = TechStackGenerator(llm_provider)
        
        if pattern_library_path:
            self.pattern_creator = PatternCreator(pattern_library_path, llm_provider)
    
    async def generate_recommendations(self, 
                                     matches: List[MatchResult], 
                                     requirements: Dict[str, Any],
                                     session_id: str = "unknown") -> List[Recommendation]:
        """Generate recommendations from pattern matches.
        
        Args:
            matches: Pattern matching results
            requirements: User requirements
            session_id: Session ID for tracking
            
        Returns:
            List of recommendations sorted by confidence
        """
        app_logger.info(f"Generating recommendations from {len(matches)} pattern matches")
        
        # Pre-processing scope gate for physical tasks
        description = requirements.get('description', '').lower()
        physical_indicators = [
            'feed', 'feeding', 'water', 'watering', 'clean', 'cleaning', 
            'walk', 'walking', 'pick up', 'pickup', 'move', 'moving',
            'pet', 'animal', 'plant', 'garden', 'physical', 'manually',
            'snail', 'dog', 'cat', 'bird', 'fish'
        ]
        
        digital_indicators = [
            'remind', 'notification', 'alert', 'schedule', 'track', 'monitor',
            'order', 'purchase', 'api', 'webhook', 'database', 'software',
            'app', 'system', 'digital', 'online', 'email', 'sms', 'automate'
        ]
        
        physical_score = sum(1 for indicator in physical_indicators if indicator in description)
        digital_score = sum(1 for indicator in digital_indicators if indicator in description)
        
        recommendations = []
        
        # If clearly physical with minimal digital indicators, create "Not Automatable" recommendation
        # Note: "automate" is often used in physical task descriptions, so we allow for 1 digital indicator
        if physical_score >= 2 and digital_score <= 1:
            app_logger.info(f"🚫 SCOPE GATE: Creating 'Not Automatable' recommendation for physical task - '{description[:100]}...'")
            physical_recommendation = Recommendation(
                pattern_id="PHYSICAL_TASK",
                feasibility="Not Automatable",
                confidence=0.95,
                reasoning=f"This requirement involves physical manipulation that cannot be automated by software agents. The task requires physical actions like picking up and feeding a pet, which are outside the scope of digital automation. Digital alternatives like 'send feeding reminders' or 'track feeding schedule' could be automated instead.",
                tech_stack=[]
            )
            return [physical_recommendation]
        
        # Check if we need to create a new pattern
        should_create_pattern = await self._should_create_new_pattern(matches, requirements, session_id)
        
        if should_create_pattern and self.pattern_creator:
            app_logger.info("No suitable existing patterns found, creating new pattern")
            try:
                new_pattern = await self.pattern_creator.create_pattern_from_requirements(
                    requirements, session_id
                )
                
                # Create a MatchResult for the new pattern
                new_match = MatchResult(
                    pattern_id=new_pattern["pattern_id"],
                    pattern_name=new_pattern["name"],
                    feasibility=new_pattern["feasibility"],
                    tech_stack=new_pattern["tech_stack"],
                    confidence=new_pattern["confidence_score"],
                    tag_score=1.0,  # Perfect tag match since it was created from requirements
                    vector_score=0.8,  # High vector score for custom pattern
                    blended_score=0.9,  # High blended score
                    rationale=f"Custom pattern created for this specific requirement"
                )
                
                # Add the new pattern match to the beginning of the list
                matches = [new_match] + matches
                app_logger.info(f"Created new pattern {new_pattern['pattern_id']}: {new_pattern['name']}")
                
            except Exception as e:
                app_logger.error(f"Failed to create new pattern: {e}")
                # Continue with existing matches if pattern creation fails
        
        for match in matches:
            # Determine feasibility based on pattern and requirements
            feasibility = self._determine_feasibility(match, requirements)
            
            # Calculate adjusted confidence score
            confidence = self._calculate_confidence(match, requirements, feasibility)
            
            # Generate intelligent tech stack suggestions
            tech_stack = await self._generate_intelligent_tech_stack(matches, requirements, match)
            
            # Generate comprehensive reasoning (now pattern-specific)
            reasoning = self._generate_reasoning(match, requirements, feasibility, confidence)
            
            # Enhance pattern with LLM insights if it's a good match
            if match.blended_score > 0.8 and requirements.get("llm_analysis_feasibility_reasoning"):
                await self._enhance_pattern_with_llm_insights(match, requirements, session_id)
            
            recommendation = Recommendation(
                pattern_id=match.pattern_id,
                feasibility=feasibility,
                confidence=confidence,
                tech_stack=tech_stack,
                reasoning=reasoning
            )
            
            recommendations.append(recommendation)
        
        # Sort by confidence (descending)
        recommendations.sort(key=lambda r: r.confidence, reverse=True)
        
        app_logger.info(f"Generated {len(recommendations)} recommendations")
        return recommendations
    
    def _determine_feasibility(self, match: MatchResult, requirements: Dict[str, Any]) -> str:
        """Determine feasibility based on LLM analysis first, then pattern match and requirements complexity.
        
        Args:
            match: Pattern matching result
            requirements: User requirements
            
        Returns:
            Feasibility assessment: "Automatable", "Partially Automatable", or "Not Automatable"
        """
        # Prioritize LLM analysis if available
        llm_feasibility = requirements.get("llm_analysis_automation_feasibility")
        if llm_feasibility:
            app_logger.info(f"Using LLM feasibility assessment: {llm_feasibility}")
            # Map LLM response to our format
            if llm_feasibility == "Automatable":
                return "Automatable"
            elif llm_feasibility == "Partially Automatable":
                return "Partially Automatable"
            elif llm_feasibility == "Not Automatable":
                return "Not Automatable"
            else:
                # Handle exact matches
                return llm_feasibility
        
        # Fallback to pattern-based analysis
        app_logger.info(f"No LLM feasibility found, using pattern-based analysis")
        base_feasibility = match.feasibility
        
        # Analyze complexity factors
        complexity_factors = self._analyze_complexity_factors(requirements)
        complexity_score = sum(complexity_factors.values())
        
        # Analyze risk factors
        risk_factors = self._analyze_risk_factors(requirements)
        risk_score = sum(risk_factors.values())
        
        # Consider pattern confidence and match quality
        match_quality = match.blended_score
        
        app_logger.debug(f"Feasibility analysis for {match.pattern_id}: "
                        f"base={base_feasibility}, complexity={complexity_score}, "
                        f"risk={risk_score}, match_quality={match_quality}")
        
        # More lenient decision logic for better user experience
        if base_feasibility in ["Automatable", "Yes"]:
            if complexity_score >= 5 or risk_score >= 4:
                return "Not Automatable"
            elif complexity_score >= 3 or risk_score >= 3 or match_quality < 0.4:
                return "Partially Automatable"
            else:
                return "Automatable"
        elif base_feasibility in ["Partially Automatable", "Partial"]:
            if complexity_score >= 4 or risk_score >= 3:
                return "Not Automatable"
            elif match_quality < 0.3:
                return "Not Automatable"
            else:
                return "Partially Automatable"
        else:  # Not Automatable or No
            if match_quality > 0.7 and complexity_score <= 2 and risk_score <= 1:
                return "Partially Automatable"
            else:
                return "Not Automatable"
    
    def _analyze_complexity_factors(self, requirements: Dict[str, Any]) -> Dict[str, int]:
        """Analyze complexity factors in requirements.
        
        Args:
            requirements: User requirements
            
        Returns:
            Dictionary of complexity factors with scores
        """
        factors = {}
        
        # Data sensitivity complexity
        data_sensitivity = requirements.get("data_sensitivity", "").lower()
        if data_sensitivity == "high":
            factors["data_sensitivity"] = 2
        elif data_sensitivity == "medium":
            factors["data_sensitivity"] = 1
        else:
            factors["data_sensitivity"] = 0
        
        # Integration complexity - be more lenient for typical use cases
        integrations = requirements.get("integrations", [])
        if len(integrations) > 8:
            factors["integrations"] = 3
        elif len(integrations) > 5:
            factors["integrations"] = 2
        elif len(integrations) > 2:
            factors["integrations"] = 1
        else:
            factors["integrations"] = 0
        
        # Workflow complexity - be more lenient
        workflow_steps = requirements.get("workflow_steps", [])
        if len(workflow_steps) > 15:
            factors["workflow_complexity"] = 2
        elif len(workflow_steps) > 8:
            factors["workflow_complexity"] = 1
        else:
            factors["workflow_complexity"] = 0
        
        # Volume complexity - be more lenient
        volume = requirements.get("volume", {})
        daily_volume = volume.get("daily", 0)
        if daily_volume > 50000:
            factors["volume"] = 2
        elif daily_volume > 5000:
            factors["volume"] = 1
        else:
            factors["volume"] = 0
        
        # Description complexity - analyze the description text
        description = requirements.get("description", "")
        if description:
            desc_lower = description.lower()
            
            # Check for physical/impossible tasks first
            physical_keywords = [
                "paint", "painting", "build", "construction", "repair", "fix", "install",
                "clean", "cleaning", "move", "transport", "deliver", "physical", "manual",
                "hardware", "mechanical", "electrical wiring", "plumbing", "carpentry",
                "landscaping", "gardening", "cooking", "driving", "walking", "running"
            ]
            
            physical_count = sum(1 for keyword in physical_keywords if keyword in desc_lower)
            if physical_count > 0:
                # Physical tasks get maximum complexity to make them "Not Automatable"
                factors["physical_impossibility"] = 10
            
            # Regular complexity keywords
            complexity_keywords = [
                "complex", "multiple", "various", "different", "several", 
                "integrate", "synchronize", "coordinate", "orchestrate",
                "real-time", "concurrent", "parallel", "distributed"
            ]
            
            keyword_count = sum(1 for keyword in complexity_keywords if keyword in desc_lower)
            if keyword_count >= 5:
                factors["description_complexity"] = 2
            elif keyword_count >= 2:
                factors["description_complexity"] = 1
            else:
                factors["description_complexity"] = 0
        else:
            factors["description_complexity"] = 0
        
        return factors
    
    def _analyze_risk_factors(self, requirements: Dict[str, Any]) -> Dict[str, int]:
        """Analyze risk factors in requirements.
        
        Args:
            requirements: User requirements
            
        Returns:
            Dictionary of risk factors with scores
        """
        factors = {}
        
        # Compliance requirements
        compliance = requirements.get("compliance", [])
        if isinstance(compliance, str):
            compliance = [compliance]
        
        high_risk_compliance = ["GDPR", "HIPAA", "SOX", "PCI-DSS"]
        if any(comp in high_risk_compliance for comp in compliance):
            factors["compliance"] = 3
        elif compliance:
            factors["compliance"] = 1
        else:
            factors["compliance"] = 0
        
        # Human review requirements
        human_review = requirements.get("human_review", "").lower()
        if human_review == "required":
            factors["human_review"] = 2
        elif human_review == "optional":
            factors["human_review"] = 1
        else:
            factors["human_review"] = 0
        
        # SLA requirements
        sla = requirements.get("sla", {})
        response_time = sla.get("response_time_ms", 0)
        if response_time > 0 and response_time < 1000:  # Sub-second SLA
            factors["sla"] = 2
        elif response_time > 0 and response_time < 5000:  # Sub-5-second SLA
            factors["sla"] = 1
        else:
            factors["sla"] = 0
        
        # Physical task risk - check description for physical activities
        description = requirements.get("description", "").lower()
        physical_keywords = [
            "paint", "painting", "build", "construction", "repair", "fix", "install",
            "clean", "cleaning", "move", "transport", "deliver", "physical", "manual",
            "hardware", "mechanical", "electrical wiring", "plumbing", "carpentry",
            "landscaping", "gardening", "cooking", "driving", "walking", "running"
        ]
        
        physical_count = sum(1 for keyword in physical_keywords if keyword in description)
        if physical_count > 0:
            factors["physical_task_risk"] = 10  # Maximum risk for physical tasks
        
        return factors
    
    def _calculate_confidence(self, 
                            match: MatchResult, 
                            requirements: Dict[str, Any], 
                            feasibility: str) -> float:
        """Calculate adjusted confidence score.
        
        Args:
            match: Pattern matching result
            requirements: User requirements
            feasibility: Determined feasibility
            
        Returns:
            Adjusted confidence score (0.0 to 1.0)
        """
        # Prioritize LLM confidence if available
        llm_confidence = requirements.get("llm_analysis_confidence_level")
        if llm_confidence and isinstance(llm_confidence, (int, float)):
            app_logger.info(f"Using LLM confidence: {llm_confidence}")
            return min(max(llm_confidence, 0.0), 1.0)  # Ensure it's between 0 and 1
        
        # Fallback to pattern-based confidence calculation
        app_logger.info("Using pattern-based confidence calculation")
        base_confidence = match.blended_score
        
        # Adjust based on feasibility determination
        feasibility_multiplier = {
            "Automatable": 1.0,
            "Partially Automatable": 0.7,
            "Not Automatable": 0.3
        }
        
        # Adjust based on pattern's inherent confidence
        pattern_confidence = match.confidence
        
        # Adjust based on requirements completeness
        completeness_score = self._calculate_completeness_score(requirements)
        
        # Calculate final confidence
        confidence = (
            base_confidence * 0.4 +
            pattern_confidence * 0.3 +
            completeness_score * 0.3
        ) * feasibility_multiplier[feasibility]
        
        # Ensure confidence is within bounds
        confidence = max(0.0, min(1.0, confidence))
        
        app_logger.debug(f"Confidence calculation for {match.pattern_id}: "
                        f"base={base_confidence:.3f}, pattern={pattern_confidence:.3f}, "
                        f"completeness={completeness_score:.3f}, "
                        f"feasibility_mult={feasibility_multiplier[feasibility]:.3f}, "
                        f"final={confidence:.3f}")
        
        return confidence
    
    def _calculate_completeness_score(self, requirements: Dict[str, Any]) -> float:
        """Calculate how complete the requirements are.
        
        Args:
            requirements: User requirements
            
        Returns:
            Completeness score (0.0 to 1.0)
        """
        # Define key fields that should be present
        key_fields = [
            "description", "domain", "workflow_steps", "integrations",
            "data_sensitivity", "volume", "sla"
        ]
        
        present_fields = 0
        for field in key_fields:
            value = requirements.get(field)
            if value and (
                (isinstance(value, str) and value.strip()) or
                (isinstance(value, (list, dict)) and len(value) > 0) or
                (isinstance(value, (int, float)) and value > 0)
            ):
                present_fields += 1
        
        return present_fields / len(key_fields)
    
    async def _generate_intelligent_tech_stack(self, 
                                              matches: List[MatchResult], 
                                              requirements: Dict[str, Any],
                                              current_match: MatchResult) -> List[str]:
        """Generate intelligent tech stack using the new TechStackGenerator.
        
        Args:
            matches: All pattern matches for context
            requirements: User requirements
            current_match: The specific match being processed
            
        Returns:
            List of recommended technologies
        """
        try:
            # Extract constraints from requirements and patterns
            req_constraints = requirements.get("constraints", {})
            constraints = {
                "banned_tools": req_constraints.get("banned_tools", []),
                "required_integrations": req_constraints.get("required_integrations", []),
                "compliance_requirements": req_constraints.get("compliance_requirements", []),
                "data_sensitivity": req_constraints.get("data_sensitivity"),
                "budget_constraints": req_constraints.get("budget_constraints"),
                "deployment_preference": req_constraints.get("deployment_preference")
            }
            
            # Add pattern-specific constraints
            if hasattr(current_match, 'constraints') and current_match.constraints:
                constraints["banned_tools"].extend(current_match.constraints.get("banned_tools", []))
                constraints["required_integrations"].extend(current_match.constraints.get("required_integrations", []))
            
            # Generate intelligent tech stack
            tech_stack = await self.tech_stack_generator.generate_tech_stack(
                matches, requirements, constraints
            )
            
            app_logger.info(f"Generated intelligent tech stack for {current_match.pattern_id}: {tech_stack}")
            return tech_stack
            
        except Exception as e:
            app_logger.error(f"Failed to generate intelligent tech stack: {e}")
            
            # Fallback to pattern's base tech stack
            fallback_stack = current_match.tech_stack.copy() if current_match.tech_stack else []
            app_logger.info(f"Using fallback tech stack: {fallback_stack}")
            return fallback_stack
    
    def _generate_reasoning(self, 
                          match: MatchResult, 
                          requirements: Dict[str, Any], 
                          feasibility: str, 
                          confidence: float) -> str:
        """Generate comprehensive human-readable reasoning.
        
        Args:
            match: Pattern matching result
            requirements: User requirements
            feasibility: Determined feasibility
            confidence: Calculated confidence
            
        Returns:
            Detailed reasoning string
        """
        # Enhance pattern reasoning with LLM insights if available
        llm_reasoning = requirements.get("llm_analysis_feasibility_reasoning")
        llm_insights = requirements.get("llm_analysis_key_insights", [])
        llm_challenges = requirements.get("llm_analysis_automation_challenges", [])
        
        if llm_reasoning and match.blended_score > 0.7:
            # For good pattern matches, blend LLM insights with pattern-specific reasoning
            app_logger.info(f"Enhancing pattern reasoning for {match.pattern_name} with LLM insights")
            
            pattern_specific = f"Based on the '{match.pattern_name}' pattern with {match.blended_score:.0%} match confidence"
            
            # Add LLM insights as enhancements
            enhanced_reasoning = [pattern_specific, llm_reasoning]
            
            if llm_insights:
                enhanced_reasoning.append(f"Key insights: {', '.join(llm_insights[:2])}")
            
            if llm_challenges:
                enhanced_reasoning.append(f"Main challenges: {', '.join(llm_challenges[:2])}")
            
            return ". ".join(enhanced_reasoning)
        
        elif llm_reasoning:
            # For poor pattern matches, use LLM reasoning but note the pattern mismatch
            app_logger.info(f"Using LLM reasoning due to poor pattern match ({match.blended_score:.0%})")
            return f"Pattern match with '{match.pattern_name}' is moderate ({match.blended_score:.0%}). {llm_reasoning}"
        
        # Fallback to pattern-based reasoning with unique insights per pattern
        app_logger.info(f"Using pattern-based reasoning for {match.pattern_name}")
        reasoning_parts = []
        
        # Pattern match quality with pattern-specific context
        pattern_context = self._get_pattern_specific_context(match, requirements)
        
        if match.blended_score > 0.8:
            reasoning_parts.append(f"Excellent pattern match ({match.blended_score:.0%}) with '{match.pattern_name}'. {pattern_context}")
        elif match.blended_score > 0.6:
            reasoning_parts.append(f"Good pattern match ({match.blended_score:.0%}) with '{match.pattern_name}'. {pattern_context}")
        else:
            reasoning_parts.append(f"Moderate pattern match ({match.blended_score:.0%}) with '{match.pattern_name}'. {pattern_context}")
        
        # Feasibility reasoning
        if feasibility == "Yes":
            reasoning_parts.append("Full automation is recommended")
            
            # Add specific reasons for positive assessment
            complexity_factors = self._analyze_complexity_factors(requirements)
            risk_factors = self._analyze_risk_factors(requirements)
            
            if sum(complexity_factors.values()) <= 1:
                reasoning_parts.append("due to low complexity requirements")
            if sum(risk_factors.values()) <= 1:
                reasoning_parts.append("and minimal risk factors")
                
        elif feasibility == "Partially Automatable":
            reasoning_parts.append("Partial automation is feasible")
            
            # Identify specific challenges
            complexity_factors = self._analyze_complexity_factors(requirements)
            risk_factors = self._analyze_risk_factors(requirements)
            
            challenges = []
            if complexity_factors.get("data_sensitivity", 0) >= 2:
                challenges.append("high data sensitivity")
            if complexity_factors.get("integrations", 0) >= 2:
                challenges.append("complex integrations")
            if risk_factors.get("compliance", 0) >= 2:
                challenges.append("strict compliance requirements")
            if risk_factors.get("human_review", 0) >= 1:
                challenges.append("human review requirements")
            
            if challenges:
                reasoning_parts.append(f"with human oversight needed for {', '.join(challenges)}")
                
        else:  # No
            reasoning_parts.append("Automation is not recommended")
            
            # Identify blocking factors
            complexity_factors = self._analyze_complexity_factors(requirements)
            risk_factors = self._analyze_risk_factors(requirements)
            
            blockers = []
            if sum(complexity_factors.values()) >= 4:
                blockers.append("high complexity")
            if sum(risk_factors.values()) >= 3:
                blockers.append("significant risk factors")
            if match.blended_score < 0.4:
                blockers.append("poor pattern fit")
            
            if blockers:
                reasoning_parts.append(f"due to {', '.join(blockers)}")
        
        # Confidence reasoning
        if confidence > 0.8:
            reasoning_parts.append(f"High confidence ({confidence:.0%}) in this assessment")
        elif confidence > 0.6:
            reasoning_parts.append(f"Moderate confidence ({confidence:.0%}) in this assessment")
        else:
            reasoning_parts.append(f"Lower confidence ({confidence:.0%}) - additional analysis recommended")
        
        # Tech stack reasoning
        if match.tech_stack:
            tech_list = ", ".join(match.tech_stack[:4])  # Show up to 4 technologies
            if len(match.tech_stack) > 4:
                tech_list += f" and {len(match.tech_stack) - 4} others"
            reasoning_parts.append(f"Recommended technologies include {tech_list}")
        
        return ". ".join(reasoning_parts) + "."
    
    async def _should_create_new_pattern(self, matches: List[MatchResult], requirements: Dict[str, Any], session_id: str = "unknown") -> bool:
        """Determine if a new pattern should be created or if an existing one should be enhanced.
        
        Args:
            matches: Existing pattern matches
            requirements: User requirements
            session_id: Session ID for tracking
            
        Returns:
            True if a new pattern should be created, False if existing pattern should be enhanced or used
        """
        # Create new pattern if no matches at all
        if not matches:
            app_logger.info("No existing pattern matches found - will create new pattern")
            return True
        
        # Create new pattern if all matches have low scores
        best_match_score = max(match.blended_score for match in matches)
        if best_match_score < 0.4:
            app_logger.info(f"Best match score {best_match_score:.3f} is too low - will create new pattern")
            return True
        
        # NEW: Check for conceptual similarity with existing patterns
        # If we find a conceptually similar pattern, enhance it instead of creating a new one
        best_match = matches[0]
        if await self._is_conceptually_similar(best_match, requirements):
            app_logger.info(f"Found conceptually similar pattern {best_match.pattern_id} - will enhance instead of creating new")
            await self._enhance_existing_pattern(best_match, requirements, session_id)
            return False
        
        # Create new pattern if the requirement is very specific and unique
        description = requirements.get("description", "").lower()
        
        # Check for unique/specific scenarios that likely need custom patterns
        unique_indicators = [
            "amazon connect",  # Specific AWS service
            "real-time translation",  # Specific real-time requirement
            "bidirectional translation",  # Specific translation requirement
            "native language",  # Language preference requirement
            "system settings",  # User preference integration
            "customer chat",  # Specific communication context
        ]
        
        unique_score = sum(1 for indicator in unique_indicators if indicator in description)
        if unique_score >= 2:
            app_logger.info(f"Detected unique scenario (score: {unique_score}) - will create new pattern")
            return True
        
        # Check for domain-specific requirements that don't match well
        domain = requirements.get("domain", "")
        if domain and matches:
            # If we have a specific domain but the best match is from a different domain
            # and the score isn't great, create a new pattern
            if best_match.blended_score < 0.7 and domain not in ["general", "automation"]:
                app_logger.info(f"Domain-specific requirement ({domain}) with mediocre match - will create new pattern")
                return True
        
        # Don't create new pattern if we have good existing matches
        app_logger.info(f"Found adequate existing matches (best: {best_match_score:.3f}) - will use existing patterns")
        return False
    
    async def _is_conceptually_similar(self, match: MatchResult, requirements: Dict[str, Any]) -> bool:
        """Check if a pattern is conceptually similar to the requirements.
        
        This checks for patterns that solve the same core business problem but may have
        different technical implementations or minor variations.
        
        Args:
            match: Best matching pattern
            requirements: User requirements
            
        Returns:
            True if the pattern is conceptually similar and should be enhanced
        """
        # Load the full pattern data to analyze
        try:
            from app.pattern.loader import PatternLoader
            from pathlib import Path
            pattern_loader = PatternLoader(Path("data/patterns"))
            patterns = pattern_loader.load_patterns()
            
            pattern_data = None
            for pattern in patterns:
                if pattern.get("pattern_id") == match.pattern_id:
                    pattern_data = pattern
                    break
            
            if not pattern_data:
                return False
            
            # Check for conceptual similarity indicators
            similarity_score = 0
            total_checks = 0
            
            # 1. Same core business process (high weight)
            req_desc = requirements.get("description", "").lower()
            pattern_desc = pattern_data.get("description", "").lower()
            
            # Core business process keywords
            business_keywords = [
                "identity verification", "card blocking", "chatbot", "otp", "security questions",
                "fraud detection", "authentication", "authorization", "user verification",
                "account security", "two-factor", "multi-factor"
            ]
            
            req_business_matches = sum(1 for keyword in business_keywords if keyword in req_desc)
            pattern_business_matches = sum(1 for keyword in business_keywords if keyword in pattern_desc)
            
            if req_business_matches > 0 and pattern_business_matches > 0:
                # Calculate overlap ratio
                overlap = min(req_business_matches, pattern_business_matches)
                total_matches = max(req_business_matches, pattern_business_matches)
                business_similarity = overlap / total_matches
                similarity_score += business_similarity * 0.4  # 40% weight
            total_checks += 0.4
            
            # 2. Same domain (medium weight)
            req_domain = requirements.get("domain", "")
            pattern_domain = pattern_data.get("domain", "")
            if req_domain and pattern_domain and req_domain == pattern_domain:
                similarity_score += 0.2  # 20% weight
            total_checks += 0.2
            
            # 3. Similar pattern types (medium weight)
            req_pattern_types = set(requirements.get("pattern_types", []))
            pattern_types = set(pattern_data.get("pattern_type", []))
            if req_pattern_types and pattern_types:
                type_overlap = len(req_pattern_types.intersection(pattern_types))
                type_total = len(req_pattern_types.union(pattern_types))
                if type_total > 0:
                    type_similarity = type_overlap / type_total
                    similarity_score += type_similarity * 0.2  # 20% weight
            total_checks += 0.2
            
            # 4. Similar feasibility and complexity (low weight)
            req_feasibility = requirements.get("feasibility", "")
            pattern_feasibility = pattern_data.get("feasibility", "")
            if req_feasibility and pattern_feasibility and req_feasibility == pattern_feasibility:
                similarity_score += 0.1  # 10% weight
            total_checks += 0.1
            
            # 5. Similar compliance requirements (low weight)
            req_compliance = set(requirements.get("compliance", []))
            pattern_compliance = set(pattern_data.get("constraints", {}).get("compliance_requirements", []))
            if req_compliance and pattern_compliance:
                compliance_overlap = len(req_compliance.intersection(pattern_compliance))
                compliance_total = len(req_compliance.union(pattern_compliance))
                if compliance_total > 0:
                    compliance_similarity = compliance_overlap / compliance_total
                    similarity_score += compliance_similarity * 0.1  # 10% weight
            total_checks += 0.1
            
            # Calculate final similarity score
            if total_checks > 0:
                final_similarity = similarity_score / total_checks
            else:
                final_similarity = 0
            
            # Consider it conceptually similar if similarity > 70%
            is_similar = final_similarity > 0.7
            
            app_logger.info(f"Conceptual similarity check for {match.pattern_id}: {final_similarity:.3f} ({'similar' if is_similar else 'different'})")
            
            return is_similar
            
        except Exception as e:
            app_logger.error(f"Error checking conceptual similarity: {e}")
            return False
    
    async def _enhance_existing_pattern(self, match: MatchResult, requirements: Dict[str, Any], session_id: str):
        """Enhance an existing pattern with new requirements data.
        
        Args:
            match: Pattern to enhance
            requirements: New requirements to incorporate
            session_id: Session ID for tracking
        """
        try:
            from app.pattern.loader import PatternLoader
            import json
            from pathlib import Path
            from datetime import datetime
            
            pattern_loader = PatternLoader(Path("data/patterns"))
            patterns = pattern_loader.load_patterns()
            
            # Find the pattern to enhance
            pattern_data = None
            for pattern in patterns:
                if pattern.get("pattern_id") == match.pattern_id:
                    pattern_data = pattern.copy()
                    break
            
            if not pattern_data:
                app_logger.error(f"Could not find pattern {match.pattern_id} to enhance")
                return
            
            app_logger.info(f"Enhancing pattern {match.pattern_id} with new requirements")
            
            # Track enhancement
            if "enhanced_sessions" not in pattern_data:
                pattern_data["enhanced_sessions"] = []
            pattern_data["enhanced_sessions"].append(session_id)
            pattern_data["last_enhanced"] = datetime.now().isoformat()
            
            # Merge tech stack (avoid duplicates)
            existing_tech = set(pattern_data.get("tech_stack", []))
            new_tech = set()
            
            # Extract tech from requirements if available
            if "tech_stack" in requirements:
                new_tech.update(requirements["tech_stack"])
            
            # Use LLM to suggest additional tech based on requirements
            if self.pattern_creator and self.pattern_creator.llm_provider:
                try:
                    suggested_tech = await self._suggest_additional_tech(pattern_data, requirements)
                    new_tech.update(suggested_tech)
                except Exception as e:
                    app_logger.warning(f"Could not get LLM tech suggestions: {e}")
            
            # Merge tech stacks
            if new_tech:
                merged_tech = list(existing_tech.union(new_tech))
                pattern_data["tech_stack"] = merged_tech
                app_logger.info(f"Enhanced tech stack: added {list(new_tech - existing_tech)}")
            
            # Merge pattern types
            existing_types = set(pattern_data.get("pattern_type", []))
            new_types = set(requirements.get("pattern_types", []))
            if new_types:
                merged_types = list(existing_types.union(new_types))
                pattern_data["pattern_type"] = merged_types
                if new_types - existing_types:
                    app_logger.info(f"Enhanced pattern types: added {list(new_types - existing_types)}")
            
            # Merge integrations
            existing_integrations = set(pattern_data.get("constraints", {}).get("required_integrations", []))
            new_integrations = set(requirements.get("integrations", []))
            if new_integrations:
                if "constraints" not in pattern_data:
                    pattern_data["constraints"] = {}
                merged_integrations = list(existing_integrations.union(new_integrations))
                pattern_data["constraints"]["required_integrations"] = merged_integrations
                if new_integrations - existing_integrations:
                    app_logger.info(f"Enhanced integrations: added {list(new_integrations - existing_integrations)}")
            
            # Merge compliance requirements
            existing_compliance = set(pattern_data.get("constraints", {}).get("compliance_requirements", []))
            new_compliance = set(requirements.get("compliance", []))
            if new_compliance:
                if "constraints" not in pattern_data:
                    pattern_data["constraints"] = {}
                merged_compliance = list(existing_compliance.union(new_compliance))
                pattern_data["constraints"]["compliance_requirements"] = merged_compliance
                if new_compliance - existing_compliance:
                    app_logger.info(f"Enhanced compliance: added {list(new_compliance - existing_compliance)}")
            
            # Update automation metadata if more specific info is available
            if "automation_metadata" in requirements:
                if "automation_metadata" not in pattern_data:
                    pattern_data["automation_metadata"] = {}
                
                req_metadata = requirements["automation_metadata"]
                pattern_metadata = pattern_data["automation_metadata"]
                
                # Update with more specific values
                for key, value in req_metadata.items():
                    if key not in pattern_metadata or value != "unknown":
                        pattern_metadata[key] = value
            
            # Save the enhanced pattern
            pattern_file = Path("data/patterns") / f"{match.pattern_id}.json"
            with open(pattern_file, 'w') as f:
                json.dump(pattern_data, f, indent=2)
            
            app_logger.info(f"Successfully enhanced pattern {match.pattern_id}")
            
        except Exception as e:
            app_logger.error(f"Failed to enhance pattern {match.pattern_id}: {e}")
    
    async def _suggest_additional_tech(self, pattern_data: Dict[str, Any], requirements: Dict[str, Any]) -> List[str]:
        """Use LLM to suggest additional technologies for pattern enhancement.
        
        Args:
            pattern_data: Existing pattern data
            requirements: New requirements
            
        Returns:
            List of suggested additional technologies
        """
        if not self.pattern_creator or not self.pattern_creator.llm_provider:
            return []
        
        existing_tech = pattern_data.get("tech_stack", [])
        req_description = requirements.get("description", "")
        
        prompt = f"""You are a senior software architect. An existing automation pattern is being enhanced with new requirements.

EXISTING PATTERN:
- Name: {pattern_data.get('name', 'Unknown')}
- Current Tech Stack: {', '.join(existing_tech)}
- Description: {pattern_data.get('description', 'No description')}

NEW REQUIREMENTS:
{req_description}

Based on the new requirements, suggest 0-3 additional technologies that would enhance this pattern.
Only suggest technologies that are:
1. Not already in the current tech stack
2. Directly relevant to the new requirements
3. Commonly used and well-established

Respond with a JSON array of technology names only, e.g. ["OAuth2", "DynamoDB"]
If no additional technologies are needed, return an empty array [].
"""
        
        try:
            response = await self.pattern_creator.llm_provider.generate(prompt, purpose="pattern_enhancement")
            
            # Parse JSON response
            if isinstance(response, str):
                import re
                json_match = re.search(r'\[.*\]', response, re.DOTALL)
                if json_match:
                    import json
                    suggested_tech = json.loads(json_match.group())
                    if isinstance(suggested_tech, list):
                        # Filter out existing tech
                        new_tech = [tech for tech in suggested_tech if tech not in existing_tech]
                        return new_tech[:3]  # Limit to 3 suggestions
            
            return []
            
        except Exception as e:
            app_logger.warning(f"Failed to get LLM tech suggestions: {e}")
            return []
    
    async def _enhance_pattern_with_llm_insights(self, 
                                               match: MatchResult, 
                                               requirements: Dict[str, Any], 
                                               session_id: str) -> None:
        """Enhance an existing pattern with LLM insights if it's a good match.
        
        Args:
            match: Pattern matching result
            requirements: User requirements with LLM analysis
            session_id: Session ID for tracking
        """
        try:
            llm_insights = requirements.get("llm_analysis_key_insights", [])
            llm_challenges = requirements.get("llm_analysis_automation_challenges", [])
            llm_approach = requirements.get("llm_analysis_recommended_approach", "")
            
            if not (llm_insights or llm_challenges or llm_approach):
                return
            
            app_logger.info(f"Enhancing pattern {match.pattern_id} with LLM insights")
            
            # Load the existing pattern
            if not self.pattern_creator:
                return
            
            pattern_file = self.pattern_creator.pattern_library_path / f"{match.pattern_id}.json"
            if not pattern_file.exists():
                return
            
            import json
            with open(pattern_file, 'r') as f:
                pattern_data = json.load(f)
            
            # Add LLM insights to pattern (without overwriting existing data)
            if llm_insights and "llm_insights" not in pattern_data:
                pattern_data["llm_insights"] = llm_insights[:3]  # Top 3 insights
            
            if llm_challenges and "llm_challenges" not in pattern_data:
                pattern_data["llm_challenges"] = llm_challenges[:3]  # Top 3 challenges
            
            if llm_approach and "llm_recommended_approach" not in pattern_data:
                pattern_data["llm_recommended_approach"] = llm_approach
            
            # Add enhancement metadata
            pattern_data["enhanced_by_llm"] = True
            pattern_data["enhanced_from_session"] = session_id
            
            # Save the enhanced pattern
            with open(pattern_file, 'w') as f:
                json.dump(pattern_data, f, indent=2)
            
            app_logger.info(f"Enhanced pattern {match.pattern_id} with LLM insights")
            
        except Exception as e:
            app_logger.error(f"Failed to enhance pattern {match.pattern_id}: {e}")
    
    def _get_pattern_specific_context(self, match: MatchResult, requirements: Dict[str, Any]) -> str:
        """Get pattern-specific context to make reasoning unique per pattern.
        
        Args:
            match: Pattern matching result
            requirements: User requirements
            
        Returns:
            Pattern-specific context string
        """
        # Create unique context based on pattern characteristics
        context_parts = []
        
        # Add pattern domain context
        if hasattr(match, 'domain') and match.domain:
            context_parts.append(f"This {match.domain} pattern")
        
        # Add pattern-specific insights based on pattern name/type
        pattern_name_lower = match.pattern_name.lower()
        
        if "physical" in pattern_name_lower:
            context_parts.append("addresses physical automation challenges")
        elif "api" in pattern_name_lower or "integration" in pattern_name_lower:
            context_parts.append("focuses on system integration capabilities")
        elif "monitoring" in pattern_name_lower:
            context_parts.append("emphasizes monitoring and alerting features")
        elif "workflow" in pattern_name_lower:
            context_parts.append("handles complex workflow orchestration")
        else:
            context_parts.append("provides general automation guidance")
        
        # Add confidence-based context
        if match.confidence > 0.8:
            context_parts.append("with high implementation confidence")
        elif match.confidence > 0.6:
            context_parts.append("with moderate implementation confidence")
        else:
            context_parts.append("requiring careful implementation planning")
        
        return " ".join(context_parts) if context_parts else "provides automation guidance"