# syntax=docker/dockerfile:1.4

# Build stage using Astral uv
FROM ghcr.io/astral-sh/uv:0.9.9 AS builder

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r requirements.txt

# Copy application code
COPY . .

# Compile Python files for faster startup
RUN python -m compileall -q .

# Runtime stage
FROM ghcr.io/astral-sh/uv:alpine3.22 AS runtime

# Install runtime dependencies
RUN apk add --no-cache \
    libpq \
    libffi \
    openssl

# Create non-root user
RUN addgroup -g 1001 -S app && \
    adduser -u 1001 -S app -G app

# Set working directory
WORKDIR /app

# Copy installed packages and application from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app /app

# Change ownership to non-root user
RUN chown -R app:app /app

# Switch to non-root user
USER app

# Expose port
EXPOSE 8007

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; import sys; r = httpx.get('http://localhost:8007/api/v1/health', timeout=5); sys.exit(0 if r.status_code == 200 else 1)"

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8007"]
