# System Monitoring and Validation Tools

This directory contains comprehensive tools for monitoring system health, validating dependencies, and managing the service registry.

## Available Tools

### 1. Unified System Monitor (`scripts/system_monitor.py`)

A unified CLI interface that provides access to all monitoring tools:

```bash
# Validate all dependencies
python scripts/system_monitor.py dependency-validator validate --verbose

# Inspect a specific service
python scripts/system_monitor.py service-inspector inspect logger --detailed

# Generate health dashboard
python scripts/system_monitor.py health-dashboard dashboard --open

# Check for dependency updates
python scripts/system_monitor.py dependency-notifier check --force

# List configured services
python scripts/system_monitor.py service-manager list-services
```

### 2. Dependency Validator (`scripts/dependency_validator.py`)

Validates system dependencies and generates comprehensive reports:

```bash
# Validate all dependencies
python scripts/dependency_validator.py validate --verbose

# Check service health
python scripts/dependency_validator.py health --service logger

# List registered services
python scripts/dependency_validator.py services

# Generate dependency report
python scripts/dependency_validator.py report --output dependency_report.json

# Install missing dependencies
python scripts/dependency_validator.py install --dry-run
```

**Features:**
- ✅ Validates required and optional dependencies
- 🏥 Checks service health status
- 📋 Lists all registered services with details
- 📄 Generates comprehensive dependency reports
- 📦 Installs missing dependencies automatically
- 💡 Provides actionable recommendations

### 3. Service Inspector (`scripts/service_inspector.py`)

Inspects and analyzes the service registry:

```bash
# Inspect a specific service
python scripts/service_inspector.py inspect logger --detailed

# Analyze dependency chain
python scripts/service_inspector.py analyze logger

# Generate service map
python scripts/service_inspector.py map --format markdown

# Monitor service lifecycle
python scripts/service_inspector.py monitor --service logger

# Debug service issues
python scripts/service_inspector.py debug --service logger
```

**Features:**
- 🔍 Detailed service inspection with metadata
- 🔗 Dependency chain analysis
- 🗺️ Service mapping in multiple formats (JSON, YAML, Markdown)
- 👀 Service lifecycle monitoring
- 🐛 Automated issue detection and recommendations
- 📊 Circular dependency detection

### 4. Health Dashboard (`scripts/health_dashboard.py`)

Web-based dashboard for real-time health monitoring:

```bash
# Check current health status
python scripts/health_dashboard.py check

# Start continuous monitoring
python scripts/health_dashboard.py monitor --interval 30 --duration 3600

# Generate HTML dashboard
python scripts/health_dashboard.py dashboard --output health.html --open

# Export metrics data
python scripts/health_dashboard.py export --format csv --output metrics.csv
```

**Features:**
- 🏥 Real-time service health monitoring
- 📊 Interactive web dashboard with auto-refresh
- 📈 Historical metrics tracking
- 🚨 Alert generation for issues
- 📤 Metrics export in JSON/CSV formats
- ⏱️ Configurable monitoring intervals
- 💚 Service uptime percentage tracking

### 5. Dependency Notifier (`scripts/dependency_notifier.py`)

Monitors dependencies for updates and security vulnerabilities:

```bash
# Check for dependency updates
python scripts/dependency_notifier.py check --force

# Generate update report
python scripts/dependency_notifier.py report --output updates.md

# Send notifications
python scripts/dependency_notifier.py notify --email --slack

# Start continuous monitoring
python scripts/dependency_notifier.py monitor --interval 24

# Show configuration
python scripts/dependency_notifier.py config
```

**Features:**
- 🔍 Automatic dependency update detection
- 🔴 Security vulnerability scanning
- 📄 Comprehensive update reports
- 📧 Email and Slack notifications
- ⏰ Continuous monitoring with configurable intervals
- 🎯 Configurable notification preferences
- 📊 Update categorization (major, minor, patch, security)

### 6. Service Manager (`manage_services.py`)

Manages service configuration and startup validation:

```bash
# List configured services
python manage_services.py list-services

# List dependencies by type
python manage_services.py list-deps --type required

# Validate all dependencies
python manage_services.py validate-deps --include-dev

# Show dependency groups
python manage_services.py show-groups

# Run startup validation
python manage_services.py startup-validation

# Install dependency group
python manage_services.py install minimal --dry-run
```

**Features:**
- 📋 Service configuration management
- 🔍 Dependency validation and reporting
- 📦 Dependency group management
- 🚀 Complete startup validation
- 📥 Automated dependency installation

## Quick Start Guide

### 1. Basic Health Check

```bash
# Quick system health overview
python scripts/system_monitor.py dependency-validator validate
python scripts/system_monitor.py dependency-validator health
```

### 2. Generate Comprehensive Report

```bash
# Generate detailed system report
python scripts/system_monitor.py dependency-validator report
python scripts/system_monitor.py service-inspector map --format markdown
```

### 3. Start Real-time Monitoring

```bash
# Start health dashboard (opens in browser)
python scripts/system_monitor.py health-dashboard dashboard --open

# Start continuous dependency monitoring
python scripts/system_monitor.py dependency-notifier monitor --interval 24
```

### 4. Debug Service Issues

```bash
# Debug all services
python scripts/system_monitor.py service-inspector debug

# Inspect specific service
python scripts/system_monitor.py service-inspector inspect <service-name> --detailed
```

## Configuration

### Health Dashboard Configuration

The health dashboard can be configured by modifying the `HealthMonitor` class initialization:

```python
monitor = HealthMonitor(check_interval=30)  # Check every 30 seconds
```

### Dependency Notifier Configuration

Create a `NotificationConfig` to customize notification behavior:

```python
config = NotificationConfig(
    email_enabled=True,
    email_recipients=["admin@example.com"],
    slack_enabled=True,
    slack_webhook="https://hooks.slack.com/...",
    notify_security_updates=True,
    notify_major_updates=True,
    notify_minor_updates=False,
    check_interval_hours=24
)
```

## Output Files

All tools generate output files in organized locations:

- **Reports:** `docs/monitoring/`
- **Dashboards:** `docs/monitoring/`
- **Metrics:** `docs/monitoring/`
- **Notifications:** `docs/monitoring/`
- **Service Maps:** `docs/architecture/dependencies/`

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: System Health Check
on:
  schedule:
    - cron: '0 8 * * *'  # Daily at 8 AM
  workflow_dispatch:

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Validate dependencies
        run: python scripts/system_monitor.py dependency-validator validate
      - name: Check service health
        run: python scripts/system_monitor.py dependency-validator health
      - name: Generate report
        run: python scripts/system_monitor.py dependency-validator report
      - name: Check for updates
        run: python scripts/system_monitor.py dependency-notifier check
```

### Pre-commit Hook

```bash
#!/bin/sh
# .git/hooks/pre-commit
python scripts/system_monitor.py dependency-validator validate --verbose
if [ $? -ne 0 ]; then
    echo "❌ Dependency validation failed"
    exit 1
fi
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure project root is in Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **Permission Errors**
   ```bash
   # Make scripts executable
   chmod +x scripts/*.py
   ```

3. **Missing Dependencies**
   ```bash
   # Install optional monitoring dependencies
   pip install psutil requests pyyaml
   ```

### Debug Mode

Enable verbose output for debugging:

```bash
python scripts/system_monitor.py dependency-validator validate --verbose
python scripts/system_monitor.py service-inspector inspect <service> --detailed
```

## Best Practices

1. **Regular Monitoring**
   - Run dependency validation daily
   - Monitor service health continuously
   - Check for updates weekly

2. **Alert Configuration**
   - Enable notifications for security updates
   - Set appropriate thresholds for health alerts
   - Configure multiple notification channels

3. **Report Generation**
   - Generate reports before deployments
   - Archive reports for compliance
   - Share reports with team members

4. **Proactive Maintenance**
   - Address warnings before they become errors
   - Keep dependencies up to date
   - Monitor resource usage trends

## Support

For issues or questions about the monitoring tools:

1. Check the troubleshooting section above
2. Review the tool-specific help: `python scripts/<tool>.py --help`
3. Examine log files in `docs/monitoring/`
4. Run tools in verbose mode for detailed output

## Contributing

When adding new monitoring capabilities:

1. Follow the existing CLI pattern
2. Add comprehensive error handling
3. Include progress indicators and clear output
4. Generate structured output files
5. Update this documentation
6. Add appropriate tests