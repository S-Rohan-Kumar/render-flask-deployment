# Use a slim Python image
FROM python:3.11

# Install runtime system dependencies and OCR language packs (only keep what you need!)
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

# Copy and install Python dependencies first (for caching)
COPY requirements.txt .

# Install build dependencies temporarily, install Python packages, then clean up
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

# Set up folders with permissions
RUN mkdir -p /app/temp /app/templates /app/static && chmod -R 777 /app/temp /app/templates /app/static

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    TESSERACT_PATH=/usr/bin/tesseract \
    RENDER_DISK_PATH=/app \
    TEMP_DIR=/app/temp \
    PORT=5000

# Copy the rest of the app
COPY . .

# Final permissions
RUN chmod -R 755 /app

# Health check (Render friendly)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:$PORT/health || exit 1

# Run the app
CMD ["sh", "-c", "gunicorn --workers=4 --timeout=300 --bind 0.0.0.0:$PORT app:app"]
