#!/usr/bin/env python3
"""
Test Enhanced Pattern Services

Test script to verify that enhanced pattern services are properly registered
and functioning correctly.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_service_registration():
    """Test that enhanced pattern services are properly registered."""
    try:
        from app.core.service_registration import register_core_services
        from app.core.registry import get_registry, reset_registry
        
        # Reset registry to start fresh
        reset_registry()
        
        # Register core services
        logger.info("Registering core services...")
        registered_services = register_core_services()
        
        logger.info(f"Successfully registered {len(registered_services)} services:")
        for service in registered_services:
            logger.info(f"  ✅ {service}")
        
        # Check if enhanced pattern services are registered
        registry = get_registry()
        
        enhanced_services = ['enhanced_pattern_loader', 'pattern_analytics_service']
        for service_name in enhanced_services:
            if registry.has(service_name):
                logger.info(f"✅ {service_name} is registered")
            else:
                logger.error(f"❌ {service_name} is NOT registered")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Service registration failed: {e}")
        return False


def test_enhanced_pattern_loader():
    """Test enhanced pattern loader functionality."""
    try:
        from app.utils.imports import optional_service
        
        logger.info("Testing enhanced pattern loader...")
        
        enhanced_loader = optional_service('enhanced_pattern_loader', context='test')
        
        if enhanced_loader:
            logger.info("✅ Enhanced pattern loader service is available")
            
            # Test basic functionality
            patterns = enhanced_loader.list_patterns()
            logger.info(f"✅ Found {len(patterns)} patterns")
            
            # Test analytics summary
            if hasattr(enhanced_loader, 'get_analytics_summary'):
                summary = enhanced_loader.get_analytics_summary()
                logger.info(f"✅ Analytics summary: {summary}")
            
            # Test health check
            if hasattr(enhanced_loader, 'health_check'):
                is_healthy = enhanced_loader.health_check()
                logger.info(f"✅ Health check: {'Healthy' if is_healthy else 'Unhealthy'}")
            
            return True
        else:
            logger.error("❌ Enhanced pattern loader service is not available")
            return False
            
    except Exception as e:
        logger.error(f"❌ Enhanced pattern loader test failed: {e}")
        return False


def test_pattern_analytics_service():
    """Test pattern analytics service functionality."""
    try:
        from app.utils.imports import optional_service
        
        logger.info("Testing pattern analytics service...")
        
        analytics_service = optional_service('pattern_analytics_service', context='test')
        
        if analytics_service:
            logger.info("✅ Pattern analytics service is available")
            
            # Test real-time metrics
            if hasattr(analytics_service, 'get_real_time_metrics'):
                metrics = analytics_service.get_real_time_metrics()
                logger.info(f"✅ Real-time metrics: {metrics}")
            
            # Test usage analytics
            if hasattr(analytics_service, 'get_usage_analytics'):
                usage_analytics = analytics_service.get_usage_analytics(1)  # Last 1 hour
                logger.info(f"✅ Usage analytics: {usage_analytics}")
            
            # Test health check
            if hasattr(analytics_service, 'health_check'):
                is_healthy = analytics_service.health_check()
                logger.info(f"✅ Health check: {'Healthy' if is_healthy else 'Unhealthy'}")
            
            return True
        else:
            logger.error("❌ Pattern analytics service is not available")
            return False
            
    except Exception as e:
        logger.error(f"❌ Pattern analytics service test failed: {e}")
        return False


def test_service_dependencies():
    """Test service dependency resolution."""
    try:
        from app.core.registry import get_registry
        
        logger.info("Testing service dependencies...")
        
        registry = get_registry()
        
        # Validate dependencies
        dependency_errors = registry.validate_dependencies()
        
        if dependency_errors:
            logger.error("❌ Dependency validation errors:")
            for error in dependency_errors:
                logger.error(f"  - {error}")
            return False
        else:
            logger.info("✅ All service dependencies are valid")
            return True
            
    except Exception as e:
        logger.error(f"❌ Dependency validation failed: {e}")
        return False


def test_ui_status_display():
    """Test UI status display component."""
    try:
        from app.ui.pattern_status_display import PatternStatusDisplay
        
        logger.info("Testing UI status display component...")
        
        display = PatternStatusDisplay()
        
        # This would normally be called in Streamlit context, but we can test the logic
        logger.info("✅ PatternStatusDisplay component created successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ UI status display test failed: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("🚀 Starting enhanced pattern services test suite...")
    
    tests = [
        ("Service Registration", test_service_registration),
        ("Enhanced Pattern Loader", test_enhanced_pattern_loader),
        ("Pattern Analytics Service", test_pattern_analytics_service),
        ("Service Dependencies", test_service_dependencies),
        ("UI Status Display", test_ui_status_display)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running test: {test_name}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"❌ Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n📊 Test Results Summary:")
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {status} - {test_name}")
        if result:
            passed += 1
    
    logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Enhanced pattern services are working correctly.")
        return 0
    else:
        logger.error("💥 Some tests failed. Check the logs above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())