# Dynamic Model Discovery Implementation

## Overview

This implementation adds dynamic model discovery to the AAA system, allowing users to fetch available models directly from LLM provider APIs instead of using hardcoded model lists. This ensures users always have access to the latest models and reduces maintenance overhead.

## Key Features

### 1. Provider-Specific Model Discovery

- **OpenAI**: Fetches models via `GET /v1/models` API endpoint
- **Claude**: Uses known model list with API key validation
- **Bedrock**: Discovers models via `list_foundation_models` API
- **Internal**: Attempts multiple common endpoints (`/models`, `/v1/models`, `/api/models`)
- **Fake**: Returns test models for development

### 2. Rich Model Metadata

Each discovered model includes:
- **ID**: Unique model identifier
- **Name**: Human-readable model name
- **Description**: Model purpose and capabilities
- **Context Length**: Maximum token context (where available)
- **Capabilities**: List of model features (text, vision, code, etc.)

### 3. Intelligent Caching

- **1-hour TTL**: Models cached for 1 hour to reduce API calls
- **Provider-specific**: Separate cache per provider configuration
- **Automatic refresh**: Cache invalidated when provider settings change

### 4. Enhanced UI Experience

- **Discover Models Button**: One-click model discovery per provider
- **Model Details Expander**: Shows context length, capabilities, and description
- **Fallback Models**: Graceful degradation to known models if discovery fails
- **Real-time Feedback**: Loading spinners and success/error messages

## Implementation Details

### Core Components

#### 1. Model Discovery Service (`app/llm/model_discovery.py`)

```python
class ModelDiscoveryService:
    async def discover_openai_models(self, api_key: str) -> List[ModelInfo]
    async def discover_claude_models(self, api_key: str) -> List[ModelInfo]
    async def discover_bedrock_models(self, region: str) -> List[ModelInfo]
    async def discover_internal_models(self, endpoint_url: str, api_key: str) -> List[ModelInfo]
    async def get_available_models(self, provider: str, **kwargs) -> List[ModelInfo]
```

#### 2. Enhanced Provider Classes

All providers now implement:
```python
async def get_available_models(self) -> List[Dict[str, Any]]
```

#### 3. New API Endpoints

- **POST /providers/models**: Discover available models for a provider
- **Enhanced POST /providers/test**: Test connection for all providers

#### 4. Updated Streamlit UI

- Dynamic model selection based on discovery results
- Provider-specific configuration panels
- Model metadata display
- Improved error handling and user feedback

### Provider-Specific Implementation

#### OpenAI
- Calls `client.models.list()` to get all available models
- Filters for chat completion models (gpt-*, o1-*)
- Adds context length and capability metadata
- Fallback to known models if API fails

#### Claude
- Uses predefined model list (Claude has no models API)
- Validates API key with minimal test request
- Includes latest Claude 3.5 models
- Rich capability metadata for each model

#### Bedrock
- Uses `boto3.client("bedrock").list_foundation_models()`
- Filters for text generation models
- Handles AWS authentication automatically
- Regional model availability

#### Internal
- Tries multiple common model endpoints
- Handles various response formats
- Supports optional authentication
- Graceful fallback to default model

## API Usage Examples

### Discover OpenAI Models
```bash
curl -X POST "http://localhost:8000/providers/models" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "api_key": "sk-..."
  }'
```

### Discover Bedrock Models
```bash
curl -X POST "http://localhost:8000/providers/models" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "bedrock",
    "region": "us-east-1"
  }'
```

### Test Provider Connection
```bash
curl -X POST "http://localhost:8000/providers/test" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "claude",
    "model": "claude-3-5-sonnet-20241022",
    "api_key": "sk-ant-..."
  }'
```

## Configuration Updates

### Environment Variables

New environment variables supported:
- `ANTHROPIC_API_KEY`: Claude API key
- `INTERNAL_ENDPOINT_URL`: Internal provider endpoint
- `INTERNAL_API_KEY`: Internal provider API key

### Provider Configuration

Updated `ProviderConfig` model supports all providers:
```python
class ProviderConfig(BaseModel):
    provider: str = "openai"  # openai, claude, bedrock, internal, fake
    model: str = "gpt-4o"
    api_key: Optional[str] = None
    endpoint_url: Optional[str] = None  # For internal provider
    region: Optional[str] = None        # For bedrock
```

## Error Handling

### Graceful Degradation
- API failures fall back to known model lists
- Invalid configurations show helpful error messages
- Network timeouts handled with appropriate user feedback

### User Feedback
- Loading spinners during discovery
- Success messages with model counts
- Detailed error messages for troubleshooting
- Validation warnings for missing credentials

## Performance Optimizations

### Caching Strategy
- 1-hour cache TTL reduces API calls
- Cache keys include provider configuration
- Automatic cache invalidation on config changes

### Parallel Discovery
- Multiple provider discoveries can run simultaneously
- Non-blocking UI updates
- Efficient resource utilization

### Timeout Management
- 10-second timeout for model discovery
- Graceful handling of slow APIs
- User feedback for long operations

## Testing

### Test Script
Run the test script to verify model discovery:
```bash
python test_model_discovery.py
```

### Unit Tests
- Mock API responses for consistent testing
- Test error conditions and edge cases
- Validate caching behavior

### Integration Tests
- Test with real API keys (when available)
- Verify UI interactions
- End-to-end provider testing

## Migration Guide

### For Existing Users
1. **No Breaking Changes**: Existing configurations continue to work
2. **Enhanced Features**: New model discovery is opt-in via UI buttons
3. **Improved Defaults**: Latest model versions available automatically

### For Developers
1. **Updated Provider Classes**: All providers now support `get_available_models()`
2. **New API Endpoints**: Model discovery and enhanced testing endpoints
3. **Enhanced UI Components**: Dynamic model selection and metadata display

## Future Enhancements

### Planned Features
- **Model Performance Metrics**: Track latency and success rates per model
- **Cost Optimization**: Display pricing information for model selection
- **Model Recommendations**: Suggest optimal models based on use case
- **Batch Discovery**: Discover models for multiple providers simultaneously

### Extensibility
- **Custom Providers**: Easy addition of new LLM providers
- **Plugin Architecture**: Support for third-party model discovery plugins
- **Configuration Templates**: Pre-configured setups for common scenarios

## Security Considerations

### API Key Handling
- Keys never logged or cached
- Secure transmission via HTTPS
- Optional key validation before storage

### Rate Limiting
- Respect provider API rate limits
- Implement exponential backoff
- Cache results to minimize API calls

### Error Information
- Sanitized error messages
- No sensitive data in logs
- Secure failure modes

## Troubleshooting

### Common Issues

1. **No Models Discovered**
   - Verify API key is correct
   - Check network connectivity
   - Ensure provider supports model listing

2. **Discovery Timeout**
   - Check API endpoint availability
   - Verify authentication credentials
   - Try different region (for Bedrock)

3. **Invalid Model Selection**
   - Clear browser cache
   - Re-discover models
   - Check provider documentation

### Debug Mode
Enable debug logging to troubleshoot issues:
```python
import logging
logging.getLogger("app.llm.model_discovery").setLevel(logging.DEBUG)
```

## Conclusion

The dynamic model discovery implementation provides a robust, user-friendly way to access the latest LLM models across all supported providers. It maintains backward compatibility while adding powerful new capabilities for model selection and configuration.

The system is designed for reliability, performance, and extensibility, ensuring it can adapt to the rapidly evolving LLM landscape while providing a consistent user experience.