import os
from dotenv import load_dotenv

load_dotenv()

FEED_USERNAME = os.getenv("FEED_USERNAME")
FEED_PASSWORD = os.getenv("FEED_PASSWORD")
TD_TOPIC = f"/topic/{os.getenv('TD_TOPIC', 'TD_ALL_SIG_AREA')}"
SIGNALMAPS_URL = f"https://signalmaps.co.uk/#{os.getenv('SIGNALMAPS_LOC', '')}"
SCHEDULE_HOST = os.getenv("SCHEDULE_HOST", None)
SCHEDULE_PORT = os.getenv("SCHEDULE_PORT", None)
HOSTNAME = os.getenv("HOST", "publicdatafeeds.networkrail.co.uk")
PORT = int(os.getenv("PORT", 61618))
TIPLOC_CODE = os.getenv("TIPLOC_CODE", "")

locs_raw = os.getenv("LOCS", "").split(",")
LOCS_FROM = [(loc.split(":")[0], loc.split(":")[2]) for loc in locs_raw if loc]
LOCS_TO = [(loc.split(":")[1], loc.split(":")[2]) for loc in locs_raw if loc]

# Create dictionaries for faster lookup
LOCS_FROM_DICT = {loc: dir for loc, dir in LOCS_FROM}
LOCS_TO_DICT = {loc: dir for loc, dir in LOCS_TO}
