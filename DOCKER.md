# Docker build and run instructions for train-catcher

## Building the Docker image

```bash
docker-compose build
```

## Running the container

```bash
docker-compose up -d
```

## Viewing logs

```bash
docker-compose logs -f train-catcher
```

## Stopping the container

```bash
docker-compose down
```

## Raspberry Pi Notes

The Dockerfile uses `python:3.13-slim` which is compatible with both ARM32 and ARM64 architectures on Raspberry Pi.

If you want to limit resource usage on your Raspberry Pi, uncomment the `deploy` section in `docker-compose.yml` to restrict CPU and memory allocation.

## Environment variables

Make sure your `.env` file is present in the project root with all required environment variables:
- FEED_USERNAME
- FEED_PASSWORD
- HOSTNAME
- PORT
- LOCS
- TIPLOC_CODE
- HEADCODES
