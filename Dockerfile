# Use uv's Alpine image which includes Python
FROM ghcr.io/astral-sh/uv:alpine

# Set working directory
WORKDIR /app

# Install system dependencies via apk
RUN apk add --no-cache \
    python3 \
    py3-pip

# Copy project files
COPY pyproject.toml uv.lock ./
COPY check_trains.py ./
COPY utils/ ./utils/
COPY static/ ./static/
COPY .env ./.env

# Install dependencies using uv
RUN uv sync

# Expose Flask port
EXPOSE 3300

# Run the application
CMD ["uv", "run", "python", "check_trains.py"]
