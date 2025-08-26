#!/usr/bin/env python3
"""
Quick SSL Fix Script for Jira Integration
This script helps diagnose and fix SSL certificate issues with Jira.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def print_banner():
    """Print banner with SSL fix options."""
    print("🔧 Jira SSL Certificate Fix Tool")
    print("=" * 50)
    print("This tool helps fix SSL certificate issues with Jira integration.")
    print()

def quick_ssl_disable():
    """Quickly disable SSL verification via environment variable."""
    print("🚨 QUICK FIX: Disabling SSL Verification")
    print("-" * 40)
    print("This will disable SSL certificate verification for Jira connections.")
    print("⚠️  WARNING: Only use this for testing, never in production!")
    print()
    
    # Set environment variable
    os.environ['JIRA_VERIFY_SSL'] = 'false'
    
    # Create/update .env file
    env_file = Path('.env')
    env_content = []
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.readlines()
    
    # Remove existing JIRA_VERIFY_SSL lines
    env_content = [line for line in env_content if not line.startswith('JIRA_VERIFY_SSL')]
    
    # Add new setting
    env_content.append('JIRA_VERIFY_SSL=false\n')
    
    # Write back to file
    with open(env_file, 'w') as f:
        f.writelines(env_content)
    
    print("✅ SSL verification disabled in .env file")
    print("✅ Environment variable set for current session")
    print()
    print("Next steps:")
    print("1. Restart your application")
    print("2. Test Jira connection again")
    print("3. If it works, you have a certificate issue")
    print("4. For production, get proper SSL certificates instead")

def export_certificate_guide():
    """Show guide for exporting SSL certificates."""
    print("📋 Certificate Export Guide")
    print("-" * 40)
    print("To properly fix SSL issues, export the server's certificate:")
    print()
    print("Method 1 - Browser Export:")
    print("1. Open your Jira URL in a web browser")
    print("2. Click the lock icon in the address bar")
    print("3. Click 'Certificate' or 'Certificate (Valid/Invalid)'")
    print("4. Go to 'Details' tab")
    print("5. Click 'Export' or 'Copy to File'")
    print("6. Save as 'Base-64 encoded X.509 (.CER)' or PEM format")
    print("7. Save the file (e.g., jira-cert.pem)")
    print()
    print("Method 2 - OpenSSL Command:")
    print("openssl s_client -connect your-jira-server.com:443 -showcerts < /dev/null 2>/dev/null | openssl x509 -outform PEM > jira-cert.pem")
    print()
    print("Method 3 - Python Script:")
    print("python -c \"import ssl; import socket; cert=ssl.get_server_certificate(('your-jira-server.com', 443)); open('jira-cert.pem', 'w').write(cert)\"")
    print()
    print("After exporting:")
    print("1. Set ca_cert_path to the certificate file location")
    print("2. Keep verify_ssl=True")
    print("3. Test the connection")

def check_current_config():
    """Check current SSL configuration."""
    print("🔍 Current SSL Configuration")
    print("-" * 40)
    
    # Check environment variables
    verify_ssl_env = os.getenv('JIRA_VERIFY_SSL', 'not set')
    ca_cert_env = os.getenv('JIRA_CA_CERT_PATH', 'not set')
    
    print(f"JIRA_VERIFY_SSL environment variable: {verify_ssl_env}")
    print(f"JIRA_CA_CERT_PATH environment variable: {ca_cert_env}")
    
    # Check .env file
    env_file = Path('.env')
    if env_file.exists():
        print("\n.env file contents (Jira-related):")
        with open(env_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if 'JIRA' in line.upper() and ('SSL' in line.upper() or 'CERT' in line.upper()):
                    print(f"  Line {line_num}: {line.strip()}")
    else:
        print("\n.env file: Not found")
    
    # Check config.yaml
    config_file = Path('config.yaml')
    if config_file.exists():
        print("\nconfig.yaml file exists - check jira section for SSL settings")
    else:
        print("\nconfig.yaml file: Not found")

async def test_connection():
    """Test Jira connection with current settings."""
    print("🔗 Testing Jira Connection")
    print("-" * 40)
    
    try:
        from app.config import JiraConfig, JiraAuthType
        from app.services.jira import JiraService
        
        # Get configuration from user
        print("Enter your Jira connection details:")
        base_url = input("Jira Base URL (e.g., https://your-company.atlassian.net): ").strip()
        if not base_url:
            print("❌ Base URL is required")
            return
        
        email = input("Email: ").strip()
        api_token = input("API Token: ").strip()
        
        if not email or not api_token:
            print("❌ Email and API token are required")
            return
        
        # Create configuration
        config = JiraConfig(
            base_url=base_url,
            auth_type=JiraAuthType.API_TOKEN,
            email=email,
            api_token=api_token
        )
        
        print(f"\nTesting connection with SSL verification: {config.verify_ssl}")
        
        # Create service and test
        service = JiraService(config)
        result = await service.test_connection_with_fallback()
        
        if result.success:
            print("✅ Connection successful!")
            if result.deployment_info:
                print(f"   Deployment: {result.deployment_info.deployment_type.value}")
            if result.api_version:
                print(f"   API Version: {result.api_version}")
        else:
            print("❌ Connection failed")
            if result.error_details:
                error_msg = result.error_details.get('message', 'Unknown error')
                print(f"   Error: {error_msg}")
                
                # Check if it's an SSL error
                if any(keyword in error_msg.lower() for keyword in ['certificate', 'ssl', 'verify']):
                    print("\n🚨 This appears to be an SSL certificate error!")
                    print("   Recommended solutions:")
                    print("   1. Run this script with option 1 to disable SSL (testing only)")
                    print("   2. Export the server certificate and configure ca_cert_path")
                    print("   3. Contact your system administrator about SSL certificates")
            
            if result.troubleshooting_steps:
                print("\n💡 Troubleshooting steps:")
                for i, step in enumerate(result.troubleshooting_steps[:5], 1):
                    print(f"   {i}. {step}")
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        if 'certificate' in str(e).lower() or 'ssl' in str(e).lower():
            print("🚨 This is an SSL-related error")

def main():
    """Main menu for SSL fix tool."""
    print_banner()
    
    while True:
        print("Choose an option:")
        print("1. 🚨 Quick Fix - Disable SSL verification (testing only)")
        print("2. 📋 Show certificate export guide")
        print("3. 🔍 Check current SSL configuration")
        print("4. 🔗 Test Jira connection")
        print("5. ❌ Exit")
        print()
        
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == '1':
            quick_ssl_disable()
        elif choice == '2':
            export_certificate_guide()
        elif choice == '3':
            check_current_config()
        elif choice == '4':
            try:
                asyncio.run(test_connection())
            except KeyboardInterrupt:
                print("\n⏹️  Connection test cancelled")
        elif choice == '5':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-5.")
        
        print("\n" + "=" * 50)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()