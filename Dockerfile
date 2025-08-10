# Multi-stage build for Automated AI Assessment (AAA)
# Stage 1: Build dependencies and test
FROM python:3.10-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy application code for testing
COPY . .

# Run tests to ensure build quality (optional - can be disabled with --build-arg SKIP_TESTS=true)
ARG SKIP_TESTS=false
RUN if [ "$SKIP_TESTS" = "false" ]; then \
        python -m pytest app/tests/unit/ -v --tb=short || exit 1; \
    fi

# Stage 2: Production runtime
FROM python:3.10-slim as runtime

# Set working directory
WORKDIR /app

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python packages from builder stage
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY app/ ./app/
COPY data/ ./data/
COPY config.yaml .
COPY streamlit_app.py .
COPY run_streamlit.py .

# Create necessary directories with proper permissions
RUN mkdir -p exports cache \
    && chmod 755 exports cache

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash agentic \
    && chown -R agentic:agentic /app
USER agentic

# Expose ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden)
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]