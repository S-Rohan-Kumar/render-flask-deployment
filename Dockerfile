# Use Python 3.10 to support numpy==2.2.4 and pydantic==2.11.3
FROM python:3.11

# Install system dependencies with proper error handling
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
    libmysqlclient-dev \      # Added for mysqlclient==2.2.7
    libssl-dev \              # Added for cryptography==44.0.2
    libffi-dev \              # Added for cffi==1.17.1
    libjpeg-dev \             # Added for pillow==10.4.0
    zlib1g-dev \              # Added for pillow==10.4.0
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
ENV PORT=10000  # Fallback for local testing; Render overrides this

# Upgrade pip to avoid version warnings
RUN pip install --upgrade pip

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Verify installations
RUN tesseract --version && ffmpeg -version

# Copy application code
COPY . .

# Make sure templates and static directories exist
RUN mkdir -p templates static

# Entry point command for Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--timeout", "120", "--workers", "3", "app:app"]
