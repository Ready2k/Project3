# 🔧 AgenticOrNot Troubleshooting Guide

## Common Issues

### 🚫 App Freezes at "Parsing" Phase

If the Streamlit app gets stuck at "Parsing (10%)" and doesn't progress:

1. **Check API Connection**: Ensure FastAPI backend is running at http://localhost:8000
2. **Restart Services**: Stop both API and UI, then restart with `make dev`
3. **Clear Browser Cache**: Hard refresh (Ctrl+F5 or Cmd+Shift+R) the Streamlit page
4. **Check Requirements**: Ensure your input has sufficient detail (at least 10 characters)
5. **View Logs**: Check the API terminal for error messages

**Quick Fix:**
```bash
# Stop any running services
pkill -f "uvicorn\|streamlit"

# Restart everything
make dev
```

### 📊 Observability Dashboard Errors

If you see JavaScript console errors about "Infinite extent" in charts:

1. **Start Analysis First**: The dashboard needs data from completed analyses
2. **Check Data**: Ensure you've run at least one successful analysis
3. **Refresh Page**: Sometimes charts need a page refresh to render properly

## LLM Provider Connection Issues

### ❌ "Connection failed" Error

#### **Common Causes & Solutions:**

1. **Invalid API Key**
   ```
   Error: Authentication failed - check your API key
   ```
   **Solution:**
   - Verify your API key is correct
   - Check it starts with `sk-` for OpenAI
   - Ensure no extra spaces or characters
   - Test with: `python3 test_provider.py YOUR_API_KEY`

2. **Invalid Model Name**
   ```
   Error: Model 'gpt-5' not found
   ```
   **Solution:**
   - Use valid OpenAI models: `gpt-4o`, `gpt-4`, `gpt-3.5-turbo`, `gpt-4-turbo`
   - ❌ Don't use: `gpt-5`, `gpt4-o`, `gpt-4-o`
   - ✅ Use: `gpt-4o` (correct spelling)

3. **Rate Limit Exceeded**
   ```
   Error: Rate limit exceeded
   ```
   **Solution:**
   - Wait a few minutes before retrying
   - Check your OpenAI usage limits
   - Consider upgrading your OpenAI plan

4. **Network/Connection Issues**
   ```
   Error: Connection error
   ```
   **Solution:**
   - Check your internet connection
   - Verify firewall isn't blocking requests
   - Try again in a few minutes

### 🐛 Debug Mode

Enable debug mode in the Streamlit sidebar to see:
- Detailed API request/response
- Full error messages
- Connection attempt logs

### 🧪 Testing Provider Connection

#### **Method 1: Test Script**
```bash
cd agentic_or_not
python3 test_provider.py YOUR_API_KEY
```

#### **Method 2: Direct API Test**
```bash
curl -X POST "http://localhost:8000/providers/test" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "model": "gpt-4o",
    "api_key": "YOUR_API_KEY"
  }'
```

#### **Method 3: Python Test**
```python
from app.llm.openai_provider import OpenAIProvider
import asyncio

async def test():
    provider = OpenAIProvider(api_key="YOUR_API_KEY", model="gpt-4o")
    success, error = await provider.test_connection_detailed()
    print(f"Success: {success}")
    if not success:
        print(f"Error: {error}")

asyncio.run(test())
```

## API Server Issues

### 🚫 "Connection Error" in Streamlit

**Symptoms:**
- Streamlit shows "Connection Error" when clicking buttons
- API calls fail

**Solutions:**
1. **Check API Server is Running**
   ```bash
   # Check if API is running
   curl http://localhost:8000/health
   
   # Should return: {"status": "healthy", "version": "1.3.2"}
   ```

2. **Start API Server**
   ```bash
   cd agentic_or_not
   python3 -m uvicorn app.api:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Check Port Conflicts**
   ```bash
   # Check what's using port 8000
   lsof -i :8000
   
   # Kill conflicting process if needed
   kill -9 PID
   ```

### 📊 "Module Not Found" Errors

**Error:**
```
ModuleNotFoundError: No module named 'app'
```

**Solution:**
```bash
cd agentic_or_not
export PYTHONPATH=$PWD:$PYTHONPATH
python3 -m uvicorn app.api:app --reload
```

## Streamlit Issues

### 🖥️ Streamlit Won't Start

**Error:**
```
streamlit: command not found
```

**Solution:**
```bash
# Use Python module instead
python3 -m streamlit run app/main.py --server.port 8501
```

### 🔄 UI Not Updating

**Symptoms:**
- Changes don't appear in UI
- Old data showing

**Solutions:**
1. **Hard Refresh Browser**: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)
2. **Clear Streamlit Cache**: Click "Clear Cache" in Streamlit menu
3. **Restart Streamlit**: Stop and restart the Streamlit server

## Installation Issues

### 📦 Package Installation Failures

**Error:**
```
ERROR: Failed building wheel for faiss-cpu
```

**Solution:**
```bash
# For macOS with Apple Silicon
pip install faiss-cpu --no-cache-dir

# For older systems
pip install faiss-cpu==1.7.4

# Alternative: Use conda
conda install -c conda-forge faiss-cpu
```

### 🐍 Python Version Issues

**Requirements:**
- Python 3.10+ recommended
- Python 3.9+ minimum

**Check Version:**
```bash
python3 --version
```

## Performance Issues

### 🐌 Slow Pattern Matching

**Symptoms:**
- Long delays when clicking "Find Pattern Matches"
- FAISS index building takes too long

**Solutions:**
1. **Reduce Pattern Library Size**: Remove unused patterns from `data/patterns/`
2. **Use Smaller Embedding Model**: Edit `app/embeddings/engine.py` to use `all-MiniLM-L6-v2`
3. **Increase Memory**: Ensure sufficient RAM available

### 💾 High Memory Usage

**Solutions:**
1. **Clear Cache**: `make clean`
2. **Restart Services**: Stop and restart API/UI
3. **Use Redis**: Configure Redis for session storage instead of disk cache

## Logging & Debugging

### 📝 Enable Detailed Logging

**Method 1: Environment Variable**
```bash
export LOGGING_LEVEL=DEBUG
python3 -m uvicorn app.api:app --reload
```

**Method 2: Config File**
```yaml
# config.yaml
logging:
  level: DEBUG
  redact_pii: false  # Show full error messages
```

### 🔍 View API Logs

**FastAPI Logs:**
- Check terminal where `uvicorn` is running
- Look for ERROR and WARNING messages

**Streamlit Logs:**
- Check browser developer console (F12)
- Look for network errors in Network tab

## Getting Help

### 📋 Information to Provide

When reporting issues, include:

1. **Error Message**: Full error text
2. **Steps to Reproduce**: What you clicked/typed
3. **Environment**: OS, Python version
4. **Logs**: Relevant log output
5. **Configuration**: Provider, model, settings used

### 🧪 Diagnostic Commands

```bash
# System info
python3 --version
pip list | grep -E "(openai|streamlit|fastapi|uvicorn)"

# Test basic functionality
cd agentic_or_not
python3 -c "from app.api import app; print('✅ API imports OK')"
python3 -c "import streamlit; print('✅ Streamlit imports OK')"

# Test API health
curl http://localhost:8000/health

# Test pattern loading
python3 -c "
from app.pattern.loader import PatternLoader
loader = PatternLoader('data/patterns')
patterns = loader.load_patterns()
print(f'✅ Loaded {len(patterns)} patterns')
"
```

### 🆘 Still Need Help?

1. **Check GitHub Issues**: Look for similar problems
2. **Enable Debug Mode**: Use debug checkbox in Streamlit
3. **Run Test Script**: `python3 test_provider.py`
4. **Check API Docs**: Visit http://localhost:8000/docs