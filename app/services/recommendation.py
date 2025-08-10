"""Recommendation generation service."""

from typing import Dict, List, Any, Tuple, Optional
import math
from pathlib import Path

from app.pattern.matcher import MatchResult
from app.state.store import Recommendation
from app.services.pattern_creator import PatternCreator
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
            llm_provider: LLM provider for pattern creation
        """
        self.confidence_threshold = confidence_threshold
        self.pattern_creator = None
        
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
        
        recommendations = []
        
        # Check if we need to create a new pattern
        should_create_pattern = self._should_create_new_pattern(matches, requirements)
        
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
            
            # Generate tech stack suggestions
            tech_stack = self._suggest_tech_stack(match, requirements)
            
            # Generate comprehensive reasoning
            reasoning = self._generate_reasoning(match, requirements, feasibility, confidence)
            
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
        """Determine feasibility based on pattern match and requirements complexity.
        
        Args:
            match: Pattern matching result
            requirements: User requirements
            
        Returns:
            Feasibility assessment: "Yes", "Partial", or "No"
        """
        # Start with pattern's base feasibility
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
                return "No"
            elif complexity_score >= 3 or risk_score >= 3 or match_quality < 0.4:
                return "Partial"
            else:
                return "Yes"
        elif base_feasibility in ["Partially Automatable", "Partial"]:
            if complexity_score >= 4 or risk_score >= 3:
                return "No"
            elif match_quality < 0.3:
                return "No"
            else:
                return "Partial"
        else:  # Not Automatable or No
            if match_quality > 0.7 and complexity_score <= 2 and risk_score <= 1:
                return "Partial"
            else:
                return "No"
    
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
        # Start with pattern match confidence
        base_confidence = match.blended_score
        
        # Adjust based on feasibility determination
        feasibility_multiplier = {
            "Yes": 1.0,
            "Partial": 0.7,
            "No": 0.3
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
    
    def _suggest_tech_stack(self, match: MatchResult, requirements: Dict[str, Any]) -> List[str]:
        """Suggest technology stack based on pattern and requirements.
        
        Args:
            match: Pattern matching result
            requirements: User requirements
            
        Returns:
            List of recommended technologies
        """
        # Start with pattern's base tech stack
        base_tech_stack = match.tech_stack.copy()
        
        # Add technologies based on requirements
        additional_tech = []
        
        # Add based on integrations
        integrations = requirements.get("integrations", [])
        for integration in integrations:
            if "database" in integration.lower():
                if "PostgreSQL" not in base_tech_stack and "SQLAlchemy" not in base_tech_stack:
                    additional_tech.append("SQLAlchemy")
            elif "api" in integration.lower() or "rest" in integration.lower():
                if "httpx" not in base_tech_stack and "requests" not in base_tech_stack:
                    additional_tech.append("httpx")
            elif "queue" in integration.lower() or "message" in integration.lower():
                if "Celery" not in base_tech_stack and "RabbitMQ" not in base_tech_stack:
                    additional_tech.append("Celery")
        
        # Add based on volume requirements
        volume = requirements.get("volume", {})
        daily_volume = volume.get("daily", 0)
        if daily_volume > 10000:
            if "Redis" not in base_tech_stack:
                additional_tech.append("Redis")
            if "Docker" not in base_tech_stack:
                additional_tech.append("Docker")
        
        # Add based on compliance requirements
        compliance = requirements.get("compliance", [])
        if isinstance(compliance, str):
            compliance = [compliance]
        
        if any(comp in ["GDPR", "HIPAA"] for comp in compliance):
            if "cryptography" not in base_tech_stack:
                additional_tech.append("cryptography")
        
        # Combine and deduplicate
        combined_tech_stack = base_tech_stack + additional_tech
        
        # Remove duplicates while preserving order
        seen = set()
        result = []
        for tech in combined_tech_stack:
            if tech not in seen:
                seen.add(tech)
                result.append(tech)
        
        return result
    
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
        reasoning_parts = []
        
        # Pattern match quality
        if match.blended_score > 0.8:
            reasoning_parts.append(f"Excellent pattern match ({match.blended_score:.0%}) with '{match.pattern_name}'")
        elif match.blended_score > 0.6:
            reasoning_parts.append(f"Good pattern match ({match.blended_score:.0%}) with '{match.pattern_name}'")
        else:
            reasoning_parts.append(f"Moderate pattern match ({match.blended_score:.0%}) with '{match.pattern_name}'")
        
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
                
        elif feasibility == "Partial":
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
    
    def _should_create_new_pattern(self, matches: List[MatchResult], requirements: Dict[str, Any]) -> bool:
        """Determine if a new pattern should be created.
        
        Args:
            matches: Existing pattern matches
            requirements: User requirements
            
        Returns:
            True if a new pattern should be created
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
            best_match = matches[0]
            if best_match.blended_score < 0.7 and domain not in ["general", "automation"]:
                app_logger.info(f"Domain-specific requirement ({domain}) with mediocre match - will create new pattern")
                return True
        
        # Don't create new pattern if we have good existing matches
        app_logger.info(f"Found adequate existing matches (best: {best_match_score:.3f}) - will use existing patterns")
        return False