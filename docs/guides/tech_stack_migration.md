# Migration Guide: Enhanced Technology Stack Generation

## Overview

This guide helps users migrate from the previous technology stack generation system to the Enhanced Technology Stack Generation system. The new system provides improved context awareness, intelligent catalog management, and better technology prioritization.

## What's Changed

### Major Improvements

1. **Context-Aware Technology Extraction**
   - Explicit technology mentions are now properly recognized and prioritized
   - Cloud ecosystem consistency is enforced
   - Technology aliases and abbreviations are resolved automatically

2. **Intelligent Catalog Management**
   - Automatic addition of missing technologies
   - Fuzzy matching for technology lookup
   - Pending review workflow for new technologies

3. **Enhanced LLM Prompting**
   - Structured prompts that prioritize explicit technologies
   - Reasoning requirements for technology selections
   - Improved conflict resolution logic

4. **Comprehensive Validation**
   - Technology compatibility checking
   - Ecosystem consistency validation
   - License and compliance verification

### Breaking Changes

1. **API Response Format Changes**
   - Technology stack responses now include confidence scores and reasoning
   - Validation results are included in generation responses
   - New metadata fields added to technology entries

2. **Configuration Changes**
   - New configuration sections for enhanced features
   - Updated service registration requirements
   - Modified logging configuration

3. **Database Schema Updates**
   - New fields added to technology catalog entries
   - Additional tables for pending review workflow
   - Updated indexes for improved performance

## Pre-Migration Checklist

### System Requirements

- [ ] Python 3.10+ installed
- [ ] Updated dependencies from `requirements.txt`
- [ ] Database backup completed
- [ ] Configuration files reviewed
- [ ] Existing patterns and catalogs backed up

### Backup Procedures

```bash
# Backup existing catalog
python -m app.cli.catalog_manager export --output backup_catalog_$(date +%Y%m%d).json

# Backup existing patterns
cp -r data/patterns/ backup_patterns_$(date +%Y%m%d)/

# Backup database
python scripts/backup_database.py --output backup_db_$(date +%Y%m%d).sql

# Backup configuration
cp -r config/ backup_config_$(date +%Y%m%d)/
```

### Dependency Updates

```bash
# Update Python dependencies
pip install -r requirements.txt

# Verify new dependencies
python -c "
from app.services.requirement_parsing.enhanced_parser import EnhancedRequirementParser
from app.services.catalog.intelligent_manager import IntelligentCatalogManager
print('New dependencies loaded successfully')
"
```

## Migration Steps

### Step 1: Update Configuration

#### 1.1 Update Service Configuration

**Old Configuration (`config/services.yaml`):**
```yaml
tech_stack_generation:
  enabled: true
  llm_provider: openai
  catalog_path: data/technologies.json
```

**New Configuration:**
```yaml
tech_stack_generation:
  enabled: true
  enhanced_parsing: true
  context_extraction: true
  intelligent_catalog: true
  compatibility_validation: true
  
  # Priority weights for technology selection
  priority_weights:
    explicit: 1.0
    contextual: 0.8
    pattern: 0.6
    generic: 0.4
  
  # Confidence thresholds
  confidence_thresholds:
    extraction: 0.7
    inclusion: 0.7
    validation: 0.8

catalog_management:
  auto_add_enabled: true
  pending_review: true
  fuzzy_matching: true
  confidence_threshold: 0.7
  
llm_integration:
  provider: openai
  model: gpt-4
  temperature: 0.1
  max_tokens: 2000
  context_aware_prompts: true
```

#### 1.2 Update Environment Variables

**Add New Environment Variables:**
```bash
# Technology extraction settings
export TECH_EXTRACTION_CONFIDENCE_THRESHOLD=0.7
export EXPLICIT_TECH_INCLUSION_RATE=0.7
export CATALOG_AUTO_ADD_ENABLED=true

# Enhanced logging
export TECH_STACK_DEBUG=false
export TECH_EXTRACTION_DEBUG=false
export LLM_INTEGRATION_DEBUG=false

# Catalog management
export CATALOG_PENDING_REVIEW_ENABLED=true
export CATALOG_FUZZY_MATCH_THRESHOLD=0.8
```

### Step 2: Migrate Technology Catalog

#### 2.1 Run Catalog Migration Script

```bash
# Run the catalog migration script
python scripts/migrate_catalog_entries.py \
  --source data/technologies.json \
  --output data/technologies_migrated.json \
  --add-missing-fields \
  --validate

# Backup original and replace
mv data/technologies.json data/technologies_backup.json
mv data/technologies_migrated.json data/technologies.json
```

#### 2.2 Validate Migrated Catalog

```bash
# Validate catalog structure
python -m app.cli.catalog_manager validate --comprehensive

# Check for missing integrations
python -m app.cli.catalog_manager validate-integrations

# Fix any issues found
python -m app.cli.catalog_manager fix-metadata --auto
```

#### 2.3 Update Technology Entries

The migration script adds new fields to existing technology entries:

**New Fields Added:**
- `aliases` - List of alternative names
- `integrates_with` - List of compatible technologies
- `alternatives` - List of alternative technologies
- `ecosystem` - Cloud provider or ecosystem classification
- `auto_generated` - Whether entry was auto-generated
- `pending_review` - Whether entry needs manual review
- `confidence_score` - Confidence in entry accuracy
- `source_context` - Source of the technology entry

**Example Migration:**

**Before:**
```json
{
  "id": "fastapi",
  "name": "FastAPI",
  "category": "web_framework",
  "description": "Modern, fast web framework for building APIs"
}
```

**After:**
```json
{
  "id": "fastapi",
  "name": "FastAPI",
  "category": "web_framework",
  "description": "Modern, fast web framework for building APIs",
  "aliases": ["FastAPI", "Fast API"],
  "integrates_with": ["postgresql", "redis", "sqlalchemy"],
  "alternatives": ["django-rest", "flask-restful"],
  "ecosystem": "open_source",
  "maturity": "stable",
  "license": "MIT",
  "auto_generated": false,
  "pending_review": false,
  "confidence_score": 1.0,
  "source_context": "manual_migration",
  "metadata": {
    "use_cases": ["api_development", "microservices"],
    "deployment_types": ["docker", "kubernetes"],
    "programming_languages": ["python"]
  }
}
```

### Step 3: Update Application Code

#### 3.1 Update Service Registration

**Old Code:**
```python
from app.services.tech_stack_generator import TechStackGenerator

# Simple service registration
service_registry.register('tech_stack_generator', TechStackGenerator())
```

**New Code:**
```python
from app.services.tech_stack_generator import TechStackGenerator
from app.services.requirement_parsing.enhanced_parser import EnhancedRequirementParser
from app.services.catalog.intelligent_manager import IntelligentCatalogManager

# Register enhanced services
service_registry.register('enhanced_requirement_parser', EnhancedRequirementParser())
service_registry.register('intelligent_catalog_manager', IntelligentCatalogManager())
service_registry.register('tech_stack_generator', TechStackGenerator())
```

#### 3.2 Update API Calls

**Old API Usage:**
```python
# Simple generation call
tech_stack = generator.generate_tech_stack(requirements)
```

**New API Usage:**
```python
# Enhanced generation with context
tech_stack = generator.generate_tech_stack(
    requirements=requirements,
    options={
        'include_reasoning': True,
        'confidence_threshold': 0.7,
        'ecosystem_preference': 'aws'
    }
)

# Access new response fields
confidence = tech_stack.metadata.total_confidence
reasoning = tech_stack.technologies[0].reasoning
validation = tech_stack.validation_results
```

#### 3.3 Update Pattern Creation Integration

**Old Integration:**
```python
# Basic tech stack integration
pattern_creator.set_tech_stack(tech_stack.technologies)
```

**New Integration:**
```python
# Enhanced integration with metadata
pattern_creator.set_tech_stack(
    technologies=tech_stack.technologies,
    confidence_scores=tech_stack.get_confidence_scores(),
    validation_results=tech_stack.validation_results,
    ecosystem=tech_stack.metadata.ecosystem_consistency
)
```

### Step 4: Database Migration

#### 4.1 Run Database Schema Updates

```bash
# Run database migration
python manage_schema.py migrate --version enhanced_tech_stack

# Verify migration
python manage_schema.py verify --check-constraints
```

#### 4.2 Update Existing Data

```bash
# Update existing tech stack records
python scripts/update_existing_tech_stacks.py --add-metadata

# Rebuild search indexes
python -m app.cli.catalog_manager rebuild-indexes
```

### Step 5: Test Migration

#### 5.1 Run Migration Tests

```bash
# Run comprehensive migration tests
python -m pytest app/tests/migration/ -v

# Test specific components
python -m pytest app/tests/unit/test_enhanced_requirement_parser.py
python -m pytest app/tests/integration/test_catalog_integration.py
```

#### 5.2 Validate Core Functionality

```bash
# Test technology extraction
python test_requirement_parsing_integration.py

# Test catalog operations
python examples/catalog_management_example.py

# Test end-to-end generation
python test_enhanced_integration.py
```

#### 5.3 Performance Validation

```bash
# Run performance tests
python -m pytest app/tests/performance/test_tech_stack_performance.py

# Compare with baseline
python scripts/performance_comparison.py --baseline backup_performance.json
```

## Post-Migration Tasks

### 1. Catalog Maintenance

#### Review Auto-Generated Entries
```bash
# Review pending technologies
python -m app.cli.catalog_manager review --pending

# Approve high-confidence entries
python -m app.cli.catalog_manager batch-approve --confidence-min 0.8
```

#### Update Integration Mappings
```bash
# Analyze missing integrations
python -m app.cli.catalog_manager analyze-integrations

# Add missing mappings
python -m app.cli.catalog_manager suggest-integrations --auto-add
```

### 2. Configuration Optimization

#### Tune Confidence Thresholds
```yaml
# Start with conservative settings
tech_stack_generation:
  confidence_thresholds:
    extraction: 0.8  # Higher for stricter matching
    inclusion: 0.7   # Standard requirement
    validation: 0.8  # Higher for quality
```

#### Optimize Performance Settings
```yaml
# Performance tuning
performance:
  parallel_processing: true
  max_worker_threads: 4
  cache_enabled: true
  cache_ttl: 3600
```

### 3. Monitoring Setup

#### Enable Enhanced Logging
```yaml
# Enhanced logging configuration
logging:
  tech_stack_generation:
    level: INFO
    include_confidence_scores: true
    include_reasoning: true
    include_validation_results: true
```

#### Set Up Monitoring
```bash
# Start monitoring services
python -m app.monitoring.tech_stack_monitor --start

# Configure alerts
python -m app.monitoring.quality_assurance --setup-alerts
```

## Rollback Procedures

### Emergency Rollback

If issues are encountered, you can rollback to the previous system:

```bash
# Stop enhanced services
python manage_services.py stop --service enhanced_tech_stack

# Restore original catalog
mv data/technologies_backup.json data/technologies.json

# Restore original configuration
cp -r backup_config_YYYYMMDD/* config/

# Restart with original system
python manage_services.py start --service original_tech_stack
```

### Partial Rollback

To disable specific enhanced features while keeping others:

```yaml
# Disable specific features
tech_stack_generation:
  enhanced_parsing: false      # Disable enhanced parsing
  context_extraction: true     # Keep context extraction
  intelligent_catalog: false   # Disable auto-catalog
  compatibility_validation: true # Keep validation
```

## Common Migration Issues

### Issue 1: Technology Not Recognized

**Symptoms:** Previously recognized technologies not found in new system

**Solution:**
```bash
# Check if technology exists with different name
python -m app.cli.catalog_manager search "partial_name"

# Add missing aliases
python -m app.cli.catalog_manager add-alias --id "tech-id" --alias "old_name"
```

### Issue 2: Performance Degradation

**Symptoms:** Slower tech stack generation after migration

**Solutions:**
```bash
# Rebuild search indexes
python -m app.cli.catalog_manager rebuild-indexes

# Enable caching
export CATALOG_CACHE_ENABLED=true

# Optimize catalog size
python -m app.cli.catalog_manager optimize --remove-unused
```

### Issue 3: Validation Failures

**Symptoms:** Technologies failing validation that previously passed

**Solutions:**
```bash
# Lower validation thresholds temporarily
export VALIDATION_CONFIDENCE_THRESHOLD=0.6

# Update compatibility rules
python -m app.cli.catalog_manager update-compatibility-rules

# Review and fix catalog inconsistencies
python -m app.cli.catalog_manager fix-inconsistencies
```

## Getting Help

### Migration Support

1. **Check Migration Logs:**
   ```bash
   tail -f logs/migration.log
   ```

2. **Run Diagnostic Tools:**
   ```bash
   python -m app.debug.migration_diagnostics
   ```

3. **Contact Support:**
   - Include migration logs
   - Provide system configuration
   - Describe specific issues encountered

### Resources

- **Migration Examples:** `/examples/migration_examples.py`
- **Test Cases:** `/app/tests/migration/`
- **Troubleshooting:** [Troubleshooting Guide](tech_stack_troubleshooting.md)
- **API Documentation:** [API Reference](../api/tech_stack_generation_api.md)

## Best Practices for Migration

### 1. Gradual Migration

- Migrate in stages (development → staging → production)
- Test each component thoroughly before proceeding
- Keep rollback options available at each stage

### 2. Data Validation

- Validate all migrated data before going live
- Compare results between old and new systems
- Monitor quality metrics during transition

### 3. User Communication

- Notify users of new features and changes
- Provide training on new capabilities
- Collect feedback during migration period

### 4. Performance Monitoring

- Monitor system performance during migration
- Set up alerts for performance degradation
- Optimize configuration based on usage patterns

The migration to the Enhanced Technology Stack Generation system provides significant improvements in accuracy and functionality. Following this guide ensures a smooth transition while maintaining system reliability and performance.