#!/usr/bin/env python3

import os
from dotenv import load_dotenv
import json


# Standard
from time import sleep

# Internal
from utils import td

# External
import stomp

load_dotenv()
feed_username = os.getenv("FEED_USERNAME")
feed_password = os.getenv("FEED_PASSWORD")
td_topic = f"/topic/{os.getenv('TD_TOPIC', 'TD_ALL_SIG_AREA')}"
hostname = os.getenv("HOST", "publicdatafeeds.networkrail.co.uk")
port = os.getenv("PORT", 61618)

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


class Listener(stomp.ConnectionListener):
    _mq: stomp.Connection

    def __init__(self, mq: stomp.Connection, durable=False):
        self._mq = mq
        self.is_durable = durable

    def on_message(self, frame):
        headers, message_raw = frame.headers, frame.body
        # print(json.dumps(headers, indent=2))
        parsed_body = json.loads(message_raw)

        if self.is_durable:
            # Acknowledging messages is important in client-individual mode
            self._mq.ack(id=headers["message-id"], subscription=headers["subscription"])

        if "TD_" in headers["destination"]:
            if td_data := td.parse_td_frame(parsed_body):
                for td_entry in td_data:
                    td_from = f"{td_entry.get('area_id')}{td_entry.get('from')}"
                    td_to = f"{td_entry.get('area_id')}{td_entry.get('to')}"
                    headcode = td_entry.get("description")
                    if (
                        td_to not in locs_from_dict
                        and td_to not in locs_to_dict
                        and td_from not in locs_from_dict
                        and td_from not in locs_to_dict
                        and headcode not in headcodes
                    ):
                        continue
                    # If the td_to is in locs_from, the train is coming
                    if td_to in locs_from_dict:
                        direction = locs_from_dict[td_to]
                        print(f"Train approaching {td_to}, direction: {direction}")
                    print(
                        "{} [{:2}] {:2} {:4} {:>5}->{:5}".format(
                            td_entry.get("timestamp"),
                            td_entry.get("type"),
                            td_entry.get("area_id"),
                            td_entry.get("description"),
                            td_entry.get("from"),
                            td_entry.get("to"),
                        )
                    )

    def on_error(self, frame):
        print("received an error {}".format(frame.body))

    def on_disconnected(self):
        print("disconnected")


if __name__ == "__main__":
    # https://stomp.github.io/stomp-specification-1.2.html#Heart-beating
    # We're committing to sending and accepting heartbeats every 5000ms
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
    print("Subscribed to TD topic")
    while td_connection.is_connected():
        sleep(1)
