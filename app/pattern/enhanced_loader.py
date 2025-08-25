"""Enhanced pattern loader that supports rich technical details with agentic capabilities."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import jsonschema

from app.utils.logger import app_logger
from app.security.pattern_sanitizer import PatternSanitizer


class EnhancedPatternValidationError(Exception):
    """Raised when enhanced pattern validation fails."""
    pass


class EnhancedPatternLoader:
    """Enhanced pattern loader supporting traditional, agentic, and enhanced patterns."""
    
    def __init__(self, pattern_library_path: str):
        self.pattern_library_path = Path(pattern_library_path)
        self.traditional_schema = self._load_traditional_schema()
        self.agentic_schema = self._load_agentic_schema()
        self.enhanced_schema = self._load_enhanced_schema()
        self._patterns_cache: Optional[List[Dict[str, Any]]] = None
        self.pattern_sanitizer = PatternSanitizer()
    
    def _load_traditional_schema(self) -> Dict[str, Any]:
        """Load the traditional pattern JSON schema."""
        schema_path = Path(__file__).parent / "schema.json"
        try:
            with open(schema_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load traditional pattern schema: {e}")
    
    def _load_agentic_schema(self) -> Dict[str, Any]:
        """Load the agentic pattern JSON schema."""
        try:
            # Try to use dynamic schema loader first
            from app.pattern.dynamic_schema_loader import dynamic_schema_loader
            dynamic_schema = dynamic_schema_loader.generate_dynamic_schema()
            if dynamic_schema:
                app_logger.info("Using dynamic agentic schema with configurable enums")
                return dynamic_schema
        except Exception as e:
            app_logger.warning(f"Failed to load dynamic agentic schema, falling back to static: {e}")
        
        # Fallback to static schema
        agentic_schema_path = Path(__file__).parent / "agentic_schema.json"
        try:
            with open(agentic_schema_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            app_logger.warning(f"Failed to load agentic schema: {e}")
            return self.traditional_schema
    
    def _load_enhanced_schema(self) -> Dict[str, Any]:
        """Load the enhanced pattern JSON schema."""
        enhanced_schema_path = Path(__file__).parent / "enhanced_schema.json"
        try:
            with open(enhanced_schema_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            app_logger.warning(f"Failed to load enhanced schema, falling back to agentic: {e}")
            return self.agentic_schema
    
    def _determine_pattern_type(self, pattern: Dict[str, Any]) -> str:
        """Determine the pattern type based on pattern_id and content."""
        pattern_id = pattern.get("pattern_id", "")
        
        if pattern_id.startswith("EPAT-"):
            return "enhanced"
        elif pattern_id.startswith("APAT-"):
            return "agentic"
        elif pattern_id.startswith("PAT-"):
            # Check if it has agentic capabilities
            agentic_keys = ["autonomy_level", "reasoning_types", "decision_boundaries", "agent_architecture"]
            if any(key in pattern for key in agentic_keys):
                return "enhanced"  # Traditional pattern with agentic features
            return "traditional"
        else:
            app_logger.warning(f"Unknown pattern ID format: {pattern_id}")
            return "traditional"  # Default to traditional for unknown formats
    
    def _get_schema_for_pattern(self, pattern: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """Get the appropriate schema for a pattern."""
        pattern_type = self._determine_pattern_type(pattern)
        
        if pattern_type == "enhanced":
            return self.enhanced_schema, "enhanced"
        elif pattern_type == "agentic":
            return self.agentic_schema, "agentic"
        elif pattern_type == "traditional":
            return self.traditional_schema, "traditional"
        else:
            # Default to enhanced schema for unknown types
            return self.enhanced_schema, "enhanced"
    
    def _validate_pattern(self, pattern: Dict[str, Any]) -> None:
        """Validate a pattern against the appropriate schema."""
        pattern_id = pattern.get("pattern_id", "")
        schema_to_use, schema_type = self._get_schema_for_pattern(pattern)
        
        try:
            jsonschema.validate(pattern, schema_to_use)
            app_logger.debug(f"Pattern {pattern_id} validated successfully using {schema_type} schema")
        except jsonschema.ValidationError as e:
            raise EnhancedPatternValidationError(f"Pattern validation failed ({schema_type} schema): {e.message}")
        except Exception as e:
            raise EnhancedPatternValidationError(f"Pattern validation error ({schema_type} schema): {e}")
    
    def _enhance_pattern_metadata(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Add metadata about pattern capabilities and structure."""
        enhanced_pattern = pattern.copy()
        
        # Add pattern type metadata
        pattern_type = self._determine_pattern_type(pattern)
        enhanced_pattern["_pattern_type"] = pattern_type
        
        # Add capability flags
        capabilities = {
            "has_agentic_features": any(key in pattern for key in ["autonomy_level", "reasoning_types", "decision_boundaries"]),
            "has_detailed_tech_stack": isinstance(pattern.get("tech_stack"), dict),
            "has_structured_requirements": isinstance(pattern.get("input_requirements"), dict),
            "has_implementation_guidance": "implementation_guidance" in pattern,
            "has_detailed_effort_breakdown": isinstance(pattern.get("effort_breakdown"), dict),
            "has_workflow_automation": "workflow_automation" in pattern
        }
        enhanced_pattern["_capabilities"] = capabilities
        
        # Add complexity scoring
        complexity_score = self._calculate_complexity_score(pattern)
        enhanced_pattern["_complexity_score"] = complexity_score
        
        return enhanced_pattern
    
    def _calculate_complexity_score(self, pattern: Dict[str, Any]) -> float:
        """Calculate a numerical complexity score based on pattern features."""
        score = 0.0
        
        # Base complexity from enum
        complexity_map = {"Low": 0.2, "Medium": 0.5, "High": 0.8, "Very High": 1.0}
        score += complexity_map.get(pattern.get("complexity", "Medium"), 0.5)
        
        # Tech stack complexity
        tech_stack = pattern.get("tech_stack", [])
        if isinstance(tech_stack, dict):
            score += len(tech_stack) * 0.05  # More categories = more complex
        else:
            score += len(tech_stack) * 0.02  # Simple array
        
        # Pattern type complexity
        pattern_types = pattern.get("pattern_type", [])
        score += len(pattern_types) * 0.03
        
        # Agentic complexity
        if pattern.get("autonomy_level", 0) > 0.8:
            score += 0.2  # High autonomy adds complexity
        
        reasoning_types = pattern.get("reasoning_types", [])
        score += len(reasoning_types) * 0.02
        
        # Cap at 1.0
        return min(score, 1.0)
    
    def load_patterns(self) -> List[Dict[str, Any]]:
        """Load all patterns from the library directory with enhancements."""
        if self._patterns_cache is not None:
            return self._patterns_cache
        
        patterns = []
        
        if not self.pattern_library_path.exists():
            app_logger.warning(f"Pattern library path does not exist: {self.pattern_library_path}")
            self._patterns_cache = patterns
            return patterns
        
        for pattern_file in self.pattern_library_path.glob("*.json"):
            # Skip deleted patterns
            if pattern_file.name.startswith('.deleted_'):
                app_logger.debug(f"Skipping deleted pattern file: {pattern_file.name}")
                continue
            
            # Only load pattern files
            if not (pattern_file.name.startswith('PAT-') or 
                   pattern_file.name.startswith('APAT-') or 
                   pattern_file.name.startswith('EPAT-')):
                app_logger.debug(f"Skipping non-pattern file: {pattern_file.name}")
                continue
            
            try:
                with open(pattern_file, 'r') as f:
                    pattern_data = json.load(f)
                
                # Validate pattern
                self._validate_pattern(pattern_data)
                
                # Enhance pattern with metadata
                enhanced_pattern = self._enhance_pattern_metadata(pattern_data)
                patterns.append(enhanced_pattern)
                
                app_logger.debug(f"Loaded pattern: {pattern_data.get('pattern_id', 'unknown')} "
                                f"(type: {enhanced_pattern.get('_pattern_type', 'unknown')})")
                
            except json.JSONDecodeError as e:
                app_logger.error(f"Invalid JSON in pattern file {pattern_file}: {e}")
                continue
            except EnhancedPatternValidationError as e:
                app_logger.error(f"Pattern validation failed for {pattern_file}: {e}")
                continue
            except Exception as e:
                app_logger.error(f"Error loading pattern from {pattern_file}: {e}")
                continue
        
        app_logger.info(f"Loaded {len(patterns)} patterns from library")
        
        # Sanitize patterns
        clean_patterns = self.pattern_sanitizer.validate_existing_patterns(patterns)
        
        self._patterns_cache = clean_patterns
        return clean_patterns
    
    def get_pattern_by_id(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific pattern by its ID."""
        patterns = self.load_patterns()
        for pattern in patterns:
            if pattern.get("pattern_id") == pattern_id:
                return pattern
        return None
    
    def get_patterns_by_capability(self, capability: str) -> List[Dict[str, Any]]:
        """Get patterns that have a specific capability."""
        patterns = self.load_patterns()
        return [p for p in patterns if p.get("_capabilities", {}).get(capability, False)]
    
    def get_agentic_patterns(self) -> List[Dict[str, Any]]:
        """Get all patterns with agentic capabilities."""
        return self.get_patterns_by_capability("has_agentic_features")
    
    def get_enhanced_patterns(self) -> List[Dict[str, Any]]:
        """Get patterns with enhanced technical details."""
        patterns = self.load_patterns()
        return [p for p in patterns if p.get("_pattern_type") in ["enhanced", "agentic"]]
    
    def get_patterns_by_complexity_score(self, min_score: float = 0.0, max_score: float = 1.0) -> List[Dict[str, Any]]:
        """Get patterns within a complexity score range."""
        patterns = self.load_patterns()
        return [p for p in patterns 
                if min_score <= p.get("_complexity_score", 0.5) <= max_score]
    
    def save_enhanced_pattern(self, pattern: Dict[str, Any]) -> Tuple[bool, str]:
        """Save an enhanced pattern with validation and metadata."""
        # Remove metadata fields before saving
        clean_pattern = {k: v for k, v in pattern.items() if not k.startswith("_")}
        
        # Sanitize pattern before storage
        should_store, sanitized_pattern, reason = self.pattern_sanitizer.sanitize_pattern_for_storage(clean_pattern)
        
        if not should_store:
            app_logger.error(f"Enhanced pattern storage blocked: {reason}")
            return False, reason
        
        try:
            # Validate sanitized pattern
            self._validate_pattern(sanitized_pattern)
            
            # Save to file
            pattern_id = sanitized_pattern.get('pattern_id', 'unknown')
            file_path = self.pattern_library_path / f"{pattern_id}.json"
            
            with open(file_path, 'w') as f:
                json.dump(sanitized_pattern, f, indent=2)
            
            # Clear cache to force reload
            self.refresh_cache()
            
            app_logger.info(f"Enhanced pattern saved successfully: {pattern_id}")
            return True, f"Enhanced pattern {pattern_id} saved successfully"
            
        except Exception as e:
            app_logger.error(f"Failed to save enhanced pattern: {e}")
            return False, f"Failed to save enhanced pattern: {e}"
    
    def refresh_cache(self) -> None:
        """Clear the pattern cache to force reload."""
        self._patterns_cache = None
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get statistics about the pattern library."""
        patterns = self.load_patterns()
        
        stats = {
            "total_patterns": len(patterns),
            "by_type": {},
            "by_complexity": {},
            "capabilities": {},
            "average_complexity_score": 0.0
        }
        
        # Count by pattern type
        for pattern in patterns:
            pattern_type = pattern.get("_pattern_type", "unknown")
            stats["by_type"][pattern_type] = stats["by_type"].get(pattern_type, 0) + 1
            
            complexity = pattern.get("complexity", "Medium")
            stats["by_complexity"][complexity] = stats["by_complexity"].get(complexity, 0) + 1
        
        # Count capabilities
        capability_keys = ["has_agentic_features", "has_detailed_tech_stack", "has_structured_requirements", 
                          "has_implementation_guidance", "has_detailed_effort_breakdown", "has_workflow_automation"]
        
        for capability in capability_keys:
            count = len(self.get_patterns_by_capability(capability))
            stats["capabilities"][capability] = count
        
        # Calculate average complexity score
        if patterns:
            total_score = sum(p.get("_complexity_score", 0.5) for p in patterns)
            stats["average_complexity_score"] = total_score / len(patterns)
        
        return stats