#!/usr/bin/env python3

# Standard
import json
from time import sleep
import os
from dotenv import load_dotenv
import requests
import threading

# Third party
import stomp
from flask import Flask, send_from_directory
from flask_cors import CORS

# Internal
from utils import td

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__) 

load_dotenv()
feed_username = os.getenv("FEED_USERNAME")
feed_password = os.getenv("FEED_PASSWORD")
td_topic = f"/topic/{os.getenv('TD_TOPIC', 'TD_ALL_SIG_AREA')}"
signalmaps_url = f"https://signalmaps.co.uk/#{os.getenv('SIGNALMAPS_LOC','')}"
schedule_host = os.getenv("SCHEDULE_HOST", None)
schedule_port = os.getenv("SCHEDULE_PORT", None)
hostname = os.getenv("HOST", "publicdatafeeds.networkrail.co.uk")
port = os.getenv("PORT", 61618)

locs_from = [
    (loc.split(":")[0], loc.split(":")[2]) for loc in os.getenv("LOCS").split(",")
]
locs_to = [
    (loc.split(":")[1], loc.split(":")[2]) for loc in os.getenv("LOCS").split(",")
]
tiploc_code = os.getenv("TIPLOC_CODE", "")

# Create dictionaries for faster lookup
locs_from_dict = {loc: dir for loc, dir in locs_from}
locs_to_dict = {loc: dir for loc, dir in locs_to}

# Global dictionary to store current state of approaching trains
trains_data = {
    'metadata':
      {'signalmaps_url': signalmaps_url
      },
    'trains':
      {}
}  


class Listener(stomp.ConnectionListener):
    _mq: stomp.Connection

    def __init__(self, mq: stomp.Connection, durable=False):
        self._mq = mq
        self.is_durable = durable

    def get_service(self, headcode):
        logger.info(f"checking services for {headcode} passing {tiploc_code}")
        service_details = {}
        if services := requests.get(
            f"http://{schedule_host}:{schedule_port}/schedules/headcode/{headcode}"
        ).json():
            logger.info(f"Found {len(services)} services for {headcode}")
            for service in services:
                for location in service.get("schedule_location"):
                    if location.get("tiploc_code") == tiploc_code:
                        service_details = {
                            "train_uid": service.get("CIF_train_uid"),
                            "atoc": service.get("atoc_code_description"),
                            "type": service.get("CIF_train_category_description"),
                            "power": service.get("CIF_power_type_description"),
                            "speed": service.get("CIF_speed"),
                            "origin": service.get("origin"),
                            "destination": service.get("destination"),
                        }
        return service_details

    def on_message(self, frame):
        headers, message_raw = frame.headers, frame.body
        logger.debug(json.dumps(headers, indent=2))
        parsed_body = json.loads(message_raw)

        if self.is_durable:
            # Acknowledging messages is important in client-individual mode
            self._mq.ack(id=headers["message-id"], subscription=headers["subscription"])

        # elif "TD_" in headers["destination"]:
        if "TD_" in headers["destination"]:
            if td_data := td.parse_td_frame(parsed_body):
                for td_entry in td_data:
                    headcode = td_entry.get("description")
                    td_from = f"{td_entry.get('area_id')}{td_entry.get('from')}"
                    td_to = f"{td_entry.get('area_id')}{td_entry.get('to')}"
                    timestamp = td_entry.get("timestamp")
                    logger.debug(f'{headcode}: {td_from}->{td_to} @ {timestamp}')

                    # If the td_from is in locs_from, the train is coming
                    if td_to in locs_from_dict:
                        direction = locs_from_dict[td_to]
                        logger.info(f"Train coming from {td_from}, direction: {direction}")
                        # only get the service data if there's a shedule host set
                        service = self.get_service(headcode) if schedule_host else {}
                        trains_data['trains'][headcode] = {
                            "direction": direction,
                            "location": td_from,
                            "headcode": headcode,
                            "timestamp": timestamp,
                            **service,
                        }
                        logger.debug(json.dumps(trains_data['trains'][headcode], indent=2))
                    # If the td_from is in locs_to, the train has left
                    elif td_from in locs_to_dict:
                        if headcode in trains_data['trains']:
                            del trains_data['trains'][headcode]
                        direction = locs_to_dict[td_from]
                        logger.info(f"Train has left {td_from}, direction: {direction}")

        # else:
        #     logger.warning("Unknown destination: ", headers["destination"])

    def on_error(self, frame):
        logger.error("received an error {}".format(frame.body))

    def on_disconnected(self):
        logger.info("disconnected")


if __name__ == "__main__":
    # Flask app with static folder
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    CORS(app)  # Enable CORS for all routes

    # Disable Flask request logging
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.WARNING)

    @app.route("/")
    def index():
        return send_from_directory("static", "index.html")

    @app.route("/trains")
    def get_trains():
        return trains_data

    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory("static", "favicon.ico")

    @app.route("/style.css")
    def style_css():
        return send_from_directory("static", "style.css")

    @app.route("/trains.js")
    def trains_js():
        return send_from_directory("static", "trains.js")

    # Function to run the STOMP listener in a thread
    def run_listener():
        logger.info("Connecting to Stomp...")
        td_connection = stomp.Connection(
            [(hostname, port)],
            keepalive=True,
            heartbeats=(5000, 5000),
        )
        td_connection.set_listener("", Listener(td_connection, durable=True))
        # Connect to feed
        td_connect_headers = {
            "username": feed_username,
            "passcode": feed_password,
            "wait": True,
            "client-id": feed_username,
        }
        td_connection.connect(**td_connect_headers)

        # Subscription
        td_subscribe_headers = {
            "destination": td_topic,
            "id": 1,
            "activemq.subscriptionName": feed_username + td_topic,
            "ack": "client-individual",
        }
        td_connection.subscribe(**td_subscribe_headers)
        logger.info("Subscribed to TD topic")
        while td_connection.is_connected():
            sleep(1)

    # Start the listener in a separate daemon thread
    listener_thread = threading.Thread(target=run_listener, daemon=True)
    listener_thread.start()

    # Run the Flask app (can be interrupted with CTRL-C)
    logger.info("Starting Flask server at http://0.0.0.0:3300")
    try:
        app.run(host="0.0.0.0", port=3300, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("\nShutting down gracefully...")
