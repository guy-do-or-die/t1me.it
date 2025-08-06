# Frontend build stage
FROM oven/bun:1 as frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY app/package.json app/bun.lock* ./

# Install frontend dependencies
RUN bun install

# Copy frontend source code
COPY app/ ./

# Build frontend
RUN bun run build

# Backend stage
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Configure Poetry
RUN poetry config virtualenvs.create false

# Set working directory
WORKDIR /app

# Copy Poetry files first for better caching
COPY pyproject.toml poetry.lock* ./

# Install Python dependencies
RUN poetry install

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application code
COPY . .

# Copy built frontend from frontend-builder stage
COPY --from=frontend-builder /app/static ./static

# Create cache directory
RUN mkdir -p cache

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "run.py"]
