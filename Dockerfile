FROM python:3.12

# Install system dependencies with proper error handling
RUN apt-get update && apt-get install -y \
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

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TESSERACT_PATH=/usr/bin/tesseract
ENV RENDER_DISK_PATH=/app
ENV TEMP_DIR=/app/temp
ENV PORT=5000
# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Verify installations
RUN tesseract --version && ffmpeg -version

# Copy application code
COPY . .

# Make sure templates and static directories exist
RUN mkdir -p templates static

# Entry point command
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT --timeout 120 app:app"]
