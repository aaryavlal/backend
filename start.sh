#!/bin/bash

# Start the main Flask app with Gunicorn
gunicorn --workers=5 --threads=2 --bind=0.0.0.0:8405 --timeout=30 --access-logfile - main:app &

# Start the SocketIO server with Gunicorn using eventlet
gunicorn --worker-class eventlet --workers=1 --bind=0.0.0.0:8500 socket.socket_server:app &

# Wait for both processes
wait
