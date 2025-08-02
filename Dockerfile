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

# Copy core application files for modular architecture
COPY core.py config.py ai_service.py google_drive.py ./
COPY search_router.py documents_router.py chat_router.py admin_router.py ./
COPY main_modular.py ./
COPY Clair-sys-prompt.txt ./

# Create symlink for backward compatibility
RUN ln -sf main_modular.py main.py

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

# Use exec form for better signal handling in Cloud Run  
# Run the enhanced modular application
CMD ["python", "main_modular.py"]