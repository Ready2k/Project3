# Jira Data Center 9.12.22 Configuration Guide

This guide provides comprehensive setup instructions for integrating the AAA system with Jira Data Center 9.12.22, including authentication methods, network configuration, and troubleshooting.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Authentication Methods](#authentication-methods)
4. [Configuration Examples](#configuration-examples)
5. [Network Configuration](#network-configuration)
6. [Troubleshooting](#troubleshooting)
7. [Migration from Cloud](#migration-from-cloud)
8. [Best Practices](#best-practices)

## Overview

Jira Data Center 9.12.22 is an on-premises deployment that differs from Jira Cloud in several key areas:

- **Authentication**: Supports Personal Access Tokens (PATs), SSO, and basic authentication
- **API Endpoints**: Uses both REST API v2 and v3 with some differences in response formats
- **Network Configuration**: Requires SSL certificate handling, proxy support, and custom timeouts
- **Deployment Detection**: Automatic detection of Data Center vs Cloud instances

The AAA system automatically detects your Jira deployment type and configures appropriate authentication and API handling.

## Prerequisites

### Jira Data Center Requirements

- Jira Data Center version 9.12.22 or compatible
- Network access to your Jira instance from the AAA system
- Appropriate user permissions for ticket access
- SSL certificates configured (if using HTTPS)

### AAA System Requirements

- AAA system version 2.3.0 or later
- Python 3.10+ with required dependencies
- Network connectivity to Jira Data Center instance

### User Permissions

Your Jira user account needs the following permissions:
- **Browse Projects**: To access project information
- **View Issues**: To read ticket details
- **API Access**: To use REST API endpoints

## Authentication Methods

### 1. Personal Access Tokens (PATs) - Recommended

Personal Access Tokens are the recommended authentication method for Jira Data Center as they provide secure, user-specific access without exposing passwords.

#### Creating a PAT in Jira Data Center

1. Log into your Jira Data Center instance
2. Go to **Profile** → **Personal Access Tokens**
3. Click **Create token**
4. Provide a meaningful name (e.g., "AAA System Integration")
5. Set expiration date (optional but recommended)
6. Copy the generated token immediately (it won't be shown again)

#### Configuration Example

```yaml
# config.yaml
jira:
  base_url: "https://jira.yourcompany.com"
  auth_type: "personal_access_token"
  personal_access_token: "your-pat-token-here"
  deployment_type: "data_center"
```

### 2. SSO Authentication

If your organization uses Single Sign-On (SSO) with Jira Data Center, the system can attempt to use your current session.

#### Requirements

- Active SSO session in your browser
- Same network/domain as Jira Data Center
- Session cookies accessible to the AAA system

#### Configuration Example

```yaml
# config.yaml
jira:
  base_url: "https://jira.yourcompany.com"
  auth_type: "sso"
  use_sso: true
  deployment_type: "data_center"
```

### 3. Basic Authentication (Fallback)

Basic authentication using username and password is available as a fallback option. Credentials are only stored in memory for the current session.

#### Configuration Example

```yaml
# config.yaml
jira:
  base_url: "https://jira.yourcompany.com"
  auth_type: "basic"
  username: "your-username"
  # Password will be prompted securely
  deployment_type: "data_center"
```

### Authentication Method Comparison

| Method | Security | Ease of Setup | Expiration | Recommended |
|--------|----------|---------------|------------|-------------|
| Personal Access Token | High | Medium | Configurable | ✅ Yes |
| SSO | High | Easy | Session-based | ✅ Yes |
| Basic Auth | Medium | Easy | None | ⚠️ Fallback only |

## Configuration Examples

### Basic Data Center Configuration

```yaml
# config.yaml
jira:
  base_url: "https://jira.yourcompany.com"
  auth_type: "personal_access_token"
  personal_access_token: "your-pat-token"
  deployment_type: "data_center"
  verify_ssl: true
  timeout: 30
```

### Enterprise Network Configuration

```yaml
# config.yaml
jira:
  base_url: "https://jira.yourcompany.com:8443"
  auth_type: "personal_access_token"
  personal_access_token: "your-pat-token"
  deployment_type: "data_center"
  
  # SSL Configuration
  verify_ssl: true
  ca_cert_path: "/path/to/your/ca-bundle.crt"
  
  # Proxy Configuration
  proxy_url: "http://proxy.yourcompany.com:8080"
  
  # Network Timeouts
  timeout: 60
  
  # Custom Context Path (if Jira is not at root)
  context_path: "/jira"
```

### Environment Variables

You can also configure using environment variables:

```bash
# .env file
JIRA_BASE_URL=https://jira.yourcompany.com
JIRA_AUTH_TYPE=personal_access_token
JIRA_PERSONAL_ACCESS_TOKEN=your-pat-token
JIRA_DEPLOYMENT_TYPE=data_center
JIRA_VERIFY_SSL=true
JIRA_TIMEOUT=30
```

## Network Configuration

### SSL Certificate Handling

#### Self-Signed Certificates

If your Jira Data Center uses self-signed certificates:

```yaml
jira:
  base_url: "https://jira.yourcompany.com"
  verify_ssl: false  # Only for development/testing
  # OR provide custom CA bundle
  ca_cert_path: "/path/to/ca-bundle.crt"
```

#### Custom CA Certificates

For internal Certificate Authorities:

```yaml
jira:
  base_url: "https://jira.yourcompany.com"
  verify_ssl: true
  ca_cert_path: "/etc/ssl/certs/company-ca-bundle.crt"
```

### Proxy Configuration

#### HTTP Proxy

```yaml
jira:
  base_url: "https://jira.yourcompany.com"
  proxy_url: "http://proxy.yourcompany.com:8080"
```

#### Authenticated Proxy

```yaml
jira:
  base_url: "https://jira.yourcompany.com"
  proxy_url: "http://username:password@proxy.yourcompany.com:8080"
```

### Custom Ports and Context Paths

#### Non-Standard Port

```yaml
jira:
  base_url: "https://jira.yourcompany.com:8443"
  custom_port: 8443
```

#### Custom Context Path

```yaml
jira:
  base_url: "https://yourcompany.com/jira"
  context_path: "/jira"
```

### Timeout Configuration

For enterprise networks with potential latency:

```yaml
jira:
  timeout: 60  # seconds
  # The system will also implement exponential backoff for retries
```

## Troubleshooting

### Common Issues and Solutions

#### 1. SSL Certificate Errors

**Error**: `SSL: CERTIFICATE_VERIFY_FAILED`

**Solutions**:
```yaml
# Option 1: Disable SSL verification (not recommended for production)
jira:
  verify_ssl: false

# Option 2: Provide custom CA bundle (recommended)
jira:
  verify_ssl: true
  ca_cert_path: "/path/to/ca-bundle.crt"
```

#### 2. Authentication Failures

**Error**: `401 Unauthorized`

**Troubleshooting Steps**:
1. Verify PAT token is correct and not expired
2. Check user permissions in Jira
3. Try authentication fallback chain
4. Verify base URL is correct

**Solutions**:
```yaml
# Enable authentication fallback
jira:
  auth_type: "sso"  # Will fallback to basic auth if SSO fails
```

#### 3. Network Connectivity Issues

**Error**: `Connection timeout` or `Connection refused`

**Troubleshooting Steps**:
1. Verify base URL and port
2. Check firewall rules
3. Test network connectivity: `curl -I https://jira.yourcompany.com`
4. Configure proxy if required

**Solutions**:
```yaml
jira:
  timeout: 60
  proxy_url: "http://proxy.yourcompany.com:8080"
```

#### 4. API Version Compatibility

**Error**: `404 Not Found` on API endpoints

**Solution**: The system automatically detects and falls back between API v3 and v2:
```yaml
# No configuration needed - automatic detection
jira:
  base_url: "https://jira.yourcompany.com"
  # System will test v3 first, fallback to v2 if needed
```

#### 5. Custom Context Path Issues

**Error**: `404 Not Found` for Jira at non-root path

**Solution**:
```yaml
jira:
  base_url: "https://yourcompany.com/jira"
  context_path: "/jira"
```

### Diagnostic Commands

#### Test Connection

```bash
# Using AAA system's built-in test
curl -X POST "http://localhost:8000/jira/test" \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "https://jira.yourcompany.com",
    "auth_type": "personal_access_token",
    "personal_access_token": "your-token"
  }'
```

#### Manual Network Test

```bash
# Test basic connectivity
curl -I https://jira.yourcompany.com

# Test with proxy
curl -I --proxy http://proxy.yourcompany.com:8080 https://jira.yourcompany.com

# Test API endpoint
curl -H "Authorization: Bearer your-pat-token" \
  https://jira.yourcompany.com/rest/api/3/serverInfo
```

### Error Code Reference

| Error Code | Description | Solution |
|------------|-------------|----------|
| 401 | Unauthorized | Check authentication credentials |
| 403 | Forbidden | Verify user permissions |
| 404 | Not Found | Check URL and API version |
| 500 | Internal Server Error | Check Jira server logs |
| SSL Error | Certificate issues | Configure SSL settings |
| Timeout | Network connectivity | Increase timeout, check proxy |

## Migration from Cloud

### Configuration Changes

When migrating from Jira Cloud to Data Center:

#### 1. Update Base URL

```yaml
# Before (Cloud)
jira:
  base_url: "https://yourcompany.atlassian.net"

# After (Data Center)
jira:
  base_url: "https://jira.yourcompany.com"
```

#### 2. Change Authentication Method

```yaml
# Before (Cloud - API Token)
jira:
  auth_type: "api_token"
  email: "user@yourcompany.com"
  api_token: "your-api-token"

# After (Data Center - PAT)
jira:
  auth_type: "personal_access_token"
  personal_access_token: "your-pat-token"
```

#### 3. Add Network Configuration

```yaml
# Data Center specific settings
jira:
  deployment_type: "data_center"
  verify_ssl: true
  ca_cert_path: "/path/to/ca-bundle.crt"  # if needed
  proxy_url: "http://proxy.yourcompany.com:8080"  # if needed
  timeout: 60
```

### Migration Checklist

- [ ] Update base URL to Data Center instance
- [ ] Create Personal Access Token in Jira Data Center
- [ ] Update authentication configuration
- [ ] Configure SSL certificates if needed
- [ ] Set up proxy configuration if required
- [ ] Test connection with new configuration
- [ ] Update any automation scripts or integrations
- [ ] Train users on new authentication method

### Backward Compatibility

The AAA system maintains backward compatibility:
- Existing Cloud configurations continue to work
- Automatic deployment type detection
- Graceful fallback for API differences
- No breaking changes to existing integrations

## Best Practices

### Security

1. **Use Personal Access Tokens**: Preferred over basic authentication
2. **Set Token Expiration**: Configure reasonable expiration dates
3. **Rotate Tokens Regularly**: Establish a token rotation schedule
4. **Enable SSL Verification**: Always verify SSL certificates in production
5. **Use Least Privilege**: Grant minimum required permissions

### Network Configuration

1. **Configure Timeouts**: Set appropriate timeouts for your network
2. **Use Proxy Settings**: Configure proxy for corporate environments
3. **Monitor Connectivity**: Implement health checks and monitoring
4. **Document Network Requirements**: Maintain network configuration documentation

### Operational

1. **Test Configurations**: Always test new configurations in development first
2. **Monitor API Usage**: Track API calls and rate limits
3. **Log Authentication Events**: Enable audit logging for security
4. **Backup Configurations**: Maintain configuration backups
5. **Document Custom Settings**: Document any custom network or security settings

### Performance

1. **Use Connection Pooling**: Enable HTTP connection pooling
2. **Implement Caching**: Cache frequently accessed data
3. **Monitor Response Times**: Track API response performance
4. **Optimize Queries**: Use efficient API queries and filters

## Support and Resources

### Documentation Links

- [Jira Data Center REST API Documentation](https://docs.atlassian.com/software/jira/docs/api/REST/)
- [Personal Access Tokens Guide](https://confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html)
- [Jira Data Center Installation Guide](https://confluence.atlassian.com/adminjiraserver/installing-jira-data-center-938846841.html)

### Getting Help

1. **Check Logs**: Review AAA system logs for detailed error information
2. **Use Debug Mode**: Enable debug mode in the Streamlit interface
3. **Test Connectivity**: Use the built-in connection test feature
4. **Consult Documentation**: Review this guide and Jira documentation
5. **Contact Support**: Reach out to your system administrator or support team

### Common Configuration Templates

#### Development Environment

```yaml
jira:
  base_url: "https://jira-dev.yourcompany.com"
  auth_type: "personal_access_token"
  personal_access_token: "dev-pat-token"
  deployment_type: "data_center"
  verify_ssl: false  # Only for development
  timeout: 30
```

#### Production Environment

```yaml
jira:
  base_url: "https://jira.yourcompany.com"
  auth_type: "personal_access_token"
  personal_access_token: "prod-pat-token"
  deployment_type: "data_center"
  verify_ssl: true
  ca_cert_path: "/etc/ssl/certs/company-ca-bundle.crt"
  proxy_url: "http://proxy.yourcompany.com:8080"
  timeout: 60
```

This guide should help you successfully configure and troubleshoot Jira Data Center integration with the AAA system. For additional support, consult your system administrator or the Jira Data Center documentation.