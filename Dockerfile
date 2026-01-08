# Use Python 3.13 slim image compatible with Raspberry Pi
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml uv.lock ./
COPY test_stomp.py ./
COPY utils/ ./utils/
COPY static/ ./static/
COPY .env ./.env

# Install Python dependencies using pip (since we're in Docker)
RUN pip install --no-cache-dir \
    flask>=3.1.2 \
    python-dotenv>=1.2.1 \
    pytz>=2025.2 \
    requests>=2.32.5 \
    stomp-py>=8.2.0

# Expose Flask port
EXPOSE 5000

# Run the application
CMD ["python", "test_stomp.py"]
