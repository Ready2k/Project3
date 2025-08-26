#!/usr/bin/env python3
"""
Debug script to test SSL verification issue with Jira integration.
This script will help identify where SSL verification is still being enforced.
"""

import asyncio
import sys
from app.config import JiraConfig, JiraAuthType
from app.services.jira import JiraService

async def test_ssl_configuration():
    """Test SSL configuration propagation through all Jira components."""
    
    print("🔍 Testing SSL Configuration Propagation")
    print("=" * 60)
    
    # Create a test configuration with SSL verification disabled
    config = JiraConfig(
        base_url="https://your-jira-instance.com",  # Replace with your actual URL
        auth_type=JiraAuthType.API_TOKEN,
        email="test@example.com",
        api_token="test-token",
        verify_ssl=False,  # SSL verification DISABLED
        ca_cert_path=None,
        timeout=30
    )
    
    print(f"📋 Configuration: verify_ssl = {config.verify_ssl}")
    print()
    
    # Create Jira service
    jira_service = JiraService(config)
    
    # Check SSL configuration in all components
    print("🔧 Component SSL Configuration:")
    print(f"  - JiraService.ssl_handler.verify_ssl: {jira_service.ssl_handler.verify_ssl}")
    print(f"  - JiraService.ssl_handler.get_httpx_verify_config(): {jira_service.ssl_handler.get_httpx_verify_config()}")
    print(f"  - DeploymentDetector.verify_ssl: {jira_service.deployment_detector.verify_ssl}")
    print(f"  - DeploymentDetector._get_verify_config(): {jira_service.deployment_detector._get_verify_config()}")
    print(f"  - APIVersionManager.verify_ssl: {jira_service.api_version_manager.verify_ssl}")
    print(f"  - APIVersionManager._get_verify_config(): {jira_service.api_version_manager._get_verify_config()}")
    print()
    
    # Check if all components have consistent SSL configuration
    ssl_configs = [
        jira_service.ssl_handler.verify_ssl,
        jira_service.deployment_detector.verify_ssl,
        jira_service.api_version_manager.verify_ssl
    ]
    
    httpx_configs = [
        jira_service.ssl_handler.get_httpx_verify_config(),
        jira_service.deployment_detector._get_verify_config(),
        jira_service.api_version_manager._get_verify_config()
    ]
    
    print("✅ SSL Configuration Consistency Check:")
    if all(ssl == False for ssl in ssl_configs):
        print("  ✅ All components have SSL verification disabled")
    else:
        print("  ❌ SSL configuration is inconsistent across components!")
        print(f"     SSL configs: {ssl_configs}")
    
    if all(httpx == False for httpx in httpx_configs):
        print("  ✅ All components will use httpx with SSL verification disabled")
    else:
        print("  ❌ httpx configuration is inconsistent across components!")
        print(f"     httpx configs: {httpx_configs}")
    
    print()
    
    # Test actual connection (this will show where the SSL error occurs)
    print("🌐 Testing Connection (this may show SSL errors):")
    try:
        result = await jira_service.test_connection_with_fallback()
        if result.success:
            print("  ✅ Connection successful!")
        else:
            print(f"  ❌ Connection failed: {result.error_details}")
            if result.ssl_validation_result:
                print(f"     SSL validation: {result.ssl_validation_result.error_message}")
    except Exception as e:
        print(f"  ❌ Connection test failed with exception: {e}")
        if "certificate verify failed" in str(e).lower():
            print("     🔍 This is the SSL certificate verification error!")
    
    print()
    print("🔒 SSL Security Warnings:")
    warnings = jira_service.ssl_handler.get_ssl_security_warnings()
    for warning in warnings:
        print(f"  {warning}")

async def test_ticket_fetch_ssl():
    """Test SSL configuration specifically for ticket fetching (where the error occurs)."""
    
    print("\n" + "=" * 60)
    print("🎫 Testing Ticket Fetch SSL Configuration")
    print("=" * 60)
    
    # Create a test configuration with SSL verification disabled
    config = JiraConfig(
        base_url="https://your-jira-instance.com",  # Replace with your actual URL
        auth_type=JiraAuthType.API_TOKEN,
        email="test@example.com",
        api_token="test-token",
        verify_ssl=False,  # SSL verification DISABLED
        ca_cert_path=None,
        timeout=30
    )
    
    jira_service = JiraService(config)
    
    print("🔧 Testing HTTP client configuration for ticket operations...")
    
    # Test the SSL configuration that would be used for ticket fetching
    verify_config = jira_service.ssl_handler.get_httpx_verify_config()
    proxy_config = jira_service.proxy_handler.get_httpx_proxy_config()
    
    print(f"  - SSL verify config: {verify_config}")
    print(f"  - Proxy config: {proxy_config}")
    
    # Create the same client configuration that would be used in ticket fetching
    client_config = {
        "timeout": jira_service.timeout,
        "verify": verify_config,
        "proxies": proxy_config
    }
    
    print(f"  - Client config: {client_config}")
    
    if verify_config is False:
        print("  ✅ HTTP client will be created with SSL verification DISABLED")
        print("  ✅ This should resolve the 'certificate verify failed' error")
    else:
        print("  ❌ HTTP client will still verify SSL certificates")
        print("  ❌ This may still cause 'certificate verify failed' errors")

if __name__ == "__main__":
    print("🚀 SSL Configuration Debug Script")
    print("This script will help identify SSL configuration issues in Jira integration.")
    print("🔧 FIXED: Added proper SSL configuration to ticket fetching HTTP client")
    print()
    
    # Run the tests
    asyncio.run(test_ssl_configuration())
    asyncio.run(test_ticket_fetch_ssl())