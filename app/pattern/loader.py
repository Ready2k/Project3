"""Pattern library loading and validation."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema

from app.utils.logger import app_logger
from app.security.pattern_sanitizer import PatternSanitizer


class PatternValidationError(Exception):
    """Raised when pattern validation fails."""
    pass


class PatternLoader:
    """Loads and validates patterns from the pattern library."""
    
    def __init__(self, pattern_library_path: str):
        self.pattern_library_path = Path(pattern_library_path)
        self.schema = self._load_schema()
        self.agentic_schema = self._load_agentic_schema()
        self._patterns_cache: Optional[List[Dict[str, Any]]] = None
        self.pattern_sanitizer = PatternSanitizer()
    
    def _load_schema(self) -> Dict[str, Any]:
        """Load the pattern JSON schema."""
        schema_path = Path(__file__).parent / "schema.json"
        try:
            with open(schema_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load pattern schema: {e}")
    
    def _load_agentic_schema(self) -> Dict[str, Any]:
        """Load the agentic pattern JSON schema with dynamic enum support."""
        try:
            # Try to use dynamic schema loader first
            from app.pattern.dynamic_schema_loader import dynamic_schema_loader
            dynamic_schema = dynamic_schema_loader.generate_dynamic_schema()
            if dynamic_schema:
                app_logger.info("Using dynamic schema with configurable enums")
                return dynamic_schema
        except Exception as e:
            app_logger.warning(f"Failed to load dynamic schema, falling back to static: {e}")
        
        # Fallback to static schema
        agentic_schema_path = Path(__file__).parent / "agentic_schema.json"
        try:
            with open(agentic_schema_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            app_logger.warning(f"Failed to load agentic schema, using traditional schema: {e}")
            return self.schema
    
    def _validate_pattern(self, pattern: Dict[str, Any]) -> None:
        """Validate a pattern against the appropriate schema."""
        pattern_id = pattern.get("pattern_id", "")
        
        # Use appropriate schema based on pattern type and content
        if pattern_id.startswith("APAT-"):
            # APAT patterns must use agentic schema
            schema_to_use = self.agentic_schema
            schema_type = "agentic"
            
            try:
                jsonschema.validate(pattern, schema_to_use)
                app_logger.debug(f"Pattern {pattern_id} validated successfully using {schema_type} schema")
                return
            except jsonschema.ValidationError as e:
                raise PatternValidationError(f"Pattern validation failed ({schema_type} schema): {e.message}")
            except Exception as e:
                raise PatternValidationError(f"Pattern validation error ({schema_type} schema): {e}")
                
        elif pattern_id.startswith("PAT-"):
            # For PAT patterns, try agentic schema first if it has agentic fields, then fall back to traditional
            has_agentic_fields = any(key in pattern for key in ["autonomy_level", "reasoning_types", "decision_boundaries"])
            
            if has_agentic_fields:
                # Try agentic schema first
                try:
                    jsonschema.validate(pattern, self.agentic_schema)
                    app_logger.debug(f"Pattern {pattern_id} validated successfully using agentic schema")
                    return
                except jsonschema.ValidationError as e:
                    app_logger.debug(f"Pattern {pattern_id} failed agentic validation, trying traditional schema: {e.message}")
                    # Fall through to traditional validation
                except Exception as e:
                    app_logger.debug(f"Pattern {pattern_id} agentic validation error, trying traditional schema: {e}")
                    # Fall through to traditional validation
            
            # Use traditional schema (either as fallback or primary choice)
            try:
                jsonschema.validate(pattern, self.schema)
                app_logger.debug(f"Pattern {pattern_id} validated successfully using traditional schema")
                return
            except jsonschema.ValidationError as e:
                raise PatternValidationError(f"Pattern validation failed (traditional schema): {e.message}")
            except Exception as e:
                raise PatternValidationError(f"Pattern validation error (traditional schema): {e}")
        elif pattern_id.startswith("TRAD-"):
            # TRAD patterns use traditional schema
            try:
                jsonschema.validate(pattern, self.schema)
                app_logger.debug(f"Pattern {pattern_id} validated successfully using traditional schema")
                return
            except jsonschema.ValidationError as e:
                raise PatternValidationError(f"Pattern validation failed (traditional schema): {e.message}")
            except Exception as e:
                raise PatternValidationError(f"Pattern validation error (traditional schema): {e}")
        else:
            # Unknown pattern type, use traditional schema
            try:
                jsonschema.validate(pattern, self.schema)
                app_logger.debug(f"Pattern {pattern_id} validated successfully using traditional schema")
            except jsonschema.ValidationError as e:
                raise PatternValidationError(f"Pattern validation failed (traditional schema): {e.message}")
            except Exception as e:
                raise PatternValidationError(f"Pattern validation error (traditional schema): {e}")
    
    def load_patterns(self) -> List[Dict[str, Any]]:
        """Load all patterns from the library directory."""
        if self._patterns_cache is not None:
            return self._patterns_cache
        
        patterns = []
        
        if not self.pattern_library_path.exists():
            app_logger.warning(f"Pattern library path does not exist: {self.pattern_library_path}")
            self._patterns_cache = patterns
            return patterns
        
        for pattern_file in self.pattern_library_path.glob("*.json"):
            # Skip deleted patterns (files that start with .deleted_)
            if pattern_file.name.startswith('.deleted_'):
                app_logger.debug(f"Skipping deleted pattern file: {pattern_file.name}")
                continue
            
            # Only load files that match the PAT-*, APAT-*, or TRAD-* pattern
            if not (pattern_file.name.startswith('PAT-') or 
                   pattern_file.name.startswith('APAT-') or
                   pattern_file.name.startswith('TRAD-')):
                app_logger.debug(f"Skipping non-pattern file: {pattern_file.name}")
                continue
            
            try:
                with open(pattern_file, 'r') as f:
                    pattern_data = json.load(f)
                
                # Validate pattern
                self._validate_pattern(pattern_data)
                patterns.append(pattern_data)
                
                app_logger.debug(f"Loaded pattern: {pattern_data.get('pattern_id', 'unknown')}")
                
            except json.JSONDecodeError as e:
                app_logger.error(f"Invalid JSON in pattern file {pattern_file}: {e}")
                continue
            except PatternValidationError as e:
                app_logger.error(f"Pattern validation failed for {pattern_file}: {e}")
                continue
            except Exception as e:
                app_logger.error(f"Error loading pattern from {pattern_file}: {e}")
                continue
        
        app_logger.info(f"Loaded {len(patterns)} patterns from library")
        
        # Sanitize patterns to remove any security testing patterns
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
    
    def get_patterns_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """Get all patterns for a specific domain."""
        patterns = self.load_patterns()
        return [p for p in patterns if p.get("domain") == domain]
    
    def get_patterns_by_type(self, pattern_type: str) -> List[Dict[str, Any]]:
        """Get all patterns that include a specific type."""
        patterns = self.load_patterns()
        return [p for p in patterns if pattern_type in p.get("pattern_type", [])]
    
    def get_patterns_by_feasibility(self, feasibility: str) -> List[Dict[str, Any]]:
        """Get all patterns with a specific feasibility level."""
        patterns = self.load_patterns()
        return [p for p in patterns if p.get("feasibility") == feasibility]
    
    def refresh_cache(self) -> None:
        """Clear the pattern cache to force reload."""
        self._patterns_cache = None
    
    def save_pattern(self, pattern: Dict[str, Any]) -> tuple[bool, str]:
        """Save a pattern to the library with security validation."""
        # Sanitize pattern before storage
        should_store, sanitized_pattern, reason = self.pattern_sanitizer.sanitize_pattern_for_storage(pattern)
        
        if not should_store:
            app_logger.error(f"Pattern storage blocked: {reason}")
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
            
            app_logger.info(f"Pattern saved successfully: {pattern_id}")
            return True, f"Pattern {pattern_id} saved successfully"
            
        except Exception as e:
            app_logger.error(f"Failed to save pattern: {e}")
            return False, f"Failed to save pattern: {e}"