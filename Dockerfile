# Use official Python image as base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies and clean up apt cache
RUN apt-get update && apt-get install -y --no-install-recommends \
    git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy application code into the container
COPY . /app

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn eventlet

# Set environment variables
ENV FLASK_ENV=production

# Expose application ports
EXPOSE 8405 8406

# Make start.sh executable
RUN chmod +x start.sh

# Start both servers
CMD ["./start.sh"]
