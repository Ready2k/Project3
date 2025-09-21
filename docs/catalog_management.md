# Technology Catalog Management Guide

This guide provides comprehensive documentation for managing the technology catalog using the CLI tools and admin interfaces.

## Overview

The technology catalog management system provides:

- **CLI Tools**: Command-line utilities for catalog operations
- **Review Queue Management**: Workflow for approving/rejecting technologies
- **Bulk Operations**: Import/export capabilities for maintenance
- **Health Monitoring**: Statistics and quality dashboards
- **Automated Workflows**: Auto-addition and validation systems

## Quick Start

### Installation and Setup

The catalog management tools are part of the main application. No additional installation is required.

```bash
# Navigate to project directory
cd Project3

# Verify tools are available
python -m app.cli.main --help
```

### Basic Operations

```bash
# Show catalog overview
python -m app.cli.main dashboard overview

# List all technologies
python -m app.cli.main catalog list

# Search for technologies
python -m app.cli.main catalog search "fastapi"

# Validate catalog
python -m app.cli.main catalog validate
```

## CLI Tools Reference

### 1. Catalog Manager (`catalog`)

Basic catalog management operations.

#### Adding Technologies

```bash
# Add a new technology
python -m app.cli.main catalog add \
  --name "FastAPI" \
  --category "frameworks" \
  --description "Modern, fast web framework for building APIs with Python" \
  --ecosystem "open_source" \
  --maturity "stable" \
  --license "MIT" \
  --aliases "fast-api" "fast_api" \
  --integrates-with "python" "pydantic" "uvicorn" \
  --alternatives "django" "flask" \
  --tags "python" "api" "async" "web" \
  --use-cases "rest_api" "microservices" "web_backend"
```

#### Updating Technologies

```bash
# Update basic information
python -m app.cli.main catalog update fastapi \
  --description "Updated description" \
  --maturity "mature"

# Add additional metadata
python -m app.cli.main catalog update fastapi \
  --add-alias "fastapi-framework" \
  --add-integration "sqlalchemy" \
  --add-tag "production-ready"
```

#### Listing and Searching

```bash
# List all technologies
python -m app.cli.main catalog list

# List by category
python -m app.cli.main catalog list --category "frameworks"

# List by ecosystem
python -m app.cli.main catalog list --ecosystem "aws"

# List pending review only
python -m app.cli.main catalog list --pending-review

# Search technologies
python -m app.cli.main catalog search "fast" --limit 5

# Show detailed technology information
python -m app.cli.main catalog show fastapi
```

#### Validation

```bash
# Basic validation
python -m app.cli.main catalog validate

# Detailed validation with individual entry checks
python -m app.cli.main catalog validate --detailed

# Show catalog statistics
python -m app.cli.main catalog stats
```

#### Deleting Technologies

```bash
# Delete a technology (with confirmation)
python -m app.cli.main catalog delete old_tech_id

# Force delete without confirmation
python -m app.cli.main catalog delete old_tech_id --force
```

### 2. Review Manager (`review`)

Manage the technology review queue for auto-generated entries.

#### Listing Pending Reviews

```bash
# List all pending reviews
python -m app.cli.main review list

# List with detailed information
python -m app.cli.main review list --verbose

# Show detailed review information for a technology
python -m app.cli.main review show tech_id
```

#### Reviewing Technologies

```bash
# Approve a technology
python -m app.cli.main review approve tech_id \
  --reviewer "john.doe" \
  --notes "Verified and looks good"

# Reject a technology
python -m app.cli.main review reject tech_id \
  --reviewer "jane.smith" \
  --notes "Not a real technology, appears to be a typo"

# Request updates to a technology
python -m app.cli.main review request-update tech_id \
  --reviewer "admin" \
  --notes "Please add more detailed description and use cases"
```

#### Batch Operations

```bash
# Batch approve high-confidence auto-generated entries
python -m app.cli.main review batch-approve \
  --reviewer "admin" \
  --min-confidence 0.8 \
  --auto-generated-only \
  --valid-only

# Batch approve all entries in a specific category
python -m app.cli.main review batch-approve \
  --reviewer "admin" \
  --category "frameworks" \
  --valid-only
```

#### Review Statistics

```bash
# Show review queue statistics
python -m app.cli.main review stats
```

### 3. Bulk Operations (`bulk`)

Import and export catalog data in various formats.

#### Exporting Data

```bash
# Export entire catalog to JSON
python -m app.cli.main bulk export catalog.json

# Export to CSV format
python -m app.cli.main bulk export catalog.csv --format csv

# Export specific ecosystem
python -m app.cli.main bulk export aws_techs.json --ecosystem aws

# Export specific category
python -m app.cli.main bulk export frameworks.yaml --category frameworks --format yaml

# Export only pending review technologies
python -m app.cli.main bulk export pending.json --pending-only

# Export minimal fields only
python -m app.cli.main bulk export minimal_catalog.json --minimal
```

#### Importing Data

```bash
# Import from JSON file
python -m app.cli.main bulk import new_technologies.json

# Import and update existing entries
python -m app.cli.main bulk import updated_catalog.json --update-existing

# Import from CSV with verbose output
python -m app.cli.main bulk import technologies.csv --verbose

# Import ignoring validation errors
python -m app.cli.main bulk import problematic_data.json --ignore-validation
```

#### Backup and Restore

```bash
# Create a backup
python -m app.cli.main bulk backup

# Create backup with specific filename
python -m app.cli.main bulk backup --output catalog_backup_20231201.json

# Restore from backup
python -m app.cli.main bulk restore catalog_backup_20231201.json

# Force restore without confirmation
python -m app.cli.main bulk restore catalog_backup_20231201.json --force
```

### 4. Dashboard (`dashboard`)

Monitor catalog health and statistics.

#### Overview Dashboard

```bash
# Show comprehensive overview
python -m app.cli.main dashboard overview
```

This displays:
- Total technologies count
- Pending review count
- Health score and status
- Distribution by ecosystem, category, and maturity
- Recent activity
- Quality metrics
- Actionable recommendations

#### Health Report

```bash
# Show detailed health report
python -m app.cli.main dashboard health
```

This provides:
- Overall health score breakdown
- Health component scores (completeness, consistency, freshness, quality)
- Critical issues, warnings, and suggestions
- Validation summary

#### Trends and Analytics

```bash
# Show trends and analytics
python -m app.cli.main dashboard trends
```

This includes:
- Growth trends over time
- Usage patterns (most mentioned/selected technologies)
- Review queue trends
- Technology popularity rankings

#### Quality Report

```bash
# Show detailed quality report
python -m app.cli.main dashboard quality
```

This covers:
- Completeness metrics
- Validation metrics
- Review metrics
- Top quality issues by technology

## Catalog Management Workflows

### 1. Daily Maintenance Workflow

```bash
# 1. Check catalog health
python -m app.cli.main dashboard overview

# 2. Review pending technologies
python -m app.cli.main review list --verbose

# 3. Approve high-confidence entries
python -m app.cli.main review batch-approve \
  --reviewer "daily_admin" \
  --min-confidence 0.9 \
  --auto-generated-only \
  --valid-only

# 4. Validate catalog consistency
python -m app.cli.main catalog validate --detailed

# 5. Check for quality issues
python -m app.cli.main dashboard quality
```

### 2. Weekly Quality Review

```bash
# 1. Generate comprehensive health report
python -m app.cli.main dashboard health

# 2. Review technologies with validation errors
python -m app.cli.main catalog list --verbose | grep "ERRORS"

# 3. Update technologies with missing information
# (Manual process based on quality report findings)

# 4. Create weekly backup
python -m app.cli.main bulk backup --output "weekly_backup_$(date +%Y%m%d).json"

# 5. Review trends and usage patterns
python -m app.cli.main dashboard trends
```

### 3. Bulk Import Workflow

```bash
# 1. Validate import file format
python -m app.cli.main bulk import new_data.json --verbose

# 2. Create backup before import
python -m app.cli.main bulk backup --output "pre_import_backup.json"

# 3. Perform import with validation
python -m app.cli.main bulk import new_data.json --update-existing --verbose

# 4. Validate catalog after import
python -m app.cli.main catalog validate --detailed

# 5. Review newly imported technologies
python -m app.cli.main review list --verbose
```

### 4. Catalog Cleanup Workflow

```bash
# 1. Identify quality issues
python -m app.cli.main dashboard quality

# 2. Find technologies with validation errors
python -m app.cli.main catalog validate --detailed

# 3. Review and fix individual technologies
python -m app.cli.main catalog show problematic_tech_id
python -m app.cli.main catalog update problematic_tech_id --description "Updated description"

# 4. Remove duplicate or invalid entries
python -m app.cli.main catalog delete invalid_tech_id

# 5. Verify improvements
python -m app.cli.main dashboard health
```

## Best Practices

### Technology Entry Guidelines

1. **Naming Conventions**
   - Use official technology names as canonical names
   - Include common aliases and abbreviations
   - Be consistent with capitalization

2. **Descriptions**
   - Provide clear, concise descriptions (50+ characters)
   - Include key features and use cases
   - Avoid marketing language

3. **Categorization**
   - Use consistent category names
   - Assign appropriate ecosystem (AWS, Azure, GCP, etc.)
   - Set realistic maturity levels

4. **Relationships**
   - Include integration technologies
   - List viable alternatives
   - Add relevant tags and use cases

### Review Process Guidelines

1. **Auto-Generated Entries**
   - Review entries with confidence < 0.8 carefully
   - Verify technology names and descriptions
   - Check for duplicates before approving

2. **Batch Approvals**
   - Use conservative confidence thresholds (≥0.9)
   - Always include validation checks
   - Review batch results after approval

3. **Quality Standards**
   - Ensure all required fields are populated
   - Verify integration and alternative lists
   - Check for consistent ecosystem assignment

### Maintenance Guidelines

1. **Regular Monitoring**
   - Check dashboard daily for health status
   - Review pending queue weekly
   - Perform detailed quality reviews monthly

2. **Backup Strategy**
   - Create daily automated backups
   - Maintain weekly manual backups
   - Test restore procedures regularly

3. **Performance Optimization**
   - Monitor catalog size and growth
   - Clean up rejected or obsolete entries
   - Optimize search indexes regularly

## Troubleshooting

### Common Issues

1. **Validation Errors**
   ```bash
   # Check specific validation issues
   python -m app.cli.main catalog validate --detailed
   
   # Fix individual entries
   python -m app.cli.main catalog update tech_id --description "Fixed description"
   ```

2. **Import Failures**
   ```bash
   # Check import file format
   python -m app.cli.main bulk import data.json --verbose
   
   # Import with validation disabled (use carefully)
   python -m app.cli.main bulk import data.json --ignore-validation
   ```

3. **Performance Issues**
   ```bash
   # Check catalog statistics
   python -m app.cli.main catalog stats
   
   # Monitor health metrics
   python -m app.cli.main dashboard health
   ```

4. **Duplicate Entries**
   ```bash
   # Search for potential duplicates
   python -m app.cli.main catalog search "technology_name"
   
   # Validate catalog consistency
   python -m app.cli.main catalog validate
   ```

### Recovery Procedures

1. **Restore from Backup**
   ```bash
   python -m app.cli.main bulk restore backup_file.json --force
   ```

2. **Rebuild Indexes**
   ```bash
   # Restart the application to rebuild indexes
   # Or use the validation command to check consistency
   python -m app.cli.main catalog validate
   ```

3. **Clean Corrupted Data**
   ```bash
   # Export clean data
   python -m app.cli.main bulk export clean_catalog.json --approved-only
   
   # Restore from clean export
   python -m app.cli.main bulk restore clean_catalog.json --force
   ```

## API Integration

The catalog management tools can be integrated into automated workflows:

### Python Integration

```python
from app.services.catalog.intelligent_manager import IntelligentCatalogManager
from app.services.catalog.models import TechEntry, EcosystemType

# Initialize manager
manager = IntelligentCatalogManager()

# Add technology programmatically
tech = TechEntry(
    id="new_tech",
    name="New Technology",
    category="frameworks",
    description="A new technology for our catalog"
)
manager.technologies[tech.id] = tech
manager._save_catalog()

# Search and validate
result = manager.lookup_technology("fastapi")
validation = manager.validate_catalog_consistency()
```

### Automation Scripts

```bash
#!/bin/bash
# Daily maintenance script

# Check health
HEALTH_OUTPUT=$(python -m app.cli.main dashboard health)
echo "$HEALTH_OUTPUT"

# Auto-approve high confidence entries
python -m app.cli.main review batch-approve \
  --reviewer "automation" \
  --min-confidence 0.95 \
  --auto-generated-only \
  --valid-only \
  --force

# Create backup
python -m app.cli.main bulk backup --output "daily_backup_$(date +%Y%m%d).json"

# Send health report via email (implement as needed)
echo "$HEALTH_OUTPUT" | mail -s "Daily Catalog Health Report" admin@company.com
```

## Configuration

### Environment Variables

- `CATALOG_PATH`: Path to the technology catalog file (default: `Project3/data/technologies.json`)
- `BACKUP_PATH`: Default path for backups (default: current directory)
- `LOG_LEVEL`: Logging level for catalog operations (default: INFO)

### Customization

The CLI tools can be customized by modifying the configuration files:

- `Project3/config/services.yaml`: Service configuration
- `Project3/config/dependencies.yaml`: Dependency definitions

## Support and Maintenance

For issues or questions:

1. Check the troubleshooting section above
2. Review the application logs for detailed error information
3. Use the validation tools to identify specific issues
4. Consult the API documentation for programmatic access

Regular maintenance tasks should be automated using the provided CLI tools and integrated into your deployment pipeline.