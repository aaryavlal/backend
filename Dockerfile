# Use official Python image as base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Rust and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    pkg-config \
    libssl-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && . ~/.cargo/env && rustup target add x86_64-unknown-linux-gnu

# Add Rust to PATH
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy application code into the container
COPY . /app

# Install maturin and build the Rust extension
RUN pip install --upgrade pip && \
    pip install --no-cache-dir maturin && \
    cd rust/rustism && maturin build --release --out /tmp/wheels && \
    pip install --no-cache-dir /tmp/wheels/*.whl

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn eventlet

# Set environment variables
ENV FLASK_ENV=production

# Expose application ports
EXPOSE 8405 8406

# Start Gunicorn server
CMD ["gunicorn", "main:app"]
