import threading
import json
import logging
import requests
from datetime import datetime
import includes.config as config
import includes.database as database

logger = logging.getLogger(__name__)


class TrainManager:
    def __init__(self):
        self.trains_data = {
            "metadata": {"signalmaps_url": config.SIGNALMAPS_URL},
            "trains": {},
        }
        self.lock = threading.Lock()
        database.init_db()

    def add_train(self, td_entry):
        headcode = td_entry.get("description")
        td_from = f"{td_entry.get('area_id')}{td_entry.get('from')}"
        td_to = f"{td_entry.get('area_id')}{td_entry.get('to')}"
        direction = config.LOCS_FROM_DICT.get(td_to)
        logger.info(f"{headcode} approaching {td_from}, direction: {direction}")

        # only get the service data if there's a schedule host set
        service = self._get_service(headcode) if config.SCHEDULE_HOST else {}

        with self.lock:
            self.trains_data["trains"][headcode] = {
                "direction": direction,
                "location": td_from,
                "headcode": headcode,
                "timestamp": td_entry.get("timestamp"),
                **service,
            }
        logger.debug(json.dumps(self.trains_data["trains"][headcode], indent=2))
        database.log_movement(
            headcode,
            td_from,
            direction,
            "ARRIVAL",
            self.trains_data["trains"][headcode],
        )

    def remove_train(self, td_entry):
        headcode = td_entry.get("description")
        td_from = f"{td_entry.get('area_id')}{td_entry.get('from')}"
        with self.lock:
            if headcode in self.trains_data["trains"]:
                train_details = self.trains_data["trains"][headcode]
                del self.trains_data["trains"][headcode]
                logger.info(
                    f"{headcode} departing {td_from}, direction: {config.LOCS_TO_DICT.get(td_from)}"
                )
                database.log_movement(
                    headcode,
                    td_from,
                    config.LOCS_TO_DICT.get(td_from),
                    "DEPARTURE",
                    train_details,
                )

    def _get_service(self, headcode):
        logger.info(f"checking services for {headcode} passing {config.TIPLOC_CODE}")
        service_details = {}
        try:
            response = requests.get(
                f"http://{config.SCHEDULE_HOST}:{config.SCHEDULE_PORT}/schedules/headcode/{headcode}"
            )
            if response.ok and (services := response.json().get('schedules',[])):
                logger.info(f"Found {len(services)} services for {headcode}")
                for service in services:
                    for location in service.get("schedule_location"):
                        if location.get("tiploc_code") == config.TIPLOC_CODE:
                            service_details = {
                                "train_uid": service.get("CIF_train_uid"),
                                "atoc": service.get("atoc_code_description"),
                                "type": service.get("CIF_train_category_description"),
                                "power": service.get("CIF_power_type_description"),
                                "speed": service.get("CIF_speed"),
                                "origin": service.get("origin"),
                                "destination": service.get("destination"),
                            }
        except Exception as e:
            logger.error(f"Failed to get service details: {e}")
        return service_details

    def get_snapshot(self):
        with self.lock:
            return {
                "metadata": self.trains_data["metadata"],
                "trains": self.trains_data["trains"].copy(),
            }

    def cleanup(self):
        now = datetime.now()
        with self.lock:
            for k, v in list(self.trains_data["trains"].items()):
                if (
                    now - datetime.strptime(v["timestamp"], "%Y-%m-%d %H:%M:%S")
                ).total_seconds() >= 3600:
                    self.trains_data["trains"].pop(k, None)
                    logger.info(f"Removed stale train: {k}")


train_manager = TrainManager()
