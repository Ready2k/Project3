"""
Integration Example: Service Configuration with Existing Application

This module demonstrates how the new service configuration system
integrates with the existing application startup and configuration.
"""

import logging
from typing import Dict, Any, Optional

from app.core.startup import ApplicationStartup
from app.core.registry import get_registry
from app.config import load_settings

logger = logging.getLogger(__name__)


class IntegratedApplicationStartup:
    """
    Demonstrates integration between new service configuration system
    and existing application configuration.
    """
    
    def __init__(self, config_dir: str = "config"):
        """Initialize integrated startup."""
        self.config_dir = config_dir
        self.service_startup = ApplicationStartup(config_dir)
        self.registry = get_registry()
        self.app_settings = None
    
    def initialize_application(self) -> Dict[str, Any]:
        """
        Initialize the application with both old and new configuration systems.
        
        Returns:
            Dictionary with initialization results
        """
        results = {
            'success': False,
            'service_startup': {},
            'app_settings': {},
            'integration': {}
        }
        
        try:
            logger.info("Starting integrated application initialization...")
            
            # Step 1: Load existing application settings
            logger.info("Loading existing application settings...")
            self.app_settings = load_settings()
            results['app_settings'] = {
                'loaded': True,
                'version': self.app_settings.version,
                'environment': getattr(self.app_settings, 'environment', 'unknown'),
                'provider': self.app_settings.provider,
                'model': self.app_settings.model
            }
            
            # Step 2: Run new service startup
            logger.info("Running service configuration startup...")
            service_results = self.service_startup.run_startup_sequence()
            results['service_startup'] = service_results
            
            # Step 3: Demonstrate integration
            logger.info("Demonstrating service integration...")
            integration_results = self._demonstrate_integration()
            results['integration'] = integration_results
            
            results['success'] = True
            logger.info("Integrated application initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Integrated initialization failed: {e}")
            results['error'] = str(e)
            results['error_type'] = type(e).__name__
        
        return results
    
    def _demonstrate_integration(self) -> Dict[str, Any]:
        """Demonstrate how services can be used with existing configuration."""
        integration_results = {
            'services_available': [],
            'configuration_access': {},
            'service_health': {}
        }
        
        try:
            # Show available services
            services = self.registry.list_services()
            integration_results['services_available'] = services
            logger.info(f"Available services: {services}")
            
            # Demonstrate configuration access through services
            if self.registry.has('config'):
                try:
                    config_service = self.registry.get('config')
                    # This would work if we had implemented the ConfigService
                    integration_results['configuration_access']['config_service'] = 'available'
                except Exception as e:
                    integration_results['configuration_access']['config_service'] = f'error: {e}'
            
            # Show service health
            health_status = self.registry.health_check()
            integration_results['service_health'] = health_status
            
            # Demonstrate how existing settings can be used with new services
            if self.app_settings:
                integration_results['settings_integration'] = {
                    'llm_provider': self.app_settings.provider,
                    'llm_model': self.app_settings.model,
                    'pattern_library_path': str(self.app_settings.pattern_library_path),
                    'export_path': str(self.app_settings.export_path)
                }
            
        except Exception as e:
            logger.error(f"Integration demonstration failed: {e}")
            integration_results['error'] = str(e)
        
        return integration_results
    
    def get_service_by_name(self, service_name: str) -> Optional[Any]:
        """
        Get a service instance by name (convenience method).
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            Service instance or None if not available
        """
        try:
            if self.registry.has(service_name):
                return self.registry.get(service_name)
        except Exception as e:
            logger.error(f"Failed to get service '{service_name}': {e}")
        return None
    
    def get_startup_summary(self) -> str:
        """Get a summary of the startup process."""
        if not self.service_startup.is_startup_completed():
            return "Startup has not been completed yet."
        
        return self.service_startup.get_startup_report()


def demonstrate_service_usage():
    """Demonstrate how to use the new service configuration system."""
    print("Service Configuration Integration Demo")
    print("=" * 50)
    
    try:
        # Initialize the integrated application
        app = IntegratedApplicationStartup()
        results = app.initialize_application()
        
        if results['success']:
            print("✅ Application initialization successful!")
            
            # Show service startup results
            service_results = results['service_startup']
            print(f"\n📋 Service Configuration:")
            print(f"   Environment: {service_results.get('environment', 'unknown')}")
            
            if 'services' in service_results:
                services = service_results['services']
                print(f"   Services registered: {services.get('registered_count', 0)}")
                if services.get('failed_count', 0) > 0:
                    print(f"   Services failed: {services['failed_count']}")
            
            # Show integration results
            integration = results['integration']
            print(f"\n🔧 Service Integration:")
            available_services = integration.get('services_available', [])
            print(f"   Available services: {len(available_services)}")
            for service in available_services[:5]:  # Show first 5
                print(f"     - {service}")
            
            # Show health status
            health = integration.get('service_health', {})
            healthy_count = sum(1 for status in health.values() if status)
            print(f"   Healthy services: {healthy_count}/{len(health)}")
            
            # Show settings integration
            settings_integration = integration.get('settings_integration', {})
            if settings_integration:
                print(f"\n⚙️  Settings Integration:")
                print(f"   LLM Provider: {settings_integration.get('llm_provider', 'unknown')}")
                print(f"   LLM Model: {settings_integration.get('llm_model', 'unknown')}")
            
            print(f"\n📊 Full Startup Report:")
            print(app.get_startup_summary())
            
        else:
            print("❌ Application initialization failed!")
            if 'error' in results:
                print(f"   Error: {results['error']}")
        
        return results['success']
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    """Run the integration demonstration."""
    import sys
    
    # Set up basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    success = demonstrate_service_usage()
    sys.exit(0 if success else 1)