import sqlite3
import json
import logging
import os
import includes.config as config

logger = logging.getLogger(__name__)


def get_connection():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    try:
        db_folder = os.path.dirname(config.DB_PATH)
        if db_folder and not os.path.exists(db_folder):
            os.makedirs(db_folder)

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


def get_history(limit=50):
    try:
        conn = get_connection()
        cursor = conn.execute(
            "SELECT timestamp, headcode, location, direction, event FROM movements ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        return []
