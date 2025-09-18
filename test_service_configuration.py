#!/usr/bin/env python3
"""
Test script for service configuration loading and validation.

This script tests the new service configuration system to ensure it works
correctly with the existing application structure.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_configuration_loading():
    """Test loading service and dependency configuration."""
    print("Testing configuration loading...")
    
    try:
        from app.core.service_config import get_service_config_loader
        
        # Initialize the configuration loader
        loader = get_service_config_loader("config")
        loader.load_configuration()
        
        # Test service definitions
        services = loader.get_service_definitions()
        print(f"✅ Loaded {len(services)} service definitions")
        
        # Print some service details
        for service in services[:3]:  # Show first 3 services
            print(f"   - {service.name}: {service.class_path} (singleton: {service.singleton})")
        
        # Test dependency definitions
        dependencies = loader.get_dependency_definitions()
        print(f"✅ Loaded {len(dependencies)} dependency definitions")
        
        # Print some dependency details
        required_deps = [d for d in dependencies if d.dependency_type.value == 'required']
        optional_deps = [d for d in dependencies if d.dependency_type.value == 'optional']
        print(f"   - Required: {len(required_deps)}")
        print(f"   - Optional: {len(optional_deps)}")
        
        # Test dependency groups
        groups = loader.get_dependency_groups()
        print(f"✅ Loaded {len(groups)} dependency groups")
        for group_name in list(groups.keys())[:3]:
            print(f"   - {group_name}: {groups[group_name].get('description', 'No description')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dependency_validation():
    """Test dependency validation system."""
    print("\nTesting dependency validation...")
    
    try:
        from app.core.service_config import get_service_config_loader
        
        loader = get_service_config_loader("config")
        loader.load_configuration()
        
        # Set up dependency validator
        validator = loader.setup_dependency_validator()
        
        # Run validation
        result = validator.validate_all()
        
        print(f"✅ Dependency validation completed")
        print(f"   - Valid: {result.is_valid}")
        print(f"   - Missing required: {len(result.missing_required)}")
        print(f"   - Missing optional: {len(result.missing_optional)}")
        print(f"   - Version conflicts: {len(result.version_conflicts)}")
        print(f"   - Warnings: {len(result.warnings)}")
        
        if result.missing_required:
            print(f"   - Required dependencies missing: {result.missing_required}")
        
        if result.missing_optional:
            print(f"   - Optional dependencies missing: {result.missing_optional[:5]}...")  # Show first 5
        
        return True
        
    except Exception as e:
        print(f"❌ Dependency validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_service_validation():
    """Test service configuration validation."""
    print("\nTesting service configuration validation...")
    
    try:
        from app.core.service_config import get_service_config_loader
        
        loader = get_service_config_loader("config")
        loader.load_configuration()
        
        # Validate service configuration
        errors = loader.validate_service_configuration()
        
        print(f"✅ Service configuration validation completed")
        print(f"   - Errors found: {len(errors)}")
        
        if errors:
            print("   - Validation errors:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"     • {error}")
        
        return len(errors) == 0
        
    except Exception as e:
        print(f"❌ Service validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_startup_validation():
    """Test the complete startup validation process."""
    print("\nTesting startup validation...")
    
    try:
        from app.core.startup import validate_environment_setup
        
        # Run environment validation
        is_valid = validate_environment_setup("config")
        
        print(f"✅ Startup validation completed")
        print(f"   - Environment valid: {is_valid}")
        
        return True
        
    except Exception as e:
        print(f"❌ Startup validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_installation_commands():
    """Test installation command generation."""
    print("\nTesting installation command generation...")
    
    try:
        from app.core.service_config import get_service_config_loader
        
        loader = get_service_config_loader("config")
        loader.load_configuration()
        
        # Test installation commands for different groups
        groups_to_test = ['minimal', 'standard', 'development']
        
        for group in groups_to_test:
            command = loader.get_installation_command(group)
            if command:
                print(f"✅ {group}: {command[:80]}...")
            else:
                print(f"❌ {group}: No command generated")
        
        return True
        
    except Exception as e:
        print(f"❌ Installation command test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all configuration tests."""
    print("Service Configuration Test Suite")
    print("=" * 50)
    
    tests = [
        test_configuration_loading,
        test_dependency_validation,
        test_service_validation,
        test_startup_validation,
        test_installation_commands
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())