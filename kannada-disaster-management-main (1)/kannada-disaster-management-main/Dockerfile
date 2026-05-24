# Production Dockerfile for Kannada Disaster AI
# Build stage to configure dependencies and model files

FROM python:3.10-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    portaudio19-dev \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Expose server port
EXPOSE 5000

# Set environment defaults
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Run the app
CMD ["python", "app.py"]
