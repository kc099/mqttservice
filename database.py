"""
Database creation and initialization module for MQTT client.
Creates SQLite database with necessary tables for storing device data.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'mqtt_data.db')


def create_connection():
    """Create a database connection to SQLite."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None


def init_database():
    """Initialize the database with necessary tables."""
    conn = create_connection()
    if conn is None:
        print("Failed to create database connection")
        return False

    cursor = conn.cursor()

    try:
        # Temperature and Humidity logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS temperature_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                temperature REAL NOT NULL,
                humidity REAL NOT NULL,
                status TEXT NOT NULL DEFAULT '',
                timestamp DATETIME NOT NULL,
                date TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Power status logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS power_status_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                ebstatus TEXT NOT NULL,
                dgstatus TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                date TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Fingerprint authentication logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fingerprint_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                auth_status TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                date TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create indexes for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_temp_device_date 
            ON temperature_logs(device_id, date)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_power_device_date 
            ON power_status_logs(device_id, date)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_fingerprint_device_date 
            ON fingerprint_logs(device_id, date)
        ''')

        conn.commit()
        print("Database initialized successfully")
        return True

    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")
        return False
    finally:
        conn.close()


def insert_temperature_log(device_id, temperature, humidity, status, timestamp):
    """Insert temperature and humidity log."""
    conn = create_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        date = timestamp.split('T')[0] if 'T' in timestamp else timestamp.split(' ')[0]
        
        cursor.execute('''
            INSERT INTO temperature_logs (device_id, temperature, humidity, status, timestamp, date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (device_id, temperature, humidity, status, timestamp, date))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error inserting temperature log: {e}")
        return False
    finally:
        conn.close()


def insert_power_status_log(device_id, ebstatus, dgstatus, timestamp):
    """Insert power status log."""
    conn = create_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        date = timestamp.split('T')[0] if 'T' in timestamp else timestamp.split(' ')[0]
        
        cursor.execute('''
            INSERT INTO power_status_logs (device_id, ebstatus, dgstatus, timestamp, date)
            VALUES (?, ?, ?, ?, ?)
        ''', (device_id, ebstatus, dgstatus, timestamp, date))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error inserting power status log: {e}")
        return False
    finally:
        conn.close()


def insert_fingerprint_log(device_id, user_id, auth_status, timestamp):
    """Insert fingerprint authentication log."""
    conn = create_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        date = timestamp.split('T')[0] if 'T' in timestamp else timestamp.split(' ')[0]
        
        cursor.execute('''
            INSERT INTO fingerprint_logs (device_id, user_id, auth_status, timestamp, date)
            VALUES (?, ?, ?, ?, ?)
        ''', (device_id, user_id, auth_status, timestamp, date))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error inserting fingerprint log: {e}")
        return False
    finally:
        conn.close()


def get_temperature_logs_by_date(device_id, date):
    """Retrieve temperature logs for a specific device and date."""
    conn = create_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, device_id, temperature, humidity, status, timestamp
            FROM temperature_logs
            WHERE device_id = ? AND date = ?
            ORDER BY timestamp DESC
        ''', (device_id, date))
        
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error retrieving temperature logs: {e}")
        return []
    finally:
        conn.close()


def get_power_status_logs_by_date(device_id, date):
    """Retrieve power status logs for a specific device and date."""
    conn = create_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, device_id, ebstatus, dgstatus, timestamp
            FROM power_status_logs
            WHERE device_id = ? AND date = ?
            ORDER BY timestamp DESC
        ''', (device_id, date))
        
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error retrieving power status logs: {e}")
        return []
    finally:
        conn.close()


def get_fingerprint_logs_by_date(device_id, date):
    """Retrieve fingerprint logs for a specific device and date."""
    conn = create_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, device_id, user_id, auth_status, timestamp
            FROM fingerprint_logs
            WHERE device_id = ? AND date = ?
            ORDER BY timestamp DESC
        ''', (device_id, date))
        
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error retrieving fingerprint logs: {e}")
        return []
    finally:
        conn.close()


if __name__ == "__main__":
    # Initialize the database when script is run directly
    init_database()
