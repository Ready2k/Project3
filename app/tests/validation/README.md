# Tech Stack Generation Validation Framework

This comprehensive validation framework ensures the quality, performance, and accuracy of the tech stack generation system. It includes regression tests, performance benchmarks, catalog validation, and automated quality assurance.

## Overview

The validation framework consists of several test suites:

1. **Comprehensive Tech Stack Generation Tests** - End-to-end validation and regression tests
2. **Performance Benchmarks** - Performance and scalability testing
3. **Catalog Consistency Tests** - Technology catalog validation and quality assurance
4. **Test Data Sets** - Comprehensive test data for various scenarios
5. **Automated Test Runner** - Orchestrates all tests and generates reports

## Quick Start

### Run All Validation Tests

```bash
# Run complete validation suite
python -m app.tests.validation.test_runner

# Or using make (if configured)
make validate-tech-stack
```

### Run Specific Test Suites

```bash
# Run only regression tests
python -m pytest app/tests/validation/test_tech_stack_generation_comprehensive.py -v

# Run only performance tests
python -m pytest app/tests/performance/test_tech_stack_performance.py -v

# Run only catalog tests
python -m pytest app/tests/validation/test_catalog_consistency.py -v
```

### Run with Custom Options

```bash
# Skip performance tests (faster execution)
python -m app.tests.validation.test_runner --no-performance

# Skip catalog tests
python -m app.tests.validation.test_runner --no-catalog

# Custom output directory
python -m app.tests.validation.test_runner --output-dir ./my_reports
```

## Test Suites

### 1. Comprehensive Tech Stack Generation Tests

**File:** `test_tech_stack_generation_comprehensive.py`

**Purpose:** Validates the core tech stack generation functionality with comprehensive scenarios.

**Key Tests:**
- AWS Connect bug regression test
- Multi-cloud context prioritization
- Generic pattern override validation
- End-to-end scenario testing
- Accuracy metrics collection
- Technology context validation

**Example:**
```python
def test_aws_connect_bug_regression(self, tech_stack_generator, requirement_parser):
    """Regression test for the original AWS Connect bug."""
    requirements = {
        "description": "Build customer service system with Amazon Connect...",
        "integrations": ["Amazon Connect", "AWS Comprehend", "AWS S3"]
    }
    
    result = tech_stack_generator.generate_tech_stack(requirements)
    
    # Verify all explicit AWS technologies are included
    assert "Amazon Connect" in result.get("tech_stack", [])
    assert "AWS Comprehend" in result.get("tech_stack", [])
```

### 2. Performance Benchmarks

**File:** `test_tech_stack_performance.py`

**Purpose:** Validates system performance under various load conditions.

**Key Tests:**
- Single operation performance
- Batch processing performance
- Concurrent processing performance
- Memory usage scaling
- Sustained load testing
- Performance regression detection

**Performance Thresholds:**
- Single generation: < 10 seconds
- Batch throughput: > 1 ops/second
- Memory usage: < 200 MB
- Concurrent processing: < 30 seconds

**Example:**
```python
def test_large_requirement_processing_performance(self, tech_stack_generator):
    """Benchmark performance for large requirement processing."""
    start_time = time.time()
    result = tech_stack_generator.generate_tech_stack(large_requirements)
    processing_time = time.time() - start_time
    
    assert processing_time < 5.0, f"Processing took too long: {processing_time:.2f}s"
```

### 3. Catalog Consistency Tests

**File:** `test_catalog_consistency.py`

**Purpose:** Validates technology catalog quality and consistency.

**Key Tests:**
- Catalog consistency validation
- Ecosystem consistency checking
- Integration pattern validation
- Completeness for common stacks
- Entry quality validation
- Domain coverage validation

**Quality Metrics:**
- Consistency score: > 90%
- Completeness score: > 80%
- Quality score: > 70%

**Example:**
```python
def test_catalog_consistency_validation(self, consistency_validator):
    """Test comprehensive catalog consistency validation."""
    report = consistency_validator.validate_catalog_consistency()
    
    assert report.consistency_score > 0.9, "Low consistency score"
    assert report.completeness_score > 0.8, "Low completeness score"
```

### 4. Test Data Sets

**File:** `tech_stack_test_data.py`

**Purpose:** Provides comprehensive test data for various scenarios.

**Test Data Categories:**
- AWS ecosystem test cases
- Azure ecosystem test cases
- GCP ecosystem test cases
- Open source stack test cases
- Mixed ecosystem test cases
- Domain-specific test cases
- Performance test cases

**Example Test Case:**
```python
TechStackTestCase(
    name="AWS Serverless Web Application",
    requirements={
        "description": "Build serverless web application using AWS Lambda...",
        "explicit_technologies": ["AWS Lambda", "AWS API Gateway", "DynamoDB"]
    },
    expected_technologies=["AWS Lambda", "AWS API Gateway", "DynamoDB"],
    expected_ecosystem="AWS",
    expected_confidence_min=0.9,
    expected_inclusion_rate_min=0.85
)
```

## Validation Metrics

### Accuracy Metrics

- **Explicit Technology Inclusion Rate**: Percentage of explicitly mentioned technologies included in generated stacks
- **Ecosystem Consistency Rate**: Percentage of generated stacks that maintain ecosystem consistency
- **Pattern Override Accuracy**: Accuracy of prioritizing explicit technologies over pattern-based recommendations

### Performance Metrics

- **Execution Time**: Time taken for various operations
- **Memory Usage**: Memory consumption during processing
- **Throughput**: Operations per second for batch processing
- **Scalability**: Performance under concurrent load

### Catalog Quality Metrics

- **Consistency Score**: Percentage of catalog entries that pass validation rules
- **Completeness Score**: Coverage of common technology stacks
- **Quality Score**: Overall quality based on entry completeness and accuracy

## Validation Reports

The test runner generates comprehensive JSON reports with:

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "total_execution_time": 45.2,
  "overall_success_rate": 0.92,
  "suite_results": [...],
  "performance_metrics": {
    "status": "completed",
    "thresholds_met": true,
    "benchmarks": {...}
  },
  "catalog_metrics": {
    "consistency_score": 0.85,
    "completeness_score": 0.78,
    "quality_score": 0.82
  },
  "accuracy_metrics": {
    "explicit_technology_inclusion_rate": 0.92,
    "ecosystem_consistency_rate": 0.88,
    "aws_connect_bug_fixed": true
  },
  "recommendations": [
    "All validation tests passed - system quality is good"
  ]
}
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Tech Stack Validation
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run validation suite
        run: python -m app.tests.validation.test_runner
      - name: Upload reports
        uses: actions/upload-artifact@v2
        with:
          name: validation-reports
          path: validation_reports/
```

### Make Integration

Add to your `Makefile`:

```makefile
.PHONY: validate-tech-stack validate-tech-stack-fast validate-tech-stack-full

validate-tech-stack:
	python -m app.tests.validation.test_runner

validate-tech-stack-fast:
	python -m app.tests.validation.test_runner --no-performance

validate-tech-stack-full:
	python -m app.tests.validation.test_runner --output-dir ./validation_reports
```

## Troubleshooting

### Common Issues

1. **Performance Tests Failing**
   - Check system resources (CPU, memory)
   - Adjust performance thresholds if needed
   - Run with `--no-performance` to skip

2. **Catalog Tests Failing**
   - Verify catalog data integrity
   - Check for missing technology entries
   - Review integration references

3. **Regression Tests Failing**
   - Check for breaking changes in core logic
   - Verify mock data and responses
   - Review requirement parsing logic

### Debug Mode

Run tests with verbose output:

```bash
python -m pytest app/tests/validation/ -v -s --tb=long
```

### Performance Profiling

For detailed performance analysis:

```bash
python -m pytest app/tests/performance/ --profile-svg
```

## Extending the Framework

### Adding New Test Cases

1. **Create test data** in `tech_stack_test_data.py`:
```python
new_test_case = TechStackTestCase(
    name="My New Test Case",
    requirements={...},
    expected_technologies=[...],
    expected_ecosystem="...",
    expected_confidence_min=0.8,
    expected_inclusion_rate_min=0.8
)
```

2. **Add test method** in appropriate test file:
```python
def test_my_new_scenario(self, tech_stack_generator):
    """Test my new scenario."""
    # Test implementation
    pass
```

### Adding New Validation Rules

1. **Extend validation rules** in `test_catalog_consistency.py`:
```python
def _load_validation_rules(self):
    return {
        "required_fields": [...],
        "my_new_rule": {...}
    }
```

2. **Implement validation logic**:
```python
def validate_my_new_rule(self):
    """Validate my new rule."""
    # Validation implementation
    pass
```

### Custom Metrics

Add custom metrics to the validation report:

```python
def _generate_custom_metrics(self) -> Dict[str, Any]:
    """Generate custom metrics."""
    return {
        "my_metric": self._calculate_my_metric(),
        "status": "completed"
    }
```

## Best Practices

1. **Test Data Management**
   - Keep test data realistic and representative
   - Update test cases when adding new technologies
   - Maintain separate test data for different scenarios

2. **Performance Testing**
   - Run performance tests on consistent hardware
   - Set realistic performance thresholds
   - Monitor performance trends over time

3. **Catalog Validation**
   - Regularly update validation rules
   - Review and fix catalog inconsistencies
   - Maintain high catalog quality standards

4. **Continuous Validation**
   - Run validation suite in CI/CD pipeline
   - Set up alerts for validation failures
   - Review validation reports regularly

## Support

For issues or questions about the validation framework:

1. Check the troubleshooting section above
2. Review test logs and error messages
3. Run individual test suites to isolate issues
4. Check system requirements and dependencies