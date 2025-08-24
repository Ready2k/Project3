# System Configuration Management Feature

## Overview

The System Configuration Management feature exposes previously hardcoded values through a comprehensive GUI interface, allowing users to customize system behavior without code changes. This addresses the need for configurable thresholds, weights, and parameters throughout the AAA system.

## Problem Solved

Previously, critical system parameters were hardcoded throughout the codebase:

```python
# Hardcoded values scattered across files
min_autonomy_threshold = 0.7
confidence_boost_factor = 1.2
autonomy_weights = {"reasoning_capability": 0.3, "decision_independence": 0.25, ...}
tag_weight = 0.3, vector_weight = 0.5, confidence_weight = 0.2
temperature = 0.3, max_tokens = 1000
```

This made it impossible for users to:
- Adjust autonomy assessment sensitivity
- Fine-tune pattern matching behavior
- Customize LLM generation parameters
- Modify recommendation thresholds
- Adapt the system to different use cases

## Solution Architecture

### 1. Configuration Data Classes

**File**: `app/ui/system_configuration.py`

Four main configuration categories:

```python
@dataclass
class AutonomyConfig:
    min_autonomy_threshold: float = 0.7
    confidence_boost_factor: float = 1.2
    reasoning_capability_weight: float = 0.3
    # ... other autonomy parameters

@dataclass  
class PatternMatchingConfig:
    tag_weight: float = 0.3
    vector_weight: float = 0.5
    strong_tag_match_threshold: float = 0.7
    # ... other pattern matching parameters

@dataclass
class LLMGenerationConfig:
    temperature: float = 0.3
    max_tokens: int = 1000
    top_p: float = 1.0
    # ... other LLM parameters

@dataclass
class RecommendationConfig:
    min_recommendation_confidence: float = 0.7
    tech_stack_inclusion_threshold: float = 0.6
    # ... other recommendation parameters
```

### 2. Configuration Service

**File**: `app/services/configuration_service.py`

Centralized service providing:
- Singleton pattern for consistent configuration access
- Convenience methods for common operations
- Type-safe parameter access
- Configuration persistence and reloading

```python
class ConfigurationService:
    def get_autonomy_weights(self) -> Dict[str, float]
    def get_llm_params(self) -> Dict[str, Any]
    def is_fully_automatable(self, score: float) -> bool
    def get_feasibility_classification(self, score: float) -> str
    # ... other convenience methods
```

### 3. Management Interface

**File**: `app/ui/system_configuration.py`

Comprehensive Streamlit interface with:
- **5 Configuration Tabs**: Autonomy Assessment, Pattern Matching, LLM Generation, Recommendations, Management
- **Real-time Validation**: Weight sum validation, threshold range checking
- **Import/Export**: YAML-based configuration sharing
- **Reset to Defaults**: Easy restoration of original values
- **Live Preview**: Current configuration display

## User Interface

### System Configuration Tab

The new "🔧 System Config" tab provides:

#### 🤖 Autonomy Assessment
- **Thresholds**: Min autonomy, confidence boost, feasibility classification thresholds
- **Scoring Weights**: Configurable weights for reasoning, decision independence, exception handling, learning, monitoring
- **Real-time Validation**: Ensures weights sum to 1.0

#### 🔍 Pattern Matching  
- **Blending Weights**: Tag, vector, and confidence weight configuration
- **Similarity Thresholds**: Strong/moderate match classification thresholds
- **Agentic Scoring**: Specialized weights for agentic pattern evaluation

#### 🧠 LLM Generation
- **Generation Parameters**: Temperature, max tokens, top-p, penalties
- **Timeout Configuration**: LLM and HTTP timeout settings
- **Provider Settings**: Per-provider parameter customization

#### 💡 Recommendations
- **Confidence Thresholds**: Minimum confidence for recommendations and tech inclusion
- **Boost Factors**: Autonomy, reasoning, and multi-agent boost configuration
- **Creation Thresholds**: When to create new patterns vs enhance existing

#### ⚙️ Management
- **Save/Load**: Persistent configuration storage
- **Import/Export**: YAML-based configuration sharing
- **Reset to Defaults**: Quick restoration of original values
- **Configuration Preview**: Live YAML preview of current settings

## Integration Points

### Services Updated

1. **AutonomyAssessor** (`app/services/autonomy_assessor.py`)
   ```python
   # Before: Hardcoded weights
   self.autonomy_weights = {"reasoning_capability": 0.3, ...}
   
   # After: Dynamic configuration
   self.config_service = get_config()
   self.autonomy_weights = self.config_service.get_autonomy_weights()
   ```

2. **AgenticRecommendationService** (`app/services/agentic_recommendation_service.py`)
   ```python
   # Before: Hardcoded thresholds
   self.min_autonomy_threshold = 0.7
   
   # After: Dynamic configuration
   self.min_autonomy_threshold = self.config_service.autonomy.min_autonomy_threshold
   ```

3. **PatternMatcher** (Ready for integration)
   - Tag/vector/confidence weight configuration
   - Similarity threshold customization
   - Agentic scoring weight adjustment

## Configuration Persistence

### File Format: `system_config.yaml`

```yaml
autonomy:
  min_autonomy_threshold: 0.7
  confidence_boost_factor: 1.2
  reasoning_capability_weight: 0.3
  decision_independence_weight: 0.25
  exception_handling_weight: 0.2
  learning_adaptation_weight: 0.15
  self_monitoring_weight: 0.1
  fully_automatable_threshold: 0.8
  partially_automatable_threshold: 0.6

pattern_matching:
  tag_weight: 0.3
  vector_weight: 0.5
  confidence_weight: 0.2
  strong_tag_match_threshold: 0.7
  high_similarity_threshold: 0.7
  excellent_fit_threshold: 0.8

llm_generation:
  temperature: 0.3
  max_tokens: 1000
  top_p: 1.0
  frequency_penalty: 0.0
  presence_penalty: 0.0
  llm_timeout: 20
  http_timeout: 10

recommendations:
  min_recommendation_confidence: 0.7
  tech_stack_inclusion_threshold: 0.6
  new_pattern_creation_threshold: 0.7
  autonomy_boost_factor: 0.2
```

## Usage Examples

### Basic Configuration Access

```python
from app.services.configuration_service import get_config

config = get_config()

# Check feasibility
if config.is_fully_automatable(autonomy_score):
    feasibility = "Fully Automatable"

# Get LLM parameters
llm_params = config.get_llm_params()
response = await llm_provider.generate(prompt, **llm_params)

# Use dynamic thresholds
if score > config.recommendations.min_recommendation_confidence:
    include_recommendation(recommendation)
```

### Configuration Management

```python
from app.ui.system_configuration import SystemConfigurationManager

# Load configuration
manager = SystemConfigurationManager()

# Modify settings
manager.config.autonomy.min_autonomy_threshold = 0.75
manager.config.llm_generation.temperature = 0.5

# Save changes
manager.save_config()

# Export for sharing
config_dict = manager.export_config()
```

## Benefits

### For Users
- **Customizable Behavior**: Adjust system sensitivity and thresholds
- **No Code Changes**: GUI-based configuration management
- **Team Collaboration**: Export/import configurations across environments
- **Easy Experimentation**: Quick parameter adjustment and testing
- **Professional Control**: Fine-tune system for specific use cases

### For Developers
- **Centralized Configuration**: Single source of truth for system parameters
- **Type Safety**: Pydantic-based configuration with validation
- **Easy Integration**: Simple service injection pattern
- **Backward Compatibility**: Gradual migration from hardcoded values
- **Testing Support**: Easy configuration mocking and testing

## Future Enhancements

### Planned Integrations
1. **PatternMatcher**: Complete integration of similarity thresholds
2. **LLM Providers**: Dynamic parameter injection for all providers
3. **TechStackGenerator**: Configurable recommendation algorithms
4. **SecuritySystem**: Configurable detection thresholds

### Advanced Features
1. **Configuration Profiles**: Named configuration sets for different scenarios
2. **A/B Testing**: Configuration-based feature experimentation
3. **Performance Monitoring**: Track configuration impact on system performance
4. **Auto-tuning**: ML-based parameter optimization
5. **Configuration Validation**: Advanced validation rules and constraints

## Testing

### Test Coverage
- **Unit Tests**: `test_system_configuration.py` - Configuration service functionality
- **Integration Tests**: Service integration and parameter usage
- **UI Tests**: Streamlit interface validation and user workflows

### Validation
- ✅ Configuration persistence and loading
- ✅ Service integration and parameter injection
- ✅ UI functionality and validation
- ✅ Import/export capabilities
- ✅ Reset to defaults functionality

## Migration Guide

### For Existing Hardcoded Values

1. **Identify Hardcoded Parameters**
   ```bash
   grep -r "0\.[0-9]" app/services/ | grep -E "threshold|weight|score"
   ```

2. **Add to Configuration Classes**
   ```python
   @dataclass
   class YourConfig:
       your_threshold: float = 0.7
   ```

3. **Update Service Integration**
   ```python
   # Before
   if score > 0.7:
   
   # After  
   if score > self.config_service.your_config.your_threshold:
   ```

4. **Add UI Controls**
   ```python
   config.your_threshold = st.slider(
       "Your Threshold",
       min_value=0.0, max_value=1.0, 
       value=config.your_threshold
   )
   ```

## Conclusion

The System Configuration Management feature transforms the AAA system from a rigid, hardcoded application into a flexible, user-configurable platform. Users can now fine-tune system behavior for their specific needs while developers benefit from centralized, type-safe configuration management.

This feature represents a significant step toward making the AAA system enterprise-ready and adaptable to diverse organizational requirements and use cases.