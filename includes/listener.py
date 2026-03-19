import stomp
import json
import logging
from time import sleep
from includes import td
import includes.config as config
from includes.train_manager import train_manager

logger = logging.getLogger(__name__)


class Listener(stomp.ConnectionListener):
    _mq: stomp.Connection

    def __init__(self, mq: stomp.Connection, manager, durable=False):
        self._mq = mq
        self.manager = manager
        self.is_durable = durable

    def on_message(self, frame):
        headers, message_raw = frame.headers, frame.body
        logger.debug(json.dumps(headers, indent=2))
        parsed_body = json.loads(message_raw)

        if self.is_durable:
            self._mq.ack(id=headers["message-id"], subscription=headers["subscription"])

        if "TD_" in headers["destination"]:
            if td_data := td.parse_td_frame(parsed_body):
                for td_entry in td_data:
                    headcode = td_entry.get("description")
                    td_from = f"{td_entry.get('area_id')}{td_entry.get('from')}"
                    td_to = f"{td_entry.get('area_id')}{td_entry.get('to')}"
                    timestamp = td_entry.get("timestamp")
                    logger.debug(f"{headcode}: {td_from}->{td_to} @ {timestamp}")

                    if td_to in config.LOCS_FROM_DICT:
                        self.manager.add_train(td_entry)
                    elif td_from in config.LOCS_TO_DICT:
                        self.manager.remove_train(td_entry)

    def on_error(self, frame):
        logger.error("received an error {}".format(frame.body))

    def on_disconnected(self):
        logger.warning("STOMP listener disconnected.")


def run_listener():
    while True:
        try:
            logger.info("Connecting to Stomp...")
            td_connection = stomp.Connection(
                [(config.HOSTNAME, config.PORT)],
                keepalive=True,
                heartbeats=(5000, 5000),
            )
            td_connection.set_listener(
                "", Listener(td_connection, train_manager, durable=True)
            )

            td_connect_headers = {
                "username": config.FEED_USERNAME,
                "passcode": config.FEED_PASSWORD,
                "wait": True,
                "client-id": config.FEED_USERNAME,
            }
            td_connection.connect(**td_connect_headers)

            td_subscribe_headers = {
                "destination": config.TD_TOPIC,
                "id": 1,
                "activemq.subscriptionName": config.FEED_USERNAME + config.TD_TOPIC,
                "ack": "client-individual",
            }
            td_connection.subscribe(**td_subscribe_headers)
            logger.info("Subscribed to TD topic. Listening for messages.")
            while td_connection.is_connected():
                sleep(1)
        except stomp.exception.ConnectFailedException as e:
            logger.warning(f"Failed to connect to STOMP: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in listener: {e}", exc_info=True)

        logger.info("Attempting to reconnect in 30 seconds...")
        sleep(30)
