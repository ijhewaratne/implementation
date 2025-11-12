# Dockerfile for Branitz Energy Decision AI - Enhanced Multi-Agent System with Google ADK
# Multi-stage build for optimized production deployment

# Stage 1: Base Python environment
FROM python:3.9-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    libspatialindex-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Development environment
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    black \
    ruff \
    jupyter \
    ipython

# Copy source code
COPY . .

# Create necessary directories
RUN mkdir -p processed/cha processed/dha processed/kpi processed/comparison \
    && mkdir -p agents\ copy/configs \
    && mkdir -p logs

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port for Jupyter (if needed)
EXPOSE 8888

# Default command for development
CMD ["python", "scripts/deploy_adk_system.py", "--environment", "development"]

# Stage 3: Production environment
FROM base as production

# Copy source code
COPY . .

# Create necessary directories
RUN mkdir -p processed/cha processed/dha processed/kpi processed/comparison \
    && mkdir -p agents\ copy/configs \
    && mkdir -p logs

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command for production
CMD ["python", "start_adk_system.py"]

# Stage 4: ADK-specific environment
FROM production as adk-production

# Set ADK-specific environment variables
ENV ADK_ENABLED=true \
    FALLBACK_ENABLED=true \
    GEMINI_API_KEY=""

# Copy ADK-specific configurations
COPY configs/gemini_config.yml agents\ copy/configs/

# Create ADK-specific directories
RUN mkdir -p agents\ copy/adk

# ADK-specific health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from agents.copy.run_enhanced_agent_system import ADKAgentRunner; print('ADK System Healthy')"

# Default command for ADK production
CMD ["python", "start_adk_system.py"]
