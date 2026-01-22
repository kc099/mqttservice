"""
Configuration settings for MQTT client.
Customize these settings based on your AWS Lightsail environment.
"""

import os

# MQTT Broker Configuration
MQTT_BROKER_HOST = os.getenv('MQTT_BROKER_HOST', 'localhost')
MQTT_BROKER_PORT = int(os.getenv('MQTT_BROKER_PORT', 1883))
MQTT_CLIENT_ID = os.getenv('MQTT_CLIENT_ID', 'mqtt_client_1')
MQTT_USERNAME = os.getenv('MQTT_USERNAME', None)
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', None)
MQTT_KEEPALIVE = 60

# Topic Configuration
# These topics will be suffixed with client ID to make them unique per client
TEMP_REQUEST_TOPIC_PREFIX = 'home/gettemp'
TEMP_DATA_TOPIC_PREFIX = 'home/datatemp'
POWER_STATUS_TOPIC = 'home/power/status'
FINGERPRINT_TOPIC = 'home/fingerprint/auth'

# Device subscription topics
TEMPERATURE_DEVICE_TOPIC = 'home/temperature'
POWER_DEVICE_TOPIC = 'home/power'
FINGERPRINT_DEVICE_TOPIC = 'home/fingerprint'

# Database Configuration
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'mqtt_data.db')

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.path.join(os.path.dirname(__file__), 'mqtt_client.log')

# Reconnection Configuration
RECONNECT_DELAY = 5  # seconds
MAX_RECONNECT_ATTEMPTS = 10

# Message payload format expectations
# Messages should be JSON formatted
TEMP_PAYLOAD_FORMAT = {
    'device_id': 'str',
    'temperature': 'float',
    'humidity': 'float',
    'timestamp': 'str'  # ISO format: YYYY-MM-DDTHH:MM:SS
}

POWER_PAYLOAD_FORMAT = {
    'device_id': 'str',
    'status': 'str',  # ON/OFF/TOGGLE
    'timestamp': 'str'
}

FINGERPRINT_PAYLOAD_FORMAT = {
    'device_id': 'str',
    'user_id': 'str',
    'auth_status': 'str',  # PASS/FAIL
    'timestamp': 'str'
}

# Request payload format
REQUEST_PAYLOAD_FORMAT = {
    'device_id': 'str',
    'date': 'str'  # YYYY-MM-DD format
}
