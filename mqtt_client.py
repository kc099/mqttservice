"""
MQTT Client for AWS Lightsail.
Connects to MQTT broker, receives data from three device types,
stores data in SQLite database, and responds to data requests.
"""

import json
import logging
import time
import sys
from datetime import datetime
import paho.mqtt.client as mqtt

import config
from database import (
    init_database,
    insert_temperature_log,
    insert_power_status_log,
    insert_fingerprint_log,
    get_temperature_logs_by_date,
    get_power_status_logs_by_date,
    get_fingerprint_logs_by_date
)

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MQTTClient:
    """MQTT Client for handling device communications and data storage."""

    def __init__(self):
        """Initialize MQTT client."""
        self.client = mqtt.Client(client_id=config.MQTT_CLIENT_ID)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.on_publish = self.on_publish
        self.client.on_subscribe = self.on_subscribe
        self.reconnect_count = 0
        self.is_connected = False

    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker."""
        if rc == 0:
            logger.info("Connected to MQTT broker successfully")
            self.is_connected = True
            self.reconnect_count = 0
            self.subscribe_to_topics()
        else:
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
            self.is_connected = False

    def on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the broker."""
        self.is_connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection. Return code: {rc}")

    def on_message(self, client, userdata, msg):
        """Callback for when a message is received."""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            logger.debug(f"Received message on topic {topic}: {payload}")

            # Parse JSON payload
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON payload on topic {topic}: {payload}")
                return

            # Route message based on topic
            if topic == config.TEMPERATURE_DEVICE_TOPIC:
                self.handle_temperature_data(data)
            elif topic == config.POWER_DEVICE_TOPIC:
                self.handle_power_status_data(data)
            elif topic == config.FINGERPRINT_DEVICE_TOPIC:
                self.handle_fingerprint_data(data)
            elif topic.startswith(config.TEMP_REQUEST_TOPIC_PREFIX):
                self.handle_temperature_request(data, topic)
            elif topic.startswith(config.POWER_REQUEST_TOPIC_PREFIX):
                self.handle_power_request(data, topic)
            elif topic.startswith(config.FINGERPRINT_REQUEST_TOPIC_PREFIX):
                self.handle_fingerprint_request(data, topic)
            else:
                logger.warning(f"Unknown topic: {topic}")

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

    def on_publish(self, client, userdata, mid):
        """Callback for when a message is published."""
        logger.debug(f"Message published with MID: {mid}")

    def on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback for when subscription acknowledgement is received."""
        logger.debug(f"Subscription acknowledged with QoS: {granted_qos}")

    def subscribe_to_topics(self):
        """Subscribe to all required topics."""
        topics = [
            config.TEMPERATURE_DEVICE_TOPIC,
            config.POWER_DEVICE_TOPIC,
            config.FINGERPRINT_DEVICE_TOPIC,
            f"{config.TEMP_REQUEST_TOPIC_PREFIX}/{config.MQTT_CLIENT_ID}",
            f"{config.POWER_REQUEST_TOPIC_PREFIX}/{config.MQTT_CLIENT_ID}",
            f"{config.FINGERPRINT_REQUEST_TOPIC_PREFIX}/{config.MQTT_CLIENT_ID}"
        ]

        for topic in topics:
            self.client.subscribe(topic, qos=1)
            logger.info(f"Subscribed to topic: {topic}")

    def handle_temperature_data(self, data):
        """Handle incoming temperature data from devices."""
        try:
            device_id = data.get('device_id')
            temperature = float(data.get('temperature'))
            humidity = float(data.get('humidity'))
            timestamp = data.get('timestamp')

            if not all([device_id, temperature, humidity, timestamp]):
                logger.warning(f"Incomplete temperature data: {data}")
                return

            if insert_temperature_log(device_id, temperature, humidity, timestamp):
                logger.info(f"Stored temperature data - Device: {device_id}, "
                           f"Temp: {temperature}°C, Humidity: {humidity}%")
            else:
                logger.error(f"Failed to store temperature data for device {device_id}")

        except Exception as e:
            logger.error(f"Error handling temperature data: {e}", exc_info=True)

    def handle_power_status_data(self, data):
        """Handle incoming power status data from devices."""
        try:
            device_id = data.get('device_id')
            status = data.get('status')
            timestamp = data.get('timestamp')

            if not all([device_id, status, timestamp]):
                logger.warning(f"Incomplete power status data: {data}")
                return

            if insert_power_status_log(device_id, status, timestamp):
                logger.info(f"Stored power status - Device: {device_id}, Status: {status}")
            else:
                logger.error(f"Failed to store power status for device {device_id}")

        except Exception as e:
            logger.error(f"Error handling power status data: {e}", exc_info=True)

    def handle_fingerprint_data(self, data):
        """Handle incoming fingerprint authentication data from devices."""
        try:
            device_id = data.get('device_id')
            user_id = data.get('user_id')
            auth_status = data.get('auth_status')
            timestamp = data.get('timestamp')

            if not all([device_id, user_id, auth_status, timestamp]):
                logger.warning(f"Incomplete fingerprint data: {data}")
                return

            if insert_fingerprint_log(device_id, user_id, auth_status, timestamp):
                logger.info(f"Stored fingerprint auth - Device: {device_id}, "
                           f"User: {user_id}, Status: {auth_status}")
            else:
                logger.error(f"Failed to store fingerprint data for device {device_id}")

        except Exception as e:
            logger.error(f"Error handling fingerprint data: {e}", exc_info=True)

    def handle_temperature_request(self, request_data, request_topic):
        """Handle temperature data requests from mobile app."""
        try:
            device_id = request_data.get('device_id')
            date = request_data.get('date')

            if not device_id or not date:
                logger.warning(f"Incomplete request data: {request_data}")
                return

            # Validate date format (YYYY-MM-DD)
            try:
                datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                logger.warning(f"Invalid date format: {date}. Expected YYYY-MM-DD")
                return

            # Retrieve temperature logs for the requested date
            logs = get_temperature_logs_by_date(device_id, date)

            # Format response
            response_data = {
                'device_id': device_id,
                'date': date,
                'count': len(logs),
                'records': []
            }

            for log in logs:
                response_data['records'].append({
                    'temperature': log['temperature'],
                    'humidity': log['humidity'],
                    'timestamp': log['timestamp']
                })

            # Publish response on the datatemp topic with client ID suffix
            response_topic = f"{config.TEMP_DATA_TOPIC_PREFIX}/{config.MQTT_CLIENT_ID}"
            response_payload = json.dumps(response_data)

            self.client.publish(response_topic, response_payload, qos=1)
            logger.info(f"Published temperature data response on {response_topic} - "
                       f"Records: {len(logs)}")

        except Exception as e:
            logger.error(f"Error handling temperature request: {e}", exc_info=True)

    def handle_power_request(self, request_data, request_topic):
        """Handle power status data requests from mobile app."""
        try:
            device_id = request_data.get('device_id')
            date = request_data.get('date')

            if not device_id or not date:
                logger.warning(f"Incomplete power request data: {request_data}")
                return

            try:
                datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                logger.warning(f"Invalid date format: {date}. Expected YYYY-MM-DD")
                return

            logs = get_power_status_logs_by_date(device_id, date)

            response_data = {
                'device_id': device_id,
                'date': date,
                'count': len(logs),
                'records': []
            }

            for log in logs:
                response_data['records'].append({
                    'status': log['status'],
                    'timestamp': log['timestamp']
                })

            response_topic = f"{config.POWER_DATA_TOPIC_PREFIX}/{config.MQTT_CLIENT_ID}"
            response_payload = json.dumps(response_data)
            self.client.publish(response_topic, response_payload, qos=1)
            logger.info(f"Published power status data on {response_topic} - Records: {len(logs)}")

        except Exception as e:
            logger.error(f"Error handling power request: {e}", exc_info=True)

    def handle_fingerprint_request(self, request_data, request_topic):
        """Handle fingerprint authentication data requests from mobile app."""
        try:
            device_id = request_data.get('device_id')
            date = request_data.get('date')

            if not device_id or not date:
                logger.warning(f"Incomplete fingerprint request data: {request_data}")
                return

            try:
                datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                logger.warning(f"Invalid date format: {date}. Expected YYYY-MM-DD")
                return

            logs = get_fingerprint_logs_by_date(device_id, date)

            response_data = {
                'device_id': device_id,
                'date': date,
                'count': len(logs),
                'records': []
            }

            for log in logs:
                response_data['records'].append({
                    'user_id': log['user_id'],
                    'auth_status': log['auth_status'],
                    'timestamp': log['timestamp']
                })

            response_topic = f"{config.FINGERPRINT_DATA_TOPIC_PREFIX}/{config.MQTT_CLIENT_ID}"
            response_payload = json.dumps(response_data)
            self.client.publish(response_topic, response_payload, qos=1)
            logger.info(f"Published fingerprint data on {response_topic} - Records: {len(logs)}")

        except Exception as e:
            logger.error(f"Error handling fingerprint request: {e}", exc_info=True)

    def connect(self):
        """Connect to MQTT broker with reconnection logic."""
        try:
            # Set username and password if configured
            if config.MQTT_USERNAME and config.MQTT_PASSWORD:
                self.client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)

            # Connect to broker
            self.client.connect(
                config.MQTT_BROKER_HOST,
                config.MQTT_BROKER_PORT,
                keepalive=config.MQTT_KEEPALIVE
            )

            # Start network loop
            self.client.loop_start()
            logger.info(f"Connecting to MQTT broker at {config.MQTT_BROKER_HOST}:"
                       f"{config.MQTT_BROKER_PORT}")

        except Exception as e:
            logger.error(f"Connection error: {e}", exc_info=True)
            self.reconnect()

    def reconnect(self):
        """Attempt to reconnect to broker with exponential backoff."""
        if self.reconnect_count < config.MAX_RECONNECT_ATTEMPTS:
            self.reconnect_count += 1
            delay = config.RECONNECT_DELAY * (2 ** (self.reconnect_count - 1))
            logger.warning(f"Reconnection attempt {self.reconnect_count} in {delay} seconds")
            time.sleep(delay)
            self.connect()
        else:
            logger.error("Max reconnection attempts reached. Exiting.")
            sys.exit(1)

    def run(self):
        """Start the MQTT client and keep it running."""
        try:
            # Initialize database
            init_database()
            logger.info("Database initialized")

            # Connect to broker
            self.connect()

            # Keep the client running
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received. Shutting down.")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
        finally:
            self.shutdown()

    def shutdown(self):
        """Gracefully shutdown the MQTT client."""
        logger.info("Shutting down MQTT client")
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT client disconnected")


def main():
    """Main entry point for the application."""
    mqtt_client = MQTTClient()
    mqtt_client.run()


if __name__ == "__main__":
    main()
