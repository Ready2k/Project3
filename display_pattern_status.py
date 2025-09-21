#!/usr/bin/env python3
"""
Display Pattern Status

Simple script to display pattern enhancement and analytics status
in a Streamlit-like format for testing.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def display_pattern_status():
    """Display pattern status without Streamlit."""
    try:
        from app.core.service_registration import register_core_services
        from app.core.registry import get_registry, reset_registry
        from app.utils.imports import optional_service
        
        print("🔧 Pattern System Status")
        print("=" * 50)
        
        # Reset and register services
        reset_registry()
        register_core_services()
        
        # Check enhanced pattern loader
        print("\n📊 Pattern Enhancement Status:")
        enhanced_loader = optional_service('enhanced_pattern_loader', context='StatusDisplay')
        
        if enhanced_loader:
            print("✅ Pattern enhancement available: Enhanced pattern system services are registered.")
            
            # Get analytics summary
            try:
                summary = enhanced_loader.get_analytics_summary()
                if summary:
                    print(f"   • Total Patterns: {summary.get('total_patterns', 0)}")
                    print(f"   • Total Accesses: {summary.get('total_accesses', 0)}")
                    print(f"   • Cache Status: {'Enabled' if summary.get('cache_enabled', False) else 'Disabled'}")
                    print(f"   • Analytics: {'Enabled' if summary.get('analytics_enabled', False) else 'Disabled'}")
            except Exception as e:
                print(f"   ⚠️ Could not get enhancement details: {e}")
        else:
            print("❌ Pattern enhancement not available: Required services not registered.")
            print("💡 This feature requires the enhanced pattern system services to be registered.")
        
        # Check pattern analytics
        print("\n📈 Pattern Analytics Status:")
        analytics_service = optional_service('pattern_analytics_service', context='StatusDisplay')
        
        if analytics_service:
            print("✅ Pattern analytics available: Enhanced pattern analytics service is registered.")
            
            # Get real-time metrics
            try:
                metrics = analytics_service.get_real_time_metrics()
                if metrics:
                    print(f"   • Patterns Accessed: {metrics.get('total_patterns_accessed', 0)}")
                    print(f"   • Success Rate: {metrics.get('success_rate', 0.0):.1%}")
                    print(f"   • Avg Response Time: {metrics.get('average_response_time_ms', 0.0):.1f}ms")
                    last_updated = metrics.get('last_updated', 'Never')
                    if last_updated != 'Never' and len(last_updated) > 8:
                        last_updated = last_updated[-8:]  # Show just the time part
                    print(f"   • Last Updated: {last_updated}")
            except Exception as e:
                print(f"   ⚠️ Could not get analytics details: {e}")
        else:
            print("❌ Pattern analytics not available: Enhanced pattern loader service not registered.")
            print("💡 This feature requires the enhanced pattern system services to be registered.")
        
        # Service health check
        print("\n🏥 Service Health Check:")
        registry = get_registry()
        
        pattern_services = {
            'pattern_loader': 'Basic Pattern Loader',
            'enhanced_pattern_loader': 'Enhanced Pattern Loader',
            'pattern_analytics_service': 'Pattern Analytics Service'
        }
        
        for service_name, display_name in pattern_services.items():
            try:
                if registry.has(service_name):
                    service = registry.get(service_name)
                    if hasattr(service, 'health_check'):
                        is_healthy = service.health_check()
                    else:
                        is_healthy = True  # Assume healthy if no health check method
                    
                    if is_healthy:
                        print(f"✅ {display_name}: Healthy")
                    else:
                        print(f"❌ {display_name}: Unhealthy")
                else:
                    print(f"⚠️ {display_name}: Not registered")
                    
            except Exception as e:
                print(f"❌ {display_name}: Error - {str(e)}")
        
        print("\n" + "=" * 50)
        print("✅ Pattern status check complete!")
        
    except Exception as e:
        print(f"❌ Error displaying pattern status: {e}")


if __name__ == "__main__":
    display_pattern_status()