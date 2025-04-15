FROM python:3.12

# Install system dependencies with proper error handling
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
    gcc \
    g++ \
    build-essential \
    libpoppler-cpp-dev \
    pkg-config \
    python3-dev \
    wget \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Create and set permissions for temp directory
RUN mkdir -p /app/temp && chmod 777 /app/temp
RUN mkdir -p /app/templates /app/static && chmod 777 /app/templates /app/static

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TESSERACT_PATH=/usr/bin/tesseract
ENV RENDER_DISK_PATH=/app
ENV TEMP_DIR=/app/temp
ENV PORT=5000

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with error handling
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn

# Verify installations
RUN tesseract --version && ffmpeg -version

# Copy application code
COPY . .

# Ensure proper permissions
RUN chmod -R 755 /app

# Entry point command with health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:$PORT/health || exit 1

CMD ["sh", "-c", "gunicorn --workers=4 --timeout=300 --bind 0.0.0.0:$PORT app:app"]
