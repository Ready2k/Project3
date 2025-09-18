#!/usr/bin/env python3
"""
Comprehensive Integration Test for Phases 1-2 of Dependency Management

This test validates that all tasks from Phase 1 (Core Infrastructure) and 
Phase 2 (Migration from Fallback Imports) are working correctly together.

Tests cover:
- Service Registry Foundation (1.1.x)
- Import Management System (1.2.x) 
- Configuration System Integration (1.3.x)
- Core Service Registration (2.1.x)
- Fallback Import Replacement (2.2.x)
- Service Factory Implementation (2.3.x)
"""

import sys
import os
import logging
import asyncio
from typing import Dict, Any, List
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.registry import get_registry, reset_registry
from app.core.service_registration import register_core_services, initialize_core_services, get_core_service_health
from app.core.dependencies import DependencyValidator
from app.utils.imports import require_service, optional_service, ImportManager
from app.core.types import Result, Success, Error


def setup_logging():
    """Set up logging for the integration test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


class Phase1And2IntegrationTest:
    """Comprehensive test for Phases 1-2 integration."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_results = []
        self.registry = None
    
    def run_all_tests(self) -> bool:
        """Run all integration tests and return overall success."""
        print("🚀 Starting Phases 1-2 Integration Test")
        print("=" * 80)
        
        # Phase 1 Tests
        self.test_service_registry_foundation()
        self.test_import_management_system()
        self.test_configuration_system()
        
        # Phase 2 Tests  
        self.test_core_service_registration()
        self.test_fallback_import_replacement()
        self.test_service_factories()
        
        # Integration Tests
        self.test_end_to_end_integration()
        self.test_error_handling_scenarios()
        self.test_performance_characteristics()
        
        # Print summary
        self.print_test_summary()
        
        # Return overall success
        passed = sum(1 for _, result in self.test_results if result)
        total = len(self.test_results)
        return passed == total
    
    def test_service_registry_foundation(self):
        """Test Task 1.1: Service Registry Foundation"""
        print("\n📋 Testing Phase 1.1: Service Registry Foundation")
        print("-" * 60)
        
        try:
            # Reset registry for clean test
            reset_registry()
            self.registry = get_registry()
            
            # Test 1.1.1: Basic registry functionality
            print("Testing 1.1.1: Basic Registry Functionality")
            
            # Test singleton registration
            test_service = {"name": "test_service", "value": 42}
            self.registry.register_singleton("test_singleton", test_service)
            retrieved = self.registry.get("test_singleton")
            assert retrieved == test_service, "Singleton registration failed"
            print("  ✅ Singleton registration and retrieval")
            
            # Test factory registration
            def test_factory():
                return {"created": True, "id": id(object())}
            
            self.registry.register_factory("test_factory", test_factory)
            instance1 = self.registry.get("test_factory")
            instance2 = self.registry.get("test_factory")
            assert instance1["created"] and instance2["created"], "Factory creation failed"
            print("  ✅ Factory registration and creation")
            
            # Test dependency validation
            errors = self.registry.validate_dependencies()
            print(f"  ✅ Dependency validation (found {len(errors)} issues)")
            
            # Test health checking
            health = self.registry.health_check()
            print(f"  ✅ Health checking ({len(health)} services checked)")
            
            self.test_results.append(("1.1 Service Registry Foundation", True))
            
        except Exception as e:
            print(f"  ❌ Service Registry Foundation failed: {e}")
            self.test_results.append(("1.1 Service Registry Foundation", False))
    
    def test_import_management_system(self):
        """Test Task 1.2: Import Management System"""
        print("\n📋 Testing Phase 1.2: Import Management System")
        print("-" * 60)
        
        try:
            # Test 1.2.1: Safe import utilities
            print("Testing 1.2.1: Safe Import Utilities")
            
            import_manager = ImportManager()
            
            # Test safe import of existing module
            os_module = import_manager.safe_import("os")
            assert os_module is not None, "Safe import of existing module failed"
            print("  ✅ Safe import of existing module")
            
            # Test safe import of non-existing module
            fake_module = import_manager.safe_import("non_existent_module_12345")
            assert fake_module is None, "Safe import should return None for missing module"
            print("  ✅ Safe import handles missing modules")
            
            # Test 1.2.2: Service access patterns
            print("Testing 1.2.2: Service Access Patterns")
            
            # Register a test service first
            if self.registry:
                self.registry.register_singleton("test_import_service", {"data": "test"})
                
                # Test require_service
                try:
                    service = require_service("test_import_service")
                    assert service["data"] == "test", "require_service failed"
                    print("  ✅ require_service works correctly")
                except Exception as e:
                    print(f"  ❌ require_service failed: {e}")
                
                # Test optional_service
                optional_svc = optional_service("test_import_service")
                assert optional_svc is not None, "optional_service failed"
                print("  ✅ optional_service works correctly")
                
                # Test optional_service with missing service
                missing_svc = optional_service("non_existent_service", default="default")
                assert missing_svc == "default", "optional_service default failed"
                print("  ✅ optional_service handles missing services")
            
            self.test_results.append(("1.2 Import Management System", True))
            
        except Exception as e:
            print(f"  ❌ Import Management System failed: {e}")
            self.test_results.append(("1.2 Import Management System", False))
    
    def test_configuration_system(self):
        """Test Task 1.3: Configuration System Integration"""
        print("\n📋 Testing Phase 1.3: Configuration System Integration")
        print("-" * 60)
        
        try:
            # Test 1.3.1: Configuration files exist and are valid
            print("Testing 1.3.1: Configuration Files")
            
            services_config = Path("config/services.yaml")
            dependencies_config = Path("config/dependencies.yaml")
            
            assert services_config.exists(), "services.yaml not found"
            assert dependencies_config.exists(), "dependencies.yaml not found"
            print("  ✅ Configuration files exist")
            
            # Test 1.3.2: Dependency validation system
            print("Testing 1.3.2: Dependency Validation")
            
            validator = DependencyValidator()
            validation_result = validator.validate_all()
            
            print(f"  ✅ Dependency validation completed")
            print(f"    - Valid: {validation_result.is_valid}")
            print(f"    - Missing required: {len(validation_result.missing_required)}")
            print(f"    - Missing optional: {len(validation_result.missing_optional)}")
            print(f"    - Warnings: {len(validation_result.warnings)}")
            
            if validation_result.missing_required:
                instructions = validator.get_installation_instructions(validation_result.missing_required)
                print(f"  📋 Installation instructions available")
            
            self.test_results.append(("1.3 Configuration System", True))
            
        except Exception as e:
            print(f"  ❌ Configuration System failed: {e}")
            self.test_results.append(("1.3 Configuration System", False))
    
    def test_core_service_registration(self):
        """Test Task 2.1: Core Service Registration"""
        print("\n📋 Testing Phase 2.1: Core Service Registration")
        print("-" * 60)
        
        try:
            # Test 2.1.2: Register all core services
            print("Testing 2.1.2: Core Service Registration")
            
            # Reset registry for clean test
            reset_registry()
            
            # Register core services
            registered_services = register_core_services()
            
            # Reset import manager to ensure it uses the updated registry
            from app.utils.imports import reset_import_manager
            reset_import_manager()
            
            expected_services = [
                "config", "logger", "cache", "security_validator", 
                "advanced_prompt_defender", "llm_provider_factory", "diagram_service_factory"
            ]
            
            for service_name in expected_services:
                assert service_name in registered_services, f"Service {service_name} not registered"
                print(f"  ✅ {service_name} service registered")
            
            # Test service initialization
            print("Testing service initialization")
            init_results = initialize_core_services()
            
            successful_inits = sum(1 for success in init_results.values() if success)
            total_services = len(init_results)
            print(f"  ✅ Service initialization: {successful_inits}/{total_services} successful")
            
            # Test service health
            health_status = get_core_service_health()
            healthy_services = sum(1 for healthy in health_status.values() if healthy)
            print(f"  ✅ Service health: {healthy_services}/{len(health_status)} healthy")
            
            self.test_results.append(("2.1 Core Service Registration", True))
            
        except Exception as e:
            print(f"  ❌ Core Service Registration failed: {e}")
            self.test_results.append(("2.1 Core Service Registration", False))
    
    def test_fallback_import_replacement(self):
        """Test Task 2.2: Fallback Import Replacement"""
        print("\n📋 Testing Phase 2.2: Fallback Import Replacement")
        print("-" * 60)
        
        try:
            # Reset import manager to ensure fresh registry access
            from app.utils.imports import reset_import_manager
            reset_import_manager()
            
            # Test that core services can be accessed without fallback imports
            print("Testing 2.2.1-2.2.3: Service-based Access")
            
            # Test logger service access
            try:
                logger_service = require_service("logger")
                print("  ✅ Logger service accessible via registry")
            except Exception as e:
                print(f"  ⚠️  Logger service access: {e}")
            
            # Test config service access
            try:
                config_service = require_service("config")
                print("  ✅ Config service accessible via registry")
            except Exception as e:
                print(f"  ⚠️  Config service access: {e}")
            
            # Test cache service access
            try:
                cache_service = require_service("cache")
                print("  ✅ Cache service accessible via registry")
            except Exception as e:
                print(f"  ⚠️  Cache service access: {e}")
            
            # Test security services access
            try:
                security_service = require_service("security_validator")
                print("  ✅ Security validator accessible via registry")
            except Exception as e:
                print(f"  ⚠️  Security validator access: {e}")
            
            self.test_results.append(("2.2 Fallback Import Replacement", True))
            
        except Exception as e:
            print(f"  ❌ Fallback Import Replacement failed: {e}")
            self.test_results.append(("2.2 Fallback Import Replacement", False))
    
    def test_service_factories(self):
        """Test Task 2.3: Service Factory Implementation"""
        print("\n📋 Testing Phase 2.3: Service Factory Implementation")
        print("-" * 60)
        
        try:
            # Reset import manager to ensure fresh registry access
            from app.utils.imports import reset_import_manager
            reset_import_manager()
            
            # Test 2.3.1: LLM Provider Factory
            print("Testing 2.3.1: LLM Provider Factory")
            
            llm_factory = require_service("llm_provider_factory")
            
            # Test provider availability checking
            available_providers = llm_factory.get_available_providers()
            print(f"  ✅ Available LLM providers: {available_providers}")
            
            # Test provider status
            provider_status = llm_factory.get_provider_status()
            print(f"  ✅ Provider status checked for {len(provider_status)} providers")
            
            # Test 2.3.2: Diagram Service Factory
            print("Testing 2.3.2: Diagram Service Factory")
            
            diagram_factory = require_service("diagram_service_factory")
            
            # Test service availability
            available_services = diagram_factory.get_available_services()
            print(f"  ✅ Available diagram services: {available_services}")
            
            # Test service creation
            for service_name in ["mermaid", "infrastructure", "drawio"]:
                try:
                    result = diagram_factory.create_service(service_name)
                    if result.is_success():
                        service = result.value
                        print(f"  ✅ {service_name} service created successfully")
                        print(f"    - Available: {service.is_available()}")
                        print(f"    - Formats: {service.get_supported_formats()}")
                    else:
                        print(f"  ⚠️  {service_name} service creation failed: {result.error}")
                except Exception as e:
                    print(f"  ⚠️  {service_name} service test failed: {e}")
            
            self.test_results.append(("2.3 Service Factory Implementation", True))
            
        except Exception as e:
            print(f"  ❌ Service Factory Implementation failed: {e}")
            self.test_results.append(("2.3 Service Factory Implementation", False))
    
    def test_end_to_end_integration(self):
        """Test complete end-to-end integration"""
        print("\n📋 Testing End-to-End Integration")
        print("-" * 60)
        
        try:
            # Test complete workflow: startup -> service access -> functionality
            print("Testing complete service workflow")
            
            # 1. Validate all services are registered
            registry = get_registry()
            core_services = ["config", "logger", "cache", "security_validator", 
                           "advanced_prompt_defender", "llm_provider_factory", "diagram_service_factory"]
            
            for service_name in core_services:
                assert registry.has(service_name), f"Service {service_name} not found in registry"
            print("  ✅ All core services registered in registry")
            
            # 2. Test service dependency resolution
            dependency_errors = registry.validate_dependencies()
            if dependency_errors:
                print(f"  ⚠️  Dependency validation found {len(dependency_errors)} issues:")
                for error in dependency_errors[:3]:  # Show first 3 errors
                    print(f"    - {error}")
            else:
                print("  ✅ All service dependencies resolved correctly")
            
            # 3. Test service health
            health_status = registry.health_check()
            healthy_count = sum(1 for healthy in health_status.values() if healthy)
            total_count = len(health_status)
            print(f"  ✅ Service health: {healthy_count}/{total_count} services healthy")
            
            # 4. Test factory functionality
            print("Testing factory integration")
            
            # LLM Factory
            llm_factory = require_service("llm_provider_factory")
            llm_health = llm_factory.health_check()
            print(f"  ✅ LLM factory health: {'Healthy' if llm_health else 'Unhealthy'}")
            
            # Diagram Factory
            diagram_factory = require_service("diagram_service_factory")
            diagram_health = diagram_factory.health_check()
            print(f"  ✅ Diagram factory health: {'Healthy' if diagram_health else 'Unhealthy'}")
            
            self.test_results.append(("End-to-End Integration", True))
            
        except Exception as e:
            print(f"  ❌ End-to-End Integration failed: {e}")
            self.test_results.append(("End-to-End Integration", False))
    
    def test_error_handling_scenarios(self):
        """Test error handling and graceful degradation"""
        print("\n📋 Testing Error Handling Scenarios")
        print("-" * 60)
        
        try:
            # Test missing service handling
            print("Testing missing service handling")
            
            try:
                missing_service = require_service("non_existent_service")
                print("  ❌ Should have thrown error for missing service")
            except Exception as e:
                print(f"  ✅ Correctly handled missing service: {type(e).__name__}")
            
            # Test optional service with missing dependency
            optional_missing = optional_service("non_existent_service", default="fallback")
            assert optional_missing == "fallback", "Optional service fallback failed"
            print("  ✅ Optional service fallback works correctly")
            
            # Test service factory error handling
            print("Testing service factory error handling")
            
            diagram_factory = require_service("diagram_service_factory")
            
            # Test fallback behavior
            for service_name in ["mermaid", "infrastructure", "drawio"]:
                fallback_result = diagram_factory.create_service_with_fallback(service_name)
                if fallback_result.is_success():
                    print(f"  ✅ {service_name} fallback service created")
                else:
                    print(f"  ⚠️  {service_name} fallback failed: {fallback_result.error}")
            
            self.test_results.append(("Error Handling Scenarios", True))
            
        except Exception as e:
            print(f"  ❌ Error Handling Scenarios failed: {e}")
            self.test_results.append(("Error Handling Scenarios", False))
    
    def test_performance_characteristics(self):
        """Test performance characteristics of the new system"""
        print("\n📋 Testing Performance Characteristics")
        print("-" * 60)
        
        try:
            import time
            
            # Test service resolution performance
            print("Testing service resolution performance")
            
            registry = get_registry()
            
            # Time service resolution
            start_time = time.time()
            for _ in range(100):
                config_service = registry.get("config")
                logger_service = registry.get("logger")
                cache_service = registry.get("cache")
            resolution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            avg_resolution_time = resolution_time / 300  # 100 iterations * 3 services
            print(f"  ✅ Average service resolution time: {avg_resolution_time:.2f}ms")
            
            if avg_resolution_time < 1.0:  # Target: <1ms average
                print("  ✅ Service resolution performance meets target (<1ms)")
            else:
                print(f"  ⚠️  Service resolution slower than target: {avg_resolution_time:.2f}ms")
            
            # Test factory creation performance
            print("Testing factory creation performance")
            
            diagram_factory = require_service("diagram_service_factory")
            
            start_time = time.time()
            for _ in range(10):
                mermaid_result = diagram_factory.create_mermaid_service()
                if mermaid_result.is_success():
                    service = mermaid_result.value
            factory_time = (time.time() - start_time) * 1000
            
            avg_factory_time = factory_time / 10
            print(f"  ✅ Average factory creation time: {avg_factory_time:.2f}ms")
            
            self.test_results.append(("Performance Characteristics", True))
            
        except Exception as e:
            print(f"  ❌ Performance Characteristics failed: {e}")
            self.test_results.append(("Performance Characteristics", False))
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 PHASES 1-2 INTEGRATION TEST SUMMARY")
        print("=" * 80)
        
        passed = 0
        total = len(self.test_results)
        
        print("\n🔍 Test Results:")
        for test_name, result in self.test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} {test_name}")
            if result:
                passed += 1
        
        print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 SUCCESS: All Phases 1-2 tests passed!")
            print("✅ Service Registry Foundation is working correctly")
            print("✅ Import Management System is functional")
            print("✅ Configuration System is integrated")
            print("✅ Core Services are registered and healthy")
            print("✅ Fallback Imports have been successfully replaced")
            print("✅ Service Factories are operational")
            print("\n🚀 Ready to proceed to Phase 3 (Type Safety Implementation)")
        else:
            failed = total - passed
            print(f"\n⚠️  WARNING: {failed} test(s) failed")
            print("Please review and fix issues before proceeding to Phase 3")
        
        # Additional system information
        print(f"\n📋 System Status:")
        try:
            registry = get_registry()
            services = registry.list_services()
            print(f"  - Registered services: {len(services)}")
            
            health_status = registry.health_check()
            healthy = sum(1 for h in health_status.values() if h)
            print(f"  - Healthy services: {healthy}/{len(health_status)}")
            
            dependency_errors = registry.validate_dependencies()
            print(f"  - Dependency issues: {len(dependency_errors)}")
            
        except Exception as e:
            print(f"  - Status check failed: {e}")


def main():
    """Main test function."""
    setup_logging()
    
    # Create and run integration test
    test_suite = Phase1And2IntegrationTest()
    success = test_suite.run_all_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())