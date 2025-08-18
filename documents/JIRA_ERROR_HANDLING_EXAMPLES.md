# Jira Error Handling and Troubleshooting Examples

This document provides comprehensive examples of error handling scenarios for Jira Data Center integration, including detailed error responses, troubleshooting steps, and resolution examples.

## Table of Contents

1. [Error Response Structure](#error-response-structure)
2. [Authentication Errors](#authentication-errors)
3. [Network and Connectivity Errors](#network-and-connectivity-errors)
4. [Configuration Errors](#configuration-errors)
5. [API and Version Errors](#api-and-version-errors)
6. [SSL and Certificate Errors](#ssl-and-certificate-errors)
7. [Troubleshooting Workflows](#troubleshooting-workflows)
8. [Automated Error Recovery](#automated-error-recovery)

## Error Response Structure

All Jira integration errors follow a consistent structure to provide comprehensive troubleshooting information:

```json
{
  "ok": false,
  "message": "Human-readable error description",
  "error_details": {
    "error_type": "category_of_error",
    "error_code": "HTTP_or_specific_error_code",
    "message": "Detailed error message",
    "troubleshooting_steps": [
      "Step-by-step resolution instructions"
    ],
    "documentation_links": [
      "https://relevant-documentation-urls"
    ],
    "suggested_config_changes": {
      "field": "suggested_value"
    }
  },
  "auth_methods_available": [],
  "api_version_detected": null
}
```

## Authentication Errors

### 1. Invalid Personal Access Token

**Scenario**: PAT token is incorrect, expired, or has insufficient permissions.

**Request**:
```bash
curl -X POST "http://localhost:8000/jira/test" \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "https://jira.yourcompany.com",
    "auth_type": "pat",
    "personal_access_token": "invalid-token-123"
  }'
```

**Response**:
```json
{
  "ok": false,
  "message": "Authentication failed: Invalid Personal Access Token",
  "error_details": {
    "error_type": "authentication_error",
    "error_code": "401",
    "message": "The provided Personal Access Token is invalid or expired",
    "troubleshooting_steps": [
      "Verify the PAT token is copied correctly without extra spaces",
      "Check if the token has expired in Jira Data Center",
      "Ensure the user account has necessary permissions",
      "Try regenerating the Personal Access Token",
      "Verify the token has required scopes for API access"
    ],
    "documentation_links": [
      "https://confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html",
      "https://confluence.atlassian.com/jirakb/how-to-create-a-personal-access-token-in-jira-data-center-1026032365.html"
    ],
    "suggested_config_changes": {
      "auth_type": "sso",
      "use_sso": true
    }
  },
  "auth_methods_available": ["sso", "basic"],
  "api_version_detected": null
}
```

**Resolution Steps**:
1. Log into Jira Data Center
2. Navigate to **Profile** → **Personal Access Tokens**
3. Check token status and expiration
4. Create new token if needed
5. Update configuration with new token

### 2. SSO Session Expired

**Scenario**: SSO session has expired or is not available.

**Request**:
```bash
curl -X POST "http://localhost:8000/jira/test" \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "https://jira.yourcompany.com",
    "auth_type": "sso",
    "use_sso": true
  }'
```

**Response**:
```json
{
  "ok": false,
  "message": "SSO authentication failed: No active session found",
  "error_details": {
    "error_type": "sso_error",
    "error_code": "401",
    "message": "No active SSO session detected or session has expired",
    "troubleshooting_steps": [
      "Log into Jira Data Center in your browser",
      "Ensure you're on the same network/domain as the AAA system",
      "Check if SSO is properly configured in Jira Data Center",
      "Try refreshing your browser session",
      "Use basic authentication as fallback",
      "Contact your system administrator for SSO configuration"
    ],
    "documentation_links": [
      "https://confluence.atlassian.com/enterprise/configuring-sso-with-saml-1026032365.html"
    ],
    "suggested_config_changes": {
      "auth_type": "basic",
      "username": "your-username"
    }
  },
  "auth_methods_available": ["basic", "pat"],
  "api_version_detected": null
}
```

**Automated Fallback Response**:
```json
{
  "ok": true,
  "message": "Authentication successful using fallback method",
  "deployment_info": {
    "deployment_type": "data_center",
    "version": "9.12.22"
  },
  "auth_methods_available": ["basic", "pat", "sso"],
  "api_version_detected": "3",
  "fallback_used": true,
  "fallback_method": "basic",
  "fallback_message": "SSO failed, successfully authenticated using basic authentication"
}
```

### 3. Insufficient Permissions

**Scenario**: User account lacks required permissions for API access.

**Response**:
```json
{
  "ok": false,
  "message": "Authentication failed: Insufficient permissions",
  "error_details": {
    "error_type": "authorization_error",
    "error_code": "403",
    "message": "User account does not have sufficient permissions for API access",
    "troubleshooting_steps": [
      "Contact your Jira administrator to verify user permissions",
      "Ensure user has 'Browse Projects' permission",
      "Verify user has 'View Issues' permission for required projects",
      "Check if user account is active and not locked",
      "Verify API access is enabled for the user account"
    ],
    "documentation_links": [
      "https://confluence.atlassian.com/adminjiraserver/managing-project-permissions-938847142.html",
      "https://confluence.atlassian.com/jirakb/how-to-check-user-permissions-in-jira-203394973.html"
    ],
    "suggested_config_changes": null
  },
  "auth_methods_available": [],
  "api_version_detected": null
}
```

## Network and Connectivity Errors

### 1. Connection Timeout

**Scenario**: Network timeout due to slow connection or firewall issues.

**Request**:
```bash
curl -X POST "http://localhost:8000/jira/test" \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "https://jira.yourcompany.com",
    "auth_type": "pat",
    "personal_access_token": "valid-token",
    "timeout": 5
  }'
```

**Response**:
```json
{
  "ok": false,
  "message": "Connection failed: Request timeout after 5 seconds",
  "error_details": {
    "error_type": "timeout_error",
    "error_code": "TIMEOUT",
    "message": "Connection to Jira Data Center timed out",
    "troubleshooting_steps": [
      "Increase timeout value in configuration (try 60 seconds)",
      "Check network connectivity to Jira Data Center",
      "Verify firewall rules allow access to Jira",
      "Test connection from command line: curl -I https://jira.yourcompany.com",
      "Check if proxy configuration is required",
      "Contact network administrator if issues persist"
    ],
    "documentation_links": [
      "https://confluence.atlassian.com/jirakb/unable-to-connect-to-jira-applications-due-to-network-or-firewall-issues-203394974.html"
    ],
    "suggested_config_changes": {
      "timeout": 60,
      "proxy_url": "http://proxy.yourcompany.com:8080"
    }
  },
  "auth_methods_available": [],
  "api_version_detected": null
}
```

### 2. Proxy Configuration Error

**Scenario**: Incorrect proxy configuration preventing connection.

**Response**:
```json
{
  "ok": false,
  "message": "Connection failed: Proxy authentication required",
  "error_details": {
    "error_type": "proxy_error",
    "error_code": "407",
    "message": "Proxy server requires authentication",
    "troubleshooting_steps": [
      "Verify proxy URL is correct: http://proxy.company.com:8080",
      "Add proxy authentication: http://username:password@proxy.company.com:8080",
      "Check if proxy bypass is needed for internal domains",
      "Test proxy connection: curl --proxy http://proxy.company.com:8080 -I https://jira.yourcompany.com",
      "Contact network administrator for proxy credentials",
      "Try connecting without proxy if on internal network"
    ],
    "documentation_links": [
      "https://confluence.atlassian.com/jirakb/configuring-jira-to-work-with-a-proxy-server-203394975.html"
    ],
    "suggested_config_changes": {
      "proxy_url": "http://username:password@proxy.yourcompany.com:8080"
    }
  },
  "auth_methods_available": [],
  "api_version_detected": null
}
```

### 3. DNS Resolution Error

**Scenario**: Unable to resolve Jira Data Center hostname.

**Response**:
```json
{
  "ok": false,
  "message": "Connection failed: Unable to resolve hostname",
  "error_details": {
    "error_type": "dns_error",
    "error_code": "DNS_RESOLUTION_FAILED",
    "message": "Cannot resolve hostname: jira.yourcompany.com",
    "troubleshooting_steps": [
      "Verify the hostname is correct in base_url",
      "Test DNS resolution: nslookup jira.yourcompany.com",
      "Check if VPN connection is required",
      "Verify DNS server configuration",
      "Try using IP address instead of hostname",
      "Contact network administrator for DNS configuration"
    ],
    "documentation_links": [
      "https://confluence.atlassian.com/jirakb/troubleshooting-dns-issues-203394976.html"
    ],
    "suggested_config_changes": {
      "base_url": "https://192.168.1.100:8080"
    }
  },
  "auth_methods_available": [],
  "api_version_detected": null
}
```

## Configuration Errors

### 1. Invalid Base URL Format

**Scenario**: Malformed or incorrect base URL.

**Request**:
```bash
curl -X POST "http://localhost:8000/jira/test" \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "jira.yourcompany.com",
    "auth_type": "pat",
    "personal_access_token": "valid-token"
  }'
```

**Response**:
```json
{
  "ok": false,
  "message": "Configuration validation failed: Invalid base URL format",
  "error_details": {
    "error_type": "configuration_error",
    "error_code": "INVALID_URL",
    "message": "Base URL must start with http:// or https://",
    "troubleshooting_steps": [
      "Add protocol to base URL: https://jira.yourcompany.com",
      "Ensure URL format is correct: https://domain:port/path",
      "Remove trailing slashes from URL",
      "Verify the URL is accessible in browser",
      "Check if custom port is required"
    ],
    "documentation_links": [
      "https://confluence.atlassian.com/jirakb/jira-base-url-configuration-203394977.html"
    ],
    "suggested_config_changes": {
      "base_url": "https://jira.yourcompany.com"
    }
  },
  "auth_methods_available": [],
  "api_version_detected": null
}
```

### 2. Missing Required Authentication Fields

**Scenario**: Required authentication fields are missing.

**Request**:
```bash
curl -X POST "http://localhost:8000/jira/test" \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "https://jira.yourcompany.com",
    "auth_type": "basic"
  }'
```

**Response**:
```json
{
  "ok": false,
  "message": "Authentication configuration validation failed",
  "error_details": {
    "error_type": "configuration_error",
    "error_code": "MISSING_FIELDS",
    "message": "Invalid authentication configuration",
    "troubleshooting_steps": [
      "Username is required for basic authentication",
      "Password is required for basic authentication",
      "Provide both username and password fields",
      "Consider using PAT authentication instead",
      "Review authentication requirements for selected auth type"
    ],
    "documentation_links": [
      "https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/",
      "https://confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html"
    ],
    "suggested_config_changes": {
      "auth_type": "pat",
      "personal_access_token": "your-pat-token"
    }
  },
  "auth_methods_available": [],
  "api_version_detected": null
}
```

## API and Version Errors

### 1. API Endpoint Not Found

**Scenario**: API endpoint not available (version compatibility issue).

**Response**:
```json
{
  "ok": false,
  "message": "API endpoint not found: REST API v3 not available",
  "error_details": {
    "error_type": "api_error",
    "error_code": "404",
    "message": "REST API v3 endpoint not found, falling back to v2",
    "troubleshooting_steps": [
      "System will automatically fallback to API v2",
      "Verify Jira Data Center version supports REST API",
      "Check if custom context path is configured correctly",
      "Ensure Jira Data Center is running and accessible",
      "Contact administrator if API access is restricted"
    ],
    "documentation_links": [
      "https://docs.atlassian.com/software/jira/docs/api/REST/",
      "https://confluence.atlassian.com/jirakb/jira-rest-api-version-compatibility-203394978.html"
    ],
    "suggested_config_changes": {
      "preferred_api_version": "2"
    }
  },
  "auth_methods_available": ["pat", "basic"],
  "api_version_detected": "2"
}
```

### 2. Ticket Not Found

**Scenario**: Requested Jira ticket does not exist or is not accessible.

**Request**:
```bash
curl -X POST "http://localhost:8000/jira/fetch" \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "https://jira.yourcompany.com",
    "auth_type": "pat",
    "personal_access_token": "valid-token",
    "ticket_key": "NONEXISTENT-123"
  }'
```

**Response**:
```json
{
  "ok": false,
  "message": "Ticket not found: NONEXISTENT-123",
  "error_details": {
    "error_type": "ticket_not_found",
    "error_code": "404",
    "message": "The requested ticket does not exist or you don't have permission to view it",
    "troubleshooting_steps": [
      "Verify the ticket key is correct: PROJECT-123",
      "Check if the ticket exists in Jira Data Center",
      "Ensure you have permission to view the ticket",
      "Verify the project key is correct",
      "Check if the ticket has been deleted or moved"
    ],
    "documentation_links": [
      "https://confluence.atlassian.com/jirakb/how-to-find-jira-issue-keys-203394979.html"
    ],
    "suggested_config_changes": null
  },
  "auth_methods_available": ["pat", "basic"],
  "api_version_detected": "3"
}
```

## SSL and Certificate Errors

### 1. Self-Signed Certificate Error

**Scenario**: Jira Data Center uses self-signed SSL certificate.

**Response**:
```json
{
  "ok": false,
  "message": "SSL certificate verification failed",
  "error_details": {
    "error_type": "ssl_error",
    "error_code": "CERTIFICATE_VERIFY_FAILED",
    "message": "SSL certificate verification failed - self-signed certificate",
    "troubleshooting_steps": [
      "For production: Obtain proper SSL certificate from trusted CA",
      "For development: Set verify_ssl to false (NOT recommended for production)",
      "For internal CA: Provide ca_cert_path with certificate bundle",
      "Download certificate: openssl s_client -connect jira.yourcompany.com:443",
      "Contact system administrator for proper SSL configuration"
    ],
    "documentation_links": [
      "https://confluence.atlassian.com/jirakb/ssl-certificate-issues-203394980.html",
      "https://confluence.atlassian.com/enterprise/configuring-ssl-certificates-1026032365.html"
    ],
    "suggested_config_changes": {
      "verify_ssl": false,
      "ca_cert_path": "/path/to/ca-bundle.crt"
    }
  },
  "auth_methods_available": [],
  "api_version_detected": null
}
```

### 2. Certificate Chain Error

**Scenario**: Incomplete SSL certificate chain.

**Response**:
```json
{
  "ok": false,
  "message": "SSL certificate chain verification failed",
  "error_details": {
    "error_type": "ssl_error",
    "error_code": "CERTIFICATE_CHAIN_ERROR",
    "message": "SSL certificate chain is incomplete or invalid",
    "troubleshooting_steps": [
      "Verify certificate chain includes all intermediate certificates",
      "Download complete certificate chain from Jira administrator",
      "Use ca_cert_path to specify custom certificate bundle",
      "Test certificate chain: openssl verify -CAfile ca-bundle.crt server.crt",
      "Contact system administrator to fix certificate configuration"
    ],
    "documentation_links": [
      "https://confluence.atlassian.com/jirakb/ssl-certificate-chain-issues-203394981.html"
    ],
    "suggested_config_changes": {
      "ca_cert_path": "/etc/ssl/certs/ca-certificates.crt"
    }
  },
  "auth_methods_available": [],
  "api_version_detected": null
}
```

## Troubleshooting Workflows

### Workflow 1: Connection Troubleshooting

```mermaid
flowchart TD
    A[Connection Failed] --> B{Check Base URL}
    B -->|Invalid| C[Fix URL Format]
    B -->|Valid| D{Test Network}
    D -->|Timeout| E[Check Firewall/Proxy]
    D -->|DNS Error| F[Check DNS/VPN]
    D -->|SSL Error| G[Check Certificates]
    D -->|Success| H{Test Authentication}
    H -->|401/403| I[Check Credentials]
    H -->|Success| J[Connection OK]
    
    C --> K[Retry Connection]
    E --> K
    F --> K
    G --> K
    I --> K
    K --> L{Success?}
    L -->|Yes| J
    L -->|No| M[Contact Administrator]
```

### Workflow 2: Authentication Troubleshooting

```mermaid
flowchart TD
    A[Auth Failed] --> B{Check Auth Type}
    B -->|PAT| C{Token Valid?}
    B -->|SSO| D{Session Active?}
    B -->|Basic| E{Credentials Valid?}
    
    C -->|No| F[Regenerate Token]
    C -->|Yes| G[Check Permissions]
    
    D -->|No| H[Login to Jira]
    D -->|Yes| I[Check SSO Config]
    
    E -->|No| J[Verify Username/Password]
    E -->|Yes| K[Check User Permissions]
    
    F --> L[Update Config]
    G --> M[Contact Admin]
    H --> N[Retry SSO]
    I --> M
    J --> L
    K --> M
    
    L --> O[Test Connection]
    M --> O
    N --> O
```

### Workflow 3: Network Troubleshooting

```bash
#!/bin/bash
# network-troubleshoot.sh - Comprehensive network troubleshooting

JIRA_URL="https://jira.yourcompany.com"
echo "Troubleshooting connection to $JIRA_URL"

# Step 1: Basic connectivity
echo "1. Testing basic connectivity..."
if curl -I --connect-timeout 10 "$JIRA_URL" > /dev/null 2>&1; then
    echo "✅ Basic connectivity OK"
else
    echo "❌ Basic connectivity failed"
    echo "   - Check if URL is correct"
    echo "   - Verify network connectivity"
    echo "   - Check firewall rules"
fi

# Step 2: DNS resolution
echo "2. Testing DNS resolution..."
if nslookup "$(echo $JIRA_URL | sed 's|https://||' | sed 's|/.*||')" > /dev/null 2>&1; then
    echo "✅ DNS resolution OK"
else
    echo "❌ DNS resolution failed"
    echo "   - Check DNS server configuration"
    echo "   - Verify hostname is correct"
    echo "   - Try using IP address"
fi

# Step 3: SSL certificate
echo "3. Testing SSL certificate..."
if echo | openssl s_client -connect "$(echo $JIRA_URL | sed 's|https://||' | sed 's|/.*||'):443" -servername "$(echo $JIRA_URL | sed 's|https://||' | sed 's|/.*||')" > /dev/null 2>&1; then
    echo "✅ SSL certificate OK"
else
    echo "❌ SSL certificate issues"
    echo "   - Check certificate validity"
    echo "   - Verify certificate chain"
    echo "   - Consider using ca_cert_path"
fi

# Step 4: API endpoint
echo "4. Testing API endpoint..."
if curl -I "$JIRA_URL/rest/api/3/serverInfo" > /dev/null 2>&1; then
    echo "✅ API endpoint accessible"
else
    echo "❌ API endpoint not accessible"
    echo "   - Check if Jira is running"
    echo "   - Verify context path"
    echo "   - Try API v2: /rest/api/2/serverInfo"
fi

echo "Troubleshooting complete."
```

## Automated Error Recovery

### Python Error Recovery Example

```python
import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class RecoveryAction:
    action_type: str
    config_changes: Dict[str, Any]
    retry_delay: float = 1.0
    max_retries: int = 3

class JiraErrorRecovery:
    """Automated error recovery for Jira integration."""
    
    def __init__(self):
        self.recovery_strategies = {
            "ssl_error": self._recover_ssl_error,
            "timeout_error": self._recover_timeout_error,
            "authentication_error": self._recover_auth_error,
            "api_error": self._recover_api_error
        }
    
    async def attempt_recovery(self, error_type: str, config: Dict[str, Any]) -> Optional[RecoveryAction]:
        """Attempt to recover from error automatically."""
        recovery_func = self.recovery_strategies.get(error_type)
        if recovery_func:
            return await recovery_func(config)
        return None
    
    async def _recover_ssl_error(self, config: Dict[str, Any]) -> RecoveryAction:
        """Recover from SSL certificate errors."""
        if config.get("verify_ssl", True):
            logging.warning("SSL error detected, attempting recovery with certificate validation disabled")
            return RecoveryAction(
                action_type="disable_ssl_verification",
                config_changes={"verify_ssl": False},
                retry_delay=2.0
            )
        return None
    
    async def _recover_timeout_error(self, config: Dict[str, Any]) -> RecoveryAction:
        """Recover from timeout errors."""
        current_timeout = config.get("timeout", 30)
        if current_timeout < 120:  # Don't exceed 2 minutes
            new_timeout = min(current_timeout * 2, 120)
            logging.warning(f"Timeout error detected, increasing timeout from {current_timeout}s to {new_timeout}s")
            return RecoveryAction(
                action_type="increase_timeout",
                config_changes={"timeout": new_timeout},
                retry_delay=5.0
            )
        return None
    
    async def _recover_auth_error(self, config: Dict[str, Any]) -> RecoveryAction:
        """Recover from authentication errors."""
        current_auth = config.get("auth_type", "pat")
        
        # Try fallback authentication methods
        fallback_methods = {
            "pat": "sso",
            "sso": "basic",
            "basic": None
        }
        
        fallback_method = fallback_methods.get(current_auth)
        if fallback_method:
            logging.warning(f"Auth error with {current_auth}, trying fallback to {fallback_method}")
            return RecoveryAction(
                action_type="fallback_authentication",
                config_changes={"auth_type": fallback_method},
                retry_delay=3.0
            )
        return None
    
    async def _recover_api_error(self, config: Dict[str, Any]) -> RecoveryAction:
        """Recover from API version errors."""
        current_version = config.get("api_version", "3")
        if current_version == "3":
            logging.warning("API v3 error detected, falling back to API v2")
            return RecoveryAction(
                action_type="api_version_fallback",
                config_changes={"api_version": "2"},
                retry_delay=1.0
            )
        return None

# Usage example
async def test_with_recovery():
    recovery = JiraErrorRecovery()
    config = {
        "base_url": "https://jira.yourcompany.com",
        "auth_type": "pat",
        "personal_access_token": "token",
        "verify_ssl": True,
        "timeout": 30
    }
    
    max_recovery_attempts = 3
    for attempt in range(max_recovery_attempts):
        try:
            # Attempt Jira connection
            result = await test_jira_connection(config)
            if result["ok"]:
                return result
            
            # Attempt recovery
            error_type = result.get("error_details", {}).get("error_type")
            recovery_action = await recovery.attempt_recovery(error_type, config)
            
            if recovery_action:
                logging.info(f"Attempting recovery: {recovery_action.action_type}")
                config.update(recovery_action.config_changes)
                await asyncio.sleep(recovery_action.retry_delay)
            else:
                logging.error("No recovery strategy available")
                break
                
        except Exception as e:
            logging.error(f"Recovery attempt {attempt + 1} failed: {e}")
            if attempt == max_recovery_attempts - 1:
                raise
    
    return {"ok": False, "message": "All recovery attempts failed"}
```

This comprehensive error handling documentation provides detailed examples and troubleshooting guidance for all common Jira Data Center integration scenarios.