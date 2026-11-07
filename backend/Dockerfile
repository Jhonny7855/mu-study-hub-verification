# MU STUDY HUB - AI Document Verification Bot
# Docker build for deployment

FROM python:3.11-slim

# System dependencies for PDF processing and OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    libtesseract-dev \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Tesseract language data (English + Hindi for MU)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy dependency files first for layer caching
COPY backend/pyproject.toml backend/requirements.txt* ./

# Install Python dependencies
RUN pip install --no-cache-dir uv && \
    uv pip install -r requirements.txt --system

# Copy application code
COPY backend/app ./app
COPY backend/migrations ./migrations

# Create non-root user for security
RUN useradd -m -d /app appuser && chown -R appuser /app
USER appuser

# Expose FastAPI port
EXPOSE 8000

# Create storage directory
RUN mkdir -p /app/storage/uploads

# Run the server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]