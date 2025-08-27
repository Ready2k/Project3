# Jira SSL and Proxy Troubleshooting Guide

## Quick Fixes for Common Issues

### SSL Certificate Errors

If you see errors like:
- "SSL certificate verification failed"
- "Could not retrieve certificate information"
- "certificate verify failed"

**Quick Fix Options:**

1. **Disable SSL Verification (Testing Only)**
   - In Streamlit UI: Uncheck "Verify SSL Certificates"
   - Via Environment Variable: `export JIRA_VERIFY_SSL=false`
   - Via Code: `config.disable_ssl_verification()`

2. **For Self-Signed Certificates**
   - Add your certificate to `ca_cert_path` in configuration
   - Or temporarily disable SSL verification for testing

### Proxy Configuration Errors

If you see errors like:
- `__init__() got an unexpected keyword argument 'proxies'`
- "Proxy connection error"

**Fixed Issues:**
- ✅ Proxy parameter handling has been fixed
- ✅ Now properly handles `None` proxy configurations
- ✅ Improved error messages for proxy issues

**Configuration Options:**
```yaml
jira:
  proxy_url: "http://proxy.company.com:8080"
  # Or with authentication:
  proxy_url: "http://username:password@proxy.company.com:8080"
```

## Environment Variables for Quick Configuration

```bash
# Disable SSL verification
export JIRA_VERIFY_SSL=false

# Set proxy
export JIRA_PROXY_URL="http://proxy.company.com:8080"

# Basic Jira configuration
export JIRA_BASE_URL="https://your-jira-instance.com"
export JIRA_EMAIL="your-email@company.com"
export JIRA_API_TOKEN="your-api-token"
```

## Streamlit UI Configuration

1. **Navigate to Jira Configuration section**
2. **For SSL Issues:**
   - Uncheck "Verify SSL Certificates" for testing
   - Add CA certificate path for production use
3. **For Proxy Issues:**
   - Enter proxy URL in format: `http://proxy.company.com:8080`
   - Include credentials if needed: `http://user:pass@proxy.com:8080`

## Testing Your Configuration

Run the test script to verify fixes:
```bash
python3 test_ssl_proxy_fixes.py
```

## Production Recommendations

⚠️ **Security Warning**: Only disable SSL verification for testing with trusted internal servers. Never use `verify_ssl=false` in production environments.

**For Production:**
- Use proper SSL certificates
- Add custom CA certificates to `ca_cert_path`
- Configure proxy authentication securely
- Enable SSL verification (`verify_ssl=true`)

## Error Log Analysis

### Before Fix:
```
ERROR | Failed to detect Jira deployment: Version detection failed: __init__() got an unexpected keyword argument 'proxies'
WARNING | SSL validation failed: Could not retrieve certificate information
```

### After Fix:
- ✅ Proxy parameters handled correctly
- ✅ SSL verification can be easily disabled
- ✅ Better error messages with troubleshooting steps
- ✅ Improved configuration options

## Additional Resources

- [Jira Data Center Setup Guide](documents/JIRA_DATA_CENTER_SETUP.md)
- [Jira Authentication Flows](documents/JIRA_AUTHENTICATION_FLOWS.md)
- [Jira Troubleshooting](documents/JIRA_DATA_CENTER_TROUBLESHOOTING.md)