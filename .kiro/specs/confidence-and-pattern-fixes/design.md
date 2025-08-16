# Design Document

## Overview

This design addresses two critical bugs in the AAA system: confidence levels being hardcoded at 85.00% instead of using LLM-generated values, and the pattern library failing to create new patterns despite novel technologies being present. The solution involves enhancing LLM response parsing, improving confidence extraction logic, and refining pattern creation decision algorithms.

## Architecture

### Current Issues Analysis

1. **Confidence Level Problem**: The system extracts `llm_analysis_confidence_level` from requirements but the recommendation service's `_calculate_confidence` method may not be properly using this value
2. **Pattern Creation Problem**: The `_should_create_new_pattern` method in RecommendationService is too restrictive, preventing new pattern creation when conceptual similarity is detected

### Solution Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   LLM Provider  │───▶│  Response Parser │───▶│ Confidence      │
│                 │    │                  │    │ Extractor       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Pattern Creator │◀───│ Decision Engine  │◀───│ Requirements    │
│                 │    │                  │    │ Analyzer        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Components and Interfaces

### 1. Enhanced LLM Response Parser

**Location**: `app/services/recommendation.py` and `app/services/pattern_creator.py`

**Interface**:
```python
class LLMResponseParser:
    def extract_confidence(self, llm_response: str) -> Optional[float]
    def extract_pattern_data(self, llm_response: str) -> Dict[str, Any]
    def validate_confidence_range(self, confidence: float) -> float
```

**Responsibilities**:
- Parse LLM responses in both JSON and text formats
- Extract confidence values with validation
- Handle malformed responses gracefully
- Provide fallback mechanisms

### 2. Confidence Calculation Enhancement

**Location**: `app/services/recommendation.py._calculate_confidence`

**Current Logic**:
```python
# Prioritize LLM confidence if available
llm_confidence = requirements.get("llm_analysis_confidence_level")
if llm_confidence and isinstance(llm_confidence, (int, float)):
    return min(max(llm_confidence, 0.0), 1.0)
```

**Enhanced Logic**:
- Improve LLM confidence extraction and validation
- Add logging for confidence source (LLM vs pattern-based)
- Handle edge cases where confidence is string or malformed

### 3. Pattern Creation Decision Engine

**Location**: `app/services/recommendation.py._should_create_new_pattern`

**Current Issues**:
- Too restrictive conceptual similarity checking
- Always enhances existing patterns instead of creating new ones
- Doesn't consider technology novelty

**Enhanced Logic**:
- Separate technology novelty from conceptual similarity
- Create new patterns when technology stack is significantly different
- Improve logging for pattern creation decisions

## Data Models

### Confidence Data Structure
```python
@dataclass
class ConfidenceResult:
    value: float  # 0.0 to 1.0
    source: str   # "llm" or "pattern_based"
    raw_value: Any  # Original extracted value
    validation_errors: List[str]
```

### Pattern Creation Decision
```python
@dataclass
class PatternCreationDecision:
    should_create: bool
    reason: str
    conceptual_similarity_score: float
    technology_novelty_score: float
    best_match_score: float
```

## Error Handling

### Confidence Extraction Errors
1. **Invalid LLM Response**: Log error, use pattern-based calculation
2. **Confidence Out of Range**: Clamp to 0.0-1.0, log warning
3. **Non-numeric Confidence**: Attempt text parsing, fallback to pattern-based

### Pattern Creation Errors
1. **LLM Analysis Failure**: Use rule-based pattern creation
2. **File System Errors**: Log error, continue with existing patterns
3. **Validation Failures**: Log detailed error, skip pattern creation

## Testing Strategy

### Unit Tests
1. **Confidence Extraction Tests**:
   - Valid LLM confidence values (0.0, 0.5, 1.0)
   - Invalid values (negative, > 1.0, strings)
   - Malformed JSON responses
   - Missing confidence in response

2. **Pattern Creation Tests**:
   - High conceptual similarity with new technology
   - Low conceptual similarity scenarios
   - Technology novelty detection
   - Decision logging verification

### Integration Tests
1. **End-to-End Confidence Flow**:
   - LLM generates confidence → extraction → display
   - Pattern-based fallback when LLM fails
   - UI displays varying confidence levels

2. **Pattern Library Growth**:
   - New patterns created for novel requirements
   - Existing patterns enhanced appropriately
   - No duplicate pattern creation

## Implementation Approach

### Phase 1: Confidence Level Fix
1. Enhance `_calculate_confidence` method with better LLM extraction
2. Add comprehensive logging for confidence sources
3. Improve validation and error handling
4. Add unit tests for confidence extraction

### Phase 2: Pattern Creation Fix
1. Analyze current `_should_create_new_pattern` logic
2. Implement technology novelty scoring
3. Separate conceptual similarity from technology assessment
4. Add decision logging and audit trail

### Phase 3: Testing and Validation
1. Create comprehensive test suite
2. Test with various LLM response formats
3. Validate pattern creation with novel technologies
4. Performance testing for enhanced logic

## Monitoring and Observability

### Metrics to Track
1. **Confidence Distribution**: Track range of confidence values over time
2. **Pattern Creation Rate**: Monitor new pattern creation frequency
3. **LLM vs Pattern-based Confidence**: Ratio of confidence sources
4. **Pattern Enhancement vs Creation**: Decision distribution

### Logging Enhancements
1. **Confidence Extraction**: Log source, raw value, final value
2. **Pattern Decisions**: Log similarity scores, technology novelty, decision rationale
3. **Error Tracking**: Detailed error logs for debugging

## Security Considerations

### Input Validation
- Validate LLM confidence values are numeric and in range
- Sanitize pattern data before file system operations
- Validate JSON parsing to prevent injection attacks

### Error Information Disclosure
- Avoid exposing internal LLM response details in user-facing errors
- Log sensitive debugging information securely
- Sanitize file paths in pattern creation