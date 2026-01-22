# Use official Python image as base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies and clean up apt cache
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Add Rust to PATH
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy application code into the container
COPY . /app

# Upgrade pip and install maturin for Rust
RUN pip install --upgrade pip && \
    pip install maturin

# Build and install the Rust module
WORKDIR /app/rust/rustism
RUN maturin build --release && \
    pip install target/wheels/*.whl

# Go back to app
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

ENV GUNICORN_CMD_ARGS="--workers=1 --bind=0.0.0.0:8405"

# Expose application ports
EXPOSE 8405

# Start Gunicorn server with access logs enabled
CMD ["gunicorn", "--bind", "0.0.0.0:8405", "--access-logfile", "-", "--error-logfile", "-", "--capture-output", "main:app"]
