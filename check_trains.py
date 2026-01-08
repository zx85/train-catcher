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
from flask import Flask

# Internal
from utils import td, trust

load_dotenv()
feed_username = os.getenv("FEED_USERNAME")
feed_password = os.getenv("FEED_PASSWORD")
hostname = os.getenv("HOSTNAME")
port = os.getenv("PORT")
locs_from = [
    (loc.split(":")[0], loc.split(":")[2]) for loc in os.getenv("LOCS").split(",")
]
locs_to = [
    (loc.split(":")[1], loc.split(":")[2]) for loc in os.getenv("LOCS").split(",")
]
tiploc_code = os.getenv("TIPLOC_CODE")
headcodes = [headcode for headcode in os.getenv("HEADCODES", "").split(",")]

# Create dictionaries for faster lookup
locs_from_dict = {loc: dir for loc, dir in locs_from}
locs_to_dict = {loc: dir for loc, dir in locs_to}

# Global dictionary to store current state of approaching trains
approaching_trains = {}  # headcode: {'direction': dir, 'location': td_from, 'timestamp': ...}


class Listener(stomp.ConnectionListener):
    _mq: stomp.Connection

    def __init__(self, mq: stomp.Connection, durable=False):
        self._mq = mq
        self.is_durable = durable

    def get_service(self, headcode):
        print(f"checking services for {headcode}")
        service_details = {}
        if services := requests.get(
            f"http://192.168.75.4:3333/schedules/headcode/{headcode}"
        ).json():
            print(f"Found {len(services)} services for {headcode}")
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
        # print(json.dumps(headers, indent=2))
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

                    # If the td_from is in locs_from, the train is coming
                    if td_to in locs_from_dict:
                        direction = locs_from_dict[td_to]
                        print(f"Train coming from {td_from}, direction: {direction}")
                        if len(headcode) == 4:
                            service = self.get_service(headcode)
                            approaching_trains[headcode] = {
                                "direction": direction,
                                "location": td_from,
                                "headcode": headcode,
                                "timestamp": timestamp,
                                **service,
                            }
                            print(json.dumps(approaching_trains[headcode], indent=2))
                    # If the td_from is in locs_to, the train has left
                    elif td_from in locs_to_dict:
                        if headcode in approaching_trains:
                            del approaching_trains[headcode]
                        direction = locs_to_dict[td_from]
                        print(f"Train has left {td_from}, direction: {direction}")

        # else:
        #     print("Unknown destination: ", headers["destination"])

    def on_error(self, frame):
        print("received an error {}".format(frame.body))

    def on_disconnected(self):
        print("disconnected")


if __name__ == "__main__":
    # Flask app with static folder
    app = Flask(__name__, static_folder="static", static_url_path="")

    @app.route("/")
    def index():
        return app.send_static_file("index.html")

    @app.route("/trains")
    def get_trains():
        return approaching_trains

    @app.route("/favicon.ico")
    def favicon():
        return app.send_static_file("favicon.ico")

    # Function to run the STOMP listener in a thread
    def run_listener():
        td_connection = stomp.Connection(
            [(hostname, port)],
            keepalive=True,
            heartbeats=(3300, 3300),
        )
        trust_connection = stomp.Connection(
            [(hostname, port)],
            keepalive=True,
            heartbeats=(3300, 3300),
        )
        td_connection.set_listener("", Listener(td_connection, durable=True))
        trust_connection.set_listener("", Listener(trust_connection))
        # Connect to feed
        td_connect_headers = {
            "username": feed_username,
            "passcode": feed_password,
            "wait": True,
            "client-id": feed_username,
        }
        trust_connect_headers = {
            "username": feed_username,
            "passcode": feed_password,
            "wait": True,
        }

        td_connection.connect(**td_connect_headers)
        trust_connection.connect(**trust_connect_headers)
        td_topic = "/topic/TD_ANG_SIG_AREA"
        trust_topic = "/topic/TRAIN_MVT_ALL_TOC"

        # Subscription
        td_subscribe_headers = {
            "destination": td_topic,
            "id": 1,
            "activemq.subscriptionName": feed_username + td_topic,
            "ack": "client-individual",
        }
        trust_subscribe_headers = {"destination": trust_topic, "id": 2}
        td_connection.subscribe(**td_subscribe_headers)
        print("Subscribed to TD topic")
        trust_connection.subscribe(**trust_subscribe_headers)
        print("Subscribed to TRUST topic")
        while td_connection.is_connected() or trust_connection.is_connected():
            sleep(1)

    # Start the listener in a separate daemon thread
    listener_thread = threading.Thread(target=run_listener, daemon=True)
    listener_thread.start()

    # Run the Flask app (can be interrupted with CTRL-C)
    try:
        app.run(host="0.0.0.0", port=3300)
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
