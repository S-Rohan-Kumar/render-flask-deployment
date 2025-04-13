# Use Python 3.10 for compatibility with numpy==2.2.4 and pydantic==2.11.3
FROM python:3.10

# Install system dependencies for mysqlclient, cryptography, pillow, pytesseract, moviepy, etc.
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    tesseract-ocr-eng \
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
    libmysqlclient-dev \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create temp directory with permissions
RUN mkdir -p /app/temp && chmod 777 /app/temp

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TESSERACT_PATH=/usr/bin/tesseract
ENV RENDER_DISK_PATH=/app
ENV TEMP_DIR=/app/temp
ENV PORT 10000

# Upgrade pip to latest version
RUN pip install --upgrade pip

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Verify Tesseract and FFmpeg installations
RUN tesseract --version && ffmpeg -version

# Copy application code
COPY . .

# Ensure templates and static directories exist
RUN mkdir -p templates static

# Run Gunicorn with dynamic port binding for Render
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--timeout", "120", "--workers", "3", "app:app"]
