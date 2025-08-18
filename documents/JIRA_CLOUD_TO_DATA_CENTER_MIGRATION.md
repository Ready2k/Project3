# Jira Cloud to Data Center Migration Guide

This guide helps you migrate your AAA system configuration from Jira Cloud to Jira Data Center 9.12.22, ensuring a smooth transition with minimal downtime.

## Migration Overview

### Key Differences

| Aspect | Jira Cloud | Jira Data Center |
|--------|------------|------------------|
| **Base URL** | `*.atlassian.net` | Your domain (e.g., `jira.company.com`) |
| **Authentication** | Email + API Token | Personal Access Token (PAT) or SSO |
| **SSL Certificates** | Managed by Atlassian | Self-managed (may include custom CAs) |
| **Network** | Direct internet access | May require proxy, custom ports |
| **API Versions** | Primarily v3 | Both v2 and v3 (automatic detection) |
| **Deployment Detection** | Automatic | Automatic with enhanced detection |

### Migration Benefits

- **Enhanced Security**: Better control over authentication and network security
- **Customization**: More configuration options for enterprise environments
- **Performance**: Potentially better performance for internal networks
- **Compliance**: Better compliance with internal security policies

## Pre-Migration Checklist

### 1. Information Gathering

Before starting the migration, collect the following information:

#### Current Jira Cloud Configuration
- [ ] Current base URL (e.g., `https://yourcompany.atlassian.net`)
- [ ] Email address used for authentication
- [ ] API token (for reference, will not be used in Data Center)
- [ ] Projects and tickets currently being accessed
- [ ] Any custom configurations or integrations

#### New Jira Data Center Information
- [ ] New base URL (e.g., `https://jira.yourcompany.com`)
- [ ] Custom port (if not standard 443/80)
- [ ] Context path (if Jira is not at root, e.g., `/jira`)
- [ ] SSL certificate information
- [ ] Proxy configuration (if required)
- [ ] Network access requirements

#### User Account Information
- [ ] Username in Data Center (may differ from Cloud)
- [ ] User permissions in Data Center
- [ ] Access to create Personal Access Tokens
- [ ] SSO availability and configuration

### 2. Access Verification

Verify you have the necessary access:

- [ ] Can log into Jira Data Center web interface
- [ ] Can create Personal Access Tokens
- [ ] Can access projects and tickets you need
- [ ] Network connectivity from AAA system to Jira Data Center

## Step-by-Step Migration

### Step 1: Backup Current Configuration

First, backup your current working configuration:

```bash
# Backup current config
cp config.yaml config.yaml.cloud.backup
cp .env .env.cloud.backup
```

### Step 2: Create Personal Access Token

1. **Log into Jira Data Center:**
   - Navigate to your Jira Data Center instance
   - Log in with your credentials

2. **Create PAT:**
   - Go to **Profile** → **Personal Access Tokens**
   - Click **Create token**
   - Name: "AAA System Integration"
   - Expiration: Set appropriate expiration (e.g., 1 year)
   - **Copy the token immediately** (it won't be shown again)

### Step 3: Update Configuration

#### Option A: Update config.yaml

```yaml
# Before (Jira Cloud)
jira:
  base_url: "https://yourcompany.atlassian.net"
  auth_type: "api_token"
  email: "user@yourcompany.com"
  api_token: "your-cloud-api-token"
  deployment_type: "cloud"

# After (Jira Data Center)
jira:
  base_url: "https://jira.yourcompany.com"
  auth_type: "personal_access_token"
  personal_access_token: "your-data-center-pat"
  deployment_type: "data_center"
  verify_ssl: true
  timeout: 30
```

#### Option B: Update .env file

```bash
# Before (Jira Cloud)
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_AUTH_TYPE=api_token
JIRA_EMAIL=user@yourcompany.com
JIRA_API_TOKEN=your-cloud-api-token

# After (Jira Data Center)
JIRA_BASE_URL=https://jira.yourcompany.com
JIRA_AUTH_TYPE=personal_access_token
JIRA_PERSONAL_ACCESS_TOKEN=your-data-center-pat
JIRA_DEPLOYMENT_TYPE=data_center
```

### Step 4: Configure Network Settings (If Required)

If your Data Center deployment requires additional network configuration:

```yaml
jira:
  base_url: "https://jira.yourcompany.com"
  auth_type: "personal_access_token"
  personal_access_token: "your-pat-token"
  deployment_type: "data_center"
  
  # SSL Configuration (if using custom certificates)
  verify_ssl: true
  ca_cert_path: "/path/to/ca-bundle.crt"
  
  # Proxy Configuration (if required)
  proxy_url: "http://proxy.yourcompany.com:8080"
  
  # Custom Port (if not standard)
  custom_port: 8443
  
  # Context Path (if Jira is not at root)
  context_path: "/jira"
  
  # Timeout (for slower networks)
  timeout: 60
```

### Step 5: Test New Configuration

1. **Test Connection:**
   ```bash
   # Using AAA system's test endpoint
   curl -X POST "http://localhost:8000/jira/test" \
     -H "Content-Type: application/json" \
     -d '{
       "base_url": "https://jira.yourcompany.com",
       "auth_type": "personal_access_token",
       "personal_access_token": "your-pat-token"
     }'
   ```

2. **Test in Streamlit Interface:**
   - Start the AAA system: `make dev`
   - Go to Jira configuration in sidebar
   - Enter new Data Center details
   - Click "Test Connection"
   - Verify successful connection

3. **Test Ticket Fetching:**
   ```bash
   # Test fetching a known ticket
   curl -X POST "http://localhost:8000/jira/fetch" \
     -H "Content-Type: application/json" \
     -d '{
       "base_url": "https://jira.yourcompany.com",
       "auth_type": "personal_access_token",
       "personal_access_token": "your-pat-token",
       "ticket_key": "PROJECT-123"
     }'
   ```

### Step 6: Verify Full Functionality

Test the complete workflow:

1. **Ingest from Jira:**
   - Use the Jira integration to fetch a ticket
   - Verify ticket data is parsed correctly
   - Check that all required fields are present

2. **Run Analysis:**
   - Process the ticket through the full AAA workflow
   - Verify pattern matching works correctly
   - Check that recommendations are generated

3. **Export Results:**
   - Export results in different formats
   - Verify all data is included correctly

## Common Migration Issues and Solutions

### Issue 1: SSL Certificate Errors

**Problem:** `SSL: CERTIFICATE_VERIFY_FAILED`

**Solution:**
```yaml
# For internal CA certificates
jira:
  verify_ssl: true
  ca_cert_path: "/etc/ssl/certs/company-ca-bundle.crt"

# For self-signed certificates (development only)
jira:
  verify_ssl: false
```

### Issue 2: Authentication Failures

**Problem:** `401 Unauthorized` with valid PAT

**Troubleshooting:**
1. Verify PAT is not expired
2. Check user permissions in Jira Data Center
3. Ensure PAT has correct scopes

**Solution:**
```yaml
# Enable authentication fallback
jira:
  auth_type: "sso"  # Will try SSO first, then fallback to basic auth
```

### Issue 3: Network Connectivity

**Problem:** Connection timeouts or proxy issues

**Solution:**
```yaml
jira:
  proxy_url: "http://proxy.yourcompany.com:8080"
  timeout: 60
```

### Issue 4: API Compatibility

**Problem:** Different API responses between Cloud and Data Center

**Solution:** The system automatically handles API differences. No configuration needed.

### Issue 5: Custom Context Path

**Problem:** Jira is at `/jira` path instead of root

**Solution:**
```yaml
jira:
  base_url: "https://yourcompany.com/jira"
  context_path: "/jira"
```

## Advanced Migration Scenarios

### Scenario 1: Gradual Migration

If you need to support both Cloud and Data Center temporarily:

```yaml
# config.yaml - Support multiple environments
jira_cloud:
  base_url: "https://yourcompany.atlassian.net"
  auth_type: "api_token"
  email: "user@yourcompany.com"
  api_token: "cloud-token"

jira_data_center:
  base_url: "https://jira.yourcompany.com"
  auth_type: "personal_access_token"
  personal_access_token: "dc-pat-token"
  deployment_type: "data_center"

# Use environment variable to switch
active_jira: "${JIRA_ENVIRONMENT:-data_center}"
```

### Scenario 2: Multiple Data Center Instances

For organizations with multiple Jira Data Center instances:

```yaml
jira_production:
  base_url: "https://jira.yourcompany.com"
  auth_type: "personal_access_token"
  personal_access_token: "prod-pat-token"

jira_staging:
  base_url: "https://jira-staging.yourcompany.com"
  auth_type: "personal_access_token"
  personal_access_token: "staging-pat-token"
```

### Scenario 3: SSO Integration

For organizations using SSO:

```yaml
jira:
  base_url: "https://jira.yourcompany.com"
  auth_type: "sso"
  use_sso: true
  deployment_type: "data_center"
  # Fallback to basic auth if SSO fails
```

## Post-Migration Tasks

### 1. Update Documentation

- [ ] Update internal documentation with new configuration
- [ ] Share migration guide with team members
- [ ] Document any custom network configurations

### 2. Monitor Performance

- [ ] Monitor connection times and performance
- [ ] Check for any API rate limiting issues
- [ ] Verify all integrations work correctly

### 3. Security Review

- [ ] Review PAT permissions and expiration
- [ ] Ensure SSL certificates are properly configured
- [ ] Verify network security settings

### 4. User Training

- [ ] Train users on any new authentication methods
- [ ] Update user guides and documentation
- [ ] Provide troubleshooting resources

## Rollback Plan

If you need to rollback to Jira Cloud:

### Quick Rollback

```bash
# Restore Cloud configuration
cp config.yaml.cloud.backup config.yaml
cp .env.cloud.backup .env

# Restart AAA system
make dev
```

### Gradual Rollback

```yaml
# Temporarily switch back to Cloud
jira:
  base_url: "https://yourcompany.atlassian.net"
  auth_type: "api_token"
  email: "user@yourcompany.com"
  api_token: "your-cloud-api-token"
  deployment_type: "cloud"
```

## Migration Checklist

### Pre-Migration
- [ ] Backup current configuration
- [ ] Gather Data Center information
- [ ] Create Personal Access Token
- [ ] Verify network access
- [ ] Test Data Center connectivity

### Migration
- [ ] Update base URL
- [ ] Change authentication method
- [ ] Configure network settings
- [ ] Test connection
- [ ] Verify ticket fetching
- [ ] Test full workflow

### Post-Migration
- [ ] Monitor performance
- [ ] Update documentation
- [ ] Train users
- [ ] Schedule PAT rotation
- [ ] Plan regular reviews

## Support and Resources

### Internal Resources
- Contact your Jira administrator for Data Center specific information
- Review your organization's network and security policies
- Check internal documentation for proxy and SSL configurations

### External Resources
- [Jira Data Center Documentation](https://confluence.atlassian.com/enterprise/)
- [Personal Access Tokens Guide](https://confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html)
- [Jira REST API Documentation](https://docs.atlassian.com/software/jira/docs/api/REST/)

### Getting Help
If you encounter issues during migration:
1. Check the troubleshooting guide
2. Review system logs for detailed error information
3. Contact your system administrator
4. Consult Atlassian documentation
5. Reach out to support if needed

This migration guide should help you successfully transition from Jira Cloud to Data Center. Take your time with each step and don't hesitate to seek help if you encounter any issues.