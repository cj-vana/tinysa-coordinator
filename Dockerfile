# =============================================================================
# TinySA Coordinator - Multi-stage Dockerfile
# =============================================================================
# Production-ready image optimized for small size:
# - Stage 1: Build frontend with Node.js 20 (Alpine)
# - Stage 2: Production runtime with Python 3.11 (slim) serving backend + static
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Frontend Build
# -----------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files first for better layer caching
COPY frontend/package.json frontend/package-lock.json ./

# Install dependencies (production only where possible, skip optional deps)
RUN npm ci --no-audit --no-fund --ignore-scripts

# Copy frontend source
COPY frontend/ ./

# Build the frontend for production
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2: Production Runtime
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS production

# Set environment variables for optimization
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore

WORKDIR /app

# Install minimal system dependencies in a single layer and clean up
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create non-root user for security
RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --shell /sbin/nologin --no-create-home app

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && rm -rf ~/.cache/pip

# Copy backend code
COPY --chown=app:app backend/ ./backend/

# Copy built frontend from the builder stage
COPY --from=frontend-builder --chown=app:app /app/frontend/dist ./static

# Create data directory for SQLite database with proper permissions
RUN mkdir -p /app/data && chown -R app:app /app/data

# Switch to non-root user
USER app

# Expose the application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application with uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
