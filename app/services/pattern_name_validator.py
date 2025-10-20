"""Pattern name validation service that runs on startup to ensure all patterns have unique names."""

import json
from pathlib import Path
from typing import Dict, List, Any
from app.services.pattern_name_manager import PatternNameManager
from app.utils.imports import require_service


class PatternNameValidator:
    """Service to validate and fix pattern names on startup."""
    
    def __init__(self, pattern_library_path: Path):
        """Initialize the pattern name validator.
        
        Args:
            pattern_library_path: Path to pattern library directory
        """
        self.pattern_library_path = pattern_library_path
        self.name_manager = PatternNameManager(pattern_library_path)
        self.logger = require_service("logger", context="PatternNameValidator")
    
    async def validate_all_patterns(self) -> Dict[str, Any]:
        """Validate all patterns and fix any naming issues.
        
        Returns:
            Dictionary with validation results
        """
        results = {
            'total_patterns': 0,
            'duplicates_found': 0,
            'patterns_fixed': 0,
            'errors': [],
            'fixed_patterns': []
        }
        
        try:
            # Get all pattern files
            pattern_files = list(self.pattern_library_path.glob("*.json"))
            results['total_patterns'] = len(pattern_files)
            
            if not pattern_files:
                self.logger.info("No pattern files found to validate")
                return results
            
            # Track names to detect duplicates
            name_counts = {}
            patterns_by_name = {}
            
            # First pass: identify all names and duplicates
            for pattern_file in pattern_files:
                try:
                    with open(pattern_file, 'r', encoding='utf-8') as f:
                        pattern = json.load(f)
                    
                    name = pattern.get('name', '').strip()
                    if not name:
                        name = f"UNNAMED_{pattern_file.stem}"
                        
                    name_lower = name.lower()
                    
                    if name_lower not in name_counts:
                        name_counts[name_lower] = 0
                        patterns_by_name[name_lower] = []
                    
                    name_counts[name_lower] += 1
                    patterns_by_name[name_lower].append({
                        'file': pattern_file,
                        'pattern': pattern,
                        'original_name': name
                    })
                    
                except Exception as e:
                    error_msg = f"Error reading pattern file {pattern_file}: {e}"
                    self.logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            # Identify duplicates
            duplicates = {name: count for name, count in name_counts.items() if count > 1}
            results['duplicates_found'] = len(duplicates)
            
            if duplicates:
                self.logger.warning(f"Found {len(duplicates)} duplicate pattern names")
                
                # Fix duplicates
                for duplicate_name, count in duplicates.items():
                    self.logger.info(f"Fixing duplicate name '{duplicate_name}' ({count} patterns)")
                    
                    patterns_with_duplicate = patterns_by_name[duplicate_name]
                    
                    # Keep the first one as-is, rename the others
                    for i, pattern_info in enumerate(patterns_with_duplicate):
                        if i == 0:
                            continue  # Keep first one unchanged
                            
                        pattern = pattern_info['pattern']
                        pattern_file = pattern_info['file']
                        original_name = pattern_info['original_name']
                        
                        # Generate requirements-like dict for name generation
                        requirements = {
                            'description': pattern.get('description', ''),
                            'domain': pattern.get('domain', 'general')
                        }
                        
                        # Generate unique name
                        new_name = self.name_manager.generate_unique_name(
                            original_name, requirements, pattern
                        )
                        
                        # Update pattern
                        old_name = pattern['name']
                        pattern['name'] = new_name
                        
                        # Add metadata about the fix
                        if 'metadata' not in pattern:
                            pattern['metadata'] = {}
                        pattern['metadata']['name_auto_fixed'] = True
                        pattern['metadata']['original_duplicate_name'] = old_name
                        pattern['metadata']['fix_reason'] = 'duplicate_name_on_startup'
                        
                        # Save updated pattern
                        try:
                            with open(pattern_file, 'w', encoding='utf-8') as f:
                                json.dump(pattern, f, indent=2, ensure_ascii=False)
                            
                            results['patterns_fixed'] += 1
                            results['fixed_patterns'].append({
                                'file': pattern_file.name,
                                'old_name': old_name,
                                'new_name': new_name
                            })
                            
                            self.logger.info(f"Fixed pattern {pattern_file.name}: '{old_name}' → '{new_name}'")
                            
                        except Exception as e:
                            error_msg = f"Error saving fixed pattern {pattern_file}: {e}"
                            self.logger.error(error_msg)
                            results['errors'].append(error_msg)
                
                # Invalidate cache after fixes
                self.name_manager.invalidate_cache()
            
            else:
                self.logger.info("No duplicate pattern names found")
            
        except Exception as e:
            error_msg = f"Error during pattern validation: {e}"
            self.logger.error(error_msg)
            results['errors'].append(error_msg)
        
        # Log summary
        if results['patterns_fixed'] > 0:
            self.logger.info(
                f"Pattern validation complete: {results['patterns_fixed']} patterns fixed, "
                f"{results['duplicates_found']} duplicates resolved"
            )
        else:
            self.logger.info("Pattern validation complete: all pattern names are unique")
        
        return results
    
    def check_pattern_name_before_save(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Check a pattern name before saving and suggest fixes if needed.
        
        Args:
            pattern: Pattern dictionary to check
            
        Returns:
            Dictionary with check results and potentially updated pattern
        """
        name = pattern.get('name', '').strip()
        
        if not name:
            # Generate a name if missing
            requirements = {
                'description': pattern.get('description', ''),
                'domain': pattern.get('domain', 'general')
            }
            
            pattern['name'] = self.name_manager.generate_unique_name(
                'Automation Pattern', requirements, pattern
            )
            
            return {
                'modified': True,
                'reason': 'missing_name',
                'old_name': '',
                'new_name': pattern['name'],
                'pattern': pattern
            }
        
        # Check if name is unique
        if not self.name_manager.is_name_unique(name):
            requirements = {
                'description': pattern.get('description', ''),
                'domain': pattern.get('domain', 'general')
            }
            
            old_name = pattern['name']
            pattern['name'] = self.name_manager.generate_unique_name(
                name, requirements, pattern
            )
            
            return {
                'modified': True,
                'reason': 'duplicate_name',
                'old_name': old_name,
                'new_name': pattern['name'],
                'pattern': pattern
            }
        
        return {
            'modified': False,
            'reason': 'name_is_unique',
            'old_name': name,
            'new_name': name,
            'pattern': pattern
        }