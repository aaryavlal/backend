FROM python:3.11

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y git build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip

# Install Rust toolchain
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:$PATH"

# Install Maturin
RUN pip install maturin

COPY .. /app

# Build the Rust component
RUN cd /app/rust/rustism && maturin build --release --out /tmp/wheels

# Install Python requirements (install local wheel first)
RUN pip install --no-cache-dir /tmp/wheels/*.whl && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /tmp/wheels

# Add WebSocket support
RUN pip install eventlet

# Install Gunicorn for production
RUN pip install gunicorn

# Expose the port used by your Flask-SocketIO server
EXPOSE 8406

ENV FLASK_ENV=production

# Run with Gunicorn in headless mode
CMD ["gunicorn", "--worker-class", "eventlet", "--bind=0.0.0.0:8500", "socket_server:app"]
