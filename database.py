import sqlite3
import json
import logging
import config

logger = logging.getLogger(__name__)


def get_connection():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    try:
        conn = get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                headcode TEXT,
                location TEXT,
                direction TEXT,
                event TEXT,
                details TEXT
            )
        """)
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {config.DB_PATH}")
    except Exception as e:
        logger.error(f"Failed to init DB: {e}")


def log_movement(headcode, location, direction, event, details):
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO movements (headcode, location, direction, event, details) VALUES (?, ?, ?, ?, ?)",
            (headcode, location, direction, event, json.dumps(details)),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to log movement: {e}")
