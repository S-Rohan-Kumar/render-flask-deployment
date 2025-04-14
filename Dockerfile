FROM python:3.11

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    tesseract-ocr-eng \
    ffmpeg \
    libavcodec-extra \
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

# Create temp directory
RUN mkdir -p /tmp

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TESSERACT_PATH=/usr/bin/tesseract
ENV RENDER_DISK_PATH=/app
ENV TEMP_DIR=/tmp
ENV PORT=5000

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Verify installations
RUN tesseract --version && ffmpeg -version

# Copy application code
COPY . .

# Make sure templates and static directories exist
RUN mkdir -p templates static

# Entry point command
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT --timeout 300 --workers 1 app:app"]
