FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir build && \
    mkdir -p src/mcp_registry && \
    pip install --no-cache-dir -e .

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN groupadd -r mcp && useradd -r -g mcp mcp

# Copy only necessary artifacts from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/

# Set environment
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

USER mcp

EXPOSE 8000

CMD ["uvicorn", "mcp_registry.main:app", "--host", "0.0.0.0", "--port", "8000"]
