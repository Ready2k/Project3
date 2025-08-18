# Jira Authentication Flow Documentation

This document provides detailed documentation of authentication flows for Jira Data Center integration, including sequence diagrams, error handling, and implementation examples.

## Table of Contents

1. [Authentication Overview](#authentication-overview)
2. [Authentication Methods](#authentication-methods)
3. [Authentication Flows](#authentication-flows)
4. [Fallback Mechanisms](#fallback-mechanisms)
5. [Error Handling](#error-handling)
6. [Implementation Examples](#implementation-examples)
7. [Security Considerations](#security-considerations)

## Authentication Overview

The AAA system supports multiple authentication methods for Jira Data Center, with automatic fallback capabilities to ensure reliable connectivity across different enterprise environments.

### Supported Authentication Methods

| Method | Description | Use Case | Security Level |
|--------|-------------|----------|----------------|
| **Personal Access Token (PAT)** | Token-based authentication | Recommended for Data Center | High |
| **Single Sign-On (SSO)** | Session-based authentication | Enterprise environments | High |
| **Basic Authentication** | Username/password | Fallback only | Medium |
| **API Token** | Email + token | Jira Cloud only | High |

### Authentication Priority

The system follows this authentication priority order:

1. **Configured Method**: Use the explicitly configured authentication method
2. **SSO Detection**: Attempt SSO if available and configured
3. **Fallback Chain**: Fall back to basic authentication if primary method fails
4. **User Prompting**: Prompt for credentials when needed

## Authentication Methods

### 1. Personal Access Token (PAT)

**Recommended for Jira Data Center**

Personal Access Tokens provide secure, user-specific access without exposing passwords.

#### Configuration
```json
{
  "auth_type": "pat",
  "personal_access_token": "NjE2NTc2NzI2ODc4NjY4NjE2NTc2NzI2ODc4NjY4"
}
```

#### Token Creation Process
1. Log into Jira Data Center
2. Navigate to **Profile** → **Personal Access Tokens**
3. Click **Create token**
4. Set name and expiration
5. Copy token immediately

#### Validation Process
```http
GET /rest/api/3/myself
Authorization: Bearer NjE2NTc2NzI2ODc4NjY4NjE2NTc2NzI2ODc4NjY4
```

### 2. Single Sign-On (SSO)

**For Enterprise Environments**

SSO authentication leverages existing browser sessions or Windows authentication.

#### Configuration
```json
{
  "auth_type": "sso",
  "use_sso": true,
  "sso_session_cookie": "JSESSIONID=ABC123DEF456..."
}
```

#### Session Detection
- Automatic browser session detection
- Windows credential integration
- Session cookie extraction
- Session validation

### 3. Basic Authentication

**Fallback Method Only**

Username and password authentication used as a fallback when other methods fail.

#### Configuration
```json
{
  "auth_type": "basic",
  "username": "jdoe",
  "password": "secure-password"
}
```

#### Security Features
- Session-only credential storage
- No persistent credential storage
- Secure credential prompting
- Automatic credential cleanup

### 4. API Token (Cloud Only)

**Jira Cloud Compatibility**

Email and API token authentication for Jira Cloud instances.

#### Configuration
```json
{
  "auth_type": "api_token",
  "email": "user@company.com",
  "api_token": "ATATT3xFfGF0T..."
}
```

## Authentication Flows

### Flow 1: Personal Access Token Authentication

```mermaid
sequenceDiagram
    participant Client
    participant AAA_API
    participant Auth_Manager
    participant Jira_DC
    
    Client->>AAA_API: POST /jira/test (PAT config)
    AAA_API->>AAA_API: Validate PAT configuration
    AAA_API->>Auth_Manager: Create PAT handler
    Auth_Manager->>Jira_DC: GET /rest/api/3/myself
    Note over Auth_Manager,Jira_DC: Authorization: Bearer {PAT}
    
    alt PAT Valid
        Jira_DC-->>Auth_Manager: 200 OK (User info)
        Auth_Manager->>Jira_DC: GET /rest/api/3/serverInfo
        Jira_DC-->>Auth_Manager: Server info
        Auth_Manager-->>AAA_API: Authentication success
        AAA_API-->>Client: Success response with deployment info
    else PAT Invalid
        Jira_DC-->>Auth_Manager: 401 Unauthorized
        Auth_Manager-->>AAA_API: Authentication failed
        AAA_API-->>Client: Error response with troubleshooting
    end
```

### Flow 2: SSO Authentication with Fallback

```mermaid
sequenceDiagram
    participant Client
    participant AAA_API
    participant Auth_Manager
    participant SSO_Handler
    participant Basic_Handler
    participant Jira_DC
    
    Client->>AAA_API: POST /jira/test (SSO config)
    AAA_API->>Auth_Manager: Create authentication chain
    Auth_Manager->>SSO_Handler: Attempt SSO authentication
    
    SSO_Handler->>SSO_Handler: Detect current session
    SSO_Handler->>Jira_DC: GET /rest/api/3/myself (with session)
    
    alt SSO Success
        Jira_DC-->>SSO_Handler: 200 OK (User info)
        SSO_Handler-->>Auth_Manager: SSO authentication success
        Auth_Manager-->>AAA_API: Authentication complete
        AAA_API-->>Client: Success response
    else SSO Failed
        Jira_DC-->>SSO_Handler: 401 Unauthorized
        SSO_Handler-->>Auth_Manager: SSO failed, try fallback
        Auth_Manager->>Basic_Handler: Attempt basic auth fallback
        Basic_Handler->>AAA_API: Request credentials from user
        AAA_API-->>Client: Prompt for username/password
        Client->>AAA_API: Provide credentials
        AAA_API->>Basic_Handler: Forward credentials
        Basic_Handler->>Jira_DC: GET /rest/api/3/myself (basic auth)
        
        alt Basic Auth Success
            Jira_DC-->>Basic_Handler: 200 OK (User info)
            Basic_Handler-->>Auth_Manager: Basic auth success
            Auth_Manager-->>AAA_API: Authentication complete
            AAA_API-->>Client: Success response (with fallback note)
        else Basic Auth Failed
            Jira_DC-->>Basic_Handler: 401 Unauthorized
            Basic_Handler-->>Auth_Manager: All authentication failed
            Auth_Manager-->>AAA_API: Authentication failed
            AAA_API-->>Client: Error response with troubleshooting
        end
    end
```

### Flow 3: Automatic Deployment Detection

```mermaid
sequenceDiagram
    participant AAA_API
    participant Deployment_Detector
    participant API_Version_Manager
    participant Jira_Instance
    
    AAA_API->>Deployment_Detector: Detect deployment type
    Deployment_Detector->>Deployment_Detector: Analyze base URL
    
    alt Cloud Detection
        Note over Deployment_Detector: URL contains "atlassian.net"
        Deployment_Detector->>Jira_Instance: GET /rest/api/3/serverInfo
        Jira_Instance-->>Deployment_Detector: Cloud server info
        Deployment_Detector-->>AAA_API: Deployment: Cloud
    else Data Center Detection
        Note over Deployment_Detector: Custom domain detected
        Deployment_Detector->>Jira_Instance: GET /rest/api/3/serverInfo
        Jira_Instance-->>Deployment_Detector: Data Center server info
        Deployment_Detector->>API_Version_Manager: Test API versions
        API_Version_Manager->>Jira_Instance: Test /rest/api/3/
        
        alt API v3 Available
            Jira_Instance-->>API_Version_Manager: 200 OK
            API_Version_Manager-->>Deployment_Detector: Use API v3
        else API v3 Not Available
            Jira_Instance-->>API_Version_Manager: 404 Not Found
            API_Version_Manager->>Jira_Instance: Test /rest/api/2/
            Jira_Instance-->>API_Version_Manager: 200 OK
            API_Version_Manager-->>Deployment_Detector: Use API v2
        end
        
        Deployment_Detector-->>AAA_API: Deployment: Data Center, API version
    end
```

### Flow 4: Authentication Method Discovery

```mermaid
sequenceDiagram
    participant AAA_API
    participant Auth_Manager
    participant Jira_DC
    
    AAA_API->>Auth_Manager: Discover available auth methods
    Auth_Manager->>Jira_DC: GET /rest/api/3/serverInfo
    Jira_DC-->>Auth_Manager: Server info with capabilities
    
    Auth_Manager->>Auth_Manager: Analyze server capabilities
    
    Note over Auth_Manager: Check for PAT support
    Auth_Manager->>Jira_DC: Test PAT endpoint availability
    Jira_DC-->>Auth_Manager: PAT support status
    
    Note over Auth_Manager: Check for SSO support
    Auth_Manager->>Jira_DC: Test SSO endpoints
    Jira_DC-->>Auth_Manager: SSO support status
    
    Auth_Manager-->>AAA_API: Available methods: [pat, sso, basic]
```

## Fallback Mechanisms

### Authentication Fallback Chain

The system implements a sophisticated fallback mechanism:

1. **Primary Authentication**: Attempt configured authentication method
2. **Secondary Methods**: Try alternative methods if available
3. **User Prompting**: Request additional credentials when needed
4. **Graceful Degradation**: Provide clear error messages and guidance

### Fallback Decision Matrix

| Primary Method | Fallback Options | User Prompt Required |
|----------------|------------------|---------------------|
| PAT | SSO → Basic | Yes (for basic) |
| SSO | Basic | Yes |
| Basic | None | No |
| API Token | None (Cloud only) | No |

### Implementation Example

```python
class AuthenticationManager:
    async def authenticate_with_fallback(self, config: JiraConfig) -> AuthResult:
        """Authenticate with fallback chain."""
        
        # Try primary authentication method
        primary_result = await self._try_primary_auth(config)
        if primary_result.success:
            return primary_result
        
        # Try fallback methods
        for fallback_method in self._get_fallback_methods(config.auth_type):
            fallback_result = await self._try_fallback_auth(config, fallback_method)
            if fallback_result.success:
                fallback_result.used_fallback = True
                fallback_result.fallback_method = fallback_method
                return fallback_result
        
        # All methods failed
        return AuthResult(
            success=False,
            error_message="All authentication methods failed",
            troubleshooting_steps=self._get_troubleshooting_steps(config)
        )
```

## Error Handling

### Authentication Error Types

| Error Type | Description | Resolution |
|------------|-------------|------------|
| `invalid_credentials` | Wrong username/password/token | Verify credentials |
| `expired_token` | PAT or session expired | Regenerate token |
| `insufficient_permissions` | User lacks required permissions | Check Jira permissions |
| `sso_unavailable` | SSO not configured | Use alternative method |
| `network_error` | Connection issues | Check network/proxy |
| `api_unavailable` | API endpoint not accessible | Check Jira version |

### Error Response Structure

```json
{
  "error_type": "authentication_error",
  "error_code": "401",
  "message": "Personal Access Token expired",
  "troubleshooting_steps": [
    "Check token expiration in Jira Data Center",
    "Regenerate Personal Access Token",
    "Verify token permissions and scopes"
  ],
  "documentation_links": [
    "https://confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html"
  ],
  "suggested_config_changes": {
    "auth_type": "sso"
  },
  "fallback_options": ["sso", "basic"]
}
```

### Common Error Scenarios

#### Scenario 1: Expired PAT Token

```json
{
  "error_type": "expired_token",
  "message": "Personal Access Token has expired",
  "troubleshooting_steps": [
    "Log into Jira Data Center",
    "Navigate to Profile → Personal Access Tokens",
    "Check token expiration date",
    "Create new token if expired",
    "Update configuration with new token"
  ],
  "auto_fallback": true,
  "fallback_method": "sso"
}
```

#### Scenario 2: SSO Session Expired

```json
{
  "error_type": "session_expired",
  "message": "SSO session has expired",
  "troubleshooting_steps": [
    "Log into Jira Data Center in browser",
    "Ensure browser session is active",
    "Try refreshing the page",
    "Use basic authentication as fallback"
  ],
  "prompt_for_fallback": true,
  "fallback_method": "basic"
}
```

## Implementation Examples

### Python Authentication Handler

```python
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

class AuthType(Enum):
    PAT = "pat"
    SSO = "sso"
    BASIC = "basic"
    API_TOKEN = "api_token"

@dataclass
class AuthResult:
    success: bool
    auth_type: AuthType
    headers: Dict[str, str]
    error_message: Optional[str] = None
    used_fallback: bool = False
    fallback_method: Optional[AuthType] = None

class PATHandler:
    """Personal Access Token authentication handler."""
    
    async def authenticate(self, config: JiraConfig) -> AuthResult:
        """Authenticate using Personal Access Token."""
        if not config.personal_access_token:
            return AuthResult(
                success=False,
                auth_type=AuthType.PAT,
                headers={},
                error_message="Personal Access Token is required"
            )
        
        headers = {
            "Authorization": f"Bearer {config.personal_access_token}",
            "Content-Type": "application/json"
        }
        
        # Test authentication
        try:
            response = await self._test_auth(config.base_url, headers)
            if response.status_code == 200:
                return AuthResult(
                    success=True,
                    auth_type=AuthType.PAT,
                    headers=headers
                )
            else:
                return AuthResult(
                    success=False,
                    auth_type=AuthType.PAT,
                    headers={},
                    error_message=f"PAT authentication failed: {response.status_code}"
                )
        except Exception as e:
            return AuthResult(
                success=False,
                auth_type=AuthType.PAT,
                headers={},
                error_message=f"PAT authentication error: {str(e)}"
            )

class SSOHandler:
    """SSO authentication handler."""
    
    async def authenticate(self, config: JiraConfig) -> AuthResult:
        """Authenticate using SSO session."""
        # Detect current session
        session_cookie = await self._detect_session(config)
        
        if not session_cookie:
            return AuthResult(
                success=False,
                auth_type=AuthType.SSO,
                headers={},
                error_message="No active SSO session found"
            )
        
        headers = {
            "Cookie": session_cookie,
            "Content-Type": "application/json"
        }
        
        # Test authentication
        try:
            response = await self._test_auth(config.base_url, headers)
            if response.status_code == 200:
                return AuthResult(
                    success=True,
                    auth_type=AuthType.SSO,
                    headers=headers
                )
            else:
                return AuthResult(
                    success=False,
                    auth_type=AuthType.SSO,
                    headers={},
                    error_message="SSO session invalid or expired"
                )
        except Exception as e:
            return AuthResult(
                success=False,
                auth_type=AuthType.SSO,
                headers={},
                error_message=f"SSO authentication error: {str(e)}"
            )
    
    async def _detect_session(self, config: JiraConfig) -> Optional[str]:
        """Detect active SSO session."""
        # Implementation for session detection
        # This could involve:
        # 1. Reading browser cookies
        # 2. Windows credential integration
        # 3. Provided session cookie
        
        if config.sso_session_cookie:
            return config.sso_session_cookie
        
        # Try to detect from browser/system
        # Implementation depends on deployment environment
        return None
```

### JavaScript/TypeScript Client

```typescript
interface AuthConfig {
  authType: 'pat' | 'sso' | 'basic' | 'api_token';
  personalAccessToken?: string;
  username?: string;
  password?: string;
  email?: string;
  apiToken?: string;
  useSso?: boolean;
  ssoSessionCookie?: string;
}

interface AuthResult {
  success: boolean;
  authType: string;
  headers: Record<string, string>;
  errorMessage?: string;
  usedFallback?: boolean;
  fallbackMethod?: string;
}

class JiraAuthenticator {
  async authenticate(baseUrl: string, config: AuthConfig): Promise<AuthResult> {
    switch (config.authType) {
      case 'pat':
        return this.authenticateWithPAT(baseUrl, config);
      case 'sso':
        return this.authenticateWithSSO(baseUrl, config);
      case 'basic':
        return this.authenticateWithBasic(baseUrl, config);
      case 'api_token':
        return this.authenticateWithAPIToken(baseUrl, config);
      default:
        throw new Error(`Unsupported auth type: ${config.authType}`);
    }
  }
  
  private async authenticateWithPAT(baseUrl: string, config: AuthConfig): Promise<AuthResult> {
    if (!config.personalAccessToken) {
      return {
        success: false,
        authType: 'pat',
        headers: {},
        errorMessage: 'Personal Access Token is required'
      };
    }
    
    const headers = {
      'Authorization': `Bearer ${config.personalAccessToken}`,
      'Content-Type': 'application/json'
    };
    
    try {
      const response = await fetch(`${baseUrl}/rest/api/3/myself`, {
        method: 'GET',
        headers
      });
      
      if (response.ok) {
        return {
          success: true,
          authType: 'pat',
          headers
        };
      } else {
        return {
          success: false,
          authType: 'pat',
          headers: {},
          errorMessage: `PAT authentication failed: ${response.status}`
        };
      }
    } catch (error) {
      return {
        success: false,
        authType: 'pat',
        headers: {},
        errorMessage: `PAT authentication error: ${error.message}`
      };
    }
  }
  
  private async authenticateWithSSO(baseUrl: string, config: AuthConfig): Promise<AuthResult> {
    // SSO implementation
    // This would typically involve:
    // 1. Checking for existing session cookies
    // 2. Redirecting to SSO provider if needed
    // 3. Handling SSO callback
    
    const sessionCookie = config.ssoSessionCookie || this.detectSessionCookie();
    
    if (!sessionCookie) {
      return {
        success: false,
        authType: 'sso',
        headers: {},
        errorMessage: 'No active SSO session found'
      };
    }
    
    const headers = {
      'Cookie': sessionCookie,
      'Content-Type': 'application/json'
    };
    
    try {
      const response = await fetch(`${baseUrl}/rest/api/3/myself`, {
        method: 'GET',
        headers,
        credentials: 'include'
      });
      
      if (response.ok) {
        return {
          success: true,
          authType: 'sso',
          headers
        };
      } else {
        return {
          success: false,
          authType: 'sso',
          headers: {},
          errorMessage: 'SSO session invalid or expired'
        };
      }
    } catch (error) {
      return {
        success: false,
        authType: 'sso',
        headers: {},
        errorMessage: `SSO authentication error: ${error.message}`
      };
    }
  }
  
  private detectSessionCookie(): string | null {
    // Implementation to detect session cookie from browser
    // This would read document.cookie and extract JSESSIONID
    const cookies = document.cookie.split(';');
    for (const cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === 'JSESSIONID') {
        return `JSESSIONID=${value}`;
      }
    }
    return null;
  }
}
```

## Security Considerations

### Token Security

1. **Token Storage**: Never store tokens in plain text
2. **Token Transmission**: Always use HTTPS
3. **Token Expiration**: Set appropriate expiration dates
4. **Token Rotation**: Implement regular token rotation
5. **Token Scope**: Use minimum required permissions

### Session Security

1. **Session Validation**: Regularly validate session status
2. **Session Timeout**: Implement appropriate timeouts
3. **Session Cleanup**: Clean up expired sessions
4. **Cross-Site Protection**: Implement CSRF protection

### Network Security

1. **SSL/TLS**: Always use encrypted connections
2. **Certificate Validation**: Validate SSL certificates
3. **Proxy Security**: Secure proxy configurations
4. **Network Isolation**: Use appropriate network segmentation

### Audit and Monitoring

1. **Authentication Logging**: Log all authentication attempts
2. **Failed Login Monitoring**: Monitor failed authentication attempts
3. **Token Usage Tracking**: Track token usage patterns
4. **Security Event Alerting**: Alert on suspicious activities

This authentication flow documentation provides comprehensive guidance for implementing secure and reliable authentication with Jira Data Center instances.