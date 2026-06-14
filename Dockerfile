# Use a lightweight Python base image
FROM python:3.12-slim

# Install system dependencies needed for network monitoring
RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping \
    iproute2 \
    network-manager \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency definition first to leverage Docker cache
COPY requirements.txt .

# Install dependencies (gunicorn will be installed from requirements)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Ensure data directory exists
RUN mkdir -p data config

# Expose the dashboard port (default 5000)
EXPOSE 5000

# Run the application with Gunicorn
# Using 1 worker and 4 threads to support SSE and background auto-ping loop
CMD ["gunicorn", "-w", "1", "--threads", "4", "-b", "0.0.0.0:5000", "dashboard.app:create_app(auto_run=True)"]
