"""Pattern library loading and validation."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema

from app.utils.logger import app_logger


class PatternValidationError(Exception):
    """Raised when pattern validation fails."""
    pass


class PatternLoader:
    """Loads and validates patterns from the pattern library."""
    
    def __init__(self, pattern_library_path: str):
        self.pattern_library_path = Path(pattern_library_path)
        self.schema = self._load_schema()
        self._patterns_cache: Optional[List[Dict[str, Any]]] = None
    
    def _load_schema(self) -> Dict[str, Any]:
        """Load the pattern JSON schema."""
        schema_path = Path(__file__).parent / "schema.json"
        try:
            with open(schema_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load pattern schema: {e}")
    
    def _validate_pattern(self, pattern: Dict[str, Any]) -> None:
        """Validate a pattern against the schema."""
        try:
            jsonschema.validate(pattern, self.schema)
        except jsonschema.ValidationError as e:
            raise PatternValidationError(f"Pattern validation failed: {e.message}")
        except Exception as e:
            raise PatternValidationError(f"Pattern validation error: {e}")
    
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
        self._patterns_cache = patterns
        return patterns
    
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