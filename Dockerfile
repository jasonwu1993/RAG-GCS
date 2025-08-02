# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy modular application code
COPY main_modular.py .
COPY config.py core.py ai_service.py google_drive.py .
COPY documents_router.py search_router.py chat_router.py admin_router.py .
COPY Clair-sys-prompt.txt .

# Create symlink for backward compatibility
RUN ln -sf main_modular.py main.py

# Set environment variables for Cloud Run
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port for Cloud Run
EXPOSE 8080

# Health check optimized for Cloud Run
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=2 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Use exec form for better signal handling in Cloud Run
CMD ["python", "main_modular.py"]