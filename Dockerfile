# Use uv's Alpine image which includes Python
FROM ghcr.io/astral-sh/uv:alpine

# Set working directory
WORKDIR /app

# Update Alpine packages to get latest security patches
RUN apk update && apk upgrade

# Copy project files
COPY pyproject.toml uv.lock ./
COPY uv.lock ./
COPY check_trains.py ./
COPY includes/ ./includes/
COPY static/ ./static/
COPY .env ./.env


# Install dependencies using uv
RUN uv sync

# Expose Flask port
EXPOSE 3300

# Run the application
CMD ["uv", "run", "python", "check_trains.py"]
