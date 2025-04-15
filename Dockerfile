FROM python:3.12-slim

# Install apt tools and basic dependencies first
RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-utils \
    gnupg \
    dirmngr \
    ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install OCR and media system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    tesseract-ocr-tam \
    tesseract-ocr-tel \
    tesseract-ocr-kan \
    ffmpeg \
    libsndfile1 \
    libpq-dev \
    libpoppler-cpp-dev \
    pkg-config \
    wget \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    && pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn && \
    apt-get purge -y build-essential gcc g++ python3-dev && \
    apt-get autoremove -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Setup app folders and permissions
RUN mkdir -p /app/temp /app/templates /app/static && chmod -R 777 /app/temp /app/templates /app/static

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    TESSERACT_PATH=/usr/bin/tesseract \
    RENDER_DISK_PATH=/app \
    TEMP_DIR=/app/temp \
    PORT=5000

# Copy application code
COPY . .

# Final permission setting
RUN chmod -R 755 /app

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:$PORT/health || exit 1

# Start command
CMD ["sh", "-c", "gunicorn --workers=4 --timeout=300 --bind 0.0.0.0:$PORT app:app"]
