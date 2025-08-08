"""Pattern matching engine with tag filtering and vector similarity."""

from dataclasses import dataclass
from typing import Any, Dict, List

from app.embeddings.index import FAISSIndex
from app.llm.base import EmbeddingProvider
from app.pattern.loader import PatternLoader
from app.utils.logger import app_logger


@dataclass
class MatchResult:
    """Result of pattern matching."""
    pattern_id: str
    pattern_name: str
    feasibility: str
    tech_stack: List[str]
    confidence: float
    tag_score: float
    vector_score: float
    blended_score: float
    rationale: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_name": self.pattern_name,
            "feasibility": self.feasibility,
            "tech_stack": self.tech_stack,
            "confidence": self.confidence,
            "tag_score": self.tag_score,
            "vector_score": self.vector_score,
            "blended_score": self.blended_score,
            "rationale": self.rationale
        }


class PatternMatcher:
    """Pattern matching engine combining tag filtering and vector similarity."""
    
    def __init__(self, 
                 pattern_loader: PatternLoader,
                 embedding_provider: EmbeddingProvider,
                 faiss_index: FAISSIndex):
        """Initialize pattern matcher.
        
        Args:
            pattern_loader: Loader for pattern library
            embedding_provider: Provider for generating embeddings
            faiss_index: FAISS index for vector similarity search
        """
        self.pattern_loader = pattern_loader
        self.embedding_provider = embedding_provider
        self.faiss_index = faiss_index
    
    def _filter_by_tags(self, requirements: Dict[str, Any], patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter patterns by tag-based criteria.
        
        Args:
            requirements: User requirements with potential tags
            patterns: List of available patterns
            
        Returns:
            List of patterns matching tag criteria with scores
        """
        matching_patterns = []
        
        req_domain = requirements.get("domain")
        req_pattern_types = requirements.get("pattern_types", [])
        
        for pattern in patterns:
            score = 0.0
            matches = 0
            total_criteria = 0
            
            # Check domain match
            if req_domain:
                total_criteria += 1
                if pattern.get("domain") == req_domain:
                    score += 1.0
                    matches += 1
            
            # Check pattern type matches
            if req_pattern_types:
                pattern_types = pattern.get("pattern_type", [])
                for req_type in req_pattern_types:
                    total_criteria += 1
                    if req_type in pattern_types:
                        score += 1.0
                        matches += 1
            
            # If no specific criteria, include all patterns with base score
            if total_criteria == 0:
                matching_patterns.append({
                    **pattern,
                    "tag_score": 0.5  # Base score for no criteria
                })
            elif matches > 0:
                # Calculate normalized score
                tag_score = score / total_criteria
                matching_patterns.append({
                    **pattern,
                    "tag_score": tag_score
                })
        
        app_logger.debug(f"Tag filtering found {len(matching_patterns)} matching patterns")
        return matching_patterns
    
    def _blend_scores(self, 
                     tag_candidates: List[Dict[str, Any]], 
                     vector_candidates: List[Dict[str, Any]],
                     pattern_confidences: Dict[str, float],
                     tag_weight: float = 0.3,
                     vector_weight: float = 0.5,
                     confidence_weight: float = 0.2) -> List[Dict[str, Any]]:
        """Blend tag and vector scores with pattern confidence.
        
        Args:
            tag_candidates: Patterns with tag scores
            vector_candidates: Patterns with vector similarity scores
            pattern_confidences: Pattern confidence scores by ID
            tag_weight: Weight for tag scores
            vector_weight: Weight for vector scores
            confidence_weight: Weight for pattern confidence
            
        Returns:
            List of patterns with blended scores
        """
        # Create lookup for vector scores
        vector_scores = {vc["pattern_id"]: vc["score"] for vc in vector_candidates}
        
        blended_results = []
        
        for tag_candidate in tag_candidates:
            pattern_id = tag_candidate["pattern_id"]
            tag_score = tag_candidate["tag_score"]
            vector_score = vector_scores.get(pattern_id, 0.0)
            confidence = pattern_confidences.get(pattern_id, 0.5)
            
            # Calculate blended score
            blended_score = (
                tag_score * tag_weight +
                vector_score * vector_weight +
                confidence * confidence_weight
            )
            
            blended_results.append({
                **tag_candidate,
                "vector_score": vector_score,
                "blended_score": blended_score
            })
        
        # Sort by blended score (descending)
        blended_results.sort(key=lambda x: x["blended_score"], reverse=True)
        
        app_logger.debug(f"Blended {len(blended_results)} pattern scores")
        return blended_results
    
    def _apply_constraints(self, 
                          candidates: List[Dict[str, Any]], 
                          patterns: List[Dict[str, Any]],
                          constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply constraints to filter out banned patterns.
        
        Args:
            candidates: Pattern candidates with scores
            patterns: Full pattern data for constraint checking
            constraints: Constraint configuration
            
        Returns:
            Filtered list of candidates
        """
        banned_tools = constraints.get("banned_tools", [])
        
        if not banned_tools:
            return candidates
        
        # Create pattern lookup
        pattern_lookup = {p["pattern_id"]: p for p in patterns}
        
        filtered_candidates = []
        
        for candidate in candidates:
            pattern_id = candidate["pattern_id"]
            pattern = pattern_lookup.get(pattern_id)
            
            if not pattern:
                continue
            
            # Check if pattern uses any banned tools
            pattern_banned_tools = pattern.get("constraints", {}).get("banned_tools", [])
            pattern_tech_stack = pattern.get("tech_stack", [])
            
            # Check if any banned tools are in pattern's constraints or tech stack
            has_banned_tool = (
                any(tool in banned_tools for tool in pattern_banned_tools) or
                any(tool in banned_tools for tool in pattern_tech_stack)
            )
            
            if not has_banned_tool:
                filtered_candidates.append(candidate)
            else:
                app_logger.debug(f"Filtered out pattern {pattern_id} due to banned tools")
        
        app_logger.debug(f"Constraint filtering left {len(filtered_candidates)} candidates")
        return filtered_candidates
    
    async def match_patterns(self, 
                           requirements: Dict[str, Any], 
                           constraints: Dict[str, Any],
                           top_k: int = 5) -> List[MatchResult]:
        """Match patterns against requirements using combined scoring.
        
        Args:
            requirements: User requirements dictionary
            constraints: Constraint configuration
            top_k: Number of top results to return
            
        Returns:
            List of matching patterns with scores
        """
        app_logger.info(f"Matching patterns for requirements with top_k={top_k}")
        
        # Load all patterns
        patterns = self.pattern_loader.load_patterns()
        
        if not patterns:
            app_logger.warning("No patterns available for matching")
            return []
        
        # 1. Fast tag filtering
        tag_candidates = self._filter_by_tags(requirements, patterns)
        
        if not tag_candidates:
            app_logger.warning("No patterns matched tag criteria")
            return []
        
        # 2. Vector similarity search
        query_text = requirements.get("description", "")
        vector_results = await self.faiss_index.search(query_text, top_k=len(patterns))
        
        # Map vector results to pattern IDs (assuming FAISS index built from pattern descriptions)
        pattern_descriptions = [p["description"] for p in patterns]
        vector_candidates = []
        
        for result in vector_results:
            result_index = result["index"]
            if result_index < len(patterns):
                pattern = patterns[result_index]
                vector_candidates.append({
                    "pattern_id": pattern["pattern_id"],
                    "score": result["score"]
                })
        
        # 3. Create pattern confidence lookup
        pattern_confidences = {p["pattern_id"]: p["confidence_score"] for p in patterns}
        
        # 4. Blend scores
        blended_candidates = self._blend_scores(tag_candidates, vector_candidates, pattern_confidences)
        
        # 5. Apply constraints
        filtered_candidates = self._apply_constraints(blended_candidates, patterns, constraints)
        
        # 6. Convert to MatchResult objects
        results = []
        pattern_lookup = {p["pattern_id"]: p for p in patterns}
        
        for candidate in filtered_candidates[:top_k]:
            pattern = pattern_lookup[candidate["pattern_id"]]
            
            # Generate rationale
            rationale = self._generate_rationale(candidate, requirements)
            
            result = MatchResult(
                pattern_id=candidate["pattern_id"],
                pattern_name=pattern["name"],
                feasibility=pattern["feasibility"],
                tech_stack=pattern["tech_stack"],
                confidence=pattern["confidence_score"],
                tag_score=candidate["tag_score"],
                vector_score=candidate["vector_score"],
                blended_score=candidate["blended_score"],
                rationale=rationale
            )
            
            results.append(result)
        
        app_logger.info(f"Found {len(results)} matching patterns")
        return results
    
    def _generate_rationale(self, candidate: Dict[str, Any], requirements: Dict[str, Any]) -> str:
        """Generate human-readable rationale for the match.
        
        Args:
            candidate: Pattern candidate with scores
            requirements: Original requirements
            
        Returns:
            Human-readable rationale string
        """
        rationale_parts = []
        
        tag_score = candidate["tag_score"]
        vector_score = candidate["vector_score"]
        blended_score = candidate["blended_score"]
        
        if tag_score > 0.7:
            rationale_parts.append("Strong tag-based match")
        elif tag_score > 0.4:
            rationale_parts.append("Moderate tag-based match")
        
        if vector_score > 0.7:
            rationale_parts.append("high semantic similarity")
        elif vector_score > 0.4:
            rationale_parts.append("moderate semantic similarity")
        
        if blended_score > 0.8:
            rationale_parts.append("excellent overall fit")
        elif blended_score > 0.6:
            rationale_parts.append("good overall fit")
        else:
            rationale_parts.append("reasonable fit")
        
        if not rationale_parts:
            return "Basic pattern match"
        
        return f"Match based on {', '.join(rationale_parts)}"