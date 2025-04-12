#!/usr/bin/env bash
# Install system dependencies
apt-get update
apt-get install -y tesseract-ocr tesseract-ocr-eng ffmpeg libmysqlclient-dev

# Verify Tesseract installation
tesseract --version
which tesseract

# Exit on error
set -o errexit
