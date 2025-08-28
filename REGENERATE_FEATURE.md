# Regenerate Analysis Feature

## Overview

The **Regenerate Analysis** feature allows users to re-run their analysis using different LLM models while preserving the same requirements and Q&A answers. This is particularly useful for:

- **Model Comparison**: Test how different AI models (GPT-4, Claude, etc.) analyze the same requirement
- **Quality Assessment**: Compare recommendation quality across different providers
- **Alternative Perspectives**: Get different insights on the same business requirement
- **Performance Testing**: Evaluate which models work best for specific types of requirements

## How It Works

### 1. Complete Initial Analysis
- Run a normal analysis through the system (Text input, File upload, or Jira integration)
- Answer any Q&A questions that appear
- Wait for the analysis to complete and show results

### 2. Access Regenerate Option
- In the **Results & Recommendations** section, look for the "🔄 Regenerate Analysis" expandable section
- This appears only after you have completed results

### 3. Select Different Model
- Choose from available LLM providers and models
- The system shows your current model and warns if you select the same one
- Available options depend on your configured API keys

### 4. Regenerate
- Click "🚀 Regenerate" to start the process
- The system creates a new session with the same requirements and Q&A answers
- Analysis runs with the selected model
- New results appear with a new session ID

## Technical Details

### API Endpoint
- **POST** `/regenerate`
- Accepts requirements, Q&A answers, and provider override
- Returns new session ID for the regenerated analysis

### Session Management
- Each regeneration creates a new session ID
- Original session remains accessible via "Resume Previous Session"
- Both sessions can be compared side-by-side in different browser tabs

### Provider Support
- Works with all configured LLM providers (OpenAI, Claude, Bedrock, Internal)
- Fake provider available for testing when no real providers are configured
- Provider availability depends on API key configuration

## Use Cases

### 1. Model Performance Testing
```
Requirement: "Automate customer support ticket routing"
- Run with GPT-4: Gets 85% feasibility, suggests traditional workflow
- Regenerate with Claude: Gets 92% feasibility, suggests agentic AI approach
- Compare results to choose best recommendation
```

### 2. Quality Assurance
```
Complex Requirement: "Multi-tenant SaaS billing automation with compliance"
- Test with multiple models to ensure consistent high-quality recommendations
- Identify which models handle complex requirements better
- Use best-performing model for similar future requirements
```

### 3. Alternative Perspectives
```
Ambiguous Requirement: "Improve our data processing pipeline"
- Different models may interpret this differently
- One focuses on performance optimization
- Another suggests automation and monitoring
- Combine insights from multiple models
```

## Best Practices

### 1. Model Selection Strategy
- Start with your most reliable model for initial analysis
- Use regeneration to test alternative approaches
- Consider model strengths (GPT-4 for reasoning, Claude for analysis, etc.)

### 2. Comparison Workflow
- Keep original session ID for reference
- Open regenerated results in new browser tab
- Document differences in recommendations
- Choose best approach or combine insights

### 3. Performance Considerations
- Regeneration takes similar time to original analysis (30-120 seconds)
- Each regeneration uses API credits for the selected provider
- Consider cost implications when testing multiple models

## Limitations

- Requires completed initial analysis (can't regenerate partial results)
- Q&A answers are reused as-is (no opportunity to modify them)
- Provider availability depends on API key configuration
- Each regeneration creates a new session (original session unchanged)

## Future Enhancements

- **Batch Regeneration**: Test multiple models simultaneously
- **Comparison Dashboard**: Side-by-side result comparison
- **Model Recommendations**: Suggest best model based on requirement type
- **Cost Tracking**: Monitor API usage across regenerations