# OPTIMIZED DOCKERFILE FOR FAST CLOUD RUN DEPLOYMENTS
# Fixes deployment timeout issues and startup failures
# CACHE BUST: 2025-08-06-23:15 - SINGLE VERSION VARIABLE FIX

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# OPTIMIZATION 1: Minimize build layers and reduce image size
RUN apt-get update && apt-get install -y \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# OPTIMIZATION 2: Better caching strategy
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all application files (like working deployments did)
COPY . ./
# Remove unnecessary files and conflicting directories
RUN rm -rf rag-frontend-vercel/ tests/ *.md src/ run_server_graceful.py || true
# Ensure we have the system prompt file
RUN ls -la Clair-sys-prompt.txt || echo "Warning: Clair-sys-prompt.txt not found"
# Debug: Show what main files exist
RUN echo "=== MAIN FILES AFTER CLEANUP ===" && ls -la main*.py

# Set environment variables for Cloud Run with production optimizations
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONOPTIMIZE=1
# CRITICAL: Tell the app it's in production
ENV ENVIRONMENT=production
# OPTIMIZATION: Reduce startup time
ENV GRPC_POLL_STRATEGY=poll
ENV GRPC_ENABLE_FORK_SUPPORT=1

# OPTIMIZATION 5: Security with minimal overhead
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# OPTIMIZATION 6: Expose port
EXPOSE 8080

# OPTIMIZATION 7: Remove health check during startup (Cloud Run handles this)
# This prevents startup conflicts

# Run with production optimizations and timeout handling
CMD ["python", "-m", "uvicorn", "main_modular:app", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--timeout-keep-alive", "30", \
     "--timeout-graceful-shutdown", "30"]