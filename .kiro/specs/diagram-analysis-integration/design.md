# Design Document

## Overview

This design addresses the integration of enhanced analysis data (tech stack and architecture explanation) with the diagram generation system. The solution ensures that diagrams use the same technology recommendations and architectural insights that users see in the analysis section, providing consistency across the application.

## Architecture

### Current Flow
```
Requirements → Pattern Matching → Basic Tech Stack → Diagram Generation
                                                  ↗
Analysis Phase → Enhanced Tech Stack + Architecture Explanation (not used)
```

### Proposed Flow
```
Requirements → Pattern Matching → Basic Tech Stack → Analysis Phase → Enhanced Data
                                                                           ↓
                                  Diagram Generation ← Enhanced Tech Stack + Architecture Explanation
```

## Components and Interfaces

### 1. Enhanced Data Retrieval

**Location:** `streamlit_app.py` - Diagram generation section

**Function:** `get_enhanced_analysis_data()`
```python
def get_enhanced_analysis_data() -> Dict[str, Any]:
    """Retrieve enhanced tech stack and architecture explanation from session state."""
    return {
        'enhanced_tech_stack': st.session_state.get('recommendations', {}).get('enhanced_tech_stack'),
        'architecture_explanation': st.session_state.get('recommendations', {}).get('architecture_explanation'),
        'has_enhanced_data': bool(enhanced_tech_stack or architecture_explanation)
    }
```

### 2. Diagram Function Signature Updates

**Current Signature:**
```python
async def build_tech_stack_wiring_diagram(requirement: str, recommendations: List[Dict]) -> str
```

**New Signature:**
```python
async def build_tech_stack_wiring_diagram(
    requirement: str, 
    recommendations: List[Dict],
    enhanced_tech_stack: Optional[List[str]] = None,
    architecture_explanation: Optional[str] = None
) -> str
```

### 3. Enhanced Prompt Generation

**Tech Stack Priority Logic:**
1. Use `enhanced_tech_stack` if available
2. Fall back to `recommendations[0]['tech_stack']` if enhanced not available
3. Fall back to default tech stack if neither available

**Architecture Context Integration:**
- Include architecture explanation in LLM prompt as context
- Use explanation to inform component relationships and data flow
- Maintain existing prompt structure while adding context

### 4. Session State Integration

**Data Flow:**
1. Analysis phase generates and stores enhanced data in session state
2. Diagram generation retrieves enhanced data from session state
3. Enhanced data is passed to diagram generation functions
4. Functions prioritize enhanced data over basic recommendations

## Data Models

### Enhanced Analysis Data Structure
```python
@dataclass
class EnhancedAnalysisData:
    enhanced_tech_stack: Optional[List[str]] = None
    architecture_explanation: Optional[str] = None
    has_enhanced_data: bool = False
    
    @classmethod
    def from_session_state(cls) -> 'EnhancedAnalysisData':
        """Create from current session state."""
        recommendations = st.session_state.get('recommendations', {})
        enhanced_tech_stack = recommendations.get('enhanced_tech_stack')
        architecture_explanation = recommendations.get('architecture_explanation')
        
        return cls(
            enhanced_tech_stack=enhanced_tech_stack,
            architecture_explanation=architecture_explanation,
            has_enhanced_data=bool(enhanced_tech_stack or architecture_explanation)
        )
```

### Updated Diagram Generation Parameters
```python
@dataclass
class DiagramGenerationContext:
    requirement: str
    recommendations: List[Dict]
    enhanced_tech_stack: Optional[List[str]] = None
    architecture_explanation: Optional[str] = None
    provider_config: Dict = None
```

## Error Handling

### Fallback Strategy
1. **Enhanced Data Unavailable:** Fall back to original recommendation tech stack
2. **Architecture Explanation Missing:** Generate diagrams without architectural context
3. **Session State Issues:** Use empty enhanced data and log warning
4. **LLM Generation Errors:** Maintain existing error handling with enhanced context

### Logging Strategy
```python
# Log enhanced data usage
if enhanced_tech_stack:
    app_logger.info(f"Using enhanced tech stack for diagram: {len(enhanced_tech_stack)} technologies")
else:
    app_logger.info("No enhanced tech stack available, using recommendation tech stack")

if architecture_explanation:
    app_logger.info(f"Including architecture explanation in diagram context: {len(architecture_explanation)} chars")
```

## Testing Strategy

### Unit Tests
1. **Enhanced Data Retrieval:** Test session state data extraction
2. **Fallback Logic:** Test behavior when enhanced data is unavailable
3. **Prompt Generation:** Test LLM prompt construction with enhanced context
4. **Tech Stack Priority:** Test tech stack selection logic

### Integration Tests
1. **End-to-End Flow:** Test complete analysis → diagram generation flow
2. **Session State Consistency:** Test data persistence across UI interactions
3. **Multiple Diagram Types:** Test enhanced data usage across all diagram types
4. **Provider Compatibility:** Test with different LLM providers

### Test Scenarios
```python
# Test enhanced data availability
def test_enhanced_data_available():
    # Setup session state with enhanced data
    # Generate diagram
    # Verify enhanced tech stack is used

# Test fallback behavior
def test_enhanced_data_unavailable():
    # Setup session state without enhanced data
    # Generate diagram
    # Verify fallback to recommendation tech stack

# Test architecture explanation integration
def test_architecture_explanation_context():
    # Setup session state with architecture explanation
    # Generate diagram
    # Verify explanation is included in LLM prompt
```

## Implementation Phases

### Phase 1: Data Retrieval Infrastructure
- Implement `get_enhanced_analysis_data()` function
- Add enhanced data extraction from session state
- Add logging for enhanced data availability

### Phase 2: Diagram Function Updates
- Update all diagram generation function signatures
- Implement tech stack priority logic
- Add architecture explanation to LLM prompts

### Phase 3: UI Integration
- Update diagram generation calls to pass enhanced data
- Add enhanced data retrieval in diagram generation flow
- Test consistency across all diagram types

### Phase 4: Testing and Validation
- Add comprehensive unit tests
- Add integration tests for end-to-end flow
- Validate consistency between analysis and diagrams