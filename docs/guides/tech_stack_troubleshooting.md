# Technology Stack Generation Troubleshooting Guide

## Overview

This guide helps diagnose and resolve common issues with the Enhanced Technology Stack Generation system. It covers problems ranging from technology extraction failures to unexpected recommendations.

## Quick Diagnosis

### System Health Check

```bash
# Run comprehensive system health check
python -m app.cli.catalog_manager health-check

# Check specific components
python -m app.cli.catalog_manager check --component tech_extraction
python -m app.cli.catalog_manager check --component llm_integration
python -m app.cli.catalog_manager check --component catalog_consistency
```

### Common Symptoms and Quick Fixes

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| Technologies not recognized | Missing from catalog | Add to catalog or use aliases |
| Wrong ecosystem selection | Unclear context | Specify cloud provider explicitly |
| Generic recommendations | Vague requirements | Provide specific technology names |
| Conflicting technologies | Ecosystem mismatch | Review ecosystem consistency |
| Low confidence scores | Ambiguous requirements | Add more context and details |

## Technology Extraction Issues

### Problem: Technologies Not Recognized

**Symptoms:**
- Explicitly mentioned technologies not included in recommendations
- System suggests generic alternatives instead of specific technologies
- Low extraction confidence scores

**Diagnosis:**
```bash
# Check if technology exists in catalog
python -m app.cli.catalog_manager search "Technology Name"

# Test technology extraction
python -c "
from app.services.requirement_parsing.enhanced_parser import EnhancedRequirementParser
parser = EnhancedRequirementParser()
result = parser.extract_explicit_technologies('Your requirement text here')
print(result)
"
```

**Solutions:**

1. **Add Missing Technology to Catalog:**
```bash
python -m app.cli.catalog_manager add --name "Technology Name" --category "appropriate_category"
```

2. **Use Recognized Aliases:**
```python
# Check available aliases
python -m app.cli.catalog_manager aliases "partial_name"
```

3. **Improve Requirement Phrasing:**
```
❌ "Use Connect for calls"
✅ "Use Amazon Connect for call handling"
```

### Problem: Incorrect Technology Extraction

**Symptoms:**
- Wrong technologies extracted from requirements
- Misinterpretation of technology names
- False positive extractions

**Diagnosis:**
```bash
# Enable debug logging
export TECH_EXTRACTION_DEBUG=true

# Test extraction with debug output
python -c "
from app.services.requirement_parsing.enhanced_parser import EnhancedRequirementParser
parser = EnhancedRequirementParser()
result = parser.parse_requirements({'description': 'Your text'})
print('Extracted:', result.explicit_technologies)
"
```

**Solutions:**

1. **Update Technology Aliases:**
```bash
# Add specific aliases to prevent mismatching
python -m app.cli.catalog_manager add-alias --id "correct-tech" --alias "ambiguous-term"
```

2. **Improve Context Clues:**
```
❌ "Use Lambda functions"
✅ "Use AWS Lambda functions for serverless compute"
```

3. **Adjust Confidence Thresholds:**
```python
# In configuration
TECH_EXTRACTION_CONFIDENCE_THRESHOLD = 0.8  # Increase for stricter matching
```

## Context and Prioritization Issues

### Problem: Wrong Technology Priorities

**Symptoms:**
- Explicit technologies ranked lower than generic ones
- Pattern-based selections override specific mentions
- Inconsistent prioritization across similar requirements

**Diagnosis:**
```bash
# Check context extraction
python -c "
from app.services.requirement_parsing.context_extractor import TechnologyContextExtractor
extractor = TechnologyContextExtractor()
# Test with your requirements
"
```

**Solutions:**

1. **Verify Priority Weights:**
```yaml
# config/services.yaml
tech_stack_generation:
  priority_weights:
    explicit: 1.0
    contextual: 0.8
    pattern: 0.6
    generic: 0.4
```

2. **Improve Requirement Structure:**
```
✅ Good Structure:
"Primary Technologies (Required):
- Amazon Connect for call handling
- AWS Lambda for processing

Secondary Technologies (Preferred):
- Amazon S3 for storage
- Amazon RDS for database"
```

3. **Use Context Prioritization:**
```python
from app.services.requirement_parsing.context_prioritizer import ContextPrioritizer
prioritizer = ContextPrioritizer()
prioritized = prioritizer.prioritize_context(requirements)
```

### Problem: Ecosystem Inconsistency

**Symptoms:**
- Mixed cloud providers in recommendations
- Incompatible technology combinations
- Ecosystem conflicts not resolved

**Diagnosis:**
```bash
# Check ecosystem consistency
python -c "
from app.services.validation.compatibility_validator import TechnologyCompatibilityValidator
validator = TechnologyCompatibilityValidator()
result = validator.check_ecosystem_consistency(['tech1', 'tech2', 'tech3'])
print(result)
"
```

**Solutions:**

1. **Specify Ecosystem Preference:**
```
"This is an AWS-based solution requiring..."
"Azure cloud implementation using..."
"Google Cloud Platform deployment with..."
```

2. **Update Ecosystem Classifications:**
```bash
python -m app.cli.catalog_manager update --id "tech-id" --field "ecosystem" --value "aws"
```

3. **Configure Ecosystem Rules:**
```yaml
# config/validation.yaml
ecosystem_rules:
  aws:
    preferred_alternatives:
      database: ["amazon-rds", "amazon-dynamodb"]
      compute: ["aws-lambda", "amazon-ec2"]
```

## LLM Integration Issues

### Problem: Poor LLM Responses

**Symptoms:**
- LLM ignores explicit technology requirements
- Generic or irrelevant technology suggestions
- Inconsistent reasoning in responses

**Diagnosis:**
```bash
# Enable LLM debug logging
export LLM_DEBUG_LOGGING=true

# Test prompt generation
python -c "
from app.services.context_aware_prompt_generator import ContextAwarePromptGenerator
generator = ContextAwarePromptGenerator()
prompt = generator.build_context_aware_prompt(context, catalog)
print('Generated Prompt:', prompt)
"
```

**Solutions:**

1. **Improve Prompt Structure:**
```python
# Ensure explicit technologies are prominently featured
prompt_template = '''
CRITICAL: You MUST include these explicitly mentioned technologies:
{explicit_technologies}

PRIORITY ORDER:
1. Explicit technologies (MUST INCLUDE)
2. Contextual technologies (STRONGLY PREFERRED)
3. Pattern-based suggestions (IF NEEDED)
'''
```

2. **Adjust LLM Parameters:**
```yaml
# config/llm.yaml
llm_settings:
  temperature: 0.1  # Lower for more consistent responses
  max_tokens: 2000
  top_p: 0.9
```

3. **Validate LLM Responses:**
```python
# Add response validation
from app.services.validation.llm_response_validator import LLMResponseValidator
validator = LLMResponseValidator()
validated_response = validator.validate_and_fix(llm_response, requirements)
```

### Problem: LLM Timeout or Errors

**Symptoms:**
- LLM requests timing out
- API rate limit errors
- Connection failures

**Diagnosis:**
```bash
# Check LLM provider status
python -c "
from app.llm.factory import LLMProviderFactory
factory = LLMProviderFactory()
provider = factory.get_provider()
health = provider.health_check()
print('Provider Health:', health)
"
```

**Solutions:**

1. **Configure Retry Logic:**
```yaml
# config/llm.yaml
retry_config:
  max_retries: 3
  backoff_factor: 2
  timeout: 30
```

2. **Implement Fallback Providers:**
```python
# Use multiple providers for reliability
LLM_PROVIDERS = ['openai', 'anthropic', 'bedrock']
```

3. **Optimize Request Size:**
```python
# Reduce prompt size for large catalogs
MAX_CATALOG_ENTRIES_IN_PROMPT = 50
```

## Catalog Management Issues

### Problem: Catalog Inconsistencies

**Symptoms:**
- Duplicate technology entries
- Missing integration mappings
- Inconsistent metadata

**Diagnosis:**
```bash
# Run catalog validation
python -m app.cli.catalog_manager validate --comprehensive

# Check for specific issues
python -m app.cli.catalog_manager check-duplicates
python -m app.cli.catalog_manager validate-integrations
```

**Solutions:**

1. **Fix Duplicates:**
```bash
# Find and merge duplicates
python -m app.cli.catalog_manager find-duplicates
python -m app.cli.catalog_manager merge --primary "tech-a" --duplicate "tech-b"
```

2. **Update Integration Mappings:**
```bash
# Add missing integrations
python -m app.cli.catalog_manager add-integration --from "tech-a" --to "tech-b"

# Validate bidirectional consistency
python -m app.cli.catalog_manager fix-bidirectional-integrations
```

3. **Repair Metadata:**
```bash
# Fix common metadata issues
python -m app.cli.catalog_manager fix-metadata --auto
```

### Problem: Auto-Addition Failures

**Symptoms:**
- New technologies not automatically added
- Pending review queue not processing
- Missing metadata in auto-added entries

**Diagnosis:**
```bash
# Check auto-addition status
python -c "
from app.services.catalog.intelligent_manager import IntelligentCatalogManager
manager = IntelligentCatalogManager()
status = manager.get_auto_addition_status()
print('Auto-addition Status:', status)
"
```

**Solutions:**

1. **Enable Auto-Addition:**
```yaml
# config/catalog.yaml
auto_addition:
  enabled: true
  require_approval: true
  confidence_threshold: 0.7
```

2. **Process Pending Queue:**
```bash
# Review pending technologies
python -m app.cli.catalog_manager review --pending

# Batch approve high-confidence additions
python -m app.cli.catalog_manager batch-approve --confidence-min 0.8
```

3. **Improve Metadata Extraction:**
```python
# Configure metadata extraction
METADATA_EXTRACTION_SOURCES = ['llm_knowledge', 'web_search', 'documentation']
```

## Performance Issues

### Problem: Slow Technology Generation

**Symptoms:**
- Long response times for tech stack generation
- Timeouts during processing
- High memory usage

**Diagnosis:**
```bash
# Run performance profiling
python -m app.tests.performance.test_tech_stack_performance --profile

# Check component performance
python -c "
import time
from app.services.tech_stack_generator import TechStackGenerator

start = time.time()
generator = TechStackGenerator()
result = generator.generate_tech_stack(requirements)
print(f'Generation time: {time.time() - start:.2f}s')
"
```

**Solutions:**

1. **Optimize Catalog Queries:**
```python
# Use indexed lookups
from app.services.catalog.intelligent_manager import IntelligentCatalogManager
manager = IntelligentCatalogManager()
manager.build_search_index()  # Build search index for faster lookups
```

2. **Cache Frequently Used Data:**
```yaml
# config/caching.yaml
cache_settings:
  catalog_cache_ttl: 3600
  extraction_cache_ttl: 1800
  llm_response_cache_ttl: 7200
```

3. **Parallel Processing:**
```python
# Enable parallel processing for large requirements
PARALLEL_PROCESSING_ENABLED = True
MAX_WORKER_THREADS = 4
```

### Problem: High Memory Usage

**Symptoms:**
- Memory usage growing over time
- Out of memory errors
- Slow garbage collection

**Solutions:**

1. **Implement Memory Management:**
```python
# Clear caches periodically
from app.utils.memory_manager import MemoryManager
memory_manager = MemoryManager()
memory_manager.cleanup_caches()
```

2. **Optimize Data Structures:**
```python
# Use generators for large datasets
def process_large_catalog():
    for entry in catalog_manager.iter_entries():
        yield process_entry(entry)
```

3. **Configure Memory Limits:**
```yaml
# config/performance.yaml
memory_limits:
  max_catalog_size_mb: 100
  max_cache_size_mb: 50
  gc_threshold: 0.8
```

## Validation and Quality Issues

### Problem: Technology Compatibility Conflicts

**Symptoms:**
- Incompatible technologies recommended together
- License conflicts in recommendations
- Performance mismatches

**Diagnosis:**
```bash
# Test compatibility validation
python -c "
from app.services.validation.compatibility_validator import TechnologyCompatibilityValidator
validator = TechnologyCompatibilityValidator()
result = validator.validate_stack(['tech1', 'tech2', 'tech3'], context)
print('Validation Result:', result)
"
```

**Solutions:**

1. **Update Compatibility Rules:**
```yaml
# config/compatibility.yaml
compatibility_rules:
  conflicts:
    - ['mysql', 'postgresql']  # Don't recommend both databases
    - ['aws-lambda', 'azure-functions']  # Don't mix cloud providers
  
  requirements:
    'kubernetes':
      requires: ['docker']
      conflicts: ['aws-lambda']
```

2. **Implement Custom Validation:**
```python
# Add domain-specific validation rules
class CustomCompatibilityValidator(TechnologyCompatibilityValidator):
    def validate_domain_specific(self, tech_stack, domain):
        # Custom validation logic
        pass
```

3. **Configure Conflict Resolution:**
```python
# Priority-based conflict resolution
CONFLICT_RESOLUTION_STRATEGY = 'priority_based'  # or 'user_choice', 'automatic'
```

## Debugging Tools and Techniques

### Enable Debug Logging

```bash
# Enable comprehensive debug logging
export TECH_STACK_DEBUG=true
export LOG_LEVEL=DEBUG

# Component-specific debugging
export TECH_EXTRACTION_DEBUG=true
export LLM_INTEGRATION_DEBUG=true
export CATALOG_DEBUG=true
```

### Debug Commands

```bash
# Test individual components
python -m app.debug.test_tech_extraction --requirements "your requirements"
python -m app.debug.test_context_extraction --text "your text"
python -m app.debug.test_llm_integration --prompt "your prompt"

# Trace generation process
python -m app.debug.trace_generation --requirements-file requirements.json
```

### Performance Profiling

```bash
# Profile tech stack generation
python -m cProfile -o profile.stats -m app.services.tech_stack_generator

# Analyze profile results
python -c "
import pstats
stats = pstats.Stats('profile.stats')
stats.sort_stats('cumulative').print_stats(20)
"
```

### Memory Profiling

```bash
# Install memory profiler
pip install memory-profiler

# Profile memory usage
python -m memory_profiler app/services/tech_stack_generator.py
```

## Getting Additional Help

### Log Analysis

**Key Log Locations:**
- `/logs/tech_stack_generation.log` - Main generation logs
- `/logs/catalog_operations.log` - Catalog management logs
- `/logs/llm_interactions.log` - LLM request/response logs
- `/logs/validation_errors.log` - Validation failure logs

**Log Analysis Commands:**
```bash
# Search for specific errors
grep "ERROR" /logs/tech_stack_generation.log | tail -20

# Analyze performance patterns
grep "generation_time" /logs/tech_stack_generation.log | awk '{print $NF}' | sort -n
```

### Support Information

When contacting support, include:

1. **System Information:**
   - Python version
   - System configuration
   - Installed dependencies

2. **Error Details:**
   - Complete error messages
   - Stack traces
   - Relevant log entries

3. **Reproduction Steps:**
   - Input requirements
   - Configuration settings
   - Expected vs actual behavior

4. **Environment Context:**
   - Deployment environment
   - Resource constraints
   - Integration requirements

### Community Resources

- **Documentation**: `/docs/` directory
- **Examples**: `/examples/` directory
- **Test Cases**: `/app/tests/` directory
- **Issue Tracker**: GitHub issues
- **Discussion Forum**: Community discussions

For complex issues requiring code changes, see the [Development Guide](../development/DEVELOPMENT_GUIDE.md).