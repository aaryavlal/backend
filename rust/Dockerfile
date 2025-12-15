# Build stage for Rust extension
FROM rust:1.75-slim as rust-builder

# Install Python and maturin build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install maturin in the virtual environment
RUN pip install --no-cache-dir maturin

# Copy only the Rust project files
WORKDIR /build
COPY rust/rustism /build/rustism

# Build the Rust extension wheel
WORKDIR /build/rustism
RUN maturin build --release --out /build/wheels

# Final stage - Python application
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies and clean up apt cache
RUN apt-get update && apt-get install -y --no-install-recommends \
    git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the built wheel from the builder stage
COPY --from=rust-builder /build/wheels/*.whl /tmp/wheels/

# Copy application code into the container
COPY . /app

# Upgrade pip, install the local rustism wheel first, then other dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir /tmp/wheels/*.whl && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn && \
    rm -rf /tmp/wheels

# Set environment variables
ENV FLASK_ENV=production \
    GUNICORN_CMD_ARGS="--workers=5 --threads=2 --bind=0.0.0.0:8587 --timeout=30 --access-logfile -"

# Expose application port
EXPOSE 8587

# Start Gunicorn server
CMD ["gunicorn", "main:app"]
