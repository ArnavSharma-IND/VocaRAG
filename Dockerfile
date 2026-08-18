# Stage 1: Build Frontend Assets
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python Backend (Hugging Face Spaces / Docker)
FROM python:3.11-slim
WORKDIR /app

# Set non-interactive and unbuffered environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860 \
    HOST=0.0.0.0 \
    HF_HOME=/app/.cache \
    TRANSFORMERS_CACHE=/app/.cache/transformers \
    SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence_transformers

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Pre-download and cache embedding model weights to eliminate runtime cold starts
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')"

# Copy application source code and pre-built frontend
COPY backend/ ./backend/
COPY data/ ./data/
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Hugging Face Spaces non-root user setup (UID 1000)
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/data/storage /app/.cache && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 7860

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
