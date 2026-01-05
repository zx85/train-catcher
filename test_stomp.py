#!/usr/bin/env python3

# Standard
import json
from time import sleep
import os
from dotenv import load_dotenv
import requests

# Third party
import stomp

# Internal
from utils import td, trust

load_dotenv()
feed_username = os.getenv("FEED_USERNAME")
feed_password = os.getenv("FEED_PASSWORD")
hostname = os.getenv("HOSTNAME")
port = os.getenv("PORT")
locs_from = [loc.split(":")[0] for loc in os.getenv("LOCS").split(",")]
locs_to = [loc.split(":")[1] for loc in os.getenv("LOCS").split(",")]


class Listener(stomp.ConnectionListener):
    _mq: stomp.Connection

    def __init__(self, mq: stomp.Connection, durable=False):
        self._mq = mq
        self.is_durable = durable

    def get_service(headcode):
        print(f"checking services for {headcode}")
        if services := requests.get(
            f"http://localhost:3333/schedules/headcode/{headcode}"
        ).json():
            print(f"Found {len(services)} services for {headcode}")
            for service in services:
                for location in service.get("schedule_location"):
                    if location.get("tiploc_code") == "BSTEDMS":
                        return service

    def on_message(self, frame):
        headers, message_raw = frame.headers, frame.body
        # print(json.dumps(headers, indent=2))
        parsed_body = json.loads(message_raw)

        if self.is_durable:
            # Acknowledging messages is important in client-individual mode
            self._mq.ack(id=headers["message-id"], subscription=headers["subscription"])

        # not a whole lot of point in using this
        # if "TRAIN_MVT_" in headers["destination"]:
        #     if trust_data := trust.parse_trust_frame(parsed_body):
        #         if trust_data["headcode"] in ("4M76", "2W29", "2E80"):
        #             print(trust_data["summary"])
        #             print(json.dumps(trust_data["body"], indent=2))

        # elif "TD_" in headers["destination"]:
        if "TD_" in headers["destination"]:
            if td_data := td.parse_td_frame(parsed_body):
                for td_entry in td_data:
                    td_from = f"{td_entry.get('area_id')}{td_entry.get('from')}"
                    td_to = f"{td_entry.get('area_id')}{td_entry.get('to')}"
                    if td_from in locs_from or td_to in locs_to:
                        if " " in td_entry.get("description"):
                            headcode = td_entry.get("description").split(" ")[1]
                            service = self.get_service(headcode)
                            print(service)
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

        # else:
        #     print("Unknown destination: ", headers["destination"])

    def on_error(self, frame):
        print("received an error {}".format(frame.body))

    def on_disconnected(self):
        print("disconnected")


if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument(
    #     "-d",
    #     "--durable",
    #     action="store_true",
    #     help="Request a durable subscription. Note README before trying this.",
    # )
    # action = parser.add_mutually_exclusive_group(required=False)
    # action.add_argument(
    #     "--td", action="store_true", help="Show messages from TD feed", default=True
    # )
    # action.add_argument(
    #     "--trust", action="store_true", help="Show messages from TRUST feed"
    # )

    # args = parser.parse_args()

    # https://stomp.github.io/stomp-specification-1.2.html#Heart-beating
    # We're committing to sending and accepting heartbeats every 5000ms

    # check to see if the json is there

    td_connection = stomp.Connection(
        [(hostname, port)],
        keepalive=True,
        heartbeats=(5000, 5000),
    )
    trust_connection = stomp.Connection(
        [(hostname, port)],
        keepalive=True,
        heartbeats=(5000, 5000),
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
    # Determine topic to subscribe
    # topic = None
    # if args.trust:
    #     topic = "/topic/TRAIN_MVT_ALL_TOC"
    # elif args.td:
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
