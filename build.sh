#!/usr/bin/env bash
# Install system dependencies
apt-get update
apt-get install -y tesseract-ocr ffmpeg libmysqlclient-dev

# Exit on error
set -o errexit
