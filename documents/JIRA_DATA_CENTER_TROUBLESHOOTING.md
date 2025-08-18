# Jira Data Center Troubleshooting Guide

This guide provides detailed troubleshooting steps for common issues when integrating with Jira Data Center 9.12.22.

## Quick Diagnostic Checklist

Before diving into specific issues, run through this quick checklist:

- [ ] Base URL is correct and accessible
- [ ] Authentication credentials are valid
- [ ] Network connectivity is working
- [ ] SSL certificates are properly configured
- [ ] User has required permissions in Jira
- [ ] AAA system is running the latest version

## Common Issues and Solutions

### 1. Connection Issues

#### Issue: "Connection failed" or "Connection timeout"

**Symptoms:**
- Cannot connect to Jira Data Center
- Timeout errors during connection test
- "Connection refused" errors

**Diagnostic Steps:**

1. **Test Basic Connectivity:**
   ```bash
   # Test if Jira is reachable
   curl -I https://jira.yourcompany.com
   
   # Test with specific timeout
   curl -I --connect-timeout 10 https://jira.yourcompany.com
   ```

2. **Check Network Configuration:**
   ```bash
   # Test with proxy if required
   curl -I --proxy http://proxy.yourcompany.com:8080 https://jira.yourcompany.com
   
   # Test DNS resolution
   nslookup jira.yourcompany.com
   ```

**Solutions:**

1. **Increase Timeout:**
   ```yaml
   jira:
     timeout: 60  # Increase from default 30 seconds
   ```

2. **Configure Proxy:**
   ```yaml
   jira:
     proxy_url: "http://proxy.yourcompany.com:8080"
   ```

3. **Check Firewall Rules:**
   - Ensure outbound HTTPS (443) is allowed
   - Check if custom ports are blocked
   - Verify proxy configuration

### 2. SSL Certificate Issues

#### Issue: "SSL: CERTIFICATE_VERIFY_FAILED"

**Symptoms:**
- SSL verification errors
- Certificate chain issues
- Self-signed certificate warnings

**Diagnostic Steps:**

1. **Check Certificate Details:**
   ```bash
   # View certificate information
   openssl s_client -connect jira.yourcompany.com:443 -servername jira.yourcompany.com
   
   # Check certificate chain
   curl -vI https://jira.yourcompany.com
   ```

2. **Test Certificate Validation:**
   ```bash
   # Test with system CA bundle
   curl --cacert /etc/ssl/certs/ca-certificates.crt https://jira.yourcompany.com
   ```

**Solutions:**

1. **For Self-Signed Certificates (Development Only):**
   ```yaml
   jira:
     verify_ssl: false  # NOT recommended for production
   ```

2. **For Internal CA Certificates:**
   ```yaml
   jira:
     verify_ssl: true
     ca_cert_path: "/path/to/your/ca-bundle.crt"
   ```

3. **For Certificate Chain Issues:**
   ```bash
   # Download and combine certificate chain
   echo | openssl s_client -connect jira.yourcompany.com:443 -servername jira.yourcompany.com 2>/dev/null | openssl x509 > jira-cert.pem
   ```

### 3. Authentication Failures

#### Issue: "401 Unauthorized" or "403 Forbidden"

**Symptoms:**
- Authentication fails with valid credentials
- Permission denied errors
- Token validation failures

**Diagnostic Steps:**

1. **Test Authentication Manually:**
   ```bash
   # Test PAT authentication
   curl -H "Authorization: Bearer your-pat-token" \
     https://jira.yourcompany.com/rest/api/3/myself
   
   # Test basic authentication
   curl -u username:password \
     https://jira.yourcompany.com/rest/api/3/myself
   ```

2. **Check Token Validity:**
   ```bash
   # Check token expiration and permissions
   curl -H "Authorization: Bearer your-pat-token" \
     https://jira.yourcompany.com/rest/api/3/myself
   ```

**Solutions:**

1. **Personal Access Token Issues:**
   - Verify token is not expired
   - Check token permissions in Jira
   - Regenerate token if necessary

2. **User Permission Issues:**
   - Ensure user has "Browse Projects" permission
   - Verify "View Issues" permission
   - Check API access permissions

3. **Enable Authentication Fallback:**
   ```yaml
   jira:
     auth_type: "sso"  # Will fallback to basic auth if needed
   ```

### 4. API Version Compatibility

#### Issue: "404 Not Found" on API endpoints

**Symptoms:**
- API endpoints return 404 errors
- Different response formats than expected
- Missing fields in API responses

**Diagnostic Steps:**

1. **Check Available API Versions:**
   ```bash
   # Test API v3
   curl -H "Authorization: Bearer your-token" \
     https://jira.yourcompany.com/rest/api/3/serverInfo
   
   # Test API v2
   curl -H "Authorization: Bearer your-token" \
     https://jira.yourcompany.com/rest/api/2/serverInfo
   ```

2. **Check Jira Version:**
   ```bash
   curl -H "Authorization: Bearer your-token" \
     https://jira.yourcompany.com/rest/api/2/serverInfo
   ```

**Solutions:**

1. **Automatic API Version Detection:**
   The system automatically detects and uses the appropriate API version. No configuration needed.

2. **Manual API Version Override:**
   ```yaml
   jira:
     preferred_api_version: "2"  # Force API v2 if v3 has issues
   ```

### 5. Custom Context Path Issues

#### Issue: "404 Not Found" for Jira at non-root path

**Symptoms:**
- Jira is accessible at `/jira` or custom path
- API endpoints return 404 errors
- Base URL includes context path

**Diagnostic Steps:**

1. **Identify Context Path:**
   ```bash
   # Test root path
   curl -I https://yourcompany.com/
   
   # Test Jira context path
   curl -I https://yourcompany.com/jira/
   ```

**Solutions:**

1. **Configure Context Path:**
   ```yaml
   jira:
     base_url: "https://yourcompany.com/jira"
     context_path: "/jira"
   ```

2. **Alternative Configuration:**
   ```yaml
   jira:
     base_url: "https://yourcompany.com"
     context_path: "/jira"
   ```

### 6. Proxy Configuration Issues

#### Issue: Proxy authentication or connection failures

**Symptoms:**
- Connection works without proxy but fails with proxy
- Proxy authentication errors
- Timeout errors through proxy

**Diagnostic Steps:**

1. **Test Proxy Connectivity:**
   ```bash
   # Test proxy connection
   curl -I --proxy http://proxy.yourcompany.com:8080 https://jira.yourcompany.com
   
   # Test with authentication
   curl -I --proxy http://username:password@proxy.yourcompany.com:8080 https://jira.yourcompany.com
   ```

**Solutions:**

1. **Basic Proxy Configuration:**
   ```yaml
   jira:
     proxy_url: "http://proxy.yourcompany.com:8080"
   ```

2. **Authenticated Proxy:**
   ```yaml
   jira:
     proxy_url: "http://username:password@proxy.yourcompany.com:8080"
   ```

3. **Environment Variables:**
   ```bash
   export HTTP_PROXY=http://proxy.yourcompany.com:8080
   export HTTPS_PROXY=http://proxy.yourcompany.com:8080
   ```

### 7. SSO Authentication Issues

#### Issue: SSO authentication fails or session expires

**Symptoms:**
- SSO authentication doesn't work
- Session expires quickly
- Browser session not recognized

**Diagnostic Steps:**

1. **Check Browser Session:**
   - Verify you're logged into Jira in the same browser
   - Check if session cookies are accessible
   - Test manual login to Jira

2. **Check Network Configuration:**
   - Ensure AAA system and browser are on same network
   - Verify domain/subdomain configuration

**Solutions:**

1. **Enable SSO with Fallback:**
   ```yaml
   jira:
     auth_type: "sso"
     use_sso: true
     # System will fallback to basic auth if SSO fails
   ```

2. **Manual Session Configuration:**
   ```yaml
   jira:
     auth_type: "sso"
     sso_session_cookie: "JSESSIONID=your-session-id"
   ```

## Advanced Troubleshooting

### Enable Debug Mode

1. **In Streamlit Interface:**
   - Check "Debug Mode" in the sidebar
   - View detailed error messages and logs

2. **In Configuration:**
   ```yaml
   logging:
     level: DEBUG
   ```

3. **Environment Variable:**
   ```bash
   export LOGGING_LEVEL=DEBUG
   ```

### Network Diagnostics

#### Comprehensive Network Test

```bash
#!/bin/bash
# network-test.sh - Comprehensive Jira connectivity test

JIRA_URL="https://jira.yourcompany.com"
PROXY_URL="http://proxy.yourcompany.com:8080"

echo "Testing Jira Data Center connectivity..."

# Test 1: Basic connectivity
echo "1. Testing basic connectivity..."
curl -I --connect-timeout 10 $JIRA_URL

# Test 2: DNS resolution
echo "2. Testing DNS resolution..."
nslookup $(echo $JIRA_URL | sed 's|https://||' | sed 's|/.*||')

# Test 3: SSL certificate
echo "3. Testing SSL certificate..."
echo | openssl s_client -connect $(echo $JIRA_URL | sed 's|https://||' | sed 's|/.*||'):443 -servername $(echo $JIRA_URL | sed 's|https://||' | sed 's|/.*||') 2>/dev/null | openssl x509 -noout -dates

# Test 4: Proxy connectivity (if proxy is configured)
if [ ! -z "$PROXY_URL" ]; then
    echo "4. Testing proxy connectivity..."
    curl -I --proxy $PROXY_URL --connect-timeout 10 $JIRA_URL
fi

# Test 5: API endpoint
echo "5. Testing API endpoint..."
curl -I $JIRA_URL/rest/api/3/serverInfo

echo "Network test complete."
```

#### Performance Testing

```bash
# Test response times
time curl -s $JIRA_URL/rest/api/3/serverInfo > /dev/null

# Test with different timeouts
for timeout in 5 10 30 60; do
    echo "Testing with ${timeout}s timeout..."
    time curl --connect-timeout $timeout -s $JIRA_URL/rest/api/3/serverInfo > /dev/null
done
```

### Configuration Validation

#### Validate Configuration File

```python
# validate-config.py
import yaml
from pydantic import BaseModel, ValidationError

class JiraConfig(BaseModel):
    base_url: str
    auth_type: str
    deployment_type: str = "data_center"
    verify_ssl: bool = True
    timeout: int = 30

try:
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    jira_config = JiraConfig(**config.get('jira', {}))
    print("✅ Configuration is valid")
    print(f"Base URL: {jira_config.base_url}")
    print(f"Auth Type: {jira_config.auth_type}")
    print(f"Deployment: {jira_config.deployment_type}")
    
except ValidationError as e:
    print("❌ Configuration validation failed:")
    print(e)
except Exception as e:
    print(f"❌ Error reading configuration: {e}")
```

### Log Analysis

#### Common Log Patterns

1. **Connection Timeouts:**
   ```
   ERROR: Connection timeout after 30 seconds
   ```
   **Solution:** Increase timeout value

2. **SSL Verification Errors:**
   ```
   ERROR: SSL: CERTIFICATE_VERIFY_FAILED
   ```
   **Solution:** Configure CA certificates or disable SSL verification

3. **Authentication Failures:**
   ```
   ERROR: 401 Unauthorized - Invalid token
   ```
   **Solution:** Check token validity and permissions

4. **API Version Issues:**
   ```
   ERROR: 404 Not Found - /rest/api/3/issue/KEY-123
   ```
   **Solution:** System will automatically fallback to API v2

### Performance Optimization

#### Connection Pooling

```yaml
jira:
  # Enable connection pooling for better performance
  connection_pool_size: 10
  connection_pool_maxsize: 20
```

#### Caching Configuration

```yaml
jira:
  # Cache deployment detection results
  cache_deployment_info: true
  cache_ttl: 3600  # 1 hour
```

## Error Code Reference

| Error Code | Description | Common Causes | Solutions |
|------------|-------------|---------------|-----------|
| 400 | Bad Request | Invalid request format | Check API request structure |
| 401 | Unauthorized | Invalid credentials | Verify token/password |
| 403 | Forbidden | Insufficient permissions | Check user permissions |
| 404 | Not Found | Invalid URL or endpoint | Verify base URL and API version |
| 408 | Request Timeout | Network timeout | Increase timeout value |
| 500 | Internal Server Error | Jira server issue | Check Jira server logs |
| 502 | Bad Gateway | Proxy/load balancer issue | Check proxy configuration |
| 503 | Service Unavailable | Jira maintenance/overload | Retry later or check Jira status |

## Getting Additional Help

### Diagnostic Information to Collect

When seeking help, collect the following information:

1. **System Information:**
   - AAA system version
   - Python version
   - Operating system

2. **Jira Information:**
   - Jira Data Center version
   - Base URL (sanitized)
   - Authentication method used

3. **Network Information:**
   - Proxy configuration (if any)
   - SSL certificate type
   - Network topology

4. **Error Details:**
   - Complete error messages
   - Log entries with timestamps
   - Steps to reproduce

### Support Channels

1. **Internal Support:**
   - Contact your system administrator
   - Check internal documentation
   - Review Jira server logs

2. **Community Resources:**
   - Atlassian Community forums
   - Jira Data Center documentation
   - Stack Overflow

3. **Professional Support:**
   - Atlassian Support (if you have a license)
   - Professional services consultation

This troubleshooting guide should help you resolve most common issues with Jira Data Center integration. For complex issues, don't hesitate to seek additional support from your system administrator or Atlassian support team.