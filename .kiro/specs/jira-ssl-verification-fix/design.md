# Design Document

## Overview

This design addresses the JIRA SSL verification issue where the "Verify SSL Certificates" setting is being ignored due to duplicate configuration assignments and inconsistent SSL handling across different parts of the codebase.

## Architecture

### Current Issues Identified

1. **Duplicate Configuration Lines**: Multiple files contain duplicate lines that assign `verify_ssl` twice, potentially causing the second assignment to overwrite the first
2. **Inconsistent SSL Handler Initialization**: SSL handlers are initialized with duplicate parameters
3. **Configuration Propagation**: The verify_ssl setting may not be properly propagated through all layers of the HTTP client stack

### Target Architecture

1. **Clean Configuration Assignment**: Single, clear assignment of SSL verification settings
2. **Consistent SSL Handler Usage**: Proper initialization and usage of SSL handlers across all HTTP clients
3. **Unified SSL Configuration**: Centralized SSL configuration that applies consistently to all JIRA API calls

## Components and Interfaces

### Component 1: Streamlit UI Configuration (streamlit_app.py)

**Current Issues:**
- Lines 2611, 2723, 2822 contain duplicate `"verify_ssl": verify_ssl,` assignments
- This creates redundant configuration entries that may cause confusion

**Target Implementation:**
```python
# Clean, single assignment
jira_config = {
    "base_url": base_url,
    "email": email,
    "api_token": api_token,
    "verify_ssl": verify_ssl,  # Single assignment only
    "ca_cert_path": ca_cert_path if ca_cert_path else None,
    "proxy_url": proxy_url if proxy_url else None,
    # ... other config
}
```

**Interface:**
- Input: User checkbox selection for "Verify SSL Certificates"
- Output: Clean JiraConfig object with single verify_ssl assignment
- Validation: Ensure verify_ssl is boolean and properly set

### Component 2: JIRA Service SSL Handler (app/services/jira.py)

**Current Issues:**
- Lines 82, 108, 114 contain duplicate `verify_ssl=config.verify_ssl,` assignments in SSL handler initialization
- This may cause initialization issues or unexpected behavior

**Target Implementation:**
```python
# Clean SSL handler initialization
self.ssl_handler = SSLHandler(
    verify_ssl=config.verify_ssl,
    ca_cert_path=config.ca_cert_path
)

# Clean deployment detector initialization
self.deployment_detector = DeploymentDetector(
    timeout=self.timeout,
    verify_ssl=config.verify_ssl,
    ca_cert_path=config.ca_cert_path,
    proxy_url=config.proxy_url
)

# Clean API version manager initialization
self.api_version_manager = APIVersionManager(
    timeout=self.timeout,
    verify_ssl=config.verify_ssl,
    ca_cert_path=config.ca_cert_path,
    proxy_url=config.proxy_url
)
```

**Interface:**
- Input: JiraConfig with verify_ssl setting
- Output: Properly configured SSL handlers
- Validation: Ensure SSL handlers receive correct configuration

### Component 3: HTTP Client SSL Configuration

**Current Implementation:** SSL configuration is handled through `ssl_handler.get_httpx_verify_config()`

**Target Enhancement:**
- Ensure all HTTP clients consistently use the SSL handler configuration
- Add logging to show when SSL verification is enabled/disabled
- Provide clear feedback about SSL configuration status

**Interface:**
- Input: SSL handler with verify_ssl setting
- Output: Properly configured httpx clients
- Logging: Clear indication of SSL verification status

## Data Models

### JiraConfig SSL Fields
```python
class JiraConfig:
    verify_ssl: bool = True          # Whether to verify SSL certificates
    ca_cert_path: Optional[str] = None  # Path to custom CA certificate
    # ... other fields
```

### SSL Configuration Flow
```
User Input (checkbox) 
    → Streamlit UI (single assignment)
    → JiraConfig object
    → JiraService initialization
    → SSL Handler creation
    → HTTP Client configuration
    → API calls with proper SSL settings
```

## Error Handling

### SSL Configuration Validation
1. **Invalid CA Certificate Path**: Validate that ca_cert_path exists and is readable
2. **SSL Context Creation**: Handle errors when creating SSL contexts with custom certificates
3. **HTTP Client Configuration**: Ensure SSL settings are properly applied to HTTP clients

### User Feedback
1. **SSL Disabled Warning**: Show warning when SSL verification is disabled
2. **Certificate Issues**: Provide clear error messages for certificate problems
3. **Configuration Status**: Display current SSL verification status in connection test results

### Troubleshooting Integration
1. **SSL Error Detection**: Identify SSL-related connection failures
2. **Suggested Fixes**: Provide specific recommendations for SSL configuration
3. **Quick Fixes**: Offer option to disable SSL verification for testing

## Testing Strategy

### Unit Tests
1. **Configuration Assignment**: Test that verify_ssl is set correctly without duplicates
2. **SSL Handler Initialization**: Test SSL handler creation with various configurations
3. **HTTP Client Configuration**: Test that httpx clients use correct SSL settings

### Integration Tests
1. **End-to-End SSL Flow**: Test complete flow from UI to API calls
2. **SSL Verification Scenarios**: Test with SSL enabled/disabled
3. **Certificate Validation**: Test with valid/invalid certificates

### Manual Testing Scenarios
1. **Self-Signed Certificate**: Test with self-signed certificate and SSL disabled
2. **Valid Certificate**: Test with valid certificate and SSL enabled
3. **Invalid Certificate**: Test error handling with invalid certificates
4. **Configuration Changes**: Test that SSL setting changes take effect immediately

## Implementation Plan

### Phase 1: Fix Duplicate Assignments
1. Remove duplicate `verify_ssl` assignments in streamlit_app.py
2. Remove duplicate parameter assignments in jira.py SSL handler initialization
3. Verify configuration objects are created correctly

### Phase 2: Enhance SSL Feedback
1. Add logging to show SSL verification status
2. Improve error messages for SSL-related failures
3. Add warnings when SSL verification is disabled

### Phase 3: Testing and Validation
1. Create comprehensive test suite for SSL configuration
2. Test with various SSL scenarios (valid, invalid, self-signed certificates)
3. Validate that SSL settings are respected across all authentication methods

## Security Considerations

### SSL Verification Disabled
- Show clear warnings when SSL verification is disabled
- Recommend enabling SSL verification for production environments
- Provide guidance on proper certificate configuration

### Certificate Validation
- Validate custom CA certificate files before use
- Provide clear error messages for certificate issues
- Support both PEM and other common certificate formats

### Configuration Security
- Ensure SSL settings cannot be bypassed unintentionally
- Validate that SSL configuration is applied consistently
- Log SSL configuration changes for audit purposes