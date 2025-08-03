# Use Python 3.11 slim image for smaller size and faster builds
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better Docker layer caching  
COPY requirements.txt .

# Install Python dependencies with optimizations for Cloud Run
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy modular application files
COPY . ./
# Remove unnecessary files and conflicting directories
RUN rm -rf rag-frontend-vercel/ tests/ *.md src/ run_server_graceful.py || true
# Ensure we have the system prompt file
RUN ls -la Clair-sys-prompt.txt || echo "Warning: Clair-sys-prompt.txt not found"
# Debug: Show what main files exist
RUN echo "=== MAIN FILES AFTER CLEANUP ===" && ls -la main*.py
# Debug: Check for any graceful references
RUN grep -r "GRACEFUL" . || echo "No GRACEFUL references found"

# Set environment variables for Cloud Run
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose the port that Cloud Run expects
EXPOSE 8080

# Health check optimized for Cloud Run
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=2 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Run minimal working version to ensure endpoints are available
CMD ["python", "-m", "uvicorn", "minimal_working_main:app", "--host", "0.0.0.0", "--port", "8080"]