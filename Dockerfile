FROM python:3.11

WORKDIR /app

# Install system dependencies for mysqlclient, cryptography, pillow, pytesseract, and moviepy
RUN apt-get update && apt-get install -y \
    pkg-config \
    libmysqlclient-dev \
    build-essential \
    python3-dev \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    tesseract-ocr \
    libtesseract-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Use PORT environment variable for Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app:app"]
