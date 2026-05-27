# Train Catcher

Train Catcher is a Python application that monitors live train movements using Network Rail's Open Data feeds. It provides a real-time web interface to track trains passing between specific signalling locations (berths).

## How it works

The application connects to the Network Rail Open Data platform using the STOMP protocol. It subscribes to Train Describer (TD) messages, which represent train movements across the rail network.

By configuring specific "from" and "to" berths (locations), Train Catcher listens for trains moving between these points. When a movement is detected, it captures the train's headcode and direction.

Optionally, it can query a separate **Schedule API** to fetch detailed information about the service (such as origin, destination, operator, and vehicle type) to enrich the display data.

## Key Functions

*   **Real-time Monitoring**: Live dashboard of trains passing your configured monitoring points.
*   **Schedule Integration**: Fetches full service details (Origin, Destination, Power Type) from a schedule API.
*   **History**: Logs movements to a local database for historical review.
*   **Docker Ready**: Simple deployment using Docker Compose.

## Requirements

*   **Network Rail Account**: A registered account at [Network Rail Data Feeds](https://datafeeds.networkrail.co.uk/).
*   **Docker** (Recommended) or Python 3.10+.
*   **(Optional) Schedule API**: A running instance of `uk-rail-schedule-api` to provide train details.

## Schedule Data API Setup

To get meaningful data (like "London Euston to Manchester Piccadilly") instead of just a headcode (e.g., "1H05"), this project is designed to work with a local schedule API.

This requires the following service to be running:

[andrewl/uk-rail-schedule-api](andrewl/uk-rail-schedule-api)

The latest version of uk-rail-schedule-api now builds the Go app natively as part of Docker, so (in theory) will work on any platform that supports the Go libraries.

Once set up, configure the `SCHEDULE_HOST` and `SCHEDULE_PORT` in your `.env` file to point to it.

## Environment Variables

Create a `.env` file in the project root. Below are the required and optional variables:

### Network Rail Connection
*   `FEED_USERNAME`: Your Network Rail Data Feed email/username.
*   `FEED_PASSWORD`: Your Network Rail Data Feed password.
*   `TD_TOPIC`: The topic for the signalling area to monitor (e.g., `TD_ALL_SIG_AREA` or `TD_MC_SIG_AREA`).
*   `HOST`: (Optional) STOMP host, defaults to `publicdatafeeds.networkrail.co.uk`.
*   `PORT`: (Optional) STOMP port, defaults to `61618`.

### Monitoring Configuration
*   `LOCS`: Comma-separated list of monitoring points.
    *   Format: `FROM_BERTH:TO_BERTH:DIRECTION`
    *   Note: Berths should usually include the Area ID (e.g., `K21234`). Use `test_stomp.py` to discover these IDs, cross-referencing to services on [signalmaps.co.uk](https://www.signalmaps.co.uk).
*   `TIPLOC_CODE`: The TIPLOC code of a nearby location (used to match the train against the schedule).
*   `HEADCODES`: (Optional) Comma-separated list of specific headcodes to filter for.

### Schedule API
*   `SCHEDULE_HOST`: IP address of your schedule API (e.g., `192.168.75.4`).
*   `SCHEDULE_PORT`: Port of your schedule API (e.g., `3333`).

### Other
*   `SIGNALMAPS_URL`: (Optional) URL to a visual signal map for reference.
*   `DB_PATH`: Path to the SQLite database (Default: `/app/data/trains.db` inside Docker).

## Running the Project

### Using Docker

Please refer to DOCKER.md for build and run instructions.

```bash
docker-compose up -d