# Use official Python image as base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies and clean up apt cache
RUN apt-get update && apt-get install -y --no-install-recommends \
    git && \
    build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Rust toolchain
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:$PATH"

# Install maturin
RUN pip install maturin

# Copy application code into the container
COPY . /app

# Build the Rust component
RUN cd rust/rustism && maturin build --out /tmp/wheels

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir /tmp/wheels/*.whl && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn eventlet && \
    rm -rf /tmp/wheels

# Set environment variables
ENV FLASK_ENV=production

# Expose application ports
EXPOSE 8405 8406

# Make start.sh executable
RUN chmod +x start.sh

# Start both servers
CMD ["./start.sh"]
