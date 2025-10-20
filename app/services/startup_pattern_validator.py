"""Startup service to validate pattern names when the application starts."""

from pathlib import Path
from app.services.pattern_name_validator import PatternNameValidator
from app.utils.imports import require_service


class StartupPatternValidator:
    """Service that validates pattern names on application startup."""
    
    def __init__(self):
        """Initialize the startup validator."""
        self.logger = require_service("logger", context="StartupPatternValidator")
    
    async def run_startup_validation(self, pattern_library_path: Path) -> bool:
        """Run pattern name validation on startup.
        
        Args:
            pattern_library_path: Path to pattern library directory
            
        Returns:
            True if validation completed successfully, False otherwise
        """
        try:
            self.logger.info("Starting pattern name validation on application startup...")
            
            validator = PatternNameValidator(pattern_library_path)
            results = await validator.validate_all_patterns()
            
            # Log results
            if results['patterns_fixed'] > 0:
                self.logger.info(
                    f"✅ Startup validation complete: Fixed {results['patterns_fixed']} duplicate pattern names"
                )
                
                # Log details of fixed patterns
                for fixed in results['fixed_patterns']:
                    self.logger.info(
                        f"   📝 {fixed['file']}: '{fixed['old_name']}' → '{fixed['new_name']}'"
                    )
            else:
                self.logger.info("✅ Startup validation complete: All pattern names are unique")
            
            if results['errors']:
                self.logger.warning(f"⚠️  Validation completed with {len(results['errors'])} errors:")
                for error in results['errors']:
                    self.logger.warning(f"   ❌ {error}")
            
            return len(results['errors']) == 0
            
        except Exception as e:
            self.logger.error(f"❌ Startup pattern validation failed: {e}")
            return False


# Global instance for easy access
startup_validator = StartupPatternValidator()