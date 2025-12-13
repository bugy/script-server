# Multi-stage build for script-server

# Stage 1: Build frontend
# Using Node 16 for compatibility with older webpack
FROM node:16-alpine AS frontend-builder

WORKDIR /app/web-src

# Copy package files first for better caching
COPY web-src/package*.json ./
RUN npm ci

# Copy frontend source and build
COPY web-src/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for pty support
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/
COPY launcher.py ./
COPY conf/ ./conf/

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/web /app/web

# Create directories for configs and logs
RUN mkdir -p /app/conf/runners /app/conf/scripts /app/logs

# Default port
EXPOSE 5000

# Environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python3", "launcher.py"]

