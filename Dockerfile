# syntax=docker/dockerfile:1

# --- Frontend Build Stage ---
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
# We set VITE_API_BASE_URL to /api so that it uses the relative path proxied by Nginx
ENV VITE_API_BASE_URL=/api
RUN npm run build

# --- Backend & Final Image Stage ---
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=backend.app \
    UPLOAD_FOLDER=/app/uploads \
    DATABASE_URL=sqlite:////app/data.sqlite

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir gunicorn uv && \
    uv pip install --system .

# Copy backend code and scripts
COPY backend/ ./backend/
COPY scripts/ ./scripts/
COPY migrations/ ./migrations/
COPY entrypoint.sh ./

# Copy built frontend from frontend-builder stage
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

# Copy Nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create upload directory and set permissions
RUN mkdir -p /app/uploads && \
    chmod +x /app/entrypoint.sh

# Security: Adjust permissions for Nginx and App
# In a slim image, we might need to adjust some paths for the nginx user
RUN touch /var/run/nginx.pid && \
    mkdir -p /var/cache/nginx /var/lib/nginx /var/log/nginx && \
    chown -R www-data:www-data /var/run/nginx.pid /var/cache/nginx /var/lib/nginx /var/log/nginx /usr/share/nginx/html /app

# Switch to non-root user
USER www-data

# Expose port 80
EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost/health || exit 1

# Entrypoint script handles migrations and starts services
ENTRYPOINT ["/app/entrypoint.sh"]
