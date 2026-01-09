#!/usr/bin/env python3

# Standard
from time import sleep
import threading
import logging

# Third party
from flask import Flask, send_from_directory
from flask_cors import CORS

# Internal
from includes.train_manager import train_manager
from includes.listener import run_listener
from includes import database

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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
    return train_manager.get_snapshot()


@app.route("/history")
def get_history():
    return {"history": database.get_history()}


@app.route("/favicon.ico")
def favicon():
    return send_from_directory("static", "favicon.ico")


@app.route("/style.css")
def style_css():
    return send_from_directory("static", "style.css")


@app.route("/trains.js")
def trains_js():
    return send_from_directory("static", "trains.js")


def cleanup_loop():
    while True:
        sleep(60)
        train_manager.cleanup()


if __name__ == "__main__":
    # Start the listener in a separate daemon thread
    listener_thread = threading.Thread(target=run_listener, daemon=True)
    listener_thread.start()

    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()

    # Run the Flask app (can be interrupted with CTRL-C)
    logger.info("Starting Flask server at http://0.0.0.0:3300")
    try:
        app.run(host="0.0.0.0", port=3300, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("\nShutting down gracefully...")
