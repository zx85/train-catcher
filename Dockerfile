# Get some alpine uv
FROM ghcr.io/astral-sh/uv:alpine

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY check_trains.py ./
COPY utils/ ./utils/
COPY static/ ./static/
COPY .env ./.env


# Expose Flask port
EXPOSE 3300

# Run the application
CMD ["uv", "run", "python", "check_trainspy"]
