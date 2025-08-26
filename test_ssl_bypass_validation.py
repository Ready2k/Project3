#!/usr/bin/env python3
"""
Test script to validate SSL bypass functionality for Jira integration.
This script tests that SSL verification can be properly disabled.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.config import JiraConfig, JiraAuthType, JiraDeploymentType
from app.services.jira import JiraService
from app.utils.logger import app_logger


async def test_ssl_bypass():
    """Test SSL bypass functionality with various configurations."""
    
    print("🧪 Testing SSL Bypass Functionality")
    print("=" * 50)
    
    # Test configurations
    test_configs = [
        {
            "name": "SSL Disabled - Self-signed Certificate",
            "config": JiraConfig(
                base_url="https://your-jira-server.com",  # Replace with your Jira URL
                auth_type=JiraAuthType.API_TOKEN,
                email="your-email@company.com",  # Replace with your email
                api_token="your-api-token",  # Replace with your token
                verify_ssl=False,  # SSL verification disabled
                timeout=30
            )
        },
        {
            "name": "SSL Disabled with Custom CA Path (should ignore CA)",
            "config": JiraConfig(
                base_url="https://your-jira-server.com",
                auth_type=JiraAuthType.API_TOKEN,
                email="your-email@company.com",
                api_token="your-api-token",
                verify_ssl=False,  # SSL verification disabled
                ca_cert_path="/nonexistent/path/cert.pem",  # Should be ignored
                timeout=30
            )
        }
    ]
    
    for test_case in test_configs:
        print(f"\n🔍 Testing: {test_case['name']}")
        print("-" * 40)
        
        try:
            # Create Jira service
            jira_service = JiraService(test_case['config'])
            
            # Test SSL handler configuration
            ssl_config = jira_service.ssl_handler.get_ssl_configuration_info()
            print(f"SSL Verification Enabled: {ssl_config['ssl_verification_enabled']}")
            print(f"Security Level: {ssl_config['security_level']}")
            
            # Test httpx verify config
            try:
                verify_config = jira_service.ssl_handler.get_httpx_verify_config()
                print(f"HTTPX Verify Config: {verify_config}")
                
                if verify_config is False:
                    print("✅ SSL verification properly disabled")
                else:
                    print("❌ SSL verification not properly disabled")
                    
            except Exception as e:
                print(f"❌ Error getting verify config: {e}")
            
            # Test connection (this will show if SSL bypass works)
            print("\n🔗 Testing connection...")
            try:
                result = await jira_service.test_connection_with_fallback()
                
                if result.success:
                    print("✅ Connection successful with SSL bypass")
                    if result.deployment_info:
                        print(f"   Deployment Type: {result.deployment_info.deployment_type.value}")
                    if result.api_version:
                        print(f"   API Version: {result.api_version}")
                else:
                    print("❌ Connection failed")
                    if result.error_details:
                        print(f"   Error: {result.error_details.get('message', 'Unknown error')}")
                    
                    # Check if it's still an SSL error
                    error_msg = result.error_details.get('message', '') if result.error_details else ''
                    if 'certificate' in error_msg.lower() or 'ssl' in error_msg.lower():
                        print("🚨 SSL error still occurring - SSL bypass may not be working properly")
                        print("   This indicates the SSL settings are not being applied correctly")
                    else:
                        print("ℹ️  Non-SSL error - SSL bypass appears to be working")
                        
            except Exception as e:
                print(f"❌ Connection test failed with exception: {e}")
                if 'certificate' in str(e).lower() or 'ssl' in str(e).lower():
                    print("🚨 SSL exception still occurring - SSL bypass not working")
                
        except Exception as e:
            print(f"❌ Test setup failed: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 SSL Bypass Testing Complete")
    print("\nIf you're still seeing SSL certificate errors:")
    print("1. Check that verify_ssl=False in your Jira configuration")
    print("2. Verify the configuration is being loaded correctly")
    print("3. Check the logs for SSL configuration messages")
    print("4. Try restarting the application after configuration changes")


async def test_environment_override():
    """Test SSL bypass via environment variables."""
    
    print("\n🌍 Testing Environment Variable Override")
    print("=" * 50)
    
    # Set environment variable to disable SSL
    os.environ['JIRA_VERIFY_SSL'] = 'false'
    
    try:
        # Create config that would normally verify SSL
        config = JiraConfig(
            base_url="https://your-jira-server.com",
            auth_type=JiraAuthType.API_TOKEN,
            email="your-email@company.com",
            api_token="your-api-token",
            verify_ssl=True,  # This should be overridden by environment variable
            timeout=30
        )
        
        # Check if environment override works
        if hasattr(config, 'verify_ssl'):
            actual_ssl_setting = config.verify_ssl
            print(f"Config SSL Setting: {actual_ssl_setting}")
            
            if not actual_ssl_setting:
                print("✅ Environment variable override working")
            else:
                print("❌ Environment variable override not working")
                print("   You may need to implement environment variable support")
        
    except Exception as e:
        print(f"❌ Environment override test failed: {e}")
    
    finally:
        # Clean up environment variable
        if 'JIRA_VERIFY_SSL' in os.environ:
            del os.environ['JIRA_VERIFY_SSL']


def print_ssl_troubleshooting_guide():
    """Print comprehensive SSL troubleshooting guide."""
    
    print("\n📋 SSL Certificate Troubleshooting Guide")
    print("=" * 50)
    
    print("\n🔧 Quick Fixes for SSL Certificate Issues:")
    print("1. Disable SSL Verification (Testing Only):")
    print("   - In Jira configuration: set verify_ssl=False")
    print("   - Environment variable: JIRA_VERIFY_SSL=false")
    print("   - ⚠️  WARNING: Only use for testing, never in production!")
    
    print("\n2. Add Custom CA Certificate:")
    print("   - Export certificate from browser (click lock icon → Certificate)")
    print("   - Save as .pem or .crt file")
    print("   - Set ca_cert_path to the file location")
    print("   - Keep verify_ssl=True")
    
    print("\n3. Common SSL Error Messages:")
    print("   - 'CERTIFICATE_VERIFY_FAILED' → Certificate validation failed")
    print("   - 'hostname mismatch' → URL doesn't match certificate")
    print("   - 'self signed certificate' → Server uses self-signed cert")
    print("   - 'certificate has expired' → Certificate is expired")
    
    print("\n4. Environment-Specific Solutions:")
    print("   - Corporate networks: May need custom CA bundle")
    print("   - Self-hosted Jira: Often uses self-signed certificates")
    print("   - Development environments: SSL bypass is acceptable")
    print("   - Production: Always use proper SSL certificates")
    
    print("\n5. Verification Steps:")
    print("   - Test URL in browser first")
    print("   - Check certificate details in browser")
    print("   - Verify network connectivity")
    print("   - Check firewall/proxy settings")


if __name__ == "__main__":
    print("🚀 Starting SSL Bypass Validation Tests")
    print("Please update the configuration with your actual Jira details before running")
    print()
    
    # Print troubleshooting guide first
    print_ssl_troubleshooting_guide()
    
    # Run the tests
    try:
        asyncio.run(test_ssl_bypass())
        asyncio.run(test_environment_override())
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✨ Test execution complete")