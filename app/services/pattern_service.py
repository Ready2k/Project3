"""Pattern service for managing patterns."""

from typing import Dict, Any, List, Optional
import json
from pathlib import Path


class PatternService:
    """Service for pattern management operations."""
    
    def __init__(self):
        self.patterns_dir = Path("data/patterns")
        self.patterns_dir.mkdir(parents=True, exist_ok=True)
    
    def get_all_patterns(self) -> List[Dict[str, Any]]:
        """Get all patterns from the patterns directory."""
        patterns = []
        
        try:
            for pattern_file in self.patterns_dir.glob("*.json"):
                try:
                    with open(pattern_file, 'r') as f:
                        pattern = json.load(f)
                        patterns.append(pattern)
                except Exception as e:
                    print(f"Error loading pattern {pattern_file.name}: {e}")
            
            return patterns
        
        except Exception as e:
            print(f"Error loading patterns: {e}")
            return []
    
    def get_pattern_by_id(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific pattern by ID."""
        pattern_file = self.patterns_dir / f"{pattern_id}.json"
        
        if pattern_file.exists():
            try:
                with open(pattern_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading pattern {pattern_id}: {e}")
        
        return None
    
    def save_pattern(self, pattern: Dict[str, Any]) -> bool:
        """Save a pattern to the patterns directory."""
        try:
            pattern_id = pattern.get('pattern_id', 'unknown')
            pattern_file = self.patterns_dir / f"{pattern_id}.json"
            
            with open(pattern_file, 'w') as f:
                json.dump(pattern, f, indent=2)
            
            return True
        
        except Exception as e:
            print(f"Error saving pattern: {e}")
            return False
    
    def delete_pattern(self, pattern_id: str) -> bool:
        """Delete a pattern by ID."""
        try:
            pattern_file = self.patterns_dir / f"{pattern_id}.json"
            
            if pattern_file.exists():
                pattern_file.unlink()
                return True
            
            return False
        
        except Exception as e:
            print(f"Error deleting pattern {pattern_id}: {e}")
            return False